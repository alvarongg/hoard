#!/bin/bash
# Lint TypeScript/TSX files with ESLint.
#
# Kiro sends a JSON payload on stdin, e.g.:
#   {"session_id":"...","hook_event_name":"PostFileSave","cwd":"...",
#    "file_path":"/abs/path/to/file.tsx"}
#
# Kiro may also fire the hook a second time with an EMPTY stdin. In that case
# there is nothing to lint, so we skip quietly instead of failing.

set -uo pipefail

# --- Read stdin fully, but never block forever. -----------------------------
PAYLOAD=""
if [ ! -t 0 ]; then
    IFS= read -r -d '' -t 2 PAYLOAD || true
fi

# --- Extract the file path (flat "file_path" in practice; search recursively
# to tolerate nested variants). ---------------------------------------------
FILE_PATH=""
if [ -n "${PAYLOAD//[[:space:]]/}" ]; then
    FILE_PATH="$(printf '%s' "$PAYLOAD" | jq -r '.. | .file_path? // .filePath? // .path? // .file? // empty' 2>/dev/null | head -1 || true)"
fi

if [ -z "$FILE_PATH" ] && [ "$#" -gt 0 ]; then
    FILE_PATH="$1"
fi
if [ -z "$FILE_PATH" ] && [ -n "${KIRO_FILE_PATH:-}" ]; then
    FILE_PATH="$KIRO_FILE_PATH"
fi

# Empty payload / no path: skip silently with success.
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi
case "$FILE_PATH" in
    *.ts|*.tsx) ;;
    *) exit 0 ;;
esac

# --- Resolve the frontend directory relative to this script. ----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Make the path absolute so it still resolves after we cd into frontend.
case "$FILE_PATH" in
    /*) ABS_FILE="$FILE_PATH" ;;
    *)  ABS_FILE="$PROJECT_ROOT/$FILE_PATH" ;;
esac

cd "$FRONTEND_DIR"
npx eslint --no-error-on-unmatched-pattern "$ABS_FILE"
