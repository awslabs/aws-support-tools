# eks-addon-upgrade-check

Pre-upgrade compatibility check for AWS EKS managed add-ons. Grades a proposed add-on upgrade against multiple signals — API compatibility, config schema diff, current install health, IAM posture, upstream changelog scan, and a curated known-issue registry — then emits a Markdown/JSON report with a CI-gate exit code.

Single-file bash script. Runs on macOS default bash (3.2.57), Amazon Linux 2, Amazon Linux 2023, and base Debian/Ubuntu. No installs beyond `aws` CLI v2, `jq`, `curl`, and `sha256sum` or `shasum`.

## Quickstart

```bash
chmod +x eks-addon-upgrade-check.sh

# Discover and grade every installed add-on on a cluster
./eks-addon-upgrade-check.sh --cluster <name> --region <region>

# Single add-on against a specific target version
./eks-addon-upgrade-check.sh --cluster <name> --region <region> --addon aws-ebs-csi-driver --target-version v1.49.0-eksbuild.1

# CI gate — non-zero exit on any BREAKING finding
./eks-addon-upgrade-check.sh --cluster <name> --min-grade breaking --format json --json-out report.json
```

Exit codes: `0` clean, `1` FYI, `2` SOFT, `3` BREAKING, `10` usage error, `11` AWS API error, `12` manifest error, `13` partial (some add-on couldn't be fully analyzed).

## IAM permissions

The script is read-only and needs exactly five IAM actions, one per API call it makes:

| API call | IAM action |
|---|---|
| `eks describe-cluster` | `eks:DescribeCluster` |
| `eks list-addons` | `eks:ListAddons` |
| `eks describe-addon` | `eks:DescribeAddon` |
| `eks describe-addon-versions` | `eks:DescribeAddonVersions` |
| `eks describe-addon-configuration` | `eks:DescribeAddonConfiguration` |

The `sts get-caller-identity` preflight check needs no IAM permission — it is allowed for any valid identity.

## The rules manifest

The rules manifest is the script's grading rulebook. It carries the per-add-on adapter dispatch, changelog source URLs, skip-level version policies, POSIX-ERE breaking-change regexes, PR-label allowlists, and the curated known-issue registry (S7) where known upgrade pitfalls live.

**The manifest is embedded in the script** — there is a single self-contained file with nothing to ship alongside it. The embedded copy is canonical and is used by default; the manifest source is reported as `embedded`.

You can override it with an external manifest for testing or customization:

- Pass `--rules-manifest-url <url|file://path>` (or set `EKS_ADDON_CHECK_RULES_URL`). The source is then reported as `external`. If the requested manifest can't be fetched, the script warns and falls back to the embedded copy.
- Pin a specific manifest for CI with `--rules-sha <sha256>` — the script dies with `E_MANIFEST` (12) on mismatch, so a manifest drift never silently changes grading behavior.

## Grading signals

| Signal | Source | Confidence tier |
|---|---|---|
| S1 | `describe-addon-versions` compatibility with target K8s | `api-derived` |
| S1b | Skip-level jump vs manifest `skipLevelPolicy.maxMinorJump` | `api-derived` |
| S2 | `describe-addon-configuration` JSON-schema diff (current ↔ target) | `schema-derived` |
| S3 | Current install health (`describe-addon.status`) | `api-derived` |
| S4 | `serviceAccountRoleArn` presence when IAM is required | `api-derived` |
| S5 | Upstream changelog / release-notes regex scan | `single-signal-heuristic` |
| S7 | Curated known-issue registry (per-version-range entries) | `curated` |




