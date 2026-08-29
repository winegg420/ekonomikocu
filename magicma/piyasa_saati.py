"""
magicma/piyasa_saati.py

Bir sembolun ait oldugu piyasanin SU AN acik olup olmadigini soyler. Amac:
telegram_alarm.py'nin kapali piyasadaki semboller icin bosuna fiyat cekmesini
ve anlamsiz "temas" bildirimi gondermesini engellemek.

KAPSAM:
  - `bist.txt`        -> BIST: hafta ici 09:40-18:10 TSI. Hafta sonu kapali.
  - `abd_hisse.txt`   -> NYSE/Nasdaq: hafta ici 09:30-16:00 **New York saati**.
  - `forex_emtia.txt` -> FX/emtia 24/5 seansi: Pazar 17:00 New York'ta acilir,
    Cuma 17:00 New York'ta kapanir. TSI karsiligi DST ile kayar (yaz Pzt 00:00 -
    Cmt 00:00, kis Pzt 01:00 - Cmt 01:00). **Hafta sonu KAPALI.**
  - `endeks_faiz.txt` -> ayni 24/5 seans (SPX/NDX/DJI/VIX/US10Y hafta sonu islem
    gormez). Istisna: XU100/XU030 BIST saatine tabidir (SEMBOL_PIYASA).
  - `kripto.txt`, `gunun_hareketlileri.txt` -> HER ZAMAN ACIK, filtre yok (7/24).

BILINEN SINIRLAMALAR (kullanici karari, bu surumde bilerek yok):
  - Resmi tatil takvimi yok (BIST'te de ABD'de de). Yalnizca hafta ici/hafta
    sonu ayrimi yapilir; tatil gunu piyasa "acik" sayilir.
  - Yarim gun / erken kapanis seanslari dikkate alinmaz.
  - FX seansi tek blok sayilir; Pazar acilisindaki dusuk likidite ayirt edilmez.

ABD SAATI NEDEN SABIT DEGIL: ABD kendi yaz saati uygulamasini surdurdugu icin
TSI karsiligi yil icinde kayar (yaz 16:30-23:00, kis 17:30-00:00). Bu yuzden
tarih araliklari ASLA elle yazilmaz; saat `zoneinfo` ile New York yerel
saatine cevrilip 09:30-16:00 penceresiyle karsilastirilir. Boylece DST gecis
tarihleri her yil kendiliginden dogru olur.

YEDEK YOL: Windows'ta sistem saat dilimi veritabani yoktur, `zoneinfo` icin
`tzdata` paketi gerekir (requirements.txt'e eklendi). Paket yoksa modul
cokmez: Turkiye 2016'dan beri sabit UTC+3 oldugu icin dogrudan hesaplanir,
ABD icin de 2007'den beri gecerli DST KURALI (Mart'in 2. Pazari - Kasim'in
1. Pazari) uygulanir. Yani yine tarih hardcode edilmez, kural uygulanir.
"""

from datetime import date, datetime, time, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:                                   # Python < 3.9
    ZoneInfo = None

TSI_BOLGE = "Europe/Istanbul"
ABD_BOLGE = "America/New_York"

BIST_ACILIS, BIST_KAPANIS = time(9, 40), time(18, 10)      # TSI
ABD_ACILIS, ABD_KAPANIS = time(9, 30), time(16, 0)         # New York yerel saati

# FX 24/5 seansi — New York yerel saatiyle: Pazar 17:00 acilir, Cuma 17:00 kapanir.
FX_ACILIS, FX_KAPANIS = time(17, 0), time(17, 0)

# Sembol listesi dosyasi -> piyasa anahtari. Burada olmayan her dosya "serbest"
# (her zaman acik) sayilir.
DOSYA_PIYASA = {
    "bist.txt": "bist",
    "abd_hisse.txt": "abd",
    "forex_emtia.txt": "forex",
    "endeks_faiz.txt": "forex",
}

# Dosyasindan farkli piyasaya ait semboller. endeks_faiz.txt cogunlukla ABD
# endeksi/faizi (24/5 FX seansi) ama BIST endekslerini de tasiyor.
SEMBOL_PIYASA = {
    "XU100": "bist",
    "XU030": "bist",
}

_TSI_YEDEK = timezone(timedelta(hours=3))    # Turkiye 2016'dan beri sabit UTC+3


def _bolge(ad):
    """ZoneInfo dondurur; tzdata yoksa None (cagiran yedek yola duser)."""
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(ad)
    except Exception:
        return None


# --------------------------------------------------------------------------
# Saat dilimi yardimcilari
# --------------------------------------------------------------------------

def simdi_tsi():
    """Su anki Turkiye saati (timezone-aware)."""
    bolge = _bolge(TSI_BOLGE)
    return datetime.now(bolge) if bolge else datetime.now(_TSI_YEDEK)


def _kacinci_pazar(yil, ay, kacinci):
    """O ayin `kacinci` Pazar gununun tarihi (1 = ilk Pazar)."""
    ilk = date(yil, ay, 1)
    ilk_pazar = 1 + (6 - ilk.weekday()) % 7          # weekday: Pzt=0 ... Paz=6
    return date(yil, ay, ilk_pazar + 7 * (kacinci - 1))


def _abd_yaz_saati_mi(an_utc):
    """ABD DST kurali (2007'den beri): Mart'in 2. Pazari 02:00 yerel standart
    saatte baslar, Kasim'in 1. Pazari 02:00 yerel yaz saatinde biter."""
    yil = an_utc.year
    basla = datetime.combine(_kacinci_pazar(yil, 3, 2), time(7, 0), tzinfo=timezone.utc)
    bit = datetime.combine(_kacinci_pazar(yil, 11, 1), time(6, 0), tzinfo=timezone.utc)
    return basla <= an_utc < bit


def abd_yerel(an):
    """Verilen ani New York yerel saatine cevirir (tzdata yoksa DST kuraliyla)."""
    bolge = _bolge(ABD_BOLGE)
    if bolge:
        return an.astimezone(bolge)
    an_utc = an.astimezone(timezone.utc)
    saat = -4 if _abd_yaz_saati_mi(an_utc) else -5
    return an_utc.astimezone(timezone(timedelta(hours=saat)))


# --------------------------------------------------------------------------
# Piyasalar
# --------------------------------------------------------------------------

def _hafta_ici(an):
    return an.weekday() < 5                          # Pzt-Cum


def _aralikta(an, acilis, kapanis):
    return acilis <= an.time() <= kapanis


def bist_acik_mi(simdi=None):
    """BIST: hafta ici 09:40-18:10 TSI."""
    an = simdi or simdi_tsi()
    return _hafta_ici(an) and _aralikta(an, BIST_ACILIS, BIST_KAPANIS)


def abd_acik_mi(simdi=None):
    """NYSE/Nasdaq: hafta ici 09:30-16:00 New York saati (TSI karsiligi DST ile kayar)."""
    an = abd_yerel(simdi or simdi_tsi())
    return _hafta_ici(an) and _aralikta(an, ABD_ACILIS, ABD_KAPANIS)


def forex_acik_mi(simdi=None):
    """FX/emtia 24/5 seansi: Pazar 17:00 NY -> Cuma 17:00 NY.

    Hafta sonu (Cumartesi tum gun, Cuma 17:00 sonrasi, Pazar 17:00 oncesi)
    KAPALI. Saat New York yerel saatine cevrilerek karsilastirilir; boylece
    TSI karsiligi DST gecislerinde kendiliginden kayar.
    """
    an = abd_yerel(simdi or simdi_tsi())
    gun = an.weekday()                               # Pzt=0 ... Cmt=5, Paz=6
    if gun == 5:                                     # Cumartesi: tum gun kapali
        return False
    if gun == 6:                                     # Pazar: aksam acilis
        return an.time() >= FX_ACILIS
    if gun == 4:                                     # Cuma: aksam kapanis
        return an.time() < FX_KAPANIS
    return True                                      # Pzt-Per: kesintisiz


PIYASA_KONTROL = {
    "bist": bist_acik_mi,
    "abd": abd_acik_mi,
    "forex": forex_acik_mi,
}


PIYASA_ADI = {"bist": "BIST", "abd": "ABD", "forex": "FOREX"}


def _piyasa_coz(sembol_dosya_adi, sembol=None):
    """Sembol istisnasi varsa o kazanir, yoksa dosyanin piyasasi."""
    ozel = SEMBOL_PIYASA.get((sembol or "").strip().upper())
    if ozel:
        return ozel
    return DOSYA_PIYASA.get((sembol_dosya_adi or "").strip().lower())


def piyasa_acik_mi(sembol_dosya_adi, simdi=None, sembol=None):
    """Sembolun geldigi liste dosyasina gore piyasa acik mi?

    sembol_dosya_adi : "bist.txt" / "abd_hisse.txt" / "forex_emtia.txt" / ...
    simdi            : test icin TSI datetime; verilmezse su an
    sembol           : verilirse SEMBOL_PIYASA istisnasi dosyayi ezer
    Bilinmeyen veya filtresiz dosyalar icin DAIMA True (fail-open) — boylece
    yeni bir liste dosyasi eklendiginde sembolleri sessizce kaybolmaz.
    """
    piyasa = _piyasa_coz(sembol_dosya_adi, sembol)
    if not piyasa:
        return True
    return PIYASA_KONTROL[piyasa](simdi)


def piyasa_adi(sembol_dosya_adi, sembol=None):
    """Log/rapor icin okunur piyasa adi ('BIST'/'ABD'/'FOREX' veya None)."""
    return PIYASA_ADI.get(_piyasa_coz(sembol_dosya_adi, sembol))


def durum_ozeti(simdi=None):
    """{'BIST': ..., 'ABD': ..., 'FOREX': ...} — log satiri icin."""
    an = simdi or simdi_tsi()
    return {"BIST": bist_acik_mi(an), "ABD": abd_acik_mi(an),
            "FOREX": forex_acik_mi(an)}
