#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guvenli tarama girisi: ONCE hesap dogrula, gecerse tara.
Kullanim:
  python tara_guvenli.py                    # ekonomikocu artimli guncel tarama
  python tara_guvenli.py --abone            # abone tweet metinlerini doldur
  python tara_guvenli.py --hesap iriscibre  # ikinci hesap (ayri klasore yazar)
  python tara_guvenli.py --hesap iriscibre --days 7   # son 7 gun

Giris yapilmis X hesabi @420cryptofarmer degilse HICBIR tarama calismaz.
--hesap TARANACAK profili secer; giris yapan hesabi degistirmez."""
from __future__ import annotations
import argparse, os, subprocess, sys
from pathlib import Path

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
PY = sys.executable

def main() -> int:
    ap = argparse.ArgumentParser(description="Hesap dogrulamali tarama")
    ap.add_argument("--abone", action="store_true", help="abone_tamamla.py calistir")
    ap.add_argument("--hesap", default="ekonomikocu",
                    help="Taranacak profil (varsayilan: ekonomikocu). Ornek: --hesap iriscibre")
    ap.add_argument("--port", type=int, default=9222)
    args, ekstra = ap.parse_known_args()
    hesap = (args.hesap or "ekonomikocu").lstrip("@").lower()
    if args.abone and hesap != "ekonomikocu":
        print("--abone sadece ekonomikocu icin gecerli (abone akisi ona ozgu).", flush=True)
        return 2
    sys.path.insert(0, str(KOD))
    try:
        from hesap_dogrula import dogrula
    except Exception as e:
        print(f"hesap_dogrula yuklenemedi: {e}", flush=True)
        return 5
    if not dogrula(port=args.port):
        return 4  # yanlis/eksik hesap — tarama yok
    hedef = "abone_tamamla.py" if args.abone else "tara_guncel_yeni.py"
    cmd = [PY, str(KOD / hedef)] + ekstra
    if not args.abone:
        cmd += ["--handle", hesap]
    # Alt sureclerin tamami ayni hesabi gorsun. SADECE handle ayarlanir; veri koku
    # hesap_kok.veri_koku() tarafindan turetilir — iki ayri ayar tutulmaz ki biri
    # unutulup ikinci hesap ekonomikocu arsivine yazmasin.
    os.environ["EKO_HANDLE"] = hesap
    os.environ.pop("EKO_VERI_KOK", None)
    print(f"[tara_guvenli] hesap=@{hesap} | calistiriliyor: {hedef} {' '.join(ekstra)}", flush=True)
    try:
        rc = subprocess.run(cmd, cwd=str(ROOT)).returncode
    except Exception as e:
        print(f"Tarama hatasi: {e}", flush=True)
        return 1
    # NOT (2026-08-20): Ham veri aynasi (public ekonomikocu-veri) KALDIRILDI.
    # Uzak repo 2026-08-10'dan beri yoktu (404), her taramada hata basiyordu.
    # Geri istenirse: git log -- 99_BOT_ARSIV/kod/veri_ayna_push.py
    # Push sonrasi opsiyonel LFS kota uyarisi — bilgi amacli, akisi BOZMAZ.
    try:
        subprocess.run([PY, str(KOD / "lfs_kota_kontrol.py")], cwd=str(ROOT), check=False)
    except Exception as e:
        print(f"[LFS] kota kontrolu atlandi: {e}", flush=True)
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
