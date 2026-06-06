#!/usr/bin/env python3
"""Public tweet + alinti + grafik durumu (abonelik/kilitli sayilmaz)."""
import json
from datetime import datetime
from pathlib import Path

JSONL = Path(__file__).parent / "cekilen_tweetler.jsonl"
MEDYA = Path(__file__).parent / "medya"
ERISILEMEDI = "[erişilemedi]"


def has_text(r: dict) -> bool:
    t = (r.get("text") or "").strip()
    return bool(t) and t != ERISILEMEDI


def main():
    rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    public_main = [
        r for r in rows if not r.get("is_quote") and not r.get("locked") and has_text(r)
    ]
    quotes = [r for r in rows if r.get("is_quote")]
    quotes_ok = [r for r in quotes if has_text(r)]
    quotes_eksik = [r for r in quotes if not has_text(r)]
    grafikli = [r for r in rows if r.get("media_files") and (not r.get("locked") or r.get("is_quote"))]
    en = [r for r in public_main if r.get("lang") == "en"]

    oldest = newest = None
    may_oncesi = 0
    for r in public_main:
        dt = r.get("datetime")
        if not dt:
            continue
        d = datetime.fromisoformat(dt.replace("Z", "+00:00")).replace(tzinfo=None)
        if oldest is None or d < oldest:
            oldest = d
        if newest is None or d > newest:
            newest = d
        if d < datetime(2026, 5, 1):
            may_oncesi += 1

    medya_klasor = len(list(MEDYA.iterdir())) if MEDYA.is_dir() else 0

    print("=== PUBLIC (kilitli/abonelik haric) ===")
    print(f"Ana tweet (tam metin): {len(public_main)}")
    print(f"Alinti: {len(quotes)} | tam metin: {len(quotes_ok)} | EKSIK: {len(quotes_eksik)}")
    print(f"Grafik dosyasi olan kayit: {len(grafikli)} | medya/ klasor: {medya_klasor}")
    print(f"Ingilizce(kirli) public: {len(en)}")
    print(f"Mayis 2026 oncesi public ana: {may_oncesi}")
    print(f"Tarih araligi: {oldest} -> {newest}")

    if quotes_eksik:
        print("\nEksik alintilar (metin/grafik tamamlanmali):")
        for r in quotes_eksik[:8]:
            print(f"  {r['tweet_id']} <- ana {r.get('quoted_by')}")

    hazir = len(en) == 0 and len(quotes_eksik) <= 5
    print("\nDURUM:", "Public analize hazir" if hazir else "Eksik alinti veya Ocak-Mart taramasi devam")
    if may_oncesi < 80:
        print("- Subat 2026 oncesi: devam_gecmis.py / derin tarama")


if __name__ == "__main__":
    main()
