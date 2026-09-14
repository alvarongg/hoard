#!/bin/bash
# Lint Python files with ruff.
#
# Kiro sends a JSON payload on stdin, e.g.:
#   {"session_id":"...","hook_event_name":"PostFileSave","cwd":"...",
#    "file_path":"/abs/path/to/file.py"}
#
# Kiro may also fire the hook a second time with an EMPTY stdin. In that case
# there is nothing to lint, so we skip quietly instead of failing.

set -uo pipefail

# --- Read stdin fully, but never block forever. -----------------------------
# `read -d ''` returns non-zero at EOF even after reading data, so we ignore
# its exit status. `-t 2` guarantees we give up if stdin is left open empty.
PAYLOAD=""
if [ ! -t 0 ]; then
    IFS= read -r -d '' -t 2 PAYLOAD || true
fi

# --- Extract the file path. The real payload is flat with key "file_path",
# but we search recursively to tolerate nested variants too. -----------------
FILE_PATH=""
if [ -n "${PAYLOAD//[[:space:]]/}" ]; then
    FILE_PATH="$(printf '%s' "$PAYLOAD" | jq -r '.. | .file_path? // .filePath? // .path? // .file? // empty' 2>/dev/null | head -1 || true)"
fi

# Fallbacks: file passed as an argument or via env var.
if [ -z "$FILE_PATH" ] && [ "$#" -gt 0 ]; then
    FILE_PATH="$1"
fi
if [ -z "$FILE_PATH" ] && [ -n "${KIRO_FILE_PATH:-}" ]; then
    FILE_PATH="$KIRO_FILE_PATH"
fi

# Empty payload (Kiro's duplicate trigger) or no path: nothing to do. Skip
# silently with success so the hook is not reported as failed.
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Skip non-existent files and anything that is not Python.
if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi
case "$FILE_PATH" in
    *.py) ;;
    *) exit 0 ;;
esac

# --- Run ruff. Prefer the one on PATH, fall back to anaconda python. --------
if command -v ruff >/dev/null 2>&1; then
    ruff check "$FILE_PATH" --no-fix
elif [ -x /opt/anaconda3/bin/python ]; then
    /opt/anaconda3/bin/python -m ruff check "$FILE_PATH" --no-fix
else
    python -m ruff check "$FILE_PATH" --no-fix
fi
