"""
Inference Script — Team Invotex (Muzamil Shaik)
Meta x PyTorch x HuggingFace OpenEnv Hackathon 2026

MANDATORY ENVIRONMENT VARIABLES:
  API_BASE_URL        The API endpoint for the LLM.
  MODEL_NAME          The model identifier to use for inference.
  HF_TOKEN            Your Hugging Face / API key.
  LOCAL_IMAGE_NAME    Local Docker image name (if using from_docker_image).

STDOUT FORMAT (mandatory — deviation = disqualification):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import List, Optional

from openai import OpenAI

# ── Required env vars ────────────────────────────────────────────────────────
IMAGE_NAME    = os.getenv("LOCAL_IMAGE_NAME", "")
API_KEY       = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY", "")
API_BASE_URL  = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME    = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_SPACE_URL  = os.getenv("HF_SPACE_URL", "http://localhost:7860")
DOMAIN        = os.getenv("DOMAIN", "email_triage")
BENCHMARK     = os.getenv("BENCHMARK", "openenv_invotex")

SUCCESS_SCORE_THRESHOLD = 0.5   # episode is "success" if grader_score >= 0.5

if not API_KEY:
    sys.exit(
        "ERROR: Set HF_TOKEN (or OPENAI_API_KEY) before running inference.py\n"
        "  Example (Windows): set HF_TOKEN=hf_... && python inference.py\n"
        "  Example (Linux):   HF_TOKEN=hf_... python inference.py"
    )

# ── Import environment client ─────────────────────────────────────────────────
try:
    import domains  # noqa: F401 — registers all domain plugins
    from client import MultiDomainEnv
    from models import EnvAction
    from server.domain_registry import DomainRegistry
except ImportError:
    from . import domains  # noqa: F401
    from .client import MultiDomainEnv
    from .models import EnvAction
    from .server.domain_registry import DomainRegistry


# ── Mandatory stdout loggers ──────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    """Emit the mandatory [START] line."""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Emit one mandatory [STEP] line immediately after env.step()."""
    error_val = error if error else "null"
    done_val  = str(done).lower()
    # Sanitise action — must be on one line, no newlines
    action_str = str(action).replace("\n", " ").replace("\r", "")[:120]
    print(
        f"[STEP] step={step} action={action_str} "
        f"reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Emit the mandatory [END] line — ALWAYS emitted, even on exception."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _extract_text(response) -> str:
    choice  = response.choices[0].message
    content = choice.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [i.get("text", "") for i in content if isinstance(i, dict) and i.get("type") == "text"]
        if parts:
            return "".join(parts)
    raise ValueError("OpenAI response contained no text content.")


def build_system_prompt(domain_name: str, task: dict) -> str:
    return (
        f"You are an expert {domain_name} agent completing the following task:\n\n"
        f"Task ID: {task['id']}\n"
        f"Difficulty: {task.get('difficulty', '?')}\n"
        f"Objective: {task.get('objective', 'See initial observation.')}\n\n"
        "At each step respond with a JSON object ONLY — no markdown, no extra text:\n"
        '{"tool_name": "<name>", "tool_args": {<args>}, "thought": "<reasoning>"}\n\n'
        "Rules:\n"
        "- Do NOT repeat the same tool call consecutively.\n"
        "- Complete ALL sub-tasks in the objective before stopping.\n"
    )


def get_action(client: OpenAI, messages: list) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=400,
    )
    raw = _extract_text(response)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"tool_name": "", "tool_args": {}, "thought": raw, "_parse_error": True}


# ── Episode runner ────────────────────────────────────────────────────────────

def run_episode(env, client: OpenAI, task: dict, domain_name: str) -> dict:
    """Run one complete episode. Returns result dict with score and rewards."""
    task_id    = task["id"]
    max_steps  = task.get("max_steps", 20)
    rewards:   List[float] = []
    steps_taken = 0
    score       = 0.0
    success     = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        # ── reset ─────────────────────────────────────────────────────────────
        result = env.reset(task_id=task_id)
        obs    = result.observation
        done   = result.done

        system_prompt = build_system_prompt(domain_name, task)
        messages = [
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": obs.content},
        ]

        last_tool_call        = None
        consecutive_repeats   = 0

        for step in range(1, max_steps + 1):
            if done:
                break

            # ── LLM decision ──────────────────────────────────────────────────
            action_dict = get_action(client, messages)
            tool_name   = action_dict.get("tool_name", "")
            tool_args   = action_dict.get("tool_args", {})
            thought     = action_dict.get("thought", "")

            # Detect infinite loops
            cur = (tool_name, json.dumps(tool_args, sort_keys=True))
            if cur == last_tool_call:
                consecutive_repeats += 1
                if consecutive_repeats >= 3:
                    print(f"[DEBUG] Loop detected — forcing episode end at step {step}", flush=True)
                    break
            else:
                consecutive_repeats = 0
            last_tool_call = cur

            # ── env.step ──────────────────────────────────────────────────────
            action      = EnvAction(tool_name=tool_name, tool_args=tool_args, thought=thought)
            step_result = env.step(action)
            obs         = step_result.observation
            reward      = float(step_result.reward or 0.0)
            done        = step_result.done
            error       = obs.info.get("error") if obs.info else None

            rewards.append(reward)
            steps_taken = step

            # Mandatory [STEP] log
            log_step(step=step, action=tool_name, reward=reward, done=done, error=error)

            messages.append({"role": "assistant", "content": json.dumps(action_dict)})
            messages.append({"role": "user",      "content": obs.content})

        # ── compute final score ───────────────────────────────────────────────
        grader_score = obs.info.get("grader_score") if obs.info else None
        if grader_score is not None:
            score = float(grader_score)
        elif rewards:
            score = sum(rewards) / len(rewards)
        else:
            score = 0.0

        score   = min(max(score, 0.0), 1.0)   # clamp to [0, 1]
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)
        score   = 0.0
        success = False

    finally:
        # Mandatory [END] — always emitted even on exception
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {"task_id": task_id, "score": score, "success": success, "steps": steps_taken}


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    print(f"[INFO] Team Invotex | Domain: {DOMAIN} | Model: {MODEL_NAME} | API: {API_BASE_URL}", flush=True)

    client  = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    domain  = DomainRegistry.require(DOMAIN)()
    tasks   = domain.get_tasks()

    env = MultiDomainEnv(base_url=HF_SPACE_URL).sync()
    all_results = []

    try:
        for task in tasks:
            print(f"\n{'='*60}", flush=True)
            print(f"[INFO] Running task: {task['id']} ({task.get('difficulty','?')})", flush=True)
            result = run_episode(env, client, task, DOMAIN)
            all_results.append(result)
    finally:
        try:
            env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}", flush=True)
    print(f"[SUMMARY] domain={DOMAIN} model={MODEL_NAME}", flush=True)
    for r in all_results:
        print(f"  task={r['task_id']} score={r['score']:.3f} success={str(r['success']).lower()} steps={r['steps']}", flush=True)
    avg = sum(r["score"] for r in all_results) / len(all_results) if all_results else 0.0
    print(f"  AVERAGE score={avg:.3f}", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
