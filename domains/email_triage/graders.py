"""Graders for the Email Triage domain.

Two graders:
  1. LabelAccuracyGrader  — checks that each email was labeled correctly
  2. WorkflowCompletionGrader — checks SLA escalation + folder routing + replies
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .db_models import Email, EmailAction


class LabelAccuracyGrader:
    """Grades the agent on how accurately it labeled each email.

    Score = (correct labels) / (total emails)
    """

    def grade(self, trajectory: list[dict[str, Any]], session: Session) -> dict[str, Any]:
        if session is None:
            return {"score": 0.0, "success": False, "feedback": "No session available."}

        all_emails = session.query(Email).all()
        if not all_emails:
            return {"score": 0.0, "success": False, "feedback": "No emails found in DB."}

        correct = 0
        total = len(all_emails)
        details = []

        for email in all_emails:
            expected = email.priority
            actual = email.label
            is_correct = actual == expected
            if is_correct:
                correct += 1
            details.append(
                f"[{email.email_id}] expected={expected} got={actual} → {'✓' if is_correct else '✗'}"
            )

        score = correct / total if total > 0 else 0.0
        return {
            "score": round(score, 3),
            "success": score >= 0.8,
            "correct_labels": correct,
            "total_emails": total,
            "feedback": "\n".join(details),
        }


class WorkflowCompletionGrader:
    """Grades the agent on end-to-end workflow completion.

    Checks:
      - All urgent emails are in the 'urgent' folder          (25%)
      - All spam emails are in the 'spam' folder              (25%)
      - All urgent emails with SLAs are escalated             (25%)
      - All urgent emails have a drafted reply                (25%)
    """

    def grade(self, trajectory: list[dict[str, Any]], session: Session) -> dict[str, Any]:
        if session is None:
            return {"score": 0.0, "success": False, "feedback": "No session available."}

        all_emails = session.query(Email).all()
        if not all_emails:
            return {"score": 0.0, "success": False, "feedback": "No emails found in DB."}

        urgent_emails = [e for e in all_emails if e.priority == "urgent"]
        spam_emails = [e for e in all_emails if e.priority == "spam"]
        sla_urgent = [e for e in urgent_emails if e.sla_hours is not None]

        scores = {}
        details = []

        # 1. Urgent emails in 'urgent' folder
        if urgent_emails:
            correctly_foldered = sum(1 for e in urgent_emails if e.folder == "urgent")
            scores["urgent_folder"] = correctly_foldered / len(urgent_emails)
            details.append(
                f"Urgent folder routing: {correctly_foldered}/{len(urgent_emails)} correct"
            )
        else:
            scores["urgent_folder"] = 1.0
            details.append("No urgent emails to check.")

        # 2. Spam emails in 'spam' folder
        if spam_emails:
            correctly_spammed = sum(1 for e in spam_emails if e.folder == "spam")
            scores["spam_folder"] = correctly_spammed / len(spam_emails)
            details.append(
                f"Spam folder routing: {correctly_spammed}/{len(spam_emails)} correct"
            )
        else:
            scores["spam_folder"] = 1.0
            details.append("No spam emails to check.")

        # 3. SLA-bound urgent emails escalated
        if sla_urgent:
            escalated = sum(1 for e in sla_urgent if e.is_escalated)
            scores["sla_escalation"] = escalated / len(sla_urgent)
            details.append(
                f"SLA escalation: {escalated}/{len(sla_urgent)} escalated"
            )
        else:
            scores["sla_escalation"] = 1.0
            details.append("No SLA-bound emails to check.")

        # 4. Urgent emails with drafted replies
        if urgent_emails:
            replied = sum(1 for e in urgent_emails if e.reply_drafted)
            scores["replies_drafted"] = replied / len(urgent_emails)
            details.append(
                f"Replies drafted: {replied}/{len(urgent_emails)} urgent emails replied"
            )
        else:
            scores["replies_drafted"] = 1.0
            details.append("No urgent emails requiring replies.")

        final_score = sum(scores.values()) / len(scores) if scores else 0.0
        return {
            "score": round(final_score, 3),
            "success": final_score >= 0.75,
            "component_scores": scores,
            "feedback": "\n".join(details),
        }
