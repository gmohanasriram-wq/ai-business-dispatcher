from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["Business Stub Endpoints"])

@router.post("/leads")
def create_lead(payload: Dict[str, Any]):
    # Stub for future manual lead creation
    return {"status": "success", "message": "Lead stub created"}

@router.get("/availability")
def get_availability():
    # Stub for checking Google Calendar availability
    return {"status": "success", "availability": [], "message": "Google Calendar integration not configured"}

@router.post("/appointments")
def create_appointment(payload: Dict[str, Any]):
    # Stub for confirming appointments
    return {"status": "success", "message": "Appointment stub created"}

@router.post("/notifications")
def send_notification(payload: Dict[str, Any]):
    # Stub for sending Email/WhatsApp notifications
    return {"status": "success", "message": "Notification stub triggered"}

@router.post("/call-logs")
def create_call_log(payload: Dict[str, Any]):
    # Stub for manually creating a call log
    return {"status": "success", "message": "Call log stub created"}

