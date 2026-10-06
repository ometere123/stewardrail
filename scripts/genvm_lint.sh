#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if ! command -v genvm-lint >/dev/null 2>&1; then
  echo "genvm-lint not installed; install the stable GenLayer tooling before submission" >&2
  exit 2
fi
for f in contracts/*.py; do
  echo "==> $f"
  genvm-lint check "$f"
done
