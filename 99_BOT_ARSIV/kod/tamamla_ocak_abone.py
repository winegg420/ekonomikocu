#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ocak 2026'ya kadar: abonelik icerigi + alinti + #FLOOD (en guncelden baslar).
Chrome: CHROME_X.bat (9222), abone oturumu acik.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
CDP = "9222"
REFILL = ["--refill-locked-since", "2026-01-01"]


def run(cmd: list[str], label: str) -> int:
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    return subprocess.run(cmd, cwd=ROOT).returncode


def base() -> list[str]:
    return [
        PY,
        str(ROOT / "tweet_tara.py"),
        "--attach-port",
        CDP,
        "--require-cdp",
        "--skip-hafiza",
        "--pause",
        "5500",
        "--profile-only",
    ]


def main() -> int:
    b = base()

    run(
        b + ["--max-scroll", "40", "--finish-threads"] + REFILL,
        "1/6 En guncel + FLOOD + abonelik yenile",
    )

    for since, until, label in [
        ("2026-03-01", "2026-04-01", "Mart 2026"),
        ("2026-02-01", "2026-03-01", "Subat 2026"),
        ("2026-01-01", "2026-02-01", "Ocak 2026"),
    ]:
        run(
            b
            + [
                "--since-date",
                since,
                "--until-date",
                until,
                "--max-scroll",
                "180",
                "--resume",
                "--finish-threads",
            ]
            + REFILL,
            f"2/6 Arama: {label}",
        )
        run(
            b
            + [
                "--since-date",
                since,
                "--until-date",
                until,
                "--max-scroll",
                "320",
                "--profile-period-only",
                "--finish-threads",
            ]
            + REFILL,
            f"3/6 Profil: {label}",
        )

    run(
        b
        + [
            "--max-scroll",
            "450",
            "--stop-before",
            "1 Oca 2026",
            "--finish-threads",
        ]
        + REFILL,
        "4/6 Profil scroll: 1 Ocak 2026'ya kadar + FLOOD",
    )

    run(
        [PY, str(ROOT / "alinti_tamamla.py"), "--max-rounds", "10", "--per-round", "70"],
        "5/6 Alintilar (10 tur)",
    )

    run(
        b
        + ["--max-scroll", "3", "--finish-threads"] + REFILL,
        "6/6 FLOOD + abonelik + grafik",
    )

    run([PY, str(ROOT / "analiz_devam.py")], "Analiz")
    run([PY, str(ROOT / "tweet_tara.py"), "--jsonl-only"], "Hafiza md")
    run([PY, str(ROOT / "claude_paket_olustur.py")], "Claude paketi")
    subprocess.run([PY, str(ROOT / "rapor_durum.py")], cwd=ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
