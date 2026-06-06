#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Once 2026 %100, sonra 2025. Tek komut."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
PY = sys.executable


def main() -> int:
    rc = subprocess.run([PY, str(KOD / "tara_2026_bitir.py")], cwd=ROOT).returncode
    if rc != 0:
        return rc
    return subprocess.run([PY, str(KOD / "tara_2025_devam.py")], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
