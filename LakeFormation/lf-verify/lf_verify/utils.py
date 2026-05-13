"""Shared utilities: colors, retry logic, table formatting, CSV output."""

import csv
import random
import sys
import time

import botocore.exceptions

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def retry_api_call(func, *args, **kwargs):
    """Call func with retry on throttling errors (up to 5 retries with exponential backoff)."""
    for attempt in range(6):
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code not in ("Throttling", "TooManyRequestsException") or attempt == 5:
                raise
            wait = (2 ** attempt) + random.random()
            print(f"  {YELLOW}\u26a0\ufe0f  Throttled, retrying in {wait:.1f}s (attempt {attempt + 1}/5){RESET}")
            time.sleep(wait)


def print_table_fmt(headers, rows):
    """Print data in a formatted table."""
    if not rows:
        print("No results found.")
        return
    widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for r in rows:
        print(fmt.format(*(str(r[i]) for i in range(len(headers)))))
    print(sep)


def write_csv(headers, rows):
    """Write rows as CSV to stdout."""
    writer = csv.writer(sys.stdout)
    writer.writerow(headers)
    writer.writerows(rows)
