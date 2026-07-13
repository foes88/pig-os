#!/usr/bin/env python
"""Phase D runner: setup pilot orgs, run UAT, run reconciliation, write one report."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Phase:
    name: str
    command: list[str]


API_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = API_DIR.parent
REPORT_DIR = REPO_DIR / "tests" / "db"
PHASES = (
    Phase("A_setup_pilot_orgs", [sys.executable, "-m", "scripts.setup_pilot_orgs"]),
    Phase("B_uat_pilot", [sys.executable, "-m", "scripts.uat_pilot"]),
    Phase("C_verify_pilot", [sys.executable, "-m", "scripts.verify_pilot"]),
)


def _run_phase(phase: Phase) -> tuple[int, str]:
    proc = subprocess.run(
        phase.command,
        cwd=API_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part)
    return proc.returncode, output


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"pilot_report_{stamp}.md"

    sections: list[str] = [
        f"# PigPlan Pilot Report — {stamp}",
        "",
        f"Runner: `{Path(sys.executable).name} -m scripts.run_pilot`",
        "",
    ]
    overall = 0
    for phase in PHASES:
        print(f"=== {phase.name} ===", flush=True)
        code, output = _run_phase(phase)
        print(output, flush=True)
        sections.extend([
            f"## {phase.name}",
            "",
            f"Command: `{' '.join(phase.command)}`",
            f"Exit code: `{code}`",
            "",
            "```text",
            output or "(no output)",
            "```",
            "",
        ])
        if code != 0:
            overall = code
            break

    sections.extend(["## Summary", "", f"Overall: `{'PASS' if overall == 0 else 'FAIL'}`", ""])
    report_path.write_text("\n".join(sections), encoding="utf-8")
    print(f"\n통합 리포트: {report_path}")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
