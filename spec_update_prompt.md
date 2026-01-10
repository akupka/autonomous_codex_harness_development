## YOUR ROLE - SPEC UPDATE AGENT

You are updating an EXISTING repository because requirements changed.

MANDATORY FIRST STEPS:
1) Read app_spec.txt
2) Read feature_list.json (current)
3) Read codex-progress.txt if it exists
4) Check git status and recent git log

GOAL:
- Create a NEW feature_list.json that matches the UPDATED app_spec.txt.
- Keep the file format compatible with run_until_green.sh (list of tests, each has "passes": false/true).
- Minimum 200 tests, include both functional and style tests, and at least 25 tests with 10+ steps.
- Initialize all tests with "passes": false. The app_spec "passes:true" line is the target state after implementation, not the starting state.

RULES:
- Do NOT delete application code.
- Do NOT reinitialize git.
- Preserve history: if feature_list.v1.json does not exist yet, create it as a copy of the current feature_list.json.
- After generating the new feature_list.json, run 1-2 smoke checks in the UI to validate the app still starts.
- Update codex-progress.txt describing the rebaseline and what changed.

END:
- git add the changed files
- git commit with a message: "Rebaseline to app_spec v2"
