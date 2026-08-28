"""
magicma/magicma_karne.py

MagicMA sinyal KARNESI — botun kendi bildirimlerinin gercekte tutup tutmadigini
olcer.

Mantik: telegram_alarm.py'nin gonderdigi her YENI TEMAS aslinda bir iddiadir
("bu bant tutacak / kirilacak"). Her yeni temas icin burada "acik" bir kayit
acilir; sonraki turlarda guncel fiyata bakilarak kayit su durumlardan birine
gecirilir:

  LONG adayi  (fiyat bandin ustunde = destek testi)
    basarili  : fiyat, GIRIS fiyatinin %BASARI_ESIK_YUZDE uzerine cikarsa
    basarisiz : fiyat, CIZGININ %GECERSIZ_ESIK_YUZDE altina inerse (destek kirildi)

  SHORT adayi (fiyat bandin altinda = direnc testi) — ayna mantik
    basarili  : fiyat, GIRIS fiyatinin %BASARI_ESIK_YUZDE altina inerse
    basarisiz : fiyat, CIZGININ %GECERSIZ_ESIK_YUZDE ustune cikarsa

  zaman_asimi : ZAMAN_ASIMI_SAAT icinde iki esik de gecilmezse ("kararsiz kaldi")

Kullanim:
    py -3 magicma/magicma_karne.py              # acik kayitlari degerlendir + rapor
    py -3 magicma/magicma_karne.py --sadece-rapor
    py -3 magicma/magicma_karne.py --haftalik   # haftalik ozet metnini ekrana yaz

Not: fiyat cekme mantigi TEKRAR YAZILMAZ; fiyat_kontrol.py kullanilir.
telegram_alarm.py bu modulu import eder ve zaten cektigi fiyat sozlugunu
degerlendiriciye verir (ikinci kez fiyat cekilmez).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fiyat_kontrol

# --------------------------------------------------------------------------
# Ayarlanabilir esikler (ileride tek yerden degistirilsin diye dosya basinda)
# --------------------------------------------------------------------------
BASARI_ESIK_YUZDE = 0.5      # giris fiyatindan bu kadar lehte hareket = basarili
GECERSIZ_ESIK_YUZDE = 0.3    # cizginin bu kadar otesine gecis = basarisiz
ZAMAN_ASIMI_SAAT = 48        # bu sure icinde karar cikmazsa sonucsuz kapat

REPO_KOK = fiyat_kontrol.REPO_KOK
KAYIT_YOL = os.path.join(REPO_KOK, "magicma", "karne_kayitlari.json")
RAPOR_YOL = os.path.join(REPO_KOK, "magicma", "KARNE_RAPOR.md")
OZET_DURUM_YOL = os.path.join(REPO_KOK, "magicma", "karne_son_ozet.json")

TSI = timezone(timedelta(hours=3))

KATEGORI_ADI = {
    "bist.txt": "bist",
    "abd_hisse.txt": "abd_hisse",
    "forex_emtia.txt": "forex_emtia",
    "kripto.txt": "kripto",
    "gunun_hareketlileri.txt": "gunun_hareketlileri",
    "endeks_faiz.txt": "endeks_faiz",
}

_KATEGORI_ONBELLEK = None


def simdi():
    return datetime.now(TSI)


def kategori_bul(sembol):
    """Sembolun geldigi sembol_listesi/*.txt dosyasina gore kategori adi.

    Yedek: sembol hicbir listede yoksa ("gunun hareketlileri" her taramada
    bastan uretildigi icin dunku bir coin listeden dusmus olabilir) USDT
    parite adi kriptoya sayilir; kalanlar "bilinmiyor".
    """
    global _KATEGORI_ONBELLEK
    if _KATEGORI_ONBELLEK is None:
        try:
            _KATEGORI_ONBELLEK = fiyat_kontrol.sembol_dosya_haritasi()
        except Exception:
            _KATEGORI_ONBELLEK = {}
    dosya = _KATEGORI_ONBELLEK.get(sembol, "")
    if dosya:
        return KATEGORI_ADI.get(dosya, "bilinmiyor")
    return "kripto" if (sembol or "").endswith("USDT") else "bilinmiyor"


# --------------------------------------------------------------------------
# Kayit dosyasi
# --------------------------------------------------------------------------

def kayitlari_oku(yol=KAYIT_YOL):
    if not os.path.exists(yol):
        return []
    try:
        with open(yol, encoding="utf-8") as f:
            veri = json.load(f)
        return veri if isinstance(veri, list) else []
    except (OSError, ValueError) as e:
        print(f"[UYARI] {yol} okunamadi ({type(e).__name__}: {e}); bos liste kullaniliyor.")
        return []


def kayitlari_yaz(kayitlar, yol=KAYIT_YOL):
    gecici = yol + ".tmp"
    try:
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(kayitlar, f, ensure_ascii=False, indent=1)
        os.replace(gecici, yol)
        return True
    except OSError as e:
        print(f"[HATA] karne kayitlari yazilamadi: {type(e).__name__}: {e}")
        return False


def _cizgi_kisa(ad):
    """'Magicma Gunluk Ust Cizgi' -> 'G-Ust' gibi kisa, dosya/id dostu etiket."""
    a = (ad or "").lower()
    if "haftal" in a or "weekly" in a:
        gun = "H"
    elif "günl" in a or "gunl" in a or "daily" in a:
        gun = "G"
    else:
        gun = "X"
    if "üst" in a or "ust" in a:
        uc = "Ust"
    elif "alt" in a:
        uc = "Alt"
    elif "-1" in a:
        uc = "1"
    elif "-2" in a:
        uc = "2"
    else:
        uc = "".join(ch for ch in (ad or "") if ch.isalnum())[-4:] or "X"
    return f"{gun}-{uc}"


def sinyal_kaydi_olustur(sembol, cizgi_adi, cizgi_degeri, yon, giris_fiyati, an=None,
                         confluence=False, confluence_cizgiler=None, confluence_sayisi=1,
                         confluence_tip=None, kaynak_turu="teknik", kaynak=None):
    """Tek sinyal kaydi. confluence* alanlari cakisan seviye grubu icin doldurulur.

    Cakisan grupta cizgi_adi/cizgi_degeri, gruba EN YAKIN cizgiden gelir —
    degerlendirme (gecersiz esigi) boylece degismeden calisir.

    kaynak_turu : "teknik" (MagicMA cizgisi) | "onemli_seviye" (Koc/dis kaynak) |
        "mega_confluence" (ikisi ayni bolgede). Karnede AYRI olculur — hangi
        sinyal turunun gercekten daha guvenilir oldugunu zamanla gormek icin.
    kaynak : onemli_seviye/mega icin seviyeyi veren kisi/kurum.
    """
    an = an or simdi()
    zaman = an.isoformat(timespec="seconds")
    return {
        "id": f"{sembol}_{zaman}_{_cizgi_kisa(cizgi_adi)}"
              + (f"_CONF{confluence_sayisi}" if confluence else ""),
        "sembol": sembol,
        "kategori": kategori_bul(sembol),
        "cizgi_adi": cizgi_adi,
        "cizgi_degeri": cizgi_degeri,
        "yon": yon,
        "kaynak_turu": kaynak_turu or "teknik",
        "kaynak": kaynak,
        "confluence": bool(confluence),
        "confluence_tip": confluence_tip or ("bantlar_arasi" if confluence else "tekil"),
        "confluence_sayisi": int(confluence_sayisi or 1),
        "confluence_cizgiler": list(confluence_cizgiler or [cizgi_adi]),
        "giris_fiyati": giris_fiyati,
        "giris_zamani": zaman,
        "durum": "acik",
        "sonuc_fiyati": None,
        "sonuc_zamani": None,
        "sonuc_yuzde": None,
    }


def yeni_sinyalleri_kaydet(temaslar, an=None, yol=KAYIT_YOL):
    """telegram_alarm.py kancasi: yeni temaslari 'acik' kayit olarak ekler.

    temaslar: [{sembol, cizgi_adi, cizgi, fiyat, yon}, ...]
    Ayni sembol+cizgi icin zaten ACIK bir kayit varsa yenisi ACILMAZ
    (histerezis salinimi karneyi sisirmesin).

    TEK ISTISNA — MEGA YUKSELTMESI: acik kayit "teknik" iken ayni sembol+cizgi
    icin bu turda mega-confluence tespit edilirse, YENI kayit acilmaz ama
    mevcut kayit mega'ya YUKSELTILIR. Aksi halde "bu sinyal aslinda mega'ydi"
    bilgisi kaybolur (sembol zaten teknik olarak listedeyse mega hic kaydedilmez)
    ve karnedeki mega/teknik karsilastirmasi olcusuz kalirdi. Ters yonde
    (mega -> teknik) dusurme YAPILMAZ.

    Doner: eklenen kayit sayisi.
    """
    if not temaslar:
        return 0
    try:
        kayitlar = kayitlari_oku(yol)
        acik_kayitlar = {(k.get("sembol"), k.get("cizgi_adi")): k
                         for k in kayitlar if k.get("durum") == "acik"}
        acik_imzalar = set(acik_kayitlar)
        eklenen, yukseltilen = 0, 0
        for t in temaslar:
            sembol = t.get("sembol")
            cizgi_adi = t.get("cizgi_adi")
            fiyat = t.get("fiyat")
            cizgi = t.get("cizgi")
            yon = t.get("yon")
            if not sembol or not fiyat or not cizgi or yon not in ("long", "short"):
                continue
            if (sembol, cizgi_adi) in acik_imzalar:
                mevcut = acik_kayitlar[(sembol, cizgi_adi)]
                if (t.get("kaynak_turu") == "mega_confluence"
                        and (mevcut.get("kaynak_turu") or "teknik") != "mega_confluence"):
                    mevcut["kaynak_turu"] = "mega_confluence"
                    mevcut["kaynak"] = t.get("kaynak")
                    mevcut["mega_yukseltme"] = True
                    yukseltilen += 1
                continue
            kayitlar.append(sinyal_kaydi_olustur(
                sembol, cizgi_adi, cizgi, yon, fiyat, an,
                confluence=t.get("confluence", False),
                confluence_cizgiler=t.get("confluence_cizgiler"),
                confluence_sayisi=t.get("confluence_sayisi", 1),
                confluence_tip=t.get("confluence_tip"),
                kaynak_turu=t.get("kaynak_turu", "teknik"),
                kaynak=t.get("kaynak")))
            acik_imzalar.add((sembol, cizgi_adi))
            acik_kayitlar[(sembol, cizgi_adi)] = kayitlar[-1]
            eklenen += 1
        if eklenen or yukseltilen:
            kayitlari_yaz(kayitlar, yol)
        if yukseltilen:
            print(f"[KARNE] {yukseltilen} acik kayit mega-confluence'a yukseltildi.")
        return eklenen
    except Exception as e:
        print(f"[UYARI] karne kaydi eklenemedi: {type(e).__name__}: {e}")
        return 0


# --------------------------------------------------------------------------
# Degerlendirme
# --------------------------------------------------------------------------

def _zaman_ayristir(metin):
    try:
        d = datetime.fromisoformat(metin)
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=TSI)


def _yonlu_yuzde(kayit, fiyat):
    """Sinyal yonunde KAZANC yuzdesi (long: yukari, short: asagi pozitif)."""
    giris = float(kayit["giris_fiyati"])
    fark = (fiyat - giris) / giris * 100
    return round(fark if kayit["yon"] == "long" else -fark, 3)


def sinyali_degerlendir(kayit, fiyat, an=None):
    """Tek kayit icin yeni durum: 'acik' | 'basarili' | 'basarisiz' | 'zaman_asimi'."""
    an = an or simdi()
    giris = float(kayit["giris_fiyati"])
    cizgi = float(kayit["cizgi_degeri"])
    yon = kayit["yon"]

    if yon == "long":
        if fiyat >= giris * (1 + BASARI_ESIK_YUZDE / 100):
            return "basarili"
        if fiyat <= cizgi * (1 - GECERSIZ_ESIK_YUZDE / 100):
            return "basarisiz"
    else:
        if fiyat <= giris * (1 - BASARI_ESIK_YUZDE / 100):
            return "basarili"
        if fiyat >= cizgi * (1 + GECERSIZ_ESIK_YUZDE / 100):
            return "basarisiz"

    giris_an = _zaman_ayristir(kayit.get("giris_zamani"))
    if giris_an and (an - giris_an) >= timedelta(hours=ZAMAN_ASIMI_SAAT):
        return "zaman_asimi"
    return "acik"


def acik_sinyalleri_degerlendir(fiyatlar=None, an=None, log=print, yol=KAYIT_YOL):
    """Tum 'acik' kayitlari guncel fiyata gore degerlendirir.

    fiyatlar : {sembol: fiyat} — verilmezse fiyat_kontrol ile bastan cekilir
               (telegram_alarm.py zaten cektigi sozlugu verir, ikinci cekme yok).
    Doner: durumu degisen kayitlarin listesi (bos liste = degisiklik yok).
    """
    an = an or simdi()
    kayitlar = kayitlari_oku(yol)
    acik = [k for k in kayitlar if k.get("durum") == "acik"]
    if not acik:
        log("[KARNE] Acik sinyal yok.")
        return []

    if fiyatlar is None:
        try:
            v = fiyat_kontrol.adaylari_hesapla(esik=0.0, log=lambda *a, **k: None)
            fiyatlar = v.get("tum_fiyatlar", {})
        except Exception as e:
            log(f"[KARNE][HATA] Guncel fiyatlar cekilemedi: {type(e).__name__}: {e}")
            return []

    degisen, fiyatsiz = [], 0
    for kayit in acik:
        try:
            fiyat = fiyatlar.get(kayit.get("sembol"))
            zaman_asimi_mi = False
            if not fiyat:
                # Fiyat yoksa (piyasa kapali, kaynak vermedi) yalnizca zaman
                # asimi kontrolu yapilabilir; aksi halde kayit atlanir.
                giris_an = _zaman_ayristir(kayit.get("giris_zamani"))
                if giris_an and (an - giris_an) >= timedelta(hours=ZAMAN_ASIMI_SAAT):
                    zaman_asimi_mi = True
                else:
                    fiyatsiz += 1
                    continue
            yeni = ("zaman_asimi" if zaman_asimi_mi
                    else sinyali_degerlendir(kayit, float(fiyat), an))
            if yeni == "acik":
                continue
            kayit["durum"] = yeni
            kayit["sonuc_fiyati"] = round(float(fiyat), 8) if fiyat else None
            kayit["sonuc_zamani"] = an.isoformat(timespec="seconds")
            kayit["sonuc_yuzde"] = _yonlu_yuzde(kayit, float(fiyat)) if fiyat else None
            degisen.append(kayit)
        except Exception as e:
            log(f"[KARNE][UYARI] {kayit.get('sembol')} degerlendirilemedi: "
                f"{type(e).__name__}: {e}")
            continue

    if degisen:
        kayitlari_yaz(kayitlar, yol)
    log(f"[KARNE] Acik: {len(acik)} · kapanan: {len(degisen)} · "
        f"fiyati alinamayan (atlandi): {fiyatsiz}")
    return degisen


# --------------------------------------------------------------------------
# Rapor
# --------------------------------------------------------------------------

def _oran(pay, payda):
    return (pay / payda * 100) if payda else 0.0


def _tr_yuzde(deger, ondalik=1):
    return f"%{deger:.{ondalik}f}".replace(".", ",")


def istatistik_hesapla(kayitlar=None, yol=KAYIT_YOL):
    """Kapanmis kayitlardan ozet istatistik uretir."""
    kayitlar = kayitlar if kayitlar is not None else kayitlari_oku(yol)
    kapanan = [k for k in kayitlar if k.get("durum") in
               ("basarili", "basarisiz", "zaman_asimi")]

    def _say(liste):
        return {
            "toplam": len(liste),
            "basarili": sum(1 for k in liste if k["durum"] == "basarili"),
            "basarisiz": sum(1 for k in liste if k["durum"] == "basarisiz"),
            "zaman_asimi": sum(1 for k in liste if k["durum"] == "zaman_asimi"),
        }

    kategoriler = {}
    for k in kapanan:
        kategoriler.setdefault(k.get("kategori", "bilinmiyor"), []).append(k)
    yonler = {}
    for k in kapanan:
        yonler.setdefault(k.get("yon", "?"), []).append(k)

    # Confluence kirilimi — hipotez testi: cakisan seviye gercekten daha guclu
    # bir sinyal mi? Eski kayitlarda `confluence` alani YOK; .get() ile tekil
    # sayilirlar (geriye donuk uyumluluk).
    # UC AYRI TIP olculur, cunku "iki cizgi ayni yerde" iki farkli sey olabilir:
    #   bantlar_arasi = Gunluk + Haftalik ayni bolgede (BAGIMSIZ teyit)
    #   dar_band      = tek bandin alt+ust kenari yakin (tek olcum, teyit degil)
    # Ikisini tek potada toplamak hipotezi olcemez hale getirirdi.
    # Confluence YALNIZCA teknik (MagicMA cizgisi) sinyaller icin anlamlidir —
    # onemli-seviye/mega kayitlarinda cizgi cakismasi diye bir kavram yok.
    # Onlari "tekil" saymak bu kirilimi kirletirdi, bu yuzden disarida birakilir.
    teknik_kapanan = [k for k in kapanan if (k.get("kaynak_turu") or "teknik") == "teknik"]
    cakisan = [k for k in teknik_kapanan if k.get("confluence")]
    tekil = [k for k in teknik_kapanan if not k.get("confluence")]
    bantlar_arasi = [k for k in cakisan if k.get("confluence_tip") == "bantlar_arasi"]
    dar_band = [k for k in cakisan if k.get("confluence_tip") == "dar_band"]

    # Kaynak turu kirilimi: teknik (MagicMA cizgisi) / onemli_seviye
    # (Koc + dis analist) / mega_confluence (ikisi ayni bolgede).
    # Eski kayitlarda alan YOK -> "teknik" sayilir (geriye donuk uyumluluk).
    kaynak_gruplari = {}
    for k in kapanan:
        kaynak_gruplari.setdefault(k.get("kaynak_turu") or "teknik", []).append(k)

    return {
        "acik": sum(1 for k in kayitlar if k.get("durum") == "acik"),
        "acik_confluence": sum(1 for k in kayitlar
                               if k.get("durum") == "acik" and k.get("confluence")),
        "acik_kaynak": {t: sum(1 for k in kayitlar if k.get("durum") == "acik"
                               and (k.get("kaynak_turu") or "teknik") == t)
                        for t in ("teknik", "onemli_seviye", "mega_confluence")},
        "kaynak_turu": {t: _say(kaynak_gruplari.get(t, []))
                        for t in ("mega_confluence", "onemli_seviye", "teknik")},
        "genel": _say(kapanan),
        "kategori": {ad: _say(liste) for ad, liste in sorted(kategoriler.items())},
        "yon": {ad: _say(liste) for ad, liste in sorted(yonler.items())},
        "confluence": {"cakisan": _say(cakisan), "tekil": _say(tekil),
                       "bantlar_arasi": _say(bantlar_arasi),
                       "dar_band": _say(dar_band)},
        "son_kapananlar": sorted(
            kapanan, key=lambda k: k.get("sonuc_zamani") or "", reverse=True)[:20],
    }


def karne_raporu_uret(yol=KAYIT_YOL, rapor_yol=RAPOR_YOL, log=print):
    """magicma/KARNE_RAPOR.md dosyasini bastan yazar (tam guncel gorunum)."""
    ist = istatistik_hesapla(yol=yol)
    g = ist["genel"]
    an = simdi()

    s = []
    s.append("# MagicMA Sinyal Karnesi\n")
    s.append(f"_Guncelleme: {an:%d.%m.%Y %H:%M} TSI_\n")
    s.append(f"Esikler: basari {_tr_yuzde(BASARI_ESIK_YUZDE)} · "
             f"gecersiz {_tr_yuzde(GECERSIZ_ESIK_YUZDE)} "
             f"· zaman asimi {ZAMAN_ASIMI_SAAT} saat\n")
    s.append("## Genel\n")
    s.append(f"- Acik (devam eden) sinyal: **{ist['acik']}**")
    s.append(f"- Toplam kapanan sinyal: **{g['toplam']}**")
    if g["toplam"]:
        s.append(f"- ✅ Basarili: {g['basarili']} "
                 f"({_tr_yuzde(_oran(g['basarili'], g['toplam']))})")
        s.append(f"- ❌ Basarisiz: {g['basarisiz']} "
                 f"({_tr_yuzde(_oran(g['basarisiz'], g['toplam']))})")
        s.append(f"- ⏱ Zaman asimi: {g['zaman_asimi']} "
                 f"({_tr_yuzde(_oran(g['zaman_asimi'], g['toplam']))})")
    s.append("")

    s.append("## Kategori bazinda\n")
    if ist["kategori"]:
        s.append("| Kategori | Kapanan | Basarili | Basarisiz | Zaman asimi | Basari orani |")
        s.append("|---|---:|---:|---:|---:|---:|")
        for ad, d in ist["kategori"].items():
            s.append(f"| {ad} | {d['toplam']} | {d['basarili']} | {d['basarisiz']} | "
                     f"{d['zaman_asimi']} | {_tr_yuzde(_oran(d['basarili'], d['toplam']))} |")
    else:
        s.append("_Henuz kapanan sinyal yok._")
    s.append("")

    # --- Hipotez testi 1: hangi SINYAL KAYNAGI daha guvenilir? --------------
    kt = ist["kaynak_turu"]
    ETIKET = {"mega_confluence": "🌟 Mega-confluence (teknik + temel)",
              "onemli_seviye": "📌 Önemli seviye (Koç / dış kaynak)",
              "teknik": "MagicMA teknik çizgisi"}
    s.append("## Kaynak turu bazinda\n")
    s.append("_Uc ayri sinyal kaynagi: MagicMA teknik cizgisi · Koc/dis analist "
             "seviyesi · ikisinin ayni bolgede birlestigi mega-confluence._\n")
    s.append(f"- Acik: teknik {ist['acik_kaynak']['teknik']} · "
             f"onemli seviye {ist['acik_kaynak']['onemli_seviye']} · "
             f"mega {ist['acik_kaynak']['mega_confluence']}\n")
    if any(d["toplam"] for d in kt.values()):
        s.append("| Sinyal kaynagi | Kapanan | Basarili | Basarisiz | Zaman asimi | Basari orani |")
        s.append("|---|---:|---:|---:|---:|---:|")
        for ad, d in kt.items():
            s.append(f"| {ETIKET[ad]} | {d['toplam']} | {d['basarili']} | {d['basarisiz']} | "
                     f"{d['zaman_asimi']} | {_tr_yuzde(_oran(d['basarili'], d['toplam']))} |")
    else:
        s.append("_Henuz kapanan sinyal yok._")
    s.append("")

    # --- Hipotez testi 2: cakisan seviye (confluence) daha mi guclu? --------
    c = ist["confluence"]
    s.append("## Cakisan seviye (confluence) vs tekil\n")
    s.append(f"_Yalnizca **teknik** (MagicMA) sinyaller. Cakisma tanimi: ayni sembolde "
             f"temas eden iki+ cizginin degerleri birbirine "
             f"{_tr_yuzde(fiyat_kontrol.CONFLUENCE_ESIK_YUZDE, 2)} yakin._\n")
    s.append(f"- Acik cakisan sinyal: **{ist['acik_confluence']}** / {ist['acik']}\n")
    s.append("_Iki tip ayri olculur: **bantlar arasi** = Gunluk + Haftalik gibi "
             "FARKLI bantlar ayni bolgeyi isaretliyor (bagimsiz teyit); "
             "**dar band** = tek bandin alt+ust kenari birbirine yakin "
             "(cizgiler cakisiyor ama bagimsiz teyit degil)._\n")
    if c["cakisan"]["toplam"] or c["tekil"]["toplam"]:
        s.append("| Sinyal tipi | Kapanan | Basarili | Basarisiz | Zaman asimi | Basari orani |")
        s.append("|---|---:|---:|---:|---:|---:|")
        for etiket, d in (("🔥 Cakisan — bantlar arasi", c["bantlar_arasi"]),
                          ("🔥 Cakisan — dar band", c["dar_band"]),
                          ("Tekil", c["tekil"])):
            s.append(f"| {etiket} | {d['toplam']} | {d['basarili']} | {d['basarisiz']} | "
                     f"{d['zaman_asimi']} | {_tr_yuzde(_oran(d['basarili'], d['toplam']))} |")
        if c["bantlar_arasi"]["toplam"] and c["tekil"]["toplam"]:
            fark = (_oran(c["bantlar_arasi"]["basarili"], c["bantlar_arasi"]["toplam"])
                    - _oran(c["tekil"]["basarili"], c["tekil"]["toplam"]))
            s.append("")
            s.append(f"**Bantlar arasi - tekil farki: "
                     f"{('%+.1f' % fark).replace('.', ',')} puan** "
                     f"(cakisan lehine pozitif). Ornek sayisi azken bu farka guvenme.")
        else:
            s.append("")
            s.append("_Karsilastirma icin hem bantlar-arasi hem tekil kapanan "
                     "sinyal gerekiyor._")
    else:
        s.append("_Henuz kapanan sinyal yok._")
    s.append("")

    s.append("## Yon bazinda\n")
    if ist["yon"]:
        s.append("| Yon | Kapanan | Basarili | Basarisiz | Zaman asimi | Basari orani |")
        s.append("|---|---:|---:|---:|---:|---:|")
        for ad, d in ist["yon"].items():
            s.append(f"| {ad.upper()} | {d['toplam']} | {d['basarili']} | {d['basarisiz']} | "
                     f"{d['zaman_asimi']} | {_tr_yuzde(_oran(d['basarili'], d['toplam']))} |")
    else:
        s.append("_Henuz kapanan sinyal yok._")
    s.append("")

    s.append("## Son 20 kapanan sinyal\n")
    if ist["son_kapananlar"]:
        s.append("| Kapanis | Sembol | Kategori | Tip | Yon | Sonuc | Giris | Cikis | Yonlu % |")
        s.append("|---|---|---|---|---|---|---:|---:|---:|")
        isaret = {"basarili": "✅ basarili", "basarisiz": "❌ basarisiz",
                  "zaman_asimi": "⏱ zaman asimi"}
        for k in ist["son_kapananlar"]:
            zam = (k.get("sonuc_zamani") or "")[:16].replace("T", " ")
            yuz = k.get("sonuc_yuzde")
            ktur = k.get("kaynak_turu") or "teknik"
            if ktur == "mega_confluence":
                tip = "🌟 mega"
            elif ktur == "onemli_seviye":
                tip = "📌 seviye"
            elif k.get("confluence"):
                kisa = {"bantlar_arasi": "bant-arasi", "dar_band": "dar-band"}.get(
                    k.get("confluence_tip"), "cakisan")
                tip = f"🔥 {kisa} x{k.get('confluence_sayisi', 2)}"
            else:
                tip = "tekil"
            s.append(f"| {zam} | {k.get('sembol')} | {k.get('kategori')} | {tip} | "
                     f"{(k.get('yon') or '').upper()} | {isaret.get(k['durum'], k['durum'])} | "
                     f"{k.get('giris_fiyati')} | {k.get('sonuc_fiyati')} | "
                     f"{('%.2f' % yuz).replace('.', ',') if yuz is not None else '-'} |")
    else:
        s.append("_Henuz kapanan sinyal yok._")
    s.append("")

    metin = "\n".join(s)
    try:
        with open(rapor_yol, "w", encoding="utf-8") as f:
            f.write(metin)
        log(f"[KARNE] Rapor yazildi: {rapor_yol}")
    except OSError as e:
        log(f"[KARNE][HATA] Rapor yazilamadi: {type(e).__name__}: {e}")
    return metin


# --------------------------------------------------------------------------
# Haftalik Telegram ozeti
# --------------------------------------------------------------------------

def _ozet_durum_oku(yol=OZET_DURUM_YOL):
    if not os.path.exists(yol):
        return None
    try:
        with open(yol, encoding="utf-8") as f:
            return _zaman_ayristir(json.load(f).get("son_ozet"))
    except (OSError, ValueError):
        return None


def ozet_durum_yaz(an=None, yol=OZET_DURUM_YOL):
    an = an or simdi()
    try:
        with open(yol, "w", encoding="utf-8") as f:
            json.dump({"son_ozet": an.isoformat(timespec="seconds")}, f,
                      ensure_ascii=False, indent=1)
    except OSError as e:
        print(f"[KARNE][UYARI] ozet durumu yazilamadi: {type(e).__name__}: {e}")


def haftalik_ozet_zamani_mi(an=None, yol=OZET_DURUM_YOL):
    """Pazartesi mi ve son ozetten 24 saatten fazla mi gecti?"""
    an = an or simdi()
    if an.weekday() != 0:
        return False
    son = _ozet_durum_oku(yol)
    return son is None or (an - son) >= timedelta(hours=24)


def haftalik_ozet_metni(an=None, yol=KAYIT_YOL):
    an = an or simdi()
    ist = istatistik_hesapla(yol=yol)
    g = ist["genel"]
    bas = an - timedelta(days=7)
    s = [f"\U0001F4CA HAFTALIK MagicMA KARNESİ "
         f"({bas:%d.%m.%Y} - {an:%d.%m.%Y})", ""]
    s.append(f"Toplam kapanan sinyal: {g['toplam']}")
    if g["toplam"]:
        s.append(f"✅ Başarılı: {g['basarili']} "
                 f"({_tr_yuzde(_oran(g['basarili'], g['toplam']))})")
        s.append(f"❌ Başarısız: {g['basarisiz']} "
                 f"({_tr_yuzde(_oran(g['basarisiz'], g['toplam']))})")
        s.append(f"⏱ Zaman aşımı: {g['zaman_asimi']} "
                 f"({_tr_yuzde(_oran(g['zaman_asimi'], g['toplam']))})")
        if ist["kategori"]:
            s += ["", "Kategori bazında:"]
            for ad, d in ist["kategori"].items():
                s.append(f"{ad}: {_tr_yuzde(_oran(d['basarili'], d['toplam']), 0)} "
                         f"({d['basarili']}/{d['toplam']})")
        if ist["yon"]:
            s.append("")
            s.append(" · ".join(
                f"{ad.capitalize()}: {_tr_yuzde(_oran(d['basarili'], d['toplam']), 0)}"
                for ad, d in ist["yon"].items()))
        c = ist["confluence"]
        if c["cakisan"]["toplam"]:
            s.append("")
            for etiket, d in (("🔥 Bantlar arası", c["bantlar_arasi"]),
                              ("🔥 Dar band", c["dar_band"]),
                              ("Tekil", c["tekil"])):
                if d["toplam"]:
                    s.append(f"{etiket}: "
                             f"{_tr_yuzde(_oran(d['basarili'], d['toplam']), 0)} "
                             f"({d['basarili']}/{d['toplam']})")
    else:
        s.append("Henüz kapanan sinyal yok.")
    s += ["", f"Açık (devam eden) sinyal: {ist['acik']}"]
    return "\n".join(s)


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="MagicMA sinyal karnesi")
    ap.add_argument("--sadece-rapor", action="store_true",
                    help="fiyat cekme, sadece mevcut kayitlardan raporu yeniden uret")
    ap.add_argument("--haftalik", action="store_true",
                    help="haftalik Telegram ozet metnini ekrana yaz (gondermez)")
    args = ap.parse_args()

    def _yaz(x):
        try:
            print(x)
        except UnicodeEncodeError:
            print(x.encode("ascii", "replace").decode("ascii"))

    if args.haftalik:
        _yaz(haftalik_ozet_metni())
        return 0

    if not args.sadece_rapor:
        acik_sinyalleri_degerlendir(log=_yaz)
    _yaz(karne_raporu_uret(log=_yaz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
