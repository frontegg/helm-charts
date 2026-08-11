#!/usr/bin/env bash
set -euo pipefail

chart_dir=$(cd "$(dirname "$0")/.." && pwd)
rendered=$(helm template strategy-test "$chart_dir" \
  --values "$chart_dir/tests/web-deployment-strategy.values.yaml")

grep -q '^  strategy:$' <<<"$rendered"
grep -q '^    type: Recreate$' <<<"$rendered"
