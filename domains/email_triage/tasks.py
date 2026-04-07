"""Task definitions for the Email Triage domain.

Each task defines the scenario seeded into the DB and the objective
shown to the agent. Three difficulties: easy, medium, hard.
"""

from __future__ import annotations

from datetime import datetime, timedelta


TASKS = [
    {
        "id": "email_easy",
        "domain": "email_triage",
        "difficulty": "easy",
        "max_steps": 8,
        "name": "Basic Inbox Triage",
        "objective": (
            "You have 5 new emails in your inbox. "
            "Label each email correctly as 'urgent', 'routine', or 'spam'. "
            "Move spam emails to the spam folder. "
            "Move urgent emails to the urgent folder."
        ),
        "emails": [
            {
                "email_id": "easy_001",
                "sender": "noreply@promo-deals.xyz",
                "subject": "You WON $10,000!!! Click NOW!!!",
                "body": "Congratulations! You have been selected for a cash prize...",
                "priority": "spam",
                "sla_hours": None,
            },
            {
                "email_id": "easy_002",
                "sender": "cto@company.com",
                "subject": "URGENT: Production server down",
                "body": "Our main API is returning 503 errors. Users impacted. Fix ASAP.",
                "priority": "urgent",
                "sla_hours": 1,
            },
            {
                "email_id": "easy_003",
                "sender": "hr@company.com",
                "subject": "Team lunch this Friday",
                "body": "Hey team, we're doing a team lunch at 1pm on Friday. Please RSVP.",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "easy_004",
                "sender": "billing@vendor.com",
                "subject": "Invoice #4821 Due",
                "body": "Please find attached your invoice for March services. Due in 30 days.",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "easy_005",
                "sender": "alerts@monitoring.io",
                "subject": "CRITICAL: Disk usage at 95% on prod-db-01",
                "body": "Disk usage has reached 95%. Immediate action required to prevent data loss.",
                "priority": "urgent",
                "sla_hours": 2,
            },
        ],
    },
    {
        "id": "email_medium",
        "domain": "email_triage",
        "difficulty": "medium",
        "max_steps": 14,
        "name": "Mixed Inbox with Auto-Reply",
        "objective": (
            "You have 8 emails in your inbox with mixed priorities. "
            "1) Label each email (urgent/routine/spam). "
            "2) Move emails to appropriate folders. "
            "3) Draft a reply for all urgent emails confirming receipt and next steps. "
            "4) Mark spam emails appropriately."
        ),
        "emails": [
            {
                "email_id": "med_001",
                "sender": "ceo@company.com",
                "subject": "Board meeting postponed - need your input",
                "body": "The board meeting moved to next week. Please send me your Q1 summary by EOD.",
                "priority": "urgent",
                "sla_hours": 8,
            },
            {
                "email_id": "med_002",
                "sender": "newsletter@techdigest.io",
                "subject": "Your weekly tech roundup",
                "body": "This week in tech: AI breakthroughs, new frameworks, and more...",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "med_003",
                "sender": "security@company.com",
                "subject": "URGENT: Suspicious login detected on your account",
                "body": "We detected a login from an unknown IP address. Immediate verification required.",
                "priority": "urgent",
                "sla_hours": 1,
            },
            {
                "email_id": "med_004",
                "sender": "deals@shopfast.com",
                "subject": "50% OFF Everything Today Only!!!",
                "body": "Don't miss out! Shop now for incredible savings...",
                "priority": "spam",
                "sla_hours": None,
            },
            {
                "email_id": "med_005",
                "sender": "devops@company.com",
                "subject": "Deployment scheduled for tonight",
                "body": "Reminder: prod deployment v2.4.1 scheduled for 11pm. Please be on standby.",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "med_006",
                "sender": "client@bigcorp.com",
                "subject": "Contract renewal - urgent decision needed",
                "body": "Our current contract expires in 48 hours. We need a response to proceed.",
                "priority": "urgent",
                "sla_hours": 4,
            },
            {
                "email_id": "med_007",
                "sender": "lottery@winbig.biz",
                "subject": "Claim your prize immediately!",
                "body": "You have been randomly selected as a winner. Click to claim.",
                "priority": "spam",
                "sla_hours": None,
            },
            {
                "email_id": "med_008",
                "sender": "it-support@company.com",
                "subject": "Your ticket #7821 has been resolved",
                "body": "Your IT support ticket regarding VPN access has been resolved.",
                "priority": "routine",
                "sla_hours": None,
            },
        ],
    },
    {
        "id": "email_hard",
        "domain": "email_triage",
        "difficulty": "hard",
        "max_steps": 22,
        "name": "Multi-Thread Escalation with SLA Check",
        "objective": (
            "You have a complex multi-department email chain with SLA deadlines. "
            "1) Triage all 12 emails by priority. "
            "2) Check SLA status for all time-sensitive emails. "
            "3) Escalate any emails with breached or at-risk SLAs. "
            "4) Draft appropriate responses for urgent and escalated emails. "
            "5) Archive routine emails that require no action. "
            "Goal: Zero unaddressed urgent emails, all SLA breaches escalated."
        ),
        "emails": [
            {
                "email_id": "hard_001",
                "sender": "legal@partner.com",
                "subject": "CONTRACT BREACH NOTICE - immediate response required",
                "body": "We are issuing a formal breach notice. You have 24 hours to respond or we escalate to litigation.",
                "priority": "urgent",
                "sla_hours": 24,
            },
            {
                "email_id": "hard_002",
                "sender": "ops-lead@company.com",
                "subject": "Re: Re: Re: Database migration - who approved this?",
                "body": "This has gone back and forth 3 times. Engineering says approved, Finance says not approved.",
                "priority": "urgent",
                "sla_hours": 4,
            },
            {
                "email_id": "hard_003",
                "sender": "finance@company.com",
                "subject": "Month-end close reminder",
                "body": "Please submit all expense reports by Friday 5pm for month-end closing.",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "hard_004",
                "sender": "customer-vip@topaccount.com",
                "subject": "Service degradation - we're losing money",
                "body": "Our SLA guarantees 99.9% uptime. We've had 4 hours of downtime this week. This is unacceptable.",
                "priority": "urgent",
                "sla_hours": 2,
            },
            {
                "email_id": "hard_005",
                "sender": "hr@company.com",
                "subject": "Performance review season begins",
                "body": "Annual performance reviews start next month. Please schedule 1:1s with your team.",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "hard_006",
                "sender": "security-audit@compliance.gov",
                "subject": "Compliance audit request - respond within 48 hours",
                "body": "As part of the annual security audit, please provide access logs for the past 90 days.",
                "priority": "urgent",
                "sla_hours": 48,
            },
            {
                "email_id": "hard_007",
                "sender": "marketing@company.com",
                "subject": "Campaign performance report",
                "body": "Q1 campaign results are attached. Overall positive, click-through up 12%.",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "hard_008",
                "sender": "noreply@promo-spam.xyz",
                "subject": "Incredible offer just for you!!!",
                "body": "Limited time! Act now! This offer expires in 1 hour!!!",
                "priority": "spam",
                "sla_hours": None,
            },
            {
                "email_id": "hard_009",
                "sender": "engineering-lead@company.com",
                "subject": "P0 incident: memory leak in production",
                "body": "We have a confirmed memory leak causing gradual service degradation. Needs immediate team response.",
                "priority": "urgent",
                "sla_hours": 1,
            },
            {
                "email_id": "hard_010",
                "sender": "vendor-support@cloudprovider.com",
                "subject": "Scheduled maintenance window",
                "body": "Maintenance window: April 8, 2am-4am UTC. Some services may be unavailable.",
                "priority": "routine",
                "sla_hours": None,
            },
            {
                "email_id": "hard_011",
                "sender": "cfo@company.com",
                "subject": "Budget freeze - no new spend until further notice",
                "body": "Due to market conditions, all discretionary budget is frozen effective immediately.",
                "priority": "urgent",
                "sla_hours": 8,
            },
            {
                "email_id": "hard_012",
                "sender": "offers@newsletter.spam.io",
                "subject": "You've been pre-approved!",
                "body": "Claim your pre-approved offer today. No credit check needed!",
                "priority": "spam",
                "sla_hours": None,
            },
        ],
    },
]


def get_tasks() -> list[dict]:
    """Return task definitions (without the seed email data)."""
    return [
        {k: v for k, v in t.items() if k != "emails"}
        for t in TASKS
    ]


def get_task_by_id(task_id: str) -> dict | None:
    """Return the full task dict including emails, or None if not found."""
    return next((t for t in TASKS if t["id"] == task_id), None)
