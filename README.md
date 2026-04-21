---
title: OpenEnv Invotex
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
base_path: /web
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - llm-evaluation
  - multi-domain
---

# OpenEnv Invotex — Multi-Domain RL Environment

> **Team:** Invotex | **Author:** Muzamil Shaik  
> **Hackathon:** Meta × PyTorch × Hugging Face × Scaler — OpenEnv Hackathon 2026

---

## What This Environment Does

A containerized **OpenEnv-compliant multi-domain RL environment** for evaluating LLM agents on
real-world professional workflows. Switch domains via one environment variable — same container, same API.

**Live Space:** `https://muzamil1844-openenv-invotex.hf.space`  
**Live Web UI:** `https://muzamil1844-openenv-invotex.hf.space/web/`  
**Health Check:** `https://muzamil1844-openenv-invotex.hf.space/health`

---

## Domains

| Domain | Description | Tools | Tasks |
|--------|-------------|-------|-------|
| `email_triage` | AI triages inbox: label, sort, escalate, auto-reply, SLA check | 7 | 3 |
| `traffic_control` | AI manages smart city intersections with emergency corridors | 7 | 3 |
| `customer_support` | AI resolves billing disputes, refunds, escalation workflows | 7 | 3 |

Each domain has **easy / medium / hard** tasks.

### Email Triage Tasks
| Task | Difficulty | Objective | Max Steps |
|------|-----------|-----------|-----------|
| `email_easy` | Easy | Sort 5 emails by priority, move spam | 8 |
| `email_medium` | Medium | Mixed inbox with auto-reply drafting | 14 |
| `email_hard` | Hard | Multi-thread escalation with SLA checks | 22 |

### Traffic Control Tasks
| Task | Difficulty | Objective | Max Steps |
|------|-----------|-----------|-----------|
| `traffic_easy` | Easy | Clear single intersection queue | 8 |
| `traffic_medium` | Medium | Emergency vehicle corridor management | 14 |
| `traffic_hard` | Hard | Peak hour multi-intersection grid | 24 |

### Customer Support Tasks
| Task | Difficulty | Objective | Max Steps |
|------|-----------|-----------|-----------|
| `support_easy` | Easy | Resolve billing inquiry | 6 |
| `support_medium` | Medium | Refund with identity verification | 12 |
| `support_hard` | Hard | VIP multi-ticket dispute with escalation | 20 |

---

## Quick Start

### Local Docker
```bash
docker build -t invotex-env .

# Run email triage domain
docker run -p 7860:7860 -e DOMAIN=email_triage invotex-env

# Run traffic control domain
docker run -p 7860:7860 -e DOMAIN=traffic_control invotex-env

# Run customer support domain
docker run -p 7860:7860 -e DOMAIN=customer_support invotex-env
```

### Local Python (no Docker)
```bash
pip install "openenv-core[core]>=0.2.1" sqlalchemy fastapi uvicorn openai pydantic prometheus-client

DOMAIN=email_triage uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Validate with OpenEnv CLI
```bash
pip install openenv-core
DOMAIN=email_triage openenv validate --verbose
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check + registered domains |
| `/tasks` | GET | Domain tasks and action schema |
| `/reset` | POST | Start a new episode (optional `task_id`) |
| `/step` | POST | Execute one environment action |
| `/state` | GET | Current episode metadata |
| `/baseline` | POST | Run the built-in scripted baseline agent |
| `/grader` | POST | Score a trajectory externally |
| `/metrics` | GET | Prometheus metrics |
| `/web/metadata` | GET | Web UI metadata |
| `/web/reset` | POST | Reset for the browser UI |
| `/web/step` | POST | Step for the browser UI |
| `/web/state` | GET | Browser UI state |

---

## Action & Observation Format

### Action
```json
{
  "tool_name": "label_email",
  "tool_args": {"email_id": "easy_002", "label": "urgent"},
  "thought": "Production server down emails should be labeled urgent."
}
```

### Observation
```json
{
  "content": "Email 'easy_002' labeled as 'urgent'.",
  "done": false,
  "reward": 0.05,
  "info": {
    "step_count": 3,
    "task_id": "email_easy",
    "trace_id": "uuid",
    "domain": "email_triage",
    "grader_score": null
  }
}
```

`grader_score` is only present on terminal (done=true) observations.

---

## Running Inference

### Required Environment Variables
- `OPENAI_API_KEY`: OpenAI or compatible API key (or fall back to `HF_TOKEN`)
- `API_BASE_URL`: LLM endpoint, default `https://api.openai.com/v1`
- `MODEL_NAME`: model id, default `gpt-4o-mini`
- `HF_TOKEN`: HuggingFace token (used as fallback for `OPENAI_API_KEY`)
- `HF_SPACE_URL`: environment base URL, default `http://localhost:7860`
- `DOMAIN`: `email_triage`, `traffic_control`, or `customer_support`

### Run Against Local Docker
```bash
docker run -p 7860:7860 -e DOMAIN=email_triage invotex-env &
OPENAI_API_KEY=sk-... DOMAIN=email_triage python inference.py
```

### Run Against Live HF Space
```bash
OPENAI_API_KEY=sk-... \
HF_SPACE_URL=https://muzamil1844-openenv-invotex.hf.space \
DOMAIN=email_triage python inference.py
```

### OpenAI-Compatible Providers

OpenRouter example:
```bash
OPENAI_API_KEY=sk-or-v1-... API_BASE_URL=https://openrouter.ai/api/v1 \
MODEL_NAME=meta-llama/llama-3.1-70b-instruct \
HF_SPACE_URL=https://muzamil1844-openenv-invotex.hf.space \
DOMAIN=email_triage python inference.py
```

Groq example:
```bash
OPENAI_API_KEY=gsk_... API_BASE_URL=https://api.groq.com/openai/v1 \
MODEL_NAME=llama-3.1-8b-instant \
HF_SPACE_URL=https://muzamil1844-openenv-invotex.hf.space \
DOMAIN=email_triage python inference.py
```

---

## Baseline Scores

> Baseline evaluated at `temperature=0.0` using `gpt-4o-mini`. All grader outputs clamped to `[0.0, 1.0]`.

| Domain | Easy | Medium | Hard | Average |
|--------|------|--------|------|---------|
| `email_triage` | 0.8000 | 0.7500 | 0.6500 | **0.7333** |
| `traffic_control` | 0.7500 | 0.7000 | 0.6000 | **0.6833** |
| `customer_support` | 0.8500 | 0.7500 | 0.6500 | **0.7500** |

Configuration:
- Model: `gpt-4o-mini`
- Temperature: `0.0`
- Response format: JSON object

---

## Tools by Domain

### 📧 Email Triage
- `fetch_emails(folder)` — list inbox/folder contents
- `label_email(email_id, label)` — assign urgent/routine/spam
- `move_to_folder(email_id, folder)` — route to correct folder
- `draft_reply(email_id, reply_body)` — draft a reply
- `escalate_email(email_id, reason)` — escalate to supervisor
- `mark_spam(email_id)` — mark as spam
- `check_sla_status(task_id)` — check SLA deadlines

### 🚦 Traffic Control
- `get_intersection_state(intersection_id)` — current signal state
- `set_signal_phase(intersection_id, phase, direction, duration_seconds)` — change signal
- `dispatch_emergency_corridor(intersection_id, emergency_direction)` — emergency green lane
- `get_vehicle_queue(intersection_id, direction)` — vehicle queue lengths
- `reroute_traffic(intersection_id, from_direction, to_direction)` — divert traffic
- `set_pedestrian_crossing(intersection_id, active)` — pedestrian signals
- `get_traffic_metrics(task_id)` — overall metrics

### 📞 Customer Support
- `search_tickets(query)` — find tickets by name/email/ID
- `lookup_customer(customer_id)` — customer account details
- `verify_identity(customer_id, email)` — identity verification before refund
- `process_refund(ticket_id, amount, reason)` — process refund
- `escalate_to_manager(ticket_id, reason)` — escalate to senior manager
- `close_ticket(ticket_id, resolution)` — close with resolution summary
- `send_notification(customer_id, message)` — notify customer

---

## Grading

Each domain has **2 deterministic code graders** averaged to a final score `[0.0 – 1.0]`:

| Domain | Grader 1 | Grader 2 |
|--------|----------|----------|
| Email Triage | Label Accuracy (correct labels/total) | Workflow Completion (routing + escalation + replies) |
| Traffic Control | Emergency Clearance (emergency vehicles cleared) | Traffic Flow (vehicles cleared / wait time reduction) |
| Customer Support | Ticket Resolution (closed + refunds + escalations) | Customer Satisfaction (identity check + notifications + efficiency) |

Grader audit coverage:
- Determinism — same trajectory always scores identically
- Score bounds — always in `[0.0, 1.0]`
- Session isolation — episodes don't bleed into each other
- Malformed/partial trajectories — handled gracefully
- Exploit resistance — repeated identical tools penalised

---

## Tests

```bash
# Unit tests
PYTHONPATH=. pytest tests/unit -q

# Integration tests (full episode runs)
PYTHONPATH=. pytest tests/integration -q
```

---

## Deploying to HuggingFace Spaces

```bash
pip install huggingface_hub openenv-core
huggingface-cli login

openenv push . --repo-id muzamil1844/openenv_invotex --exclude .hfignore
```

Add Space secrets on the HuggingFace dashboard:
- `DOMAIN` = `email_triage` (or whichever domain you want live)

---

## Project Structure

```
openenv_invotex/
├── openenv.yaml              # OpenEnv manifest (9 tasks across 3 domains)
├── pyproject.toml            # Python dependencies
├── Dockerfile                # HF Spaces compatible build (UID 1000, port 7860)
├── models.py                 # EnvAction + EnvObservation types
├── baseline.py               # Scripted baseline agent runner
├── client.py                 # EnvClient WebSocket client
├── inference.py              # LLM evaluation runner (competition script)
├── domains/
│   ├── base_domain.py        # Abstract BaseDomain interface
│   ├── email_triage/         # 3 tasks, 7 tools, 2 graders
│   ├── traffic_control/      # 3 tasks, 7 tools, 2 graders
│   └── customer_support/     # 3 tasks, 7 tools, 2 graders
├── server/
│   ├── app.py                # FastAPI entrypoint
│   ├── environment.py        # MultiDomainEnvironment engine
│   ├── domain_registry.py    # DomainRegistry singleton
│   ├── system_prompt_builder.py
│   └── utils/                # DB, logging, Prometheus metrics
└── tests/
    ├── unit/                 # Unit tests for tools and graders
    └── integration/          # Full episode integration tests
```

---

*Built with ❤️ by Team Invotex (Muzamil Shaik) for the Meta × PyTorch × HuggingFace OpenEnv Hackathon 2026.*

---

## 📝 Mini-Blog: How We Built OpenEnv Invotex

*by Muzamil Shaik, Team Invotex — Meta × PyTorch × HuggingFace OpenEnv Hackathon 2026*

### The Problem with Existing RL Environments

Every popular RL benchmark like WebArena or ALFWorld tests agents in a *perfect, static world*. APIs never change their contracts, business rules never update, and systems never fail in unexpected ways. But anyone who has worked in enterprise software knows this is completely unrealistic.

We asked ourselves: **what happens when an AI agent hits a real enterprise system where the rules suddenly change?**

### What We Built

We built **OpenEnv Invotex** — a fully containerized, multi-domain RL environment targeting Theme 3.1 (World Modeling / Professional Tasks) with a special focus on **Schema Drift**, the Patronus AI bonus mechanic.

The environment spans **3 enterprise domains**, each with 3 difficulty levels (Easy → Medium → Hard):

- 📧 **Email Triage** — the AI manages a realistic inbox with SLA deadlines, spam filters, and urgent escalation workflows
- 🚦 **Traffic Control** — the AI controls city intersections using physics-based queue simulation, emergency corridors, and pedestrian safety
- 📞 **Customer Support** — the AI resolves billing disputes, verifies identities, processes refunds, and handles escalations

All 3 domains share the same FastAPI engine, the same OpenEnv-compliant API, and the same Docker container. Switch domains with a single environment variable.

### The Crown Jewel: Schema Drift

In the `support_hard` task, we introduced **Schema Drift** — a dynamic API failure mechanic. When an agent tries to process a refund, it gets hit with:

```
API ERROR: 403 Forbidden - Schema Validation Failed.
The /v2/refunds endpoint now requires an 'authorization_code' parameter.
Transaction blocked by Security policy.
```

No warning. No hint about where to find the code. The agent must:
1. Read and understand the cryptic API error
2. Deduce it needs a dynamic `authorization_code`
3. Pivot to use `lookup_customer` to retrieve it from the database
4. Retry `process_refund` with the discovered code

A standard LLM loops on the 403 error and fails. An intelligent, adaptive agent recovers in 2 steps and scores full marks. **This is exactly the kind of real-world adaptability that enterprise AI needs.**

### Training Pipeline

We used **Unsloth + HuggingFace TRL** to fine-tune Llama-3 8B against our live environment. The training notebook (`scripts/train_unsloth.ipynb`) connects directly to our HuggingFace Space deployment, pulling real episode trajectories and training on successful Schema Drift recovery patterns.

**Before training:** Qwen-72B baseline scores 0.0 on `support_hard` — completely fails Schema Drift.
**After fine-tuning:** The model learns to use `lookup_customer` as a recovery step and scores above 0.7 consistently.

### Try It Yourself

🔗 **Live Space:** https://huggingface.co/spaces/muzamil1844/openenv_invotex
🔗 **GitHub:** https://github.com/shaikmuzamil1844-coder/openenv_invotex

```python
from openenv import EnvEnv, EnvAction

with EnvEnv.from_env("muzamil1844/openenv_invotex") as env:
    obs = await env.reset()
    result = await env.step(EnvAction(tool_name="fetch_emails", tool_args={"folder": "inbox"}))
    print(result)
```
