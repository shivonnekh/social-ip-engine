#!/usr/bin/env bash
# Wrapper for the auto-fan-out watcher — used by launchd / cron.
# Loads the repo .env (NOTION_KEY, OPENAI_API_KEY, MINIMAX_*) then runs one tick.
#
#   ./scripts/run_watch.sh            # one fan-out pass (with voice)
#   ./scripts/run_watch.sh --no-voice # skip voice clips
#   ./scripts/run_watch.sh --dry-run  # preview only
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi
exec python3 scripts/notion_watch.py "$@"
