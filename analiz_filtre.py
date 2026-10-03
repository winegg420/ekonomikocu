#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gunluk analiz filtresi: yeni tweet'lerden SADECE okunmasi gerekenleri ayiklar.

Tamamen cevrimdisi, muhafazakar (supheli = gecer). Okuma/analiz scriptin isi degil.

Kullanim:
  python analiz_filtre.py                       # analiz_sinir.json'dan sonrasini isle
  python analiz_filtre.py --sinir-guncelle      # sinirı bu kosunun son tweet'ine ilerlet (elle onay)
  python analiz_filtre.py --kontrol             # analiz_elenenler.jsonl'den rastgele 10 satir
  python analiz_filtre.py --baslangic 2026-09-22 --bitis 2026-10-03T23:59:59 \
      --haric-gun 2026-09-30 --okunmusu-yoksay  # geriye donuk test (sinir dosyasina dokunmaz)

Ciktilar: analiz_kuyrugu.jsonl, gorsel_kuyrugu.jsonl (her kosuda yeniden yazilir),
          analiz_elenenler.jsonl (yalnizca EKLENIR, tweet_id ile tekrar kontrolu).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "99_BOT_ARSIV" / "kod"))
try:
    from grafik_filtre import is_irrelevant_media_url  # hisse logosu / emoji / kart
except Exception:  # modul yoksa filtre calismaya devam eder
    def is_irrelevant_media_url(url: str) -> bool:
        return False

CEKILEN = ROOT / "cekilen_tweetler.jsonl"
ABONE = ROOT / "07_ABONE_TWEETLER.jsonl"
ABONE_ETIKET = ROOT / "jev_abone_etiketler.jsonl"
GORSEL_OKUNMUS = ROOT / "gorsel_analiz.jsonl"
SINIR = ROOT / "analiz_sinir.json"
ELENENLER = ROOT / "analiz_elenenler.jsonl"
KUYRUK = ROOT / "analiz_kuyrugu.jsonl"
GORSEL_KUYRUK = ROOT / "gorsel_kuyrugu.jsonl"

ZINCIR_DK = 30
BAGLAM_ONCE, BAGLAM_SONRA = 5, 3
OLASI_URUN_GUN = 30
KESIN_MIN_KAYNAK = 3
KANON_MIN = 3  # sifirlari atilmis sayi en az 3 hane (2840 ~ 28.4 ~ 28400 -> 284)
OLASI_URUN_MAX = 3
ABONE_YAZAR_ESIK = 0.70

# ---------------------------------------------------------------- desenler
# Turkce buyuk/kucuk harf: normalize() sonrasi kucuk harfle calisilir.
URUN_RX = re.compile(
    r"(?<![a-zçğıöşü0-9])(?:btc|bitcoin|eth|ethereum|altın|altin|gümüş|gumus|nasdaq|ndx|"
    r"dax|dow|us30|us500|spx|s&p|petrol|brent|wti|dxy|jpy|eur|gbp|usd|try|chf|cad|aud|nzd|"
    r"xau|xag|bist|xu100|doge|xrp|avax|ada|link|sui|nikkei|dolar|euro|sterlin|yen|gram|"
    r"vix|us10y|faiz|otherss?\.d|spgsci)",
    re.I,
)
SEVIYE_RX = re.compile(
    r"(?<![a-zçğıöşü])(?:üstü|ustu|altı|alti|üstünde|altında|altinda|stop|destek|direnç|direnc|"
    r"hedef|long|short|öğreti|ogreti|kesişim|kesisim|pivot|seviye|kırıl|kiril|robot|"
    r"yatay|trend|kanal|band|bant|fitil|temas|kapanış|kapanis|satış|satis|alış|alis)",
    re.I,
)
AYLAR_RX = re.compile(
    r"(?<![a-zçğıöşü])(?:ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|"
    r"eylül|eylul|ekim|kasım|kasim|aralık|aralik|eyl|ağu|agu)(?![a-zçğıöşü]{4,})|"
    r"(?<!\d)(?:19|20)\d{2}(?!\d)",
    re.I,
)
SAYI_RX = re.compile(r"\d[\d.,]*")
YIL_RX = re.compile(r"^(?:19|20)\d{2}$")
ESKI_YIL_RX = re.compile(r"(?<!\d)(?:19\d{2}|20(?:0\d|1\d|2[0-5]))(?!\d)")
ESKI_KANIT_RX = re.compile(
    r"anlattım|anlattim|yazmıştım|yazmistim|göstermiştim|gostermistim|demiştim|demistim|"
    r"söylemiştim|soylemistim|paylaşmıştım|paylasmistim|uyarmıştım|uyarmistim|"
    r"hatırlat|hatirlat|bakın|bakin",
    re.I,
)
URL_RX = re.compile(r"https?://\S+|www\.\S+")
MENTION_RX = re.compile(r"@\w+")
RT_RX = re.compile(r"^\s*RT\s+@", re.I)
SOSYAL_KOK = (
    "selam", "merhaba", "günaydın", "gunaydin", "iyi", "teşekkür", "tesekkur", "sağol", "sagol",
    "sağ", "eyvallah", "dua", "rahmet", "başsağlığı", "bassagligi", "taziye", "allah", "amin",
    "inşallah", "insallah", "maşallah", "masallah", "hayırlı", "hayirli", "bol", "kazanç", "kazanc",
    "aynen", "helal", "tebrik", "kutla", "geçmiş", "gecmis", "kolay", "sağlık", "saglik", "saygı",
    "saygi", "sevgi", "öyle", "oyle", "doğru", "dogru", "evet", "tamam", "olsun", "anladım",
    "anladim", "kısmen", "kismen", "gerçekten", "gercekten", "katılıyorum", "katiliyorum",
)
# Sosyal cevapta tolere edilen dolgu sozcukleri (icerik sayilmaz)
SOSYAL_DOLGU = (
    "kardeş", "kardes", "dost", "arkadaş", "arkadas", "abi", "hocam", "hoca", "canım", "canim",
    "sen", "siz", "çok", "cok", "de", "da", "ki", "bir", "ya", "yani", "ama",
)
SOSYAL_MAX_ICERIK = 0  # sosyal/dolgu disinda kalan sozcuk sayisi (>0 ise tweet okunur)
SOSYAL_MAX_TOKEN = 8
SOSYAL_MAX_KARAKTER = 70


def normalize(s: str) -> str:
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def temiz_metin(s: str) -> str:
    s = URL_RX.sub(" ", s or "")
    s = MENTION_RX.sub(" ", s)
    return s


def tokenlar(s: str) -> list[str]:
    return re.findall(r"[#\w][\w'’]*", temiz_metin(normalize(s)), re.UNICODE)


# ---------------------------------------------------------------- g/c
def jsonl_oku(p: Path) -> list[dict]:
    out: list[dict] = []
    try:
        with open(p, encoding="utf-8") as f:
            for i, ln in enumerate(f, 1):
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    print(f"[uyari] {p.name}:{i} bozuk satir atlandi", file=sys.stderr)
    except OSError as e:
        print(f"[uyari] {p.name} okunamadi: {e}", file=sys.stderr)
    return out


def jsonl_yaz(p: Path, rows: list[dict]) -> None:
    try:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[HATA] {p.name} yazilamadi: {e}", file=sys.stderr)
        raise


def jsonl_ekle(p: Path, rows: list[dict]) -> None:
    if not rows:
        return
    try:
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[HATA] {p.name} eklenemedi: {e}", file=sys.stderr)
        raise


def dt_parse(s: str | None):
    try:
        return datetime.fromisoformat(s) if s else None
    except ValueError:
        return None


# ---------------------------------------------------------------- sinyaller
def sayi_ozellikleri(text: str) -> tuple[bool, bool]:
    """(3+ haneli sayi var, yil olmayan 3+ haneli sayi var)"""
    uc, yil_disi = False, False
    for m in SAYI_RX.findall(temiz_metin(text)):
        m = m.rstrip(".,")
        if sum(c.isdigit() for c in m) < 3:
            continue
        uc = True
        if not YIL_RX.match(m):
            yil_disi = True
    return uc, yil_disi


def sinyaller(text: str) -> dict:
    n = normalize(text)
    uc, yil_disi = sayi_ozellikleri(text)
    return {
        "sayi3": uc,
        "sayi3_yil_disi": yil_disi,
        "urun": bool(URUN_RX.search(n)),
        "seviye_kelime": bool(SEVIYE_RX.search(n)),
        "tarih": bool(AYLAR_RX.search(n)),
    }


def sinyal_var(sg: dict) -> bool:
    return sg["sayi3"] or sg["urun"] or sg["seviye_kelime"] or sg["tarih"]


URUN_HARITA = {
    "BTC": ("btc", "bitcoin"), "ETH": ("eth", "ethereum"), "ALTIN": ("altın", "altin", "xau", "gold"),
    "GUMUS": ("gümüş", "gumus", "xag"), "NASDAQ": ("nasdaq", "ndx", "nq"), "DAX": ("dax",),
    "DOW": ("dow", "us30"), "PETROL": ("petrol", "brent", "wti"), "DXY": ("dxy",),
    "JPY": ("jpy", "yen"), "EUR": ("eur", "euro"), "GBP": ("gbp", "sterlin"), "SPX": ("spx", "us500"),
    "BIST": ("bist", "xu100"), "DOGE": ("doge",), "DOLAR": ("dolar",), "TRY": ("try",),
}
PARA_EKI = ("usd", "usdt", "try", "tl", "eur", "gbp", "jpy", "chf", "cad", "aud", "nzd", "gr", "g")
_ADLAR = sorted((ad, k) for k, v in URUN_HARITA.items() for ad in v)
TAM_ESLESME_MIN = {"nq", "eur", "try", "dow", "dax", "gold", "yen", "eth", "btc"}


def urunler(text: str) -> list[str]:
    """SIKI urun tespiti (olasi_urun ve urunsuz-seviye karari icin): sozcuk basi + sozluk.
    Gevsek URUN_RX yalnizca 'tut/ele' karari icindir ('yeni' -> 'yen' tuzagi burada yok)."""
    bulunan = set()
    for w in tokenlar(text):
        w = re.split(r"['’]", w.lstrip("#"))[0]
        for ad, k in _ADLAR:
            if not w.startswith(ad):
                continue
            kalan = w[len(ad):]
            while kalan and kalan not in ("",):
                for e in PARA_EKI:
                    if kalan.startswith(e):
                        kalan = kalan[len(e):]
                        break
                else:
                    break
            if kalan == "" or (ad not in TAM_ESLESME_MIN and len(ad) >= 4):
                bulunan.add(k)
    return sorted(bulunan)


def sosyal_mi(text: str, sg: dict) -> bool:
    if sinyal_var(sg):
        return False
    t = temiz_metin(text).strip()
    tok = [w.lstrip("#") for w in tokenlar(text)]
    if not tok or len(tok) > SOSYAL_MAX_TOKEN or len(t) > SOSYAL_MAX_KARAKTER:
        return False
    sosyal = [w for w in tok if w.startswith(SOSYAL_KOK)]
    if not sosyal:
        return False
    icerik = [w for w in tok if not w.startswith(SOSYAL_KOK) and not w.startswith(SOSYAL_DOLGU)]
    return len(icerik) <= SOSYAL_MAX_ICERIK


def eleme_nedeni(row: dict, text: str, sg: dict) -> str | None:
    """None = tut. Gorselli tweet'e asla cagirilmaz."""
    if RT_RX.match(text or ""):
        return "rt"
    tok = tokenlar(text)
    if not tok:
        return "bos/emoji" if not row.get("quote_of") else None
    if len(tok) == 1:
        t = tok[0].lstrip("#")
        if t.isdigit() and not YIL_RX.match(t) and len(t) >= 3:
            return None  # yalniz sayi: seviye olabilir
        return "tek_kelime"
    if sosyal_mi(text, sg):
        return "selam/tesekkur"
    return None


def kayit_sebepleri(row: dict, sg: dict, gorselli: bool) -> list[str]:
    s = []
    if gorselli:
        s.append("gorsel")
    for k, ad in (("sayi3", "sayi3+"), ("urun", "urun"), ("seviye_kelime", "seviye_kelime"), ("tarih", "tarih")):
        if sg[k]:
            s.append(ad)
    return s or ["diger"]


# ---------------------------------------------------------------- baglam / olasi urun
def kanon_sayi(tok: str) -> str:
    d = re.sub(r"\D", "", tok)
    return d.rstrip("0") if d.strip("0") else ""


def urunsuz_seviye_sayilari(text: str) -> list[str]:
    out = []
    for m in SAYI_RX.findall(temiz_metin(text)):
        m = m.rstrip(".,")
        if sum(c.isdigit() for c in m) >= 3 and not YIL_RX.match(m):
            out.append(m)
    return out


def olasi_urun_bul(sayilar: list[str], dt: datetime, tid: str, koc: list[dict]) -> list[dict]:
    alt = dt - timedelta(days=OLASI_URUN_GUN)
    sonuc: dict[str, dict] = {}
    for sayi in sayilar:
        kn = kanon_sayi(sayi)
        if len(kn) < KANON_MIN:
            continue  # '100','1300' gibi yuvarlak sayilar cok genis eslesir
        for r in koc:
            if r["tweet_id"] == tid or not (alt <= r["_dt"] < dt):
                continue
            ms = [m for m in SAYI_RX.findall(temiz_metin(r.get("text") or "")) if kanon_sayi(m.rstrip(".,")) == kn]
            if not ms:
                continue
            for u in urunler(r.get("text") or ""):
                e = sonuc.setdefault(u, {"urun": u, "kaynak_tweet_id": [], "tam_eslesme": 0})
                if r["tweet_id"] not in e["kaynak_tweet_id"]:
                    e["kaynak_tweet_id"].append(r["tweet_id"])
                    if sayi in ms:
                        e["tam_eslesme"] += 1
    return sorted(sonuc.values(), key=lambda e: (-e["tam_eslesme"], -len(e["kaynak_tweet_id"])))[:OLASI_URUN_MAX]


# ---------------------------------------------------------------- ana akis
def sinir_oku() -> dict:
    try:
        return json.loads(SINIR.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def sinir_yaz(son_tur: int, zaman: str) -> None:
    try:
        SINIR.write_text(
            json.dumps({"son_tur": son_tur, "son_tweet_zamani": zaman}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as e:
        print(f"[HATA] sinir yazilamadi: {e}", file=sys.stderr)
        raise


def kontrol_modu() -> int:
    rows = jsonl_oku(ELENENLER)
    if not rows:
        print("analiz_elenenler.jsonl bos/yok.")
        return 0
    print(f"Toplam elenen: {len(rows)} - rastgele 10:")
    for r in random.sample(rows, min(10, len(rows))):
        print(f"- {r.get('datetime')} [{r.get('neden')}] {r.get('tweet_id')}: {(r.get('text') or '')[:140]!r}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kontrol", action="store_true", help="elenenlerden rastgele 10 satir yazdir")
    ap.add_argument("--sinir-guncelle", action="store_true", help="siniri bu kosunun son tweet'ine ilerlet")
    ap.add_argument("--tur", type=int, help="--sinir-guncelle ile yeni tur no (varsayilan: son_tur+1)")
    ap.add_argument("--baslangic", help="sinir yerine bu zamandan (dahil) basla - test")
    ap.add_argument("--bitis", help="bu zamana (dahil) kadar - test")
    ap.add_argument("--haric-gun", action="append", default=[], help="YYYY-MM-DD gunu atla (tekrarlanabilir)")
    ap.add_argument("--okunmusu-yoksay", action="store_true", help="gorsel_analiz.jsonl'i yoksay - test")
    a = ap.parse_args()

    if a.kontrol:
        return kontrol_modu()

    sinir = sinir_oku()
    if a.baslangic:
        alt, alt_dahil = dt_parse(a.baslangic), True
    else:
        alt, alt_dahil = dt_parse(sinir.get("son_tweet_zamani")), False
        if alt is None:
            print("[HATA] analiz_sinir.json yok/bozuk; --baslangic ver.", file=sys.stderr)
            return 2
    ust = dt_parse(a.bitis) if a.bitis else None

    cekilen = jsonl_oku(CEKILEN)
    abone = jsonl_oku(ABONE)
    if not cekilen:
        print("[HATA] cekilen_tweetler.jsonl okunamadi.", file=sys.stderr)
        return 2

    # abone atifi: Jev etiketi varsa yazar alanina bak
    etiket = {r["tweet_id"]: r for r in jsonl_oku(ABONE_ETIKET) if r.get("tweet_id")}
    abone_ids = {r["tweet_id"] for r in abone}

    def koc_degil_belirle(r: dict) -> tuple[bool, bool]:
        """(koc_degil, atif_belirsiz)"""
        if r["tweet_id"] in abone_ids or r.get("abone_ozel") or r.get("abone_metin") or r.get("kayit_tipi") == "abone":
            e = etiket.get(r["tweet_id"])
            if e and e.get("yazar") == "koc" and (e.get("yazar_g") or 0) >= ABONE_YAZAR_ESIK:
                return False, False
            if e and e.get("yazar") == "abone" and (e.get("yazar_g") or 0) >= ABONE_YAZAR_ESIK:
                return True, False
            return True, True
        return False, False

    tum: dict[str, dict] = {}
    for r in abone + cekilen:  # cekilen oncelikli
        tid = str(r.get("tweet_id") or "")
        d = dt_parse(r.get("datetime"))
        if not tid or d is None:
            continue
        r = dict(r)
        r["tweet_id"], r["_dt"] = tid, d
        tum[tid] = r
    koc_satirlari = [r for r in tum.values() if not koc_degil_belirle(r)[0]]
    koc_satirlari.sort(key=lambda r: r["_dt"])
    sirali_hepsi = sorted(tum.values(), key=lambda r: r["_dt"])

    hariclar = set(a.haric_gun)
    hedef = [
        r for r in sirali_hepsi
        if (r["_dt"] >= alt if alt_dahil else r["_dt"] > alt)
        and (ust is None or r["_dt"] <= ust)
        and r["_dt"].strftime("%Y-%m-%d") not in hariclar
    ]

    okunmus_dosya: set[str] = set()
    if not a.okunmusu_yoksay:
        for g in jsonl_oku(GORSEL_OKUNMUS):
            if g.get("dosya"):
                okunmus_dosya.add(str(g["dosya"]).replace("\\", "/"))

    def gorseller(r: dict) -> list[str]:
        urls = list(r.get("media_urls") or [])
        files = [str(f).replace("\\", "/") for f in (r.get("media_files") or [])]
        out = []
        for i, f in enumerate(files):
            if i < len(urls) and is_irrelevant_media_url(urls[i]):
                continue
            out.append(f)
        return out

    # 1) metin filtresi
    elenen: list[dict] = []
    tutulan: list[dict] = []
    for r in hedef:
        text = r.get("text") or ""
        sg = sinyaller(text)
        gorselli = bool(gorseller(r))
        neden = None if gorselli else eleme_nedeni(r, text, sg)
        if neden:
            elenen.append({"tweet_id": r["tweet_id"], "datetime": r["datetime"], "neden": neden, "text": text})
            continue
        r["_sg"], r["_gorselli"] = sg, gorselli
        r["_koc_degil"], r["_atif_belirsiz"] = koc_degil_belirle(r)
        tutulan.append(r)

    # 2) analiz tweet'leri (madde 5'e uyan, Koc'un) -> zincir zaman/thread cekirdegi
    analiz_koc = [r for r in tutulan if not r["_koc_degil"] and sinyal_var(r["_sg"])]
    # zincir icin tam arsivdeki Koc analiz tweet'leri de gecerli (sinir/aralik kenari)
    zincir_dt = [r["_dt"] for r in analiz_koc]
    zincir_roots = {r.get("thread_root") for r in analiz_koc if r.get("thread_root")}
    zincir_roots |= {r["tweet_id"] for r in analiz_koc if r.get("thread_root")}

    def zincirde(r: dict) -> bool:
        if r.get("thread_root") and r["thread_root"] in zincir_roots:
            return True
        for d in zincir_dt:
            if d != r["_dt"] and abs((r["_dt"] - d).total_seconds()) <= ZINCIR_DK * 60:
                return True
        return False

    # 3) gorsel kuyrugu
    gorsel_kuyruk: list[dict] = []
    for r in tutulan:
        gs = gorseller(r)
        if not gs:
            continue
        text = r.get("text") or ""
        sg = r["_sg"]
        nedenler = []
        if not r["_koc_degil"]:
            nedenler.append("koc_gorseli")
        if zincirde(r):
            nedenler.append("zincir")
        if r["_koc_degil"] and (sg["urun"] or sg["sayi3_yil_disi"] or sg["seviye_kelime"]):
            nedenler.append("urun_seviye")
        if not nedenler:
            continue
        eski = bool(ESKI_YIL_RX.search(text) or ESKI_KANIT_RX.search(text))
        for f in gs:
            if f in okunmus_dosya:
                continue
            kayit = {
                "tweet_id": r["tweet_id"],
                "datetime": r["datetime"],
                "dosya": f,
                "neden": nedenler[0],
                "nedenler": nedenler,
                "eski_kanit_olabilir": eski,
                "text": text,
            }
            if r["_koc_degil"]:
                kayit["koc_degil"] = True
            gorsel_kuyruk.append(kayit)

    # 4) analiz kuyrugu + urunsuz seviye cozumu
    idx_hepsi = {r["tweet_id"]: i for i, r in enumerate(sirali_hepsi)}
    kuyruk: list[dict] = []
    urunsuz = 0
    for r in tutulan:
        text = r.get("text") or ""
        sg = r["_sg"]
        k = {
            "tweet_id": r["tweet_id"],
            "datetime": r["datetime"],
            "text": text,
            "sebepler": kayit_sebepleri(r, sg, r["_gorselli"]),
        }
        if r["_gorselli"]:
            k["gorsel_dosya"] = gorseller(r)
        if r["_koc_degil"]:
            k["koc_degil"] = True
            if r["_atif_belirsiz"]:
                k["atif_belirsiz"] = True
        if not urunler(text) and sg["sayi3_yil_disi"]:
            urunsuz += 1
            k["urunsuz_seviye"] = True
            i = idx_hepsi[r["tweet_id"]]
            k["baglam"] = {
                "once": [
                    {"tweet_id": x["tweet_id"], "datetime": x["datetime"], "text": (x.get("text") or "")[:300]}
                    for x in sirali_hepsi[max(0, i - BAGLAM_ONCE):i]
                ],
                "sonra": [
                    {"tweet_id": x["tweet_id"], "datetime": x["datetime"], "text": (x.get("text") or "")[:300]}
                    for x in sirali_hepsi[i + 1:i + 1 + BAGLAM_SONRA]
                ],
            }
            adaylar = olasi_urun_bul(urunsuz_seviye_sayilari(text), r["_dt"], r["tweet_id"], koc_satirlari)
            for e in adaylar:
                e["kesin"] = False
            if len(adaylar) == 1 and adaylar[0]["tam_eslesme"] >= KESIN_MIN_KAYNAK:
                adaylar[0]["kesin"] = True
            for e in adaylar:
                e.pop("tam_eslesme", None)
            k["olasi_urun"] = adaylar
            k["kesin"] = bool(adaylar) and all(e["kesin"] for e in adaylar)
        kuyruk.append(k)

    # 5) yaz
    mevcut = {str(x.get("tweet_id")) for x in jsonl_oku(ELENENLER)}
    yeni_elenen = [e for e in elenen if e["tweet_id"] not in mevcut]
    jsonl_ekle(ELENENLER, yeni_elenen)
    jsonl_yaz(KUYRUK, kuyruk)
    jsonl_yaz(GORSEL_KUYRUK, gorsel_kuyruk)

    toplam = len(hedef)
    oran = (100 * len(elenen) / toplam) if toplam else 0.0
    print(f"Aralik     : {'>= ' if alt_dahil else '> '}{alt.isoformat()}" + (f" .. {ust.isoformat()}" if ust else ""))
    print(f"Toplam     : {toplam}")
    print(f"Elenen     : {len(elenen)} (%{oran:.1f}) - dosyaya yeni eklenen: {len(yeni_elenen)}")
    print(f"Tutulan    : {len(tutulan)}  -> analiz_kuyrugu.jsonl")
    print(f"Gorsel kuy.: {len(gorsel_kuyruk)} gorsel  -> gorsel_kuyrugu.jsonl")
    print(f"Urunsuz sev: {urunsuz}")

    if a.sinir_guncelle:
        if not hedef:
            print("[sinir] islenecek tweet yok, sinir degismedi.")
        else:
            son = max(r["datetime"] for r in hedef)
            tur = a.tur if a.tur else int(sinir.get("son_tur", 0)) + 1
            sinir_yaz(tur, son)
            print(f"[sinir] guncellendi: son_tur={tur}, son_tweet_zamani={son}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
