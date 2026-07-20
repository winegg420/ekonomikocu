#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Git LFS kota izleme — SADECE UYARI (prune / silme / history-rewrite YOK).

GitHub ucretsiz LFS kotasi: 1 GB depolama + 1 GB/ay bant genisligi. Her tarama
05_GRAFIKLER.zip'in yeni bir ~106 MB surumunu ekler; eski surumler de kotada
sayilir. Bu script tum LFS surumlerinin toplam boyutunu hesaplar, %70 esigi
asilinca acik uyari basar ve kac tarama daha sigacagini tahmin eder.

Hicbir sey silmez, gecmisi yeniden yazmaz — yalnizca bilgilendirir.

Kullanim:
    python lfs_kota_kontrol.py
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

KOTA_MB = 1024          # GitHub ucretsiz LFS depolama: 1 GB
ESIK_ORAN = 0.70        # %70 -> uyari
TARAMA_MB = 106         # her tarama ~106 MB yeni LFS surumu ekler

_BIRIM = {"B": 1 / (1024 * 1024), "KB": 1 / 1024, "MB": 1.0, "GB": 1024.0}
_RE_BOYUT = re.compile(r"\(([\d.]+)\s*(B|KB|MB|GB)\)\s*$")


def _proje_kok() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    return up if (up / ".git").exists() else here


def lfs_toplam_mb(kok: Path) -> float | None:
    """Tum LFS surumlerinin (--all) toplam boyutu, MB. git lfs yoksa None."""
    try:
        cp = subprocess.run(
            ["git", "lfs", "ls-files", "--all", "-s"],
            cwd=str(kok), capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode != 0:
        return None
    toplam = 0.0
    for satir in cp.stdout.splitlines():
        m = _RE_BOYUT.search(satir.strip())
        if m:
            toplam += float(m.group(1)) * _BIRIM[m.group(2)]
    return toplam


def main() -> int:
    kok = _proje_kok()
    mb = lfs_toplam_mb(kok)
    if mb is None:
        print("[LFS] git lfs bulunamadi ya da LFS objesi yok — kontrol atlandi.")
        return 0

    oran = mb / KOTA_MB
    kalan_mb = max(KOTA_MB - mb, 0.0)
    kalan_tarama = int(kalan_mb // TARAMA_MB)
    print(
        f"[LFS] Depo kullanimi: {mb:.0f} MB / {KOTA_MB} MB (%{oran * 100:.0f}) | "
        f"tahmini {kalan_tarama} tarama daha sigar (~{TARAMA_MB} MB/tarama)"
    )

    if oran >= ESIK_ORAN:
        print("=" * 62)
        print(f"!! UYARI: LFS deposu %{oran * 100:.0f} dolu ({mb:.0f}/{KOTA_MB} MB).")
        print(f"!! Yalnizca ~{kalan_tarama} taramaya yer kaldi.")
        print("!! Kota dolmadan eski 05_GRAFIKLER.zip surumlerini GitHub tarafinda")
        print("!! temizlemeyi (repo ayarlari / manuel) degerlendir.")
        print("!! (Bu script hicbir sey silmez — sadece uyarir.)")
        print("=" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
