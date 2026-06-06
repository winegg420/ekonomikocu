#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calisan tarama surecini durdur, pipeline'i yeniden baslat."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "tamamla_watch_log.txt"
BOOKMARK = ROOT / "tara_bookmark.json"
DEFAULT_PIPELINE = ROOT / "tamamla_ocak_abone.py"

KILL_MARKERS = (
    "tamamla_ocak_abone.py",
    "tamamla_eksiksiz.py",
    "tamamla_abone",
    "tweet_tara.py --attach",
    "devam_gecmis.py",
    "guncelle_yeni.py",
)


def _log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def stop_running_bots() -> int:
    if os.name != "nt":
        return 0
    markers = "|".join(KILL_MARKERS)
    ps = f"""
Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object {{ $_.ProcessId -ne {os.getpid()} -and $_.CommandLine -match '{markers}' }} |
  ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; $_.ProcessId }}
"""
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    pids = [x.strip() for x in (r.stdout or "").splitlines() if x.strip().isdigit()]
    return len(pids)


def start_pipeline(clear_bookmark: bool = True) -> int:
    pipe = Path(os.environ.get("EKO_BOT_PIPELINE", str(DEFAULT_PIPELINE)))
    if not pipe.is_file():
        _log(f"HATA: pipeline yok: {pipe}")
        return 1
    if clear_bookmark and BOOKMARK.exists():
        BOOKMARK.unlink(missing_ok=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    with LOG.open("a", encoding="utf-8") as out:
        subprocess.Popen(
            [sys.executable, str(pipe)],
            cwd=ROOT,
            stdout=out,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
    _log(f"Baslatildi: {pipe.name} (log: {LOG.name})")
    return 0


def restart(*, clear_bookmark: bool = True, wait_sec: float = 2.0) -> int:
    n = stop_running_bots()
    _log(f"Durdurulan surec: {n}")
    time.sleep(wait_sec)
    return start_pipeline(clear_bookmark=clear_bookmark)


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Bot yeniden baslat")
    p.add_argument("--no-bookmark-clear", action="store_true")
    p.add_argument("--stop-only", action="store_true")
    args = p.parse_args()
    if args.stop_only:
        stop_running_bots()
        return 0
    return restart(clear_bookmark=not args.no_bookmark_clear)


if __name__ == "__main__":
    raise SystemExit(main())
