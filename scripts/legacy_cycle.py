from __future__ import annotations

import subprocess
from pathlib import Path


def run_legacy(prompt_file: str, codex_model: str) -> None:
    prompt_path = Path(prompt_file)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    prompt_text = prompt_path.read_text(encoding="utf-8")
    cmd = ["codex", "exec", "--yolo"]
    if codex_model:
        cmd.extend(["--model", codex_model])
    cmd.append(prompt_text)

    subprocess.run(cmd, check=True)
