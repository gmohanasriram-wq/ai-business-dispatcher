from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Dict

class CustomAnalysisData(BaseModel):
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    service_address: Optional[str] = None
    city: Optional[str] = None
    service_type: Optional[str] = None
    problem_description: Optional[str] = None
    is_emergency: Optional[Any] = False # Will normalize below
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    booking_requested: Optional[Any] = False # Will normalize below
    service_area_status: Optional[str] = "unknown"
    call_outcome: Optional[str] = "incomplete_information"

    @field_validator("is_emergency", "booking_requested", mode="before")
    @classmethod
    def normalize_boolean(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return False
        
    @field_validator("service_area_status", mode="before")
    @classmethod
    def normalize_service_area(cls, v):
        allowed = {"in_area", "out_of_area", "unknown"}
        if v and v.lower() in allowed:
            return v.lower()
        return "unknown"

    @field_validator("call_outcome", mode="before")
    @classmethod
    def normalize_call_outcome(cls, v):
        allowed = {
            "appointment_request",
            "urgent_escalation_required",
            "out_of_area_follow_up",
            "information_only",
            "incomplete_information"
        }
        if v and v.lower() in allowed:
            return v.lower()
        return "incomplete_information"

class CallAnalysis(BaseModel):
    custom_analysis_data: Optional[CustomAnalysisData] = Field(default_factory=CustomAnalysisData)

class RetellCallEvent(BaseModel):
    call_id: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    call_status: Optional[str] = None
    transcript: Optional[str] = None
    call_analysis: Optional[CallAnalysis] = Field(default_factory=CallAnalysis)

class RetellWebhookPayload(BaseModel):
    event: str
    call: RetellCallEvent

