#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tum zenginlestirme adimlarini sirayla calistir."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

KOD = Path(__file__).resolve().parent.parent
ROOT = KOD.parent.parent


def run(script: str) -> int:
    print(f"\n=== {script} ===", flush=True)
    return subprocess.run([sys.executable, str(KOD / "enrichment" / script)], cwd=ROOT).returncode


def main() -> int:
    steps = ["kaynak_etiketle.py", "cagri_cikar.py", "grafik_vision_oku.py"]
    for s in steps:
        code = run(s)
        if code != 0:
            print(f"HATA: {s} kod {code}", flush=True)
            return code
    print("\nZenginlestirme tamam.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
