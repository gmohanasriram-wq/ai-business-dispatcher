from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.database import Appointment
from ..models.db_setup import get_db
from ..schemas.appointment import AppointmentConfirmationRequest

router = APIRouter(tags=["Appointments"])

@router.post("/appointments")
def confirm_appointment(payload: AppointmentConfirmationRequest, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.lead_id == payload.lead_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found for the given lead_id")

    if appointment.status == "confirmed":
        if appointment.google_calendar_event_id == payload.google_calendar_event_id:
            return {
                "status": "already_confirmed",
                "appointment_id": appointment.id,
                "google_calendar_event_id": appointment.google_calendar_event_id
            }
        else:
            raise HTTPException(
                status_code=409, 
                detail="Appointment is already confirmed with a different calendar event ID"
            )

    appointment.status = "confirmed"
    appointment.google_calendar_event_id = payload.google_calendar_event_id
    if payload.event_link:
        appointment.event_link = payload.event_link
        
    db.add(appointment)
    db.commit()

    return {
        "status": "success",
        "appointment_id": appointment.id,
        "google_calendar_event_id": appointment.google_calendar_event_id,
        "message": "Appointment confirmed and persisted"
    }

