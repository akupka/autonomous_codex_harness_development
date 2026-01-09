#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

INIT_PROMPT_FILE="${INIT_PROMPT_FILE:-init_prompt.md}"

if [[ ! -f "$INIT_PROMPT_FILE" ]]; then
  echo "ERROR: Prompt-Datei nicht gefunden: $INIT_PROMPT_FILE"
  exit 1
fi

if [[ ! -f "app_spec.txt" ]]; then
  echo "ERROR: app_spec.txt nicht gefunden im Projektroot."
  exit 1
fi

echo "==> Starte Codex Initializer (YOLO, ohne Sandbox/Landlock)…"

codex exec \
  --yolo \
  "$(cat "$INIT_PROMPT_FILE")"
