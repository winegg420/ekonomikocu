#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tarama kapsami: gunumuzden gecmise hangi tarihe kadar eksiksiz kayit var?
Cikti: tara_kapsam.json + TARAMA_DURUMU.md (kok klasor)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HEDEF = "2025-01-01"  # bu tarihe kadar inilecek
ERISILEMEDI = "[erişilemedi]"


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    return up


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"
KAPSAM_JSON = ROOT / "tara_kapsam.json"
DURUM_MD = ROOT / "TARAMA_DURUMU.md"
ALINTI_BEK = ROOT / "99_BOT_ARSIV/kod/alinti_bekleyen.jsonl"
if not ALINTI_BEK.is_file():
    ALINTI_BEK = ROOT / "alinti_bekleyen.jsonl"


def _has_text(r: dict) -> bool:
    t = (r.get("text") or "").strip()
    return bool(t) and t != ERISILEMEDI


def _month_key(dt: str) -> str:
    return (dt or "")[:7]


def _parse_rows() -> list[dict]:
    if not JSONL.is_file():
        return []
    return [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]


def _flood_roots(rows: list[dict]) -> tuple[int, int]:
    """(flood_kok, eksik_parca tahmini)"""
    roots: set[str] = set()
    parts_by_root: dict[str, int] = defaultdict(int)
    for r in rows:
        if r.get("is_quote"):
            continue
        text = (r.get("text") or "")
        root = r.get("thread_root") or r.get("threadRoot")
        if re.search(r"#FLOOD|/flood\b", text, re.I):
            tid = r.get("tweet_id") or ""
            if tid:
                roots.add(tid)
        if root:
            parts_by_root[str(root)] += 1
    # Kok tweet #FLOOD iceriyorsa parca sayisi 1 ise eksik olabilir
    eksik = sum(1 for rid in roots if parts_by_root.get(rid, 1) <= 1)
    return len(roots), eksik


def _continuous_until(
    all_months: list[str],
    months_bad: set[str],
    by_month_main: Counter,
) -> str | None:
    """Takvim ayi ayi geriye — ilk sorunlu ayda dur."""
    last_ok: str | None = None
    for mo in all_months:
        if mo in months_bad:
            break
        if mo >= "2026-01" and by_month_main.get(mo, 0) == 0:
            break
        last_ok = mo
    return last_ok


def analyze(hedef: str = HEDEF) -> dict:
    rows = _parse_rows()
    main = [r for r in rows if not r.get("is_quote")]
    quotes = [r for r in rows if r.get("is_quote")]
    main_txt = [r for r in main if _has_text(r) and not r.get("locked")]
    bos = [r for r in main if r.get("locked") and not _has_text(r)]
    quotes_eksik = [r for r in quotes if not _has_text(r)]

    alinti_bek = 0
    if ALINTI_BEK.is_file():
        alinti_bek = sum(1 for l in ALINTI_BEK.read_text(encoding="utf-8").splitlines() if l.strip())

    flood_kok, flood_eksik = _flood_roots(rows)

    by_month_main = Counter(_month_key(r.get("datetime") or "") for r in main_txt)
    by_month_bos = Counter(_month_key(r.get("datetime") or "") for r in bos)

    dts = [r["datetime"] for r in main_txt if r.get("datetime")]
    en_yeni = max(dts, default="")[:10]
    en_eski = min(dts, default="")[:10]

    # Hedef araliktaki aylar (2025-01 .. simdi)
    now = datetime.now()
    hedef_m = hedef[:7]
    cur_m = now.strftime("%Y-%m")
    all_months: list[str] = []
    y, m = int(cur_m[:4]), int(cur_m[5:7])
    hy, hm = int(hedef_m[:4]), int(hedef_m[5:7])
    while (y, m) >= (hy, hm):
        all_months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1

    months_bad: set[str] = set()
    eksik_aylar: list[dict] = []
    for mo in all_months:
        cnt = by_month_main.get(mo, 0)
        bos_n = by_month_bos.get(mo, 0)
        sorun = []
        if mo >= "2026-01" and cnt == 0:
            sorun.append("0 tweet")
            months_bad.add(mo)
        if bos_n > 0:
            sorun.append(f"{bos_n} bos kilitli")
            months_bad.add(mo)
        if sorun:
            eksik_aylar.append({"ay": mo, "metinli": cnt, "bos": bos_n, "sorun": sorun})

    surekli = _continuous_until(all_months, months_bad, by_month_main)

    if surekli:
        surekli_label = (
            f"{en_yeni} - {surekli} sonuna kadar kesintisiz kayit VAR "
            f"(alt aylarda bosluk/sorun olabilir)"
        )
        tamam_kadar = f"{surekli}-sonu"
    else:
        surekli_label = "Henuz kesintisiz blok yok"
        tamam_kadar = en_eski or "—"

    abone = sum(1 for r in main_txt if r.get("abone_metin") or r.get("kayit_tipi") == "abone")

    return {
        "guncelleme": datetime.now().isoformat(timespec="seconds"),
        "hedef_tarih": hedef,
        "en_yeni": en_yeni,
        "en_eski_kayit": en_eski,
        "tamam_kadar": tamam_kadar,
        "surekli_ozet": surekli_label,
        "toplam_satir": len(rows),
        "ana_metinli": len(main_txt),
        "abone_metinli": abone,
        "bos_kilitli": len(bos),
        "alinti_toplam": len(quotes),
        "alinti_eksik": len(quotes_eksik),
        "alinti_bekleyen": alinti_bek,
        "flood_kok": flood_kok,
        "flood_eksik_tahmin": flood_eksik,
        "eksik_aylar": eksik_aylar[:24],
        "aylik_metinli": dict(sorted(by_month_main.items(), reverse=True)[:18]),
        "is_tamam": (
            len(bos) == 0
            and len(quotes_eksik) == 0
            and alinti_bek == 0
            and not any(e["ay"] == "2026-03" for e in eksik_aylar)
            and en_eski <= hedef
        ),
    }


def render_md(s: dict) -> str:
    eksik_lines = "\n".join(
        f"- **{e['ay']}**: {e['metinli']} metinli, {e['bos']} bos — {', '.join(e['sorun'])}"
        for e in s.get("eksik_aylar", [])
    ) or "- (yok)"

    aylik = "\n".join(
        f"| {m} | {n} |" for m, n in sorted(s.get("aylik_metinli", {}).items(), reverse=True)[:12]
    )

    tam = "EVET — hedefe ulasildi" if s.get("is_tamam") else "HAYIR — tarama devam etmeli"

    return f"""# TARAMA DURUMU (@ekonomikocu)

**Guncelleme:** {s.get('guncelleme', '—')}

## Ozet (Ida'ya)

> **{s.get('surekli_ozet', '—')}**
>
> Hedef: **{s.get('hedef_tarih', HEDEF)}**'e kadar tum tweet + alinti + #FLOOD
>
> **Tamam mi?** {tam}

| Metrik | Deger |
|--------|-------|
| En yeni kayit | **{s.get('en_yeni', '—')}** |
| En eski kayit (metinli) | **{s.get('en_eski_kayit', '—')}** |
| Surekli tamam kadar | **{s.get('tamam_kadar', '—')}** |
| Ana tweet (metinli) | **{s.get('ana_metinli', 0)}** |
| Abone (metinli) | **{s.get('abone_metinli', 0)}** |
| Bos / kilitli (eksik) | **{s.get('bos_kilitli', 0)}** |
| Alinti eksik | **{s.get('alinti_eksik', 0)}** (+ bekleyen dosya: {s.get('alinti_bekleyen', 0)}) |
| #FLOOD kok / eksik tahmin | **{s.get('flood_kok', 0)}** / **{s.get('flood_eksik_tahmin', 0)}** |

## Eksik aylar / sorunlu donemler

{eksik_lines}

## Son 12 ay (metinli ana tweet)

| Ay | Adet |
|----|------|
{aylik}

## Bot is akisi (hedef)

1. **Profil** — gunumuzden geriye kaydir (hedef: {s.get('hedef_tarih', HEDEF)})
2. **Alinti** — alintilanan gecmis tweetlerin metni
3. **#FLOOD** — thread parcalari
4. **Abone** — kilitli/bos metinleri doldur
5. Bu dosyayi guncelle: `python 99_BOT_ARSIV/kod/kapsam_durum.py`

Tek komut: `python 99_BOT_ARSIV/kod/tara_tam.py`

---
*Otomatik: kapsam_durum.py*
"""


def main() -> int:
    s = analyze()
    KAPSAM_JSON.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    DURUM_MD.write_text(render_md(s), encoding="utf-8")
    text = DURUM_MD.read_text(encoding="utf-8")
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))
    # 2026 ozet (ayri rapor)
    k2026 = KOD / "kapsam_2026.py"
    if k2026.is_file():
        subprocess.run([sys.executable, str(k2026)], cwd=ROOT, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
