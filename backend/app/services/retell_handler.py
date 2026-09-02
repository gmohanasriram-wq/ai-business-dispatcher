from sqlalchemy.orm import Session
from ..models.database import CallLog, Customer, Lead, Appointment
from ..schemas.retell import RetellWebhookPayload
from fastapi import HTTPException
import json

def process_retell_webhook(db: Session, payload: RetellWebhookPayload):
    if payload.event != "call_analyzed":
        return {"status": "ignored", "reason": f"Event {payload.event} is not call_analyzed"}
        
    call_data = payload.data
    call_id = call_data.call_id
    
    # Check idempotency
    existing_call = db.query(CallLog).filter(CallLog.call_id == call_id).first()
    if existing_call:
        return {"status": "duplicate", "call_id": call_id, "message": "Call already processed"}
        
    # Log the call
    call_log = CallLog(
        call_id=call_id,
        agent_id=call_data.agent_id,
        agent_name=call_data.agent_name,
        raw_payload=payload.model_dump(),
        status="processing"
    )
    db.add(call_log)
    db.flush()
    
    custom_data = call_data.call_analysis.custom_analysis_data
    if not custom_data:
        call_log.status = "failed"
        db.commit()
        return {"status": "failed", "reason": "No custom_analysis_data found"}
        
    # Find or create customer
    customer = None
    if custom_data.phone_number:
        customer = db.query(Customer).filter(Customer.phone_number == custom_data.phone_number).first()
        
    if not customer:
        customer = Customer(
            name=custom_data.customer_name,
            phone_number=custom_data.phone_number
        )
        db.add(customer)
        db.flush()
    else:
        # Update name if previously missing
        if not customer.name and custom_data.customer_name:
            customer.name = custom_data.customer_name
            db.add(customer)
            db.flush()
            
    # Normalize service_type
    service_type_norm = None
    if custom_data.service_type:
        s_type = custom_data.service_type.lower()
        if "leak" in s_type: service_type_norm = "leak"
        elif "clog" in s_type or "drain" in s_type: service_type_norm = "drain_clog"
        elif "burst" in s_type: service_type_norm = "burst_pipe"
        elif "fixture" in s_type: service_type_norm = "fixture_issue"
        elif "heater" in s_type: service_type_norm = "water_heater"
        else: service_type_norm = s_type # Keep original if unknown
    
    # Create Lead
    lead = Lead(
        customer_id=customer.id,
        service_address=custom_data.service_address,
        city=custom_data.city,
        service_type=service_type_norm,
        problem_description=custom_data.problem_description,
        is_emergency=custom_data.is_emergency
    )
    
    # Apply Business Rules
    is_em = custom_data.is_emergency
    co = custom_data.call_outcome
    sas = custom_data.service_area_status
    
    # RULE 1: EMERGENCY
    if is_em or co == "urgent_escalation_required":
        lead.status = "urgent_escalation"
        # TODO: Trigger external escalation logic here
        
    # RULE 2: OUTSIDE SERVICE AREA
    elif sas == "out_of_area":
        lead.status = "out_of_area"
        
    # RULE 3: NORMAL IN-AREA REQUEST
    elif sas == "in_area" and not is_em and custom_data.booking_requested and co == "appointment_request":
        lead.status = "appointment_requested"
        db.add(lead)
        db.flush()
        
        # Create Appointment Request
        appt = Appointment(
            lead_id=lead.id,
            preferred_date=custom_data.preferred_date,
            preferred_time=custom_data.preferred_time,
            status="requested"
        )
        db.add(appt)
        
    # RULE 4 & 5: INFO ONLY or INCOMPLETE
    elif co in ("information_only", "incomplete_information"):
        lead.status = "incomplete"
    else:
        lead.status = "new"
        
    db.add(lead)
    
    # Finalize Call Log
    call_log.status = "processed"
    db.add(call_log)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    return {
        "status": "success",
        "call_id": call_id,
        "lead_id": lead.id,
        "lead_status": lead.status,
        "action": "completed"
    }

