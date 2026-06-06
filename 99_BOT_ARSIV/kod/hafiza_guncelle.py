#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ekonomikocu hafıza güncelleyici (yarı-otomatik).

Kullanım:
  1. Chrome/Edge'de x.com/ekonomikocu profilinde tweetleri görünür kılın.
  2. İlgili bölümü seçip kopyalayın → ham_veri.txt dosyasına yapıştırın.
  3. python hafiza_guncelle.py
     python hafiza_guncelle.py --dry-run   # dosyaya yazmadan önizleme

Girdi: ham_veri.txt (aynı klasör)
Çıktı: ekonomikocu_hafiza_v1.md güncellenir (+ .bak yedek)
"""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HAM_VERI = ROOT / "ham_veri.txt"
HAFIZA = ROOT / "ekonomikocu_hafiza_v1.md"

# --- Sabitler (hafıza formatı) ---
SECTION_5_MARKER = "## 5. ÜRÜN BAZLI KANIT DEFTERİ"
SECTION_6_MARKER = "## 6. CLAUDE'UN DEĞERLENDİRMESİ"
SECTION_9_MARKER = "## 9. İLERLEME"

PRODUCT_SECTIONS = {
    "BTC": "### BTC",
    "GUMUS_PETROL": "### GÜMÜŞ / PETROL / ENFLASYON / DOLAR",
    "GUMUS_120": r"### GÜMÜŞ — \$120",
    "GENEL": "### Genel tez tweetleri",
}

MONTH_TR = {
    "oca": 1, "şub": 2, "sub": 2, "mar": 3, "nis": 4, "may": 5, "haz": 6,
    "tem": 7, "ağu": 8, "agu": 8, "eyl": 9, "eki": 10, "kas": 11, "ara": 12,
}
MONTH_EN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# X arayüzünden kopyalanan gürültü satırları
JUNK_LINE = re.compile(
    r"^(?:"
    r"Home|Explore|Notifications|Messages|Grok|Bookmarks|Communities|Premium|Profile|More|"
    r"Post|Show more|Show less|Translate post|View post engagements|"
    r"Promoted|Who to follow|What\'s happening|Subscribe to|Subscribed|"
    r"Relevant people|Follow|Following|Pinned|"
    r"\d+(?:\.\d+)?[KMB]?\s*(?:reposts?|replies|likes?|views?|bookmarks?)|"
    r"Replying to|Read \d+ replies|"
    r"ekonomikocu\.com|"
    r"@ekonomikocu\s*$|"
    r"Ekonomi\s*Koç\s*$|"
    r"Verified|"
    r")\s*$",
    re.I,
)

STATUS_URL = re.compile(
    r"(?:https?://)?(?:www\.)?(?:x|twitter)\.com/ekonomikocu/status/(\d+)",
    re.I,
)

# Tarih/saat kalıpları (X kopya-yapıştır)
RELATIVE_TIME = re.compile(r"^\d+\s*[smhd]\b", re.I)

DATE_PATTERNS = [
    # 3 Haz 2026 · 15:36  veya  15:36 · 3 Haz 2026
    re.compile(
        r"(?:(\d{1,2}):(\d{2})\s*(?:AM|PM)?\s*·\s*)?"
        r"(\d{1,2})\s+(Oca|Şub|Sub|Mar|Nis|May|Haz|Tem|Ağu|Agu|Eyl|Eki|Kas|Ara)\.?\s+(\d{4})"
        r"(?:\s*·\s*(\d{1,2}):(\d{2})\s*(?:AM|PM)?)?",
        re.I,
    ),
    # 1 Jun 2026 (gün önce ay)
    re.compile(
        r"(\d{1,2})\s+"
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|"
        r"Oca|Şub|Sub|Mar|Nis|May|Haz|Tem|Ağu|Agu|Eyl|Eki|Kas|Ara)\.?\s+(\d{4})"
        r"(?:\s+(\d{1,2}):(\d{2})\s*(?:AM|PM)?)?",
        re.I,
    ),
    re.compile(
        r"(Oca|Şub|Sub|Mar|Nis|May|Haz|Tem|Ağu|Agu|Eyl|Eki|Kas|Ara|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})"
        r"(?:\s+(\d{1,2}):(\d{2})\s*(?:AM|PM)?)?",
        re.I,
    ),
    # 2 Haz 12:17 (hafızadaki kısa format)
    re.compile(
        r"(\d{1,2})\s+(Oca|Şub|Sub|Mar|Nis|May|Haz|Tem|Ağu|Agu|Eyl|Eki|Kas|Ara)\.?\s+(\d{4})?\s*(\d{1,2}):(\d{2})",
        re.I,
    ),
    re.compile(
        r"(\d{1,2})\s+(Oca|Şub|Sub|Mar|Nis|May|Haz|Tem|Ağu|Agu|Eyl|Eki|Kas|Ara)\.?\s+(\d{1,2}):(\d{2})",
        re.I,
    ),
]

LOCKED_MARKERS = re.compile(
    r"subscriber|subscribers\s+only|abonelere|subscribe to unlock|abone|abonelik|"
    r"kilidi|content is unavailable|unlock this post|bu gönderinin tamamı",
    re.I,
)

FLOOD_MARKERS = re.compile(r"#FLOOD|/flood\b", re.I)

PRODUCT_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("BTC", re.compile(r"\b(?:#?btc|bitcoin|kobeissi)\b", re.I)),
    (
        "GUMUS_PETROL",
        re.compile(r"\b(?:#?gümüş|#?gumus|gümüş|silver|#?petrol|#?emtia|emtia|enflasyon|dolar)\b", re.I),
    ),
    ("GUMUS_120", re.compile(r"gümüşün\s+120|gumus.*120|\$120|120\s*dolar", re.I)),
]


@dataclass
class TweetRecord:
    tweet_id: str | None
    dt: datetime | None
    date_label: str  # "3 Haz 15:36"
    locked: bool
    text: str
    products: list[str] = field(default_factory=list)
    tip: str = "yorum"  # kayıt rolü: asıl tahmin, flood, alıntı satırı…
    icerik_tip: list[str] = field(default_factory=lambda: ["yorum"])  # vizyon,seviye,…
    is_quote: bool = False
    quoted_by: str | None = None  # ana tweet id (alıntı ise)
    quote_of: str | None = None  # alıntılanan tweet id
    thread_root: str | None = None  # #FLOOD thread kök id (parça ise)
    lang: str = "tr"  # tr | en | ceviri_suphe
    analyzed: bool = False
    raw_excerpt: str = ""
    fiyat: str = "—"
    sonra: str = "—"
    sonuc: str = ""
    baglanti: str = ""
    media_urls: list[str] = field(default_factory=list)
    media_files: list[str] = field(default_factory=list)

    def sort_key(self) -> tuple:
        if self.dt:
            return (self.dt,)
        return (datetime.min,)

    def product_label(self) -> str:
        m = {"BTC": "BTC", "GUMUS_PETROL": "GÜMÜŞ/PETROL/EMTIA/DOLAR", "GUMUS_120": "GÜMÜŞ$120", "GENEL": "GENEL"}
        return ", ".join(m.get(p, p) for p in self.products) or "GENEL"

    def hafiza_line(self) -> str:
        """EKSİKSİZ KAYIT satırı (Claude şablonu)."""
        lock = "KİLİTLİ" if self.locked else "ACIK"
        text_clean = self.text.replace("\n", " ").strip()
        if len(text_clean) > 2000:
            text_clean = text_clean[:1997] + "…"
        text_clean = text_clean.replace('"', "'")

        id_part = self.tweet_id or "id-yok"
        itip = "+".join(self.icerik_tip) if self.icerik_tip else "yorum"
        kayit = self.tip or ("kilitli" if self.locked else "yorum")
        urun = self.product_label()

        if self.locked and not text_clean:
            metin = "eksik (abonelik)."
        else:
            metin = f'"{text_clean}"' if text_clean else "eksik (abonelik)."

        extra = []
        if self.quote_of:
            extra.append(f"alıntılanan tweet: {self.quote_of}")
        if self.quoted_by:
            extra.append(f"ana tweet {self.quoted_by} içinde alıntı")
        if self.is_quote and not self.quote_of:
            extra.append("alıntı (tarih tweet_id ile)")
        if self.thread_root and self.thread_root != self.tweet_id:
            extra.append(f"#FLOOD thread parçası (kök: {self.thread_root})")
        if self.media_files:
            graf = ", ".join(self.media_files[:12])
            if len(self.media_files) > 12:
                graf += f" (+{len(self.media_files) - 12} grafik)"
            extra.append(f"grafikler: {graf}")
            extra.append("GRAFİK ANALİZ: çizilen hatlar, destek/direnç, ok/etiket, zaman dilimi")

        fiyat = self.fiyat or "—"
        if fiyat == "—" and re.search(r"\$[\d,]+|seviye|hedef|göreceği|gorecegi", text_clean, re.I):
            fiyat = "DOĞRULANACAK (web)"

        if self.sonuc:
            sonuc = self.sonuc
        elif self.lang == "en":
            sonuc = "CEVIRI_KIRLI — yeniden tara (Chrome çeviri kapalı)"
        elif not self.analyzed:
            sonuc = "ANALİZ_BEKLİYOR"
        elif re.search(r"seviye|hedef|\$[\d,]+|tarih", text_clean, re.I):
            sonuc = "izleniyor"
        else:
            sonuc = "yorum"

        sonra = self.sonra or "—"
        if self.baglanti:
            extra.append(self.baglanti)

        tail = f" | fiyat: {fiyat} | sonra: {sonra} | sonuç: {sonuc}"
        ctx = (" " + " ".join(extra)) if extra else ""
        if self.lang == "en":
            ctx += " [İngilizce metin — Koç Türkçe; çeviri açık olabilir]"
        return (
            f"- **{id_part} | {self.date_label} UTC | {urun} | {lock} | tip: {itip} | kayıt: {kayit}** — "
            f"{metin}{tail}{ctx}"
        )


def detect_lang(text: str) -> str:
    if not text or len(text) < 8:
        return "tr"
    tr = len(re.findall(r"[ğıüşöçİĞÜŞÖÇ]", text))
    en_markers = len(
        re.findall(
            r"\b(the|and|you|this|that|with|for|are|was|have|will|using|during)\b",
            text,
            re.I,
        )
    )
    if tr >= 2:
        return "tr"
    if en_markers >= 2 or (tr == 0 and re.search(r"\b[A-Za-z]{5,}\b", text)):
        return "en"
    return "tr"


def rebuild_section_5_from_records(records: list[TweetRecord]) -> str:
    """Bölüm 5'i Claude düzeninde sıfırdan üret."""
    groups: dict[str, list[TweetRecord]] = {k: [] for k in PRODUCT_SECTIONS}
    for rec in records:
        for prod in rec.products:
            if rec not in groups[prod]:
                groups[prod].append(rec)

    parts = ["## 5. ÜRÜN BAZLI KANIT DEFTERİ (eksiksiz kayıt — bu oturumda işlenenler)\n"]
    order = ["BTC", "GUMUS_PETROL", "GUMUS_120", "GENEL"]
    for key in order:
        header = PRODUCT_SECTIONS[key]
        items = sorted(groups[key], key=lambda r: r.sort_key(), reverse=True)
        if not items:
            continue
        parts.append(f"\n{header}\n")
        seen: set[str] = set()
        for rec in items:
            line = rec.hafiza_line()
            if line in seen:
                continue
            seen.add(line)
            parts.append(line)
    return "\n".join(parts).rstrip() + "\n"


def rebuild_hafiza_md(md: str, records: list[TweetRecord]) -> str:
    """Bölüm 5'i yenile; 0-4 ve 6+ koru; Bölüm 9 gerçek en eski/yeni."""
    s5 = rebuild_section_5_from_records(records)
    md = re.sub(
        r"## 5\. ÜRÜN BAZLI KANIT DEFTERİ.*?(?=\n## 6\.)",
        s5 + "\n---\n\n",
        md,
        count=1,
        flags=re.DOTALL,
    )
    dated = [r for r in records if r.dt]
    if dated:
        newest = max(dated, key=lambda r: r.dt)
        oldest = min(dated, key=lambda r: r.dt)
        md = re.sub(
            r"- \*\*Bu oturumda işlenen aralık:\*\*.*",
            f"- **Bu oturumda işlenen aralık:** {newest.date_label} → {oldest.date_label} (UTC). Profil tarama.",
            md,
        )
        if newest.tweet_id:
            md = re.sub(
                r"- \*\*En son/en yeni tweet_id:\*\*.*",
                f"- **En son/en yeni tweet_id:** {newest.tweet_id} ({newest.date_label}).",
                md,
            )
        md = re.sub(
            r"- \*\*En eski işlenen:\*\*.*",
            f"- **En eski işlenen:** {oldest.date_label} ({oldest.tweet_id or '—'}).",
            md,
        )
    md = re.sub(
        r"- \*\*SONRAKİ HEDEF:\*\*.*",
        "- **SONRAKİ HEDEF:** `python tweet_tara.py` — geriye devam; donarsa yeni sekme + profil.",
        md,
    )
    return bump_version(md)


def normalize_month(name: str | None) -> int | None:
    if not name:
        return None
    key = name.lower().replace(".", "")[:3]
    return MONTH_TR.get(key) or MONTH_EN.get(key)


def parse_ampm(hour: int, ampm: str | None) -> int:
    if not ampm:
        return hour
    ap = ampm.upper()
    if ap == "PM" and hour < 12:
        return hour + 12
    if ap == "AM" and hour == 12:
        return 0
    return hour


def try_parse_date(text: str) -> tuple[datetime | None, str]:
    """Metinden ilk mutlak tarih/saati çıkar; hafıza etiketi döndür."""
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        groups = m.groups()
        try:
            g = list(groups)

            # Türkçe: (h1?, m1?,) day, mon, year, (h2?, m2?)
            if (
                len(g) >= 4
                and g[2]
                and str(g[2]).isdigit()
                and len(str(g[2])) <= 2
                and g[3]
                and normalize_month(g[3])
            ):
                h1, m1, day, mon, year = g[0], g[1], int(g[2]), g[3], int(g[4])
                h2, m2 = (g[5], g[6]) if len(g) > 6 else (None, None)
                month = normalize_month(mon)
                hour = int(h2 or h1 or 0)
                minute = int(m2 or m1 or 0)
                dt = datetime(year, month, day, hour, minute)
                label = f"{day} {mon[:3].title()} {hour:02d}:{minute:02d}"
                return dt, label

            # 1 Jun 2026 — day, mon, year
            if g[0] and str(g[0]).isdigit() and g[1] and normalize_month(g[1]):
                day, mon, year = int(g[0]), g[1], int(g[2])
                month = normalize_month(mon)
                hour, minute = (int(g[3]), int(g[4])) if len(g) > 4 and g[3] else (0, 0)
                dt = datetime(year, month, day, hour, minute)
                label = f"{day} {mon[:3].title()} {hour:02d}:{minute:02d}" if hour else f"{day} {mon[:3].title()}"
                return dt, label

            # Jun 1, 2026 — mon, day, year
            if g[0] and g[0][0].isalpha() and g[1] and str(g[1]).isdigit():
                mon, day, year = g[0], int(g[1]), int(g[2])
                month = normalize_month(mon)
                hour, minute = (int(g[3]), int(g[4])) if len(g) > 4 and g[3] else (0, 0)
                dt = datetime(year, month, day, hour, minute)
                label = f"{day} {mon[:3].title()} {hour:02d}:{minute:02d}" if hour else f"{day} {mon[:3].title()}"
                return dt, label

            # 2 Haz 12:17
            if g[0] and str(g[0]).isdigit() and g[1] and normalize_month(g[1]):
                day, mon = int(g[0]), g[1]
                month = normalize_month(mon)
                year = int(g[2]) if len(g) > 2 and g[2] and str(g[2]).isdigit() and len(str(g[2])) == 4 else 2026
                if len(g) >= 4 and g[-2] and str(g[-2]).isdigit() and int(g[-2]) < 24:
                    hour, minute = int(g[-2]), int(g[-1])
                else:
                    hour, minute = 0, 0
                dt = datetime(year, month, day, hour, minute)
                label = f"{day} {mon[:3].title()} {hour:02d}:{minute:02d}" if hour else f"{day} {mon[:3].title()}"
                return dt, label
        except (ValueError, TypeError):
            continue

    rel = re.search(r"\b(\d+)\s*([smhd])\b", text, re.I)
    if rel:
        return None, f"göreli ({rel.group(1)}{rel.group(2)}) — tarih netleştir"
    return None, "tarih-belirsiz"


def has_absolute_date(text: str) -> bool:
    dt, label = try_parse_date(text)
    return dt is not None or (
        label != "tarih-belirsiz" and not label.startswith("göreli")
    )


def classify_products(text: str) -> list[str]:
    found: list[str] = []
    for key, rx in PRODUCT_RULES:
        if rx.search(text) and key not in found:
            found.append(key)
    return found or ["GENEL"]


def classify_tip(text: str, locked: bool, is_quote: bool) -> str:
    if locked:
        return "kilitli"
    if FLOOD_MARKERS.search(text):
        return "flood"
    if is_quote:
        if re.search(r"demiştim|alıntı|quote", text, re.I) or len(text) < 80:
            return "hatırlatma"
        return "hatırlatma+olay"
    if re.search(r"\$[\d,]+|seviye|hedef|göreceği|gorecegi|tarih.*\d", text, re.I):
        return "asıl tahmin"
    return "yorum"


def clean_raw_text(raw: str) -> str:
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        if JUNK_LINE.match(s):
            continue
        if re.match(r"^\d+$", s):
            continue
        if STATUS_URL.search(s) and len(s) < 80:
            continue
        lines.append(s)
    return "\n".join(lines)


def split_into_blocks(raw: str) -> list[str]:
    """Ham metni tweet bloklarına böl."""
    # 1) En güvenilir: her "Ekonomi Koç" / @ekonomikocu başlığı = yeni tweet
    chunks = re.split(
        r"(?=(?:Ekonomi\s*Koç|@ekonomikocu)(?:\s*[\n·]|\s*$))",
        raw,
        flags=re.I,
    )
    blocks = [c.strip() for c in chunks if len(c.strip()) > 35]
    if len(blocks) >= 2:
        return blocks

    # 2) Status URL sonundan geriye doğru parça
    url_iter = list(STATUS_URL.finditer(raw))
    if url_iter:
        blocks = []
        prev_end = 0
        for match in url_iter:
            chunk = raw[prev_end : match.end()].strip()
            prev_end = match.end()
            if len(chunk) > 25:
                blocks.append(chunk)
        tail = raw[prev_end:].strip()
        if len(tail) > 25:
            if blocks and LOCKED_MARKERS.search(tail) and not STATUS_URL.search(tail):
                blocks[-1] = blocks[-1] + "\n" + tail
            else:
                blocks.append(tail)
        if blocks:
            return blocks

    chunks = re.split(
        r"(?=\n(?:\d{1,2}:\d{2}\s*·\s*)?\d{1,2}\s+(?:Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Eyl|Eki|Kas|Ara|Jun|May|Apr)\b)",
        raw,
        flags=re.I,
    )
    blocks = [c.strip() for c in chunks if len(c.strip()) > 40]
    if blocks:
        return blocks

    blocks = [b.strip() for b in re.split(r"\n{2,}", raw) if len(b.strip()) > 40]
    return blocks if blocks else [raw.strip()]


def parse_block(block: str) -> TweetRecord | None:
    if len(block.strip()) < 15:
        return None

    ids = STATUS_URL.findall(block)
    tweet_id = ids[0] if ids else None
    locked = bool(LOCKED_MARKERS.search(block))

    block = clean_raw_text(block)
    if len(block) < 10 and not locked:
        return None
    dt, date_label = try_parse_date(block)

    # Tweet metni: tarih satırından sonra gelen içerik (gürültüyü at)
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    start_idx = 0
    for i, s in enumerate(lines):
        if has_absolute_date(s):
            start_idx = i + 1
            break

    text_lines = []
    for s in lines[start_idx:]:
        if JUNK_LINE.match(s) or STATUS_URL.search(s):
            continue
        if RELATIVE_TIME.match(s.replace("·", "").strip()):
            continue
        if re.match(r"^[\d,\.\s]+$", s):
            continue
        if has_absolute_date(s) and len(s) < 30:
            continue
        if len(s) < 8 and not re.search(r"#|\$", s):
            continue
        text_lines.append(s)

    text = " ".join(text_lines).strip()
    text = re.sub(r"\s+", " ", text)

    if not text and not locked:
        return None

    # Yalnızca göreli süre ve mutlak tarih yoksa — zayıf kayıt, atla (isteğe bağlı sıkı mod)
    if date_label.startswith("göreli") and not tweet_id:
        return None

    is_quote = bool(
        re.search(r"Quote\b|alıntıladı|retweet|reposted", block, re.I)
        or re.search(r"@[A-Za-z0-9_]+\s+·", block)
    )

    products = classify_products(text or block)
    tip = classify_tip(text or block, locked, is_quote)

    return TweetRecord(
        tweet_id=tweet_id,
        dt=dt,
        date_label=date_label,
        locked=locked,
        text=text if not locked else (text or ""),
        products=products,
        tip=tip,
        is_quote=is_quote,
        raw_excerpt=block[:200],
    )


def explode_multi_tweet_blocks(block: str) -> list[str]:
    """Tek yapıştırmada birden fazla status URL varsa alt bloklara ayır."""
    matches = list(STATUS_URL.finditer(block))
    if len(matches) <= 1:
        return [block]

    parts: list[str] = []
    prev = 0
    for m in matches:
        chunk = block[prev : m.end()].strip()
        prev = m.end()
        if len(chunk) > 25:
            parts.append(chunk)
    tail = block[prev:].strip()
    if tail and LOCKED_MARKERS.search(tail):
        parts.append(tail)
    return parts if parts else [block]


def parse_ham_veri(content: str) -> list[TweetRecord]:
    content = content.replace("\r\n", "\n").strip()
    # Yorum satırlarını at (boş ham_veri.txt şablonu)
    content = "\n".join(
        ln for ln in content.splitlines() if ln.strip() and not ln.strip().startswith("#")
    ).strip()
    if not content:
        return []

    blocks = split_into_blocks(content)
    records: list[TweetRecord] = []
    seen_ids: set[str] = set()

    for block in blocks:
        for sub in explode_multi_tweet_blocks(block):
            rec = parse_block(sub)
            if not rec:
                continue
            if rec.tweet_id:
                if rec.tweet_id in seen_ids:
                    continue
                seen_ids.add(rec.tweet_id)
            records.append(rec)

    # Kronolojik: yeniden eskiye (profil akışı genelde böyle kopyalanır)
    records.sort(key=lambda r: r.sort_key(), reverse=True)
    return records


def extract_existing_ids(md: str) -> set[str]:
    return set(re.findall(r"\*\*(\d{16,22})\s*\|", md))


def extract_progress(md: str) -> dict:
    prog = {
        "newest_id": None,
        "oldest_label": None,
        "range": None,
    }
    m = re.search(r"En son/en yeni tweet_id:\*\*\s*(\d+)", md)
    if m:
        prog["newest_id"] = m.group(1)
    m = re.search(r"En eski işlenen:\*\*\s*([^\n]+)", md)
    if m:
        prog["oldest_label"] = m.group(1).strip()
    m = re.search(r"işlenen aralık:\*\*\s*([^\n]+)", md)
    if m:
        prog["range"] = m.group(1).strip()
    return prog


def bump_version(md: str) -> str:
    def repl(m: re.Match) -> str:
        ver = m.group(1)
        if "." in ver:
            major, minor = ver.split(".", 1)
            try:
                return f"**Versiyon:** v{major}.{int(minor) + 1}"
            except ValueError:
                pass
        return f"**Versiyon:** v{ver}.1"

    return re.sub(r"\*\*Versiyon:\*\*\s*v([\d.]+)", repl, md, count=1)


def insert_into_section(md: str, section_header: str, new_lines: list[str]) -> str:
    """Belirli ### altına madde ekle (bölüm sonuna, bir sonraki ### öncesi)."""
    if not new_lines:
        return md

    # Sonraki ### veya ## 6 sınırı
    pattern = re.compile(
        rf"({re.escape(section_header)}\s*\n)(.*?)(?=\n### |\n---\n\n## 6\.)",
        re.DOTALL,
    )
    m = pattern.search(md)
    if not m:
        # Bölüm yoksa Genel'e ekle veya oluştur
        if section_header != PRODUCT_SECTIONS["GENEL"]:
            return insert_into_section(md, PRODUCT_SECTIONS["GENEL"], new_lines)
        # Section 5 sonuna yeni alt başlık
        insert_at = md.find(SECTION_6_MARKER)
        block = section_header + "\n" + "\n".join(new_lines) + "\n\n"
        return md[:insert_at] + block + md[insert_at:]

    header, body = m.group(1), m.group(2)
    addition = "\n".join(new_lines) + "\n"
    new_body = body.rstrip() + "\n" + addition
    return md[: m.start()] + header + new_body + md[m.end() :]


def update_section_5(md: str, records: list[TweetRecord], existing_ids: set[str]) -> tuple[str, list[TweetRecord]]:
    added: list[TweetRecord] = []
    by_section: dict[str, list[str]] = {k: [] for k in PRODUCT_SECTIONS}

    for rec in records:
        if rec.tweet_id and rec.tweet_id in existing_ids:
            continue
        line = rec.hafiza_line()
        for prod in rec.products:
            sec = PRODUCT_SECTIONS.get(prod, PRODUCT_SECTIONS["GENEL"])
            if line not in by_section[prod]:
                by_section[prod].append(line)
        added.append(rec)
        if rec.tweet_id:
            existing_ids.add(rec.tweet_id)

    new_md = md
    for prod, lines in by_section.items():
        if lines:
            header = PRODUCT_SECTIONS[prod]
            new_md = insert_into_section(new_md, header, lines)

    return new_md, added


def update_section_9(md: str, added: list[TweetRecord], existing_prog: dict) -> str:
    if not added:
        return md

    dated = [r for r in added if r.dt]
    if not dated:
        return md

    newest = max(dated, key=lambda r: r.dt)
    oldest = min(dated, key=lambda r: r.dt)

    def fmt_dt(r: TweetRecord) -> str:
        if r.dt:
            return r.dt.strftime("%d %b %Y %H:%M").replace("Jun", "Haziran").replace("May", "Mayıs")
        return r.date_label

    new_newest_id = newest.tweet_id or existing_prog.get("newest_id")
    batch_newest = fmt_dt(newest)
    batch_oldest = fmt_dt(oldest)

    # Aralık metnini güncelle
    range_line = f"- **Bu oturumda işlenen aralık:** {batch_newest} (UTC) → {batch_oldest} (UTC). Ham_veri oturumu eklendi."
    if existing_prog.get("range"):
        range_line = (
            f"- **Bu oturumda işlenen aralık:** {existing_prog['range'].split('→')[0].strip()} → "
            f"{batch_oldest} (UTC). Geriye doğru devam."
        )

    id_line = f"- **En son/en yeni tweet_id:** {new_newest_id or '—'} — profil tepesi (değişmediyse önceki geçerli)."
    oldest_line = f"- **En eski işlenen:** {oldest.date_label} (ham_veri güncellemesi)."
    next_line = (
        f"- **SONRAKİ HEDEF:** {oldest.date_label}'den GERİYE devam. "
        "Yeni ham_veri.txt yapıştır → hafiza_guncelle.py tekrar çalıştır."
    )

    section = re.search(
        rf"({re.escape(SECTION_9_MARKER)}.*?)(?=\n## CİHAZ)",
        md,
        re.DOTALL,
    )
    if not section:
        return md

    body = section.group(1)
    body = re.sub(r"- \*\*Bu oturumda işlenen aralık:\*\*.*", range_line, body)
    if new_newest_id:
        body = re.sub(r"- \*\*En son/en yeni tweet_id:\*\*.*", id_line, body)
    body = re.sub(r"- \*\*En eski işlenen:\*\*.*", oldest_line, body)
    body = re.sub(r"- \*\*SONRAKİ HEDEF:\*\*.*", next_line, body)

    return md[: section.start()] + body + md[section.end() :]


def update_section_7_date(md: str) -> str:
    today = datetime.now().strftime("%d %B %Y").replace("June", "Haziran").replace("May", "Mayıs")
    return re.sub(
        r"(## 7\. GÜNCEL HARİTA \()[^)]+(\))",
        rf"\g<1>{today}\g<2>",
        md,
        count=1,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="ham_veri.txt → ekonomikocu_hafiza_v1.md")
    parser.add_argument("--dry-run", action="store_true", help="Dosyaya yazma, sadece önizleme")
    parser.add_argument("--ham", type=Path, default=HAM_VERI, help="Ham veri dosyası")
    parser.add_argument("--hafiza", type=Path, default=HAFIZA, help="Hafıza markdown dosyası")
    args = parser.parse_args()

    if not args.ham.exists():
        print(f"Eksik: {args.ham}")
        print("X profilinden kopyalayıp ham_veri.txt oluşturun.")
        return 1

    if not args.hafiza.exists():
        print(f"Eksik: {args.hafiza}")
        return 1

    raw = args.ham.read_text(encoding="utf-8", errors="replace")
    records = parse_ham_veri(raw)

    if not records:
        print("Tweet çıkarılamadı. ham_veri.txt içeriğini kontrol edin.")
        print("İpucu: Profilde birkaç tweet görünürken sadece o bölümü seçip kopyalayın;")
        print("mümkünse her tweetin altındaki 'x.com/.../status/ID' satırı da kopyada olsun.")
        return 1

    md = args.hafiza.read_text(encoding="utf-8")
    existing_ids = extract_existing_ids(md)
    prog = extract_progress(md)

    print(f"Ham metinden {len(records)} tweet ayrıştırıldı.\n")

    new_md, added = update_section_5(md, records, existing_ids)
    new_md = update_section_9(new_md, added, prog)
    new_md = bump_version(new_md)
    new_md = update_section_7_date(new_md)

    print(f"Yeni eklenecek: {len(added)} tweet")
    print(f"Zaten kayıtlı (atlandı): {len(records) - len(added)}\n")

    for rec in added:
        print(rec.hafiza_line()[:120] + ("…" if len(rec.hafiza_line()) > 120 else ""))

    if args.dry_run:
        print("\n[--dry-run] Hafıza dosyası yazılmadı.")
        return 0

    if not added:
        print("\nEklenecek yeni kayıt yok.")
        return 0

    backup = args.hafiza.with_suffix(".md.bak")
    shutil.copy2(args.hafiza, backup)
    args.hafiza.write_text(new_md, encoding="utf-8")
    print(f"\nGüncellendi: {args.hafiza}")
    print(f"Yedek: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
