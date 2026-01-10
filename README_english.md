# Autonomous Agent Harness (Spec → Tests → Git → "until green")

This repository contains a small **harness** that controls an autonomous development agent. The goal is to iteratively develop a project based on a specification (`app_spec.txt`) and a **testable feature/test list** (`feature_list.json`) until **all tests are green**.

Inspired by https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents - compared with the blog post in ANTHROPIC_COMPLIANCE.md. (I don't have an Anthropic account, but the idea is great, so I implemented it on Codex with some extensions.)

The automation consists of three core scripts:

- `run_init.sh` – Initializes a new project (prompt-driven).
- `run_cycle.sh` – Executes **one** implementation cycle
- `run_until_green.sh` – Repeats cycles until all tests are `passes: true` (or stop conditions apply).

---

## Basic Principle

1. **Specification:** `app_spec.txt` defines *what* should be built.
2. **Tests/Features as Harness:** `feature_list.json` defines *how* to verify if it's complete.
3. **Agent works test-by-test:** The coding agent picks the next test with `"passes": false`, implements the functionality, verifies via UI, and then sets it to `"passes": true`.
4. **Git as Audit Trail:** Every change is committed. Optionally, push after each successful cycle (see configuration).

> Important: In normal operation, only the `passes` field in `feature_list.json` should be changed (from `false` to `true`). Descriptions/steps are not "rewritten" to keep the harness stable.

---

## Files and Directory Structure

- `app_spec.txt`  
  Requirements / Specification (input).
- `feature_list.json`  
  Test catalog (Single Source of Truth). Format: either JSON array `[...]` or object `{ "tests": [ ... ] }`.
- `codex-progress.txt`  
  Progress notes (what's done, what's next).
- `init.sh`  
  Start/setup script for the project environment (typically generated during init).
- `logs/`  
  Log files per cycle (`run_until_green.sh` writes here).
- `scripts/`  
  Dispatcher scripts

---

## Prerequisites

### Required: For the Harness (the scripts)

For `run_init.sh`, `run_cycle.sh`, and `run_until_green.sh` to run, the following tools must be installed and available in `PATH`:

- **Bash** (Linux/macOS recommended; on Windows use **WSL**)
- **codex CLI** (`codex`)  
  Used by `run_init.sh` and `run_cycle.sh` (`codex exec --yolo`).
- **Python 3** (`python3`)  
  Used by `run_until_green.sh` and the scripts.
- **Python packages:** No external libraries required (stdlib only).  
  Optional: `pip install -r requirements.txt` (intentionally empty).

Optional: Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- **Git** (`git`)  
  Required for the audit trail (commits); also for optional auto-push.
- **OpenSSH Tools** (`ssh-agent`, `ssh-add`)  
  Only required if `push_each_cycle=1` is set in `harness.conf`.
- **Standard Unix Utilities** (typically already present): `date`, `seq`, `mkdir`, `cat`, `chmod`, `timeout`


### Project-specific: Depends on your `app_spec.txt`

Additionally, depending on the tech stack, the following may be required (often used/expected by `init.sh`):

- **Node.js** + package manager (`npm`/`pnpm`/`yarn`)
- **Python** tooling (`pip`, `poetry`, `venv`)
- **Docker / Docker Compose** (e.g., for DB/Redis)
- Database CLI/Clients (e.g., `psql`), if provided in the project

Which of these tools are actually needed depends on the requirements and the generated `init.sh`.

---

## Creating a New Project – 6 Steps

### Step 1: Create project folder and place harness files
Create a new folder and copy into it:
- `run_init.sh`
- `run_cycle.sh`
- `run_until_green.sh`
- your prompt files (e.g., `coding_prompt.md` and `init_prompt.md`)
- a new `app_spec.txt` (see Step 2)

### Step 2: Write `app_spec.txt`
Formulate requirements so that concrete end-to-end tests can be derived:
- Core features
- UI/UX requirements
- Validations/error cases
- Roles/permissions (if relevant)
- Integrations/data persistence (if relevant)

### Step 3: Start initializer (creates baseline)
```bash
chmod +x run_init.sh
./run_init.sh
```

If your init prompt file is not named `init_prompt.md`:
```bash
INIT_PROMPT_FILE=YOUR_INIT_PROMPT.md ./run_init.sh
```

Expected after init (baseline):
- `feature_list.json` exists (comprehensive test catalog)
- `init.sh` exists (environment setup)
- first Git commits exist (project start documented)

### Step 4: Start environment
```bash
chmod +x init.sh
./init.sh
```

### Step 5: Ensure ssh-agent (checked by the loop)
`run_until_green.sh` expects an active `ssh-agent`:
```bash
eval $(ssh-agent -s)
ssh-add
```

### Step 6: Start autonomous loop ("until green")
```bash
chmod +x run_until_green.sh run_cycle.sh
./run_until_green.sh
```

The loop writes logs to `logs/` and runs until all tests are `passes: true` or a stop condition applies.

---

## Extending a Project (Standard case: spec stays the same)

If you want new commits without changing the specification:
1. Ensure the environment is running (`./init.sh`).
2. Start the loop:
   ```bash
   ./run_until_green.sh
   ```
3. The agent processes the next tests with `"passes": false`, verifies, and marks them as passing.

---

## Extending a Project with Changed Specification – 6 Steps (Re-Baseline)

If requirements in `app_spec.txt` **change** (not just additive!), the harness (`feature_list.json`) must match the specification again. Otherwise, you'll fight against outdated/inconsistent tests.

### Step 1: Create clean checkpoint (before the change)
```bash
git add -A
git commit -m "Checkpoint before spec change"
git tag spec-v1-baseline
```

### Step 2: Update `app_spec.txt` and commit
```bash
git add app_spec.txt
git commit -m "Update app_spec to v2 requirements"
git tag spec-v2-requirements
```

### Step 3: Decide: Additive vs. Re-Baseline
- **Only additive (only new features):** You can add new tests (with `passes:false`).
- **Changed/replaced/removed:** Re-baseline is recommended.

### Step 4: Archive old test list
```bash
cp feature_list.json feature_list.v1.json
git add feature_list.v1.json
git commit -m "Archive feature_list v1"
```

### Step 5: Generate new `feature_list.json` (deliberately outside normal mode)
In normal mode, `feature_list.json` should not be rewritten (only `passes`).
For a re-baseline, use a **separate prompt** (e.g., `spec_update_prompt.md`) that explicitly allows regenerating the list to match the new spec.

```bash
CYCLE_PROMPT_FILE=spec_update_prompt.md ./run_cycle.sh
```

Then:
```bash
git add feature_list.json codex-progress.txt
git commit -m "Rebaseline feature_list to app_spec v2"
git tag spec-v2-tests
```

### Step 6: Run normally again ("until green")
```bash
./run_until_green.sh
```

---

## Configuration (Environment Variables)

### New Central Config File: harness.conf

Since the current version, there is a **central configuration file** `harness.conf` that bundles all important parameters in one place:

```bash
# Example harness.conf
test_case_limit=50          # For small projects: 20-50 tests
cycle_prompt_file=coding_prompt.md
init_prompt_file=init_prompt.md
max_errors=10               # More error tolerance
push_each_cycle=0           # No auto-push
```

The config file is automatically read by the Python scripts. Values can still be overridden via environment variables.

**Important Config Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `test_case_limit` | 200 | Number of tests in feature_list.json (0 = all) |
| `use_smart_test_limit` | 1 | Dynamic test count based on failures |
| `codex_model` | "" | LLM Model (e.g., "claude-sonnet-4.5") |
| `cycle_prompt_file` | coding_prompt.md | Prompt for implementation cycles |
| `init_prompt_file` | init_prompt.md | Prompt for initialization |
| `max_files` | 200 | Max files in context |
| `max_file_bytes` | 200000 | Max bytes per file |
| `sleep_secs` | 2 | Pause between cycles |
| `max_iterations` | 9999 | Max number of cycles |
| `max_errors` | 5 | Max errors before stop |
| `cycle_timeout` | 1800 | Timeout per cycle (seconds) |
| `push_each_cycle` | 1 | Git push after cycle (1=yes, 0=no) |
| `git_remote` | origin | Git remote name |
| `log_level` | INFO | Log level (DEBUG/INFO/WARNING/ERROR) |
| `stuck_threshold` | 5 | Stop when N cycles without progress |
| `checkpoint_interval` | 10 | Git tag every N successful cycles |
| `validate_feature_list` | 1 | Validation after each cycle |

### Legacy: Direct Environment Variables

Old method (still works):

**Prompt files:**
- `INIT_PROMPT_FILE` (Default: `init_prompt.md`)
- `CYCLE_PROMPT_FILE` (Default: `coding_prompt.md`)

Examples:
```bash
INIT_PROMPT_FILE=init_prompt.md ./run_init.sh
CYCLE_PROMPT_FILE=coding_prompt.md ./run_cycle.sh
```

**run_until_green.sh:**
- `SLEEP_SECS` (Default: `2`)
- `MAX_ITERS` (Default: `9999`)
- `MAX_ERRORS` (Default: `5`)
- `LOG_DIR` (Default: `logs`)

Git Push (after successful cycle):
- `PUSH_EACH_CYCLE` (Default: `1`, set `0` to disable push)
- `GIT_REMOTE` (Default: `origin`)
- `GIT_BRANCH` (Default: empty = current branch)

Examples:
```bash
SLEEP_SECS=1 MAX_ERRORS=10 ./run_until_green.sh
PUSH_EACH_CYCLE=0 ./run_until_green.sh
```

---

## Troubleshooting

### 1) `ERROR: Prompt file not found`
- Cause: `run_init.sh` or `run_cycle.sh` cannot find the prompt file.
- Solution: Check filename or set via env var:
  ```bash
  INIT_PROMPT_FILE=YOUR_INIT_PROMPT.md ./run_init.sh
  CYCLE_PROMPT_FILE=YOUR_CYCLE_PROMPT.md ./run_cycle.sh
  ```

### 2) `ERROR: app_spec.txt not found in project root.`
- Cause: `run_init.sh` requires `app_spec.txt` in project root.
- Solution: Create file or move to root.

### 3) `ERROR: feature_list.json missing. Run run_init.sh first.`
- Cause: The loop needs `feature_list.json`.
- Solution:
  ```bash
  ./run_init.sh
  ```

### 4) `ERROR: feature_list.json format unknown`
- Cause: JSON doesn't have expected format.
- Expected is either:
  - `[...]` (list of tests) or
  - `{ "tests": [ ... ] }`
- Solution: Correct format or re-baseline.

### 5) `ERROR: ssh-agent not available`
- Cause: `push_each_cycle=1` is set, but no `ssh-agent` available.
- Solution Option 1 (start ssh-agent):
  ```bash
  eval $(ssh-agent -s)
  ssh-add
  ```
- Solution Option 2 (disable push):
  Set in `harness.conf`:
  ```
  push_each_cycle=0
  ```

### 6) Loop stops with `STOP: error_count=... exceeded MAX_ERRORS=...`
- Cause: Too many errors in `run_cycle.sh` or during optional push.
- Solution:
  - Open log file under `logs/` (last iteration).
  - Increase `MAX_ERRORS` and restart:
    ```bash
    MAX_ERRORS=10 ./run_until_green.sh
    ```

### 7) `codex: command not found`
- Cause: `codex` CLI is not available.
- Solution: Install `codex` correctly or make it available in `PATH`.

---

## Advanced Features

### 1. Metrics & Progress Tracking

The harness automatically collects metrics for each cycle:

```bash
# Display metrics
python3 scripts/metrics.py summary
```

Output:
```
📊 Harness Metrics Summary
━━━━━━━━━━━━━━━━━━━━━━━━
Total Cycles:         42
Successful Cycles:    38 (90.5%)
Total Tests Fixed:    187
Avg Cycle Duration:   845.3s
Error Rate:           0.095
Timeout Count:        2
```

Metrics are stored in `harness_metrics.jsonl` (JSONL format for easy analysis).

### 2. Stuck Detection

When multiple cycles in a row make no progress (same tests failing), the harness automatically stops:

```bash
# In harness.conf
stuck_threshold=5  # Stop after 5 cycles without progress
```

Recognizable by logs like:
```
[WARNING] No progress in last 3 cycles (same 5 tests failing)
[ERROR] Stuck detected: no progress in 5 cycles
```

### 3. Pause & Resume

Control during runtime without abort:

```bash
# Pause (finishes current cycle cleanly, then waits)
touch .harness_pause

# Resume (delete file)
rm .harness_pause

# Complete stop after current cycle
touch .harness_stop
```

### 4. Checkpoints

Automatic Git tags at milestones:

```bash
# In harness.conf
checkpoint_interval=10  # Tag every 10 successful cycles
```

Tags have format: `checkpoint-iter-50-passing-187`

Return to checkpoint:
```bash
git tag | grep checkpoint
git checkout checkpoint-iter-40-passing-180
```

### 5. Prompt Versioning

Each metric entry contains a hash of `coding_prompt.md`:

```jsonl
{"iteration": 42, "prompt_version": "a3f2b91c", ...}
```

This allows you to track which prompt version delivered which results.

### 6. Smart Test Limit

The harness automatically adjusts the number of tests in context:

- **Few failures (≤3):** Show more context (up to 15 tests)
- **Many failures:** Limit to configured value

```bash
# In harness.conf
use_smart_test_limit=1  # Enable
test_case_limit=30      # Fallback with many failures
```

### 7. Context Size Optimization

Files are prioritized by relevance:

- **High Priority:** `.json`, `.md`, `.txt`, `package.json`
- **Medium Priority:** Code files (`.py`, `.js`, `.ts`, etc.)
- **Low Priority:** Styling/Config (`.css`, `.yml`)
- **Failing Test Match:** +200 points if filename mentioned in test

### 8. Structured Commit Messages

The prompt requests structured commits:

```
[FIX] Authentication redirect loop

- Fixed session cookie persistence issue
- Updated login handler to check existing session
- Improved error messages for auth failures

Tests: 187 passing (+3 new), 15 failing (-3 fixed)
```

Types: `[FEAT]`, `[FIX]`, `[TEST]`, `[REFACTOR]`, `[DOCS]`

### 9. Smoke Tests

Check environment before first cycle:

```bash
chmod +x scripts/smoke_test.sh
./scripts/smoke_test.sh
```

Checks:
- Required commands (git, python3, codex)
- Files (feature_list.json, app_spec.txt)
- Git repository status
- Python environment
- feature_list.json format

### 10. Web Dashboard

Real-time monitoring via browser:

```bash
python3 scripts/dashboard.py 8080
```

Then open: http://localhost:8080

**Features:**
- 📊 Live Metrics (Cycles, Success Rate, Tests Fixed)
- 🎯 Test Progress (Pass/Fail Ratio with Progress Bar)
- 📈 Recent Cycles (last 20 with status)
- 🏷️ Git History & Checkpoints
- 📝 Recent Log Files
- 🎮 Control Panel (Pause/Resume/Stop)
- 🔄 Auto-Refresh every 5 seconds

**Control API:**
```bash
# Via curl (alternative to touch .harness_pause)
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "pause"}'
```

---

## Security Notice

The scripts start the agent with **`codex exec --yolo`** (without sandbox/landlock). This means:
- The agent can make **arbitrary changes** in the repo.
- Depending on the environment, it can also **execute commands**, change/delete files, etc.

Recommendations:
- Work in an isolated environment (VM/Container/Separate User).
- Use branches and review changes (`git diff`, `git log`) regularly.
- Keep secrets out of the repo (e.g., no API keys in plain text).
- Rely on the Git audit trail: commit frequently, name clearly.

## Fully Autonomous
To ensure it runs even if the shell session terminates:
```bash
nohup ./run_until_green.sh > codex.log 2>&1 &
```
