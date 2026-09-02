from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from ..models.database import Appointment
from ..models.db_setup import get_db
from ..schemas.appointment import AppointmentConfirmationRequest

logger = logging.getLogger("dispatcher.appointments")

router = APIRouter(tags=["Appointments"])

@router.post("/appointments")
def confirm_appointment(payload: AppointmentConfirmationRequest, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.lead_id == payload.lead_id).first()
    
    if not appointment:
        logger.warning("Appointment not found for lead_id=%s", payload.lead_id)
        raise HTTPException(status_code=404, detail="Appointment not found for the given lead_id")

    if appointment.status == "confirmed":
        if appointment.google_calendar_event_id == payload.google_calendar_event_id:
            logger.info("Appointment already confirmed: lead_id=%s, appointment_id=%s", payload.lead_id, appointment.id)
            return {
                "status": "already_confirmed",
                "appointment_id": appointment.id,
                "google_calendar_event_id": appointment.google_calendar_event_id
            }
        else:
            logger.warning("Appointment conflict for lead_id=%s: existing_event_id=%s, incoming_event_id=%s",
                           payload.lead_id, appointment.google_calendar_event_id, payload.google_calendar_event_id)
            raise HTTPException(
                status_code=409, 
                detail="Appointment is already confirmed with a different calendar event ID"
            )

    appointment.status = "confirmed"
    appointment.google_calendar_event_id = payload.google_calendar_event_id
    if payload.event_link:
        appointment.event_link = payload.event_link
        
    db.add(appointment)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to commit appointment confirmation for lead_id=%s: %s", payload.lead_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to persist appointment confirmation"
        )

    logger.info("Confirmed appointment: lead_id=%s, appointment_id=%s, event_id=%s",
                payload.lead_id, appointment.id, appointment.google_calendar_event_id)

    return {
        "status": "success",
        "appointment_id": appointment.id,
        "google_calendar_event_id": appointment.google_calendar_event_id,
        "message": "Appointment confirmed and persisted"
    }

