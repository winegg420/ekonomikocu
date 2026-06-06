#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oncelik 1 — kaynak etiketleme.
Girdi: 04_TWEETLER.jsonl, 07_ABONE_TWEETLER.jsonl
Cikti: *_v2.jsonl, kaynak_raporu.md
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from enrichment.common import LOG, ROOT, iter_jsonl, setup_log, write_jsonl

# --- Metin imza kurallari (oncelik sirasi: spesifik -> genel) ---
IMZA_KURALLARI: list[tuple[str, re.Pattern[str]]] = [
    ("alinti:dd_finance", re.compile(r"dd_finance|dd_finance/status", re.I)),
    ("alinti:cowen", re.compile(
        r"cowen'?a\s+gore|benjamin\s+cowen|cowren\s+yayin|cowen\s+.*video|"
        r"videodaki\s+en\s+onemli|yeni\s+ozet.*cowen|birbenjamin\s+cowren",
        re.I,
    )),
    ("alinti:green", re.compile(
        r"@green\b|greenwood|ascensionun\s+bindiren\s+greenwood",
        re.I,
    )),
    ("alinti:saylor", re.compile(
        r"^saylor\s*$|asla\s+btc\s+satmam\s+diyen\s+saylor|"
        r"takip\s+etmeniz\s+gereken.*strategy\s*\(saylor\)",
        re.I,
    )),
    ("alinti:raoul", re.compile(r"\braoul\b|raoul\s+pal", re.I)),
    ("alinti:pentoshi", re.compile(r"pentoshi", re.I)),
    ("alinti:trump", re.compile(
        r"@realdonaldtrump|"
        r"(?:^|\n)\s*trump\s*:\s*[\"']|"
        r"muhabir\s*:.*\n\s*trump\s*:|"
        r"donald\s+trump\s*:\s*",
        re.I | re.M,
    )),
]

UCUNCU_SAHIS = re.compile(
    r"videosuna\s+gore|ozet\s+\d|yayinina\s+gore|dedi\s+ki|yazdi\s+ki|"
    r"aktardi|paylasti|retweet|rt\s+@|x\.com/(?!ekonomikocu)[\w]+/status",
    re.I,
)

BIRINCI_SAHIS = re.compile(
    r"\b(ben|biz|bana\s+gore|bekliyorum|dusunuyorum|diyorum|dedik|"
    r"yazdim|soyledim|goruyorum|izliyorum)\b",
    re.I,
)

KOÇ_YORUM_TRUMP = re.compile(
    r"trump\s*,|trump\s+kanal|trump\s+gelene|trump\s+da\s+|trump\s+in\s+|"
    r"trump\s+faiz|trump\s+baris|trump\s+oturdu|trump\s+muhtemelen|"
    r"trump\s+bu\s+sefer|trump\s+dunya|trump\s+koltuk|#trump\b",
    re.I,
)


def _tip_list(row: dict) -> list[str]:
    t = row.get("tip") or []
    if isinstance(t, str):
        return [t]
    return list(t)


def _metin_imzasi(text: str) -> str | None:
    for kaynak, rx in IMZA_KURALLARI:
        if rx.search(text):
            return kaynak
    return None


def _trump_alinti_mi(text: str) -> bool:
    """Koç'un Trump'i aktardigi (sozlu alinti) vs Koç'un Trump yorumu."""
    if re.search(r"(?:^|\n)\s*trump\s*:\s*", text, re.I | re.M):
        return True
    if re.search(r"muhabir\s*:.*trump\s*:", text, re.I | re.S):
        return True
    if "@realdonaldtrump" in text.lower():
        return True
    if KOÇ_YORUM_TRUMP.search(text):
        return False
    return False


def classify_kaynak(row: dict) -> str:
    text = (row.get("text") or "").strip()
    baglanti = (row.get("baglanti") or "").strip()
    kayit = (row.get("kayit_tipi") or "").strip().lower()

    # Yabanci konusma parcasi
    if "alinti-flood" in baglanti and "eko" not in baglanti.lower():
        if "alinti-flood-eko" not in (row.get("role") or ""):
            pass
    if kayit and "foreign" in kayit:
        return "belirsiz"

    imza = _metin_imzasi(text)
    if imza:
        if imza == "alinti:trump" and not _trump_alinti_mi(text):
            if KOÇ_YORUM_TRUMP.search(text):
                return "koc"
        return imza

    # dd_finance: trader gunlugu yapisi (Ingilizce, Basarilar.)
    if re.search(r"0\.\d+R\s+ile\s+stop|basarilar\.?\s*$", text, re.I):
        if "dd_finance" in text.lower() or re.search(r"x\.com/\w+/status", text, re.I):
            return "alinti:dd_finance"

    # Cowen ozeti — ucuncu sahis + cowen
    if re.search(r"cowen", text, re.I) and UCUNCU_SAHIS.search(text):
        return "alinti:cowen"
    if re.search(r"cowen'?a\s+gore", text, re.I):
        return "alinti:cowen"

    # is_quote: Koç'un gecmis kendi tweeti (icerik Koç'a ait)
    if row.get("is_quote"):
        if row.get("quote_stub") and not text:
            return "belirsiz"
        # Baskasinin sozu gibi gorunmuyorsa Koç'un eski tweeti
        if _metin_imzasi(text) is None and not UCUNCU_SAHIS.search(text):
            return "koc"
        if BIRINCI_SAHIS.search(text):
            return "koc"

    # Ucuncu sahis aktarim, zayif imza
    if UCUNCU_SAHIS.search(text) and not BIRINCI_SAHIS.search(text):
        return "belirsiz"

    # Birinci sahis / Koç tezi
    if BIRINCI_SAHIS.search(text):
        return "koc"

    # Varsayilan: Koç hesabindan, kendi sozu kabul (zayif sinyal)
    if text and not row.get("quote_stub"):
        return "koc"

    return "belirsiz"


def process_file(src: Path, dst: Path) -> tuple[int, Counter[str], int]:
    out_rows: list[dict] = []
    counts: Counter[str] = Counter()
    errors = 0
    n_in = 0

    for line_no, row in iter_jsonl(src):
        n_in += 1
        try:
            new_row = dict(row)
            new_row["kaynak"] = classify_kaynak(row)
            counts[new_row["kaynak"]] += 1
            out_rows.append(new_row)
        except Exception as e:
            errors += 1
            LOG.warning("Satir %d atlandi (%s): %s", line_no, src.name, e)

    write_jsonl(dst, out_rows)
    return n_in, counts, errors


def write_rapor(sections: list[tuple[str, int, Counter[str], int]]) -> None:
    lines = [
        "# Kaynak Raporu",
        "",
        "Otomatik etiketleme — `kaynak_etiketle.py`",
        "",
    ]
    for label, n_in, counts, errors in sections:
        lines.append(f"## {label}")
        lines.append("")
        lines.append(f"- Giris satiri: **{n_in}**")
        lines.append(f"- Cikis satiri: **{sum(counts.values())}**")
        if errors:
            lines.append(f"- Hatali/atlanan: **{errors}**")
        lines.append("")
        koc = counts.get("koc", 0)
        belirsiz = counts.get("belirsiz", 0)
        alinti = sum(v for k, v in counts.items() if k.startswith("alinti:"))
        lines.append(f"| Kategori | Adet |")
        lines.append(f"|----------|------|")
        lines.append(f"| koc | {koc} |")
        lines.append(f"| alinti (toplam) | {alinti} |")
        lines.append(f"| belirsiz | {belirsiz} |")
        lines.append("")
        for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            if k not in ("koc", "belirsiz"):
                lines.append(f"- `{k}`: {v}")
        lines.append("")

    (ROOT / "kaynak_raporu.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    setup_log("kaynak_etiketle")
    pairs = [
        (ROOT / "04_TWEETLER.jsonl", ROOT / "04_TWEETLER_v2.jsonl", "04_TWEETLER_v2"),
        (ROOT / "07_ABONE_TWEETLER.jsonl", ROOT / "07_ABONE_TWEETLER_v2.jsonl", "07_ABONE_v2"),
    ]
    sections = []
    for src, dst, label in pairs:
        if not src.is_file():
            LOG.warning("Dosya yok, bos cikti: %s", src)
            write_jsonl(dst, [])
            sections.append((label, 0, Counter(), 0))
            continue
        n_in, counts, err = process_file(src, dst)
        LOG.info("%s -> %s | %d kayit | koc=%d alinti=%d belirsiz=%d",
                 src.name, dst.name, n_in,
                 counts.get("koc", 0),
                 sum(v for k, v in counts.items() if k.startswith("alinti:")),
                 counts.get("belirsiz", 0))
        sections.append((label, n_in, counts, err))

    write_rapor(sections)
    print(f"Tamam: kaynak_raporu.md", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
