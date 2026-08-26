# -*- coding: utf-8 -*-
"""Gorsel analiz defteri.

medya/ altindaki her gorsel icin bir kayit tutar: hangi tweete ait, tweet metni,
tarih, urunler ve (analiz yapildiysa) analiz metni. Analiz oturumlar arasi
kesintiye dayanikli olsun diye ilerleme JSONL'de tutulur; ayni gorsel iki kez
analiz edilmez.

Kullanim:
    py -3 gorsel_defter.py durum              # kac gorsel var / kaci analizli
    py -3 gorsel_defter.py sirada [N] [--eski]  # analiz bekleyen ilk N gorsel (varsayilan yeniden eskiye)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFTER = ROOT / "gorsel_analiz.jsonl"
UZANTI = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _hesap_kok(hesap: str) -> Path:
    return ROOT if hesap == "ekonomikocu" else ROOT / hesap


def tweet_bilgi(hesap: str = "ekonomikocu") -> dict:
    """tweet_id -> {datetime, text, products}"""
    kok = _hesap_kok(hesap)
    yol = kok / "cekilen_tweetler.jsonl"
    bilgi: dict[str, dict] = {}
    if not yol.exists():
        return bilgi
    with yol.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            tid = str(d.get("tweet_id") or "")
            if tid:
                bilgi[tid] = {
                    "datetime": d.get("datetime") or "",
                    "text": (d.get("text") or "").replace("\n", " ")[:400],
                    "products": d.get("products") or [],
                    "tip": d.get("tip") or [],
                }
    return bilgi


def gorseller(hesap: str = "ekonomikocu") -> list[dict]:
    kok = _hesap_kok(hesap)
    medya = kok / "medya"
    bilgi = tweet_bilgi(hesap)
    out: list[dict] = []
    if not medya.exists():
        return out
    for klasor in medya.iterdir():
        if not klasor.is_dir():
            continue
        tid = klasor.name
        for dosya in sorted(klasor.iterdir()):
            if dosya.suffix.lower() not in UZANTI:
                continue
            meta = bilgi.get(tid, {})
            out.append({
                "hesap": hesap,
                "tweet_id": tid,
                "dosya": str(dosya.relative_to(ROOT)).replace("\\", "/"),
                "datetime": meta.get("datetime", ""),
                "text": meta.get("text", ""),
                "products": meta.get("products", []),
            })
    out.sort(key=lambda r: (r["datetime"], r["dosya"]), reverse=True)
    return out


def analizli() -> set[str]:
    s: set[str] = set()
    if not DEFTER.exists():
        return s
    with DEFTER.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("analiz"):
                s.add(d.get("dosya", ""))
    return s


def kaydet(kayitlar: list[dict]) -> int:
    """Analiz kayitlarini deftere ekler (append). Var olan dosyalari atlar."""
    var = analizli()
    n = 0
    with DEFTER.open("a", encoding="utf-8") as f:
        for k in kayitlar:
            if not k.get("dosya") or k["dosya"] in var:
                continue
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
            var.add(k["dosya"])
            n += 1
    return n


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    komut = sys.argv[1] if len(sys.argv) > 1 else "durum"
    hesaplar = ["ekonomikocu", "iriscibre", "efloud"]
    tum: list[dict] = []
    for h in hesaplar:
        tum.extend(gorseller(h))
    yapilmis = analizli()
    bekleyen = [g for g in tum if g["dosya"] not in yapilmis]

    if komut == "durum":
        print(f"toplam gorsel : {len(tum)}")
        print(f"analiz edilmis: {len(yapilmis)}")
        print(f"bekleyen      : {len(bekleyen)}")
        for h in hesaplar:
            t = [g for g in tum if g["hesap"] == h]
            b = [g for g in bekleyen if g["hesap"] == h]
            print(f"  {h:12s} toplam {len(t):5d}  bekleyen {len(b):5d}")
        return 0

    if komut == "sirada":
        n = 20
        for a in sys.argv[2:]:
            if a.isdigit():
                n = int(a)
        if "--eski" in sys.argv:
            bekleyen = sorted(bekleyen, key=lambda r: (r["datetime"], r["dosya"]))
        for g in bekleyen[:n]:
            print(json.dumps(g, ensure_ascii=False))
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
