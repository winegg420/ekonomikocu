#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tam tarama: gunumuz -> gecmis (hedef 2025-01-01)
  1) Profil kaydirma (tum tweetler)
  2) Alintilar (gecmis alintilanan tweetler)
  3) #FLOOD thread parcalari
  4) Abone metin tamamlama
  5) Kapsam raporu (TARAMA_DURUMU.md)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HEDEF = "1 Oca 2025"
MART_SINCE = "2026-03-01"
MART_UNTIL = "2026-04-01"


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return here


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--pause", "4000"]


def run(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)

    # 0 — Mart 2026: X ARAMA (profil kaydirma Mayis'ta takiliyor)
    run(
        "0/5 Mart 2026 (arama: from:ekonomikocu since/until)",
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
            "--since-date",
            MART_SINCE,
            "--until-date",
            MART_UNTIL,
            "--max-scroll",
            "250",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    # 1 — Profil: bugunden geriye hedef tarihe kadar
    run(
        f"1/5 Profil kaydirma — {HEDEF}'e kadar",
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
            "--profile-only",
            "--max-scroll",
            "900",
            "--stop-before",
            HEDEF,
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    # 2 — Alintilar
    run(
        "2/5 Alintilar (gecmis tweet metinleri)",
        [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "8", "--per-round", "50"],
    )

    # 3 — FLOOD + eksik grafik (kisa profil turu)
    run(
        "3/5 #FLOOD thread + grafik",
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
            "--profile-only",
            "--max-scroll",
            "5",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    # 4 — Abone metin (Mart 2026+)
    run(
        "4/5 Abone metin tamamlama",
        [
            PY,
            str(KOD / "abone_tamamla.py"),
            "--since",
            MART_SINCE,
            "--per-round",
            "250",
            "--max-rounds",
            "50",
            "--profile-scroll",
            "400",
            "--no-pack",
            "--stall-sec",
            "120",
        ],
    )

    subprocess.run([PY, str(KOD / "abone_etiketle.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)

    print("\nBITTI — TARAMA_DURUMU.md dosyasina bak.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
