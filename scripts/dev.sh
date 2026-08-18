#!/usr/bin/env bash
# Dev supervisor. Keeps telepane open in this pane while you edit:
#   • any change under src/telepane/ hot-restarts the app (code + styles)
#   • a crash auto-heals (the app is relaunched)
#   • the screen is reset before each launch, so no stale frame leaks through
#   • pressing `q` quits cleanly; Ctrl-C stops the supervisor
#
# Run this in a dedicated tmux pane, then edit source elsewhere and watch it
# reload live.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python"
exec "$PY" scripts/_dev_watch.py
