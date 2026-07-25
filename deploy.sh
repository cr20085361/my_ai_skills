#!/usr/bin/env bash
# PGRMS deployment wrapper for macOS/Linux.
# Default mode is dry-run. Pass --apply to write user-global configuration.

set -euo pipefail

APPLY=0
HOME_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY=1
      shift
      ;;
    --home)
      HOME_OVERRIDE="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./deploy.sh [--apply] [--home <path>]" >&2
      exit 2
      ;;
  esac
done

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

ARGS=(scripts/pgrms.py deploy --target all)
if [[ "$APPLY" -eq 1 ]]; then
  ARGS+=(--apply)
else
  echo "Mode: dry-run. Pass --apply to write user-global files."
fi

if [[ -n "$HOME_OVERRIDE" ]]; then
  ARGS+=(--home "$HOME_OVERRIDE")
fi

"$PYTHON_BIN" "${ARGS[@]}"
