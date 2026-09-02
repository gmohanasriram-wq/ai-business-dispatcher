from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Business(Base):
    __tablename__ = 'businesses'
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ServiceArea(Base):
    __tablename__ = 'service_areas'
    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey('businesses.id'), nullable=False)
    city = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Service(Base):
    __tablename__ = 'services'
    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey('businesses.id'), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=True)
    phone_number = Column(String, unique=True, nullable=True) # Usually unique per customer
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False)
    service_address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    service_type = Column(String, nullable=True)
    problem_description = Column(Text, nullable=True)
    is_emergency = Column(Boolean, default=False)
    status = Column(String, default='new') # new, urgent_escalation, out_of_area, incomplete
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(String, primary_key=True, default=generate_uuid)
    lead_id = Column(String, ForeignKey('leads.id'), nullable=False)
    preferred_date = Column(String, nullable=True)
    preferred_time = Column(String, nullable=True)
    status = Column(String, default='requested') # requested, confirmed, cancelled, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CallLog(Base):
    __tablename__ = 'call_logs'
    id = Column(String, primary_key=True, default=generate_uuid)
    call_id = Column(String, unique=True, nullable=False) # Idempotency key
    agent_id = Column(String, nullable=True)
    agent_name = Column(String, nullable=True)
    status = Column(String, default='processed') # processed, failed, duplicate
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

