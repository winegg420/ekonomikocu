#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2019-2024 gecmis — koçun eski tweetleri + alinti flood arsivi.

Sira:
  1) Sabitle (pinned) tweet
  2) Haftalik X aramasi 2019-01-01 .. 2025-01-01
  3) Profil kaydirma 2019'a kadar
  4) Alinti tamamla
  5) Alinti flood (tum yillar) + keşif
  6) #FLOOD
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

HEDEF = "2019-01-01"
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--pause", "4000", "--skip-media"]


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


def main() -> int:
    print(
        "\nGECMIS ALINTI TARAMA — 2019'a kadar\n"
        "Hedef: koçun eski bildigi/yanildigi tweetler + her alintinin flood'u\n",
        flush=True,
    )

    run("Sabitle (pinned) tweet + flood", [PY, str(KOD / "pin_flood_tara.py"), "--attach-port", "9222"])

    base = [PY, str(KOD / "tweet_tara.py"), *CDP]

    for a, b in week_ranges("2019-01-01", "2025-01-01"):
        run(
            f"Gecmis arama {a} .. {b}",
            base
            + [
                "--since-date",
                a,
                "--until-date",
                b,
                "--max-scroll",
                "40",
                "--pause",
                "2000",
                "--no-finish-quotes",
                "--fast-period",
                "--skip-media",
            ],
        )

    run(
        "Profil — 2019-01-01'e kadar",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "1200",
            "--stop-before",
            HEDEF,
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    run("Alintilar", [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "6", "--per-round", "80"])

    run(
        "Alinti flood (TUM yillar + keşif)",
        [
            PY,
            str(KOD / "alinti_flood_tara.py"),
            "--yil",
            "tum",
            "--attach-port",
            "9222",
            "--max-scroll",
            "50",
            "--discover",
            "800",
            "--no-pack",
        ],
    )

    run(
        "#FLOOD kalan",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "5",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
    print("\nGecmis alinti turu bitti.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
