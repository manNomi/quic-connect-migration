#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env

require_command aws

AWS_REGION="${AWS_REGION:-ap-northeast-2}"

if [[ -n "${AWS_PROFILE:-}" ]]; then
  export AWS_PROFILE
fi

export AWS_REGION
export AWS_DEFAULT_REGION="$AWS_REGION"

echo "== AWS CLI =="
aws --version

echo
echo "== AWS configure list =="
aws configure list

echo
echo "== STS caller identity =="
aws sts get-caller-identity --output json

echo
echo "== Region availability check =="
aws ec2 describe-regions \
  --region "$AWS_REGION" \
  --region-names "$AWS_REGION" \
  --output table

echo
echo "preflight=ok"
print_kv "aws_region" "$AWS_REGION"
print_kv "aws_profile" "${AWS_PROFILE:-default}"
