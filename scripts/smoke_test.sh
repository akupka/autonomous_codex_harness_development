#!/usr/bin/env bash
# Smoke Tests - Check if environment is ready for autonomous development
set -euo pipefail

echo "==> Running smoke tests..."

EXIT_CODE=0

# -----------------------------
# Check 1: Required Commands
# -----------------------------
echo "  [1/5] Checking required commands..."
for cmd in git python3 codex; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "    ❌ ERROR: Required command not found: $cmd"
    EXIT_CODE=1
  else
    echo "    ✓ $cmd"
  fi
done

# -----------------------------
# Check 2: Required Files
# -----------------------------
echo "  [2/5] Checking required files..."
for file in app_spec.txt feature_list.json; do
  if [[ ! -f "$file" ]]; then
    echo "    ❌ ERROR: Required file missing: $file"
    EXIT_CODE=1
  else
    echo "    ✓ $file"
  fi
done

# -----------------------------
# Check 3: Git Repository
# -----------------------------
echo "  [3/5] Checking git repository..."
if ! git rev-parse --git-dir &>/dev/null; then
  echo "    ❌ ERROR: Not in a git repository"
  EXIT_CODE=1
else
  echo "    ✓ Git repository"
  
  # Check for uncommitted changes (warning only)
  if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "    ⚠ WARNING: Uncommitted changes detected"
  fi
fi

# -----------------------------
# Check 4: Python Dependencies
# -----------------------------
echo "  [4/5] Checking Python environment..."
if ! python3 -c "import json, pathlib" 2>/dev/null; then
  echo "    ❌ ERROR: Python standard library import failed"
  EXIT_CODE=1
else
  echo "    ✓ Python environment OK"
fi

# -----------------------------
# Check 5: Config & feature_list.json
# -----------------------------
echo "  [5/5] Validating feature_list.json..."
validation=$(python3 - <<'PY' 2>&1 || echo "FAILED"
import json, sys
from pathlib import Path

try:
    data = json.loads(Path("feature_list.json").read_text())
    tests = data.get("tests") if isinstance(data, dict) else data
    
    if not isinstance(tests, list):
        print("ERROR: tests is not a list")
        sys.exit(1)
    
    # Quick validation of first few tests
    for i, test in enumerate(tests[:5]):
        required = ["category", "description", "steps", "passes"]
        for field in required:
            if field not in test:
                print(f"ERROR: Test {i} missing field: {field}")
                sys.exit(1)
    
    print(f"OK ({len(tests)} tests)")
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON - {e}")
    sys.exit(1)
PY
)

if [[ "$validation" == FAILED* ]] || [[ "$validation" == ERROR* ]]; then
  echo "    ❌ $validation"
  EXIT_CODE=1
else
  echo "    ✓ $validation"
fi

# -----------------------------
# Optional: Check if servers are running
# -----------------------------
if [[ -f "init.sh" ]]; then
  echo "  [OPTIONAL] Checking if application servers are running..."
  
  # Try to detect common ports from app_spec.txt
  if [[ -f "app_spec.txt" ]]; then
    # Check for localhost:PORT patterns
    ports=$(grep -oP 'localhost:\K\d+' app_spec.txt 2>/dev/null | sort -u || true)
    
    if [[ -n "$ports" ]]; then
      for port in $ports; do
        if curl -sf "http://localhost:$port" &>/dev/null || \
           curl -sf "http://localhost:$port/health" &>/dev/null; then
          echo "    ✓ Server responding on port $port"
        else
          echo "    ⚠ WARNING: No server on port $port (may need to run ./init.sh)"
        fi
      done
    fi
  fi
fi

# -----------------------------
# Summary
# -----------------------------
echo
if [[ $EXIT_CODE -eq 0 ]]; then
  echo "✅ All smoke tests passed - environment ready!"
  exit 0
else
  echo "❌ Some smoke tests failed - please fix errors above"
  exit $EXIT_CODE
fi
