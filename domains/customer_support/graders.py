"""Graders for the Customer Support domain."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .db_models import Customer, SupportTicket, SupportAction


class TicketResolutionGrader:
    """Grades whether all open tickets were properly resolved.

    Score = (correctly closed tickets) / (total tickets)
    Bonus if refunds were processed where needed.
    """

    def grade(self, trajectory: list[dict[str, Any]], session: Session) -> dict[str, Any]:
        if session is None:
            return {"score": 0.0, "success": False, "feedback": "No session."}

        tickets = session.query(SupportTicket).all()
        if not tickets:
            return {"score": 0.0, "success": False, "feedback": "No tickets found."}

        total = len(tickets)
        closed = sum(1 for t in tickets if t.status == "closed")
        refund_tickets = [t for t in tickets if t.issue_type == "refund"]
        refunds_processed = sum(1 for t in refund_tickets if t.refund_processed)

        # Base score: closure rate
        closure_score = closed / total

        # Refund accuracy
        refund_score = (refunds_processed / len(refund_tickets)) if refund_tickets else 1.0

        # Escalation check for high-priority
        high_priority = [t for t in tickets if t.priority in ("high", "critical")]
        escalated = sum(1 for t in high_priority if t.escalated)
        escalation_score = (escalated / len(high_priority)) if high_priority else 1.0

        score = (0.5 * closure_score + 0.3 * refund_score + 0.2 * escalation_score)
        return {
            "score": round(score, 3),
            "success": score >= 0.75,
            "tickets_closed": closed,
            "total_tickets": total,
            "refunds_processed": refunds_processed,
            "escalations_done": escalated,
            "feedback": (
                f"Closed {closed}/{total} tickets. "
                f"Refunds: {refunds_processed}/{len(refund_tickets)}. "
                f"Escalations: {escalated}/{len(high_priority)}."
            ),
        }


class CustomerSatisfactionGrader:
    """Grades the quality of customer handling workflow.

    Checks:
      - Identity was verified before refund                  (30%)
      - Customer was notified                                (30%)
      - No invalid refund attempts (failed tool calls)       (20%)
      - Efficient resolution (low step count)                (20%)
    """

    def grade(self, trajectory: list[dict[str, Any]], session: Session) -> dict[str, Any]:
        if session is None:
            return {"score": 0.0, "success": False, "feedback": "No session."}

        customers = session.query(Customer).all()
        if not customers:
            return {"score": 0.0, "success": False, "feedback": "No customers found."}

        scores = {}
        details = []

        # 1. Identity verification
        customers_needing_refund = []
        for c in customers:
            refund_tickets = session.query(SupportTicket).filter(
                SupportTicket.customer_id == c.customer_id,
                SupportTicket.issue_type == "refund",
            ).count()
            if refund_tickets > 0:
                customers_needing_refund.append(c)

        if customers_needing_refund:
            verified = sum(1 for c in customers_needing_refund if c.identity_verified)
            scores["identity_check"] = verified / len(customers_needing_refund)
            details.append(f"Identity verified: {verified}/{len(customers_needing_refund)}")
        else:
            scores["identity_check"] = 1.0
            details.append("No refund customers requiring ID verification.")

        # 2. Notifications sent
        notified = sum(1 for c in customers if c.notification_sent)
        scores["notifications"] = notified / len(customers)
        details.append(f"Notifications sent: {notified}/{len(customers)}")

        # 3. No bad refund attempts (Allows 1 free fail for Schema Drift discovery)
        failed_actions = session.query(SupportAction).filter(
            SupportAction.action_type.in_(["process_refund", "process_refund_failed"]),
            SupportAction.success == False,
        ).count()
        
        # Give them 1 free grace action in case of dynamic Schema Drift 403 API errors
        penalized_fails = max(0, failed_actions - 1)
        
        total_refund_actions = session.query(SupportAction).filter(
            SupportAction.action_type.in_(["process_refund", "process_refund_failed"])
        ).count()
        
        if total_refund_actions > 0:
            scores["refund_accuracy"] = max(0.0, 1 - (penalized_fails / max(1, total_refund_actions - 1)))
        else:
            scores["refund_accuracy"] = 1.0
        details.append(f"Refund accuracy: {penalized_fails} penalized failures out of {total_refund_actions} attempts")

        # 4. Efficiency (penalize very long trajectories)
        step_count = len(trajectory)
        efficiency = max(0.0, 1.0 - (step_count / 30))
        scores["efficiency"] = efficiency
        details.append(f"Steps taken: {step_count} (efficiency: {efficiency:.2f})")

        weights = {"identity_check": 0.30, "notifications": 0.30, "refund_accuracy": 0.20, "efficiency": 0.20}
        final_score = sum(weights[k] * v for k, v in scores.items())

        return {
            "score": round(final_score, 3),
            "success": final_score >= 0.70,
            "component_scores": scores,
            "feedback": "\n".join(details),
        }
