#!/usr/bin/env python3
"""
Metrics Collector for Autonomous Codex Harness
Collects and analyzes cycle performance metrics
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class MetricsCollector:
    def __init__(self, metrics_file: str | Path = "harness_metrics.jsonl"):
        self.metrics_file = Path(metrics_file)

    def record_cycle(
        self,
        iteration: int,
        duration_secs: float,
        success: bool,
        failing_before: int,
        failing_after: int,
        error_msg: str | None = None,
        timeout: bool = False,
        prompt_version: str | None = None
    ) -> None:
        """Record metrics for a single cycle."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "duration_secs": round(duration_secs, 2),
            "success": success,
            "failing_before": failing_before,
            "failing_after": failing_after,
            "progress": failing_before - failing_after,
            "timeout": timeout,
            "error_msg": error_msg,
            "prompt_version": prompt_version,
        }

        with self.metrics_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics from all recorded metrics."""
        if not self.metrics_file.exists():
            return {
                "total_cycles": 0,
                "successful_cycles": 0,
                "total_tests_fixed": 0,
                "avg_cycle_duration": 0,
                "error_rate": 0,
                "timeout_count": 0,
                "last_10_success_rate": 0.0,
            }

        lines = self.metrics_file.read_text(encoding="utf-8").strip().split("\n")
        entries = [json.loads(line) for line in lines if line]

        if not entries:
            return {
                "total_cycles": 0,
                "successful_cycles": 0,
                "total_tests_fixed": 0,
                "avg_cycle_duration": 0,
                "error_rate": 0,
                "timeout_count": 0,
                "last_10_success_rate": 0.0,
            }

        successful = sum(1 for e in entries if e["success"])
        total_progress = sum(e["progress"] for e in entries)
        avg_duration = sum(e["duration_secs"] for e in entries) / len(entries)
        timeout_count = sum(1 for e in entries if e.get("timeout", False))

        return {
            "total_cycles": len(entries),
            "successful_cycles": successful,
            "total_tests_fixed": total_progress,
            "avg_cycle_duration": round(avg_duration, 2),
            "error_rate": round((len(entries) - successful) / len(entries), 3),
            "timeout_count": timeout_count,
            "last_10_success_rate": self._last_n_success_rate(entries, 10),
        }

    def _last_n_success_rate(self, entries: list[dict], n: int) -> float:
        """Calculate success rate of last N cycles."""
        if not entries:
            return 0.0
        last_n = entries[-n:] if len(entries) >= n else entries
        successful = sum(1 for e in last_n if e["success"])
        return round(successful / len(last_n), 3)

    def print_summary(self) -> None:
        """Print a human-readable summary."""
        summary = self.get_summary()

        print("=" * 50)
        print("📊 Metrics Summary")
        print("=" * 50)
        print(f"Total Cycles:          {summary['total_cycles']}")
        print(f"Successful Cycles:     {summary['successful_cycles']}")
        print(f"Total Tests Fixed:     {summary['total_tests_fixed']}")
        print(f"Avg Cycle Duration:    {summary['avg_cycle_duration']}s")
        print(f"Error Rate:            {summary['error_rate']:.1%}")
        print(f"Timeout Count:         {summary['timeout_count']}")
        print(f"Last 10 Success Rate:  {summary['last_10_success_rate']:.1%}")
        print("=" * 50)


def main() -> int:
    """CLI for metrics operations."""
    if len(sys.argv) < 2:
        print("Usage: metrics.py <command> [args...]")
        print("Commands:")
        print("  record <iteration> <duration> <success> <failing_before> <failing_after> [error_msg] [timeout] [prompt_version]")
        print("  summary")
        return 1

    command = sys.argv[1]
    collector = MetricsCollector()

    if command == "record":
        if len(sys.argv) < 7:
            print("ERROR: record needs: iteration duration success failing_before failing_after")
            return 1

        iteration = int(sys.argv[2])
        duration = float(sys.argv[3])
        success = sys.argv[4].lower() in ("true", "1", "yes")
        failing_before = int(sys.argv[5])
        failing_after = int(sys.argv[6])
        error_msg = sys.argv[7] if len(sys.argv) > 7 else None
        timeout = sys.argv[8].lower() in ("true", "1", "yes") if len(sys.argv) > 8 else False
        prompt_version = sys.argv[9] if len(sys.argv) > 9 else None

        collector.record_cycle(
            iteration, duration, success, failing_before, failing_after, error_msg, timeout, prompt_version
        )
        print(f"✓ Recorded cycle #{iteration} to {collector.metrics_file}")
        return 0

    elif command == "summary":
        collector.print_summary()
        return 0

    else:
        print(f"ERROR: Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
