"""SQLAlchemy models for the Customer Support domain."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, Integer, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "support_customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(64), unique=True, nullable=False, index=True)
    task_id = Column(String(64), nullable=False)
    name = Column(String(256), nullable=False)
    email = Column(String(256), nullable=False)
    plan = Column(String(64), default="standard")         # standard, premium, vip
    account_balance = Column(Float, default=0.0)
    identity_verified = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    authorization_code = Column(String(64), nullable=True)  # Schema Drift mechanic


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(64), unique=True, nullable=False, index=True)
    customer_id = Column(String(64), nullable=False)
    task_id = Column(String(64), nullable=False)
    issue_type = Column(String(64), nullable=False)       # billing, refund, technical, escalation
    description = Column(Text, nullable=False)
    status = Column(String(32), default="open")           # open, in_progress, resolved, closed
    priority = Column(String(32), default="normal")       # low, normal, high, critical
    amount_disputed = Column(Float, nullable=True)
    refund_processed = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)


class SupportAction(Base):
    __tablename__ = "support_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False)
    ticket_id = Column(String(64), nullable=True)
    customer_id = Column(String(64), nullable=True)
    action_type = Column(String(64), nullable=False)
    action_value = Column(String(512), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
