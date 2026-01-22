from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "logs",
    ".pytest_cache",
    "venv",
    "env",
}

# File priority for context building
RELEVANCE_PATTERNS = {
    "high": [".json", ".md", ".txt", "package.json", "requirements.txt", "Cargo.toml"],
    "medium": [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"],
    "low": [".css", ".scss", ".html", ".yml", ".yaml", ".toml"],
}


def _read_text(path: Path, max_bytes: int) -> str:
    if not path.exists():
        return ""
    try:
        raw = path.read_bytes()
        truncated = raw[:max_bytes]
        text = truncated.decode("utf-8", errors="replace")
        if len(raw) > max_bytes:
            text += f"\n\n[TRUNCATED: {len(raw) - max_bytes} bytes]"
        return text
    except OSError:
        return ""


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def get_next_failing_test(feature_list_path: Path) -> dict | None:
    data = _load_json(feature_list_path)
    if not data:
        return None
    
    tests = data.get("tests") if isinstance(data, dict) else data
    if not isinstance(tests, list):
        return None
        
    for i, test in enumerate(tests):
        if not test.get("passes", False):
            # Return the test with its index
            test_copy = test.copy()
            test_copy["_index"] = i
            return test_copy
            
    return None


def _format_test_markdown(test: dict) -> str:
    if not test:
        return "No failing tests found. All clear?"
    
    idx = test.get("_index", "?")
    return f"""
## CURRENT FOCUS: Test #{idx}

**Category:** {test.get('category', 'unknown')}
**Description:** {test.get('description', 'No description')}

**Steps:**
{chr(10).join(f"- {step}" for step in test.get('steps', []))}

**Status:** FAILING ("passes": false)
"""


def build_smart_prompt(prompt_template_path: Path, config: dict) -> str:
    """Builds a complete prompt with injected context."""
    
    # 1. Read static artifacts
    app_spec = _read_text(Path("app_spec.txt"), 10000)
    progress = _read_text(Path("codex-progress.txt"), 5000)
    
    # 2. Get next failing test
    next_test = get_next_failing_test(Path("feature_list.json"))
    test_context = _format_test_markdown(next_test) if next_test else "ALL TESTS PASSING."
    
    # 3. Read the prompt template (instructions)
    if not prompt_template_path.exists():
        return f"ERROR: Prompt file {prompt_template_path} not found."
    
    instructions = prompt_template_path.read_text(encoding="utf-8")
    
    # 4. Assemble the prompt
    # We put context BEFORE instructions so the model sees the "Grounding" first, 
    # then the "Task".
    
    combined = f"""
# PROJECT CONTEXT

## App Specification (app_spec.txt)
```text
{app_spec}
```

## Progress Notes (codex-progress.txt)
```text
{progress}
```

{test_context}

---

# INSTRUCTIONS

{instructions}
"""
    return combined
