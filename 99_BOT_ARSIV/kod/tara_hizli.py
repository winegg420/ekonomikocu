#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hizli ay tarama — haftalik X aramasi + abone (Nisan bosluklari).

Neden hafta hafta?
- Tam ay aramasi yavas / takilir; kisa pencere daha hizli dolar.
- Nisan: cogu tweet abone/kilitli — arama sonrasi abone_tamamla sart.
"""
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
FAST = ["--pause", "1800", "--skip-hafiza", "--no-finish-quotes", "--fast-period", "--skip-media"]


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
            "40",
            *FAST,
        ],
        cwd=ROOT,
    ).returncode


def run_month_weeks(month_label: str, since: str, until: str) -> None:
    print(f"\n{'=' * 60}\n{month_label} (haftalik arama)\n{'=' * 60}", flush=True)
    for a, b in week_ranges(since, until):
        run_week(a, b, month_label)


def main() -> int:
    # Subat hafta 2+ (hafta 1 zaten ~190 tweet), Mart, Nisan
    for a, b in week_ranges("2026-02-08", "2026-03-01"):
        run_week(a, b, "Subat 2026")
    run_month_weeks("Mart 2026", "2026-03-01", "2026-04-01")
    run_month_weeks("Nisan 2026", "2026-04-01", "2026-05-01")

    print(f"\n{'=' * 60}\nNisan abone metin (bos kilitli)\n{'=' * 60}", flush=True)
    subprocess.run(
        [
            PY,
            str(KOD / "abone_tamamla.py"),
            "--since",
            "2026-04-01",
            "--per-round",
            "350",
            "--max-rounds",
            "25",
            "--profile-scroll",
            "250",
            "--no-pack",
            "--stall-sec",
            "90",
        ],
        cwd=ROOT,
    )

    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
