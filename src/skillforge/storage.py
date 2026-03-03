from __future__ import annotations

from pathlib import Path

from skillforge.models import SkillManifest
from skillforge.serializer import manifest_to_python, manifest_to_yaml, yaml_to_manifest

_DEFAULT_BASE = Path.home() / ".skillforge" / "skills"


def save_skill(manifest: SkillManifest, base_dir: Path | None = None) -> Path:
    base = base_dir or _DEFAULT_BASE
    skill_dir = base / manifest.name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "skill.yaml").write_text(manifest_to_yaml(manifest))
    (skill_dir / "skill.py").write_text(manifest_to_python(manifest))
    return skill_dir


def load_skill(name: str, base_dir: Path | None = None) -> SkillManifest | None:
    base = base_dir or _DEFAULT_BASE
    yaml_path = base / name / "skill.yaml"
    if not yaml_path.exists():
        return None
    try:
        return yaml_to_manifest(yaml_path.read_text())
    except Exception:
        return None


def list_skills(base_dir: Path | None = None) -> list[str]:
    base = base_dir or _DEFAULT_BASE
    if not base.exists():
        return []
    return [
        d.name
        for d in sorted(base.iterdir())
        if d.is_dir() and (d / "skill.yaml").exists()
    ]
