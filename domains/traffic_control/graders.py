"""Graders for the Traffic Control domain."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .db_models import Intersection, VehicleQueue, TrafficAction


class EmergencyClearanceGrader:
    """Grades whether emergency vehicles were cleared correctly and quickly.

    Score = (emergencies cleared) / (total emergencies)
    Bonus: if cleared in < 4 actions per emergency.
    """

    def grade(self, trajectory: list[dict[str, Any]], session: Session) -> dict[str, Any]:
        if session is None:
            return {"score": 0.0, "success": False, "feedback": "No session."}

        intersections = session.query(Intersection).all()
        if not intersections:
            return {"score": 0.0, "success": False, "feedback": "No intersections found."}

        total_emergencies = sum(1 for i in intersections if i.has_emergency)
        if total_emergencies == 0:
            return {"score": 1.0, "success": True, "feedback": "No emergencies — full score."}

        emergencies_cleared = sum(1 for i in intersections if i.has_emergency and i.emergency_cleared)
        base_score = emergencies_cleared / total_emergencies

        # Check if emergency corridors were dispatched efficiently
        emergency_actions = [
            s for s in trajectory
            if s.get("tool_name") == "dispatch_emergency_corridor"
        ]
        efficiency_bonus = 0.0
        if emergencies_cleared > 0 and len(emergency_actions) <= total_emergencies * 2:
            efficiency_bonus = 0.1

        final_score = min(1.0, base_score + efficiency_bonus)
        return {
            "score": round(final_score, 3),
            "success": emergencies_cleared == total_emergencies,
            "emergencies_cleared": emergencies_cleared,
            "total_emergencies": total_emergencies,
            "efficiency_bonus": efficiency_bonus,
            "feedback": f"Cleared {emergencies_cleared}/{total_emergencies} emergencies. Bonus: {efficiency_bonus}",
        }


class TrafficFlowGrader:
    """Grades overall traffic flow improvement.

    Score = 1 - (remaining_wait_ratio)
    where remaining_wait_ratio = current_total_wait / initial_total_wait.
    """

    def grade(self, trajectory: list[dict[str, Any]], session: Session) -> dict[str, Any]:
        if session is None:
            return {"score": 0.0, "success": False, "feedback": "No session."}

        all_queues = session.query(VehicleQueue).all()
        if not all_queues:
            return {"score": 0.0, "success": False, "feedback": "No queue data."}

        # Current wait times
        current_total_wait = sum(q.wait_time_seconds for q in all_queues)
        current_total_vehicles = sum(q.queue_length for q in all_queues)

        # Actions taken
        actions = session.query(TrafficAction).all()
        total_cleared = sum(a.vehicles_cleared for a in actions)

        # Score: vehicles cleared / (original vehicles + cleared)
        # We approximate original as current + cleared
        original_estimate = current_total_vehicles + total_cleared
        if original_estimate == 0:
            return {"score": 1.0, "success": True, "feedback": "No vehicles to manage."}

        clearance_ratio = total_cleared / original_estimate
        # Also reward low remaining wait
        wait_ratio = current_total_wait / max(1, current_total_wait + total_cleared * 30)
        score = min(1.0, 0.6 * clearance_ratio + 0.4 * (1 - wait_ratio))

        return {
            "score": round(score, 3),
            "success": score >= 0.6,
            "total_cleared": total_cleared,
            "remaining_vehicles": current_total_vehicles,
            "remaining_wait_seconds": current_total_wait,
            "feedback": (
                f"Cleared {total_cleared} vehicles. "
                f"{current_total_vehicles} still waiting ({current_total_wait}s total wait)."
            ),
        }
