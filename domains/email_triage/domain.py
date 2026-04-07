"""EmailTriageDomain — orchestrates tools, tasks, reward, and graders."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..base_domain import BaseDomain
from .db_models import Base, Email, EmailAction
from .tools import TOOLS
from .tasks import get_tasks, get_task_by_id
from .graders import LabelAccuracyGrader, WorkflowCompletionGrader


_SYSTEM_PROMPT_TEMPLATE = """\
You are an AI email triage agent. Your job is to manage an email inbox efficiently.

You have access to the following tools:
{{TOOLS}}

Guidelines:
- Always fetch emails first to understand the current inbox state.
- Label each email as 'urgent', 'routine', or 'spam' based on its content.
- Move emails to the correct folders: urgent → 'urgent', spam → 'spam', routine → 'archive'.
- Draft replies for all urgent emails to confirm receipt and next steps.
- Check SLA status and escalate any emails with tight or breached deadlines.
- Do not label an email without reading its subject and sender first.
- Think carefully before each action. Efficiency matters.

Action format:
  tool_name: <tool_name>
  tool_args: {<arg_key>: <arg_value>, ...}
  thought: <your reasoning>
"""

# Correct action → reward mapping
_REWARD_MAP = {
    "label": 0.05,       # per correct label
    "move": 0.05,        # per correct folder move
    "draft_reply": 0.10, # per urgent email replied to
    "escalate": 0.15,    # per SLA-urgent email escalated
    "mark_spam": 0.05,   # per spam correctly marked
    "check_sla_status": 0.03,  # small reward for checking SLA
    "fetch_emails": 0.01,      # minimal reward for fetching
}


class EmailTriageDomain(BaseDomain):
    """Email Triage domain plugin for the OpenEnv Hackathon."""

    def __init__(self) -> None:
        self._current_task_id: str | None = None

    def get_tools(self) -> dict[str, dict[str, Any]]:
        return TOOLS

    def get_tasks(self) -> list[dict[str, Any]]:
        return get_tasks()

    def get_graders(self) -> list[Any]:
        return [LabelAccuracyGrader(), WorkflowCompletionGrader()]

    def seed_episode(self, task_id: str, session: Session) -> dict[str, Any]:
        """Seed the DB with emails for this task."""
        task = get_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Unknown task_id '{task_id}' for email_triage domain.")

        self._current_task_id = task_id

        # Clear old records for this task (idempotent re-seed)
        session.query(EmailAction).filter(EmailAction.task_id == task_id).delete()
        session.query(Email).filter(Email.task_id == task_id).delete()
        session.flush()

        for e in task["emails"]:
            session.add(Email(
                email_id=e["email_id"],
                sender=e["sender"],
                subject=e["subject"],
                body=e["body"],
                priority=e["priority"],
                sla_hours=e.get("sla_hours"),
                folder="inbox",
                task_id=task_id,
            ))
        session.flush()

        num_emails = len(task["emails"])
        urgent_count = sum(1 for e in task["emails"] if e["priority"] == "urgent")
        spam_count = sum(1 for e in task["emails"] if e["priority"] == "spam")
        sla_count = sum(1 for e in task["emails"] if e.get("sla_hours") is not None)

        description = (
            f"{task['objective']}\n\n"
            f"Inbox summary: {num_emails} total emails | "
            f"{urgent_count} urgent | {spam_count} spam | "
            f"{sla_count} with SLA deadlines.\n"
            f"Start by calling fetch_emails with folder='inbox'."
        )
        return {"description": description}

    def compute_step_reward(
        self,
        tool_name: str,
        result: str,
        session: Session,
        step_count: int,
    ) -> float:
        base_reward = _REWARD_MAP.get(tool_name, 0.0)
        # Penalize if result contains "Error"
        if "Error" in result:
            return -0.05
        # Small efficiency penalty for too many steps
        if step_count > 15:
            base_reward = max(0.0, base_reward - 0.02)
        return base_reward

    def is_done(self, tool_name: str, result: str, session: Session) -> bool:
        """Episode ends when all urgent emails are labeled + foldered + replied."""
        if self._current_task_id is None:
            return False
        try:
            urgent_emails = session.query(Email).filter(
                Email.task_id == self._current_task_id,
                Email.priority == "urgent",
            ).all()
            if not urgent_emails:
                return False
            return all(
                e.label == "urgent"
                and e.folder == "urgent"
                and e.reply_drafted
                for e in urgent_emails
            )
        except Exception:
            return False

    def get_system_prompt_template(self) -> str:
        return _SYSTEM_PROMPT_TEMPLATE

    def create_tables(self, engine: Any) -> None:
        Base.metadata.create_all(bind=engine)
