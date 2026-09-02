import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.database import Base, CallLog, Lead, Customer, Appointment, Business, Service
from app.models.db_setup import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown

def build_payload(call_id, custom_data):
    return {
        "event": "call_analyzed",
        "data": {
            "call_id": call_id,
            "call_analysis": {
                "custom_analysis_data": custom_data
            }
        }
    }

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_normal_in_area_appointment_request():
    custom_data = {
        "is_emergency": False,
        "service_area_status": "in_area",
        "booking_requested": True,
        "call_outcome": "appointment_request",
        "phone_number": "1234567890",
        "service_type": "I have a leaky faucet",
        "city": "Toronto"
    }
    payload = build_payload("call_1", custom_data)
    response = client.post("/webhooks/retell", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_status"] == "appointment_requested"
    
    db = TestingSessionLocal()
    lead = db.query(Lead).first()
    assert lead.service_type == "leak" # checking normalization
    
    appt = db.query(Appointment).first()
    assert appt is not None
    assert appt.status == "requested"

def test_emergency_request():
    custom_data = {
        "is_emergency": True,
        "service_area_status": "in_area",
        "call_outcome": "urgent_escalation_required"
    }
    payload = build_payload("call_2", custom_data)
    response = client.post("/webhooks/retell", json=payload)
    assert response.status_code == 200
    assert response.json()["lead_status"] == "urgent_escalation"

def test_outside_area_request():
    custom_data = {
        "is_emergency": False,
        "service_area_status": "out_of_area",
        "call_outcome": "out_of_area_follow_up"
    }
    payload = build_payload("call_3", custom_data)
    response = client.post("/webhooks/retell", json=payload)
    assert response.status_code == 200
    assert response.json()["lead_status"] == "out_of_area"
    
    db = TestingSessionLocal()
    appt = db.query(Appointment).first()
    assert appt is None

def test_information_only_call():
    custom_data = {
        "call_outcome": "information_only"
    }
    payload = build_payload("call_4", custom_data)
    response = client.post("/webhooks/retell", json=payload)
    assert response.status_code == 200
    assert response.json()["lead_status"] == "incomplete"
    
    db = TestingSessionLocal()
    appt = db.query(Appointment).first()
    assert appt is None

def test_incomplete_information_call():
    custom_data = {
        "call_outcome": "incomplete_information"
    }
    payload = build_payload("call_5", custom_data)
    response = client.post("/webhooks/retell", json=payload)
    assert response.status_code == 200
    assert response.json()["lead_status"] == "incomplete"

def test_duplicate_call_id():
    custom_data = {"is_emergency": False}
    payload = build_payload("call_duplicate", custom_data)
    
    # First request
    resp1 = client.post("/webhooks/retell", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "success"
    
    # Second request
    resp2 = client.post("/webhooks/retell", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "duplicate"

def test_malformed_payload():
    payload = {"event": "call_analyzed", "data": {}} # Missing call_id
    resp = client.post("/webhooks/retell", json=payload)
    assert resp.status_code == 422

def test_boolean_normalization():
    custom_data = {
        "is_emergency": "TRUE",
        "booking_requested": "false"
    }
    payload = build_payload("call_bools", custom_data)
    resp = client.post("/webhooks/retell", json=payload)
    assert resp.status_code == 200
    
    db = TestingSessionLocal()
    lead = db.query(Lead).first()
    assert lead.is_emergency is True

def test_unknown_service_type():
    custom_data = {
        "service_type": "I want someone to install a dishwasher"
    }
    payload = build_payload("call_unknown_service", custom_data)
    resp = client.post("/webhooks/retell", json=payload)
    assert resp.status_code == 200
    
    db = TestingSessionLocal()
    lead = db.query(Lead).first()
    assert lead.service_type == "i want someone to install a dishwasher" # Lowercased but intact

def test_service_model_creation():
    db = TestingSessionLocal()
    biz = Business(name="NorthStar Plumbing")
    db.add(biz)
    db.flush()
    svc = Service(business_id=biz.id, name="Leak Repair", category="leak")
    db.add(svc)
    db.commit()
    fetched_svc = db.query(Service).filter(Service.name == "Leak Repair").first()
    assert fetched_svc is not None
    assert fetched_svc.business_id == biz.id
    assert fetched_svc.category == "leak"