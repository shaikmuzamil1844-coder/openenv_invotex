"""Task definitions for the Traffic Control domain."""

from __future__ import annotations


TASKS = [
    {
        "id": "traffic_easy",
        "domain": "traffic_control",
        "difficulty": "easy",
        "max_steps": 8,
        "name": "Single Intersection Clearance",
        "objective": (
            "Manage a single 4-way intersection. "
            "Clear the vehicle queue by optimally setting signal phases. "
            "No emergency vehicles present. Minimize total wait time."
        ),
        "intersections": [
            {
                "intersection_id": "INT-A1",
                "location": "Main St & 1st Ave",
                "current_phase": "red",
                "active_direction": "north_south",
                "has_emergency": False,
                "queues": [
                    {"direction": "north", "queue_length": 8, "wait_time_seconds": 45, "has_emergency_vehicle": False},
                    {"direction": "south", "queue_length": 6, "wait_time_seconds": 35, "has_emergency_vehicle": False},
                    {"direction": "east",  "queue_length": 3, "wait_time_seconds": 20, "has_emergency_vehicle": False},
                    {"direction": "west",  "queue_length": 4, "wait_time_seconds": 25, "has_emergency_vehicle": False},
                ],
            }
        ],
    },
    {
        "id": "traffic_medium",
        "domain": "traffic_control",
        "difficulty": "medium",
        "max_steps": 14,
        "name": "Emergency Vehicle Priority",
        "objective": (
            "Manage a 4-way intersection with an emergency vehicle approaching from the east. "
            "1) Dispatch an emergency corridor for the ambulance. "
            "2) Clear the intersection for emergency passage. "
            "3) Resume normal traffic flow after emergency passes. "
            "Emergency vehicle must clear within 5 steps."
        ),
        "intersections": [
            {
                "intersection_id": "INT-B1",
                "location": "Central Ave & Park Blvd",
                "current_phase": "green",
                "active_direction": "north_south",
                "has_emergency": True,
                "emergency_direction": "east",
                "queues": [
                    {"direction": "north", "queue_length": 12, "wait_time_seconds": 60, "has_emergency_vehicle": False},
                    {"direction": "south", "queue_length": 10, "wait_time_seconds": 50, "has_emergency_vehicle": False},
                    {"direction": "east",  "queue_length": 5,  "wait_time_seconds": 30, "has_emergency_vehicle": True},
                    {"direction": "west",  "queue_length": 7,  "wait_time_seconds": 40, "has_emergency_vehicle": False},
                ],
            }
        ],
    },
    {
        "id": "traffic_hard",
        "domain": "traffic_control",
        "difficulty": "hard",
        "max_steps": 24,
        "name": "Peak Hour Grid with Multi-Emergency",
        "objective": (
            "Coordinate 3 intersections during peak hour traffic with 2 emergency vehicles. "
            "Intersection A has an ambulance approaching from north. "
            "Intersection C has a fire truck approaching from west. "
            "1) Create emergency corridors for both vehicles. "
            "2) Reroute non-emergency traffic to reduce congestion. "
            "3) Minimize overall system wait time. "
            "4) Resume normal operations after both emergencies clear."
        ),
        "intersections": [
            {
                "intersection_id": "INT-C1",
                "location": "Highway 1 & Industrial Rd",
                "current_phase": "red",
                "active_direction": "east_west",
                "has_emergency": True,
                "emergency_direction": "north",
                "queues": [
                    {"direction": "north", "queue_length": 20, "wait_time_seconds": 120, "has_emergency_vehicle": True},
                    {"direction": "south", "queue_length": 15, "wait_time_seconds": 90, "has_emergency_vehicle": False},
                    {"direction": "east",  "queue_length": 18, "wait_time_seconds": 110, "has_emergency_vehicle": False},
                    {"direction": "west",  "queue_length": 22, "wait_time_seconds": 130, "has_emergency_vehicle": False},
                ],
            },
            {
                "intersection_id": "INT-C2",
                "location": "Highway 1 & Commerce St",
                "current_phase": "green",
                "active_direction": "north_south",
                "has_emergency": False,
                "queues": [
                    {"direction": "north", "queue_length": 14, "wait_time_seconds": 80, "has_emergency_vehicle": False},
                    {"direction": "south", "queue_length": 11, "wait_time_seconds": 65, "has_emergency_vehicle": False},
                    {"direction": "east",  "queue_length": 9,  "wait_time_seconds": 55, "has_emergency_vehicle": False},
                    {"direction": "west",  "queue_length": 8,  "wait_time_seconds": 50, "has_emergency_vehicle": False},
                ],
            },
            {
                "intersection_id": "INT-C3",
                "location": "Commerce St & 5th Ave",
                "current_phase": "red",
                "active_direction": "north_south",
                "has_emergency": True,
                "emergency_direction": "west",
                "queues": [
                    {"direction": "north", "queue_length": 10, "wait_time_seconds": 60, "has_emergency_vehicle": False},
                    {"direction": "south", "queue_length": 13, "wait_time_seconds": 75, "has_emergency_vehicle": False},
                    {"direction": "east",  "queue_length": 7,  "wait_time_seconds": 45, "has_emergency_vehicle": False},
                    {"direction": "west",  "queue_length": 16, "wait_time_seconds": 95, "has_emergency_vehicle": True},
                ],
            },
        ],
    },
]


def get_tasks() -> list[dict]:
    return [{k: v for k, v in t.items() if k != "intersections"} for t in TASKS]


def get_task_by_id(task_id: str) -> dict | None:
    return next((t for t in TASKS if t["id"] == task_id), None)
