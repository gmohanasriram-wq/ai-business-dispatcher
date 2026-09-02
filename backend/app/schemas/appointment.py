from pydantic import BaseModel, Field, field_validator
from typing import Optional

class AppointmentConfirmationRequest(BaseModel):
    call_id: str = Field(..., min_length=1)
    lead_id: str = Field(..., min_length=1)
    google_calendar_event_id: str = Field(..., min_length=1)
    event_link: Optional[str] = None
    booking_confirmed: bool

    @field_validator("booking_confirmed")
    @classmethod
    def must_be_true(cls, v):
        if not v:
            raise ValueError("booking_confirmed must be true for confirmation endpoint")
        return v

