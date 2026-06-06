#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude: 01 + 02 + 03 (metin) + 04 zip (grafikler — 03'ün devamı)."""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return here


ROOT = _project_root()
HAFIZA = ROOT / "ekonomikocu_hafiza_v1.md"
JSONL = ROOT / "cekilen_tweetler.jsonl"

# Kök klasörde alt alta — Explorer'da en üstte (00–06)
F0 = ROOT / "00_OKU_YUKLEME_SIRASI.txt"
F1 = ROOT / "01_BURADAN_BASLA.md"
F8 = ROOT / "02_MENTOR_REHBERI.md"
F2 = ROOT / "03_HAFIZA.md"
F3 = ROOT / "04_TWEETLER.jsonl"
ZIP04 = ROOT / "05_GRAFIKLER.zip"
F5 = ROOT / "06_ANALIZ.md"
F7_ABONE = ROOT / "07_ABONE_TWEETLER.jsonl"
# Gemini — kok klasorde (Cloud 01-07 ayni, sonra 08-10)
F8_GEMINI_TWEET = ROOT / "08_TWEETLER_GEMINI.md"
DIR09_GEMINI_GRAF = ROOT / "09_GRAFIKLER_GEMINI"
F10_ABONE_GEMINI = ROOT / "10_ABONE_TWEETLER_GEMINI.md"
STAGING = ROOT / "99_BOT_ARSIV/_claude_zip_build"
ARSIV = ROOT / "99_BOT_ARSIV"
PROTOKOL_EK = ARSIV / "veri_yedek" / "MENTOR_PROTOKOL_EK.md"
GITHUB_REPO = "https://github.com/winegg420/ekonomikocu"

# 05_CLAUDE_ANALIZ.md ASLA silinmez / uzerine yazilmaz (Claude'in analiz beyni)
LEGACY = (
    ROOT / "CLAUDE_PAKET.zip",
    ROOT / "05_ONEMLI_GRAFIKLER_CLAUDE.md",
    ROOT / "05_GRAFIKLER_CLAUDE.jsonl",
    ROOT / "05_ONEMLI_GRAFIKLER_CLAUDE",
    ROOT / "04_vizyon_seviye_CLAUDE.jsonl",
    ROOT / "03_tweetler_GEMINI.md",
    ROOT / "04_CLAUDE_GRAFIKLER",
    ROOT / "00_CLAUDE_ATMA_SIRASI.md",
    ROOT / "01_CLAUDE_BURADAN_BASLA.md",
    ROOT / "02_ekonomikocu_hafiza_CLAUDE.md",
    ROOT / "03_cekilen_tweetler_CLAUDE.jsonl",
    ROOT / "04_CLAUDE_GRAFIKLER.zip",
    ROOT / "05_CLAUDE_ANALIZ.md",
    ROOT / "08_AI_MENTOR_REHBERI.md",
    ROOT / "06_tweetler_GEMINI.md",
    ROOT / "08_TWEETLER_GEMINI.md",
    ROOT / "10_ABONE_TWEETLER_GEMINI.md",
    ROOT / "00_CLAUDE_YUKLE",
)

ERISILEMEDI = "[erişilemedi]"

from eko_filtre import is_eko_media_row, is_spam_row
from grafik_filtre import graf_index, is_stock_logo_file, should_drop_media


def _has_text(r: dict) -> bool:
    t = (r.get("text") or "").strip()
    return bool(t) and t != ERISILEMEDI


def is_public_record(r: dict) -> bool:
    if r.get("is_quote"):
        return True
    if r.get("locked"):
        return False
    return _has_text(r)


def _icerik_tip_list(r: dict) -> list:
    t = r.get("tip")
    if isinstance(t, list):
        return t
    if isinstance(t, str) and t in ("vizyon", "seviye", "tarih", "tez", "yorum"):
        return [t]
    return []


def remove_legacy() -> None:
    for p in LEGACY:
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)


def stats() -> dict:
    rows = [
        json.loads(l)
        for l in JSONL.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    public = [r for r in rows if is_public_record(r)]
    main_pub = [r for r in public if not r.get("is_quote")]
    quotes = [r for r in public if r.get("is_quote")]
    quotes_ok = [r for r in quotes if _has_text(r)]
    quotes_eksik = [r for r in quotes if not _has_text(r)]
    with_graf = [r for r in public if r.get("media_files")]
    may_pub = [
        r
        for r in main_pub
        if r.get("datetime")
        and datetime.fromisoformat(r["datetime"]) < datetime(2026, 5, 1)
    ]
    dts = [r["datetime"] for r in main_pub if r.get("datetime")]
    nisan_main = [
        r
        for r in main_pub
        if r.get("datetime") and r["datetime"] >= "2026-04-01"
    ]
    abone_bos = [
        r
        for r in rows
        if not r.get("is_quote")
        and r.get("locked")
        and not _has_text(r)
    ]
    abone_metin = [
        r
        for r in rows
        if not r.get("is_quote")
        and _has_text(r)
        and (r.get("abone_metin") or r.get("kayit_tipi") == "abone")
    ]
    return {
        "toplam": len(public),
        "ana": len(main_pub),
        "alinti": len(quotes),
        "alinti_tam": len(quotes_ok),
        "alinti_eksik": len(quotes_eksik),
        "grafikli": len(with_graf),
        "may_oncesi": len(may_pub),
        "nisan_metinli": len(nisan_main),
        "abone_bos": len(abone_bos),
        "abone_metin": len(abone_metin),
        "en_eski": min(dts, default="—"),
        "en_yeni": max(dts, default="—"),
    }


def atma_sirasi_md(s: dict) -> str:
    g = s.get("graf_zip", 0)
    f5 = "var" if F5.is_file() else "YOK"
    f8 = "var" if F8.is_file() else "YOK"
    return f"""# YENİ SOHBET — NE ATILIR? (Claude / Gemini)

**Yeni yapay zeka sayfası açtığında önce bunu oku.**

## Claude (sıra)

1. `01_BURADAN_BASLA.md`
2. `02_MENTOR_REHBERI.md` [{f8}]
3. `03_HAFIZA.md`
4. `04_TWEETLER.jsonl`
5. `05_GRAFIKLER.zip` ({g} grafik)
6. `06_ANALIZ.md` [{f5}]

## Gemini (06'dan sonra — ayni kok klasor, 08-10)

7. `07_ABONE_TWEETLER.jsonl` (opsiyonel; abone icin **10** yeterli)
8. **`08_TWEETLER_GEMINI.md`** — tum public tweetler (.md)
9. **`09_GRAFIKLER_GEMINI/`** — jpg klasoru (zip yerine)
10. **`10_ABONE_TWEETLER_GEMINI.md`** — sadece abone tweetleri (.md)

Paket: `python claude_paket_olustur.py` · Güncel: {s["toplam"]} public | {datetime.now().strftime("%d.%m.%Y %H:%M")}
"""


def basla_md(s: dict) -> str:
    g = s.get("graf_zip", 0)
    return f"""# CLAUDE — BURADAN BAŞLA

**Kaynak (birincil):** [{GITHUB_REPO}]({GITHUB_REPO}) — dosyalari yerel yukleme yerine repodan cek. Claude Project: GitHub entegrasyonu veya repo clone.

**Claude:** `01` → `02` (**makro sentez — ZORUNLU**) → `03` → `04` → `05` → `06` (+ opsiyonel `07`)

**Gemini:** ayni `01-06`, sonra `08` → `09` klasor → `10`

**Tarama:** `TARAMA_DURUMU.md` — su tarihe kadar kayit tamam (`python 99_BOT_ARSIV/kod/kapsam_durum.py`)

`00_OKU_YUKLEME_SIRASI.txt` · Paket: `99_BOT_ARSIV/kod/claude_paket_olustur.py` · GitHub: `99_BOT_ARSIV/kod/github_guncelle.py`

## Amaç
Ida'yı **mentorlük** ile yönlendir: Koç'un **Trump / ABD / Fed makro yorumları** ile **teknik analiz ve grafiklerini birleştirerek** makro resmi okut. Bot değil; **kanıt defteri**. Detay: **02** bölüm «Makro sentez».

## Öncelik (yapay zeka)
Makro (Trump, Fed, ABD politikası, jeopolitik) + teknik (seviye, grafik) **ayrı değil — tek anlatı**. Haber botu değilsin; sadece Koç'un söylediklerini sentezle. **02 ★ Kalıcı mentor kuralları** (grafik, güncel fiyat, atıf, iletişim).

## Veri ({datetime.now().strftime("%d %B %Y")})
Public: **{s["toplam"]}** | Grafik: **{g}** | Detay: **08** + **05**

## Abonelik (Nisan 2026+)
**{s["abone_metin"]}** abone tweeti metinli (`07_ABONE_TWEETLER.jsonl` veya **04**'te `kayit_tipi: abone`) · **{s["abone_bos"]}** hâlâ boş.

**ÖNEMLİ:** Abone metinleri `locked: false`. `locked: true` arama = yanlış. Önce **07** dosyasını oku veya `kayit_tipi: abone` filtrele.
"""


def _load_protokol_ek() -> str:
    """Kalici mentor kurali — veri_yedek; paket her yenilendiginde 02'ye eklenir."""
    if not PROTOKOL_EK.is_file():
        return ""
    return PROTOKOL_EK.read_text(encoding="utf-8").strip()


def _tip_counts(public_rows: list[dict]) -> dict[str, int]:
    c = {t: 0 for t in ("vizyon", "seviye", "tarih", "tez", "yorum")}
    for r in public_rows:
        if r.get("is_quote"):
            continue
        for t in _icerik_tip_list(r):
            if t in c:
                c[t] += 1
    return c


def build_mentor_md(s: dict, public_rows: list[dict]) -> str:
    tips = _tip_counts(public_rows)
    tip_line = " · ".join(f"{k} {tips[k]}" for k in tips)
    protokol = _load_protokol_ek()
    protokol_block = ""
    if protokol:
        body = protokol.strip()
        if body:
            protokol_block = f"""
## ★ Kalıcı mentor kuralları — ZORUNLU (her sohbette uygula)

{body}

"""
    return f"""# 02 — YAPAY ZEKA MENTOR REHBERİ (@ekonomikocu)

**Bu dosya yeni Claude / Gemini sohbetinin ikinci adımıdır** (`01` → **`02`** → `03`…`06`).

**Sen kimsin?** Ida'nın mentorüsün. Koç'un kanıt defterinden **makro (Trump, ABD, Fed, jeopolitik) ile teknik analizi birleştirerek** makroekonomi yorumlarsın; haber ajansı veya saf teknik analist değilsin.

**Güncelleme:** {datetime.now().strftime("%d %B %Y %H:%M")} · Paket: `python claude_paket_olustur.py`

---

## ★ Makro sentez — ZORUNLU (Trump / ABD / Fed + teknik)

**En önemli görevin:** Koç'un ABD, Trump, Fed/faiz, jeopolitik ve borsa/kripto/emtia yorumlarını **teknik seviyeler ve grafiklerle birleştirip** Ida'ya **tutarlı makro anlatı** sunmak.

### Nasıl çalışırsın

1. **Makro katman** — `tip: tez` · `vizyon` · `tarih` tweetleri; anahtar: Trump, Fed, Powell, faiz, ABD, seçim, barış, Çin, enflasyon, DXY, NASDAQ, SP500, petrol.
2. **Teknik katman** — aynı dönem / aynı ürün için `tip: seviye` + `05_GRAFIKLER` / `09_GRAFIKLER_GEMINI` (sadece yazılı rakam ve grafik; uydurma yok).
3. **Sentez** — «Koç makroda X diyor; teknikte Y seviyesi/grafiği bunu şöyle destekliyor veya çelişiyor» formatında, **tek paragraf akış**, tablo yok.

### Kurallar

- BTC, NASDAQ, altın, petrolu **makro çerçevesiz** tek başına yorumlama.
- Trump/Fed tweeti ile aynı haftanın seviye tweetini **bilerek eşleştir**; eşleşme yoksa «Koç bu dönemde makro yazmış, teknik ayrı» de.
- Dış haber ekleme; sadece **03, 04, 06, grafikler**.
- Ida sorunca önce **büyük resim (makro tez)**, sonra **kanıt seviyesi (tweet_id + tarih)**.

### Örnek soru → cevap iskeleti

«Trump / Fed son gelişmeye göre Koç ne diyor ve grafikte neredeyiz?»
→ Makro özet (tez tweetleri) → ilgili seviye/grafik → senaryo (yükseliş / zaman geçirme / düzeltme) → belirsizlikte «Koç yazmadı».

---
{protokol_block}---
## 1. Projenin amacı

- X'te **sadece public** @ekonomikocu içeriğini topluyoruz: ana tweet, **alıntı** (quote), **#FLOOD** thread parçaları, **grafik görselleri**.
- Amaç: Ida yeni bir yapay zeka sayfası açtığında **Koç'un makro tezini, ürün bazlı uzun vade görüşünü, kritik seviyeleri ve tarih pencerelerini** kayıp yaşamadan devam ettirebilsin.
- **06_ANALIZ.md** = özetlenmiş "beyin" (Claude yazdı; script üzerine yazmaz). **02** = nasıl çalıştığımız + nasıl mentorluk yapacağın.

---

## 2. Dosya haritası (yükleme sırası)

| Sıra | Dosya | Ne işe yarar |
|------|--------|----------------|
| 1 | `01_BURADAN_BASLA.md` | Kısa giriş |
| 2 | **`02_MENTOR_REHBERI.md`** | **Bu dosya** — iş akışı, alıntı kuralları, mentorluk |
| 3 | `03_HAFIZA.md` | İnsan okunur kanıt defteri |
| 4 | `04_TWEETLER.jsonl` | Yapısal veri: `tweet_id`, `tip`, `products`… |
| 5 | `05_GRAFIKLER.zip` | `tweet_id` ile eşleşen jpg + indeks |
| 6 | `06_ANALIZ.md` | Koç özeti — **en son** |

Gemini (kok): `08_TWEETLER_GEMINI.md` → `09_GRAFIKLER_GEMINI/` → `10_ABONE_TWEETLER_GEMINI.md`

---

## 3. Bot ne yapıyor?

1. Chrome (CDP 9222) ile @ekonomikocu profilini tarar (`tweet_tara.py`, `tamamla_eksiksiz.py`).
2. Her tweet `cekilen_tweetler.jsonl`; hafıza `ekonomikocu_hafiza_v1.md`.
3. Öncelik: en yeni → 2026 ayları → alıntılar → medya → geriye scroll.
4. Reklam/spam paketten çıkar. `claude_paket_olustur.py` → 01–04, 06–07, Gemini 08–10 yenilenir; **06_ANALIZ'e dokunulmaz**.
5. **Ekran görüntüsü (2024–2025, bot henüz inmedi):** `python manuel_ekran_ekle.py` → aynı **02, 03, 04, 07** içinde (`tweet_id` `MANUEL-…`, görsel `medya/MANUEL-…/graf_01.jpg`). **Ekstra yükleme dosyası yok.**

**Mentor:** Akıcı Türkçe, tablo yok, seviye uydurma yok. Grafik/ekran: **04 zip** ve **07 klasörü** (03'teki `media_files` ile eşleşir).

---

## 4. Alıntı (quote) — kritik kural

| Durum | Anlam | Mentorluk |
|--------|--------|-----------|
| **Önceden alıntı** | Önce asıl tweet; sonra başka tweette eski tweeti alıntılayıp "demiştim" | **Geçerli kanıt** — asıl tarih + metin esas |
| **Sonradan alıntı** | Olaydan hemen sonra alıntı ile başarı gösterme | **Başarı sayma** — hafızada `SONRADAN alıntı` |

- `is_quote: true` → alıntı satırı (orijinal içerik).
- `[erişilemedi]` → tamamlanana kadar seviye çıkarma (`alinti_tamamla.py`).

---

## 5. İçerik tipleri (`tip`)

| tip | Kayıt | Mentorluk |
|-----|--------|-----------|
| **vizyon** | Uzun vade potansiyel, döngü | "Bu enstrümanda Koç ne görüyor?" |
| **seviye** | Fiyat bandı, fib, destek/direnç | ★ Grafik okuma + yazılı rakam; çizili etiketleri jpg'den oku |
| **tarih** | Temmuz 9-11, #2026, barış günleri | Takvim / senaryo |
| **tez** | Makro anlatı (Trump, Fed, ABD, jeopolitik), zaman geçirme | ★ bölümde teknikle birleştir; 06 ile büyük resim |
| **yorum** | Günlük nabız | Daha hafif ağırlık |

**Ana tweet tip dağılımı:** {tip_line}

---

## 6. Ürünler (`products`)

`BTC`, `ETH`, `GUMUS_PETROL`, `GENEL`… — 03'te filtrele → `vizyon` + `seviye` önce → `tweet_id` → 04 grafik.

**Kilitli (`locked`):** analize dahil etme, seviye uydurma.

---

## 7. Grafikler

`medya/{{tweet_id}}/graf_XX.jpg` → pakette `{{tweet_id}}_graf_XX.jpg` (Claude: **05** zip · Gemini: **09** klasör). Seviye sorusunda görseli **AÇ** — ★ Grafik okuma kuralı. Metinde olmayan rakamı uydurma.

---

## 8. #FLOOD

Thread parçaları ayrı satır; parçaları birleştir, tek parçayı nihai tez sanma.

---

## 9. Güncel veri

| Metrik | Değer |
|--------|--------|
| Public | **{s["toplam"]}** |
| Ana tweet | **{s["ana"]}** |
| Alıntı (tam / eksik) | **{s["alinti"]}** (**{s["alinti_tam"]}** / **{s["alinti_eksik"]}**) |
| Grafikli | **{s["grafikli"]}** |
| May 2026 öncesi ana | **{s["may_oncesi"]}** |
| Aralık | **{s["en_eski"]}** → **{s["en_yeni"]}** |
| Nisan+ metinli ana (abone dönemi) | **{s["nisan_metinli"]}** |
| **Abone metinli** (`abone_metin: true`) | **{s["abone_metin"]}** |
| Abone — hâlâ boş/kilitli | **{s["abone_bos"]}** (pakette yok) |

Mart 2026 ve bazı aylar seyrek — "veri henüz tam değil" de. **Abone metinleri `locked: false` + `kayit_tipi: abone`** — `locked: true` arama yapma.

---

## 10. Mentorluk şablonu

1. **Makro sentez (★)** — Trump/ABD/Fed tezleri + teknik/grafik birlikte oku.
2. 02 + 06'yı esas al; kanıt için 03/04 + `tweet_id`.
3. **Seviye sorusu:** ★ Grafik okuma — tweet_id ile jpg AÇ, çizili rakamları oku + metin `seviye`; alıntıda önceden/sonradan ayır.
4. Emin değilsen: "Koç yazmadı / kilitli" de.

**Omurga (06):** Zaman geçirme, BTC döngü, Trump/ABD–Çin/emtia kozları, Fed/enflasyon, Temmuz/Ağustos pencereleri.

---

## 11. Ida'ya tek cümle

*"02'deki makro sentez + grafik okuma kurallarını uygula; seviye sorusunda jpg'yi AÇ; uydurma yok."*

---

*Otomatik: `claude_paket_olustur.py`. `05` yalnızca Claude oturumunda güncellenir.*
"""


def _grafik_entries(public_rows: list[dict]) -> list[dict]:
    """Sadece @ekonomikocu grafikleri (reklam / yabanci alinti yok)."""
    entries: list[dict] = []
    for r in public_rows:
        if not is_eko_media_row(r):
            continue
        media = r.get("media_files") or []
        if not media:
            continue
        tid = r.get("tweet_id") or ""
        text = (r.get("text") or "").strip()
        urls = r.get("media_urls") or []
        for src_rel in media:
            src = ROOT / Path(str(src_rel).replace("\\", "/"))
            if not src.is_file():
                continue
            idx = graf_index(str(src_rel))
            url = urls[idx - 1] if idx and idx <= len(urls) else ""
            if should_drop_media(url, str(src_rel), ROOT) or is_stock_logo_file(src):
                continue
            dest_name = f"{tid}_{src.stem}{src.suffix.lower()}"
            entries.append(
                {
                    "tweet_id": tid,
                    "datetime": r.get("datetime") or "",
                    "date_label": r.get("date_label") or "",
                    "tip": _icerik_tip_list(r),
                    "products": r.get("products") or [],
                    "text": text,
                    "zip_dosya": f"grafikler/{dest_name}",
                    "src": src,
                    "dest_name": dest_name,
                }
            )
    entries.sort(key=lambda e: e.get("datetime") or "", reverse=True)
    return entries


def _rows_to_gemini_md(
    rows: list[dict],
    *,
    title: str,
    intro: str,
) -> str:
    lines = [title, "", intro, "", f"Toplam: **{len(rows)}**", ""]
    for r in sorted(rows, key=lambda x: x.get("datetime") or "", reverse=True):
        tid = r.get("tweet_id") or ""
        tips = ", ".join(_icerik_tip_list(r)) or "—"
        prods = ", ".join(r.get("products") or []) or "GENEL"
        mf = ", ".join(r.get("media_files") or []) or "—"
        abone = (
            "abone"
            if r.get("abone_metin") or r.get("kayit_tipi") == "abone"
            else "public"
        )
        graf = f"09_GRAFIKLER_GEMINI/{tid}_graf_01.jpg" if mf != "—" else "—"
        text = (r.get("text") or "").strip()
        lines += [
            f"## {r.get('date_label') or ''} | `{tid}` | {prods} | {tips} | {abone}",
            "",
            text,
            "",
            f"- media: {mf}",
            f"- gemini_grafik: {graf}",
            "",
        ]
    return "\n".join(lines)


def build_gemini_tweet_md(public_rows: list[dict]) -> None:
    """Gemini jsonl okumaz — 08 numarali .md."""
    body = _rows_to_gemini_md(
        public_rows,
        title="# 08 — TWEETLER (Gemini)",
        intro=(
            "Once Cloud dosyalari: 01-06 (+ opsiyonel 07). Sonra bu dosya, "
            "09_GRAFIKLER_GEMINI klasoru, 10_ABONE_TWEETLER_GEMINI.md.\n"
            "ZORUNLU: 02_MENTOR_REHBERI.md — Makro sentez + kalici mentor kurallari (grafik, guncel fiyat, atif)."
        ),
    )
    F8_GEMINI_TWEET.write_text(body, encoding="utf-8")


def build_gemini_abone_md(abone_rows: list[dict]) -> None:
    """Abone tweetleri — Gemini icin .md (07 jsonl yerine veya ek)."""
    body = _rows_to_gemini_md(
        abone_rows,
        title="# 10 — ABONE TWEETLER (Gemini)",
        intro=(
            "Sadece abone donemi tweetleri (`kayit_tipi: abone`). "
            "Makro (Trump/Fed/ABD) + teknik yorumlari burada da birlestir — 02 kurallari gecerli."
        ),
    )
    F10_ABONE_GEMINI.write_text(body, encoding="utf-8")


def build_09_gemini_folder(graf_entries: list[dict]) -> int:
    """Gemini: 09 klasoru (jpg — zip yerine)."""
    if DIR09_GEMINI_GRAF.exists():
        shutil.rmtree(DIR09_GEMINI_GRAF)
    DIR09_GEMINI_GRAF.mkdir(parents=True)
    for e in graf_entries:
        shutil.copy2(e["src"], DIR09_GEMINI_GRAF / e["dest_name"])
    (DIR09_GEMINI_GRAF / "OKU_BENI.txt").write_text(
        "09_GRAFIKLER_GEMINI — 08_TWEETLER_GEMINI.md ile eslesir.\n"
        "Dosya adi: TWEET_ID_graf_XX.jpg\n",
        encoding="utf-8",
    )
    return len(graf_entries)


def build_04_zip(graf_entries: list[dict]) -> int:
    """Sadece grafikler + indeks — 01-02-03 ayrı dosya olarak kalır."""
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)
    graf_dir = STAGING / "grafikler"
    graf_dir.mkdir()
    for e in graf_entries:
        shutil.copy2(e["src"], graf_dir / e["dest_name"])

    lines = [
        "# Grafikler — 03_cekilen_tweetler_CLAUDE.jsonl ile eşleşir",
        "",
        "Bu zip, **04** numaralı dosyadır. Önce 01, 08, 02, 03 yüklendi.",
        "Her jpg adı `TWEET_ID_graf_XX.jpg` — 03'te `tweet_id` ile aynı satırı bul.",
        "",
    ]
    cur = None
    for e in graf_entries:
        if e["tweet_id"] != cur:
            cur = e["tweet_id"]
            tips = ", ".join(e["tip"]) or "—"
            prods = ", ".join(e["products"]) or "GENEL"
            ozet = e["text"].replace("\n", " ")
            if len(ozet) > 500:
                ozet = ozet[:497] + "…"
            lines += [
                f"## {e['date_label']} | tweet_id `{cur}` | {prods} | {tips}",
                "",
                ozet,
                "",
            ]
        lines.append(f"- `{e['zip_dosya']}`")
        lines.append("")

    (STAGING / "GRAFIK_INDEKS.md").write_text("\n".join(lines), encoding="utf-8")
    (STAGING / "OKU_BENI.txt").write_text(
        "04 numarali dosya — 01, 08, 02, 03 ile birlikte at.\n"
        "grafikler/ = 03 jsonl satirlarindaki media_files gorselleri.\n",
        encoding="utf-8",
    )

    if ZIP04.exists():
        ZIP04.unlink()
    with zipfile.ZipFile(ZIP04, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(STAGING.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(STAGING).as_posix())
    shutil.rmtree(STAGING)
    return len(graf_entries)


def write_upload_readme(s: dict) -> None:
    g = s.get("graf_gemini", 0)
    lines = [
        "YUKLEME SIRASI — ekonomikocu (00-10)",
        "",
        f"GITHUB (birincil kaynak): {GITHUB_REPO}",
        "Claude Project: GitHub repo bagla veya clone. Yerel yukleme yedek.",
        "",
        "=== CLOUD (Claude) — ayni sira ===",
        "1. 01_BURADAN_BASLA.md",
        "2. 02_MENTOR_REHBERI.md",
        "3. 03_HAFIZA.md",
        "4. 04_TWEETLER.jsonl",
        "5. 05_GRAFIKLER.zip",
    ]
    if F5.is_file():
        lines.append("6. 06_ANALIZ.md")
    lines += [
        "7. 07_ABONE_TWEETLER.jsonl  (opsiyonel — abone jsonl)",
        "",
        "=== GEMINI — 06'dan sonra ===",
        "8. 08_TWEETLER_GEMINI.md",
        f"9. 09_GRAFIKLER_GEMINI/  ({g} jpg)",
        "10. 10_ABONE_TWEETLER_GEMINI.md",
        "",
        f"Guncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        f"Public: {s.get('toplam', '—')} | Abone metinli: {s.get('abone_metin', '—')}",
        f"Abone bos kilitli: {s.get('abone_bos', '—')}",
        "Paket yenile: python 99_BOT_ARSIV/kod/claude_paket_olustur.py",
        "GitHub gonder: python 99_BOT_ARSIV/kod/github_guncelle.py",
    ]
    F0.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not HAFIZA.is_file():
        raise SystemExit(f"Eksik: {HAFIZA}")
    if not JSONL.is_file():
        raise SystemExit(f"Eksik: {JSONL}")

    for old, new in (
        (ROOT / "05_CLAUDE_ANALIZ.md", F5),
        (ROOT / "08_AI_MENTOR_REHBERI.md", F8),
        (ROOT / "01_CLAUDE_BURADAN_BASLA.md", F1),
    ):
        if not new.is_file() and old.is_file():
            shutil.copy2(old, new)

    remove_legacy()

    s = stats()
    public_rows: list[dict] = []
    spam_n = 0
    for l in JSONL.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if is_spam_row(r):
            spam_n += 1
            continue
        if is_public_record(r):
            public_rows.append(r)
    if spam_n:
        print(f"  Reklam/kirli atlandi: {spam_n} satir (pakette yok)")

    F8.write_text(build_mentor_md(s, public_rows), encoding="utf-8")
    shutil.copy2(HAFIZA, F2)
    F3.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in public_rows)
        + ("\n" if public_rows else ""),
        encoding="utf-8",
    )
    abone_rows = [
        r
        for r in public_rows
        if r.get("abone_metin") or r.get("kayit_tipi") == "abone"
    ]
    F7_ABONE.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in abone_rows)
        + ("\n" if abone_rows else ""),
        encoding="utf-8",
    )

    graf_entries = _grafik_entries(public_rows)
    build_gemini_tweet_md(public_rows)
    build_gemini_abone_md(abone_rows)
    s["graf_gemini"] = build_09_gemini_folder(graf_entries)
    s["graf_zip"] = build_04_zip(graf_entries)
    F1.write_text(basla_md(s), encoding="utf-8")
    write_upload_readme(s)

    mb = round(ZIP04.stat().st_size / (1024 * 1024), 1) if ZIP04.is_file() else 0
    print("")
    print("Claude'a AT — kok klasor, sirayla:")
    for i, p in enumerate((F1, F8, F2, F3, ZIP04, F5), 1):
        tag = ""
        if p == ZIP04:
            tag = f"  ({mb} MB, {s['graf_zip']} grafik)"
        elif p == F5 and not p.is_file():
            tag = "  *** YOK ***"
        elif p == F5:
            tag = "  (analiz — dokunulmadi)"
        print(f"  {i}. {p.name}{tag}")
    print("  --- Gemini (kok klasor) ---")
    print(f"  7. {F7_ABONE.name}  (opsiyonel)")
    print(f"  8. {F8_GEMINI_TWEET.name}")
    print(f"  9. {DIR09_GEMINI_GRAF.name}/  ({s.get('graf_gemini', 0)} jpg)")
    print(f"  10. {F10_ABONE_GEMINI.name}")
    print(f"  Yukleme kilavuzu: {F0.name}")
    print("  Kok klasorde 00-10 alt alta (Explorer en ust)")


if __name__ == "__main__":
    main()
