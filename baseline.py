"""Scripted baseline agent that runs through all tasks with rule-based logic.

Usage:
    DOMAIN=email_triage python baseline.py
    DOMAIN=traffic_control python baseline.py
"""

from __future__ import annotations

import os
import requests
from typing import Any

BASE_URL = os.getenv("HF_SPACE_URL", "http://localhost:7860")


def _post(endpoint: str, payload: dict | None = None) -> dict:
    url = f"{BASE_URL}{endpoint}"
    resp = requests.post(url, json=payload or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _get(endpoint: str) -> dict:
    url = f"{BASE_URL}{endpoint}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ─── Domain-specific baseline strategies ─────────────────────────────────────

def _email_baseline(task_id: str) -> list[dict]:
    """Simple rule-based email triage agent."""
    actions = [
        {"tool_name": "fetch_emails", "tool_args": {"folder": "inbox"}, "thought": "First, fetch all emails."},
        {"tool_name": "check_sla_status", "tool_args": {"task_id": task_id}, "thought": "Check for SLA deadlines."},
        {"tool_name": "label_email", "tool_args": {"email_id": "easy_002", "label": "urgent"}, "thought": "Production down = urgent."},
        {"tool_name": "label_email", "tool_args": {"email_id": "easy_001", "label": "spam"}, "thought": "Prize email = spam."},
        {"tool_name": "mark_spam", "tool_args": {"email_id": "easy_001"}, "thought": "Mark and move spam."},
        {"tool_name": "move_to_folder", "tool_args": {"email_id": "easy_002", "folder": "urgent"}, "thought": "Move urgent to folder."},
        {"tool_name": "escalate_email", "tool_args": {"email_id": "easy_002", "reason": "Production outage, SLA breach risk."}, "thought": "Escalate urgent SLA email."},
        {"tool_name": "draft_reply", "tool_args": {"email_id": "easy_002", "reply_body": "We are investigating the production issue. ETA for resolution: 30 mins."}, "thought": "Draft reply for urgent email."},
    ]
    return actions


def _traffic_baseline(task_id: str) -> list[dict]:
    """Simple rule-based traffic control agent."""
    actions = [
        {"tool_name": "get_intersection_state", "tool_args": {"intersection_id": "INT-A1"}, "thought": "Check current state."},
        {"tool_name": "get_vehicle_queue", "tool_args": {"intersection_id": "INT-A1", "direction": "all"}, "thought": "Check all queues."},
        {"tool_name": "set_signal_phase", "tool_args": {"intersection_id": "INT-A1", "phase": "green", "direction": "north_south", "duration_seconds": 60}, "thought": "Green for longest queue."},
        {"tool_name": "set_pedestrian_crossing", "tool_args": {"intersection_id": "INT-A1", "active": False}, "thought": "Disable pedestrian crossing during green."},
        {"tool_name": "get_vehicle_queue", "tool_args": {"intersection_id": "INT-A1", "direction": "all"}, "thought": "Check remaining queue."},
        {"tool_name": "set_signal_phase", "tool_args": {"intersection_id": "INT-A1", "phase": "green", "direction": "east_west", "duration_seconds": 30}, "thought": "Green for east-west."},
        {"tool_name": "get_traffic_metrics", "tool_args": {"task_id": task_id}, "thought": "Check overall metrics."},
    ]
    return actions


def _support_baseline(task_id: str) -> list[dict]:
    """Simple rule-based customer support agent."""
    actions = [
        {"tool_name": "search_tickets", "tool_args": {"query": "billing"}, "thought": "Search for billing tickets."},
        {"tool_name": "lookup_customer", "tool_args": {"customer_id": "C-1001"}, "thought": "Look up customer account."},
        {"tool_name": "verify_identity", "tool_args": {"customer_id": "C-1001", "email": "alice@example.com"}, "thought": "Verify identity."},
        {"tool_name": "close_ticket", "tool_args": {"ticket_id": "TKT-5001", "resolution": "Resolved billing inquiry. Charge was a one-time fee per plan terms."}, "thought": "Close ticket."},
        {"tool_name": "send_notification", "tool_args": {"customer_id": "C-1001", "message": "Your billing inquiry has been resolved. The $25 charge was a standard plan fee. No refund required."}, "thought": "Notify customer."},
    ]
    return actions


_BASELINE_STRATEGIES = {
    "email_triage": _email_baseline,
    "traffic_control": _traffic_baseline,
    "customer_support": _support_baseline,
}

_DEFAULT_TASK_IDS = {
    "email_triage": "email_easy",
    "traffic_control": "traffic_easy",
    "customer_support": "support_easy",
}


def run_baseline_all(domain: str) -> dict[str, Any]:
    """Run the baseline agent against all tasks and return scores."""
    task_resp = _get("/tasks")
    tasks = task_resp.get("tasks", [])
    results = []

    strategy = _BASELINE_STRATEGIES.get(domain, _email_baseline)

    for task in tasks:
        task_id = task["id"]
        print(f"\n[Baseline] Running task: {task_id} ({task.get('difficulty', '?')})")

        obs = _post("/reset", {"task_id": task_id})
        print(f"  Task: {obs.get('content', '')[:120]}...")

        actions = strategy(task_id)
        final_obs = obs
        for action in actions:
            try:
                final_obs = _post("/step", {"action": action})
                print(f"  [{action['tool_name']}] → {str(final_obs.get('content', ''))[:80]}")
                if final_obs.get("done"):
                    break
            except Exception as exc:
                print(f"  Error: {exc}")
                break

        score = final_obs.get("info", {}).get("grader_score")
        results.append({
            "task_id": task_id,
            "difficulty": task.get("difficulty"),
            "grader_score": score,
        })
        print(f"  Grader score: {score}")

    return {"domain": domain, "results": results}


if __name__ == "__main__":
    domain = os.getenv("DOMAIN", "email_triage")
    print(f"Running baseline for domain: {domain}")
    results = run_baseline_all(domain)
    print("\n=== Baseline Results ===")
    for r in results["results"]:
        print(f"  {r['task_id']} ({r['difficulty']}): {r['grader_score']}")
