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


def _calculate_priority(path: str, failing_tests: list[dict]) -> int:
    """Calculate file priority based on relevance to failing tests."""
    score = 0
    path_lower = path.lower()
    
    # Check file extension
    for priority, patterns in RELEVANCE_PATTERNS.items():
        if any(path.endswith(p) for p in patterns):
            score += {"high": 100, "medium": 50, "low": 10}[priority]
    
    # Check if mentioned in failing tests (first 10)
    for test in failing_tests[:10]:
        desc = test.get("description", "").lower()
        steps = " ".join(test.get("steps", [])).lower()
        
        # Check if file name or parts appear in test
        file_stem = Path(path).stem.lower()
        if file_stem in desc or file_stem in steps:
            score += 200
        
        # Check directory names
        parts = path.lower().split("/")
        for part in parts:
            if part in desc or part in steps:
                score += 50
    
    return score


def _read_text(path: Path, max_bytes: int) -> str:
    raw = path.read_bytes()
    truncated = raw[:max_bytes]
    text = truncated.decode("utf-8", errors="replace")
    if len(raw) > max_bytes:
        text += f"\n\n[TRUNCATED: {len(raw) - max_bytes} bytes]"
    return text


def _load_feature_list(path: Path, limit: int | None) -> Any:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    tests = data.get("tests") if isinstance(data, dict) else data
    if not isinstance(tests, list):
        return data
    if limit is None or limit <= 0 or len(tests) <= limit:
        return data
    limited = tests[:limit]
    return {"tests": limited} if isinstance(data, dict) else limited


def get_smart_test_limit(feature_list: dict, default_limit: int) -> int:
    """Calculate optimal test limit based on failing tests.
    
    If only a few tests fail, we can include more context.
    If many tests fail, we must limit to avoid token overflow.
    """
    tests = feature_list.get("tests", [])
    if not tests:
        return default_limit
    
    total = len(tests)
    failing = sum(1 for t in tests if not t.get("passes", False))
    
    # If <=3 tests failing, show more context
    if failing <= 3:
        return min(failing + 5, total, 15)
    
    # If many failing, use configured limit
    return min(failing, default_limit)


def _git_log(max_lines: int) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{max_lines}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        return ""


def _collect_repo_files(
    root: Path, max_files: int, max_file_bytes: int, failing_tests: list[dict] = None
) -> tuple[list[str], dict[str, str]]:
    """Collect repository files with smart prioritization based on failing tests."""
    files: list[str] = []
    contents: dict[str, str] = {}
    
    # First pass: collect all files with priorities
    file_priorities: list[tuple[str, int, Path]] = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            rel = path.relative_to(root).as_posix()
            
            # Calculate priority
            priority = _calculate_priority(rel, failing_tests or [])
            file_priorities.append((rel, priority, path))
    
    # Sort by priority (highest first)
    file_priorities.sort(key=lambda x: x[1], reverse=True)
    
    # Second pass: read files in priority order
    for rel, priority, path in file_priorities:
        if len(files) >= max_files:
            break
        
        files.append(rel)
        try:
            contents[rel] = _read_text(path, max_file_bytes)
        except OSError:
            continue

    return files, contents


def build_context(config: dict[str, object]) -> dict[str, object]:
    root = Path(".")
    max_files = int(config.get("max_files", 200))
    max_file_bytes = int(config.get("max_file_bytes", 200000))
    max_git_log_lines = int(config.get("max_git_log_lines", 50))
    test_case_limit = int(config.get("test_case_limit", 200))
    
    # Load feature list first to enable smart prioritization
    feature_list_full = _load_feature_list(Path("feature_list.json"), None)
    
    # Get failing tests for prioritization
    failing_tests = []
    if feature_list_full and isinstance(feature_list_full, dict):
        tests = feature_list_full.get("tests", [])
        failing_tests = [t for t in tests if not t.get("passes", False)]
    
    # Calculate smart test limit
    smart_limit = get_smart_test_limit(
        feature_list_full if feature_list_full else {},
        test_case_limit
    )

    # Collect files with smart prioritization
    files_list, files_content = _collect_repo_files(
        root, max_files, max_file_bytes, failing_tests
    )
    
    # Load feature list with calculated limit
    feature_list = _load_feature_list(Path("feature_list.json"), smart_limit)

    context: dict[str, object] = {
        "app_spec": Path("app_spec.txt").read_text(encoding="utf-8")
        if Path("app_spec.txt").exists()
        else "",
        "feature_list": feature_list,
        "progress": Path("codex-progress.txt").read_text(encoding="utf-8")
        if Path("codex-progress.txt").exists()
        else "",
        "repo_tree": files_list,
        "files": files_content,
        "git_log": _git_log(max_git_log_lines),
    }
    return context
