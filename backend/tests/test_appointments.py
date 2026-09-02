import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.database import Base, Appointment, Lead, Customer
from app.models.db_setup import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def setup_dummy_appointment(db):
    customer = Customer(name="Test", phone_number="123")
    db.add(customer)
    db.flush()
    lead = Lead(customer_id=customer.id, service_address="123 St", city="Test")
    db.add(lead)
    db.flush()
    appointment = Appointment(lead_id=lead.id, status="requested")
    db.add(appointment)
    db.commit()
    return appointment

def test_confirm_appointment_success():
    db = TestingSessionLocal()
    appt = setup_dummy_appointment(db)
    
    payload = {
        "call_id": "call_123",
        "lead_id": appt.lead_id,
        "google_calendar_event_id": "evt_123",
        "event_link": "http://link",
        "booking_confirmed": True
    }
    
    response = client.post("/appointments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    db.expire_all()
    updated_appt = db.query(Appointment).filter(Appointment.id == appt.id).first()
    assert updated_appt.status == "confirmed"
    assert updated_appt.google_calendar_event_id == "evt_123"

def test_confirm_appointment_idempotency():
    db = TestingSessionLocal()
    appt = setup_dummy_appointment(db)
    
    payload = {
        "call_id": "call_123",
        "lead_id": appt.lead_id,
        "google_calendar_event_id": "evt_123",
        "booking_confirmed": True
    }
    
    client.post("/appointments", json=payload)
    response = client.post("/appointments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "already_confirmed"
    
def test_confirm_appointment_conflict():
    db = TestingSessionLocal()
    appt = setup_dummy_appointment(db)
    
    payload1 = {
        "call_id": "call_123",
        "lead_id": appt.lead_id,
        "google_calendar_event_id": "evt_123",
        "booking_confirmed": True
    }
    client.post("/appointments", json=payload1)
    
    payload2 = {
        "call_id": "call_123",
        "lead_id": appt.lead_id,
        "google_calendar_event_id": "evt_456",
        "booking_confirmed": True
    }
    response = client.post("/appointments", json=payload2)
    assert response.status_code == 409

def test_confirm_appointment_not_found():
    payload = {
        "call_id": "call_123",
        "lead_id": "nonexistent_lead",
        "google_calendar_event_id": "evt_123",
        "booking_confirmed": True
    }
    response = client.post("/appointments", json=payload)
    assert response.status_code == 404
    
def test_confirm_appointment_missing_event_id():
    db = TestingSessionLocal()
    appt = setup_dummy_appointment(db)
    payload = {
        "call_id": "call_123",
        "lead_id": appt.lead_id,
        "booking_confirmed": True
    }
    response = client.post("/appointments", json=payload)
    assert response.status_code == 422
    
def test_confirm_appointment_unconfirmed_rejected():
    db = TestingSessionLocal()
    appt = setup_dummy_appointment(db)
    payload = {
        "call_id": "call_123",
        "lead_id": appt.lead_id,
        "google_calendar_event_id": "evt_123",
        "booking_confirmed": False
    }
    response = client.post("/appointments", json=payload)
    assert response.status_code == 422
