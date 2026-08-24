#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hesap arsivleri birbirine karismis mi? Denetler ve rapor verir.

Kullanim:
    py -3 99_BOT_ARSIV/kod/hesap_denetle.py

Kontroller:
  1) Her hesabin arsivi ayri dosyada mi, isaret dosyasi (_HESAP.txt) dogru mu
  2) tweet_id CAKISMASI var mi (ayni tweet iki arsivde birden)
  3) medya/ klasorlerinde ortak tweet klasoru var mi
  4) Bir arsivde baska hesabin profil baglantisi gecen kayit var mi (ipucu)

Cikis kodu 0 = temiz, 1 = karisma bulundu.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hesap_kok import ANA_HESAP, ISARET_DOSYA, depo_koku  # noqa: E402


def _kayitlar(jsonl: Path) -> list[dict]:
    out = []
    if not jsonl.is_file():
        return out
    for satir in jsonl.open(encoding="utf-8"):
        satir = satir.strip()
        if not satir:
            continue
        try:
            out.append(json.loads(satir))
        except Exception:
            continue
    return out


def hesaplari_bul(depo: Path) -> dict[str, Path]:
    """{handle: veri_koku} — ana hesap + isaret dosyasi olan alt klasorler."""
    bulunan: dict[str, Path] = {}
    if (depo / "cekilen_tweetler.jsonl").is_file():
        bulunan[ANA_HESAP] = depo
    for alt in sorted(p for p in depo.iterdir() if p.is_dir()):
        isaret = alt / ISARET_DOSYA
        if not isaret.is_file():
            continue
        handle = isaret.read_text(encoding="utf-8").strip().lstrip("@").lower()
        if handle:
            bulunan[handle] = alt
    return bulunan


def main() -> int:
    depo = depo_koku()
    hesaplar = hesaplari_bul(depo)
    if not hesaplar:
        print("Hicbir hesap arsivi bulunamadi.")
        return 0

    print(f"Depo koku: {depo}")
    print(f"Bulunan hesap: {len(hesaplar)}\n")

    kimlikler: dict[str, set[str]] = {}
    medyalar: dict[str, set[str]] = {}
    for handle, kok in hesaplar.items():
        kayit = _kayitlar(kok / "cekilen_tweetler.jsonl")
        kimlikler[handle] = {r.get("tweet_id") for r in kayit if r.get("tweet_id")}
        mdir = kok / "medya"
        medyalar[handle] = {p.name for p in mdir.iterdir() if p.is_dir()} if mdir.is_dir() else set()
        tarihler = [r.get("datetime") or "" for r in kayit if r.get("datetime")]
        araligi = f"{min(tarihler)[:10]} .. {max(tarihler)[:10]}" if tarihler else "-"
        print(f"  @{handle:<16} {len(kayit):>6} kayit | {len(medyalar[handle]):>5} medya | {araligi}")
        print(f"  {'':<17} {kok}")

    sorun = 0
    adlar = sorted(hesaplar)
    print("\n--- tweet_id cakismasi ---")
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            ortak = kimlikler[a] & kimlikler[b]
            if ortak:
                sorun += 1
                print(f"  !! @{a} <-> @{b}: {len(ortak)} ORTAK kayit — ornek {list(ortak)[:5]}")
            else:
                print(f"  ok @{a} <-> @{b}: cakisma yok")

    print("\n--- medya klasoru cakismasi ---")
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            ortak = medyalar[a] & medyalar[b]
            if ortak:
                sorun += 1
                print(f"  !! @{a} <-> @{b}: {len(ortak)} ORTAK medya klasoru — {list(ortak)[:5]}")
            else:
                print(f"  ok @{a} <-> @{b}: cakisma yok")

    print("\n--- yabanci profil baglantisi (ipucu) ---")
    for handle, kok in hesaplar.items():
        yabanci = [d for d in adlar if d != handle]
        vurus = {d: 0 for d in yabanci}
        for r in _kayitlar(kok / "cekilen_tweetler.jsonl"):
            bag = (r.get("baglanti") or "").lower()
            for d in yabanci:
                if f"/{d}/status/" in bag:
                    vurus[d] += 1
        kirli = {d: n for d, n in vurus.items() if n}
        if kirli:
            sorun += 1
            print(f"  !! @{handle} arsivinde baska hesabin baglantisi: {kirli}")
        else:
            print(f"  ok @{handle}: yabanci profil baglantisi yok")

    print()
    if sorun:
        print(f"SONUC: {sorun} KARISMA BULGUSU — incelenmeli.")
        return 1
    print("SONUC: TEMIZ — hicbir hesap digerine karismamis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
