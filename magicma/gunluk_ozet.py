"""
magicma/gunluk_ozet.py

Her sabah 08:30 civari TEK bir "Gunluk Ozet" mesaji: gun icinde parca parca
gelen bildirimlerin (acik adaylar, karne, gunun hareketlileri, Koc takvimi,
confluence/mega) tek yerde toplanmis hali.

Yeni hesaplama mantigi YOK — hepsi mevcut dosyalardan sentezleme:
  - acik adaylar / son 7 gun karne : magicma/karne_kayitlari.json
  - gunun hareketlileri            : magicma/sembol_listesi/gunun_hareketlileri.txt
                                     (yuzdeler cryptobubbles'tan canli, alinamazsa "—")
  - Koc takvimi                    : 06_ANALIZ.md'de belgelenen 60 gunluk ic blok
                                     kurali — saf tarih matematigi, LLM yok
  - confluence / mega              : karne kayitlarindaki alanlar

Kullanim:
    py -3 magicma/gunluk_ozet.py --kuru      # gondermeden ekrana yaz
    py -3 magicma/gunluk_ozet.py             # gonderim penceresi/tekrar kontrolu ile
    py -3 magicma/gunluk_ozet.py --zorla     # pencere ve "bugun gonderildi" kontrolunu atla

Tekrar gonderme korumasi: magicma/gunluk_ozet_son_gonderim.json
(magicma_karne'deki haftalik ozet pattern'inin aynisi — ayri durum dosyasi).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fiyat_kontrol
import magicma_karne

REPO_KOK = fiyat_kontrol.REPO_KOK
DURUM_YOL = os.path.join(REPO_KOK, "magicma", "gunluk_ozet_son_gonderim.json")
HAREKETLI_YOL = os.path.join(REPO_KOK, "magicma", "sembol_listesi",
                             "gunun_hareketlileri.txt")
TSI = magicma_karne.TSI

# Gonderim penceresi (TSI). Task Scheduler gorevi 7/24 her 10 dk calistigi icin
# ozet, bu pencereye denk gelen ILK turda gider.
PENCERE_BASLANGIC = (8, 20)
PENCERE_BITIS = (8, 40)

HAREKETLI_ADET = 3          # mesajda gosterilecek en sert hareketli sembol sayisi
KARNE_GUN = 7               # "son N gun karne"

# --------------------------------------------------------------------------
# KOC TAKVIMI — 60 gunluk ic blok
# --------------------------------------------------------------------------
# 06_ANALIZ.md (20 Haziran kaydi, gorsel 2091191336762216911):
#   "Su an Haziran'in 3. haftasindayiz. 60 gun daha gecti mi, Agustos'un 3. haftasi."
# Bu, "Agustos 3. hafta" cagrisinin aritmetik turetimi — kehanet degil, sayma
# islemi. Cagri 20 Agustos'ta Koc tarafindan kapatildi ve TUTTU; bu yuzden son
# DOGRULANMIS donum noktasi 20 Agustos 2026 sabit referans olarak alinir.
# Sonraki duraklar bu referansa 60 gun eklenerek turetilir (~19 Ekim 2026).
KOC_REFERANS = datetime(2026, 8, 20, tzinfo=TSI)
KOC_BLOK_GUN = 60


def sonraki_donum(an=None, referans=KOC_REFERANS, blok=KOC_BLOK_GUN):
    """Bugunden SONRAKI ilk 60-gunluk donum noktasi ve kalan gun.

    Referans gecmiste kaldiysa 60'ar gun eklenerek ileri sarilir; referans
    henuz gelmediyse referansin kendisi dondurulur.
    Doner: (donum_tarihi, kalan_gun)
    """
    an = an or datetime.now(TSI)
    bugun = an.replace(hour=0, minute=0, second=0, microsecond=0)
    donum = referans.replace(hour=0, minute=0, second=0, microsecond=0)
    while donum <= bugun:
        donum += timedelta(days=blok)
    return donum, (donum - bugun).days


# --------------------------------------------------------------------------
# Veri toplama
# --------------------------------------------------------------------------

def acik_adaylar(kayitlar):
    """Acik kayitlari yone gore sayar. Doner: (toplam, long, short)."""
    acik = [k for k in kayitlar if k.get("durum") == "acik"]
    uzun = sum(1 for k in acik if k.get("yon") == "long")
    kisa = sum(1 for k in acik if k.get("yon") == "short")
    return len(acik), uzun, kisa


def son_gun_karne(kayitlar, gun=KARNE_GUN, an=None):
    """Son `gun` gunde KAPANAN sinyaller. Doner: (toplam, basarili, yuzde)."""
    an = an or datetime.now(TSI)
    sinir = an - timedelta(days=gun)
    kapanan = []
    for k in kayitlar:
        if k.get("durum") not in ("basarili", "basarisiz", "zaman_asimi"):
            continue
        zaman = magicma_karne._zaman_ayristir(k.get("sonuc_zamani"))
        if zaman is None or zaman < sinir:
            continue
        kapanan.append(k)
    basarili = sum(1 for k in kapanan if k["durum"] == "basarili")
    yuzde = (basarili / len(kapanan) * 100) if kapanan else 0.0
    return len(kapanan), basarili, yuzde


HAVUZ = 40                  # dosyadan alinip canli yuzdeyle yeniden siralanan aday sayisi


def hareketli_semboller(adet=HAREKETLI_ADET, yol=HAREKETLI_YOL, log=print):
    """Bugun en sert hareket eden sembolleri dondurur.

    Aday havuzu gunun_hareketlileri.txt'ten gelir (dosya |day| mutlak degerine
    gore AZALAN sirali uretilir). Dosyada yuzde YAZMAZ ve dosya gunde bir kez
    uretildigi icin sirasi BAYAT olabilir; bu yuzden havuzun yuzdeleri
    cryptobubbles'tan CANLI cekilip liste yeniden siralanir.
    Canli veri alinamazsa dosya sirasi korunur ve yuzde yerine "—" gosterilir.

    Doner: [(sembol, yuzde|None), ...] — en sert hareket eden basta.
    """
    havuz = []
    try:
        with open(yol, encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()
                if not satir or satir.startswith("#"):
                    continue
                havuz.append(satir.split(":")[-1])
                if len(havuz) >= HAVUZ:
                    break
    except OSError as e:
        log(f"[OZET][UYARI] {yol} okunamadi: {type(e).__name__}: {e}")
        return []

    yuzdeler = _hareketli_yuzdeler(log=log)
    if not yuzdeler:
        return [(s, None) for s in havuz[:adet]]

    bilinen = [(s, yuzdeler[s]) for s in havuz if s in yuzdeler]
    if not bilinen:
        return [(s, None) for s in havuz[:adet]]
    bilinen.sort(key=lambda x: abs(x[1]), reverse=True)
    return bilinen[:adet]


def _hareketli_yuzdeler(log=print):
    """{SEMBOLUSDT: gunluk_yuzde} — cryptobubbles'tan tek GET.

    Ureticinin (gunun_hareketlileri_guncelle.py) kendi veri_cek fonksiyonu
    kullanilir; kod tekrari yok. Erisilemezse bos sozluk doner ve ozet
    yuzdesiz uretilir — ozet ASLA bu yuzden coker.
    """
    try:
        kod = os.path.join(REPO_KOK, "99_BOT_ARSIV", "kod")
        if kod not in sys.path:
            sys.path.insert(0, kod)
        import gunun_hareketlileri_guncelle as ghg
        veri = ghg.veri_cek()
        if not veri:
            return {}
        yuzdeler = {}
        for coin in veri:
            if not isinstance(coin, dict):
                continue
            gun = (coin.get("performance") or {}).get("day")
            sembol = (coin.get("symbol") or "").upper()
            if gun is None or not sembol:
                continue
            try:
                yuzdeler[sembol + "USDT"] = float(gun)
            except (TypeError, ValueError):
                continue
        return yuzdeler
    except Exception as e:
        log(f"[OZET][UYARI] Gunluk degisim yuzdeleri alinamadi: "
            f"{type(e).__name__}: {e}")
        return {}


def guclu_sinyaller(kayitlar):
    """Acik kayitlardan confluence / mega-confluence olanlari listeler.

    Doner: (mega_listesi, confluence_listesi) — her biri sembol metni listesi.
    Alanlar eski kayitlarda yoksa .get() ile bos gecilir (geriye donuk uyumlu).
    """
    mega, conf = [], []
    for k in kayitlar:
        if k.get("durum") != "acik":
            continue
        if k.get("kaynak_turu") == "mega_confluence":
            kaynak = k.get("kaynak")
            mega.append(f"{k.get('sembol')}" + (f" ({kaynak})" if kaynak else ""))
        elif k.get("confluence"):
            tip = {"bantlar_arasi": "bantlar arası",
                   "dar_band": "dar band"}.get(k.get("confluence_tip"), "çakışan")
            conf.append(f"{k.get('sembol')} ({tip})")
    return mega, conf


# --------------------------------------------------------------------------
# Mesaj
# --------------------------------------------------------------------------

def _tr_yuzde(deger, ondalik=1):
    return f"{deger:.{ondalik}f}".replace(".", ",")


def ozet_metni(an=None, kayit_yol=None, log=print):
    an = an or datetime.now(TSI)
    kayitlar = magicma_karne.kayitlari_oku(kayit_yol or magicma_karne.KAYIT_YOL)

    toplam, uzun, kisa = acik_adaylar(kayitlar)
    kapanan, basarili, yuzde = son_gun_karne(kayitlar, an=an)
    hareketliler = hareketli_semboller(log=log)
    donum, kalan = sonraki_donum(an)
    mega, conf = guclu_sinyaller(kayitlar)

    s = [f"\U0001F4CB GÜNLÜK ÖZET — {an:%d.%m.%Y}", ""]
    s.append(f"\U0001F3AF Açık MagicMA adayları: {toplam} ({uzun} long, {kisa} short)")
    if kapanan:
        s.append(f"\U0001F4CA Son {KARNE_GUN} gün karne: %{_tr_yuzde(yuzde)} başarı "
                 f"({basarili}/{kapanan} kapanan sinyal)")
    else:
        s.append(f"\U0001F4CA Son {KARNE_GUN} gün karne: — "
                 f"(henüz kapanan sinyal yok)")

    if hareketliler:
        parcalar = []
        for sembol, yzd in hareketliler:
            parcalar.append(f"{sembol} (%{_tr_yuzde(yzd)})" if yzd is not None
                            else f"{sembol} (—)")
        s.append("\U0001F525 Bugün en sert hareket eden: " + ", ".join(parcalar))
    else:
        s.append("\U0001F525 Bugün en sert hareket eden: —")

    s.append("")
    s.append(f"\U0001F4C5 Koç takvimi: bir sonraki 60-günlük dönüm noktasına "
             f"{kalan} gün kaldı (tahmini: {donum:%d.%m.%Y})")
    s.append("")

    if mega or conf:
        satir = "⭐ Confluence/mega-confluence: "
        parcalar = []
        if mega:
            parcalar.append("🌟 " + ", ".join(mega))
        if conf:
            parcalar.append("🔥 " + ", ".join(conf))
        s.append(satir + " · ".join(parcalar))
    else:
        s.append("⭐ Confluence/mega-confluence: yok bugün")

    return "\n".join(s)


# --------------------------------------------------------------------------
# Tekrar gonderme korumasi (haftalik ozet pattern'i)
# --------------------------------------------------------------------------

def son_gonderim_oku(yol=DURUM_YOL):
    if not os.path.exists(yol):
        return None
    try:
        with open(yol, encoding="utf-8") as f:
            return magicma_karne._zaman_ayristir(json.load(f).get("son_gonderim"))
    except (OSError, ValueError):
        return None


def son_gonderim_yaz(an=None, yol=DURUM_YOL):
    an = an or datetime.now(TSI)
    try:
        with open(yol, "w", encoding="utf-8") as f:
            json.dump({"son_gonderim": an.isoformat(timespec="seconds")}, f,
                      ensure_ascii=False, indent=1)
    except OSError as e:
        print(f"[OZET][UYARI] durum yazilamadi: {type(e).__name__}: {e}")


def gonderim_zamani_mi(an=None, yol=DURUM_YOL):
    """08:20-08:40 penceresinde miyiz VE bugun henuz gonderilmedi mi?"""
    an = an or datetime.now(TSI)
    dakika = an.hour * 60 + an.minute
    bas = PENCERE_BASLANGIC[0] * 60 + PENCERE_BASLANGIC[1]
    bit = PENCERE_BITIS[0] * 60 + PENCERE_BITIS[1]
    if not (bas <= dakika <= bit):
        return False
    son = son_gonderim_oku(yol)
    return son is None or son.date() != an.date()


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="MagicMA gunluk ozet -> Telegram")
    ap.add_argument("--kuru", action="store_true",
                    help="Telegram'a gonderme, sadece ekrana yaz")
    ap.add_argument("--zorla", action="store_true",
                    help="saat penceresi ve 'bugun gonderildi' kontrolunu atla")
    args = ap.parse_args()

    def _yaz(*a):
        metin = " ".join(str(x) for x in a)
        try:
            print(metin)
        except UnicodeEncodeError:
            print(metin.encode("ascii", "replace").decode("ascii"))

    an = datetime.now(TSI)
    if not args.kuru and not args.zorla and not gonderim_zamani_mi(an):
        son = son_gonderim_oku()
        _yaz(f"Gonderim zamani degil ({an:%H:%M} TSI; pencere "
             f"{PENCERE_BASLANGIC[0]:02d}:{PENCERE_BASLANGIC[1]:02d}-"
             f"{PENCERE_BITIS[0]:02d}:{PENCERE_BITIS[1]:02d})"
             + (f", son gonderim: {son:%d.%m.%Y %H:%M}" if son else "") + ".")
        return 0

    metin = ozet_metni(an, log=_yaz)
    if args.kuru:
        _yaz("\n--- GONDERILECEK MESAJ (kuru mod) ---")
        _yaz(metin)
        _yaz("--- son ---")
        return 0

    import telegram_alarm
    token, chat_id = telegram_alarm.telegram_bilgileri()
    if telegram_alarm.telegram_gonder(token, chat_id, metin):
        son_gonderim_yaz(an)
        _yaz(f"Gunluk ozet Telegram'a gonderildi ({an:%d.%m.%Y %H:%M}).")
        return 0
    _yaz("[HATA] Gunluk ozet gonderilemedi — sonraki turda tekrar denenecek.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
