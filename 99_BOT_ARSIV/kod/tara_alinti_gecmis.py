#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025 alintilarindan geriye — gecmis flood arsivi (2019'a kadar).

Tam 2025 profil taramasi YOK. Sadece:
  1) 2025 hafif arama — alinti tasiyan ana tweetleri bul (derin arsiv degil)
  2) Alinti metinlerini tamamla
  3) Her alintinin status sayfasindan TUM flood + ic ice alintilar (BFS → 2019)
  4) Sabitle (pinned) flood
  5) Paket

Amac: Claude'un Koç'un gecmis tezlerini / yanildigi-yaptigi yerleri gormesi.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--pause", "3000", "--skip-media"]


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
        "\nALINTI GECMIS FLOOD — 2025 tohum -> 2019'a kadar\n"
        "Hedef: Koç'un gecmisten alintiladigi her tweetin flood/thread zinciri\n",
        flush=True,
    )

    base = [PY, str(KOD / "tweet_tara.py"), *CDP]

    for a, b in week_ranges("2025-01-01", "2026-01-01"):
        run(
            f"2025 alinti tohumu {a} .. {b}",
            base
            + [
                "--since-date",
                a,
                "--until-date",
                b,
                "--max-scroll",
                "18",
                "--pause",
                "1800",
                "--no-finish-quotes",
                "--fast-period",
                "--skip-media",
            ],
        )

    run(
        "Alinti metinleri",
        [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "10", "--per-round", "100"],
    )

    run(
        "Alinti flood BFS (2025->gecmis, 2019'a kadar)",
        [
            PY,
            str(KOD / "alinti_flood_tara.py"),
            "--yil",
            "gecmis",
            "--attach-port",
            "9222",
            "--max-scroll",
            "50",
            "--discover",
            "2500",
            "--kesif-yillar",
            "2025,2026",
            "--no-pack",
        ],
    )

    run("Sabitle (pinned) flood", [PY, str(KOD / "pin_flood_tara.py"), "--attach-port", "9222"])

    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
    print("\nAlinti gecmis flood turu bitti.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
