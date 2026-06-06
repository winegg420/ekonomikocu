#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025 yili tarama kapsami — %100 hedefi (ana tweet + abone + alinti + #FLOOD).
Cikti: tara_2025.json + TARAMA_2025.md (kok klasor)
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

YIL = "2025"
ERISILEMEDI = "[erişilemedi]"

try:
    from tara_ilerle import skipped_ids as _skipped_ids
except ImportError:
    def _skipped_ids(reason: str | None = None) -> set[str]:
        return set()


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
JSONL = ROOT / "cekilen_tweetler.jsonl"
ALINTI_BEK = ROOT / "99_BOT_ARSIV/kod/alinti_bekleyen.jsonl"
if not ALINTI_BEK.is_file():
    ALINTI_BEK = ROOT / "alinti_bekleyen.jsonl"
OUT_JSON = ROOT / "tara_2025.json"
OUT_MD = ROOT / "TARAMA_2025.md"


def _has_text(r: dict) -> bool:
    t = (r.get("text") or "").strip()
    return bool(t) and t != ERISILEMEDI


def _is_yil(r: dict, yil: str = YIL) -> bool:
    return (r.get("datetime") or "").startswith(yil)


def _pct(ok: int, total: int) -> float:
    return round(100.0 * ok / total, 1) if total else 100.0


def _quote_incomplete(r: dict) -> bool:
    if not r.get("is_quote"):
        return False
    if r.get("locked"):
        return False
    t = (r.get("text") or "").strip()
    if t == ERISILEMEDI:
        return False
    if not t:
        return True
    if (r.get("media_files") or r.get("media_urls")) and len(t) >= 25:
        return False
    if r.get("quote_stub"):
        return True
    if len(t) < 80 and ("…" in t or "..." in t):
        return True
    return False


def analyze() -> dict:
    rows = []
    if JSONL.is_file():
        rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]

    main = [r for r in rows if not r.get("is_quote")]
    quotes = [r for r in rows if r.get("is_quote")]

    main_yil = [r for r in main if _is_yil(r)]
    metinli = [r for r in main_yil if _has_text(r) and not r.get("locked")]
    bos = [r for r in main_yil if r.get("locked") and not _has_text(r)]
    erisilemedi_ana = [
        r
        for r in main_yil
        if (r.get("text") or "").strip() == ERISILEMEDI and not r.get("locked")
    ]

    ids_yil = {str(r.get("tweet_id")) for r in main_yil if r.get("tweet_id")}
    quotes_scope = [
        q
        for q in quotes
        if str(q.get("quoted_by") or "") in ids_yil
        or _is_yil(q)
    ]
    quotes_ok = [q for q in quotes_scope if not _quote_incomplete(q)]
    quotes_bad = [q for q in quotes_scope if _quote_incomplete(q)]

    parts_by_root: dict[str, int] = defaultdict(int)
    flood_roots: set[str] = set()
    for r in rows:
        if r.get("is_quote"):
            continue
        if not _is_yil(r):
            continue
        text = r.get("text") or ""
        tid = str(r.get("tweet_id") or "")
        root = str(r.get("thread_root") or r.get("threadRoot") or tid)
        if re.search(r"#FLOOD|/flood\b", text, re.I) and tid:
            flood_roots.add(tid)
        if root:
            parts_by_root[root] += 1

    flood_skipped = _skipped_ids("flood")
    flood_eksik = [
        rid
        for rid in flood_roots
        if parts_by_root.get(rid, 1) <= 1 and rid not in flood_skipped
    ]

    alinti_bek = 0
    if ALINTI_BEK.is_file():
        alinti_bek = sum(1 for l in ALINTI_BEK.read_text(encoding="utf-8").splitlines() if l.strip())

    ana_toplam = len(metinli) + len(bos) + len(erisilemedi_ana)
    ana_pct = _pct(len(metinli) + len(erisilemedi_ana), ana_toplam)
    alinti_pct = _pct(len(quotes_ok), len(quotes_scope))
    flood_pct = _pct(len(flood_roots) - len(flood_eksik), len(flood_roots))

    parcalar = [ana_pct]
    if quotes_scope:
        parcalar.append(alinti_pct)
    if flood_roots:
        parcalar.append(flood_pct)
    genel_pct = min(parcalar) if parcalar else 0.0

    by_month_m = Counter((r.get("datetime") or "")[:7] for r in metinli)
    by_month_b = Counter((r.get("datetime") or "")[:7] for r in bos)

    dts = [r["datetime"] for r in metinli if r.get("datetime")]
    en_yeni = max(dts, default="")[:10]

    tamam = (
        len(bos) == 0
        and len(quotes_bad) == 0
        and len(flood_eksik) == 0
        and alinti_bek == 0
        and genel_pct >= 100.0
    )

    return {
        "guncelleme": datetime.now().isoformat(timespec="seconds"),
        "yil": YIL,
        "genel_yuzde": genel_pct,
        "tamam": tamam,
        "en_yeni": en_yeni,
        "ana": {
            "metinli": len(metinli),
            "bos_kilitli": len(bos),
            "erisilemedi": len(erisilemedi_ana),
            "toplam": ana_toplam,
            "yuzde": ana_pct,
        },
        "alinti": {
            "kapsam": len(quotes_scope),
            "tam": len(quotes_ok),
            "eksik": len(quotes_bad),
            "yuzde": alinti_pct,
            "bekleyen_dosya": alinti_bek,
        },
        "flood": {
            "kok": len(flood_roots),
            "eksik_parcali": len(flood_eksik),
            "atlandi": len(flood_skipped & flood_roots),
            "yuzde": flood_pct,
            "eksik_kok_id": flood_eksik[:20],
        },
        "aylik": {
            mo: {"metinli": by_month_m[mo], "bos": by_month_b[mo]}
            for mo in sorted(set(by_month_m) | set(by_month_b))
        },
        "eksik_bos_id": [r.get("tweet_id") for r in bos[:30]],
        "eksik_alinti_id": [q.get("tweet_id") for q in quotes_bad[:30]],
    }


def render_md(s: dict) -> str:
    a, q, f = s["ana"], s["alinti"], s["flood"]
    tam = "EVET — 2025 %100" if s["tamam"] else "HAYIR — tarama devam"
    aylik = "\n".join(
        f"| {mo} | {v['metinli']} | {v['bos']} | "
        f"{_pct(v['metinli'], v['metinli'] + v['bos'])}% |"
        for mo, v in s.get("aylik", {}).items()
    )
    return f"""# TARAMA 2025 (@ekonomikocu)

**Guncelleme:** {s.get('guncelleme', '—')}

## Ozet

> **Genel tamamlanma: {s.get('genel_yuzde', 0)}%**
>
> Hedef: **2025 yilindaki TUM tweetler** + **abone metinleri** + **alintilanan gecmis tweetler** + **#FLOOD parcalari** → **%100**
>
> **Tamam mi?** {tam}

| Alan | Tam | Eksik | % |
|------|-----|-------|---|
| Ana tweet (2025) | {a['metinli']} | {a['bos_kilitli']} (+{a.get('erisilemedi', 0)} erisilemedi) | **{a['yuzde']}%** |
| Alinti (2025 kapsami) | {q['tam']} | {q['eksik']} | **{q['yuzde']}%** |
| #FLOOD kok (2025) | {f['kok'] - f['eksik_parcali']} | {f['eksik_parcali']} | **{f['yuzde']}%** |

**En yeni kayit:** {s.get('en_yeni', '—')}

## Aylik (2025)

| Ay | Metinli | Bos | % |
|----|---------|-----|---|
{aylik}

## Kural

Eksik kalmamali: ana metin, abone, alinti, alinti flood.

---
*Otomatik: kapsam_2025.py*
"""


def main() -> int:
    s = analyze()
    OUT_JSON.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_md(s), encoding="utf-8")
    text = OUT_MD.read_text(encoding="utf-8")
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))
    return 0 if s["tamam"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
