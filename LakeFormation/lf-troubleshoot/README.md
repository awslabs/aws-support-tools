# lf-troubleshoot

**Lake Formation troubleshooter — recommend solutions from a skills knowledge base.**

Describe your Lake Formation issue and get matched solutions, causes, and CLI commands to fix it. Powered by a local skills knowledge base (YAML files) that you can extend with your own LF data.

## Installation

```bash
pip install lf-troubleshoot
```

Optional — for full YAML support:
```bash
pip install lf-troubleshoot[yaml]
```

## Quick Start

```bash
# Direct query
lf-troubleshoot "access denied on athena query"

# Interactive mode
lf-troubleshoot

# List all available skills
lf-troubleshoot --list

# JSON output
lf-troubleshoot "cross account access" --json
```

## Live Diagnosis Mode

Check real AWS resources with `lf-verify` and get matched solutions automatically:

```bash
# Install with diagnose support
pip install lf-troubleshoot[diagnose]

# Check if a principal can access a table — get fix recommendations if not
lf-troubleshoot --diagnose --database mydb --table mytable \
  --principal arn:aws:iam::123456789012:role/GlueRole --region us-east-1

# Audit a database — flag issues like IAMAllowedPrincipals
lf-troubleshoot --diagnose --database mydb --region us-east-1

# With a specific profile
lf-troubleshoot --diagnose --database mydb --table orders \
  --principal arn:aws:iam::123456789012:role/AnalystRole \
  --region us-east-1 --profile prod

# JSON output for automation
lf-troubleshoot --diagnose --database mydb --principal arn:aws:iam::123456789012:role/Role --region us-east-1 --json
```

The diagnose mode:
1. Runs `lf-verify` against your real AWS resources
2. Identifies issues (no access, IAMAllowedPrincipals, missing grants)
3. Maps each finding to the skills knowledge base
4. Recommends specific solutions with CLI commands to fix

## How It Works

1. You describe your issue in plain text
2. The engine matches your description against a knowledge base of skills
3. Each skill contains: symptoms, keywords, causes, and step-by-step solutions
4. Top matches are displayed with actionable fixes

## Built-in Skills

| Skill | Category | Description |
|-------|----------|-------------|
| Access Denied on Glue/Athena | permissions | Missing SELECT/DESCRIBE grants |
| Cross-Account Access | sharing | RAM shares, resource links |
| Data Lake Administrator | admin | Grant/revoke permission issues |
| Glue Crawler LF Issues | permissions | Crawler CREATE_TABLE/ALTER/DROP |
| IAMAllowedPrincipals | permissions | LF not enforced, legacy mode |
| LF-Tag Access Not Working | tags | Tag-based access control issues |
| Migration to LF | migration | Transitioning from IAM-only |
| S3 Location Registration | registration | Data location registration |

## Adding Your Own Skills

Create a YAML file in the `skills/` directory:

```yaml
id: my-custom-issue
title: "My Custom LF Issue"
category: custom
severity: high
symptoms:
  - "error message I see"
  - "another symptom"
keywords:
  - keyword1
  - keyword2
causes:
  - "Why this happens"
solutions:
  - title: "Fix it"
    steps:
      - "Step 1"
      - "Step 2"
    command: |
      aws lakeformation some-command
```

Use a custom skills directory:
```bash
lf-troubleshoot --skills-dir /path/to/my/skills "my issue"
```

## Usage with lf-verify

This tool pairs well with [lf-verify](https://github.com/your-repo/lf-verify) for diagnosing AND verifying Lake Formation access:

```bash
# 1. Diagnose the issue
lf-troubleshoot "glue crawler access denied"

# 2. Verify the fix
lf-verify --resource-type database --database mydb \
  --principal arn:aws:iam::123456789012:role/GlueCrawlerRole --region us-east-1
```

## License

MIT
