"""TrafficControlDomain — orchestrates tools, tasks, reward, and graders."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..base_domain import BaseDomain
from .db_models import Base, Intersection, VehicleQueue, TrafficAction
from .tools import TOOLS
from .tasks import get_tasks, get_task_by_id
from .graders import EmergencyClearanceGrader, TrafficFlowGrader


_SYSTEM_PROMPT_TEMPLATE = """\
You are an AI traffic control agent managing smart city intersections.
Your goal is to minimize vehicle wait times and ensure emergency vehicles have clear passage.

Available tools:
{{TOOLS}}

Guidelines:
- Always inspect intersection state before taking action.
- Emergency vehicles (ambulances, fire trucks) MUST be given priority — dispatch corridor immediately.
- Set signal phases strategically: clear the direction with the longest queue first.
- After handling emergencies, resume normal signal optimization.
- Use reroute_traffic to reduce congestion in blocked directions.
- Always check traffic metrics at the end to assess your performance.
- Pedestrian crossings must be safely managed — do not activate during green phases.

Action format:
  tool_name: <tool_name>
  tool_args: {<arg_key>: <arg_value>, ...}
  thought: <your reasoning>
"""

_REWARD_MAP = {
    "get_intersection_state": 0.01,
    "set_signal_phase": 0.08,
    "dispatch_emergency_corridor": 0.25,
    "get_vehicle_queue": 0.01,
    "reroute_traffic": 0.05,
    "set_pedestrian_crossing": 0.03,
    "get_traffic_metrics": 0.02,
}


class TrafficControlDomain(BaseDomain):
    """Traffic Control domain plugin."""

    def __init__(self) -> None:
        self._current_task_id: str | None = None

    def get_tools(self) -> dict[str, dict[str, Any]]:
        return TOOLS

    def get_tasks(self) -> list[dict[str, Any]]:
        return get_tasks()

    def get_graders(self) -> list[Any]:
        return [EmergencyClearanceGrader(), TrafficFlowGrader()]

    def seed_episode(self, task_id: str, session: Session) -> dict[str, Any]:
        task = get_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Unknown task_id '{task_id}' for traffic_control domain.")

        self._current_task_id = task_id

        # Clear old data
        session.query(TrafficAction).filter(TrafficAction.task_id == task_id).delete()
        session.query(VehicleQueue).filter(VehicleQueue.task_id == task_id).delete()
        session.query(Intersection).filter(Intersection.task_id == task_id).delete()
        session.flush()

        total_emergency = 0
        total_vehicles = 0

        for idata in task["intersections"]:
            intersection = Intersection(
                intersection_id=idata["intersection_id"],
                task_id=task_id,
                location=idata["location"],
                current_phase=idata["current_phase"],
                active_direction=idata["active_direction"],
                has_emergency=idata.get("has_emergency", False),
                emergency_direction=idata.get("emergency_direction"),
                emergency_cleared=False,
            )
            session.add(intersection)

            if idata.get("has_emergency"):
                total_emergency += 1

            for qdata in idata.get("queues", []):
                q = VehicleQueue(
                    intersection_id=idata["intersection_id"],
                    task_id=task_id,
                    direction=qdata["direction"],
                    queue_length=qdata["queue_length"],
                    wait_time_seconds=qdata["wait_time_seconds"],
                    has_emergency_vehicle=qdata.get("has_emergency_vehicle", False),
                )
                session.add(q)
                total_vehicles += qdata["queue_length"]

        session.flush()

        intersection_ids = [i["intersection_id"] for i in task["intersections"]]
        description = (
            f"{task['objective']}\n\n"
            f"System summary: {len(task['intersections'])} intersection(s) | "
            f"{total_vehicles} vehicles queued | {total_emergency} emergency vehicle(s).\n"
            f"Intersections: {', '.join(intersection_ids)}.\n"
            f"Start by calling get_intersection_state for each intersection."
        )
        return {"description": description}

    def compute_step_reward(
        self,
        tool_name: str,
        result: str,
        session: Session,
        step_count: int,
    ) -> float:
        if "Error" in result:
            return -0.05
        reward = _REWARD_MAP.get(tool_name, 0.0)
        if "EMERGENCY CORRIDOR DISPATCHED" in result:
            reward += 0.15  # extra bonus for emergency
        if step_count > 18:
            reward = max(0.0, reward - 0.02)
        return reward

    def is_done(self, tool_name: str, result: str, session: Session) -> bool:
        if self._current_task_id is None:
            return False
        try:
            intersections = session.query(Intersection).filter(
                Intersection.task_id == self._current_task_id
            ).all()
            emergency_intersections = [i for i in intersections if i.has_emergency]
            if not emergency_intersections:
                # No emergencies: done when all queues are low
                queues = session.query(VehicleQueue).filter(
                    VehicleQueue.task_id == self._current_task_id
                ).all()
                return all(q.queue_length <= 2 for q in queues)
            # With emergencies: done when all emergencies cleared
            return all(i.emergency_cleared for i in emergency_intersections)
        except Exception:
            return False

    def get_system_prompt_template(self) -> str:
        return _SYSTEM_PROMPT_TEMPLATE

    def create_tables(self, engine: Any) -> None:
        Base.metadata.create_all(bind=engine)
