#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mart + Subat 2026 — X arama modu."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--pause", "4000", "--no-finish-quotes"]


def run_month(since: str, until: str, label: str, scroll: int) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
            "--since-date",
            since,
            "--until-date",
            until,
            "--max-scroll",
            str(scroll),
            *COMMON,
        ],
        cwd=ROOT,
    ).returncode


def main() -> int:
    steps = (
        ("2026-03-01", "2026-04-01", "Mart 2026", 350),
        ("2026-02-01", "2026-03-01", "Subat 2026", 280),
    )
    for since, until, label, scroll in steps:
        code = run_month(since, until, label, scroll)
        if code != 0:
            print(f"UYARI: {label} cikis kodu {code}", flush=True)
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
