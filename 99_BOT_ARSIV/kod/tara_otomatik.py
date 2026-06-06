#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tarama supervisor — takilinca veya Chrome/CDP kopunca otomatik yeniden baslat.

Ornek:
  python tara_otomatik.py --script tara_2025_devam.py
  python tara_otomatik.py --script tum_flood_tara.py --log tum_flood_out.txt
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

KOD = Path(__file__).resolve().parent


def _root() -> Path:
    up = KOD.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _root()
LOG_DIR = ROOT / "99_BOT_ARSIV" / "log"
PY = sys.executable
CDP_URL = "http://127.0.0.1:9222/json/version"
SESS = Path(os.environ.get("LOCALAPPDATA", "")) / "ekonomikocu_x_session"
CHROME_CANDIDATES = [
    Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
]
LOCK = LOG_DIR / "tara_chrome.lock"
HEARTBEAT = LOG_DIR / "tara_heartbeat.txt"


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with (LOG_DIR / "tara_otomatik.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


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
        _log("HATA: chrome.exe bulunamadi")
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
    _log("Chrome baslatildi (9222)")


def wait_cdp(sec: int = 90) -> bool:
    for _ in range(sec // 2):
        if cdp_ok():
            return True
        time.sleep(2)
    return False


def clear_lock() -> None:
    try:
        LOCK.unlink(missing_ok=True)
    except Exception:
        pass


def kill_child(proc: subprocess.Popen | None) -> None:
    if not proc or proc.poll() is not None:
        return
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            timeout=15,
        )
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _activity_stamp(log_path: Path, proc: subprocess.Popen | None) -> float:
    """Son aktivite: log, heartbeat veya alt surec canli."""
    t = max(_mtime(log_path), _mtime(HEARTBEAT), _mtime(LOCK))
    if proc and proc.poll() is None:
        t = max(t, time.time() - 5)
    return t


def run_supervised(
    script: str,
    log_name: str,
    *,
    stall_sec: int,
    check_sec: int,
    max_restarts: int,
) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / log_name
    script_path = KOD / script
    if not script_path.is_file():
        _log(f"HATA: script yok: {script_path}")
        return 1

    restarts = 0
    proc: subprocess.Popen | None = None

    def launch() -> subprocess.Popen:
        nonlocal restarts
        clear_lock()
        if not cdp_ok():
            _log("CDP yok — Chrome aciliyor...")
            start_chrome()
            if not wait_cdp(90):
                _log("CDP gelmedi — yine de denenecek")
        with log_path.open("a", encoding="utf-8") as lf:
            lf.write(f"\n=== OTOMATIK BASLA {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        _log(f"Baslatiliyor: {script} (deneme {restarts + 1})")
        return subprocess.Popen(
            [PY, "-u", str(script_path)],
            cwd=ROOT,
            stdout=open(log_path, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )

    proc = launch()
    last_active = _activity_stamp(log_path, proc)

    try:
        while restarts < max_restarts:
            time.sleep(check_sec)
            if proc.poll() is not None:
                code = proc.returncode
                _log(f"Surec bitti (kod {code})")
                if code == 0:
                    _log("Normal bitis — supervisor duruyor.")
                    return 0
                restarts += 1
                if restarts >= max_restarts:
                    break
                _log(f"Yeniden baslatiliyor ({restarts}/{max_restarts})...")
                time.sleep(10)
                proc = launch()
                last_active = _activity_stamp(log_path, proc)
                continue

            if not cdp_ok():
                _log("TAKILMA: CDP kapali — Chrome + surec yenileniyor")
                kill_child(proc)
                clear_lock()
                start_chrome()
                wait_cdp(60)
                restarts += 1
                proc = launch()
                last_active = _activity_stamp(log_path, proc)
                continue

            active = _activity_stamp(log_path, proc)
            if active > last_active:
                last_active = active
                continue

            idle = time.time() - last_active
            if idle >= stall_sec:
                _log(
                    f"TAKILMA: {idle:.0f}s log/heartbeat yok — "
                    f"surec oldurulup yeniden baslatiliyor"
                )
                kill_child(proc)
                clear_lock()
                if not cdp_ok():
                    start_chrome()
                    wait_cdp(60)
                restarts += 1
                time.sleep(8)
                proc = launch()
                last_active = _activity_stamp(log_path, proc)

        _log(f"Max yeniden baslatma ({max_restarts}) — durdu.")
        return 1
    except KeyboardInterrupt:
        _log("Durduruldu (Ctrl+C)")
        kill_child(proc)
        clear_lock()
        return 130


def main() -> int:
    parser = argparse.ArgumentParser(description="Tarama otomatik yeniden baslat")
    parser.add_argument("--script", default="tara_2025_devam.py", help="kod/ altindaki script")
    parser.add_argument(
        "--log",
        default="",
        help="log dosya adi (varsayilan: script adindan)",
    )
    parser.add_argument(
        "--stall-sec",
        type=int,
        default=420,
        help="Bu kadar sn log yoksa takildi say (varsayilan 7 dk)",
    )
    parser.add_argument("--check-sec", type=int, default=45, help="Kontrol araligi")
    parser.add_argument("--max-restarts", type=int, default=48, help="Max yeniden baslatma")
    args = parser.parse_args()

    log_name = args.log.strip() or args.script.replace(".py", "_out.txt")
    _log(f"Supervisor: {args.script} | log={log_name} | stall={args.stall_sec}s")
    return run_supervised(
        args.script,
        log_name,
        stall_sec=args.stall_sec,
        check_sec=args.check_sec,
        max_restarts=args.max_restarts,
    )


if __name__ == "__main__":
    raise SystemExit(main())
