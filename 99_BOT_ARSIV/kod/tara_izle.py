#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 bitene kadar izle — Chrome/CDP kapanirsa yeniden ac, taramayi surdur.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent if (KOD.parent.parent / "cekilen_tweetler.jsonl").is_file() else KOD.parent
PY = sys.executable
CDP_URL = "http://127.0.0.1:9222/json/version"
SESS = Path(os.environ.get("LOCALAPPDATA", "")) / "ekonomikocu_x_session"
CHROME_CANDIDATES = [
    Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
]


def cdp_ok() -> bool:
    try:
        with urllib.request.urlopen(CDP_URL, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def start_chrome() -> None:
    SESS.mkdir(parents=True, exist_ok=True)
    chrome = next((p for p in CHROME_CANDIDATES if p.is_file()), None)
    if not chrome:
        print("chrome.exe bulunamadi", flush=True)
        return
    subprocess.Popen(
        [
            str(chrome),
            "--remote-debugging-port=9222",
            f"--user-data-dir={SESS}",
            "--lang=tr-TR",
            "--disable-features=Translate,TranslateUI",
            "https://x.com/ekonomikocu",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    print("Chrome baslatildi (9222)", flush=True)


def wait_cdp(sec: int = 60) -> bool:
    for i in range(sec // 2):
        if cdp_ok():
            return True
        time.sleep(2)
    return False


def kapsam_tamam() -> bool:
    import importlib.util

    spec = importlib.util.spec_from_file_location("kapsam_2026", KOD / "kapsam_2026.py")
    if not spec or not spec.loader:
        return False
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return bool(mod.analyze().get("tamam"))


def main() -> int:
    lock = ROOT / "99_BOT_ARSIV" / "log" / "tara_chrome.lock"
    for tur in range(1, 25):
        if kapsam_tamam():
            print("\n2026 %100 — izleme bitti.", flush=True)
            return 0
        print(f"\n>>> IZLE tur {tur}/24", flush=True)
        if not cdp_ok():
            print("CDP kapali — Chrome aciliyor...", flush=True)
            start_chrome()
            if not wait_cdp(90):
                print("CDP gelmedi, 30s sonra tekrar...", flush=True)
                time.sleep(30)
                continue
        try:
            lock.unlink(missing_ok=True)
        except Exception:
            pass
        rc = subprocess.run([PY, str(KOD / "tara_2026_bitir.py")], cwd=ROOT).returncode
        print(f"tara_2026_bitir cikis: {rc}", flush=True)
        if kapsam_tamam():
            return 0
        time.sleep(15)
    print("24 tur doldu — TARAMA_2026.md kontrol et.", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
