#!/usr/bin/env bash
set -euo pipefail

HARNESS_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$HARNESS_SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$HARNESS_DIR/.." && pwd)"

timestamp_utc() {
  date -u +%Y%m%dT%H%M%SZ
}

load_env_if_present() {
  local file="$1"
  if [[ -f "$file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$file"
    set +a
  fi
}

load_harness_env() {
  load_env_if_present "$HARNESS_DIR/config/aws.env"
  load_env_if_present "$HARNESS_DIR/config/experiment.env"
}

require_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "missing required command: $name" >&2
    exit 127
  fi
}

print_kv() {
  printf '%s=%s\n' "$1" "$2"
}
