from __future__ import annotations

import importlib


def _make_env(monkeypatch):
    monkeypatch.setenv("DOMAIN", "email_triage")
    importlib.import_module("openenv_invotex.domains")
    module = importlib.import_module("openenv_invotex.server.environment")
    return module.MultiDomainEnvironment()


def _env_action(tool_name: str, tool_args: dict, thought: str = ""):
    module = importlib.import_module("openenv_invotex.models")
    return module.EnvAction(tool_name=tool_name, tool_args=tool_args, thought=thought)


def test_invalid_tool_gets_penalized(monkeypatch):
    env = _make_env(monkeypatch)
    env.reset(task_id="email_easy")

    obs = env.step(_env_action("hack_globals", {"x": 1}, thought="try exploit"))

    assert obs.done is False
    assert obs.reward <= -0.05
    assert "error" in (obs.info or {})
    assert "not a valid tool" in (obs.content or "")


def test_repeated_identical_action_is_penalized(monkeypatch):
    env = _make_env(monkeypatch)
    env.reset(task_id="email_easy")

    first = env.step(_env_action("fetch_emails", {"folder": "inbox"}))
    second = env.step(_env_action("fetch_emails", {"folder": "inbox"}))

    assert second.reward <= first.reward


def test_step_limit_hits_and_terminates(monkeypatch):
    env = _make_env(monkeypatch)
    env.reset(task_id="email_easy")

    final_obs = None
    for _ in range(8):
        final_obs = env.step(_env_action("fetch_emails", {"folder": "inbox"}))
        if final_obs.done:
            break

    assert final_obs is not None
    assert final_obs.done is True
    assert final_obs.info.get("step_limit_hit") is True
