#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""@ekonomikocu dil / sozluk / ton — yalnizca PUBLIC tweetler."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"
HAFIZA = ROOT / "ekonomikocu_hafiza_v1.md"
MARKER = "## 4. KOÇ DİLİ VE SÖZLÜK (otomatik)"

HASHTAG_RX = re.compile(r"#\w+", re.UNICODE)
PHRASE_KEYS = [
    "zaman geçir",
    "oyalama",
    "vade doldur",
    "demiştim",
    "söylemiştim",
    "hatırlayın",
    "zincirleri birleştir",
    "mantıklı",
    "mantıksız",
    "Subscribers",
    "#FLOOD",
    "/flood",
    "tutmaz",
    "kalıcı ralli",
    "faiz",
    "emtia",
    "Çin",
    "Avrupa",
    "Trump",
    "Fed",
]


def public_rows() -> list[dict]:
    out = []
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        if o.get("locked"):
            continue
        t = (o.get("text") or "").strip()
        if not t or t == "[erişilemedi]":
            continue
        out.append(o)
    return out


def build_block(rows: list[dict]) -> str:
    tags: Counter[str] = Counter()
    phrases: Counter[str] = Counter()
    lengths: list[int] = []
    flood_n = 0
    hatirlatma = 0
    for o in rows:
        text = o.get("text") or ""
        lengths.append(len(text))
        for h in HASHTAG_RX.findall(text):
            tags[h.lower()] += 1
        for p in PHRASE_KEYS:
            if p.lower() in text.lower():
                phrases[p] += 1
        if re.search(r"#FLOOD|/flood", text, re.I):
            flood_n += 1
        if re.search(r"demiştim|hatırlayın|söylemiştim", text, re.I) and len(text) < 220:
            hatirlatma += 1

    avg_len = sum(lengths) // max(len(lengths), 1)
    top_tags = tags.most_common(18)
    top_phr = phrases.most_common(12)

    lines = [
        MARKER,
        "",
        f"- **Public tweet sayisi (analiz):** {len(rows)}",
        f"- **Ortalama metin uzunlugu:** ~{avg_len} karakter",
        f"- **#FLOOD / flood:** {flood_n} tweet",
        f"- **Kisa hatirlatma / demiştim tonu:** ~{hatirlatma}",
        "",
        "### Sik hashtagler",
    ]
    for tag, n in top_tags:
        lines.append(f"- {tag}: {n}")
    lines.extend(["", "### Tekrar eden kavramlar / ifadeler"])
    for p, n in top_phr:
        if n:
            lines.append(f"- «{p}»: {n}")
    lines.extend(
        [
            "",
            "### Ton (Claude icin)",
            "- Makro-politik zamanlama; teknik detay az, cerceve ve yon agirlikli.",
            "- «Zaman geciriyorlar / oyaliyorlar» ana cerceve; kalici ralli suphesi.",
            "- Dar seviye iddiasi genelde publicte sinirli; grafikte cizgi/seviye varsa oradan oku.",
            "- Alinti = gecmis tahminin gunu; sonradan alinti basari sayilmaz.",
            "",
        ]
    )
    return "\n".join(lines)


def inject(md: str, block: str) -> str:
    if MARKER in md:
        return re.sub(
            rf"{re.escape(MARKER)}.*?(?=\n## 5\.|\n---\n\n## 5\.)",
            block,
            md,
            count=1,
            flags=re.DOTALL,
        )
    anchor = "## 5. ÜRÜN BAZLI KANIT DEFTERİ"
    if anchor in md:
        return md.replace(anchor, block + anchor, 1)
    return md + "\n\n" + block


def main() -> int:
    rows = public_rows()
    block = build_block(rows)
    if HAFIZA.exists():
        md = HAFIZA.read_text(encoding="utf-8")
        HAFIZA.write_text(inject(md, block), encoding="utf-8")
        print(f"Koç dili guncellendi: {len(rows)} public tweet")
    else:
        print("Hafiza yok — once tweet_tara --jsonl-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
