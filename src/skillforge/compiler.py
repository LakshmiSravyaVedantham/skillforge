from __future__ import annotations

import json
from typing import Any

import anthropic

from skillforge.models import SkillManifest, StepConfig, TriggerConfig

_COMPILE_PROMPT = """You are an expert workflow engineer. \
Convert this plain English workflow description into a structured skill manifest.

Workflow: {description}

Return JSON only — no prose, no markdown fences:
{{
  "name": "<kebab-case-name>",
  "description": "<one-line description>",
  "trigger": {{
    "type": "cron|manual|webhook",
    "schedule": "<cron expr if type=cron, e.g. '0 9 * * 1-5' for weekdays at 9am>",
    "endpoint": "<URL path if type=webhook, otherwise empty>"
  }},
  "steps": [
    {{
      "name": "<snake_case_step_name>",
      "tool": "claude|github|slack|http|shell",
      "action": "<tool action if not claude>",
      "prompt": "<Claude prompt template, use {{variable}} for inputs>",
      "inputs": {{}},
      "output": "<variable name for step output>"
    }}
  ]
}}

Rules:
- type=cron for time-based ("every morning", "daily", "weekly")
- type=manual for on-demand workflows
- type=webhook for event-triggered
- Keep steps focused and minimal
- Maximum 6 steps
"""


class WorkflowCompiler:
    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        self.client = client or anthropic.Anthropic()

    def compile(self, description: str) -> SkillManifest:
        prompt = _COMPILE_PROMPT.format(description=description)
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            block = response.content[0]
            text = block.text.strip() if hasattr(block, "text") else ""
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:])
            if text.endswith("```"):
                text = "\n".join(text.split("\n")[:-1])
            data: dict[str, Any] = json.loads(text)
        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            raise ValueError(f"Failed to parse skill manifest: {e}") from e

        trigger_data = data.get("trigger", {})
        trigger = TriggerConfig(
            type=trigger_data.get("type", "manual"),
            schedule=trigger_data.get("schedule", ""),
            endpoint=trigger_data.get("endpoint", ""),
        )

        steps = [
            StepConfig(
                name=s.get("name", ""),
                tool=s.get("tool", ""),
                action=s.get("action", ""),
                prompt=s.get("prompt", ""),
                inputs=s.get("inputs", {}),
                output=s.get("output", ""),
            )
            for s in data.get("steps", [])
        ]

        return SkillManifest(
            name=data.get("name", "unnamed-skill"),
            description=data.get("description", ""),
            trigger=trigger,
            steps=steps,
        )
