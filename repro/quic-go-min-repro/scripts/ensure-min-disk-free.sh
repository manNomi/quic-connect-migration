#!/usr/bin/env bash
set -euo pipefail

MIN_GIB="${1:-${MIN_ARTIFACT_FREE_GIB:-5}}"
CHECK_DIR="${2:-.}"

if [[ "$MIN_GIB" == "0" || "$MIN_GIB" == "0.0" ]]; then
  exit 0
fi

FREE_KIB="$(df -Pk "$CHECK_DIR" | awk 'NR==2 {print $4}')"
REQUIRED_KIB="$(python3 - "$MIN_GIB" <<'PY'
import math
import sys

print(math.ceil(float(sys.argv[1]) * 1024 * 1024))
PY
)"

if [[ -z "$FREE_KIB" || "$FREE_KIB" -lt "$REQUIRED_KIB" ]]; then
  FREE_GIB="$(python3 - "$FREE_KIB" <<'PY'
import sys

print(f"{int(sys.argv[1]) / (1024 * 1024):.2f}")
PY
)"
  echo "disk guard failed: ${FREE_GIB} GiB free under $CHECK_DIR, require at least ${MIN_GIB} GiB" >&2
  echo "set MIN_ARTIFACT_FREE_GIB=0 only for deliberate small smoke tests without heavy NetLog/qlog capture" >&2
  exit 2
fi
