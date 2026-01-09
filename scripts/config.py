from __future__ import annotations

from pathlib import Path


DEFAULT_CONFIG: dict[str, object] = {
    "test_case_limit": 200,
    "codex_model": "",
    "cycle_prompt_file": "coding_prompt.md",
    "init_prompt_file": "init_prompt.md",
    "max_files": 200,
    "max_file_bytes": 200000,
    "max_git_log_lines": 50,
    "log_level": "INFO",
    "stuck_threshold": 5,
    "checkpoint_interval": 10,
    "use_smart_test_limit": 1,
    "validate_feature_list": 1,
}


def _parse_value(raw: str) -> object:
    value = raw.strip().strip('"').strip("'")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def load_config(path: str | Path | None = None) -> dict[str, object]:
    config_path = Path(path) if path else Path("harness.conf")
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    merged = DEFAULT_CONFIG.copy()
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key_clean = key.strip()
        # Skip if value is empty (allows commenting out by leaving value blank)
        if not raw_value.strip():
            continue
        merged[key_clean] = _parse_value(raw_value)

    return merged
