#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kalici erisilemez ("inatci") alintilari isaretle -> sonsuz retry dongusunu kapat.

Bazi alintilar X UI kisaltmasi / birbirini alintilama nedeniyle metni ASLA
tamamlanamaz. Bunlar her taramada tekrar tekrar ziyaret edilir (nav israfi).
Bu script boyle satirlari bulup `kalici_erisilemedi: true` alaniyla isaretler;
alinti_common.row_quote_needs_visit() bu alani gorunce bir daha ziyaret etmez.

Kriter (tahmin degil, saf mantik): is_quote true + metin dolu +
alinti_common.quote_text_incomplete(metin) True + row_quote_needs_visit True
(yani "metin kesik" sebebiyle Asama 2'de takili) + henuz isaretlenmemis.

Kaynak dosya cekilen_tweetler.jsonl'dir (tarama retry dongusu bunu okur); paket
dosyalari 04/07 de tutarlilik icin ayni sekilde guncellenir. Idempotent: ikinci
calistirmada 0 satir bulur.

Kullanim:
    python kalici_isaretle.py            # isaretle + yaz
    python kalici_isaretle.py --dry-run  # sadece bul, yazma
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_KOD_DIR = Path(__file__).resolve().parent
if str(_KOD_DIR) not in sys.path:
    sys.path.insert(0, str(_KOD_DIR))

from alinti_common import quote_text_incomplete, row_from_jsonl, row_quote_needs_visit


def _root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return here


ROOT = _root()
HEDEF_DOSYALAR = [
    ROOT / "cekilen_tweetler.jsonl",   # tarama retry dongusunun okudugu kaynak
    ROOT / "04_TWEETLER.jsonl",        # paket (public)
    ROOT / "07_ABONE_TWEETLER.jsonl",  # paket (abone)
]


def inatci_mi(o: dict) -> bool:
    """Kalici erisilemez ("metin kesik") inatci alinti mi?"""
    if o.get("kalici_erisilemedi"):
        return False
    if not o.get("is_quote"):
        return False
    text = (o.get("text") or "").strip()
    if not text:
        return False
    if not quote_text_incomplete(text):
        return False
    return row_quote_needs_visit(row_from_jsonl(o))


def dosya_isle(path: Path, dry: bool) -> list[str]:
    """Dosyadaki inatci alintilari isaretle, isaretlenen tweet_id listesini dondur."""
    if not path.is_file():
        print(f"  ATLA (yok): {path.name}")
        return []
    satirlar = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    kayitlar = [json.loads(l) for l in satirlar]
    isaretlenen: list[str] = []
    for o in kayitlar:
        if inatci_mi(o):
            o["kalici_erisilemedi"] = True
            isaretlenen.append(str(o.get("tweet_id")))
    if isaretlenen and not dry:
        path.write_text(
            "\n".join(json.dumps(o, ensure_ascii=False) for o in kayitlar) + "\n",
            encoding="utf-8",
        )
    return isaretlenen


def main() -> int:
    dry = "--dry-run" in sys.argv
    print(f"KALICI ISARETLE {'(dry-run)' if dry else ''} | kok: {ROOT}")
    toplam = 0
    for path in HEDEF_DOSYALAR:
        ids = dosya_isle(path, dry)
        toplam += len(ids)
        print(f"  {path.name}: {len(ids)} satir isaretlendi")
        for tid in ids:
            print(f"     - {tid}")
    print(f"TOPLAM isaretlenen satir: {toplam}"
          + (" (yazilmadi: dry-run)" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
