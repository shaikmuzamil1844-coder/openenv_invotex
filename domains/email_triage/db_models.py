"""SQLAlchemy database models for the Email Triage domain."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Email(Base):
    """Represents an email in the agent's inbox."""

    __tablename__ = "email_triage_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String(64), unique=True, nullable=False, index=True)
    sender = Column(String(256), nullable=False)
    subject = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    priority = Column(String(32), default="routine")  # urgent, routine, spam
    label = Column(String(64), nullable=True)         # assigned by agent
    folder = Column(String(64), default="inbox")      # inbox, urgent, archive, spam
    is_escalated = Column(Boolean, default=False)
    reply_drafted = Column(Boolean, default=False)
    sla_hours = Column(Integer, nullable=True)        # SLA deadline in hours
    sla_breached = Column(Boolean, default=False)
    task_id = Column(String(64), nullable=False, index=True)


class EmailAction(Base):
    """Audit log of agent actions on emails."""

    __tablename__ = "email_triage_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False)
    email_id = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False)   # label, move, escalate, etc.
    action_value = Column(String(256), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    correct = Column(Boolean, nullable=True)           # grader fills this in
