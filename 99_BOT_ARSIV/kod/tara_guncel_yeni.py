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

import argparse
import json
import subprocess
import sys
import time
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
    ap = argparse.ArgumentParser(description="Guncel artimli tarama")
    ap.add_argument("--days", type=int, default=None,
                    help="Bugunden N gun geriye tara (artimli tamponu yok sayar)")
    ap.add_argument("--stop-before", dest="stop_before", default=None,
                    help="Tarama bu tarihe gelince dursun (orn: '11 Haz')")
    ap.add_argument("--alinti-rounds", type=int, default=6,
                    help="Alinti tamamlama tur sayisi")
    ap.add_argument("--alinti-per", type=int, default=40,
                    help="Alinti tamamlama tur basina adet")
    ap.add_argument("--since", default=None,
                    help="Donem taramasi: YYYY-MM-DD baslangic (arama akisi, profil kaydirmasi yok)")
    ap.add_argument("--until", default=None,
                    help="Donem taramasi: YYYY-MM-DD bitis (X aramasi bu gunu HARIC tutar)")
    ap.add_argument("--bolum-gun", type=int, default=4,
                    help="Donem penceresi buyuklugu (gun) — rate limit yememek icin bol")
    ap.add_argument("--soguma-sn", type=int, default=300,
                    help="Pencereler arasi bekleme (sn) — X limitine nefes aldirir")
    args, _ = ap.parse_known_args()

    n0, q0, f0, newest = stats()
    if args.stop_before:
        stop = None
        stop_str = args.stop_before
    elif args.days is not None:
        stop = datetime.now() - timedelta(days=args.days)
        stop_str = f"{stop.day} {TR_AY[stop.month]}"
    else:
        if newest:
            base = datetime.fromisoformat(newest[:19])
        else:
            base = datetime.now() - timedelta(days=7)
        stop = base - timedelta(days=3)
        stop_str = f"{stop.day} {TR_AY[stop.month]}"

    print(f"En yeni kayit: {newest}", flush=True)
    if args.since and args.until:
        print(f"DONEM MODU: {args.since} -> {args.until} "
              f"({args.bolum_gun} gunluk pencereler, ara soguma {args.soguma_sn} sn)", flush=True)
    else:
        print(f"Stop-before (buraya gelince dur): {stop_str}", flush=True)
    print(f"Baslangic: {n0} tweet | {q0} alinti | {f0} flood-parca\n", flush=True)

    if args.since and args.until:
        # DONEM MODU: from:ekonomikocu since:.. until:.. arama akisi.
        # Profilin ustundeki zaten-kayitli haftalari kaydirma israfi yok;
        # aralik kucuk pencerelere bolunur, aralarda soguma ile limit yenilmez.
        s_dt = datetime.fromisoformat(args.since)
        u_dt = datetime.fromisoformat(args.until)
        pencereler: list[tuple[str, str]] = []
        # En yeniden geriye dogru pencere olustur
        p_end = u_dt
        while p_end > s_dt:
            p_start = max(s_dt, p_end - timedelta(days=args.bolum_gun))
            pencereler.append((p_start.strftime("%Y-%m-%d"), p_end.strftime("%Y-%m-%d")))
            p_end = p_start
        for k, (ps, pu) in enumerate(pencereler, 1):
            print(f"\n--- Pencere {k}/{len(pencereler)}: {ps} -> {pu} ---", flush=True)
            cmd = [
                PY, str(KOD / "tweet_tara.py"),
                "--attach-port", "9222", "--require-cdp",
                "--since-date", ps, "--until-date", pu,
                "--max-scroll", "100", "--pause", "5000",
                "--finish-threads", "--skip-hafiza", "--no-finish-quotes",
            ]
            subprocess.run(cmd, cwd=ROOT)
            np, _, _, _ = stats()
            print(f"--- Pencere {k} bitti | toplam {np} tweet ---", flush=True)
            if k < len(pencereler):
                print(f"Soguma: {args.soguma_sn} sn (X limitine nefes)...", flush=True)
                time.sleep(args.soguma_sn)
    else:
        cmd = [
            PY, str(KOD / "tweet_tara.py"),
            "--attach-port", "9222", "--require-cdp",
            "--profile-only", "--stop-before", stop_str,
            "--max-scroll", "120", "--pause", "5000",
            "--finish-threads", "--skip-hafiza",
        ]
        subprocess.run(cmd, cwd=ROOT)

    # Yeni alintilarin gecmis metni (bounded)
    subprocess.run(
        [PY, str(KOD / "alinti_tamamla.py"),
         "--max-rounds", str(args.alinti_rounds), "--per-round", str(args.alinti_per)],
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
    # 5) Siniflandirma: ham taranan tweetler paketlemeden ONCE analyzed:true yapilir
    try:
        subprocess.run([PY, str(KOD / "analiz_devam.py")], cwd=str(ROOT), check=False)
    except Exception as e:
        print(f"[analiz] analiz_devam.py hatasi: {e}", flush=True)
    # 6) Paketleme: ham veriden 04/07 + kapsam yeniden uretilir
    for _script in ("claude_paket_olustur.py", "kapsam_durum.py"):
        try:
            subprocess.run([PY, str(KOD / _script)], cwd=str(ROOT), check=False)
        except Exception as e:
            print(f"[paket] {_script} hatasi: {e}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
