# Contributing to aws-support-tools

Thanks for your interest in contributing. This repo is a curated collection of tools and scripts that help AWS customers diagnose, troubleshoot, and operate their AWS environments.

## What belongs here

A good tool here is:

- **Useful**: solves a real, recurring problem, not a one-off script for a single account.
- **Impactful**: saves meaningful time or reduces risk for the people who use it.
- **Safe**: doesn't do anything destructive by default, handles credentials and API calls responsibly, and fails safely.
- **Genuinely helpful to customers**: written for someone outside your own team to pick up and use, with enough context to understand what it does and why.

## Contributing a new tool

1. Fork the repo and create a new top-level folder named after the AWS service your tool targets (e.g. `EC2/`, `S3/`), or add to an existing one if it fits.
2. Include a `README.md` in your tool's folder that explains what the tool does, how to run it, what permissions/IAM it needs, and any prerequisites.
3. Submit source code only. No pre-built or compiled binaries (no `.zip`, `.exe`, `.jar`, etc.). Reviewers and users need to be able to read what they're running.
4. Open a pull request using the PR template.

## Fixing or improving an existing tool

Open a pull request against the tool's existing folder. Keep the change scoped to that tool, and update its `README.md` if the fix changes how it's run or what it needs.

## Testing

There's no repo-wide test suite. If the tool you're touching has its own tests, run them and make sure they pass. If it doesn't, describe in the pull request how you validated the change (what you ran it against, what you checked).

## Review

A maintainer will review your pull request, typically within a few business days. Feel free to ping the PR if you haven't heard back after a couple of weeks.

## Reporting issues or requesting features

Open a GitHub issue using the appropriate template. Please include enough detail (AWS service, tool name, steps to reproduce, expected vs. actual behavior) for someone to act on it without a back-and-forth.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0 (see `LICENSE`).
