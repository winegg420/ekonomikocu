#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public odak: alinti + #FLOOD + medya + hafiza (devam_gecmis bitince calistir)."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
CDP = "9222"


def run(cmd: list[str], label: str) -> int:
    print(f"\n{'='*60}\n{label}\n{'='*60}")
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

    print("Bekleniyor (devam_gecmis / Chrome isi bitsin)...")
    time.sleep(45)

    run([PY, str(ROOT / "alinti_tamamla.py")], "Alintilar + grafik")
    run(base + ["--quotes-only"], "Alinti turu (quotes-only)")
    run(
        base
        + ["--max-scroll", "1", "--finish-threads", "--no-finish-quotes", "--pause", "2500"],
        "#FLOOD + eksik grafikler",
    )
    run([PY, str(ROOT / "analiz_devam.py")], "Analiz")
    run([PY, str(ROOT / "tweet_tara.py"), "--jsonl-only"], "Hafiza md")
    run([PY, str(ROOT / "claude_paket_olustur.py")], "Claude paketi (public)")
    subprocess.run([PY, str(ROOT / "rapor_durum.py")], cwd=ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
