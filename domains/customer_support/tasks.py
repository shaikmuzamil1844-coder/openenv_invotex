"""Task definitions for the Customer Support domain."""

from __future__ import annotations


TASKS = [
    {
        "id": "support_easy",
        "domain": "customer_support",
        "difficulty": "easy",
        "max_steps": 6,
        "name": "Billing Inquiry Resolution",
        "objective": (
            "A customer has a billing inquiry. "
            "1) Search for their ticket using their name or email. "
            "2) Look up the customer account. "
            "3) Resolve the billing question using the account information. "
            "4) Close the ticket and send a notification. "
        ),
        "customers": [
            {
                "customer_id": "C-1001",
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "plan": "standard",
                "account_balance": -25.00,
            }
        ],
        "tickets": [
            {
                "ticket_id": "TKT-5001",
                "customer_id": "C-1001",
                "issue_type": "billing",
                "description": "Customer is asking why they were charged an extra $25 this month. Says they didn't sign up for any add-ons.",
                "status": "open",
                "priority": "normal",
                "amount_disputed": 25.00,
            }
        ],
    },
    {
        "id": "support_medium",
        "domain": "customer_support",
        "difficulty": "medium",
        "max_steps": 12,
        "name": "Refund Request with Verification",
        "objective": (
            "A premium customer is requesting a refund for a double-charge. "
            "1) Search for their ticket. "
            "2) Look up the customer account details. "
            "3) Verify the customer's identity before processing any refund. "
            "4) Process the refund if identity is verified and charge is legitimate. "
            "5) Close the ticket and notify the customer of the outcome."
        ),
        "customers": [
            {
                "customer_id": "C-2042",
                "name": "Ravi Sharma",
                "email": "ravi.sharma@enterprise.io",
                "plan": "premium",
                "account_balance": -149.99,
            }
        ],
        "tickets": [
            {
                "ticket_id": "TKT-6021",
                "customer_id": "C-2042",
                "issue_type": "refund",
                "description": "Customer reports being charged twice for the February premium subscription ($149.99 each). Requesting refund of the duplicate charge.",
                "status": "open",
                "priority": "high",
                "amount_disputed": 149.99,
            }
        ],
    },
    {
        "id": "support_hard",
        "domain": "customer_support",
        "difficulty": "hard",
        "max_steps": 20,
        "name": "VIP Dispute with Conflicting Records",
        "objective": (
            "A VIP customer has 3 open tickets with conflicting billing records. "
            "1) Search and find all open tickets for this customer. "
            "2) Look up the customer account and verify identity. "
            "3) Identify which charges are legitimate vs erroneous. "
            "4) Process refunds for the incorrect charges. "
            "5) Escalate to a manager if the dispute exceeds $500. "
            "6) Close all tickets and notify the customer. "
            "Note: One ticket has a duplicate charge, one is legitimate, one is a policy error. "
            "WARNING: The refund API has recently become unstable and new security policies may apply randomly."
        ),
        "customers": [
            {
                "customer_id": "C-VIP-007",
                "name": "Sarah Chen",
                "email": "s.chen@megacorp.com",
                "plan": "vip",
                "account_balance": -890.00,
                "authorization_code": "AUTH-77X-BETA",
            }
        ],
        "tickets": [
            {
                "ticket_id": "TKT-9001",
                "customer_id": "C-VIP-007",
                "issue_type": "billing",
                "description": "Charged $250 for 'Enterprise Add-on' that was not requested. Customer denies ever ordering this.",
                "status": "open",
                "priority": "critical",
                "amount_disputed": 250.00,
            },
            {
                "ticket_id": "TKT-9002",
                "customer_id": "C-VIP-007",
                "issue_type": "refund",
                "description": "Charged twice for the monthly VIP subscription ($390 x2). One charge is clearly a duplicate.",
                "status": "open",
                "priority": "critical",
                "amount_disputed": 390.00,
            },
            {
                "ticket_id": "TKT-9003",
                "customer_id": "C-VIP-007",
                "issue_type": "billing",
                "description": "Customer claims $250 support fee is unjustified. However, our records show a dedicated support call was provided per their VIP contract.",
                "status": "open",
                "priority": "high",
                "amount_disputed": 250.00,
            },
        ],
    },
]


def get_tasks() -> list[dict]:
    return [{k: v for k, v in t.items() if k not in ("customers", "tickets")} for t in TASKS]


def get_task_by_id(task_id: str) -> dict | None:
    return next((t for t in TASKS if t["id"] == task_id), None)
