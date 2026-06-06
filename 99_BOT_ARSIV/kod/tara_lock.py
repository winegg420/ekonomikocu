#!/usr/bin/env python3
"""Tek Chrome bot — cift calistirmayi engelle (alt surec serbest)."""
from __future__ import annotations

import os
from pathlib import Path


def _lock_path() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    return root / "99_BOT_ARSIV" / "log" / "tara_chrome.lock"


def _holder_pid() -> int | None:
    p = _lock_path()
    if not p.exists():
        return None
    try:
        return int(p.read_text(encoding="utf-8").strip().split()[0])
    except Exception:
        return None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire(label: str) -> bool:
    p = _lock_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    holder = _holder_pid()
    me = os.getpid()
    if holder and holder != me:
        if _alive(holder):
            # Ana tarama alt sureci (abone_tamamla vb.)
            if os.getppid() == holder:
                return True
            print(
                f"TARAMA ZATEN ACIK (pid {holder}). Baska .bat calistirma.",
                flush=True,
            )
            return False
        try:
            p.unlink()
        except Exception:
            pass
    p.write_text(f"{me} {label}\n", encoding="utf-8")
    return True


def release() -> None:
    p = _lock_path()
    try:
        if p.exists() and p.read_text(encoding="utf-8").startswith(str(os.getpid())):
            p.unlink()
    except Exception:
        pass
