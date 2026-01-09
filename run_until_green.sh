#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# -----------------------------
# Load config from harness.conf (Python-side)
# Bash uses env vars with fallback to defaults
# -----------------------------
load_config_value() {
  python3 - <<PY
from scripts.config import load_config
import sys
cfg = load_config()
key = sys.argv[1] if len(sys.argv) > 1 else ""
if key and key in cfg:
    print(cfg[key])
PY
}

# Settings (override via env or use from harness.conf)
SLEEP_SECS="${SLEEP_SECS:-$(load_config_value 'sleep_secs')}"
SLEEP_SECS="${SLEEP_SECS:-2}"
MAX_ITERS="${MAX_ITERS:-$(load_config_value 'max_iterations')}"
MAX_ITERS="${MAX_ITERS:-9999}"
CYCLE_TIMEOUT="${CYCLE_TIMEOUT:-$(load_config_value 'cycle_timeout')}"
CYCLE_TIMEOUT="${CYCLE_TIMEOUT:-1800}"
CHECKPOINT_INTERVAL="${CHECKPOINT_INTERVAL:-$(load_config_value 'checkpoint_interval')}"
CHECKPOINT_INTERVAL="${CHECKPOINT_INTERVAL:-10}"
STUCK_THRESHOLD="${STUCK_THRESHOLD:-$(load_config_value 'stuck_threshold')}"
STUCK_THRESHOLD="${STUCK_THRESHOLD:-5}"

# Git push settings
GIT_REMOTE="${GIT_REMOTE:-$(load_config_value 'git_remote')}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-$(load_config_value 'git_branch')}"
# GIT_BRANCH bleibt leer = current branch
PUSH_EACH_CYCLE="${PUSH_EACH_CYCLE:-$(load_config_value 'push_each_cycle')}"
PUSH_EACH_CYCLE="${PUSH_EACH_CYCLE:-1}"

# Stop conditions
MAX_ERRORS="${MAX_ERRORS:-$(load_config_value 'max_errors')}"
MAX_ERRORS="${MAX_ERRORS:-5}"

# Logs
LOG_DIR="${LOG_DIR:-$(load_config_value 'log_dir')}"
LOG_DIR="${LOG_DIR:-logs}"  # Fallback if empty
LOG_LEVEL="${LOG_LEVEL:-$(load_config_value 'log_level')}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"  # Fallback if empty
mkdir -p "$LOG_DIR"

echo "==> Config summary"
python3 - <<'PY'
from scripts.config import load_config

cfg = load_config()
print(f"test_case_limit={cfg.get('test_case_limit')}")
print(f"codex_model={cfg.get('codex_model')}")
print(f"cycle_prompt_file={cfg.get('cycle_prompt_file')}")
print(f"cycle_timeout={cfg.get('cycle_timeout', 1800)}s")
PY

# Only check ssh-agent if push is enabled
if [[ "$PUSH_EACH_CYCLE" == "1" ]]; then
  if [[ -z "${SSH_AUTH_SOCK:-}" ]]; then
    echo "ERROR: PUSH_EACH_CYCLE=1 requires ssh-agent. Run: eval \$(ssh-agent -s) && ssh-add"
    exit 20
  fi
fi

# -----------------------------
# Helpers
# -----------------------------

# Calculate prompt version hash
prompt_version() {
  local hash=""
  if [ -f "coding_prompt.md" ]; then
    hash=$(sha256sum coding_prompt.md | cut -d' ' -f1 | head -c 8)
  fi
  echo "$hash"
}

# Logging with levels
log() {
  local level="$1"
  shift
  local msg="$*"
  local ts="$(date -Is)"
  
  # Check if we should print this level
  case "$LOG_LEVEL" in
    DEBUG) ;;  # Print everything
    INFO) [[ "$level" =~ ^(DEBUG)$ ]] && return ;;
    WARNING) [[ "$level" =~ ^(DEBUG|INFO)$ ]] && return ;;
    ERROR) [[ "$level" =~ ^(DEBUG|INFO|WARNING)$ ]] && return ;;
  esac
  
  # Console output
  echo "[$ts] [$level] $msg"
  
  # Structured log
  echo "{\"timestamp\":\"$ts\",\"level\":\"$level\",\"message\":\"$msg\",\"iteration\":${i:-0}}" \
    >> "$LOG_DIR/harness.jsonl"
}

# Control file checks (pause/stop)
check_control_files() {
  if [[ -f ".harness_pause" ]]; then
    log INFO "PAUSE requested. Waiting for .harness_pause to be removed..."
    while [[ -f ".harness_pause" ]]; do
      sleep 5
    done
    log INFO "RESUMED"
  fi
  
  if [[ -f ".harness_stop" ]]; then
    log INFO "STOP requested. Exiting gracefully..."
    rm -f ".harness_stop"
    exit 0
  fi
}

count_failing() {
  python3 - <<'PY'
import json
from pathlib import Path

p = Path("feature_list.json")
if not p.exists():
    print("ERR_NO_FEATURE_LIST")
    raise SystemExit(2)

data = json.loads(p.read_text(encoding="utf-8"))

tests = data.get("tests") if isinstance(data, dict) else data
if not isinstance(tests, list):
    print("ERR_BAD_FORMAT")
    raise SystemExit(3)

fail = sum(1 for t in tests if not t.get("passes", False))
print(fail)
PY
}

validate_feature_list() {
  python3 - <<'PY'
import json, sys
from pathlib import Path

try:
    data = json.loads(Path("feature_list.json").read_text())
    tests = data.get("tests") if isinstance(data, dict) else data
    
    if not isinstance(tests, list):
        print("ERROR: tests is not a list")
        sys.exit(1)
    
    for i, test in enumerate(tests):
        required = ["category", "description", "steps", "passes"]
        for field in required:
            if field not in test:
                print(f"ERROR: Test {i} missing field: {field}")
                sys.exit(1)
        
        if not isinstance(test["steps"], list):
            print(f"ERROR: Test {i} steps is not a list")
            sys.exit(1)
    
    print("OK")
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON - {e}")
    sys.exit(1)
PY
}

current_branch() {
  git rev-parse --abbrev-ref HEAD 2>/dev/null || true
}

has_git_remote() {
  git remote get-url "$GIT_REMOTE" >/dev/null 2>&1
}

git_push() {
  # Determine branch to push
  local br
  if [[ -n "$GIT_BRANCH" ]]; then
    br="$GIT_BRANCH"
  else
    br="$(current_branch)"
  fi

  if [[ -z "$br" ]]; then
    echo "WARN: cannot determine git branch; skipping push."
    return 0
  fi

  if ! has_git_remote; then
    echo "WARN: git remote '$GIT_REMOTE' not configured; skipping push."
    return 0
  fi

  echo "==> git push $GIT_REMOTE $br"
  git push "$GIT_REMOTE" "$br"
}

# Stuck detection
declare -A failure_history

detect_stuck() {
  local current_failing="$1"
  local iter="$2"
  
  failure_history["$iter"]="$current_failing"
  
  # Check last N iterations
  if [[ $iter -ge $STUCK_THRESHOLD ]]; then
    local stuck=1
    local prev="${failure_history[$((iter-1))]}"
    for j in $(seq $((iter-STUCK_THRESHOLD+1)) $((iter-1))); do
      if [[ "${failure_history[$j]:-}" != "$prev" ]]; then
        stuck=0
        break
      fi
    done
    
    if [[ $stuck -eq 1 && "$current_failing" == "$prev" ]]; then
      log WARNING "No progress in last $STUCK_THRESHOLD cycles (stuck at $current_failing failing tests)"
      log WARNING "Consider manual intervention or changing strategy."
      return 1
    fi
  fi
  return 0
}

# -----------------------------
# Main loop
# -----------------------------
error_count=0
cycle_start_time=0

for i in $(seq 1 "$MAX_ITERS"); do
  # Check control files (pause/stop)
  check_control_files
  
  ts="$(date -Is)"
  cycle_start_time=$(date +%s)
  log_file="$LOG_DIR/cycle_${i}_$(date +%Y%m%dT%H%M%S).log"

  fail="$(count_failing || true)"
  if [[ "$fail" == "ERR_NO_FEATURE_LIST" ]]; then
    log ERROR "feature_list.json fehlt. Erst run_init.sh ausführen."
    exit 2
  fi
  if [[ "$fail" == "ERR_BAD_FORMAT" ]]; then
    log ERROR "feature_list.json Format unbekannt (erwarte Liste oder {tests:[...]})"
    exit 3
  fi

  echo
  echo "=============================="
  log INFO "Iteration #$i  $ts"
  log INFO "failing tests: $fail"
  log INFO "errors so far: $error_count / $MAX_ERRORS"
  log INFO "log: $log_file"
  log INFO "cycle timeout: ${CYCLE_TIMEOUT}s"
  echo "=============================="

  if [[ "$fail" == "0" ]]; then
    log INFO "All tests passing. Done."
    python3 scripts/metrics.py summary 2>&1 || log WARNING "Failed to show metrics summary"
    exit 0
  fi
  
  # Stuck detection
  if ! detect_stuck "$fail" "$i"; then
    log WARNING "Stuck detected - incrementing error count"
    error_count=$((error_count + 1))
  fi

  # Save current git state for potential rollback
  pre_cycle_commit=$(git rev-parse HEAD)

  # Run cycle with timeout and capture logs
  set +e
  if [[ "$CYCLE_TIMEOUT" -gt 0 ]]; then
    timeout "$CYCLE_TIMEOUT" ./run_cycle.sh >"$log_file" 2>&1
    rc=$?
  else
    ./run_cycle.sh >"$log_file" 2>&1
    rc=$?
  fi
  set -e
  
  # Calculate cycle duration
  cycle_end_time=$(date +%s)
  cycle_duration=$((cycle_end_time - cycle_start_time))
  
  # Determine success and record metrics
  cycle_success=false
  timeout_occurred=false
  error_msg=""

  if [[ $rc -eq 124 ]]; then
    log ERROR "run_cycle.sh timed out after ${CYCLE_TIMEOUT}s (see $log_file)"
    error_count=$((error_count + 1))
    timeout_occurred=true
    error_msg="timeout"
    
    # Rollback on timeout
    if ! git diff-index --quiet HEAD --; then
      log WARNING "Uncommitted changes detected after timeout. Rolling back."
      git reset --hard "$pre_cycle_commit"
    fi
  elif [[ $rc -ne 0 ]]; then
    error_count=$((error_count + 1))
    log ERROR "run_cycle.sh failed with exit code $rc (see $log_file)"
    error_msg="exit_code_$rc"
    
    # Rollback on error
    if ! git diff-index --quiet HEAD --; then
      log WARNING "Uncommitted changes detected. Creating backup and rolling back."
      git add -A
      git commit -m "FAILED_CYCLE_${i}: Backup before rollback" || true
      git tag "failed-cycle-${i}-backup" || true
      git reset --hard "$pre_cycle_commit"
    fi
  else
    log INFO "run_cycle.sh finished OK (see $log_file)"
    
    # Validate feature_list.json after successful cycle
    validation=$(validate_feature_list 2>&1 || echo "FAILED")
    if [[ "$validation" != "OK" ]]; then
      log ERROR "feature_list.json corrupted after cycle: $validation"
      log WARNING "Rolling back to pre-cycle state."
      git reset --hard "$pre_cycle_commit"
      error_count=$((error_count + 1))
      error_msg="corrupted_feature_list"
    else
      cycle_success=true
    fi

    # Optional push after each successful cycle
    if [[ "$PUSH_EACH_CYCLE" == "1" && "$cycle_success" == "true" ]]; then
      set +e
      git_push >>"$log_file" 2>&1
      prc=$?
      set -e

      if [[ $prc -ne 0 ]]; then
        error_count=$((error_count + 1))
        log ERROR "git push failed (see $log_file)"
      else
        log INFO "git push OK"
      fi
    fi
  fi
  
  # Recount failing tests after cycle
  new_fail="$(count_failing || true)"
  if [[ "$new_fail" != "ERR_NO_FEATURE_LIST" && "$new_fail" != "ERR_BAD_FORMAT" ]]; then
    log INFO "failing tests after iteration: $new_fail"
  fi
  
  # Get prompt version hash
  prompt_hash=$(prompt_version)
  
  # Record metrics (with prompt version)
  if ! python3 scripts/metrics.py record "$i" "$cycle_duration" "$cycle_success" "$fail" "${new_fail:-$fail}" "$error_msg" "$timeout_occurred" "$prompt_hash" 2>&1; then
    log WARNING "Failed to record metrics for cycle $i"
  fi
  
  # Checkpoint every N iterations
  if [[ "$CHECKPOINT_INTERVAL" -gt 0 && $((i % CHECKPOINT_INTERVAL)) -eq 0 && "$cycle_success" == "true" ]]; then
    passing_count=$(($(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("feature_list.json").read_text())
tests = data.get("tests") if isinstance(data, dict) else data
print(sum(1 for t in tests if t.get("passes", False)))
PY
    )))
    git tag "checkpoint-iter-${i}-passing-${passing_count}" 2>/dev/null || true
    log INFO "Checkpoint created at iteration $i (${passing_count} tests passing)"
  fi
  
  # Stop if too many errors
  if [[ $error_count -gt $MAX_ERRORS ]]; then
    log ERROR "STOP: error_count=$error_count exceeded MAX_ERRORS=$MAX_ERRORS"
    log ERROR "Last log: $log_file"
    python3 scripts/metrics.py summary 2>&1 || log WARNING "Failed to show metrics summary"
    exit 10
  fi

  sleep "$SLEEP_SECS"
done

log ERROR "reached MAX_ITERS=$MAX_ITERS without finishing."
python3 scripts/metrics.py summary 2>&1 || log WARNING "Failed to show metrics summary"
exit 11
