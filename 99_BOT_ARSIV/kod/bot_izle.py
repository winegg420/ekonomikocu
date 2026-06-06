#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kod dosyalari degisince botu otomatik yeniden baslat.
Baslat: python bot_izle.py   veya BOT_IZLE.bat
"""
from __future__ import annotations

import time
from pathlib import Path

from bot_yeniden_baslat import _log, restart

ROOT = Path(__file__).resolve().parent
WATCH = (
    "tweet_tara.py",
    "tara_nav.py",
    "tamamla_ocak_abone.py",
    "tamamla_eksiksiz.py",
    "eko_filtre.py",
    "alinti_tamamla.py",
    "bot_yeniden_baslat.py",
)
DEBOUNCE_SEC = 4.0
POLL_SEC = 2.0


def mtimes() -> dict[str, float]:
    out: dict[str, float] = {}
    for name in WATCH:
        p = ROOT / name
        if p.is_file():
            out[name] = p.stat().st_mtime
    return out


def main() -> int:
    _log("Izleyici acik — dosya degisince bot yeniden baslar.")
    prev = mtimes()
    pending: float | None = None
    pending_m: dict[str, float] | None = None

    while True:
        time.sleep(POLL_SEC)
        cur = mtimes()
        if cur == prev:
            if pending and (time.time() - pending) >= DEBOUNCE_SEC:
                changed = [
                    k
                    for k in cur
                    if pending_m and cur.get(k) != pending_m.get(k)
                ]
                _log(f"Guncelleme: {', '.join(changed) or 'dosya'}")
                restart()
                prev = mtimes()
                pending = None
                pending_m = None
            continue
        if not pending:
            pending = time.time()
            pending_m = dict(prev)
        prev = cur


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        _log("Izleyici durdu.")
        raise SystemExit(0)
