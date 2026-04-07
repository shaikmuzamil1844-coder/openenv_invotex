"""Client for interacting with the OpenEnv Invotex environment.

Uses the official openenv EnvClient base class with WebSocket transport.

Team Invotex — Muzamil Shaik
Meta x PyTorch x HuggingFace OpenEnv Hackathon 2026
"""

from __future__ import annotations

from typing import Any

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult

try:
    from .models import EnvAction, EnvObservation
except ImportError:
    from models import EnvAction, EnvObservation


class MultiDomainEnv(EnvClient[EnvAction, EnvObservation, dict]):
    """EnvClient for the Invotex multi-domain environment.

    Supports all three domains: email_triage, traffic_control, customer_support.
    Switch domains via the DOMAIN environment variable on the server side.
    """

    def _step_payload(self, action: EnvAction) -> dict[str, Any]:
        """Convert EnvAction into the payload expected by the server."""
        return {
            "tool_name": action.tool_name,
            "tool_args": action.tool_args,
            "thought": action.thought,
        }

    def _parse_result(self, data: dict[str, Any]) -> StepResult[EnvObservation]:
        """Parse server response into an EnvObservation wrapped in StepResult."""
        observation_payload = dict(data.get("observation", {}))
        observation_payload.setdefault("reward", data.get("reward", 0.0))
        observation_payload.setdefault("done", data.get("done", False))
        observation_payload.setdefault("info", data.get("info", {}))
        observation_payload.setdefault("content", data.get("content", ""))

        observation = EnvObservation(**observation_payload)
        return StepResult(
            observation=observation,
            reward=data.get("reward", observation.reward),
            done=data.get("done", observation.done),
        )

    def _parse_state(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return the raw state payload."""
        return data
