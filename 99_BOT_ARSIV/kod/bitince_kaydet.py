#!/usr/bin/env python3
"""JSONL guncellenince analiz calistir (tarama bitince)."""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"


def count_lines() -> int:
    if not JSONL.exists():
        return 0
    return sum(1 for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip())


def main() -> None:
    start = count_lines()
    print(f"Bekleniyor (simdiki: {start} satir)...", flush=True)
    last = start
    stable = 0
    while stable < 3:
        time.sleep(15)
        n = count_lines()
        if n != last:
            print(f"  -> {n} tweet diske yazildi", flush=True)
            last = n
            stable = 0
        else:
            stable += 1
    print(f"Kayit tamam: {last} tweet. Analiz...", flush=True)
    from analiz_devam import run_full_analysis

    run_full_analysis(write_hafiza=True)
    print("Bitti.")


if __name__ == "__main__":
    main()
