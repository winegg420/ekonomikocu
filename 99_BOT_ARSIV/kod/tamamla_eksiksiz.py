#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oncelik: 1) En guncel tweetler  2) Mart-Subat-Ocak eksiksiz  3) 1 Oca 2026'ya kadar
         4) Alinti+FLOOD  5) Aralik 2025 geriye
Chrome CHROME_X.bat (9222). Profil modu — explore/arama dongusu yok.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
CDP = "9222"

# Ustten yeni + derin profil: sadece ekonomikocu/profil (CDP arama modu KAPALI)
PROF = ["--profile-only"]
PERIOD = ["--since-date", "--until-date"]


def run(cmd: list[str], label: str) -> int:
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    return subprocess.run(cmd, cwd=ROOT).returncode


def base_cmd() -> list[str]:
    return [
        PY,
        str(ROOT / "tweet_tara.py"),
        "--attach-port",
        CDP,
        "--require-cdp",
        "--skip-hafiza",
        "--pause",
        "5500",
    ]


def period(since: str, until: str, label: str, scroll: int = 120) -> None:
    b = base_cmd()
    run(
        b
        + ["--since-date", since, "--until-date", until, "--max-scroll", str(scroll), "--resume"],
        f"Donem arama: {label}",
    )
    run(
        b
        + [
            "--since-date",
            since,
            "--until-date",
            until,
            "--max-scroll",
            "280",
            "--profile-period-only",
        ],
        f"Donem profil: {label}",
    )


def main() -> int:
    b = base_cmd()

    # 1 — Her calismada once en guncel (profil, arama yok)
    run(
        b + PROF + ["--max-scroll", "60", "--no-finish-quotes"],
        "1/7 En guncel tweetler (profil ust)",
    )

    # 2 — Mart, Subat, Ocak (public + alinti + flood icin veri)
    for since, until, label in [
        ("2026-03-01", "2026-04-01", "Mart 2026"),
        ("2026-02-01", "2026-03-01", "Subat 2026"),
        ("2026-01-01", "2026-02-01", "Ocak 2026"),
    ]:
        period(since, until, label)

    # 3 — Profilde 1 Ocak 2026'ya kadar in (guncel tekrar taramadan kacin)
    run(
        b
        + PROF
        + [
            "--max-scroll",
            "380",
            "--stop-before",
            "1 Oca 2026",
            "--finish-threads",
            "--no-finish-quotes",
        ],
        "3/7 Profil: 1 Oca 2026'ya kadar + FLOOD",
    )

    # 4 — Alintilar (Ocak oncesi dahil tum eksikler)
    run(
        [PY, str(ROOT / "alinti_tamamla.py"), "--max-rounds", "5", "--per-round", "60"],
        "4/7 Alintilar (5 tur)",
    )

    # 5 — Eksik grafik + kalan FLOOD
    run(
        b + PROF + ["--max-scroll", "2", "--finish-threads", "--no-finish-quotes"],
        "5/7 Eksik grafikler + FLOOD",
    )

    # 6 — Aralik 2025 ve geriye (Ocak bittikten sonra)
    period("2025-12-01", "2026-01-01", "Aralik 2025", scroll=100)
    run(
        b
        + PROF
        + ["--max-scroll", "250", "--stop-before", "1 Ara 2025", "--no-finish-quotes"],
        "6/7 Profil geri: Aralik 2025 oncesi",
    )

    run(
        [PY, str(ROOT / "alinti_tamamla.py"), "--max-rounds", "3", "--per-round", "40"],
        "7/7 Alintilar (Aralik+ geri)",
    )

    run([PY, str(ROOT / "analiz_devam.py")], "Analiz")
    run([PY, str(ROOT / "dil_analiz.py")], "Koç dili")
    run([PY, str(ROOT / "tweet_tara.py"), "--jsonl-only"], "Hafiza md")
    run([PY, str(ROOT / "claude_paket_olustur.py")], "Claude paketi")
    subprocess.run([PY, str(ROOT / "rapor_durum.py")], cwd=ROOT)
    subprocess.run([PY, str(ROOT / "temiz_reklam.py")], cwd=ROOT)
    subprocess.run([PY, str(ROOT / "alinti_dogrula.py")], cwd=ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
