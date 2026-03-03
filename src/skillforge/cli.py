from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from skillforge import __version__
from skillforge.compiler import WorkflowCompiler
from skillforge.storage import list_skills, load_skill, save_skill


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """skillforge — compile plain English workflows into automated agents."""


@cli.command("new")
@click.argument("description")
@click.option(
    "--name",
    default=None,
    help="Skill name (kebab-case). Auto-generated if not provided.",
)
def new(description: str, name: str | None) -> None:
    """Create a new skill from a plain English description."""
    click.echo(f"Compiling skill: {description}")
    try:
        compiler = WorkflowCompiler()
        manifest = compiler.compile(description)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    if name:
        manifest.name = name

    click.echo(f"\nName: {manifest.name}")
    click.echo(
        f"Trigger: {manifest.trigger.type}"
        + (f" ({manifest.trigger.schedule})" if manifest.trigger.schedule else "")
    )
    click.echo(f"Steps ({len(manifest.steps)}):")
    for step in manifest.steps:
        click.echo(f"  - {step.name} [{step.tool}]")

    click.confirm("\nSave this skill?", abort=True)
    skill_dir = save_skill(manifest)
    click.echo(f"\nSaved to {skill_dir}")
    click.echo("  skill.yaml — manifest")
    click.echo("  skill.py   — runnable Python")
    click.echo(f"\nRun it: skillforge run {manifest.name}")


@cli.command("list")
def list_cmd() -> None:
    """List all saved skills."""
    skills = list_skills()
    if not skills:
        click.echo("No skills yet. Create one with: skillforge new 'description'")
        return
    for name in skills:
        manifest = load_skill(name)
        trigger = f"[{manifest.trigger.type}]" if manifest else ""
        click.echo(f"  {name} {trigger}")


@cli.command("run")
@click.argument("name")
def run(name: str) -> None:
    """Run a skill locally."""
    manifest = load_skill(name)
    if not manifest:
        raise click.ClickException(
            f"Skill '{name}' not found. Run 'skillforge list' to see available skills."
        )

    from skillforge.storage import _DEFAULT_BASE

    skill_py = _DEFAULT_BASE / name / "skill.py"
    click.echo(f"Running {name}...")
    result = subprocess.run([sys.executable, str(skill_py)], capture_output=False)
    sys.exit(result.returncode)


@cli.command("deploy")
@click.argument("name")
@click.option("--dry-run", is_flag=True, help="Print workflow without writing")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("."),
    show_default=True,
)
def deploy(name: str, dry_run: bool, output_dir: Path) -> None:
    """Deploy a skill as a GitHub Actions workflow."""
    manifest = load_skill(name)
    if not manifest:
        raise click.ClickException(f"Skill '{name}' not found.")

    schedule = manifest.trigger.schedule or "0 9 * * 1-5"
    workflow = f"""\
name: {manifest.name}
# {manifest.description}

on:
  workflow_dispatch:
{f'  schedule:\\n    - cron: "{schedule}"' if manifest.trigger.type == "cron" else ""}

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install skillforge
        run: pip install skillforge
      - name: Install skill
        run: skillforge install-local {name}
      - name: Run skill
        env:
          ANTHROPIC_API_KEY: ${{{{ secrets.ANTHROPIC_API_KEY }}}}
          SLACK_WEBHOOK_URL: ${{{{ secrets.SLACK_WEBHOOK_URL }}}}
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: skillforge run {name}
"""
    if dry_run:
        click.echo(workflow)
        return

    workflow_dir = output_dir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_path = workflow_dir / f"{name}.yml"
    workflow_path.write_text(workflow)
    click.echo(f"Written: {workflow_path}")
    click.echo("Add required secrets to your repo, then push.")


@cli.command("install-local")
@click.argument("name")
def install_local(name: str) -> None:
    """Install a skill from the current directory (used in CI)."""
    skill_dir = Path(".skillforge") / name
    if not skill_dir.exists():
        raise click.ClickException(f"No .skillforge/{name}/ directory found.")
    from skillforge.storage import _DEFAULT_BASE

    target = _DEFAULT_BASE / name
    target.mkdir(parents=True, exist_ok=True)
    for f in skill_dir.glob("*"):
        (target / f.name).write_bytes(f.read_bytes())
    click.echo(f"Installed {name}")
