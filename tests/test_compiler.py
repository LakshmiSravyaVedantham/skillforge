from unittest.mock import MagicMock

import pytest

from skillforge.compiler import WorkflowCompiler
from skillforge.models import SkillManifest


def _make_mock_client(response_text: str) -> MagicMock:
    mock_client = MagicMock()
    mock_content = MagicMock()
    mock_content.text = response_text
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    return mock_client


STANDUP_RESPONSE = """{
  "name": "morning-standup",
  "description": "Summarize open PRs and post to Slack every morning",
  "trigger": {"type": "cron", "schedule": "0 9 * * 1-5"},
  "steps": [
    {"name": "fetch_prs", "tool": "github", "action": "list_open_prs", "output": "prs"},
    {
      "name": "summarize",
      "tool": "claude",
      "prompt": "Summarize these PRs for standup: {prs}",
      "output": "summary"
    },
    {
      "name": "post",
      "tool": "slack",
      "action": "post_message",
      "inputs": {"channel": "#standup", "message": "{summary}"}
    }
  ]
}"""

MANUAL_RESPONSE = """{
  "name": "manual-check",
  "description": "Manual repo health check",
  "trigger": {"type": "manual"},
  "steps": [
    {"name": "check", "tool": "github", "action": "get_stats", "output": "stats"}
  ]
}"""


def test_compile_returns_skill_manifest() -> None:
    mock_client = _make_mock_client(STANDUP_RESPONSE)
    compiler = WorkflowCompiler(client=mock_client)
    manifest = compiler.compile("every morning summarize open PRs and post to Slack")
    assert isinstance(manifest, SkillManifest)
    assert manifest.name == "morning-standup"
    assert len(manifest.steps) == 3


def test_compile_sets_cron_trigger() -> None:
    mock_client = _make_mock_client(STANDUP_RESPONSE)
    compiler = WorkflowCompiler(client=mock_client)
    manifest = compiler.compile("every morning at 9am summarize PRs")
    assert manifest.trigger.type == "cron"
    assert manifest.trigger.schedule != ""


def test_compile_sets_manual_trigger() -> None:
    mock_client = _make_mock_client(MANUAL_RESPONSE)
    compiler = WorkflowCompiler(client=mock_client)
    manifest = compiler.compile("run a repo health check")
    assert manifest.trigger.type == "manual"


def test_compile_raises_on_invalid_json() -> None:
    mock_client = _make_mock_client("not json")
    compiler = WorkflowCompiler(client=mock_client)
    with pytest.raises(ValueError, match="Failed to parse"):
        compiler.compile("do something")


def test_compile_sends_description_in_prompt() -> None:
    mock_client = _make_mock_client(STANDUP_RESPONSE)
    compiler = WorkflowCompiler(client=mock_client)
    compiler.compile("summarize HN and email me")
    prompt = mock_client.messages.create.call_args[1]["messages"][0]["content"]
    assert "summarize HN and email me" in prompt
