"""Builds the system prompt shown to the agent at the start of each episode."""

from __future__ import annotations


class SystemPromptBuilder:
    """Builds the system prompt for a domain by injecting available tool schemas."""

    @staticmethod
    def build(template: str, tools: dict) -> str:
        """Render a system prompt template with the list of available tools.

        Args:
            template: The domain's system prompt template string.
            tools: Mapping of tool_name -> tool metadata dict.

        Returns:
            Fully rendered system prompt string.
        """
        tool_lines = []
        for name, meta in tools.items():
            desc = meta.get("description", "No description.")
            schema = meta.get("schema")
            if schema:
                try:
                    fields = schema.model_fields
                    args = ", ".join(
                        f"{k}: {v.annotation.__name__ if hasattr(v.annotation, '__name__') else str(v.annotation)}"
                        for k, v in fields.items()
                    )
                    tool_lines.append(f"  - {name}({args}): {desc}")
                except Exception:
                    tool_lines.append(f"  - {name}: {desc}")
            else:
                tool_lines.append(f"  - {name}: {desc}")

        tools_section = "\n".join(tool_lines) if tool_lines else "  (no tools available)"
        return template.replace("{{TOOLS}}", tools_section)
