#!/usr/bin/env python3
"""
Claude-format analiz: alinti tarih baglantisi, #FLOOD thread, dar cagri, hafiza §5-§9.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime

from hafiza_guncelle import (
    FLOOD_MARKERS,
    TweetRecord,
    rebuild_hafiza_md,
    update_section_7_date,
    update_section_9,
)
from tweet_tara import JSONL_OUT, HAFIZA, load_jsonl, save_jsonl

TR_RESTORE: dict[str, str] = {
    "2062211573762932880": "Tamamen #piyasa odaklı ve realist yorumlar. Kimin işine gelir gelmez!",
    "2062211206312550626": "Avrupa'da savaşı bahane edip #EMTİA kozunu masaya vuran ÇİN... İsteyen buraya da giydirebilir.",
    "2062203055429288055": "Denklem basit. Avrupa barışa yanaşsa Çin emtia kartını kullanamaz, ABD'nin eli güçlenir.",
    "2062201246983823722": "Avr.pa yüzüne! ABD-ÇİN arasında #savaş geçmeye başladı. İş #emtia savaşına döndü.",
    "2062196770948436220": "Rusya-Ukrayna sürdükçe, Çin emtia kozunu tuttukça hiçbir şey kalıcı düzelmez.",
    "2061799520980148284": "Takvimleri var, ona göre gidiyorlar. #zaman geçirme tarzında ilerliyorlar.",
    "2061799073775063129": "Bu gidişle olmaz. #oyalama #zaman kazanma... Süreci yönetiyorlar.",
    "2061784198856249756": "7 Nisan günü dünyaya #barışı sattılar.",
    "2056426669221527765": "Trump döneminde: #BITCOIN 126K, #gümüş 121 USD, #petrol 120 USD.",
    "2051209147513782296": "80.600",
}

DAR_CALLS: dict[str, tuple[str, str, str]] = {
    "2061129198316421514": ("BTC ~80.600 (31 May)", "31 May + 4 May hattı ile aynı tez", "izleniyor"),
    "2051209147513782296": ("BTC 80.600 (4 May)", "31 May tweet ile bağlı", "izleniyor"),
    "2056426669221527765": ("BTC126K → gümüş121 → petrol120", "Trump dönemi sıra iddiası", "izleniyor"),
    "2061784198856249756": ("—", "7 Nisan barış satışı; 2 Haz alıntı bağlamı", "izleniyor"),
    "2061105043424563502": ("Nasdaq 29.700 üzeri", "31 May çağrısı", "izleniyor"),
}

DAR_RX = re.compile(
    r"80600|80\.?600|126\s*K|121\s*USD|120\s*#?usd|29700|29\.700|seviye|hedef|vade|Temmuz|Ağustos",
    re.I,
)
DEMISTIM_RX = re.compile(r"demiştim|söylemiştim|hatırlayın|unutmadık|bu analiz", re.I)
OYALAMA_RX = re.compile(r"zaman geçir|oyalama|vade doldur|takvim", re.I)


def apply_tr_restore(rec: TweetRecord) -> None:
    tid = rec.tweet_id or ""
    if tid in TR_RESTORE:
        rec.text = TR_RESTORE[tid]
        rec.lang = "tr"


def link_quote_timing(rec: TweetRecord, by_id: dict[str, TweetRecord]) -> None:
    if not rec.is_quote or not rec.quoted_by or not rec.dt:
        return
    main = by_id.get(rec.quoted_by)
    if not main or not main.dt:
        rec.baglanti = "alıntı — ana tweet tarihi eksik"
        return
    if rec.dt < main.dt:
        gun = (main.dt - rec.dt).days
        rec.baglanti = f"ÖNCEDEN söylenmiş ({gun} gün önce) — geçerli kanıt"
        if "önceden" not in (rec.tip or ""):
            rec.tip = (rec.tip or "alıntı") + " | önceden"
        rec.sonuc = "izleniyor" if DAR_RX.search(rec.text or "") else "yorum"
        rec.sonra = f"ana tweet {rec.quoted_by} ({main.date_label}) içinde alıntılandı"
    else:
        gun = (rec.dt - main.dt).days
        rec.baglanti = f"SONRADAN alıntı ({gun} gün sonra) — demiştim riski, başarı sayma"
        rec.tip = (rec.tip or "alıntı") + " | sonradan"
        rec.sonuc = "yorum"


def link_flood_threads(records: list[TweetRecord]) -> None:
    threads: dict[str, list[TweetRecord]] = defaultdict(list)
    for r in records:
        if r.thread_root:
            threads[r.thread_root].append(r)
    for root, parts in threads.items():
        parts.sort(key=lambda x: x.sort_key())
        ids = [p.tweet_id for p in parts if p.tweet_id]
        for i, p in enumerate(parts):
            if p.tweet_id == root:
                p.tip = "flood"
                p.sonra = f"thread {len(parts)} parça: " + ", ".join(ids[:8])
            else:
                p.tip = "flood-parça"
                p.sonra = f"parça {i + 1}/{len(parts)}, kök {root}"


def link_hatirlatma(rec: TweetRecord, by_id: dict[str, TweetRecord]) -> None:
    if rec.is_quote or rec.locked:
        return
    text = rec.text or ""
    if len(text) > 200 and not DEMISTIM_RX.search(text):
        return
    if DEMISTIM_RX.search(text) or (len(text) < 100 and re.search(r"#\d{4}|haziran|temmuz", text, re.I)):
        rec.tip = (rec.tip or "yorum") + " | hatırlatma"
        rec.sonuc = "yorum"
        rec.baglanti = (rec.baglanti or "") + " kısa vurgu / demiştim tonu"


def apply_dar_calls(rec: TweetRecord) -> None:
    tid = rec.tweet_id or ""
    if tid in DAR_CALLS:
        rec.fiyat, rec.sonra, rec.sonuc = DAR_CALLS[tid]
        rec.tip = "asıl tahmin"
        return
    if DAR_RX.search(rec.text or ""):
        rec.fiyat = "DOĞRULANACAK (web)"
        rec.sonuc = "izleniyor"
        if "asıl" not in (rec.tip or ""):
            rec.tip = "asıl tahmin"
    elif OYALAMA_RX.search(rec.text or ""):
        rec.sonuc = "izleniyor"
        rec.baglanti = (rec.baglanti or "oyalama/zaman geçirme tezi").strip()


def enrich_all(records: list[TweetRecord]) -> None:
    by_id = {r.tweet_id: r for r in records if r.tweet_id}
    for r in records:
        apply_tr_restore(r)
        if r.lang != "tr":
            r.sonuc = "CEVIRI_KIRLI — yeniden tara"
            continue
        if r.locked and not (r.text or "").strip():
            r.sonuc = "yorum"
            r.tip = "kilitli"
            r.baglanti = "eksik (abonelik) — seviye uydurma"
            r.analyzed = True
            continue
        link_quote_timing(r, by_id)
        link_hatirlatma(r, by_id)
        apply_dar_calls(r)
        if not r.sonuc:
            r.sonuc = "yorum"
        r.analyzed = True
    link_flood_threads(records)


def build_section_8(records: list[TweetRecord]) -> str:
    onceden = [r for r in records if "önceden" in (r.tip or "")]
    sonradan = [r for r in records if "sonradan" in (r.tip or "")]
    floods = {r.thread_root for r in records if r.thread_root}
    dar = [r for r in records if r.sonuc == "izleniyor" and DAR_RX.search(r.text or "")]
    lines = [
        "## 8. BAĞLANTI ÖZETİ (geçmiş ↔ güncel — otomatik)",
        f"- **Kayıt:** {len(records)} tweet | **Alıntı önceden:** {len(onceden)} | "
        f"**Alıntı sonradan (demiştim riski):** {len(sonradan)} | **#FLOOD kök:** {len(floods)} | "
        f"**Dar çağrı izleniyor:** {len(dar)}",
        "- **Kural:** Sonradan alıntı = başarı sayılmaz; önceden alıntı = geçerli kanıt; kilitli = uydurma yok.",
    ]
    for r in sorted(dar, key=lambda x: x.sort_key(), reverse=True)[:12]:
        lines.append(
            f"- `{r.tweet_id}` ({r.date_label}): {r.fiyat} — {r.sonra or '—'} [{r.sonuc}]"
        )
    for r in sonradan[:8]:
        lines.append(f"- SONRADAN `{r.tweet_id}` → ana `{r.quoted_by}` | {r.baglanti}")
    lines.append("")
    return "\n".join(lines) + "\n"


def inject_section_8(md: str, block: str) -> str:
    if "## 8. BAĞLANTI" in md:
        md = re.sub(r"## 8\. BAĞLANTI.*?(?=\n## 9\.|\n---\n\n## 9\.)", block, md, flags=re.DOTALL)
    else:
        md = md.replace("## 9. İLERLEME", block + "## 9. İLERLEME", 1)
    return md


def update_section_6_auto(md: str, records: list[TweetRecord]) -> str:
    en = sum(1 for r in records if r.lang == "en")
    sonradan = sum(1 for r in records if "sonradan" in (r.tip or ""))
    note = (
        f"\n- **Analiz motoru:** {len(records)} tweet; alıntı önceden/sonradan ayrımı; "
        f"#FLOOD thread bağları; dar çağrılar izleniyor. EN kirli: {en}. "
        f"Sonradan alıntı (risk): {sonradan}. Tuttu/tutmadı için web fiyat doğrulama gerekir.\n"
    )
    if "**Analiz motoru:**" in md:
        md = re.sub(r"\n- \*\*Analiz motoru:\*\*.*?(?=\n- \*\*Dürüstlük|\n- \*\*Cursor)", note, md, count=1, flags=re.DOTALL)
    else:
        md = md.replace("- **Dürüstlük:**", note + "- **Dürüstlük:**", 1)
    return md


def run_full_analysis(*, write_hafiza: bool = True) -> list[TweetRecord]:
    records = load_jsonl(JSONL_OUT)
    if not records:
        return []
    enrich_all(records)
    save_jsonl(records, JSONL_OUT)
    if not write_hafiza or not HAFIZA.exists():
        return records

    md = HAFIZA.read_text(encoding="utf-8")
    md = rebuild_hafiza_md(md, records)
    md = inject_section_8(md, build_section_8(records))
    md = update_section_6_auto(md, records)
    md = update_section_7_date(md)
    md = update_section_9(md, records, {})
    HAFIZA.write_text(md, encoding="utf-8")
    try:
        from dil_analiz import main as dil_main

        dil_main()
    except Exception as e:
        print(f"Dil analizi atlandi: {e}")
    return records


def main() -> None:
    records = run_full_analysis(write_hafiza=True)
    iz = sum(1 for r in records if r.sonuc == "izleniyor")
    sq = sum(1 for r in records if "sonradan" in (r.tip or ""))
    oq = sum(1 for r in records if "önceden" in (r.tip or ""))
    print(f"Analiz: {len(records)} | izleniyor: {iz} | alinti-onceden: {oq} | alinti-sonradan: {sq}")
    print(f"Guncellendi: {HAFIZA.name}, {JSONL_OUT.name}")


if __name__ == "__main__":
    main()
