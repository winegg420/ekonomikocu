# -*- coding: utf-8 -*-
"""log/eksik_abone.jsonl'deki (aramada bulunan, arsivde olmayan) tweetleri
mevcut kayit hattindan arsive ekler:
- datetime tweet_id snowflake'inden (dt_from_snowflake)
- abone_ozel arama isaretinden (icon-subscriber)
- tip/urun siniflandirma apply_to_record ile
save_jsonl mevcut 4750 kaydi korur, yalnizca yenileri ekler.
Not: arama karti uzun tweetlerde metni kisaltabilir; eksik olmaktansa
kismi metin yeglenir, sonraki tam tarama doldurur (save_jsonl kisa ile ezmez).
"""
import json
import sys
from pathlib import Path

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
sys.path.insert(0, str(KOD))
import os
os.chdir(ROOT)

from tweet_tara import scraped_to_records, save_jsonl

JSONL = Path("cekilen_tweetler.jsonl")
EKSIK = Path("log/eksik_abone.jsonl")


def main():
    arc = set()
    for line in JSONL.open(encoding="utf-8"):
        line = line.strip()
        if line:
            arc.add(str(json.loads(line).get("tweet_id")))

    rows = []
    for line in EKSIK.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        tid = str(e.get("tweet_id"))
        if tid in arc:
            continue
        text = (e.get("text") or "").strip()
        rows.append({
            "id": tid,
            "text": text,
            "datetime": e.get("dt"),
            "isQuote": False,
            "quotedBy": None,
            "quoteOf": None,
            "threadRoot": None,
            "media": [],
            "aboneOzel": bool(e.get("abone")),
        })

    print(f"Eklenecek yeni kayit: {len(rows)}")
    if not rows:
        return
    records = scraped_to_records(rows)
    n_before = sum(1 for _ in JSONL.open(encoding="utf-8"))
    save_jsonl(records, JSONL)
    n_after = sum(1 for _ in JSONL.open(encoding="utf-8"))
    print(f"Arsiv: {n_before} -> {n_after} (+{n_after - n_before})")


if __name__ == "__main__":
    main()
