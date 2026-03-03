from pathlib import Path

from skillforge.models import SkillManifest, StepConfig, TriggerConfig
from skillforge.serializer import manifest_to_python, manifest_to_yaml, yaml_to_manifest


def _make_manifest() -> SkillManifest:
    return SkillManifest(
        name="morning-standup",
        description="Post standup to Slack",
        trigger=TriggerConfig(type="cron", schedule="0 9 * * 1-5"),
        steps=[
            StepConfig(
                name="fetch", tool="github", action="list_open_prs", output="prs"
            ),
            StepConfig(
                name="post",
                tool="slack",
                action="post_message",
                inputs={"channel": "#standup"},
            ),
        ],
    )


def test_manifest_to_yaml_roundtrip(tmp_path: Path) -> None:
    manifest = _make_manifest()
    yaml_str = manifest_to_yaml(manifest)
    loaded = yaml_to_manifest(yaml_str)
    assert loaded.name == manifest.name
    assert loaded.trigger.type == "cron"
    assert len(loaded.steps) == 2


def test_manifest_to_yaml_contains_name(tmp_path: Path) -> None:
    manifest = _make_manifest()
    yaml_str = manifest_to_yaml(manifest)
    assert "morning-standup" in yaml_str


def test_manifest_to_python_generates_valid_python() -> None:
    import ast

    manifest = _make_manifest()
    code = manifest_to_python(manifest)
    # Should be parseable Python
    tree = ast.parse(code)
    assert tree is not None


def test_manifest_to_python_contains_step_names() -> None:
    manifest = _make_manifest()
    code = manifest_to_python(manifest)
    assert "fetch" in code
    assert "post" in code
