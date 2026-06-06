#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 abonelik tweetleri + #FLOOD parcalari + flood icindeki alintilar.

Sira:
  1) Nisan-Haziran haftalik X aramasi (eksik id kesfi)
  2) Abone metin tamamlama (bos kilitli)
  3) #FLOOD thread parcalari
  4) Alintilar (gecmis flood dahil)
  5) FLOOD 2. tur + etiketleme + rapor

Chrome: CHROME_X.bat (9222), x.com abone oturumu, pencere KAPATILMAZ.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ABONE_SINCE = "2026-01-01"
CDP = ["--attach-port", "9222", "--require-cdp"]
FAST = ["--pause", "1800", "--skip-hafiza", "--no-finish-quotes", "--fast-period", "--skip-media"]
COMMON = ["--skip-hafiza", "--pause", "4000"]


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable


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


def run(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


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
            "45",
            *FAST,
        ],
        cwd=ROOT,
    ).returncode


def main() -> int:
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)

    # 1 — Abone donemi kesif (Nisan-Haziran haftalik arama)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    for month_label, since, until in [
        ("Nisan 2026", "2026-04-01", "2026-05-01"),
        ("Mayis 2026", "2026-05-01", "2026-06-01"),
        ("Haziran 2026", "2026-06-01", tomorrow),
    ]:
        print(f"\n{'=' * 60}\n{month_label} (haftalik arama)\n{'=' * 60}", flush=True)
        for a, b in week_ranges(since, until):
            run_week(a, b, month_label)

    # Mart — kalan abone/kilitli id (4 adet)
    run_week("2026-03-01", "2026-04-01", "Mart 2026 (abone kalinti)")

    # 2 — Abone metin (2026 icindeki tum bos kilitli)
    run(
        "2/5 Abone metin — 2026 tum bos kilitli",
        [
            PY,
            str(KOD / "abone_tamamla.py"),
            "--since",
            ABONE_SINCE,
            "--per-round",
            "300",
            "--max-rounds",
            "60",
            "--profile-scroll",
            "500",
            "--stall-sec",
            "150",
            "--no-pack",
        ],
    )

    # 3 — #FLOOD thread parcalari
    run(
        "3/5 #FLOOD thread parcalari",
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
            "--profile-only",
            "--max-scroll",
            "3",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    # 4 — Alintilar (flood icindeki gecmis alintilar dahil)
    run(
        "4/5 Alintilar (gecmis flood / quote metinleri)",
        [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "12", "--per-round", "60"],
    )

    # 5 — FLOOD 2. tur (alinti sonrasi yeni koklar)
    run(
        "5/5 #FLOOD 2. tur",
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
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
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)

    print("\nBITTI — TARAMA_DURUMU.md ve abone_tamamla_log.txt kontrol et.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
