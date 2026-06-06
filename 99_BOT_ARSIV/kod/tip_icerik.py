#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
İçerik tipi: vizyon | seviye | tarih | tez | yorum (çoklu etiket, öncelik sırası).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from hafiza_guncelle import (
    FLOOD_MARKERS,
    PRODUCT_RULES,
    TweetRecord,
    classify_products,
    classify_tip,
    detect_lang,
    try_parse_date,
)


def format_date_label(dt: datetime | None) -> str:
    if not dt:
        return "tarih-belirsiz"
    tr_months = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    mon = tr_months[dt.month - 1]
    return f"{dt.day} {mon} {dt.hour:02d}:{dt.minute:02d}"

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"
VIZYON_SEVIYE_OUT = ROOT / "vizyon_seviye.jsonl"
ERISILEMEDI = "[erişilemedi]"

TIP_ORDER = ["vizyon", "seviye", "tarih", "tez", "yorum"]

VIZYON_RX = re.compile(
    r"görecek|gorecek|görür|gorur|gorecegi|göreceği|gelecek|gider|yapar|ulaşır|ulasir|"
    r"bitmedi|bitti|biter|ölmedi|olmedi|zirve|\bath\b|yeni\s+tepe|"
    r"\bdip\b|\btaban\b|\btavan\b|patlar|uçar|ucar|çakılır|cakilir|toparlar|döner|doner|"
    r"ulaşacak|ulasacak|gidecek|yapacak",
    re.I,
)

TEZ_RX = re.compile(
    r"zaman\s*geçir|oyala|oyalama|\bemtia\b|#emtia|çin\b|cin\b|avrupa|"
    r"\bfaiz\b|vade\s*doldur|\bvade\b|fed\b|trump|biden",
    re.I,
)

TARIH_RX = re.compile(
    r"temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik|"
    r"ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|"
    r"\d+\s*gün|\d+\s*gun|ay\s+sonu|hafta\s*\d|haftası|"
    r"\d{1,2}\s*[-–]\s*\d{1,2}|"
    r"\d{1,2}\s+(?:Oca|Şub|Sub|Mar|Nis|May|Haz|Tem|Ağu|Agu|Eyl|Eki|Kas|Ara)\b|"
    r"(?:Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Eyl|Eki|Kas|Ara)\.?\s+\d{1,2}",
    re.I,
)

SEVIYE_NUM_RX = re.compile(
    r"(?:\$\s?[\d.,]{2,}|\b\d{2,3}[.,]\d{2,5}\b|\b\d{4,6}\b|\b\d{2,3}K\b|\b\d{1,3}\s*(?:bin|k)\b)",
    re.I,
)

# Ürün yakınlığı (seviye/vizyon bağlamı)
URUN_RX: list[tuple[str, re.Pattern[str]]] = [
    ("BTC", re.compile(r"#?btc|bitcoin|kobeissi", re.I)),
    ("ETH", re.compile(r"#?eth|ethereum", re.I)),
    ("ALTIN", re.compile(r"#?altın|#?altin|\baltın\b|\baltin\b|gold", re.I)),
    ("GUMUS", re.compile(r"#?gümüş|#?gumus|silver", re.I)),
    ("PETROL", re.compile(r"#?petrol|#?oil|crude|brent", re.I)),
    ("DOW", re.compile(r"\bdow\b|djia|nasdaq", re.I)),
    ("BIST", re.compile(r"#?bist|xu100|borsa\s+istanbul", re.I)),
    ("EURUSD", re.compile(r"eurusd|eur/usd|euro", re.I)),
    ("GUMUS_PETROL", re.compile(r"#?emtia|emtia|enflasyon|dolar", re.I)),
]

# hafiza_guncelle anahtarları -> çıktı etiketi
URUN_LABEL = {
    "BTC": "BTC",
    "ETH": "ETH",
    "ALTIN": "ALTIN",
    "GUMUS": "GUMUS",
    "GUMUS_PETROL": "GUMUS",
    "GUMUS_120": "GUMUS",
    "PETROL": "PETROL",
    "DOW": "DOW",
    "BIST": "BIST",
    "EURUSD": "EURUSD",
    "GENEL": "GENEL",
}


def _sort_tips(tips: list[str]) -> list[str]:
    order = {t: i for i, t in enumerate(TIP_ORDER)}
    seen: set[str] = set()
    out: list[str] = []
    for t in TIP_ORDER:
        if t in tips and t not in seen:
            seen.add(t)
            out.append(t)
    return out or ["yorum"]


def _has_seviye(text: str) -> bool:
    if not SEVIYE_NUM_RX.search(text):
        return False
    for key, rx in URUN_RX:
        if rx.search(text):
            return True
    if re.search(r"seviye|hedef|destek|direnç|direnc|fibonacci|\bfib\b|\$", text, re.I):
        return True
    return bool(re.search(r"#\w+.{0,40}\d{2,}|\d{2,}.{0,40}#\w+", text, re.I))


def classify_icerik_tips(text: str, *, locked: bool = False) -> list[str]:
    t = (text or "").strip()
    if locked or not t or t == ERISILEMEDI:
        return ["yorum"]

    tips: list[str] = []
    if VIZYON_RX.search(t):
        tips.append("vizyon")
    if _has_seviye(t):
        tips.append("seviye")
    if TARIH_RX.search(t):
        tips.append("tarih")
    if TEZ_RX.search(t):
        tips.append("tez")
    if not tips:
        tips.append("yorum")
    return _sort_tips(tips)


def detect_products_rich(text: str) -> list[str]:
    found: list[str] = []
    for key, rx in URUN_RX:
        if rx.search(text):
            lab = URUN_LABEL.get(key, key)
            if lab not in found:
                found.append(lab)
    if not found:
        for key, rx in PRODUCT_RULES:
            if rx.search(text):
                lab = URUN_LABEL.get(key, key)
                if lab not in found:
                    found.append(lab)
    return found or ["GENEL"]


def refine_products_for_tips(
    text: str, products: list[str], tips: list[str]
) -> list[str]:
    """Seviye/vizyon: metinde geçen ürün(ler) öncelikli."""
    if "vizyon" not in tips and "seviye" not in tips:
        return products
    rich = detect_products_rich(text)
    if rich and rich != ["GENEL"]:
        return rich
    return products


def kayit_tipi_for(
    text: str, locked: bool, is_quote: bool, quoted_by: str | None, thread_root: str | None, tid: str
) -> str:
    if is_quote and quoted_by:
        return "asıl (alıntı — ayrı satır)"
    if thread_root and thread_root != tid:
        return "flood" if FLOOD_MARKERS.search(text) else "flood-parça"
    if thread_root == tid and FLOOD_MARKERS.search(text):
        return "flood"
    return classify_tip(text, locked, is_quote)


HAFIZA_PRODUCT_MAP = {
    "GUMUS": "GUMUS_PETROL",
    "ALTIN": "GUMUS_PETROL",
    "PETROL": "GUMUS_PETROL",
    "ETH": "GENEL",
    "DOW": "GENEL",
    "BIST": "GENEL",
    "EURUSD": "GENEL",
}


def products_for_jsonl(text: str, tips: list[str]) -> list[str]:
    """JSONL/vizyon_seviye: okunur etiketler (BTC, GUMUS, ALTIN…)."""
    return refine_products_for_tips(text, detect_products_rich(text), tips)


def products_for_hafiza(products: list[str]) -> list[str]:
    out: list[str] = []
    for p in products:
        key = HAFIZA_PRODUCT_MAP.get(p, p)
        if key not in out:
            out.append(key)
    return out or ["GENEL"]


def apply_to_record(rec: TweetRecord) -> None:
    rec.icerik_tip = classify_icerik_tips(rec.text, locked=rec.locked)
    rich = products_for_jsonl(rec.text or "", rec.icerik_tip)
    rec.products = products_for_hafiza(rich)


def record_from_json_obj(o: dict) -> TweetRecord:
    text = (o.get("text") or "").strip()
    locked = bool(o.get("locked"))
    is_quote = bool(o.get("is_quote"))
    tid = o.get("tweet_id")
    dt_s = o.get("datetime")
    dt, _ = try_parse_date(dt_s) if isinstance(dt_s, str) else (None, "")
    if dt is None and dt_s:
        try:
            dt = datetime.fromisoformat(str(dt_s).replace("Z", "+00:00"))
        except Exception:
            pass

    raw_tip = o.get("tip")
    if isinstance(raw_tip, list):
        icerik_tip = _sort_tips([str(x) for x in raw_tip if x])
    elif isinstance(raw_tip, str) and raw_tip in TIP_ORDER:
        icerik_tip = [raw_tip]
    else:
        icerik_tip = classify_icerik_tips(text, locked=locked)

    kayit_tipi = o.get("kayit_tipi")
    if not kayit_tipi:
        if isinstance(raw_tip, str) and raw_tip not in TIP_ORDER:
            kayit_tipi = raw_tip
        else:
            kayit_tipi = kayit_tipi_for(
                text,
                locked,
                is_quote,
                o.get("quoted_by"),
                o.get("thread_root"),
                tid,
            )

    raw_products = o.get("products") or classify_products(text)
    jsonl_products = products_for_jsonl(text, icerik_tip)
    if raw_products and raw_products != ["GENEL"]:
        jsonl_products = list(dict.fromkeys(raw_products + jsonl_products))
    products = products_for_hafiza(jsonl_products)

    lang = o.get("lang") or detect_lang(text)
    if lang == "en" and re.search(r"[ğıüşöçİĞÜŞÖÇ]", text):
        lang = "tr"

    rec = TweetRecord(
        tweet_id=tid,
        dt=dt,
        date_label=o.get("date_label") or format_date_label(dt),
        locked=locked,
        text=text,
        products=products,
        tip=kayit_tipi,
        icerik_tip=icerik_tip,
        is_quote=is_quote,
        quoted_by=o.get("quoted_by"),
        quote_of=o.get("quote_of"),
        thread_root=o.get("thread_root"),
        lang=lang,
        analyzed=bool(o.get("analyzed")),
        fiyat=o.get("fiyat") or "—",
        sonra=o.get("sonra") or "—",
        sonuc=o.get("sonuc") or "",
        baglanti=o.get("baglanti") or "",
        media_urls=o.get("media_urls") or [],
        media_files=o.get("media_files") or [],
    )
    return rec


def json_obj_from_record(rec: TweetRecord) -> dict:
    jsonl_products = products_for_jsonl(rec.text or "", rec.icerik_tip or [])
    return {
        "tweet_id": rec.tweet_id,
        "datetime": rec.dt.isoformat() if rec.dt else None,
        "date_label": rec.date_label,
        "locked": rec.locked,
        "text": rec.text,
        "products": jsonl_products,
        "tip": rec.icerik_tip or ["yorum"],
        "kayit_tipi": rec.tip or "yorum",
        "lang": rec.lang,
        "analyzed": rec.analyzed,
        "is_quote": rec.is_quote,
        "quoted_by": rec.quoted_by,
        "quote_of": rec.quote_of,
        "quote_stub": False,
        "thread_root": rec.thread_root,
        "fiyat": rec.fiyat,
        "sonra": rec.sonra,
        "sonuc": rec.sonuc,
        "baglanti": rec.baglanti,
        "media_urls": rec.media_urls,
        "media_files": rec.media_files,
    }


def write_vizyon_seviye(records: list[TweetRecord], path: Path = VIZYON_SEVIYE_OUT) -> int:
    lines: list[str] = []
    for rec in records:
        tips = rec.icerik_tip or []
        if not any(t in tips for t in ("vizyon", "seviye")):
            continue
        if rec.locked and not (rec.text or "").strip():
            continue
        t = (rec.text or "").strip()
        if not t or t == ERISILEMEDI:
            continue
        row = {
            "tweet_id": rec.tweet_id,
            "datetime": rec.dt.isoformat() if rec.dt else None,
            "date_label": rec.date_label,
            "products": products_for_jsonl(rec.text or "", tips),
            "tip": [x for x in tips if x in ("vizyon", "seviye")],
            "text": rec.text,
            "is_quote": rec.is_quote,
            "quoted_by": rec.quoted_by,
            "media_files": rec.media_files,
        }
        lines.append(json.dumps(row, ensure_ascii=False))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def relabel_all_jsonl(path: Path = JSONL) -> list[TweetRecord]:
    if not path.exists():
        return []
    records: list[TweetRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = record_from_json_obj(json.loads(line))
        apply_to_record(rec)
        records.append(rec)
    records.sort(key=lambda r: r.sort_key(), reverse=True)
    ordered = [json_obj_from_record(r) for r in records]
    path.write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in ordered) + "\n",
        encoding="utf-8",
    )
    n_vs = write_vizyon_seviye(records)
    print(f"JSONL guncellendi: {len(records)} kayit | vizyon_seviye.jsonl: {n_vs}")
    return records


def main() -> int:
    records = relabel_all_jsonl()
    if not records:
        print(f"Yok: {JSONL}")
        return 1
    from collections import Counter

    c = Counter()
    for r in records:
        for t in r.icerik_tip or []:
            c[t] += 1
    print("Icerik tip dagilimi:", dict(c))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
