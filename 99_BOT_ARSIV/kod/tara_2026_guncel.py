#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 GUNCEL TARAMA — yeni tweetler hemen kayda + %100 hedefi.

Sira:
  1) Ustten yeni tweet kesfi (profil)
  2) Bu ay haftalik X aramasi
  3) 2026 bos abone metinleri
  4) #FLOOD parcalari
  5) Alintilar (gecmis tweet + flood icindeki)
  6) FLOOD 2. tur
  7) kapsam_2026 raporu + paket (tamamsa)

Chrome: CHROME_X.bat (9222), abone oturumu acik.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

YIL_SINCE = "2026-01-01"
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--pause", "3500"]


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable


def run(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def month_week_ranges() -> list[tuple[str, str]]:
    """Bu ay + onceki 3 gun (ay devri icin)."""
    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)
    # Ay basindan onceki 3 gun (gec ay sonu tweetleri)
    start = min(start, now - timedelta(days=3))
    tomorrow = now + timedelta(days=1)
    out: list[tuple[str, str]] = []
    cur = start
    while cur < tomorrow:
        nxt = min(cur + timedelta(days=7), tomorrow)
        out.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt
    return out


def main() -> int:
    subprocess.run([PY, str(KOD / "kapsam_2026.py")], cwd=ROOT, check=False)

    base = [PY, str(KOD / "tweet_tara.py"), *CDP]

    # 1 — Ustten yeni tweetler (hemen kayit)
    run(
        "1/7 Yeni tweetler (profil ust)",
        base
        + [
            "--max-scroll",
            "100",
            "--pause",
            "2000",
            "--no-finish-quotes",
            "--skip-media",
        ],
    )

    # 2 — Bu ay haftalik arama (2026 kesif)
    for a, b in month_week_ranges():
        run(
            f"2/7 Haftalik arama {a} .. {b}",
            base
            + [
                "--since-date",
                a,
                "--until-date",
                b,
                "--max-scroll",
                "40",
                "--pause",
                "1800",
                "--no-finish-quotes",
                "--fast-period",
                "--skip-media",
            ],
        )

    # 3 — Abone bos metin (2026)
    run(
        "3/7 Abone metin (2026 bos kilitli)",
        [
            PY,
            str(KOD / "abone_tamamla.py"),
            "--since",
            YIL_SINCE,
            "--per-round",
            "200",
            "--max-rounds",
            "40",
            "--profile-scroll",
            "300",
            "--stall-sec",
            "120",
            "--no-pack",
        ],
    )

    # 4 — #FLOOD
    run(
        "4/7 #FLOOD thread parcalari",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "3",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    # 5 — Alintilar
    run(
        "5/7 Alintilar",
        [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "10", "--per-round", "50"],
    )

    # 6 — FLOOD 2. tur
    run(
        "6/7 #FLOOD 2. tur",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "2",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    subprocess.run([PY, str(KOD / "abone_etiketle.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "alinti_dogrula.py")], cwd=ROOT, check=False)

    rc = subprocess.run([PY, str(KOD / "kapsam_2026.py")], cwd=ROOT).returncode

    if rc == 0:
        subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
        print("\n2026 %100 — paket guncellendi.", flush=True)
    else:
        print("\n2026 henuz %100 degil — TARAMA_2026.md eksikleri kontrol et.", flush=True)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
