"""Tool definitions for the Email Triage domain.

7 tools:
  1. fetch_emails      — list emails in inbox for the current task
  2. label_email       — assign a priority label to an email
  3. move_to_folder    — move an email to a folder
  4. draft_reply       — draft and log a reply for an email
  5. escalate_email    — escalate an email to a supervisor
  6. mark_spam         — mark an email as spam
  7. check_sla_status  — check SLA status for all emails in the current task
"""

from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .db_models import Email, EmailAction


# ─── Argument Schemas ─────────────────────────────────────────────────────────

class FetchEmailsArgs(BaseModel):
    folder: str = Field(default="inbox", description="Folder to fetch from: inbox, urgent, spam, archive")


class LabelEmailArgs(BaseModel):
    email_id: str = Field(..., description="ID of the email to label")
    label: str = Field(..., description="Label to assign: 'urgent', 'routine', or 'spam'")


class MoveToFolderArgs(BaseModel):
    email_id: str = Field(..., description="ID of the email to move")
    folder: str = Field(..., description="Target folder: inbox, urgent, spam, archive")


class DraftReplyArgs(BaseModel):
    email_id: str = Field(..., description="ID of the email to reply to")
    reply_body: str = Field(..., description="The reply message body to draft")


class EscalateEmailArgs(BaseModel):
    email_id: str = Field(..., description="ID of the email to escalate")
    reason: str = Field(..., description="Reason for escalation")


class MarkSpamArgs(BaseModel):
    email_id: str = Field(..., description="ID of the email to mark as spam")


class CheckSLAStatusArgs(BaseModel):
    task_id: str = Field(..., description="Task ID to check SLA status for")


# ─── Tool Functions ───────────────────────────────────────────────────────────

def fetch_emails(args: FetchEmailsArgs, session: Session) -> str:
    emails = session.query(Email).filter(Email.folder == args.folder).all()
    if not emails:
        return f"No emails found in folder '{args.folder}'."
    result = []
    for e in emails:
        result.append(
            f"[{e.email_id}] From: {e.sender} | Subject: {e.subject} | "
            f"Priority: {e.priority} | Label: {e.label or 'none'} | "
            f"SLA: {e.sla_hours}h | Escalated: {e.is_escalated}"
        )
    return "\n".join(result)


def label_email(args: LabelEmailArgs, session: Session) -> str:
    email = session.query(Email).filter(Email.email_id == args.email_id).first()
    if not email:
        return f"Error: Email '{args.email_id}' not found."
    valid_labels = {"urgent", "routine", "spam"}
    if args.label not in valid_labels:
        return f"Error: Invalid label '{args.label}'. Must be one of: {sorted(valid_labels)}"
    email.label = args.label
    session.add(EmailAction(
        task_id=email.task_id,
        email_id=args.email_id,
        action_type="label",
        action_value=args.label,
        correct=(args.label == email.priority),
    ))
    session.flush()
    return f"Email '{args.email_id}' labeled as '{args.label}'."


def move_to_folder(args: MoveToFolderArgs, session: Session) -> str:
    email = session.query(Email).filter(Email.email_id == args.email_id).first()
    if not email:
        return f"Error: Email '{args.email_id}' not found."
    valid_folders = {"inbox", "urgent", "spam", "archive"}
    if args.folder not in valid_folders:
        return f"Error: Invalid folder '{args.folder}'. Must be one of: {sorted(valid_folders)}"
    email.folder = args.folder
    session.add(EmailAction(
        task_id=email.task_id,
        email_id=args.email_id,
        action_type="move",
        action_value=args.folder,
    ))
    session.flush()
    return f"Email '{args.email_id}' moved to '{args.folder}'."


def draft_reply(args: DraftReplyArgs, session: Session) -> str:
    email = session.query(Email).filter(Email.email_id == args.email_id).first()
    if not email:
        return f"Error: Email '{args.email_id}' not found."
    email.reply_drafted = True
    session.add(EmailAction(
        task_id=email.task_id,
        email_id=args.email_id,
        action_type="draft_reply",
        action_value=args.reply_body[:200],  # truncate for storage
    ))
    session.flush()
    return f"Reply drafted for email '{args.email_id}': \"{args.reply_body[:80]}...\""


def escalate_email(args: EscalateEmailArgs, session: Session) -> str:
    email = session.query(Email).filter(Email.email_id == args.email_id).first()
    if not email:
        return f"Error: Email '{args.email_id}' not found."
    email.is_escalated = True
    session.add(EmailAction(
        task_id=email.task_id,
        email_id=args.email_id,
        action_type="escalate",
        action_value=args.reason[:200],
        correct=(email.priority == "urgent"),
    ))
    session.flush()
    return f"Email '{args.email_id}' escalated to supervisor. Reason: {args.reason}"


def mark_spam(args: MarkSpamArgs, session: Session) -> str:
    email = session.query(Email).filter(Email.email_id == args.email_id).first()
    if not email:
        return f"Error: Email '{args.email_id}' not found."
    email.label = "spam"
    email.folder = "spam"
    session.add(EmailAction(
        task_id=email.task_id,
        email_id=args.email_id,
        action_type="mark_spam",
        action_value="spam",
        correct=(email.priority == "spam"),
    ))
    session.flush()
    return f"Email '{args.email_id}' marked as spam and moved to spam folder."


def check_sla_status(args: CheckSLAStatusArgs, session: Session) -> str:
    emails = session.query(Email).filter(
        Email.task_id == args.task_id,
        Email.sla_hours != None,
    ).all()
    if not emails:
        return f"No SLA-bound emails found for task '{args.task_id}'."
    result = []
    for e in emails:
        status = "BREACHED" if e.sla_breached else f"DUE IN {e.sla_hours}h"
        escalated = "ESCALATED" if e.is_escalated else "NOT ESCALATED"
        result.append(
            f"[{e.email_id}] SLA: {status} | {escalated} | From: {e.sender} | Subject: {e.subject[:50]}"
        )
    return "\n".join(result)


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOLS: dict[str, dict[str, Any]] = {
    "fetch_emails": {
        "func": fetch_emails,
        "schema": FetchEmailsArgs,
        "description": "Fetch emails from a folder (inbox, urgent, spam, archive). Returns email list with IDs.",
    },
    "label_email": {
        "func": label_email,
        "schema": LabelEmailArgs,
        "description": "Assign a priority label to an email: 'urgent', 'routine', or 'spam'.",
    },
    "move_to_folder": {
        "func": move_to_folder,
        "schema": MoveToFolderArgs,
        "description": "Move an email to a specific folder: inbox, urgent, spam, or archive.",
    },
    "draft_reply": {
        "func": draft_reply,
        "schema": DraftReplyArgs,
        "description": "Draft a reply to an email. Marks email as replied.",
    },
    "escalate_email": {
        "func": escalate_email,
        "schema": EscalateEmailArgs,
        "description": "Escalate an email to a supervisor with a stated reason.",
    },
    "mark_spam": {
        "func": mark_spam,
        "schema": MarkSpamArgs,
        "description": "Mark an email as spam and move it to the spam folder.",
    },
    "check_sla_status": {
        "func": check_sla_status,
        "schema": CheckSLAStatusArgs,
        "description": "Check SLA deadlines for all time-sensitive emails in the current task.",
    },
}
