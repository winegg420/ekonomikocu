#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mart 2026 — X arama modu (profil kaydirma yerine)."""
from __future__ import annotations

import subprocess
import sys
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


def main() -> int:
    cmd = [
        PY,
        str(KOD / "tweet_tara.py"),
        "--attach-port",
        "9222",
        "--require-cdp",
        "--since-date",
        "2026-03-01",
        "--until-date",
        "2026-04-01",
        "--max-scroll",
        "300",
        "--pause",
        "4000",
        "--no-finish-quotes",
    ]
    print("Mart 2026 — arama: from:ekonomikocu since:2026-03-01 until:2026-04-01", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
