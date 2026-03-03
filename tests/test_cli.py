from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from skillforge.cli import cli
from skillforge.models import SkillManifest, StepConfig, TriggerConfig


def _make_manifest(name: str = "test-skill") -> SkillManifest:
    return SkillManifest(
        name=name,
        description="A test skill",
        trigger=TriggerConfig(type="manual"),
        steps=[StepConfig(name="step1", tool="shell", action="echo hi", output="out")],
    )


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_list_empty(tmp_path: Path) -> None:
    runner = CliRunner()
    with patch("skillforge.cli.list_skills", return_value=[]):
        result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No skills" in result.output


def test_cli_list_with_skills(tmp_path: Path) -> None:
    runner = CliRunner()
    manifest = _make_manifest()
    with patch("skillforge.cli.list_skills", return_value=["test-skill"]):
        with patch("skillforge.cli.load_skill", return_value=manifest):
            result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "test-skill" in result.output


def test_cli_new_saves_skill() -> None:
    runner = CliRunner()
    manifest = _make_manifest()
    with patch("skillforge.cli.WorkflowCompiler") as mock_cls:
        mock_compiler = MagicMock()
        mock_compiler.compile.return_value = manifest
        mock_cls.return_value = mock_compiler
        with patch("skillforge.cli.save_skill", return_value=Path("/tmp/test-skill")):
            result = runner.invoke(
                cli,
                ["new", "run a health check"],
                input="y\n",
            )
    assert result.exit_code == 0
    assert "test-skill" in result.output


def test_cli_new_aborts_on_no() -> None:
    runner = CliRunner()
    manifest = _make_manifest()
    with patch("skillforge.cli.WorkflowCompiler") as mock_cls:
        mock_compiler = MagicMock()
        mock_compiler.compile.return_value = manifest
        mock_cls.return_value = mock_compiler
        result = runner.invoke(
            cli,
            ["new", "run a health check"],
            input="n\n",
        )
    assert result.exit_code != 0


def test_cli_run_not_found() -> None:
    runner = CliRunner()
    with patch("skillforge.cli.load_skill", return_value=None):
        result = runner.invoke(cli, ["run", "nonexistent"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_cli_deploy_dry_run() -> None:
    runner = CliRunner()
    manifest = _make_manifest()
    manifest.trigger = TriggerConfig(type="cron", schedule="0 9 * * 1-5")
    with patch("skillforge.cli.load_skill", return_value=manifest):
        result = runner.invoke(cli, ["deploy", "test-skill", "--dry-run"])
    assert result.exit_code == 0
    assert "test-skill" in result.output


def test_cli_deploy_not_found() -> None:
    runner = CliRunner()
    with patch("skillforge.cli.load_skill", return_value=None):
        result = runner.invoke(cli, ["deploy", "ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_cli_install_local_missing_dir() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["install-local", "nonexistent"])
    assert result.exit_code != 0
    assert "No .skillforge" in result.output
