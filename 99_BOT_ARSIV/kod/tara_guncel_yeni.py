#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUNCEL ARTIMLI TARAMA — son taramadan bugune yeni tweet + alinti + flood.

Politika: gecmis / %100 tamamlama YOK. Sadece profil ustunden tarar,
en son kayitli tweete (3 gun tamponla) gelince DURUR. Hizli.

Adim:
  1) Profil ustu yeni tweetler (stop-before = en yeni kayit - 3 gun)
  2) #FLOOD thread parcalari (--finish-threads, tarama icinde)
  3) Yeni alintilarin gecmis metni (alinti_tamamla)
  4) Kisa ozet (kac yeni tweet/alinti/flood)

Chrome: sessiz (CHROME_X_SESSIZ.bat, port 9222).
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
PY = sys.executable
JSONL = ROOT / "cekilen_tweetler.jsonl"

TR_AY = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz",
         7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}


def stats() -> tuple[int, int, int, str | None]:
    n = q = f = 0
    newest = None
    if JSONL.exists():
        for line in JSONL.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            n += 1
            if d.get("is_quote"):
                q += 1
            if d.get("thread_root"):
                f += 1
            dt = d.get("datetime")
            if dt and (newest is None or dt > newest):
                newest = dt
    return n, q, f, newest


def main() -> int:
    n0, q0, f0, newest = stats()
    if newest:
        base = datetime.fromisoformat(newest[:19])
    else:
        base = datetime.now() - timedelta(days=7)
    stop = base - timedelta(days=3)
    stop_str = f"{stop.day} {TR_AY[stop.month]}"

    print(f"En yeni kayit: {newest}", flush=True)
    print(f"Stop-before (buraya gelince dur): {stop_str}", flush=True)
    print(f"Baslangic: {n0} tweet | {q0} alinti | {f0} flood-parca\n", flush=True)

    cmd = [
        PY, str(KOD / "tweet_tara.py"),
        "--attach-port", "9222", "--require-cdp",
        "--profile-only", "--stop-before", stop_str,
        "--max-scroll", "120", "--pause", "3500",
        "--finish-threads", "--skip-hafiza",
    ]
    subprocess.run(cmd, cwd=ROOT)

    # Yeni alintilarin gecmis metni (bounded)
    subprocess.run(
        [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "6", "--per-round", "40"],
        cwd=ROOT, check=False,
    )
    subprocess.run([PY, str(KOD / "alinti_dogrula.py")], cwd=ROOT, check=False)

    n1, q1, f1, newest2 = stats()
    print("\n" + "=" * 50, flush=True)
    print("GUNCEL TARAMA BITTI", flush=True)
    print(f"  Yeni tweet : +{n1 - n0}  (toplam {n1})", flush=True)
    print(f"  Yeni alinti: +{q1 - q0}  (toplam {q1})", flush=True)
    print(f"  Yeni flood : +{f1 - f0}  (toplam {f1})", flush=True)
    print(f"  En yeni kayit: {newest2}", flush=True)
    print("=" * 50, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
