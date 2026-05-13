"""CLI interface for lf-troubleshoot."""

import argparse
import json
import sys

from . import __version__
from .engine import load_skills, match_skills

BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def print_skill(skill, verbose=False):
    """Print a matched skill with solutions."""
    print(f"\n{'═'*60}")
    print(f"{BOLD}{skill.get('title', 'Unknown')}{RESET}")
    print(f"{DIM}Category: {skill.get('category', '?')} | Severity: {skill.get('severity', '?')}{RESET}")
    print(f"{'═'*60}")

    # Causes
    causes = skill.get("causes", [])
    if causes:
        print(f"\n{YELLOW}Possible Causes:{RESET}")
        for c in causes:
            if isinstance(c, str):
                print(f"  • {c}")

    # Solutions
    solutions = skill.get("solutions", [])
    if solutions:
        print(f"\n{GREEN}Solutions:{RESET}")
        for i, sol in enumerate(solutions, 1):
            if isinstance(sol, dict):
                print(f"\n  {GREEN}{i}. {sol.get('title', 'Solution')}{RESET}")
                for step in sol.get("steps", []):
                    print(f"     {step}")
                cmd = sol.get("command", "")
                if cmd:
                    print(f"\n     {DIM}$ {cmd.strip()}{RESET}")
            elif isinstance(sol, str):
                print(f"  {i}. {sol}")

    # Related
    related = skill.get("related", [])
    if related and verbose:
        print(f"\n{DIM}Related: {', '.join(related)}{RESET}")


def interactive_mode(skills):
    """Run interactive troubleshooting session."""
    print(f"\n{BOLD}╔{'═'*56}╗{RESET}")
    print(f"{BOLD}║  Lake Formation Troubleshooter                        ║{RESET}")
    print(f"{BOLD}╚{'═'*56}╝{RESET}")
    print(f"{DIM}Describe your issue, or type 'list' to see all topics.{RESET}")
    print(f"{DIM}Type 'quit' to exit.{RESET}\n")

    while True:
        try:
            query = input(f"{CYAN}> {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Bye!{RESET}")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break
        if query.lower() == "list":
            print(f"\n{BOLD}Available topics:{RESET}")
            for s in skills:
                print(f"  • {s.get('title', '?')} [{s.get('category', '?')}]")
            print()
            continue

        matches = match_skills(query, skills)
        if not matches:
            print(f"\n{RED}No matching skills found.{RESET} Try different keywords or type 'list'.\n")
            continue

        print(f"\n{DIM}Found {len(matches)} match(es):{RESET}")
        # Show top 3
        for score, skill in matches[:3]:
            print_skill(skill, verbose=True)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Lake Formation troubleshooter — recommend solutions from a skills knowledge base"
    )
    parser.add_argument("query", nargs="*", help="Describe your issue (or omit for interactive mode)")
    parser.add_argument("--list", action="store_true", help="List all available skills")
    parser.add_argument("--skills-dir", help="Custom skills directory path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Diagnose mode — check real AWS resources
    diag = parser.add_argument_group("diagnose", "Check real AWS resources with lf-verify")
    diag.add_argument("--diagnose", action="store_true", help="Run live checks against AWS resources")
    diag.add_argument("--database", help="Database name to check")
    diag.add_argument("--table", help="Table name to check")
    diag.add_argument("--principal", help="Principal ARN to verify access for")
    diag.add_argument("--region", help="AWS region")
    diag.add_argument("--profile", help="AWS CLI profile")
    diag.add_argument("--catalog-id", help="AWS catalog/account ID")

    args = parser.parse_args()

    skills = load_skills(args.skills_dir)

    # Diagnose mode — run live checks
    if args.diagnose:
        if not args.database:
            parser.error("--database is required with --diagnose")
        from .diagnose import diagnose, print_diagnosis
        findings, recommendations = diagnose(
            database=args.database,
            table=args.table,
            principal=args.principal,
            region=args.region,
            profile=args.profile,
            catalog_id=args.catalog_id,
            skills_dir=args.skills_dir,
        )
        if args.json:
            output = {"findings": findings, "recommendations": [
                {"finding": r["finding"], "skills": [{"score": s, "id": sk.get("id"), "title": sk.get("title")} for s, sk in r["skills"]]}
                for r in recommendations
            ]}
            print(json.dumps(output, indent=2, default=str))
        else:
            print_diagnosis(findings, recommendations)
        return

    if args.list:
        if args.json:
            print(json.dumps([{"id": s.get("id"), "title": s.get("title"), "category": s.get("category")} for s in skills], indent=2))
        else:
            print(f"\n{BOLD}Available skills ({len(skills)}):{RESET}\n")
            for s in skills:
                print(f"  [{s.get('category', '?'):12}] {s.get('title', '?')}")
            print()
        return

    if not args.query:
        interactive_mode(skills)
        return

    # Direct mode
    query = " ".join(args.query)
    matches = match_skills(query, skills)

    if args.json:
        output = []
        for score, skill in matches[:5]:
            output.append({
                "score": round(score, 2),
                "id": skill.get("id"),
                "title": skill.get("title"),
                "causes": skill.get("causes", []),
                "solutions": skill.get("solutions", []),
            })
        print(json.dumps(output, indent=2))
        return

    if not matches:
        print(f"\n{RED}No matching skills found for: {query}{RESET}")
        print(f"Try: lf-troubleshoot --list")
        sys.exit(1)

    for score, skill in matches[:3]:
        print_skill(skill, verbose=True)
    print()
