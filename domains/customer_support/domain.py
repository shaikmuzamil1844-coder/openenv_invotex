"""CustomerSupportDomain — orchestrates tools, tasks, reward, and graders."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..base_domain import BaseDomain
from .db_models import Base, Customer, SupportTicket, SupportAction
from .tools import TOOLS
from .tasks import get_tasks, get_task_by_id
from .graders import TicketResolutionGrader, CustomerSatisfactionGrader


_SYSTEM_PROMPT_TEMPLATE = """\
You are an AI customer support agent. Your job is to resolve customer support tickets efficiently.

Available tools:
{{TOOLS}}

Guidelines:
- Always search for the customer's ticket first before taking any action.
- Look up the customer account to understand their plan and history.
- ALWAYS verify identity before processing any refund.
- For refunds, ensure the amount matches the disputed charge in the ticket.
- Escalate to manager if the dispute is large, unresolvable, or involves a VIP customer.
- After resolving each ticket, close it with a clear resolution summary.
- Always send a notification to the customer about the outcome.
- Be efficient — unnecessary repeated searches reduce your score.

Action format:
  tool_name: <tool_name>
  tool_args: {<arg_key>: <arg_value>, ...}
  thought: <your reasoning>
"""

_REWARD_MAP = {
    "search_tickets": 0.03,
    "lookup_customer": 0.03,
    "verify_identity": 0.10,
    "process_refund": 0.15,
    "escalate_to_manager": 0.10,
    "close_ticket": 0.20,
    "send_notification": 0.08,
}


class CustomerSupportDomain(BaseDomain):
    """Customer Support domain plugin."""

    def __init__(self) -> None:
        self._current_task_id: str | None = None

    def get_tools(self) -> dict[str, dict[str, Any]]:
        return TOOLS

    def get_tasks(self) -> list[dict[str, Any]]:
        return get_tasks()

    def get_graders(self) -> list[Any]:
        return [TicketResolutionGrader(), CustomerSatisfactionGrader()]

    def seed_episode(self, task_id: str, session: Session) -> dict[str, Any]:
        task = get_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Unknown task_id '{task_id}' for customer_support domain.")

        self._current_task_id = task_id

        # Clear old data
        session.query(SupportAction).filter(SupportAction.task_id == task_id).delete()
        session.query(SupportTicket).filter(SupportTicket.task_id == task_id).delete()
        session.query(Customer).filter(Customer.task_id == task_id).delete()
        session.flush()

        for cdata in task["customers"]:
            session.add(Customer(
                customer_id=cdata["customer_id"],
                task_id=task_id,
                name=cdata["name"],
                email=cdata["email"],
                plan=cdata.get("plan", "standard"),
                account_balance=cdata.get("account_balance", 0.0),
            ))

        for tdata in task["tickets"]:
            session.add(SupportTicket(
                ticket_id=tdata["ticket_id"],
                customer_id=tdata["customer_id"],
                task_id=task_id,
                issue_type=tdata["issue_type"],
                description=tdata["description"],
                status=tdata.get("status", "open"),
                priority=tdata.get("priority", "normal"),
                amount_disputed=tdata.get("amount_disputed"),
            ))
        session.flush()

        num_tickets = len(task["tickets"])
        num_customers = len(task["customers"])
        total_disputed = sum(t.get("amount_disputed", 0) or 0 for t in task["tickets"])

        description = (
            f"{task['objective']}\n\n"
            f"Case summary: {num_tickets} open ticket(s) | "
            f"{num_customers} customer(s) | Total disputed: ${total_disputed:.2f}\n"
            f"Start by calling search_tickets to find the relevant case."
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
        if step_count > 12:
            reward = max(0.0, reward - 0.02)
        return reward

    def is_done(self, tool_name: str, result: str, session: Session) -> bool:
        if self._current_task_id is None:
            return False
        try:
            tickets = session.query(SupportTicket).filter(
                SupportTicket.task_id == self._current_task_id
            ).all()
            customers = session.query(Customer).filter(
                Customer.task_id == self._current_task_id
            ).all()
            all_closed = all(t.status == "closed" for t in tickets)
            all_notified = all(c.notification_sent for c in customers)
            return all_closed and all_notified
        except Exception:
            return False

    def get_system_prompt_template(self) -> str:
        return _SYSTEM_PROMPT_TEMPLATE

    def create_tables(self, engine: Any) -> None:
        Base.metadata.create_all(bind=engine)
