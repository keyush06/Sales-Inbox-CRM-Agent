from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.sql import func
from backend.app.db import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, index=True)
    sender = Column(String, index=True)
    recipient = Column(String, index=True)
    body = Column(Text)
    is_read = Column(Boolean, default=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    source_email_id = Column(Integer, index=True)
    company = Column(String(255), nullable=False)
    contact = Column(String(255))
    sku = Column(String(255))
    qty = Column(Integer)
    budget = Column(Float)
    notes = Column(Text)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(64), nullable=False)  # e.g., RUN_AGENT, APPROVE
    email_id = Column(Integer)
    payload = Column(JSON)                       # store proposed diff / result
    created_at = Column(DateTime(timezone=True), server_default=func.now())