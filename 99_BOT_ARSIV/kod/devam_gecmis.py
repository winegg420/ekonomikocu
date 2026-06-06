#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ocak–Mart 2026 — Mayis/Haziran ile ayni kapsam (arama + profil donem modu).
Tek sekme, yabanci hesap yok (tara_nav).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CDP = 9222

# (since, until, etiket)
DONEMLER = [
    ("2026-01-01", "2026-02-01", "Ocak 2026"),
    ("2026-02-01", "2026-03-01", "Subat 2026"),
    ("2026-03-01", "2026-04-01", "Mart 2026"),
]


def run(cmd: list[str], label: str) -> int:
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    return subprocess.run(cmd, cwd=ROOT).returncode


def ozet() -> None:
    subprocess.run([sys.executable, str(ROOT / "rapor_durum.py")], cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "alinti_dogrula.py")], cwd=ROOT)


def main() -> int:
    py = sys.executable
    base = [
        py,
        str(ROOT / "tweet_tara.py"),
        "--attach-port",
        str(CDP),
        "--require-cdp",
        "--skip-hafiza",
        "--no-finish-quotes",
        "--pause",
        "2600",
    ]

    for since, until, label in DONEMLER:
        run(
            base
            + [
                "--since-date",
                since,
                "--until-date",
                until,
                "--max-scroll",
                "180",
                "--resume",
            ],
            f"Arama: {label}",
        )
        run(
            base
            + [
                "--since-date",
                since,
                "--until-date",
                until,
                "--max-scroll",
                "320",
                "--profile-period-only",
            ],
            f"Profil donem: {label}",
        )

    run(
        base
        + [
            "--max-scroll",
            "400",
            "--stop-before",
            "1 Oca 2026",
            "--finish-threads",
        ],
        "Genel gecmis — 1 Ocak 2026'ya kadar (public + FLOOD)",
    )

    run([py, str(ROOT / "devam_public.py")], "Alinti + FLOOD + grafik + paket")
    ozet()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
