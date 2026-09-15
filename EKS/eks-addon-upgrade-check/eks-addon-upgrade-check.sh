#!/usr/bin/env bash
# eks-addon-upgrade-check.sh
#
# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
#
# Refer to the AWS guidance on upgrade best practices:
#   https://docs.aws.amazon.com/eks/latest/best-practices/cluster-upgrades.html
#
# Purpose:
#   Pre-upgrade compatibility check for EKS managed add-ons.
#   Check for add-ons with hard requirements in the proposed or target upgrade version.
#   This script also flags addon degradation status.
#
#   This script is READ-ONLY. It only runs "describe", "list", "get" and
#   similar commands to AWS account or EkS. It NEVER modifies, deletes, or upgrades anything.
#   It writes only to user-configured cache/output paths plus mktemp scratch (that is cleaned on exit).
#
# Safety:
#   Safe to run in production with production-scoped read-only credentials, 
#   including a notice such as — this is a "describe/list" tool by construction.
#
# Dependencies: aws CLI v2, jq >= 1.6, curl. sha256sum OR shasum.

set -Eeuo pipefail

SCRIPT_VERSION="0.1.0"
SCRIPT_NAME="eks-addon-upgrade-check"

# ------------------------------------------------------------------------------
# Defaults & globals
# ------------------------------------------------------------------------------
CLUSTER=""
REGION="${AWS_REGION:-}"
PROFILE="${AWS_PROFILE:-}"
ADDON=""
TARGET_VERSION=""
TARGET_K8S=""
MODE="discover"
# Empty by default: the embedded manifest is canonical. Set this (or pass
# --rules-manifest-url) only to feed in an external manifest explicitly.
RULES_URL="${EKS_ADDON_CHECK_RULES_URL:-}"
RULES_SHA_EXPECTED="${EKS_ADDON_CHECK_RULES_SHA:-}"
CACHE_DIR="${EKS_ADDON_CHECK_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/eks-addon-check}"
CACHE_TTL_SECONDS=86400
OFFLINE=0
REFRESH=0
JSON_OUT=""
FORMAT="markdown"
MIN_GRADE="fyi"
NO_COLOR=0
VERBOSE=0
METRICS_OUT=""
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Exit codes (documented under "Exit codes" in README.md)
E_CLEAN=0
E_FYI=1
E_SOFT=2
E_BREAKING=3
E_USAGE=10
E_AWS=11
E_MANIFEST=12
E_PARTIAL=13

# Grade ordinals. BREAKING_HARD is the single "upgrade blocks here" tier —
# the remediation (fix available vs. requires reconfiguration) belongs in
# the finding's title/detail, not the tier name.
grade_ord() {
  case "$1" in
    CLEAN) echo 0 ;;
    FYI) echo 1 ;;
    SOFT) echo 2 ;;
    BREAKING_HARD) echo 3 ;;
    UNKNOWN) echo 0 ;;
    *) echo 0 ;;
  esac
}

min_grade_ord() {
  case "$1" in
    clean) echo 0 ;;
    fyi) echo 1 ;;
    soft) echo 2 ;;
    breaking) echo 3 ;;
    *) echo 1 ;;
  esac
}

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
_c_red=""; _c_yellow=""; _c_green=""; _c_blue=""; _c_dim=""; _c_reset=""
init_colors() {
  if [[ $NO_COLOR -eq 0 && -t 2 ]]; then
    _c_red=$'\033[31m'; _c_yellow=$'\033[33m'; _c_green=$'\033[32m'
    _c_blue=$'\033[34m'; _c_dim=$'\033[2m'; _c_reset=$'\033[0m'
  fi
}
log()  { printf '%s\n' "$*" >&2; }
info() { printf '%s[info]%s %s\n' "$_c_blue" "$_c_reset" "$*" >&2; }
warn() { printf '%s[warn]%s %s\n' "$_c_yellow" "$_c_reset" "$*" >&2; }
err()  { printf '%s[err ]%s %s\n' "$_c_red" "$_c_reset" "$*" >&2; }
dbg()  { [[ $VERBOSE -eq 1 ]] && printf '%s[dbg ]%s %s\n' "$_c_dim" "$_c_reset" "$*" >&2 || true; }

die() { local code="$1"; shift; err "$*"; exit "$code"; }

# NB: intentionally no `trap ... ERR`.
# With `set -eEuo pipefail` any real failure aborts. An ERR trap fires
# inside command substitutions even for handled non-zero returns
# (e.g., `if cmd=$(func_that_may_return_1); then`), which produces noisy
# false "unexpected failure" messages without adding safety.

# Scratch files (populated later). Cleaned up by the EXIT trap below so they
# never leak, including when the script exits early through die().
FINDINGS_FILE=""
ADDON_RESULTS_FILE=""
AWS_ERR_FILE=""
cleanup() {
  rm -f "${FINDINGS_FILE:-}" "${ADDON_RESULTS_FILE:-}" "${AWS_ERR_FILE:-}" 2>/dev/null || true
}
trap cleanup EXIT

# ------------------------------------------------------------------------------
# Usage
# ------------------------------------------------------------------------------
usage() {
  cat <<EOF
$SCRIPT_NAME v$SCRIPT_VERSION

Usage:
  $0 --cluster <name> [options]

Options:
  --cluster <name>                     EKS cluster name (required)
  --region <aws-region>                AWS region (default: env / config)
  --profile <aws-profile>              AWS profile (default: env / config)
  --addon <name>                       Restrict to one add-on (default: discover all)
  --target-version <vX.Y.Z-eksbuild.N> Target add-on version (default: cluster's defaultVersion)
  --target-cluster-version <1.NN>      Target K8s version (default: cluster's current)
  --mode <discover|single|flag-all-upper>
                                       Analysis mode (default: discover)
  --rules-manifest-url <url>           Optional external rules manifest, URL or
                                       file:// path (default: embedded manifest)
  --rules-sha <sha256>                 Expected SHA-256 of the manifest (opt-in verify)
  --cache-dir <path>                   Cache directory (default: \$XDG_CACHE_HOME/eks-addon-check)
  --cache-ttl <seconds>                Cache entry TTL (default: 86400)
  --offline                            Fail on cache miss instead of network fetch
  --refresh, --no-cache                Bypass all caches for this run (still writes new entries)
  --json-out <path>                    Write structured JSON report to path
  --format <markdown|json|both>        Console output format (default: markdown)
  --min-grade <fyi|soft|breaking>      Exit non-zero at/above this grade (default: fyi)
  --metrics-out <path>                 Write per-run metrics JSON
  --no-color                           Disable ANSI colors
  --verbose                            Verbose logging
  -h, --help                           Show this help

Environment variables:
  AWS_PROFILE, AWS_REGION              Standard AWS SDK env
  EKS_ADDON_CHECK_RULES_URL            Optional external rules manifest URL
                                       (default: embedded manifest)
  EKS_ADDON_CHECK_RULES_SHA            Expected manifest SHA
  EKS_ADDON_CHECK_CACHE_DIR            Override cache directory
  GITHUB_TOKEN                         Optional PAT for higher GitHub rate limits

Examples:
  $0 --cluster prod-us-east-1
  $0 --cluster staging --addon vpc-cni --target-version v1.20.4-eksbuild.1
  $0 --cluster prod --mode flag-all-upper --json-out report.json --format json
EOF
}

# ------------------------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------------------------
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --cluster) CLUSTER="$2"; shift 2 ;;
      --region) REGION="$2"; shift 2 ;;
      --profile) PROFILE="$2"; shift 2 ;;
      --addon) ADDON="$2"; shift 2 ;;
      --target-version) TARGET_VERSION="$2"; shift 2 ;;
      --target-cluster-version) TARGET_K8S="$2"; shift 2 ;;
      --mode) MODE="$2"; shift 2 ;;
      --rules-manifest-url) RULES_URL="$2"; shift 2 ;;
      --rules-sha) RULES_SHA_EXPECTED="$2"; shift 2 ;;
      --cache-dir) CACHE_DIR="$2"; shift 2 ;;
      --cache-ttl) CACHE_TTL_SECONDS="$2"; shift 2 ;;
      --offline) OFFLINE=1; shift ;;
      --refresh|--no-cache) REFRESH=1; shift ;;
      --json-out) JSON_OUT="$2"; shift 2 ;;
      --format) FORMAT="$2"; shift 2 ;;
      --min-grade) MIN_GRADE="$2"; shift 2 ;;
      --metrics-out) METRICS_OUT="$2"; shift 2 ;;
      --no-color) NO_COLOR=1; shift ;;
      --verbose) VERBOSE=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) die $E_USAGE "unknown argument: $1 (use --help)" ;;
    esac
  done

  [[ -z "$CLUSTER" ]] && { usage >&2; die $E_USAGE "--cluster is required"; }
  case "$MODE" in
    discover|single|flag-all-upper) ;;
    *) die $E_USAGE "--mode must be discover|single|flag-all-upper" ;;
  esac
  case "$FORMAT" in
    markdown|json|both) ;;
    *) die $E_USAGE "--format must be markdown|json|both" ;;
  esac
  case "$MIN_GRADE" in
    fyi|soft|breaking|clean) ;;
    *) die $E_USAGE "--min-grade must be clean|fyi|soft|breaking" ;;
  esac
  if [[ "$MODE" == "single" && -z "$ADDON" ]]; then
    die $E_USAGE "--mode single requires --addon"
  fi
  if (( OFFLINE == 1 && REFRESH == 1 )); then
    die $E_USAGE "--offline and --refresh are mutually exclusive"
  fi
}

# ------------------------------------------------------------------------------
# Preflight
# ------------------------------------------------------------------------------
require_bin() {
  command -v "$1" >/dev/null 2>&1 || die $E_USAGE "missing required binary: $1"
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else die $E_USAGE "need sha256sum or shasum"
  fi
}

aws_cmd=()
build_aws_cmd() {
  aws_cmd=(aws)
  [[ -n "$REGION" ]] && aws_cmd+=(--region "$REGION")
  [[ -n "$PROFILE" ]] && aws_cmd+=(--profile "$PROFILE")
  aws_cmd+=(--output json)
}

# Wrapper: aws <args> with retry/backoff on throttling.
# stderr is captured to AWS_ERR_FILE (created once in preflight, in the parent
# shell, so its path is known for cleanup — aws_call usually runs inside
# command substitutions where a new global wouldn't propagate back). stdout
# therefore stays clean JSON; error text is surfaced only when a call fails.
aws_call() {
  local tries=0 max=3 delay=1 out rc err_text
  [[ -n "$AWS_ERR_FILE" ]] || AWS_ERR_FILE=$(mktemp)
  while : ; do
    if out=$("${aws_cmd[@]}" "$@" 2>"$AWS_ERR_FILE"); then
      printf '%s' "$out"
      return 0
    else
      # Must be captured in the else branch: after `fi`, $? is the exit
      # status of the `if` statement itself, which is 0 when the condition
      # fails and no else ran — so a bare `rc=$?` below the fi is always 0.
      rc=$?
    fi
    err_text=$(<"$AWS_ERR_FILE")
    if [[ "$err_text" == *"Throttling"* || "$err_text" == *"TooManyRequests"* ]]; then
      tries=$((tries+1))
      if (( tries >= max )); then
        err "aws call throttled after $tries retries: $*"
        printf '%s\n' "$err_text" >&2
        return $rc
      fi
      warn "throttled — sleeping ${delay}s then retrying"
      sleep "$delay"
      delay=$((delay*2))
      continue
    fi
    err "aws call failed: $*"
    printf '%s\n' "$err_text" >&2
    return $rc
  done
}

preflight() {
  # bash 3.2 is the floor (macOS default). Fail early with a clear message
  # rather than surfacing a raw builtin error mid-run.
  if (( BASH_VERSINFO[0] < 3 || (BASH_VERSINFO[0] == 3 && BASH_VERSINFO[1] < 2) )); then
    die $E_USAGE "bash >= 3.2 required, found $BASH_VERSION"
  fi
  require_bin aws
  require_bin jq
  require_bin curl
  build_aws_cmd
  AWS_ERR_FILE=$(mktemp)

  if ! aws_call sts get-caller-identity >/dev/null; then
    die $E_AWS "aws sts get-caller-identity failed — check credentials"
  fi

  mkdir -p "$CACHE_DIR" \
    "$CACHE_DIR/manifest" \
    "$CACHE_DIR/api" \
    "$CACHE_DIR/changelogs"
  chmod 700 "$CACHE_DIR" 2>/dev/null || true
}

# ------------------------------------------------------------------------------
# Cache helpers
# ------------------------------------------------------------------------------
# cache_get <cache-path>  → prints file contents if fresh, else empty
cache_get() {
  local path="$1"
  (( REFRESH == 1 )) && { dbg "cache bypassed (--refresh): $path"; return 1; }
  [[ -f "$path" ]] || return 1
  local now mtime age
  now=$(date +%s)
  if stat -c '%Y' "$path" >/dev/null 2>&1; then
    mtime=$(stat -c '%Y' "$path")
  else
    mtime=$(stat -f '%m' "$path")
  fi
  age=$((now - mtime))
  if (( age > CACHE_TTL_SECONDS )); then
    dbg "cache stale (${age}s): $path"
    return 1
  fi
  cat "$path"
}

# cache_put <cache-path> <content>
cache_put() {
  local path="$1"; local content="$2"
  mkdir -p "$(dirname "$path")"
  local tmp="${path}.tmp.$$"
  printf '%s' "$content" > "$tmp"
  chmod 600 "$tmp" 2>/dev/null || true
  mv "$tmp" "$path"
}

# fetch_url <url> <cache-path> → prints content, uses cache/offline rules
fetch_url() {
  local url="$1" cache_path="$2" content
  if content=$(cache_get "$cache_path"); then
    printf '%s' "$content"
    return 0
  fi
  if (( OFFLINE )); then
    warn "offline mode: cache miss for $url"
    return 2
  fi
  local curl_args=(-fsSL --max-time 30 --retry 2 --retry-delay 1)
  if [[ "$url" == https://api.github.com/* && -n "$GITHUB_TOKEN" ]]; then
    curl_args+=(-H "Authorization: Bearer $GITHUB_TOKEN")
  fi
  if [[ "$url" == https://api.github.com/* ]]; then
    curl_args+=(-H "Accept: application/vnd.github+json")
  fi
  if [[ "$url" == file://* ]]; then
    local local_path="${url#file://}"
    if [[ ! -f "$local_path" ]]; then
      warn "local rules file not found: $local_path"
      return 2
    fi
    content=$(cat "$local_path")
  else
    if ! content=$(curl "${curl_args[@]}" "$url" 2>/dev/null); then
      warn "fetch failed: $url"
      return 2
    fi
  fi
  cache_put "$cache_path" "$content"
  printf '%s' "$content"
}

# ------------------------------------------------------------------------------
# Rules manifest
# ------------------------------------------------------------------------------
RULES_JSON=""
RULES_SHA_ACTUAL=""
RULES_SOURCE=""   # "external" | "embedded"

# embedded_manifest_write <target-path>
# Writes the embedded rules manifest to <target-path>. This heredoc is the
# canonical (and only) copy of the manifest — the script ships and runs as a
# single file. An external manifest is consulted only when explicitly
# requested via --rules-manifest-url / EKS_ADDON_CHECK_RULES_URL.
embedded_manifest_write() {
  local dest="$1"
  cat > "$dest" <<'EOF_RULES_MANIFEST'
{
  "manifestVersion": "2026-07-22.1",
  "description": "EKS add-on upgrade compatibility rules manifest. Consumed by eks-addon-upgrade-check.sh. Regexes are POSIX ERE (grep -E) — no PCRE (no (?i), no \\s, no \\d, no (?:...)). The script always calls grep -Ei so case-insensitivity is applied globally.",
  "regexPolicy": "POSIX ERE only; use [[:space:]] for whitespace, [0-9] for digits, [[:alnum:]_] for word chars, and plain (...) groups.",
  "addons": {
    "vpc-cni": {
      "adapter": "vpc-cni",
      "displayName": "Amazon VPC CNI",
      "changelogSources": [
        {
          "type": "github-releases",
          "repo": "aws/amazon-vpc-cni-k8s",
          "releasesApi": "https://api.github.com/repos/aws/amazon-vpc-cni-k8s/releases"
        },
        {
          "type": "aws-release-notes",
          "url": "https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html"
        }
      ],
      "skipLevelPolicy": {"maxMinorJump": 1},
      "shipsCRDs": false,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "^![[:space:]]",
        "removed?[[:space:]]+(the[[:space:]]+)?(config|configuration|field|flag|env|environment variable)",
        "incompatible with",
        "urgent upgrade note",
        "requires? (network|egress|access to|reachability|connectivity)",
        "new (iam|permission|policy) (required|action)",
        "deprecated"
      ],
      "prLabels": ["breaking-change", "kind/breaking", "kind/breaking-change"],
      "knownIssues": []
    },
    "coredns": {
      "adapter": "coredns",
      "displayName": "CoreDNS",
      "changelogSources": [
        {
          "type": "github-releases",
          "repo": "coredns/coredns",
          "releasesApi": "https://api.github.com/repos/coredns/coredns/releases"
        },
        {
          "type": "aws-release-notes",
          "url": "https://docs.aws.amazon.com/eks/latest/userguide/managing-coredns.html"
        }
      ],
      "skipLevelPolicy": {"maxMinorJump": 1},
      "shipsCRDs": false,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "removed?[[:space:]]+(the[[:space:]]+)?(plugin|directive)",
        "plugin .* removed",
        "urgent upgrade note",
        "requires? (network|egress|access to|reachability|connectivity)",
        "deprecated"
      ],
      "prLabels": ["breaking-change"],
      "knownIssues": []
    },
    "kube-proxy": {
      "adapter": "generic",
      "displayName": "kube-proxy",
      "changelogSources": [
        {
          "type": "aws-release-notes",
          "url": "https://docs.aws.amazon.com/eks/latest/userguide/managing-kube-proxy.html"
        }
      ],
      "skipLevelPolicy": {"maxMinorJump": 1},
      "shipsCRDs": false,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "urgent upgrade note",
        "requires? (network|egress|access to|reachability|connectivity)",
        "new (iam|permission|policy) (required|action)",
        "deprecated"
      ],
      "prLabels": ["breaking-change"],
      "knownIssues": []
    },
    "aws-ebs-csi-driver": {
      "adapter": "generic",
      "displayName": "Amazon EBS CSI Driver",
      "changelogSources": [
        {
          "type": "github-releases",
          "repo": "kubernetes-sigs/aws-ebs-csi-driver",
          "releasesApi": "https://api.github.com/repos/kubernetes-sigs/aws-ebs-csi-driver/releases"
        },
        {
          "type": "aws-release-notes",
          "url": "https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html"
        }
      ],
      "skipLevelPolicy": {"maxMinorJump": null},
      "shipsCRDs": true,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "removed?[[:space:]]+(the[[:space:]]+)?(field|flag|storage class parameter)",
        "^![[:space:]]",
        "urgent upgrade note",
        "MUST read this before you upgrade",
        "requires? (network|egress|access to|reachability|connectivity)",
        "(readiness|liveness) probe",
        "pre.?flight",
        "health check",
        "describe(AvailabilityZones|Instances|SecurityGroups|Subnets)",
        "(sts|ec2|elb|kms|iam)[:.-] ",
        "new (iam|permission|policy) (required|action)",
        "deprecated"
      ],
      "prLabels": ["breaking-change", "release-note-breaking"],
      "knownIssues": [
        {
          "id": "ebs-csi-1.49-preflight-egress",
          "minVersion": "v1.49.0-eksbuild.0",
          "maxVersion": "",
          "grade": "BREAKING_HARD",
          "category": "runtime-precondition",
          "title": "v1.49.0+ adds a dry-run EC2 API pre-flight — requires egress to STS + EC2 endpoints",
          "detail": "Starting in v1.49.0 the EBS CSI controller's readiness/liveness probes periodically issue ec2:DescribeAvailabilityZones with DryRun=true. If the controller pods cannot reach the STS endpoint (for IRSA/Pod-Identity AssumeRoleWithWebIdentity) or the EC2 endpoint on TCP 443, probes fail and the add-on install/upgrade fails with 'Failed health check (verify network connection and IAM credentials)'. Common failure modes: node/pod SG blocks 443 egress; VPC has no NAT and no VPC endpoints for sts.<region>.amazonaws.com / ec2.<region>.amazonaws.com; private DNS disabled on those endpoints; PrivateLink endpoint SGs don't allow the CNI pod CIDR. Reference: https://github.com/kubernetes-sigs/aws-ebs-csi-driver/pull/2590",
          "remediation": "Before upgrading, verify from a controller-adjacent pod: (1) `nslookup sts.<region>.amazonaws.com` resolves; (2) `curl -v https://sts.<region>.amazonaws.com/` connects (a 400/403 is fine — timeouts are the problem); (3) same for `ec2.<region>.amazonaws.com`. If using VPC endpoints: ensure endpoint SGs allow 443 from the pod CIDR (or node SG if using host networking) and 'Enable DNS Name' is on. If v1.62.0+ is a valid target, you can use the plugin method to disable/override the health check as a temporary workaround.",
          "rollback": "aws eks update-addon --cluster-name <c> --addon-name aws-ebs-csi-driver --addon-version <previous>"
        }
      ]
    },
    "aws-efs-csi-driver": {
      "adapter": "generic",
      "displayName": "Amazon EFS CSI Driver",
      "changelogSources": [
        {
          "type": "github-releases",
          "repo": "kubernetes-sigs/aws-efs-csi-driver",
          "releasesApi": "https://api.github.com/repos/kubernetes-sigs/aws-efs-csi-driver/releases"
        },
        {
          "type": "aws-release-notes",
          "url": "https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html"
        }
      ],
      "skipLevelPolicy": {"maxMinorJump": null},
      "shipsCRDs": false,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "^![[:space:]]",
        "urgent upgrade note",
        "requires? (network|egress|access to|reachability|connectivity)",
        "(readiness|liveness) probe",
        "pre.?flight",
        "health check",
        "new (iam|permission|policy) (required|action)",
        "deprecated"
      ],
      "prLabels": ["breaking-change"],
      "knownIssues": []
    },
    "eks-pod-identity-agent": {
      "adapter": "generic",
      "displayName": "EKS Pod Identity Agent",
      "changelogSources": [
        {
          "type": "aws-release-notes",
          "url": "https://docs.aws.amazon.com/eks/latest/userguide/pod-id-agent-setup.html"
        }
      ],
      "skipLevelPolicy": {"maxMinorJump": null},
      "shipsCRDs": false,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "urgent upgrade note",
        "requires? (network|egress|access to|reachability|connectivity)",
        "new (iam|permission|policy) (required|action)",
        "deprecated"
      ],
      "prLabels": ["breaking-change"],
      "knownIssues": []
    },
    "adot": {
      "adapter": "generic",
      "displayName": "AWS Distro for OpenTelemetry",
      "changelogSources": [
        {
          "type": "github-releases",
          "repo": "aws-observability/aws-otel-collector",
          "releasesApi": "https://api.github.com/repos/aws-observability/aws-otel-collector/releases"
        }
      ],
      "skipLevelPolicy": {"maxMinorJump": null},
      "shipsCRDs": true,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "^![[:space:]]",
        "urgent upgrade note",
        "requires? (network|egress|access to|reachability|connectivity)",
        "(readiness|liveness) probe",
        "pre.?flight",
        "health check",
        "new (iam|permission|policy) (required|action)",
        "deprecated"
      ],
      "prLabels": ["breaking-change"],
      "knownIssues": []
    },
    "*": {
      "adapter": "generic",
      "displayName": "Generic (unrecognized add-on)",
      "changelogSources": [],
      "skipLevelPolicy": {"maxMinorJump": null},
      "shipsCRDs": false,
      "breakingRegexes": [
        "^BREAKING( CHANGE)?[[:space:]:]",
        "breaking change",
        "^![[:space:]]",
        "urgent upgrade note",
        "requires? (network|egress|access to|reachability|connectivity)",
        "(readiness|liveness) probe",
        "pre.?flight",
        "health check",
        "new (iam|permission|policy) (required|action)",
        "deprecated"
      ],
      "prLabels": ["breaking-change", "kind/breaking"],
      "knownIssues": []
    }
  }
}
EOF_RULES_MANIFEST
}

load_rules() {
  local content=""
  # External manifest is opt-in only; the embedded manifest is the default.
  if [[ -n "$RULES_URL" ]]; then
    local cache_path="$CACHE_DIR/manifest/current.json"
    if content=$(fetch_url "$RULES_URL" "$cache_path" 2>/dev/null); then
      RULES_SOURCE="external"
    else
      warn "requested rules manifest unreachable ($RULES_URL) — falling back to embedded manifest"
      content=""
    fi
  fi
  if [[ -z "$content" ]]; then
    local embedded_path="$CACHE_DIR/manifest/embedded.json"
    embedded_manifest_write "$embedded_path"
    if ! content=$(cat "$embedded_path"); then
      die $E_MANIFEST "embedded manifest failed to load (script is corrupted?)"
    fi
    RULES_SOURCE="embedded"
  fi
  if ! printf '%s' "$content" | jq -e . >/dev/null 2>&1; then
    die $E_MANIFEST "rules manifest is not valid JSON (source=$RULES_SOURCE)"
  fi
  RULES_JSON="$content"
  RULES_SHA_ACTUAL=$(printf '%s' "$content" | { command -v sha256sum >/dev/null 2>&1 && sha256sum || shasum -a 256; } | awk '{print $1}')
  info "rules manifest sha256=$RULES_SHA_ACTUAL (source=$RULES_SOURCE)"
  if [[ -n "$RULES_SHA_EXPECTED" && "$RULES_SHA_EXPECTED" != "$RULES_SHA_ACTUAL" ]]; then
    die $E_MANIFEST "rules manifest SHA mismatch: expected=$RULES_SHA_EXPECTED actual=$RULES_SHA_ACTUAL"
  fi
}

# rules_for <addon> → prints per-addon rules JSON (falls back to "*")
rules_for() {
  local name="$1"
  local entry
  entry=$(printf '%s' "$RULES_JSON" | jq -c --arg n "$name" '.addons[$n] // .addons["*"]')
  printf '%s' "$entry"
}

# ------------------------------------------------------------------------------
# Version comparator: v1.20.4-eksbuild.1
# ------------------------------------------------------------------------------
# Emits: "<up-major> <up-minor> <up-patch> <eksbuild>"
# Non-numeric or unparseable tags (e.g., "helm-chart-aws-ebs-csi-driver-2.30.0")
# resolve to "0 0 0 0" so downstream arithmetic is always safe under `set -u`.
parse_version() {
  local v="$1"
  v="${v#v}"
  local up eks
  if [[ "$v" == *"-eksbuild."* ]]; then
    up="${v%-eksbuild.*}"
    eks="${v##*-eksbuild.}"
  else
    up="$v"
    eks="0"
  fi
  # tolerate trailing pre-release tags on the upstream part (e.g., "-rc.1")
  up="${up%%-*}"
  local mj mn pt
  IFS='.' read -r mj mn pt <<<"$up"
  # Coerce any non-numeric segment to 0 so `(( x < y ))` never sees a bareword.
  [[ "$mj" =~ ^[0-9]+$ ]] || mj=0
  [[ "$mn" =~ ^[0-9]+$ ]] || mn=0
  [[ "$pt" =~ ^[0-9]+$ ]] || pt=0
  [[ "$eks" =~ ^[0-9]+$ ]] || eks=0
  printf '%s %s %s %s' "$mj" "$mn" "$pt" "$eks"
}

# compare_versions <a> <b> → prints -1 / 0 / 1
compare_versions() {
  local a1 a2 a3 a4 b1 b2 b3 b4 pair x y
  read -r a1 a2 a3 a4 <<<"$(parse_version "$1")"
  read -r b1 b2 b3 b4 <<<"$(parse_version "$2")"
  for pair in "$a1 $b1" "$a2 $b2" "$a3 $b3" "$a4 $b4"; do
    read -r x y <<<"$pair"
    if (( x < y )); then echo -1; return; fi
    if (( x > y )); then echo  1; return; fi
  done
  echo 0
}

# same_upstream_version <a> <b> → 0 if a and b have same maj.min.patch upstream
same_upstream_version() {
  local a1 a2 a3 a4 b1 b2 b3 b4
  read -r a1 a2 a3 a4 <<<"$(parse_version "$1")"
  read -r b1 b2 b3 b4 <<<"$(parse_version "$2")"
  [[ "$a1.$a2.$a3" == "$b1.$b2.$b3" ]]
}

# minor_jump <from> <to> → integer difference in minor version
minor_jump() {
  local a1 a2 a3 a4 b1 b2 b3 b4
  read -r a1 a2 a3 a4 <<<"$(parse_version "$1")"
  read -r b1 b2 b3 b4 <<<"$(parse_version "$2")"
  if (( a1 != b1 )); then
    # major version change — treat as > any minor jump limit
    echo 999
    return
  fi
  local diff=$(( b2 - a2 ))
  (( diff < 0 )) && diff=$(( -diff ))
  echo "$diff"
}

# ------------------------------------------------------------------------------
# AWS discovery
# ------------------------------------------------------------------------------
CLUSTER_K8S=""
CLUSTER_ARN=""
ACCOUNT_ID=""
REGION_RESOLVED=""

resolve_cluster() {
  local out
  out=$(aws_call eks describe-cluster --name "$CLUSTER") || die $E_AWS "describe-cluster failed"
  CLUSTER_K8S=$(printf '%s' "$out" | jq -r '.cluster.version')
  CLUSTER_ARN=$(printf '%s' "$out" | jq -r '.cluster.arn')
  ACCOUNT_ID=$(printf '%s' "$CLUSTER_ARN" | awk -F: '{print $5}')
  REGION_RESOLVED=$(printf '%s' "$CLUSTER_ARN" | awk -F: '{print $4}')
  [[ -z "$TARGET_K8S" ]] && TARGET_K8S="$CLUSTER_K8S"
  info "cluster=$CLUSTER k8s=$CLUSTER_K8S target-k8s=$TARGET_K8S account=$ACCOUNT_ID region=$REGION_RESOLVED"
}

list_installed_addons() {
  local out
  out=$(aws_call eks list-addons --cluster-name "$CLUSTER") || die $E_AWS "list-addons failed"
  printf '%s' "$out" | jq -r '.addons[]?'
}

describe_addon() {
  # Never cached: this response is live install state (status/health/config/SA-role)
  # and callers depend on freshness (S3 install-health, S4 IAM signal).
  local name="$1"
  local out
  out=$(aws_call eks describe-addon --cluster-name "$CLUSTER" --addon-name "$name") || return 1
  printf '%s' "$out"
}

describe_addon_versions() {
  local name="$1"
  local cache_path="$CACHE_DIR/api/$REGION_RESOLVED/$ACCOUNT_ID/$CLUSTER/$name/describe-addon-versions.json"
  if content=$(cache_get "$cache_path"); then
    printf '%s' "$content"
    return
  fi
  local out
  out=$(aws_call eks describe-addon-versions --addon-name "$name" --kubernetes-version "$TARGET_K8S") || return 1
  cache_put "$cache_path" "$out"
  printf '%s' "$out"
}

describe_addon_configuration() {
  local name="$1" version="$2"
  local cache_path="$CACHE_DIR/api/$REGION_RESOLVED/$ACCOUNT_ID/$CLUSTER/$name/describe-addon-configuration/${version}.json"
  if content=$(cache_get "$cache_path"); then
    printf '%s' "$content"
    return
  fi
  local out
  if ! out=$(aws_call eks describe-addon-configuration --addon-name "$name" --addon-version "$version" 2>/dev/null); then
    return 1
  fi
  cache_put "$cache_path" "$out"
  printf '%s' "$out"
}

# ------------------------------------------------------------------------------
# Signal collectors — each writes findings to $FINDINGS_FILE as ndjson
# (FINDINGS_FILE is declared near the top with the other scratch-file globals)
# ------------------------------------------------------------------------------
SOURCES_REACHED=""
SOURCES_MISSING=""

_reach()  { SOURCES_REACHED="$SOURCES_REACHED,$1"; }
_missed() { SOURCES_MISSING="$SOURCES_MISSING,$1"; }

emit_finding() {
  # emit_finding <id> <category> <grade> <confidence> <title> <detail> [evidenceJson] [remediation] [rollback]
  local id="$1" category="$2" grade="$3" confidence="$4" title="$5" detail="$6"
  local evidence="${7:-[]}" remediation="${8:-}" rollback="${9:-}"
  jq -cn \
    --arg id "$id" --arg category "$category" --arg grade "$grade" \
    --arg confidence "$confidence" --arg title "$title" --arg detail "$detail" \
    --argjson evidence "$evidence" \
    --arg remediation "$remediation" --arg rollback "$rollback" \
    '{id:$id, category:$category, grade:$grade, confidence:$confidence, title:$title, detail:$detail, evidence:$evidence, remediation:$remediation, rollback:$rollback}' \
    >> "$FINDINGS_FILE"
}

# S1: compatibility with target K8s version
s1_compatibility() {
  local addon="$1" target_version="$2" versions_json="$3"
  local compat_k8s
  compat_k8s=$(printf '%s' "$versions_json" | jq -r --arg v "$target_version" \
    '[.addons[]?.addonVersions[]? | select(.addonVersion==$v) | .compatibilities[]?.clusterVersion] | unique | .[]?')
  if [[ -z "$compat_k8s" ]]; then
    _missed "s1_compat_data"
    return
  fi
  _reach "s1_compat_data"
  if echo "$compat_k8s" | grep -qx "$TARGET_K8S"; then
    dbg "s1: $addon@$target_version compatible with k8s $TARGET_K8S"
    return
  fi
  local compat_list
  compat_list=$(printf '%s' "$compat_k8s" | tr '\n' ',' | sed 's/,$//')
  emit_finding \
    "${addon}-${target_version}-k8s-incompatible" \
    "api" "BREAKING_HARD" "api-derived" \
    "Target version is not compatible with cluster Kubernetes version $TARGET_K8S" \
    "Add-on version $target_version supports Kubernetes: [$compat_list]. Current/target cluster K8s: $TARGET_K8S." \
    "[]" \
    "Choose a target add-on version compatible with $TARGET_K8S, or upgrade the cluster first." \
    ""
}

# S1b: skip-level jump
s1b_skip_level() {
  local addon="$1" current="$2" target="$3" rules="$4"
  local max_jump
  max_jump=$(printf '%s' "$rules" | jq -r '.skipLevelPolicy.maxMinorJump // "null"')
  [[ "$max_jump" == "null" ]] && return
  local jump
  jump=$(minor_jump "$current" "$target")
  if (( jump > max_jump )); then
    emit_finding \
      "${addon}-skip-level-${current}-${target}" \
      "skip-level" "BREAKING_HARD" "api-derived" \
      "Version jump exceeds supported skip-level policy" \
      "This add-on only supports minor version jumps of $max_jump. From $current to $target is $jump minor(s)." \
      "[]" \
      "Upgrade one minor version at a time, or as allowed by AWS documentation." \
      ""
  fi
}

# S2: schema diff between current and target configuration
s2_schema_diff() {
  local addon="$1" current="$2" target="$3" installed_config="$4"
  local cur_cfg tgt_cfg
  cur_cfg=$(describe_addon_configuration "$addon" "$current" || true)
  tgt_cfg=$(describe_addon_configuration "$addon" "$target" || true)
  if [[ -z "$cur_cfg" || -z "$tgt_cfg" ]]; then
    _missed "s2_schema"
    return
  fi
  _reach "s2_schema"

  local cur_schema tgt_schema
  cur_schema=$(printf '%s' "$cur_cfg" | jq -c '.configurationSchema // empty | fromjson? // empty')
  tgt_schema=$(printf '%s' "$tgt_cfg" | jq -c '.configurationSchema // empty | fromjson? // empty')
  if [[ -z "$cur_schema" || -z "$tgt_schema" ]]; then
    dbg "s2: no configurationSchema available for $addon"
    return
  fi

  local cur_props tgt_props tgt_required
  cur_props=$(printf '%s' "$cur_schema" | jq -r '(.properties // {}) | keys[]?' | sort -u)
  tgt_props=$(printf '%s' "$tgt_schema" | jq -r '(.properties // {}) | keys[]?' | sort -u)
  tgt_required=$(printf '%s' "$tgt_schema" | jq -r '(.required // []) | .[]?' | sort -u)

  local removed added
  removed=$(comm -23 <(printf '%s\n' "$cur_props") <(printf '%s\n' "$tgt_props"))
  added=$(comm -13 <(printf '%s\n' "$cur_props") <(printf '%s\n' "$tgt_props"))

  local installed_keys=""
  if [[ -n "$installed_config" ]]; then
    installed_keys=$(printf '%s' "$installed_config" | jq -r 'try (fromjson? // .) | if type=="object" then keys[]? else empty end' 2>/dev/null | sort -u)
  fi

  local f
  for f in $removed; do
    [[ -z "$f" ]] && continue
    if echo "$installed_keys" | grep -qx "$f"; then
      emit_finding \
        "${addon}-${target}-removed-field-inuse-${f}" \
        "config-schema" "BREAKING_HARD" "schema-derived" \
        "Removed configuration field currently in use: $f" \
        "Field '$f' was removed in $target. Your current install sets this field." \
        "$(jq -cn --arg f "$f" '[{type:"config-schema",field:$f,inUse:true}]')" \
        "Remove or migrate '$f' in configurationValues before upgrading. Consult add-on release notes." \
        ""
    else
      emit_finding \
        "${addon}-${target}-removed-field-${f}" \
        "config-schema" "SOFT" "schema-derived" \
        "Configuration field removed: $f" \
        "Field '$f' is present in $current schema but absent in $target." \
        "$(jq -cn --arg f "$f" '[{type:"config-schema",field:$f,inUse:false}]')" \
        "No action required if you were not setting this field." \
        ""
    fi
  done

  for f in $added; do
    [[ -z "$f" ]] && continue
    local is_required=0
    if echo "$tgt_required" | grep -qx "$f"; then is_required=1; fi
    local has_default
    has_default=$(printf '%s' "$tgt_schema" | jq -r --arg f "$f" '.properties[$f].default // empty')
    if (( is_required == 1 )) && [[ -z "$has_default" ]]; then
      emit_finding \
        "${addon}-${target}-new-required-${f}" \
        "config-schema" "BREAKING_HARD" "schema-derived" \
        "New required configuration field without default: $f" \
        "Target $target adds required field '$f' with no default." \
        "$(jq -cn --arg f "$f" '[{type:"config-schema",field:$f,required:true,default:null}]')" \
        "Set '$f' in configurationValues before upgrading." \
        ""
    elif (( is_required == 1 )); then
      emit_finding \
        "${addon}-${target}-new-required-with-default-${f}" \
        "config-schema" "SOFT" "schema-derived" \
        "New required configuration field with default: $f" \
        "Target $target adds required field '$f' with default value." \
        "$(jq -cn --arg f "$f" '[{type:"config-schema",field:$f,required:true,hasDefault:true}]')" \
        "Review the default; override in configurationValues if needed." \
        ""
    fi
  done
}

# S3: current install health
s3_install_health() {
  local addon="$1" describe_json="$2"
  local status
  status=$(printf '%s' "$describe_json" | jq -r '.addon.status // "UNKNOWN"')
  _reach "s3_install"
  case "$status" in
    ACTIVE|UPDATING|CREATING) return ;;
    DEGRADED|CREATE_FAILED|UPDATE_FAILED|DELETE_FAILED)
      emit_finding \
        "${addon}-current-unhealthy" \
        "install-health" "BREAKING_HARD" "api-derived" \
        "Current add-on install is unhealthy (status=$status)" \
        "Address the underlying failure before attempting an upgrade — issues will compound." \
        "$(jq -cn --arg s "$status" '[{type:"aws-api",action:"DescribeAddon",status:$s}]')" \
        "Run: aws eks describe-addon --cluster-name <c> --addon-name $addon and address the status/health issues." \
        ""
      ;;
  esac
}

# S4: IAM policy diff (best-effort — recommended policies aren't always exposed per version)
s4_iam_diff() {
  local addon="$1" describe_json="$2" versions_json="$3" current="$4" target="$5"
  # `describe-addon-versions` may include `requiresIamPermissions` under configurationValues; if not, skip
  local requires_iam
  requires_iam=$(printf '%s' "$versions_json" | jq -r --arg v "$target" \
    '[.addons[]?.addonVersions[]? | select(.addonVersion==$v) | .requiresIamPermissions // empty] | .[0] // empty' 2>/dev/null || true)
  if [[ -z "$requires_iam" || "$requires_iam" == "null" ]]; then
    _missed "s4_iam"
    return
  fi
  _reach "s4_iam"
  # For launch, emit a SOFT finding when IAM requirements exist and the current install lacks a pod-identity or SA role reference.
  local sa_role
  sa_role=$(printf '%s' "$describe_json" | jq -r '.addon.serviceAccountRoleArn // empty')
  if [[ -z "$sa_role" ]]; then
    emit_finding \
      "${addon}-${target}-iam-service-account-missing" \
      "iam" "SOFT" "api-derived" \
      "Target version has IAM requirements; add-on has no serviceAccountRoleArn attached" \
      "Verify the required IAM permissions and attach an IRSA/Pod Identity role if needed." \
      "[]" \
      "See AWS docs for the add-on's recommended IAM policy." \
      ""
  fi
}

# S5: upstream changelog scan
s5_changelog() {
  local addon="$1" current="$2" target="$3" rules="$4"
  local sources
  sources=$(printf '%s' "$rules" | jq -c '.changelogSources // []')
  local count
  count=$(printf '%s' "$sources" | jq -r 'length')
  if (( count == 0 )); then
    _missed "s5_changelog"
    return
  fi

  local any_reached=0 any_signal=0 breaking_hits=0
  local i src type url content
  for i in $(seq 0 $((count-1))); do
    src=$(printf '%s' "$sources" | jq -c ".[$i]")
    type=$(printf '%s' "$src" | jq -r '.type')
    case "$type" in
      github-releases)
        url=$(printf '%s' "$src" | jq -r '.releasesApi')
        local cache_path="$CACHE_DIR/changelogs/${addon}/gh_$(printf '%s' "$url" | { command -v sha256sum >/dev/null 2>&1 && sha256sum || shasum -a 256; } | awk '{print $1}').json"
        if content=$(fetch_url "$url" "$cache_path"); then
          any_reached=1
          local hits
          hits=$(printf '%s' "$content" | jq -c --arg from "$current" --arg to "$target" \
            '[.[]? | select(.tag_name!=null) | {tag:.tag_name, name:.name, body:.body, labels:[]} ]' 2>/dev/null || echo "[]")
          if [[ "$hits" != "[]" ]]; then
            any_signal=1
            local hits_between
            hits_between=$(printf '%s' "$hits" | jq -c --arg cur "$current" --arg tgt "$target" \
              '[.[] | select(.tag != null)]' 2>/dev/null || echo "[]")
            local n j entry body tag
            n=$(printf '%s' "$hits_between" | jq -r 'length')
            for j in $(seq 0 $((n-1))); do
              entry=$(printf '%s' "$hits_between" | jq -c ".[$j]")
              tag=$(printf '%s' "$entry" | jq -r '.tag')
              body=$(printf '%s' "$entry" | jq -r '.body // ""')
              # Include tag only if it strictly falls between current and target (exclusive of current, inclusive of target)
              local cmp_cur cmp_tgt
              cmp_cur=$(compare_versions "$tag" "$current")
              cmp_tgt=$(compare_versions "$tag" "$target")
              if (( cmp_cur > 0 && cmp_tgt <= 0 )); then
                # regex-scan the body for breaking markers
                local regex_list regex hit=0
                regex_list=$(printf '%s' "$rules" | jq -r '.breakingRegexes[]?')
                while IFS= read -r regex; do
                  [[ -z "$regex" ]] && continue
                  if printf '%s' "$body" | grep -Eqi -- "$regex"; then hit=1; break; fi
                done <<<"$regex_list"
                if (( hit == 1 )); then
                  breaking_hits=$((breaking_hits+1))
                  emit_finding \
                    "${addon}-${target}-upstream-breaking-${tag}" \
                    "changelog" "SOFT" "single-signal-heuristic" \
                    "Upstream release $tag flags a breaking change" \
                    "Regex match in release notes for $tag. Review manually to confirm impact." \
                    "$(jq -cn --arg t "$tag" '[{type:"github-releases",tag:$t}]')" \
                    "Read upstream release notes for $tag; migrate any usage of the removed or changed surface." \
                    ""
                fi
              fi
            done
          fi
        else
          :
        fi
        ;;
      aws-release-notes)
        url=$(printf '%s' "$src" | jq -r '.url')
        local cache_path="$CACHE_DIR/changelogs/${addon}/aws_$(printf '%s' "$url" | { command -v sha256sum >/dev/null 2>&1 && sha256sum || shasum -a 256; } | awk '{print $1}').html"
        if content=$(fetch_url "$url" "$cache_path"); then
          any_reached=1
          # very light heuristic — search page for target version + "breaking" nearby.
          # -F: match the version as a literal string so the dots don't act as
          # regex "any char" wildcards (e.g. v1.49.0 must not match v1X49X0).
          if printf '%s' "$content" | grep -Fqi -- "$target"; then
            if printf '%s' "$content" | grep -Eqi -- "breaking|deprecat|removed"; then
              any_signal=1
              breaking_hits=$((breaking_hits+1))
              emit_finding \
                "${addon}-${target}-aws-release-notes" \
                "changelog" "FYI" "single-signal-heuristic" \
                "AWS release notes mention target version near 'breaking/deprecated/removed'" \
                "Manual review recommended: $url" \
                "$(jq -cn --arg u "$url" '[{type:"aws-release-notes",url:$u}]')" \
                "Read the AWS documentation section for $target." \
                ""
            fi
          fi
        fi
        ;;
    esac
  done
  if (( any_reached == 1 )); then _reach "s5_changelog"; else _missed "s5_changelog"; fi
}

# S7: curated known-issue registry (per-addon, per-version)
# Each entry in manifest.addons.<name>.knownIssues[] has:
#   { id, minVersion (inclusive), maxVersion (inclusive; "" = unbounded),
#     grade, category, title, detail, remediation, rollback? }
# A known-issue fires when the *target* falls inside [minVersion, maxVersion].
# Because entries are human-authored, findings carry confidence=curated.
s7_known_issues() {
  local addon="$1" current="$2" target="$3" rules="$4"
  local issues
  issues=$(printf '%s' "$rules" | jq -c '.knownIssues // []')
  local count
  count=$(printf '%s' "$issues" | jq -r 'length')
  if (( count == 0 )); then
    _missed "s7_known_issues"
    return
  fi
  _reach "s7_known_issues"

  local i entry id min_v max_v grade category title detail remediation rollback
  for i in $(seq 0 $((count-1))); do
    entry=$(printf '%s' "$issues" | jq -c ".[$i]")
    id=$(printf '%s' "$entry" | jq -r '.id')
    min_v=$(printf '%s' "$entry" | jq -r '.minVersion // ""')
    max_v=$(printf '%s' "$entry" | jq -r '.maxVersion // ""')
    grade=$(printf '%s' "$entry" | jq -r '.grade // "SOFT"')
    category=$(printf '%s' "$entry" | jq -r '.category // "known-issue"')
    title=$(printf '%s' "$entry" | jq -r '.title')
    detail=$(printf '%s' "$entry" | jq -r '.detail // ""')
    remediation=$(printf '%s' "$entry" | jq -r '.remediation // ""')
    rollback=$(printf '%s' "$entry" | jq -r '.rollback // ""')

    # Range check: target >= min_v AND (max_v == "" OR target <= max_v)
    if [[ -n "$min_v" ]] && (( $(compare_versions "$target" "$min_v") < 0 )); then continue; fi
    if [[ -n "$max_v" ]] && (( $(compare_versions "$target" "$max_v") > 0 )); then continue; fi

    emit_finding \
      "$id" \
      "$category" "$grade" "curated" \
      "$title" "$detail" \
      "$(jq -cn --arg id "$id" --arg min "$min_v" --arg max "$max_v" \
          '[{type:"known-issue",id:$id,versionRange:{min:$min,max:$max}}]')" \
      "$remediation" \
      "$rollback"
  done
}

# ------------------------------------------------------------------------------
# Analyze one (addon, current, target) triple
# ------------------------------------------------------------------------------
analyze_one() {
  local addon="$1" current="$2" target="$3" describe_json="$4" versions_json="$5"

  SOURCES_REACHED=""
  SOURCES_MISSING=""
  : > "$FINDINGS_FILE"

  local rules
  rules=$(rules_for "$addon")
  local installed_config
  installed_config=$(printf '%s' "$describe_json" | jq -r '.addon.configurationValues // empty')

  s1_compatibility "$addon" "$target" "$versions_json"
  s1b_skip_level  "$addon" "$current" "$target" "$rules"
  s2_schema_diff  "$addon" "$current" "$target" "$installed_config"
  s3_install_health "$addon" "$describe_json"
  s4_iam_diff     "$addon" "$describe_json" "$versions_json" "$current" "$target"

  # If we're bumping only the eksbuild suffix, skip upstream S5.
  if ! same_upstream_version "$current" "$target"; then
    s5_changelog "$addon" "$current" "$target" "$rules"
  else
    _missed "s5_changelog_skipped_same_upstream"
  fi

  # S7 always runs — curated known issues apply regardless of upstream vs eksbuild jump.
  s7_known_issues "$addon" "$current" "$target" "$rules"

  # Heuristic findings (S5) are already capped at SOFT/FYI by their emit_finding
  # calls above, so no separate downgrade pass is needed here.

  # Compute overall grade from findings
  local overall="CLEAN"
  local worst_ord=0
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local g o
    g=$(printf '%s' "$line" | jq -r '.grade')
    o=$(grade_ord "$g")
    if (( o > worst_ord )); then worst_ord=$o; overall="$g"; fi
  done < "$FINDINGS_FILE"

  local findings_arr
  findings_arr=$(jq -s '.' < "$FINDINGS_FILE")

  local reached_arr missing_arr
  reached_arr=$(printf '%s' "${SOURCES_REACHED#,}" | jq -R -s -c 'split(",") | map(select(length > 0)) | unique')
  missing_arr=$(printf '%s' "${SOURCES_MISSING#,}" | jq -R -s -c 'split(",") | map(select(length > 0)) | unique')

  jq -cn \
    --arg name "$addon" \
    --arg current "$current" \
    --arg target "$target" \
    --arg grade "$overall" \
    --argjson findings "$findings_arr" \
    --argjson reached "$reached_arr" \
    --argjson missing "$missing_arr" \
    '{name:$name, currentVersion:$current, targetVersion:$target, grade:$grade, sourcesReached:$reached, sourcesMissing:$missing, findings:$findings}'
}

# ------------------------------------------------------------------------------
# Resolve default target version for an add-on & K8s version
# ------------------------------------------------------------------------------
default_target_for() {
  local addon="$1" versions_json="$2"
  printf '%s' "$versions_json" | jq -r --arg k "$TARGET_K8S" '
    [.addons[]?.addonVersions[]?
      | select(.compatibilities[]?.clusterVersion == $k)
      | select(.compatibilities[]?.defaultVersion == true)
      | .addonVersion] | first // empty'
}

# All upgrade candidate versions (strictly greater than current, compatible with target K8s)
enumerate_upgrade_candidates() {
  local current="$1" versions_json="$2"
  local candidates
  candidates=$(printf '%s' "$versions_json" | jq -r --arg k "$TARGET_K8S" '
    [.addons[]?.addonVersions[]?
      | select(.compatibilities[]?.clusterVersion == $k)
      | .addonVersion] | unique | .[]?')
  local v
  while IFS= read -r v; do
    [[ -z "$v" ]] && continue
    if (( $(compare_versions "$v" "$current") > 0 )); then
      echo "$v"
    fi
  done <<<"$candidates"
}

# ------------------------------------------------------------------------------
# Main analysis pipeline
# ------------------------------------------------------------------------------
# (ADDON_RESULTS_FILE is declared near the top with the other scratch-file globals)
ANY_PARTIAL=0
run_pipeline() {
  ADDON_RESULTS_FILE=$(mktemp)
  FINDINGS_FILE=$(mktemp)

  local addons=()
  case "$MODE" in
    single) addons=("$ADDON") ;;
    discover|flag-all-upper)
      if [[ -n "$ADDON" ]]; then addons=("$ADDON")
      else
        # Portable equivalent of `mapfile -t addons < <(...)` — mapfile is
        # a bash 4+ builtin, absent on macOS default bash (3.2).
        addons=()
        while IFS= read -r _line; do
          [[ -n "$_line" ]] && addons+=("$_line")
        done < <(list_installed_addons)
      fi
      ;;
  esac

  if (( ${#addons[@]} == 0 )); then
    warn "no add-ons found on cluster"
  else
    if [[ -n "$ADDON" ]]; then
      info "target add-on: $ADDON"
    else
      # Names only, comma-separated. Local IFS keeps the change scoped to
      # this expansion and works identically on bash 3.2 / 4 / 5.
      local _list
      _list=$(IFS=,; printf '%s' "${addons[*]}")
      _list=${_list//,/, }
      info "discovered add-ons on cluster: $_list (${#addons[@]})"
    fi
  fi

  local any_partial=$ANY_PARTIAL
  local a
  # Guard against bash 3.2 + `set -u` erroring on empty-array expansion.
  for a in ${addons[@]+"${addons[@]}"}; do
    [[ -z "$a" ]] && continue
    info "analyzing $a"
    local describe_json versions_json
    if ! describe_json=$(describe_addon "$a"); then
      warn "$a: describe-addon failed — skipping"
      any_partial=1
      continue
    fi
    if ! versions_json=$(describe_addon_versions "$a"); then
      warn "$a: describe-addon-versions failed — skipping"
      any_partial=1
      continue
    fi
    local current
    current=$(printf '%s' "$describe_json" | jq -r '.addon.addonVersion // empty')
    [[ -z "$current" ]] && { warn "$a: no currentVersion — skipping"; any_partial=1; continue; }

    case "$MODE" in
      flag-all-upper)
        local target
        while IFS= read -r target; do
          [[ -z "$target" ]] && continue
          local result
          result=$(analyze_one "$a" "$current" "$target" "$describe_json" "$versions_json")
          printf '%s\n' "$result" >> "$ADDON_RESULTS_FILE"
        done < <(enumerate_upgrade_candidates "$current" "$versions_json")
        ;;
      *)
        local target="$TARGET_VERSION"
        if [[ -z "$target" ]]; then
          target=$(default_target_for "$a" "$versions_json")
        fi
        if [[ -z "$target" ]]; then
          warn "$a: no target version resolvable — skipping"
          any_partial=1
          continue
        fi
        if [[ "$target" == "$current" ]]; then
          info "$a: already at $current — nothing to check"
          local result
          result=$(jq -cn --arg n "$a" --arg v "$current" \
            '{name:$n, currentVersion:$v, targetVersion:$v, grade:"CLEAN", sourcesReached:[], sourcesMissing:[], findings:[]}')
          printf '%s\n' "$result" >> "$ADDON_RESULTS_FILE"
          continue
        fi
        local result
        result=$(analyze_one "$a" "$current" "$target" "$describe_json" "$versions_json")
        printf '%s\n' "$result" >> "$ADDON_RESULTS_FILE"
        ;;
    esac
  done

  ANY_PARTIAL="$any_partial"
}

# ------------------------------------------------------------------------------
# Report rendering
# ------------------------------------------------------------------------------
build_json_report() {
  local generated_at
  generated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  local addons_arr
  addons_arr=$(jq -s '.' < "$ADDON_RESULTS_FILE")

  # Two rollups:
  #   byGrade         → count of ADD-ONS at each overall grade (fleet view)
  #   findingsByGrade → count of individual FINDINGS at each grade (detail view)
  #   totalAddons / totalFindings → convenience totals
  local summary
  summary=$(printf '%s' "$addons_arr" | jq '
    {
      totalAddons: length,
      totalFindings: ([.[].findings | length] | add // 0),
      byGrade: (reduce .[] as $a ({CLEAN:0,FYI:0,SOFT:0,BREAKING_HARD:0,UNKNOWN:0};
                 .[$a.grade] += 1)),
      findingsByGrade: (reduce (.[].findings // [])[] as $f
                          ({CLEAN:0,FYI:0,SOFT:0,BREAKING_HARD:0,UNKNOWN:0};
                           .[$f.grade] += 1))
    }')

  local report
  report=$(jq -n \
    --arg schemaVersion "1.0" \
    --arg producedBy "$SCRIPT_NAME" \
    --arg producedByVersion "$SCRIPT_VERSION" \
    --arg manifestSha "$RULES_SHA_ACTUAL" \
    --arg generatedAt "$generated_at" \
    --arg cluster "$CLUSTER" \
    --arg region "$REGION_RESOLVED" \
    --arg currentK8s "$CLUSTER_K8S" \
    --arg targetK8s "$TARGET_K8S" \
    --argjson addons "$addons_arr" \
    --argjson summary "$summary" \
    '{
      schemaVersion:$schemaVersion,
      producedBy:$producedBy,
      producedByVersion:$producedByVersion,
      rulesManifestSha256:$manifestSha,
      generatedAt:$generatedAt,
      cluster:{
        name:$cluster, region:$region,
        currentKubernetesVersion:$currentK8s,
        targetKubernetesVersion:$targetK8s
      },
      addons:$addons,
      summary:$summary
    }')

  # reportId = sha256 over addons + inputs (stable across identical runs)
  local canonical
  canonical=$(printf '%s' "$report" | jq -S 'del(.generatedAt)')
  local rid
  rid=$(printf '%s' "$canonical" | { command -v sha256sum >/dev/null 2>&1 && sha256sum || shasum -a 256; } | awk '{print "sha256:"$1}')
  printf '%s' "$report" | jq --arg rid "$rid" '. + {reportId:$rid}'
}

grade_badge() {
  case "$1" in
    CLEAN)          printf '%sCLEAN%s' "$_c_green" "$_c_reset" ;;
    FYI)            printf '%sFYI%s' "$_c_blue" "$_c_reset" ;;
    SOFT)           printf '%sSOFT%s' "$_c_yellow" "$_c_reset" ;;
    BREAKING_HARD)  printf '%sBREAKING_HARD%s' "$_c_red" "$_c_reset" ;;
    *)              printf '%s' "$1" ;;
  esac
}

render_markdown() {
  local report="$1"
  local rid cluster region cur_k8s tgt_k8s gen manifest_sha
  rid=$(printf '%s' "$report" | jq -r '.reportId')
  cluster=$(printf '%s' "$report" | jq -r '.cluster.name')
  region=$(printf '%s' "$report" | jq -r '.cluster.region')
  cur_k8s=$(printf '%s' "$report" | jq -r '.cluster.currentKubernetesVersion')
  tgt_k8s=$(printf '%s' "$report" | jq -r '.cluster.targetKubernetesVersion')
  gen=$(printf '%s' "$report" | jq -r '.generatedAt')
  manifest_sha=$(printf '%s' "$report" | jq -r '.rulesManifestSha256')

  # `--` guards against printf treating a leading `-` in the format as a flag.
  printf -- '\n# EKS Add-on Upgrade Compatibility Report\n\n'
  printf -- '- **Cluster:** `%s` (%s)\n' "$cluster" "$region"
  printf -- '- **Kubernetes:** current=%s, target=%s\n' "$cur_k8s" "$tgt_k8s"
  printf -- '- **Generated:** %s\n' "$gen"
  printf -- '- **Report ID:** `%s`\n' "$rid"
  printf -- '- **Rules manifest SHA-256:** `%s`\n\n' "$manifest_sha"

  local n i addon name grade current target findings_len
  n=$(printf '%s' "$report" | jq -r '.addons | length')
  for i in $(seq 0 $((n-1))); do
    addon=$(printf '%s' "$report" | jq -c ".addons[$i]")
    name=$(printf '%s' "$addon" | jq -r '.name')
    grade=$(printf '%s' "$addon" | jq -r '.grade')
    current=$(printf '%s' "$addon" | jq -r '.currentVersion')
    target=$(printf '%s' "$addon" | jq -r '.targetVersion')
    findings_len=$(printf '%s' "$addon" | jq -r '.findings | length')

    printf '## %s — [%s]\n\n' "$name" "$(grade_badge "$grade")"
    printf 'Current → Target: `%s` → `%s`\n\n' "$current" "$target"

    if (( findings_len == 0 )); then
      printf '_No findings._\n\n'
    else
      printf '| Grade | Category | Confidence | Title |\n'
      printf '|-------|----------|------------|-------|\n'
      local j f
      for j in $(seq 0 $((findings_len-1))); do
        f=$(printf '%s' "$addon" | jq -c ".findings[$j]")
        printf '| %s | %s | %s | %s |\n' \
          "$(printf '%s' "$f" | jq -r '.grade')" \
          "$(printf '%s' "$f" | jq -r '.category')" \
          "$(printf '%s' "$f" | jq -r '.confidence')" \
          "$(printf '%s' "$f" | jq -r '.title')"
      done
      printf '\n'
      for j in $(seq 0 $((findings_len-1))); do
        f=$(printf '%s' "$addon" | jq -c ".findings[$j]")
        printf '### %s\n\n' "$(printf '%s' "$f" | jq -r '.title')"
        printf -- '- **Grade:** %s\n' "$(printf '%s' "$f" | jq -r '.grade')"
        printf -- '- **Category:** %s\n' "$(printf '%s' "$f" | jq -r '.category')"
        printf -- '- **Confidence:** %s\n' "$(printf '%s' "$f" | jq -r '.confidence')"
        printf -- '- **Detail:** %s\n' "$(printf '%s' "$f" | jq -r '.detail')"
        local remediation rollback
        remediation=$(printf '%s' "$f" | jq -r '.remediation // ""')
        rollback=$(printf '%s' "$f" | jq -r '.rollback // ""')
        [[ -n "$remediation" ]] && printf -- '- **Remediation:** %s\n' "$remediation"
        [[ -n "$rollback" ]] && printf -- '- **Rollback:** `%s`\n' "$rollback"
        printf '\n'
      done
    fi
    printf 'Sources reached: %s\n' "$(printf '%s' "$addon" | jq -r '.sourcesReached | join(", ")')"
    printf 'Sources missing: %s\n\n' "$(printf '%s' "$addon" | jq -r '.sourcesMissing | join(", ")')"
    printf -- '---\n\n'
  done

  # Summary — two rollups: findings (detail) and add-ons (fleet)
  local total_addons total_findings
  total_addons=$(printf '%s' "$report" | jq -r '.summary.totalAddons // 0')
  total_findings=$(printf '%s' "$report" | jq -r '.summary.totalFindings // 0')

  printf '## Summary\n\n'
  printf 'Analyzed %s add-on(s), produced %s finding(s).\n\n' "$total_addons" "$total_findings"

  printf '### Findings by grade\n\n'
  printf '| Grade | Findings |\n|-------|---------:|\n'
  local g
  for g in CLEAN FYI SOFT BREAKING_HARD UNKNOWN; do
    printf '| %s | %s |\n' "$g" "$(printf '%s' "$report" | jq -r --arg g "$g" '.summary.findingsByGrade[$g] // 0')"
  done
  printf '\n'

  printf '### Add-ons by overall grade\n\n'
  printf '| Grade | Add-ons |\n|-------|--------:|\n'
  for g in CLEAN FYI SOFT BREAKING_HARD UNKNOWN; do
    printf '| %s | %s |\n' "$g" "$(printf '%s' "$report" | jq -r --arg g "$g" '.summary.byGrade[$g] // 0')"
  done
  printf '\n'
}

# ------------------------------------------------------------------------------
# Overall grade → exit code
# ------------------------------------------------------------------------------
compute_exit_code() {
  local report="$1" any_partial="$2"
  local threshold_ord
  threshold_ord=$(min_grade_ord "$MIN_GRADE")

  local worst=0 name_worst=""
  local i n g o
  n=$(printf '%s' "$report" | jq -r '.addons | length')
  for i in $(seq 0 $((n-1))); do
    g=$(printf '%s' "$report" | jq -r ".addons[$i].grade")
    o=$(grade_ord "$g")
    if (( o > worst )); then worst=$o; name_worst=$(printf '%s' "$report" | jq -r ".addons[$i].name"); fi
  done

  # Map grade ordinal to exit code
  local code=$E_CLEAN
  if   (( worst >= 3 )); then code=$E_BREAKING
  elif (( worst == 2 )); then code=$E_SOFT
  elif (( worst == 1 )); then code=$E_FYI
  fi

  # If the worst grade is below the operator's threshold, treat as clean
  if (( worst < threshold_ord )); then code=$E_CLEAN; fi

  # Partial data supersedes if code is otherwise clean
  if [[ "$any_partial" == "1" && $code -eq $E_CLEAN ]]; then code=$E_PARTIAL; fi

  info "worst grade: $worst${name_worst:+ ($name_worst)} → exit $code"
  echo "$code"
}

# ------------------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------------------
emit_metrics() {
  [[ -z "$METRICS_OUT" ]] && return
  local report="$1" exit_code="$2"
  jq -n \
    --arg script "$SCRIPT_NAME" \
    --arg version "$SCRIPT_VERSION" \
    --arg manifest "$RULES_SHA_ACTUAL" \
    --argjson byGrade "$(printf '%s' "$report" | jq '.summary.byGrade')" \
    --arg exitCode "$exit_code" \
    --arg cluster "$CLUSTER" \
    '{script:$script, version:$version, manifestSha:$manifest, cluster:$cluster,
      grades:$byGrade, exitCode:($exitCode|tonumber)}' > "$METRICS_OUT"
  info "metrics written to $METRICS_OUT"
}

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
main() {
  parse_args "$@"
  init_colors
  preflight
  load_rules
  resolve_cluster

  # Call directly (not in a subshell) so ADDON_RESULTS_FILE / FINDINGS_FILE
  # / ANY_PARTIAL propagate back to main.
  run_pipeline
  local any_partial="$ANY_PARTIAL"

  local report
  report=$(build_json_report)

  case "$FORMAT" in
    markdown) render_markdown "$report" ;;
    json)     printf '%s\n' "$report" | jq . ;;
    both)     render_markdown "$report"; printf '\n'; printf '%s\n' "$report" | jq . ;;
  esac

  if [[ -n "$JSON_OUT" ]]; then
    printf '%s\n' "$report" | jq . > "$JSON_OUT"
    info "json report written to $JSON_OUT"
  fi

  local code
  code=$(compute_exit_code "$report" "$any_partial")
  emit_metrics "$report" "$code"

  # Scratch files are removed by the EXIT trap (see cleanup()).
  exit "$code"
}

main "$@"
