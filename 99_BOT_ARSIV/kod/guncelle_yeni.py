#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1) Ustten yeni tweetleri topla (bugun + kayit disi)
2) Alintilari Koç tweet sayfasindan tamamla
3) Hafiza + analiz + Claude paketi
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
CDP = 9222


def run(cmd: list[str], label: str) -> int:
    print(f"\n{'='*50}\n{label}\n{'='*50}")
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    base = [
        PY,
        str(ROOT / "tweet_tara.py"),
        "--attach-port",
        str(CDP),
        "--require-cdp",
        "--skip-hafiza",
    ]

    # 1 — Yeni tweetler (ustten kaydir; alinti ID toplama)
    run(
        base
        + [
            "--max-scroll",
            "120",
            "--pause",
            "2200",
            "--no-finish-quotes",
        ],
        "Yeni + eksik tweetler (ustten)",
    )

    # 2 — Alintilar (sadece ekonomikocu/status)
    run([PY, str(ROOT / "alinti_tamamla.py")], "Alintilar (Koç sayfasindan)")

    # 3 — #FLOOD parcalari
    run(
        base
        + ["--max-scroll", "1", "--finish-threads", "--no-finish-quotes"],
        "FLOOD thread parcalari",
    )

    run([PY, str(ROOT / "analiz_devam.py")], "Analiz")
    run([PY, str(ROOT / "tweet_tara.py"), "--jsonl-only"], "Hafiza md")
    run([PY, str(ROOT / "claude_paket_olustur.py")], "Claude paketi")
    run([PY, str(ROOT / "alinti_dogrula.py")], "Alinti kontrol")
    run([PY, str(ROOT / "rapor_durum.py")], "Rapor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
