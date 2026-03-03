from pathlib import Path

from skillforge.models import SkillManifest, StepConfig, TriggerConfig
from skillforge.storage import list_skills, load_skill, save_skill


def _make_manifest(name: str = "test-skill") -> SkillManifest:
    return SkillManifest(
        name=name,
        description="Test skill",
        trigger=TriggerConfig(type="manual"),
        steps=[
            StepConfig(name="step1", tool="shell", action="echo hello", output="out")
        ],
    )


def test_save_and_load_skill(tmp_path: Path) -> None:
    manifest = _make_manifest()
    save_skill(manifest, base_dir=tmp_path)
    loaded = load_skill("test-skill", base_dir=tmp_path)
    assert loaded is not None
    assert loaded.name == "test-skill"
    assert loaded.trigger.type == "manual"


def test_save_creates_yaml_and_python(tmp_path: Path) -> None:
    manifest = _make_manifest()
    save_skill(manifest, base_dir=tmp_path)
    skill_dir = tmp_path / "test-skill"
    assert (skill_dir / "skill.yaml").exists()
    assert (skill_dir / "skill.py").exists()


def test_load_skill_returns_none_when_absent(tmp_path: Path) -> None:
    result = load_skill("nonexistent", base_dir=tmp_path)
    assert result is None


def test_list_skills_returns_saved_skills(tmp_path: Path) -> None:
    save_skill(_make_manifest("skill-a"), base_dir=tmp_path)
    save_skill(_make_manifest("skill-b"), base_dir=tmp_path)
    names = list_skills(base_dir=tmp_path)
    assert "skill-a" in names
    assert "skill-b" in names
