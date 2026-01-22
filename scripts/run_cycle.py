from __future__ import annotations

import os
import sys

from scripts.config import load_config
# from scripts.legacy_cycle import run_legacy
from scripts.smart_cycle import run_smart_cycle


def main() -> int:
    config = load_config()
    prompt_file = str(config.get("cycle_prompt_file", "coding_prompt.md"))
    env_override = os.getenv("CYCLE_PROMPT_FILE", "").strip()
    if env_override:
        prompt_file = env_override
    codex_model = str(config.get("codex_model", ""))
    
    # Switch to new smart cycle
    run_smart_cycle(prompt_file, codex_model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
