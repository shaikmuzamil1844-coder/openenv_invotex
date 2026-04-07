"""Domain-agnostic Action and Observation types per the OpenEnv spec.

Team Invotex — Muzamil Shaik
Meta x PyTorch x HuggingFace OpenEnv Hackathon 2026
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, ConfigDict, Field, model_validator
import json
from typing import Any, Optional


class EnvAction(Action):
    """Universal action type. Pick a tool name and pass its args."""

    tool_name: str = Field(..., description="Name of the tool to invoke")
    tool_args: dict = Field(
        default_factory=dict, description="Arguments validated against tool schema"
    )
    thought: str = Field(
        default="", description="Agent reasoning, logged but not executed"
    )

    @model_validator(mode='before')
    @classmethod
    def parse_gradio_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            args = data.get("tool_args")
            if isinstance(args, str):
                try:
                    data["tool_args"] = json.loads(args) if args.strip() else {}
                except json.JSONDecodeError:
                    pass
        return data


class EnvObservation(Observation):
    """Universal observation type. content is always human-readable text."""

    content: str = Field(
        ..., description="Tool result, error message, or initial task description"
    )
    done: bool = Field(..., description="True on terminal step")
    reward: float = Field(
        ...,
        description="Step reward. Negative for errors, positive for correct actions.",
    )
    info: dict = Field(
        default_factory=dict,
        description=(
            "Metadata. Contains step_count, task_id, trace_id. "
            "On terminal step: grader_score."
        ),
    )
