#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mart 2026 eksiksiz + profil kaydirarak 1 Oca 2025'e kadar + abone tamamlama."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    return up


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--no-finish-quotes", "--pause", "3500"]


def run(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def tara_period(since: str, until: str, label: str, scroll: int = 300) -> int:
    return run(
        label,
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
            "--profile-period-only",
            *COMMON,
        ],
    )


def main() -> int:
    # 1 — Mart 2026 (bosluk — oncelik)
    tara_period("2026-03-01", "2026-04-01", "Mart 2026 (profil donem)", 400)

    # 2 — 2025 aylari (seyrek — donem modu)
    for since, until, label, scroll in (
        ("2025-12-01", "2026-01-01", "Aralik 2025", 280),
        ("2025-11-01", "2025-12-01", "Kasim 2025", 200),
        ("2025-10-01", "2025-11-01", "Ekim 2025", 200),
        ("2025-09-01", "2025-10-01", "Eylul 2025", 200),
        ("2025-08-01", "2025-09-01", "Agustos 2025", 200),
        ("2025-07-01", "2025-08-01", "Temmuz 2025", 200),
        ("2025-06-01", "2025-07-01", "Haziran 2025", 200),
        ("2025-05-01", "2025-06-01", "Mayis 2025", 280),
        ("2025-04-01", "2025-05-01", "Nisan 2025", 200),
        ("2025-03-01", "2025-04-01", "Mart 2025", 200),
        ("2025-02-01", "2025-03-01", "Subat 2025", 200),
        ("2025-01-01", "2025-02-01", "Ocak 2025", 200),
    ):
        tara_period(since, until, label, scroll)

    # 3 — Profil geri: 1 Oca 2025 siniri
    run(
        "Profil kaydirma — 1 Oca 2025'e kadar",
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
            "--profile-only",
            "--max-scroll",
            "700",
            "--stop-before",
            "1 Oca 2025",
            *COMMON,
        ],
    )

    # 4 — Abone metin (Mart 2026+)
    run(
        "Abone tweet metinleri",
        [
            PY,
            str(KOD / "abone_tamamla.py"),
            "--since",
            "2026-03-01",
            "--per-round",
            "200",
            "--max-rounds",
            "40",
            "--profile-scroll",
            "400",
            "--no-pack",
            "--stall-sec",
            "120",
        ],
    )

    subprocess.run([PY, str(KOD / "abone_etiketle.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
    print("\nBITTI — Mart + 2025 tarama tamamlandi.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
