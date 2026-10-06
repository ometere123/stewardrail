#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export GENVM_VERSION="v0.3.0-rc7"
export PYTHONIOENCODING="utf-8"
export WSLENV="${WSLENV:+${WSLENV}:}GENVM_VERSION:PYTHONIOENCODING"
if command -v genvm-lint >/dev/null 2>&1; then
  LINTER=(genvm-lint)
elif command -v python >/dev/null 2>&1 && python -c 'import genvm_linter.cli' >/dev/null 2>&1; then
  # The Windows Python installer may omit its Scripts directory from PATH.
  LINTER=(python -c 'from genvm_linter.cli import cli; cli()')
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import genvm_linter.cli' >/dev/null 2>&1; then
  LINTER=(python3 -c 'from genvm_linter.cli import cli; cli()')
elif command -v powershell.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
  WINDOWS_LINTER="$({ powershell.exe -NoProfile -Command '(Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA "Python\*\Scripts\genvm-lint.exe") | Select-Object -First 1 -ExpandProperty FullName)' || true; } | tr -d '\r')"
  if [[ -z "$WINDOWS_LINTER" ]]; then
    echo "genvm-lint not installed; install the stable GenLayer tooling before submission" >&2
    exit 2
  fi
  LINTER=("$(wslpath -u "$WINDOWS_LINTER")")
else
  echo "genvm-lint not installed; install the stable GenLayer tooling before submission" >&2
  exit 2
fi
for f in contracts/*.py; do
  echo "==> $f"
  "${LINTER[@]}" check "$f"
done
