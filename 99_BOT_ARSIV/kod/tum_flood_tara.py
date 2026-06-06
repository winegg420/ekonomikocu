#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tum flood taramasi — sabitle + alinti flood (tum yillar) + #FLOOD thread.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _root()
KOD = Path(__file__).resolve().parent
PY = sys.executable
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--pause", "3000", "--skip-media"]


def run(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    print("\n=== TUM FLOOD TARAMA ===\n", flush=True)

    run("1/3 Sabitle + flood", [PY, str(KOD / "pin_flood_tara.py"), "--attach-port", "9222"])

    run(
        "2/3 Alinti flood (tum yillar + keşif)",
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
            "0",
            "--no-pack",
        ],
    )

    run(
        "3/3 #FLOOD thread parcalari",
        [
            PY,
            str(KOD / "tweet_tara.py"),
            *CDP,
            "--profile-only",
            "--max-scroll",
            "5",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    print("\nTUM FLOOD BITTI.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
