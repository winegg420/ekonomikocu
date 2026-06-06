#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Subat + Mart 2026 eksiklerini bitir (haftalik arama, medya yok)."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
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
FAST = [
    "--pause",
    "1800",
    "--skip-hafiza",
    "--no-finish-quotes",
    "--fast-period",
    "--skip-media",
]


def week_ranges(since: str, until: str) -> list[tuple[str, str]]:
    s = datetime.fromisoformat(since + "T00:00:00")
    e = datetime.fromisoformat(until + "T00:00:00")
    out: list[tuple[str, str]] = []
    cur = s
    while cur < e:
        nxt = min(cur + timedelta(days=7), e)
        out.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt
    return out


def run_week(since: str, until: str, label: str) -> int:
    print(f"  >> {label}: {since} .. {until}", flush=True)
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
            "50",
            *FAST,
        ],
        cwd=ROOT,
    ).returncode


def main() -> int:
    # Eksik pencereler: Subat 24-28, Mart 1-7 (geri kalan haftalar dolu)
    print("Eksik: Subat son hafta + Mart ilk hafta", flush=True)
    run_week("2026-02-22", "2026-03-01", "Subat son hafta")
    run_week("2026-03-01", "2026-03-08", "Mart ilk hafta")
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
