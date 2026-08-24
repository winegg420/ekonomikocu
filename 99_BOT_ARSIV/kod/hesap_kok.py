#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hesap bazli veri koku — birden fazla X hesabini BIRBIRINE KARISTIRMADAN tutar.

Kural (tek kaynak, butun tarama modulleri burayi kullanir):

    EKO_HANDLE yok  ya da  "ekonomikocu"   ->  depo koku          (eski davranis)
    EKO_HANDLE = <baska hesap>             ->  depo koku/<handle>  (ayri klasor)
    EKO_VERI_KOK verilmisse                ->  o yol kazanir       (elle yonlendirme)

Neden bu dosya var: handle ile veri koku AYRI AYRI ayarlanabilseydi, biri verilip
digeri unutuldugunda ikinci hesabin tweetleri ekonomikocu arsivine yazilirdi.
Burada kok DAIMA handle'dan turetiliyor; unutulacak ikinci bir ayar yok.

Ek koruma — `_HESAP.txt` isaret dosyasi: her ikincil veri kokunun icine hesap adi
yazilir. Baska bir hesap ayni klasore yazmaya kalkarsa RuntimeError firlatilir.
"""
from __future__ import annotations

import os
from pathlib import Path

ANA_HESAP = "ekonomikocu"
ISARET_DOSYA = "_HESAP.txt"


def aktif_handle() -> str:
    """Su an taranan hesap (kucuk harf, bastaki @ atilmis)."""
    return (os.environ.get("EKO_HANDLE") or ANA_HESAP).lstrip("@").lower().strip()


def depo_koku() -> Path:
    """Git deposunun koku — hesaptan BAGIMSIZ, her zaman ayni yer."""
    here = Path(__file__).resolve().parent          # .../99_BOT_ARSIV/kod
    up = here.parent.parent                          # depo koku
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    return up


def veri_koku(dogrula: bool = True) -> Path:
    """Aktif hesabin veri klasoru. Ana hesap icin depo koku, digerleri icin alt klasor."""
    handle = aktif_handle()
    ozel = os.environ.get("EKO_VERI_KOK")
    depo = depo_koku()
    if ozel:
        kok = Path(ozel).resolve()
    elif handle and handle != ANA_HESAP:
        kok = depo / handle
    else:
        kok = depo
    if dogrula:
        kok_dogrula(kok, handle, depo)
    return kok


def kok_dogrula(kok: Path, handle: str, depo: Path | None = None) -> None:
    """Yanlis hesabin yanlis klasore yazmasini engelle.

    Iki kontrol:
      1) Ikincil hesap DEPO KOKUNE yazamaz — orasi ekonomikocu arsivi.
      2) Klasordeki `_HESAP.txt` baska bir hesabi gosteriyorsa dur.
    """
    depo = depo or depo_koku()
    if handle != ANA_HESAP and kok == depo:
        raise RuntimeError(
            f"KARISMA ENGELI: @{handle} icin veri koku depo koku olarak cozuldu "
            f"({kok}). Ikincil hesap ekonomikocu arsivine YAZAMAZ. "
            f"EKO_VERI_KOK degerini kaldir ya da <depo>/{handle} yap."
        )
    if handle == ANA_HESAP and kok != depo:
        raise RuntimeError(
            f"KARISMA ENGELI: ekonomikocu icin veri koku {kok} olarak cozuldu, "
            f"beklenen {depo}. EKO_VERI_KOK/EKO_HANDLE degerlerini temizle."
        )
    if kok == depo:
        return  # ana arsivde isaret dosyasi tutmuyoruz
    isaret = kok / ISARET_DOSYA
    if isaret.is_file():
        yazan = isaret.read_text(encoding="utf-8").strip().lstrip("@").lower()
        if yazan and yazan != handle:
            raise RuntimeError(
                f"KARISMA ENGELI: {kok} klasoru @{yazan} hesabina ait "
                f"(_HESAP.txt), @{handle} buraya yazamaz."
            )
    else:
        kok.mkdir(parents=True, exist_ok=True)
        isaret.write_text(handle + "\n", encoding="utf-8")


if __name__ == "__main__":
    h = aktif_handle()
    print(f"hesap     : @{h}")
    print(f"depo koku : {depo_koku()}")
    print(f"veri koku : {veri_koku()}")
