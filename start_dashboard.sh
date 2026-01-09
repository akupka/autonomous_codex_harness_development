#!/usr/bin/env bash
# Start Dashboard - Quick launcher for the monitoring dashboard
set -euo pipefail

PORT="${1:-8080}"

echo "==> Starting Autonomous Codex Dashboard"
echo ""
echo "    Dashboard URL: http://localhost:$PORT"
echo "    Auto-refresh:  5 seconds"
echo ""
echo "    Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")/.."
exec python3 scripts/dashboard.py "$PORT"
