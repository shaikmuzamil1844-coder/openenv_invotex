"""Abstract base class that all domain plugins must implement.

Team Invotex — Meta x PyTorch x HuggingFace OpenEnv Hackathon 2026
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDomain(ABC):
    """Contract that every domain plugin must satisfy.

    Each domain must expose:
      - get_tools()               → dict of tool_name → tool metadata
      - get_tasks()               → list of task dicts
      - get_graders()             → list of grader objects
      - seed_episode(task_id, session) → dict with 'description' key
      - compute_step_reward(...)  → float reward for this step
      - is_done(...)              → bool indicating episode completion
      - get_system_prompt_template() → string with {{TOOLS}} placeholder
      - create_tables(engine)     → create any needed SQLAlchemy tables
    """

    @abstractmethod
    def get_tools(self) -> dict[str, dict[str, Any]]:
        """Return mapping of tool_name to tool metadata.

        Each value must be a dict with keys:
          - 'func': callable(args_schema_instance, session) -> str
          - 'schema': Pydantic BaseModel class for validating args
          - 'description': str describing the tool
        """
        raise NotImplementedError

    @abstractmethod
    def get_tasks(self) -> list[dict[str, Any]]:
        """Return list of task dicts. Each must have at minimum:
          - 'id': str — unique task identifier
          - 'difficulty': str — 'easy', 'medium', or 'hard'
          - 'max_steps': int — step budget
          - 'name': str — human-readable task name
          - 'objective': str — what the agent must accomplish
        """
        raise NotImplementedError

    @abstractmethod
    def get_graders(self) -> list[Any]:
        """Return list of grader objects.

        Each grader must implement:
          grade(trajectory: list[dict], session: Any) -> dict with 'score' key
        """
        raise NotImplementedError

    @abstractmethod
    def seed_episode(self, task_id: str, session: Any) -> dict[str, Any]:
        """Seed the database with episode-specific data.

        Must return a dict with at minimum:
          - 'description': str — the task description shown to the agent
        """
        raise NotImplementedError

    @abstractmethod
    def compute_step_reward(
        self,
        tool_name: str,
        result: str,
        session: Any,
        step_count: int,
    ) -> float:
        """Compute the immediate reward for this step.

        Args:
            tool_name: The tool that was called.
            result: The string result from the tool.
            session: Active DB session.
            step_count: Current step number in the episode.

        Returns:
            Float reward, typically in [-0.1, 0.3].
        """
        raise NotImplementedError

    @abstractmethod
    def is_done(self, tool_name: str, result: str, session: Any) -> bool:
        """Return True if the episode should terminate after this step."""
        raise NotImplementedError

    @abstractmethod
    def get_system_prompt_template(self) -> str:
        """Return the system prompt template for this domain.

        Use {{TOOLS}} as a placeholder — it will be replaced with the
        list of available tools by SystemPromptBuilder.
        """
        raise NotImplementedError

    @abstractmethod
    def create_tables(self, engine: Any) -> None:
        """Create any SQLAlchemy tables required by this domain."""
        raise NotImplementedError
