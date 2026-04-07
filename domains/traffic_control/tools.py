"""7 tools for the Traffic Control domain."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .db_models import Intersection, VehicleQueue, TrafficAction


# ─── Argument Schemas ─────────────────────────────────────────────────────────

class GetIntersectionStateArgs(BaseModel):
    intersection_id: str = Field(..., description="ID of the intersection to inspect")


class SetSignalPhaseArgs(BaseModel):
    intersection_id: str = Field(..., description="ID of the intersection")
    phase: str = Field(..., description="Signal phase to set: 'green', 'red', 'yellow'")
    direction: str = Field(..., description="Active direction: 'north_south' or 'east_west'")
    duration_seconds: int = Field(default=30, description="How long to hold this phase (10-120 seconds)")


class DispatchEmergencyCorridorArgs(BaseModel):
    intersection_id: str = Field(..., description="ID of the intersection")
    emergency_direction: str = Field(..., description="Direction emergency vehicle is coming from: north, south, east, west")


class GetVehicleQueueArgs(BaseModel):
    intersection_id: str = Field(..., description="ID of the intersection")
    direction: str = Field(default="all", description="Direction to check: north, south, east, west, or 'all'")


class RerouteTrafficArgs(BaseModel):
    intersection_id: str = Field(..., description="ID of the intersection to reroute from")
    from_direction: str = Field(..., description="Direction to reroute traffic away from")
    to_direction: str = Field(..., description="Alternative direction to route traffic")


class SetPedestrianCrossingArgs(BaseModel):
    intersection_id: str = Field(..., description="ID of the intersection")
    active: bool = Field(..., description="True to activate pedestrian crossing, False to deactivate")


class GetTrafficMetricsArgs(BaseModel):
    task_id: str = Field(..., description="Task ID to get overall traffic metrics for")


# ─── Tool Functions ───────────────────────────────────────────────────────────

def get_intersection_state(args: GetIntersectionStateArgs, session: Session) -> str:
    intersection = session.query(Intersection).filter(
        Intersection.intersection_id == args.intersection_id
    ).first()
    if not intersection:
        return f"Error: Intersection '{args.intersection_id}' not found."
    return (
        f"Intersection {args.intersection_id} ({intersection.location}): "
        f"Phase={intersection.current_phase} | Active Direction={intersection.active_direction} | "
        f"Emergency={intersection.has_emergency} (from {intersection.emergency_direction or 'N/A'}) | "
        f"Emergency Cleared={intersection.emergency_cleared} | "
        f"Pedestrian Crossing={intersection.pedestrian_crossing_active}"
    )


def set_signal_phase(args: SetSignalPhaseArgs, session: Session) -> str:
    intersection = session.query(Intersection).filter(
        Intersection.intersection_id == args.intersection_id
    ).first()
    if not intersection:
        return f"Error: Intersection '{args.intersection_id}' not found."
    valid_phases = {"green", "red", "yellow"}
    if args.phase not in valid_phases:
        return f"Error: Invalid phase '{args.phase}'. Must be one of: {sorted(valid_phases)}"
    valid_directions = {"north_south", "east_west"}
    if args.direction not in valid_directions:
        return f"Error: Invalid direction '{args.direction}'. Must be 'north_south' or 'east_west'."
    if args.duration_seconds < 10 or args.duration_seconds > 120:
        return f"Error: Duration must be between 10 and 120 seconds."

    old_phase = intersection.current_phase
    intersection.current_phase = args.phase
    intersection.active_direction = args.direction
    intersection.phase_duration_seconds = args.duration_seconds

    # Simulate clearing some vehicles when green
    if args.phase == "green":
        queues = session.query(VehicleQueue).filter(
            VehicleQueue.intersection_id == args.intersection_id,
        ).all()
        cleared = 0
        for q in queues:
            if args.direction == "north_south" and q.direction in ("north", "south"):
                cleared_now = min(q.queue_length, max(1, args.duration_seconds // 10))
                q.queue_length = max(0, q.queue_length - cleared_now)
                q.wait_time_seconds = max(0, q.wait_time_seconds - args.duration_seconds)
                cleared += cleared_now
        session.add(TrafficAction(
            task_id=intersection.task_id,
            intersection_id=args.intersection_id,
            action_type="set_signal",
            action_value=f"{args.phase}:{args.direction}:{args.duration_seconds}s",
            vehicles_cleared=cleared,
        ))
        session.flush()
        return (
            f"Signal at {args.intersection_id} set to {args.phase} ({args.direction}) "
            f"for {args.duration_seconds}s. ~{cleared} vehicles cleared."
        )

    session.add(TrafficAction(
        task_id=intersection.task_id,
        intersection_id=args.intersection_id,
        action_type="set_signal",
        action_value=f"{args.phase}:{args.direction}",
    ))
    session.flush()
    return f"Signal at {args.intersection_id} changed from {old_phase} to {args.phase} ({args.direction})."


def dispatch_emergency_corridor(args: DispatchEmergencyCorridorArgs, session: Session) -> str:
    intersection = session.query(Intersection).filter(
        Intersection.intersection_id == args.intersection_id
    ).first()
    if not intersection:
        return f"Error: Intersection '{args.intersection_id}' not found."
    if not intersection.has_emergency:
        return f"No emergency vehicle at intersection '{args.intersection_id}'."

    # Set appropriate green phase for emergency
    corridor_direction = "north_south" if args.emergency_direction in ("north", "south") else "east_west"
    intersection.current_phase = "green"
    intersection.active_direction = corridor_direction
    intersection.emergency_cleared = True

    # Clear emergency queue
    emerg_queues = session.query(VehicleQueue).filter(
        VehicleQueue.intersection_id == args.intersection_id,
        VehicleQueue.direction == args.emergency_direction,
    ).all()
    for q in emerg_queues:
        q.queue_length = max(0, q.queue_length - 5)
        q.has_emergency_vehicle = False

    session.add(TrafficAction(
        task_id=intersection.task_id,
        intersection_id=args.intersection_id,
        action_type="emergency_corridor",
        action_value=args.emergency_direction,
        vehicles_cleared=5,
    ))
    session.flush()
    return (
        f"EMERGENCY CORRIDOR DISPATCHED at {args.intersection_id}. "
        f"Green corridor opened for {args.emergency_direction}-bound emergency vehicle. "
        f"Vehicle cleared in ~30 seconds."
    )


def get_vehicle_queue(args: GetVehicleQueueArgs, session: Session) -> str:
    query = session.query(VehicleQueue).filter(
        VehicleQueue.intersection_id == args.intersection_id
    )
    if args.direction != "all":
        query = query.filter(VehicleQueue.direction == args.direction)
    queues = query.all()
    if not queues:
        return f"No queue data for intersection '{args.intersection_id}' direction '{args.direction}'."
    result = []
    for q in queues:
        emerg = " 🚨 EMERGENCY VEHICLE" if q.has_emergency_vehicle else ""
        result.append(
            f"  {q.direction.upper()}: {q.queue_length} vehicles | Wait: {q.wait_time_seconds}s{emerg}"
        )
    return f"Queue at {args.intersection_id}:\n" + "\n".join(result)


def reroute_traffic(args: RerouteTrafficArgs, session: Session) -> str:
    intersection = session.query(Intersection).filter(
        Intersection.intersection_id == args.intersection_id
    ).first()
    if not intersection:
        return f"Error: Intersection '{args.intersection_id}' not found."

    from_q = session.query(VehicleQueue).filter(
        VehicleQueue.intersection_id == args.intersection_id,
        VehicleQueue.direction == args.from_direction,
    ).first()
    to_q = session.query(VehicleQueue).filter(
        VehicleQueue.intersection_id == args.intersection_id,
        VehicleQueue.direction == args.to_direction,
    ).first()

    if not from_q or not to_q:
        return f"Error: Could not find queues for directions '{args.from_direction}' and '{args.to_direction}'."

    rerouted = min(from_q.queue_length // 3, 5)
    from_q.queue_length -= rerouted

    session.add(TrafficAction(
        task_id=intersection.task_id,
        intersection_id=args.intersection_id,
        action_type="reroute",
        action_value=f"{args.from_direction}→{args.to_direction}",
        vehicles_cleared=rerouted,
    ))
    session.flush()
    return f"Rerouted ~{rerouted} vehicles from {args.from_direction} to {args.to_direction} at {args.intersection_id}."


def set_pedestrian_crossing(args: SetPedestrianCrossingArgs, session: Session) -> str:
    intersection = session.query(Intersection).filter(
        Intersection.intersection_id == args.intersection_id
    ).first()
    if not intersection:
        return f"Error: Intersection '{args.intersection_id}' not found."
    intersection.pedestrian_crossing_active = args.active
    status = "ACTIVATED" if args.active else "DEACTIVATED"
    session.flush()
    return f"Pedestrian crossing at {args.intersection_id} {status}."


def get_traffic_metrics(args: GetTrafficMetricsArgs, session: Session) -> str:
    intersections = session.query(Intersection).filter(
        Intersection.task_id == args.task_id
    ).all()
    if not intersections:
        return f"No intersections found for task '{args.task_id}'."

    total_cleared = 0
    actions = session.query(TrafficAction).filter(
        TrafficAction.task_id == args.task_id
    ).all()
    for a in actions:
        total_cleared += a.vehicles_cleared

    all_queues = session.query(VehicleQueue).filter(
        VehicleQueue.task_id == args.task_id
    ).all()
    total_waiting = sum(q.queue_length for q in all_queues)
    total_wait_time = sum(q.wait_time_seconds for q in all_queues)
    emergencies_cleared = sum(1 for i in intersections if i.emergency_cleared)
    total_emergencies = sum(1 for i in intersections if i.has_emergency)

    return (
        f"Traffic Metrics (Task: {args.task_id}):\n"
        f"  Intersections managed: {len(intersections)}\n"
        f"  Total vehicles cleared: {total_cleared}\n"
        f"  Vehicles still waiting: {total_waiting}\n"
        f"  Total wait time remaining: {total_wait_time}s\n"
        f"  Emergencies cleared: {emergencies_cleared}/{total_emergencies}\n"
        f"  Total actions taken: {len(actions)}"
    )


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOLS: dict[str, dict] = {
    "get_intersection_state": {
        "func": get_intersection_state,
        "schema": GetIntersectionStateArgs,
        "description": "Get current state of a traffic intersection (phase, direction, emergency status).",
    },
    "set_signal_phase": {
        "func": set_signal_phase,
        "schema": SetSignalPhaseArgs,
        "description": "Set traffic signal phase (red/green/yellow) and active direction for an intersection.",
    },
    "dispatch_emergency_corridor": {
        "func": dispatch_emergency_corridor,
        "schema": DispatchEmergencyCorridorArgs,
        "description": "Open an emergency green corridor for an ambulance or fire truck approaching from a direction.",
    },
    "get_vehicle_queue": {
        "func": get_vehicle_queue,
        "schema": GetVehicleQueueArgs,
        "description": "Get the vehicle queue length and wait time for an intersection/direction.",
    },
    "reroute_traffic": {
        "func": reroute_traffic,
        "schema": RerouteTrafficArgs,
        "description": "Reroute vehicles from a congested direction to an alternate route.",
    },
    "set_pedestrian_crossing": {
        "func": set_pedestrian_crossing,
        "schema": SetPedestrianCrossingArgs,
        "description": "Activate or deactivate pedestrian crossing signals at an intersection.",
    },
    "get_traffic_metrics": {
        "func": get_traffic_metrics,
        "schema": GetTrafficMetricsArgs,
        "description": "Get overall traffic metrics: vehicles cleared, wait times, emergencies resolved.",
    },
}
