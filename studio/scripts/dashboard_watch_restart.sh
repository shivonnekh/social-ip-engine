#!/bin/bash
# Restarts the studio dashboard LaunchAgent whenever its source changes.
#
# Exists because launchd's own WatchPaths only fires on a directory's entries
# being ADDED/REMOVED, not on an existing file being edited in place (the
# common case for Claude/an editor modifying dashboard/state.py etc.) —
# verified empirically 2026-07-27: touching/appending to an already-tracked
# file under a WatchPaths directory never triggered a relaunch. This script
# polls mtimes directly instead and restarts through the SAME supervised
# `launchctl kickstart` path a human would use manually, so there's no
# nested/duplicate-process risk (the reason uvicorn's own --reload flag is
# deliberately not used in the dashboard's plist).
set -euo pipefail

WATCH_DIRS=(
  "/Users/shivonne/Claude Code/social-ip-engine/studio/dashboard"
  "/Users/shivonne/Claude Code/social-ip-engine/studio/scripts"
)
STAMP="/Users/shivonne/Claude Code/social-ip-engine/studio/.logs/dashboard-watch.stamp"
UID_N=$(id -u)

touch "$STAMP"

while true; do
  changed=$(find "${WATCH_DIRS[@]}" -name '*.py' -newer "$STAMP" -print -quit)
  if [ -n "$changed" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') change detected: $changed -> restarting dashboard"
    touch "$STAMP"
    launchctl kickstart -k "gui/${UID_N}/com.shivonne.studio-dashboard" || true
  fi
  sleep 2
done
