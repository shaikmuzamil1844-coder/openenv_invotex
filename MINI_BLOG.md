# 📝 Mini-Blog: How We Built OpenEnv Invotex

*by Team Invotex (Muzamil Shaik, Shaik Baba Azmath, Sanapathi Sai Kumar) — Meta × PyTorch × HuggingFace OpenEnv Hackathon 2026*

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
import asyncio
from openenv import EnvEnv, EnvAction

async def main():
    # Connect to our live Hugging Face Space Environment
    with EnvEnv.from_env("muzamil1844/openenv_invotex") as env:
        
        # 1. Start the Customer Support 'Schema Drift' episode
        obs = await env.reset(task_id="support_hard")
        
        # 2. Try to process a refund (This triggers the intentional 403 Error!)
        action1 = EnvAction(
            tool_name="process_refund", 
            tool_args={"ticket_id": "T-002", "amount": 50.0, "reason": "broken item"}
        )
        result1 = await env.step(action1)
        print("🚨 API ERROR:", result1.observation.content)
        
        # 3. Agent updates its World Model and pivots to get the auth code
        action2 = EnvAction(
            tool_name="lookup_customer", 
            tool_args={"customer_id": "C-002"}
        )
        result2 = await env.step(action2)
        print("✅ RECOVERY SUCCESS:", result2.observation.content)

# Run the simulation
asyncio.run(main())
```

---
**Thank you for evaluating our project! We had an amazing time building it at the hackathon.** 🙏
