from __future__ import annotations

import subprocess
from pathlib import Path
from scripts.context_builder import build_smart_prompt


def run_smart_cycle(prompt_template_file: str, codex_model: str) -> None:
    prompt_path = Path(prompt_template_file)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    
    # 1. Build the full prompt with injected context
    full_prompt = build_smart_prompt(prompt_path, {})
    
    # 2. Execute via codex CLI
    cmd = ["codex", "exec", "--yolo"]
    if codex_model:
        cmd.extend(["--model", codex_model])
    
    # Pass prompt via argument (could also be stdin if supported, but arg is safer for now)
    cmd.append(full_prompt)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running codex exec: {e}")
        raise
    except FileNotFoundError:
        print("Error: 'codex' CLI not found in PATH.")
        raise
