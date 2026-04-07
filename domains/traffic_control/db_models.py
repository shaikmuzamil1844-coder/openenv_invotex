"""SQLAlchemy database models for the Traffic Control domain."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, Integer, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Intersection(Base):
    """A traffic intersection with signal state."""

    __tablename__ = "traffic_intersections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intersection_id = Column(String(64), unique=True, nullable=False, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    location = Column(String(128), nullable=False)
    current_phase = Column(String(32), default="red")  # red, green, yellow
    active_direction = Column(String(32), default="north_south")
    phase_duration_seconds = Column(Integer, default=30)
    has_emergency = Column(Boolean, default=False)
    emergency_direction = Column(String(32), nullable=True)
    emergency_cleared = Column(Boolean, default=False)
    pedestrian_crossing_active = Column(Boolean, default=False)


class VehicleQueue(Base):
    """Vehicle queue at an intersection per direction."""

    __tablename__ = "traffic_vehicle_queues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intersection_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(64), nullable=False)
    direction = Column(String(32), nullable=False)  # north, south, east, west
    queue_length = Column(Integer, default=0)
    wait_time_seconds = Column(Integer, default=0)
    has_emergency_vehicle = Column(Boolean, default=False)


class TrafficAction(Base):
    """Audit log of traffic control actions."""

    __tablename__ = "traffic_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False)
    intersection_id = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False)
    action_value = Column(String(256), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    vehicles_cleared = Column(Integer, default=0)
