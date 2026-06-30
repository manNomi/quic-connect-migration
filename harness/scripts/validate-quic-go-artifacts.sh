#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <artifact-dir>" >&2
  exit 2
fi

ARTIFACT_DIR="$1"
SUMMARY="$ARTIFACT_DIR/results/harness-validation.txt"

mkdir -p "$ARTIFACT_DIR/results"

fail() {
  printf 'validation=fail\nreason=%s\n' "$1" | tee "$SUMMARY" >&2
  exit 1
}

[[ -f "$ARTIFACT_DIR/results/client.json" ]] || fail "missing client.json"
[[ -f "$ARTIFACT_DIR/results/server.json" ]] || fail "missing server.json"
[[ -d "$ARTIFACT_DIR/qlog" ]] || fail "missing qlog directory"

if command -v jq >/dev/null 2>&1; then
  [[ "$(jq -r '.ok' "$ARTIFACT_DIR/results/client.json")" == "true" ]] || fail "client ok is not true"
  [[ "$(jq -r '.ok' "$ARTIFACT_DIR/results/server.json")" == "true" ]] || fail "server ok is not true"
else
  grep -q '"ok"[[:space:]]*:[[:space:]]*true' "$ARTIFACT_DIR/results/client.json" || fail "client ok is not true"
  grep -q '"ok"[[:space:]]*:[[:space:]]*true' "$ARTIFACT_DIR/results/server.json" || fail "server ok is not true"
fi

if command -v rg >/dev/null 2>&1; then
  rg --no-ignore --text -n "path_challenge|path_response" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
else
  grep -R -n -E "path_challenge|path_response" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
fi

[[ -s "$ARTIFACT_DIR/results/qlog-path-validation.txt" ]] || fail "missing qlog path validation evidence"

{
  printf 'validation=ok\n'
  printf 'artifact_dir=%s\n' "$ARTIFACT_DIR"
  printf 'client_result=%s\n' "$ARTIFACT_DIR/results/client.json"
  printf 'server_result=%s\n' "$ARTIFACT_DIR/results/server.json"
  printf 'qlog_evidence=%s\n' "$ARTIFACT_DIR/results/qlog-path-validation.txt"
} | tee "$SUMMARY"
