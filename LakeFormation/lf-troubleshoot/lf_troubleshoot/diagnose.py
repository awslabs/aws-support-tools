"""Live diagnosis: run lf-verify checks against real AWS resources and map findings to skills."""

import json
import subprocess
import sys

from .engine import load_skills, match_skills

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def run_lf_verify(args_list):
    """Run lf-verify with given args and return parsed JSON output."""
    cmd = [sys.executable, "-m", "lf_verify"] + args_list + ["--output", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return None, result.stderr.strip()
        return json.loads(result.stdout), None
    except FileNotFoundError:
        return None, "lf-verify not installed. Run: pip install lf-verify"
    except json.JSONDecodeError:
        return None, f"Could not parse lf-verify output: {result.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return None, "lf-verify timed out (60s)"


def diagnose(database=None, table=None, principal=None, region=None,
             profile=None, catalog_id=None, skills_dir=None):
    """Run checks against real resources and return findings with matched skills."""
    skills = load_skills(skills_dir)
    findings = []

    base_args = []
    if region:
        base_args += ["--region", region]
    if profile:
        base_args += ["--profile", profile]
    if catalog_id:
        base_args += ["--catalog-id", catalog_id]

    # Check 1: Verify principal access to the resource
    if principal and database:
        resource_type = "table" if table else "database"
        args = base_args + ["--resource-type", resource_type, "--database", database]
        if table:
            args += ["--table", table]
        args += ["--principal", principal]

        print(f"{DIM}Checking {resource_type} access for {principal}...{RESET}")
        data, err = run_lf_verify(args)

        if err:
            findings.append({"check": "verify_access", "error": err})
        elif data:
            for result in data if isinstance(data, list) else [data]:
                has_access = (result.get("is_admin") or result.get("has_named_access")
                              or result.get("tag_access") or result.get("iam_allowed_principals"))
                if not has_access:
                    findings.append({
                        "check": "verify_access",
                        "status": "NO_ACCESS",
                        "principal": principal,
                        "resource": f"{database}.{table}" if table else database,
                        "detail": result,
                    })
                elif result.get("iam_allowed_principals"):
                    findings.append({
                        "check": "iam_allowed_principals",
                        "status": "WARNING",
                        "resource": f"{database}.{table}" if table else database,
                        "detail": "IAMAllowedPrincipals is set — LF not enforced",
                    })
                else:
                    findings.append({
                        "check": "verify_access",
                        "status": "ACCESS_OK",
                        "principal": principal,
                        "resource": f"{database}.{table}" if table else database,
                        "detail": result,
                    })

    # Check 2: Audit who has access (even without a principal)
    if database and not principal:
        resource_type = "table" if table else "database"
        args = base_args + ["--resource-type", resource_type, "--database", database, "--who-has-access"]
        if table:
            args += ["--table", table]

        print(f"{DIM}Auditing access on {database}{'.' + table if table else ''}...{RESET}")
        data, err = run_lf_verify(args)

        if err:
            findings.append({"check": "audit", "error": err})
        elif data:
            principals_map = data.get("principals", {})
            if not principals_map:
                findings.append({
                    "check": "audit",
                    "status": "NO_GRANTS",
                    "resource": f"{database}.{table}" if table else database,
                    "detail": "No principals have access — grants may be missing",
                })
            else:
                for pid in principals_map:
                    if "IAMAllowedPrincipals" in pid:
                        findings.append({
                            "check": "iam_allowed_principals",
                            "status": "WARNING",
                            "resource": f"{database}.{table}" if table else database,
                            "detail": "IAMAllowedPrincipals is set — LF not enforced",
                        })
                        break

    # Map findings to skills
    recommendations = []
    for finding in findings:
        if finding.get("status") == "ACCESS_OK":
            continue

        # Build a query from the finding to match against skills
        query_parts = []
        if finding.get("status") == "NO_ACCESS":
            query_parts.append("access denied")
        if finding.get("check") == "iam_allowed_principals":
            query_parts.append("IAMAllowedPrincipals")
        if finding.get("status") == "NO_GRANTS":
            query_parts.append("no permissions access denied")
        if finding.get("error"):
            query_parts.append(finding["error"])

        if query_parts:
            query = " ".join(query_parts)
            matched = match_skills(query, skills)
            if matched:
                recommendations.append({
                    "finding": finding,
                    "skills": [(score, skill) for score, skill in matched[:2]],
                })

    return findings, recommendations


def print_diagnosis(findings, recommendations):
    """Print diagnosis results."""
    print(f"\n{'═'*60}")
    print(f"{BOLD}Diagnosis Results{RESET}")
    print(f"{'═'*60}")

    # Summary
    errors = [f for f in findings if f.get("error")]
    issues = [f for f in findings if f.get("status") in ("NO_ACCESS", "NO_GRANTS", "WARNING")]
    ok = [f for f in findings if f.get("status") == "ACCESS_OK"]

    if ok:
        for f in ok:
            print(f"\n  {GREEN}✅ {f.get('principal', '?')} → {f.get('resource', '?')}: Access confirmed{RESET}")

    if issues:
        for f in issues:
            if f["status"] == "NO_ACCESS":
                print(f"\n  {RED}❌ {f.get('principal', '?')} → {f.get('resource', '?')}: No access{RESET}")
            elif f["status"] == "WARNING":
                print(f"\n  {YELLOW}⚠️  {f.get('resource', '?')}: {f.get('detail', '')}{RESET}")
            elif f["status"] == "NO_GRANTS":
                print(f"\n  {RED}❌ {f.get('resource', '?')}: {f.get('detail', '')}{RESET}")

    if errors:
        for f in errors:
            print(f"\n  {RED}⚠️  Check failed: {f['error']}{RESET}")

    # Recommendations
    if recommendations:
        print(f"\n{'─'*60}")
        print(f"{BOLD}Recommended Solutions:{RESET}")
        for rec in recommendations:
            for score, skill in rec["skills"]:
                print(f"\n  {GREEN}▶ {skill.get('title')}{RESET}")
                solutions = skill.get("solutions", [])
                if solutions and isinstance(solutions[0], dict):
                    sol = solutions[0]
                    print(f"    {sol.get('title', '')}")
                    for step in sol.get("steps", [])[:3]:
                        print(f"      {step}")
                    cmd = sol.get("command", "")
                    if cmd:
                        print(f"\n      {DIM}$ {cmd.strip().splitlines()[0]}{RESET}")
    elif not issues and not errors:
        print(f"\n  {GREEN}All checks passed — no issues found.{RESET}")

    print()
