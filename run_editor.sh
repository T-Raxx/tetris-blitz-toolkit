#!/usr/bin/env bash
# Launcher for macOS / Linux. Windows users: run_editor.bat
cd "$(dirname "$0")"
PY=python3; command -v "$PY" >/dev/null 2>&1 || PY=python
exec "$PY" tb_editor.py "$@"
