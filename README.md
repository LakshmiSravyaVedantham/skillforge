# skillforge

Describe workflows in plain English. Get production-ready automated agents — Python scripts you own, YAML manifests you understand.

[![CI](https://github.com/LakshmiSravyaVedantham/skillforge/actions/workflows/ci.yml/badge.svg)](https://github.com/LakshmiSravyaVedantham/skillforge/actions/workflows/ci.yml)

## The Problem

Everyone has repetitive AI-powered workflows. Setting them up as automated agents requires coding, API auth, cron setup, and infra knowledge. Most people do it manually forever.

## The Solution

Describe your workflow once. skillforge compiles it into a Python script + YAML manifest you own and can run anywhere.

## Quickstart

```bash
pip install skillforge
export ANTHROPIC_API_KEY=your_key

skillforge new "every morning at 9am, summarize open PRs and post to Slack"
skillforge run morning-standup
skillforge deploy morning-standup
```

## Community Skills

Install pre-built skills:

```bash
# 5 skills ship with skillforge
ls skills/

skillforge install morning-standup
skillforge install hn-monitor
skillforge install github-digest
```

## CLI Reference

```bash
skillforge new "description"      # Compile a new skill
skillforge list                   # Show all saved skills
skillforge run <name>             # Execute locally
skillforge deploy <name>          # Generate GitHub Actions workflow
skillforge deploy <name> --dry-run # Preview without writing
```

## What you get

Two files per skill:

**skill.yaml** — human-readable manifest:
```yaml
name: morning-standup
trigger:
  type: cron
  schedule: "0 9 * * 1-5"
steps:
  - name: fetch_prs
    tool: github
    ...
```

**skill.py** — runnable Python you can edit freely.

## Not a platform

skillforge generates code you own. No SaaS, no subscription, no lock-in. The generated Python runs anywhere Python runs.

## License

MIT
