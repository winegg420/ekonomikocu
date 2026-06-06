#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oncelik 2 — cagri cikarimi.
Girdi: 04_TWEETLER_v2.jsonl (yoksa 04_TWEETLER.jsonl)
Cikti: cagrilar.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from enrichment.common import LOG, ROOT, read_jsonl, setup_log, write_jsonl

# Fiyat yakalama
K_RX = re.compile(
    r"(?<!\d)(?:\$|#)?\s*(\d{1,3}(?:[.,]\d{1,3})?)\s*[Kk]\b|"
    r"\$\s*(\d{1,3}(?:[.,]\d{3})*(?:\.\d+)?)|"
    r"(?<!\d)(\d{2,3})[.,](\d{3})\s*(?:usd|dolar)?|"
    r"(?<!\d)(\d{4,6})(?!\d)",
    re.I,
)

YUKARI_RX = re.compile(
    r"yukari|yuksel|tepe\s+ol|zirve|hedef\s+\d|ustu|ustunde|break\s+out|"
    r"long\b|alim\b|pump",
    re.I,
)
ASAGI_RX = re.compile(
    r"asagi|dus|dip\b|tepe\s+olmas|sat\b|short\b|cakil|50\s*k\s+alt|"
    r"exit\s+rally|dusus|bear",
    re.I,
)

VADE_HAFTA = re.compile(r"(\d+)\s*hafta", re.I)
VADE_AY = re.compile(
    r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s*(ocak|subat|mart|nisan|mayis|mayıs|haziran|"
    r"temmuz|agustos|ağustos|eylul|eylül|ekim|kasim|kasım|aralik|aralık)|"
    r"(ocak|subat|mart|nisan|mayis|mayıs|haziran|temmuz|agustos|ağustos|eylul|"
    r"eylül|ekim|kasim|kasım|aralik|aralık)\s+(\d{4})|"
    r"q([1-4])\s+(\d{4})?",
    re.I,
)

AY_MAP = {
    "ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "mayıs": 5,
    "haziran": 6, "temmuz": 7, "agustos": 8, "ağustos": 8, "eylul": 9, "eylül": 9,
    "ekim": 10, "kasim": 11, "kasım": 11, "aralik": 12, "aralık": 12,
}


def _tip_has_seviye(row: dict) -> bool:
    tips = row.get("tip") or []
    if isinstance(tips, str):
        tips = [tips]
    return "seviye" in tips


def _normalize_number(raw: str, k_suffix: bool = False) -> int | None:
    s = raw.replace(",", ".").strip()
    try:
        if k_suffix or re.search(r"[Kk]$", raw):
            val = float(re.sub(r"[Kk]$", "", s))
            return int(val * 1000)
        if "." in s:
            parts = s.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                return int(parts[0] + parts[1])
            return int(float(s))
        return int(float(s))
    except ValueError:
        return None


def extract_levels(text: str) -> list[int]:
    levels: list[int] = []
    seen: set[int] = set()

    # Aralik: $124-128K
    for m in re.finditer(
        r"\$?\s*(\d{2,3})\s*[-–]\s*(\d{2,3})\s*[Kk]", text, re.I
    ):
        for g in m.groups():
            v = _normalize_number(g + "K", k_suffix=True)
            if v and 1000 <= v <= 2_000_000 and v not in seen:
                seen.add(v)
                levels.append(v)

    for m in K_RX.finditer(text):
        g = m.groups()
        val: int | None = None
        if g[0]:
            val = _normalize_number(g[0] + "K", k_suffix=True)
        elif g[1]:
            val = _normalize_number(g[1])
        elif g[2] and g[3]:
            val = int(g[2] + g[3])
        elif g[4] if len(g) > 4 else None:
            pass
        # son grup tek sayi
        full = m.group(0)
        if val is None:
            nums = re.findall(r"\d+", full.replace(",", "").replace(".", ""))
            if nums:
                try:
                    val = int("".join(nums))
                except ValueError:
                    val = None
        # Yil rakamlarini fiyat sanma (2024-2032)
        if val and 2018 <= val <= 2035:
            continue
        if val and 500 <= val <= 2_000_000 and val not in seen:
            seen.add(val)
            levels.append(val)

    # 60 K ozel
    for m in re.finditer(r"(?<!\d)(\d{1,3})\s*[Kk]\b", text):
        v = _normalize_number(m.group(1) + "K", k_suffix=True)
        if v and v not in seen:
            seen.add(v)
            levels.append(v)

    return sorted(levels)


def infer_yon(text: str) -> str:
    up = bool(YUKARI_RX.search(text))
    down = bool(ASAGI_RX.search(text))
    if up and not down:
        return "yukari"
    if down and not up:
        return "asagi"
    if up and down:
        # tepe beklentisi + dusus hedefi
        if re.search(r"tepe\s+ol", text, re.I) and re.search(r"50\s*[Kk]\s+alt", text, re.I):
            return "asagi"
        return "belirsiz"
    return "belirsiz"


def parse_vade(text: str, base_dt: str | None) -> str | None:
    if not base_dt:
        return None
    try:
        base = datetime.fromisoformat(base_dt.replace("Z", "+00:00")[:19])
    except ValueError:
        return None

    m = VADE_HAFTA.search(text)
    if m:
        weeks = int(m.group(1))
        return (base + timedelta(weeks=weeks)).strftime("%Y-%m-%d")

    m = VADE_AY.search(text)
    if m:
        gs = m.groups()
        if gs[0] and gs[1] and gs[2]:
            ay = AY_MAP.get(gs[2].lower())
            if ay:
                d1, d2 = int(gs[0]), int(gs[1])
                y = base.year
                if ay < base.month:
                    y += 1
                return f"{y}-{ay:02d}-{d2:02d}"
        if gs[3] and gs[4]:
            ay = AY_MAP.get(gs[3].lower())
            y = int(gs[4]) if gs[4] else base.year
            if ay:
                return f"{y}-{ay:02d}-15"

    if re.search(r"2026\s+ikinci\s+yar", text, re.I):
        return "2026-09-01"
    if re.search(r"q4|4\.\s*ceyrek", text, re.I):
        y = base.year
        return f"{y}-10-15"

    return None


def row_to_cagri(row: dict) -> dict | None:
    text = (row.get("text") or "").strip()
    if not text:
        return None
    if not _tip_has_seviye(row):
        return None
    levels = extract_levels(text)
    if not levels:
        return None

    dt = (row.get("datetime") or "")[:10]
    products = row.get("products") or []
    if isinstance(products, str):
        products = [products]

    return {
        "tweet_id": row.get("tweet_id"),
        "tarih": dt,
        "urun": products,
        "seviyeler": levels,
        "yon": infer_yon(text),
        "vade_tarihi": parse_vade(text, row.get("datetime")),
        "kaynak": row.get("kaynak", "belirsiz"),
        "metin": text,
        "fiyat_dogrulama": "BEKLIYOR",
    }


def main() -> int:
    setup_log("cagri_cikar")
    src = ROOT / "04_TWEETLER_v2.jsonl"
    if not src.is_file():
        src = ROOT / "04_TWEETLER.jsonl"
        LOG.warning("v2 yok, orijinal kullaniliyor: %s", src.name)

    rows = read_jsonl(src)
    cagrilar: list[dict] = []
    for row in rows:
        try:
            c = row_to_cagri(row)
            if c:
                cagrilar.append(c)
        except Exception as e:
            LOG.warning("Cagri atlandi %s: %s", row.get("tweet_id"), e)

    out = ROOT / "cagrilar.jsonl"
    write_jsonl(out, cagrilar)
    LOG.info("cagrilar.jsonl: %d cagri", len(cagrilar))

    # Kabul kriteri log
    for tid in ("1960756838129131731", "2063250939578863720"):
        hit = next((c for c in cagrilar if c.get("tweet_id") == tid), None)
        if hit:
            LOG.info("ORNEK %s: sev=%s yon=%s vade=%s", tid, hit["seviyeler"], hit["yon"], hit["vade_tarihi"])
        else:
            LOG.warning("ORNEK bulunamadi: %s", tid)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
