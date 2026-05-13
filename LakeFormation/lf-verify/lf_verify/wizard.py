#!/usr/bin/env python3
"""Interactive CLI wizard for lf-verify."""

import subprocess
import sys

CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
YELLOW = "\033[93m"
GREEN = "\033[92m"


def ask(prompt, default=None, choices=None, required=True, allow_multi=False):
    """Prompt user for input with optional default, choices, and validation."""
    hint = ""
    if choices:
        hint = f" [{'/'.join(choices)}]"
    if default:
        hint += f" (default: {default})"
    if allow_multi:
        hint += " (space-separated for multiple)"

    while True:
        val = input(f"  {CYAN}>{RESET} {prompt}{hint}: ").strip()
        if not val and default:
            return default
        if not val and not required:
            return None
        if not val:
            print(f"    {YELLOW}Required field.{RESET}")
            continue
        if choices and val not in choices:
            print(f"    {YELLOW}Choose one of: {', '.join(choices)}{RESET}")
            continue
        return val


def ask_yn(prompt, default="y"):
    val = ask(prompt, default=default, choices=["y", "n"])
    return val.lower() == "y"


def header(text):
    print(f"\n{BOLD}{text}{RESET}")
    print(f"{DIM}{'\u2500' * 50}{RESET}")


def main():
    print(f"\n{BOLD}\u2554{'═'*50}\u2557{RESET}")
    print(f"{BOLD}\u2551   Lake Formation Access Verification Wizard      \u2551{RESET}")
    print(f"{BOLD}\u255a{'═'*50}\u255d{RESET}")

    # Step 1: Mode
    header("Step 1: What do you want to do?")
    print(f"  {GREEN}1{RESET}  Verify if a principal has access to a resource")
    print(f"  {GREEN}2{RESET}  List who has access to a resource (audit)")
    print(f"  {GREEN}3{RESET}  List what a principal can access (discovery)")
    print(f"  {GREEN}4{RESET}  Find resources matching an LF-Tag")
    print()
    mode = ask("Choose", choices=["1", "2", "3", "4"])

    args = []

    # Step 2: AWS config
    header("Step 2: AWS Configuration")
    region = ask("AWS region", default="us-east-1")
    args += ["--region", region]

    profile = ask("AWS CLI profile", required=False)
    if profile:
        args += ["--profile", profile]

    catalog_id = ask("Catalog/Account ID", required=False)
    if catalog_id:
        args += ["--catalog-id", catalog_id]

    # Mode 3: what-can-access
    if mode == "3":
        header("Step 3: Principal")
        principal = ask("Principal ARN (or sso:user/name, sso:group/name)", allow_multi=True)
        args += ["--what-can-access", "--principal"] + principal.split()

        if any(p.startswith("sso:") for p in principal.split()):
            sso_id = ask("SSO Identity Store ID (e.g. d-1234567890)")
            args += ["--sso-instance-id", sso_id]

        if ask_yn("Only show LF-Tag grants?", default="n"):
            args.append("--tag-grants-only")

    # Mode 4: find-resources
    elif mode == "4":
        header("Step 3: LF-Tag Expression")
        tag_key = ask("Tag key")
        tag_values = ask("Tag values (comma-separated)")
        args += ["--resource-type", "lf-tag-policy", "--tag-key", tag_key, "--tag-values", tag_values, "--find-resources"]

    # Modes 1 and 2: resource-based
    else:
        header("Step 3: Resource Type")
        print(f"  {GREEN}1{RESET}  database")
        print(f"  {GREEN}2{RESET}  table")
        print(f"  {GREEN}3{RESET}  column")
        print(f"  {GREEN}4{RESET}  s3 (data location)")
        print(f"  {GREEN}5{RESET}  s3table (S3 Tables)")
        print(f"  {GREEN}6{RESET}  catalog")
        print(f"  {GREEN}7{RESET}  lf-tag")
        print(f"  {GREEN}8{RESET}  lf-tag-policy")
        print(f"  {GREEN}9{RESET}  lf-tag-expression")
        print()
        rt_map = {"1": "database", "2": "table", "3": "column", "4": "s3",
                  "5": "s3table", "6": "catalog", "7": "lf-tag", "8": "lf-tag-policy",
                  "9": "lf-tag-expression"}
        rt_choice = ask("Choose", choices=list(rt_map.keys()))
        rt = rt_map[rt_choice]
        args += ["--resource-type", rt]

        header("Step 4: Resource Details")

        if rt in ("database", "table", "column"):
            db = ask("Database name")
            args += ["--database", db]

        if rt in ("table", "column"):
            all_tables = ask_yn("Check all tables in the database?", default="n")
            if all_tables:
                args.append("--all-tables")
            else:
                tbl = ask("Table name")
                args += ["--table", tbl]

        if rt == "column" and "--all-tables" not in args:
            cols = ask("Column names (comma-separated)")
            args += ["--columns", cols]

        if rt == "s3":
            s3 = ask("S3 ARN (e.g. arn:aws:s3:::bucket/prefix/)")
            args += ["--s3-path", s3]

        if rt == "s3table":
            bucket = ask("S3 table bucket name")
            ns = ask("Namespace (database)")
            args += ["--s3-table-bucket", bucket, "--database", ns]
            tbl = ask("Table name (leave empty for namespace-level)", required=False)
            if tbl:
                args += ["--table", tbl]

        if rt in ("lf-tag", "lf-tag-policy"):
            tag_key = ask("Tag key")
            tag_values = ask("Tag values (comma-separated)")
            args += ["--tag-key", tag_key, "--tag-values", tag_values]

        if rt == "lf-tag-policy":
            prt = ask("Policy resource type", default="table", choices=["database", "table"])
            args += ["--policy-resource-type", prt]

        if rt == "lf-tag-expression":
            expr = ask("Expression name")
            args += ["--expression-name", expr]

        if mode == "1":
            header("Step 5: Principal(s)")
            principal = ask("Principal ARN(s) (or sso:user/name, sso:group/name)", allow_multi=True)
            args += ["--principal"] + principal.split()

            if any(p.startswith("sso:") for p in principal.split()):
                sso_id = ask("SSO Identity Store ID (e.g. d-1234567890)")
                args += ["--sso-instance-id", sso_id]
        else:
            args.append("--who-has-access")

    # Output options
    header("Options")
    if ask_yn("JSON output?", default="n"):
        args.append("--json")
    if ask_yn("Debug mode?", default="n"):
        args.append("--debug")

    # Show and run
    cmd = [sys.executable, "-m", "lf_verify"] + args
    cmd_str = " ".join(cmd)
    print(f"\n{BOLD}Command:{RESET}")
    print(f"  {DIM}{cmd_str}{RESET}")
    print()

    if ask_yn("Run now?"):
        print(f"\n{'═' * 60}\n")
        subprocess.run(cmd)
    else:
        print(f"\n  Copy and run manually:\n  {cmd_str}\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {DIM}Cancelled.{RESET}\n")
        sys.exit(0)
