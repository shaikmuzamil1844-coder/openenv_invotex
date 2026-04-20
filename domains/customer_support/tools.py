"""7 tools for the Customer Support domain."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .db_models import Customer, SupportTicket, SupportAction


# ─── Argument Schemas ─────────────────────────────────────────────────────────

class SearchTicketsArgs(BaseModel):
    query: str = Field(..., description="Search query: customer name, email, or ticket ID")


class LookupCustomerArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID to look up (e.g., C-1001)")


class VerifyIdentityArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID to verify")
    email: str = Field(..., description="Email address provided by the customer for verification")


class ProcessRefundArgs(BaseModel):
    ticket_id: str = Field(..., description="Ticket ID for the refund request")
    amount: float = Field(..., description="Amount to refund in USD")
    reason: str = Field(..., description="Reason for the refund")
    authorization_code: str = Field(None, description="Dynamic security authorization code, only if required by API")


class EscalateToManagerArgs(BaseModel):
    ticket_id: str = Field(..., description="Ticket ID to escalate")
    reason: str = Field(..., description="Reason for escalation")


class CloseTicketArgs(BaseModel):
    ticket_id: str = Field(..., description="Ticket ID to close")
    resolution: str = Field(..., description="Resolution summary for the ticket")


class SendNotificationArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID to notify")
    message: str = Field(..., description="Notification message to send to the customer")


# ─── Tool Functions ───────────────────────────────────────────────────────────

def search_tickets(args: SearchTicketsArgs, session: Session) -> str:
    query = args.query.lower()
    tickets = session.query(SupportTicket).all()
    customers = session.query(Customer).all()

    matched_customer_ids = {
        c.customer_id for c in customers
        if query in c.name.lower() or query in c.email.lower()
    }

    matched = [
        t for t in tickets
        if query in t.ticket_id.lower()
        or query in t.description.lower()
        or t.customer_id in matched_customer_ids
    ]

    if not matched:
        return f"No tickets found matching '{args.query}'."

    result = []
    for t in matched:
        result.append(
            f"[{t.ticket_id}] Customer: {t.customer_id} | Type: {t.issue_type} | "
            f"Priority: {t.priority} | Status: {t.status} | "
            f"Disputed: ${t.amount_disputed or 0:.2f} | "
            f"Description: {t.description[:80]}..."
        )
    return f"Found {len(matched)} ticket(s):\n" + "\n".join(result)


def lookup_customer(args: LookupCustomerArgs, session: Session) -> str:
    customer = session.query(Customer).filter(Customer.customer_id == args.customer_id).first()
    if not customer:
        return f"Error: Customer '{args.customer_id}' not found."

    open_tickets = session.query(SupportTicket).filter(
        SupportTicket.customer_id == args.customer_id,
        SupportTicket.status.in_(["open", "in_progress"]),
    ).count()

    output = (
        f"Customer: {customer.name} ({customer.customer_id})\n"
        f"  Email: {customer.email}\n"
        f"  Plan: {customer.plan.upper()}\n"
        f"  Account Balance: ${customer.account_balance:.2f}\n"
        f"  Identity Verified: {customer.identity_verified}\n"
        f"  Open Tickets: {open_tickets}\n"
        f"  Notification Sent: {customer.notification_sent}"
    )
    if customer.authorization_code:
        output += f"\n  Security Auth Code: {customer.authorization_code}"
        
    return output


def verify_identity(args: VerifyIdentityArgs, session: Session) -> str:
    customer = session.query(Customer).filter(Customer.customer_id == args.customer_id).first()
    if not customer:
        return f"Error: Customer '{args.customer_id}' not found."

    verified = args.email.lower().strip() == customer.email.lower().strip()
    customer.identity_verified = verified

    session.add(SupportAction(
        task_id=customer.task_id,
        customer_id=args.customer_id,
        action_type="verify_identity",
        action_value=args.email,
        success=verified,
    ))
    session.flush()

    if verified:
        return f"✓ Identity VERIFIED for customer {customer.name} ({customer.customer_id})."
    else:
        return f"✗ Identity FAILED for customer {customer.customer_id}. Provided email does not match records."


def process_refund(args: ProcessRefundArgs, session: Session) -> str:
    ticket = session.query(SupportTicket).filter(SupportTicket.ticket_id == args.ticket_id).first()
    if not ticket:
        return f"Error: Ticket '{args.ticket_id}' not found."

    customer = session.query(Customer).filter(Customer.customer_id == ticket.customer_id).first()
    if not customer:
        return f"Error: Customer associated with ticket not found."
        
    # Schema Drift / Dynamic Failure Injection
    if ticket.task_id == "support_hard" and not args.authorization_code:
        session.add(SupportAction(
            task_id=ticket.task_id,
            ticket_id=args.ticket_id,
            customer_id=ticket.customer_id,
            action_type="process_refund_failed",
            action_value="403 Forbidden - Missing authorization_code",
            success=False,
        ))
        session.flush()
        return (
            "API ERROR: 403 Forbidden - Schema Validation Failed. "
            "The /v2/refunds endpoint now requires an 'authorization_code' parameter. "
            "Transaction blocked by Security policy."
        )
    if ticket.task_id == "support_hard" and args.authorization_code != customer.authorization_code:
        session.add(SupportAction(
            task_id=ticket.task_id,
            ticket_id=args.ticket_id,
            customer_id=ticket.customer_id,
            action_type="process_refund_failed",
            action_value="403 Forbidden - Invalid authorization_code",
            success=False,
        ))
        session.flush()
        return "API ERROR: 403 Forbidden - Invalid authorization_code."

    if not customer.identity_verified:
        return (
            f"Error: Cannot process refund — customer identity not verified. "
            f"Call verify_identity first."
        )

    if args.amount <= 0:
        return "Error: Refund amount must be positive."

    max_refund = ticket.amount_disputed or 0.0
    if args.amount > max_refund * 1.1:  # allow 10% tolerance
        return (
            f"Error: Refund amount ${args.amount:.2f} exceeds disputed amount "
            f"${max_refund:.2f} by more than 10%."
        )

    ticket.refund_processed = True
    ticket.status = "in_progress"
    customer.account_balance += args.amount

    session.add(SupportAction(
        task_id=ticket.task_id,
        ticket_id=args.ticket_id,
        customer_id=ticket.customer_id,
        action_type="process_refund",
        action_value=f"${args.amount:.2f}: {args.reason}",
        success=True,
    ))
    session.flush()
    return (
        f"✓ Refund of ${args.amount:.2f} processed for ticket {args.ticket_id}. "
        f"Reason: {args.reason}. Customer balance updated."
    )


def escalate_to_manager(args: EscalateToManagerArgs, session: Session) -> str:
    ticket = session.query(SupportTicket).filter(SupportTicket.ticket_id == args.ticket_id).first()
    if not ticket:
        return f"Error: Ticket '{args.ticket_id}' not found."

    ticket.escalated = True
    ticket.priority = "critical"
    ticket.status = "in_progress"

    session.add(SupportAction(
        task_id=ticket.task_id,
        ticket_id=args.ticket_id,
        customer_id=ticket.customer_id,
        action_type="escalate",
        action_value=args.reason[:256],
        success=True,
    ))
    session.flush()
    return (
        f"Ticket {args.ticket_id} has been ESCALATED to a senior manager. "
        f"Reason: {args.reason}. Priority set to CRITICAL."
    )


def close_ticket(args: CloseTicketArgs, session: Session) -> str:
    ticket = session.query(SupportTicket).filter(SupportTicket.ticket_id == args.ticket_id).first()
    if not ticket:
        return f"Error: Ticket '{args.ticket_id}' not found."

    if ticket.status in ("closed",):
        return f"Ticket '{args.ticket_id}' is already closed."

    ticket.status = "closed"
    ticket.closed_at = datetime.utcnow()

    session.add(SupportAction(
        task_id=ticket.task_id,
        ticket_id=args.ticket_id,
        customer_id=ticket.customer_id,
        action_type="close_ticket",
        action_value=args.resolution[:256],
        success=True,
    ))
    session.flush()
    return f"✓ Ticket {args.ticket_id} CLOSED. Resolution: {args.resolution}"


def send_notification(args: SendNotificationArgs, session: Session) -> str:
    customer = session.query(Customer).filter(Customer.customer_id == args.customer_id).first()
    if not customer:
        return f"Error: Customer '{args.customer_id}' not found."

    customer.notification_sent = True

    session.add(SupportAction(
        task_id=customer.task_id,
        customer_id=args.customer_id,
        action_type="send_notification",
        action_value=args.message[:256],
        success=True,
    ))
    session.flush()
    return f"✓ Notification sent to {customer.name} ({customer.email}): \"{args.message[:80]}...\""


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOLS: dict[str, dict[str, Any]] = {
    "search_tickets": {
        "func": search_tickets,
        "schema": SearchTicketsArgs,
        "description": "Search support tickets by customer name, email, or ticket ID.",
    },
    "lookup_customer": {
        "func": lookup_customer,
        "schema": LookupCustomerArgs,
        "description": "Look up a customer account by ID and return account details.",
    },
    "verify_identity": {
        "func": verify_identity,
        "schema": VerifyIdentityArgs,
        "description": "Verify a customer's identity by matching their provided email against records.",
    },
    "process_refund": {
        "func": process_refund,
        "schema": ProcessRefundArgs,
        "description": "Process a monetary refund for a ticket. Identity must be verified first.",
    },
    "escalate_to_manager": {
        "func": escalate_to_manager,
        "schema": EscalateToManagerArgs,
        "description": "Escalate a ticket to a senior manager with a stated reason.",
    },
    "close_ticket": {
        "func": close_ticket,
        "schema": CloseTicketArgs,
        "description": "Close a resolved support ticket with a resolution summary.",
    },
    "send_notification": {
        "func": send_notification,
        "schema": SendNotificationArgs,
        "description": "Send a notification message to a customer about their support case.",
    },
}
