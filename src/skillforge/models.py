from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TriggerConfig:
    type: str  # "cron" | "manual" | "webhook"
    schedule: str = ""  # cron expression if type==cron
    endpoint: str = ""  # URL path if type==webhook


@dataclass
class StepConfig:
    name: str
    tool: str  # "claude" | "github" | "slack" | "http" | "shell"
    action: str = ""
    prompt: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    output: str = ""


@dataclass
class SkillManifest:
    name: str
    description: str
    trigger: TriggerConfig
    steps: list[StepConfig]
    version: str = "1.0"
