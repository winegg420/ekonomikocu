"""
magicma/onemli_seviye.py

MagicMA alarm motoruna IKINCI bir seviye kaynagi ekler: Koc'un ve dis
analistlerin verdigi SOMUT sayisal seviyeler (`magicma/onemli_seviyeler.json`).

Neden ayri modul: MagicMA cizgileri hassas teknik seviyeler (esik %0,25);
buradakiler kabaca hedef/pivot seviyeler — daha genis tolerans (%0,5) ve
tamamen farkli bir gecerlilik omru var. Ayni dosyaya karistirmak ikisini de
bozardi.

Uc kavram, uc AYRI kategori (karistirmayin):
  1. teknik confluence  -> birden fazla MAGICMA cizgisi cakisiyor
                           (fiyat_kontrol.confluence_isaretle)
  2. onemli seviye      -> fiyat bir KOC/DIS KAYNAK seviyesine yaklasti (bu modul)
  3. MEGA-CONFLUENCE    -> ayni sembolde teknik cizgi VE onemli seviye ayni
                           fiyat bolgesinde — teknik ve temel ayni noktada
                           birlesiyor. En yuksek oncelikli sinyal.

Kullanim:
    py -3 magicma/onemli_seviye.py            # kutuphaneyi dogrula + aday listele
    py -3 magicma/onemli_seviye.py --dogrula  # sadece dogrulama (fiyat cekmez)

GUNCELLEME NOTU: `onemli_seviyeler.json` OTOMATIK DOLMAZ. Yeni bir dis kaynak
veya Koc tweet'i 11_DIS_KAYNAKLAR.md / 06_ANALIZ.md'ye eklendiginde, icindeki
somut sayisal seviyeler buraya ELLE eklenmelidir (bkz. magicma/README.md).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fiyat_kontrol

# --------------------------------------------------------------------------
# Esikler (tek yerde, ileride kolay ayarlansin)
# --------------------------------------------------------------------------
# MagicMA'nin %0,25'inden GENIS: bunlar hassas teknik cizgi degil, kabaca
# hedef/pivot seviyeler.
ONEMLI_SEVIYE_ESIK_YUZDE = 0.5

# Teknik cizgi ile onemli seviye "ayni fiyat bolgesinde" sayilmak icin
# aralarindaki azami fark.
MEGA_CONFLUENCE_ESIK_YUZDE = 0.3

REPO_KOK = fiyat_kontrol.REPO_KOK
SEVIYE_YOL = os.path.join(REPO_KOK, "magicma", "onemli_seviyeler.json")

# Bir bandin ICINDE olan fiyat icin yon, bandin turune gore belirlenir.
# (Tek seviyelerde yon geometrik: ustundeyse destek/long, altindaysa direnc/short.)
DIRENC_TURLERI = {"direnc", "direnc_bandi", "tavan", "duvar", "robot", "alarm",
                  "hedef", "hedef_bandi", "trend_kesisimi", "boyun_cizgisi",
                  "opsiyon_yigilmasi", "sata_donus", "esik"}
DESTEK_TURLERI = {"destek", "destek_bandi", "kritik_destek", "stop", "taban",
                  "alim_seviyesi", "on_kosul", "hareketli_ortalama"}


# --------------------------------------------------------------------------
# Kutuphane okuma / dogrulama
# --------------------------------------------------------------------------

def seviyeleri_oku(yol=SEVIYE_YOL, log=print):
    """onemli_seviyeler.json'i okur ve dogrular.

    Doner: (gecerli_kayitlar, atlananlar)
    Atlama sebepleri log'a yazilir — sessizce veri kaybi olmaz.
    """
    if not os.path.exists(yol):
        log(f"[ONEMLI] Kutuphane bulunamadi: {yol}")
        return [], []
    try:
        with open(yol, encoding="utf-8") as f:
            ham = json.load(f)
        if not isinstance(ham, list):
            raise ValueError("kok oge liste degil")
    except (OSError, ValueError) as e:
        log(f"[ONEMLI][HATA] {yol} okunamadi: {type(e).__name__}: {e}")
        return [], []

    gecerli, atlanan = [], []
    for sira, kayit in enumerate(ham):
        try:
            if not isinstance(kayit, dict):
                raise ValueError("kayit sozluk degil")
            enstruman = (kayit.get("enstruman") or "").strip()
            if not enstruman:
                raise ValueError("enstruman bos")
            alt, ust = _sinirlar(kayit)
            if alt is None:
                raise ValueError("seviye / seviye_alt+seviye_ust yok veya sayi degil")
            temiz = dict(kayit)
            temiz["enstruman"] = enstruman
            temiz["_alt"] = alt
            temiz["_ust"] = ust
            temiz["_orta"] = (alt + ust) / 2
            temiz["_bant_mi"] = ust > alt
            temiz["_id"] = kayit.get("id") or f"{enstruman}#{sira}"
            gecerli.append(temiz)
        except (ValueError, TypeError) as e:
            atlanan.append((sira, kayit.get("enstruman", "?"), str(e)))

    for sira, ens, sebep in atlanan:
        log(f"[ONEMLI][ATLANDI] #{sira} {ens}: {sebep}")
    return gecerli, atlanan


def _sinirlar(kayit):
    """Kayittan (alt, ust) sayisal sinirlarini cikarir. Gecersizse (None, None)."""
    try:
        if kayit.get("seviye") is not None:
            deger = float(kayit["seviye"])
            return (deger, deger) if deger > 0 else (None, None)
        alt = float(kayit["seviye_alt"])
        ust = float(kayit["seviye_ust"])
        if alt <= 0 or ust <= 0:
            return None, None
        return (min(alt, ust), max(alt, ust))
    except (KeyError, TypeError, ValueError):
        return None, None


def kapsam_denetle(seviyeler, taranan_semboller, log=print):
    """Kutuphanedeki enstrumanin taramada karsiligi var mi?

    Karsiligi olmayan (fiyati hic cekilemeyecek) kayitlar log'a dusurulur —
    prompt kurali: "karsiligi olmayan bir enstruman varsa o kaydi atla, log'a dus".
    Doner: (kapsanan_kayitlar, kapsanmayan_enstrumanlar)
    """
    kapsanan = [k for k in seviyeler if k["enstruman"] in taranan_semboller]
    eksik = sorted({k["enstruman"] for k in seviyeler
                    if k["enstruman"] not in taranan_semboller})
    if eksik:
        log(f"[ONEMLI] Taramada karsiligi olmayan {len(eksik)} enstruman atlandi: "
            + ", ".join(eksik))
    return kapsanan, eksik


# --------------------------------------------------------------------------
# Yon ve mesafe
# --------------------------------------------------------------------------

def mesafe_hesapla(fiyat, kayit):
    """Fiyatin seviyeye (banda) yuzde mesafesi. Bandin ICINDE ise 0.0.

    Isaret: fiyat seviyenin ustundeyse +, altindaysa -.
    """
    alt, ust = kayit["_alt"], kayit["_ust"]
    if alt <= fiyat <= ust:
        return 0.0
    if fiyat > ust:
        return (fiyat - ust) / ust * 100
    return (fiyat - alt) / alt * 100


def yon_belirle(fiyat, kayit):
    """Doner: (yon, gerekce).

    Tek seviye / band DISI: geometrik — fiyat ustundeyse seviye DESTEK (long),
    altindaysa DIRENC (short).
    Band ICINDE: geometri yon veremez (iki tarafi da var), bu yuzden kaydin
    TURU belirler (direnc_bandi -> short, kritik_destek -> long). Tur de
    bilinmiyorsa banda gore orta noktanin ustunde/altinda olmasina bakilir.
    """
    alt, ust = kayit["_alt"], kayit["_ust"]
    tur = (kayit.get("tur") or "").lower()

    if fiyat > ust:
        return "long", "fiyat seviyenin ÜSTÜNDE — seviye destek"
    if fiyat < alt:
        return "short", "fiyat seviyenin ALTINDA — seviye direnç"

    # Band icinde
    if tur in DIRENC_TURLERI:
        return "short", f"bandın İÇİNDE, tür '{tur}' → direnç bandı"
    if tur in DESTEK_TURLERI:
        return "long", f"bandın İÇİNDE, tür '{tur}' → destek bandı"
    orta = kayit["_orta"]
    return ("long", "bandın İÇİNDE, üst yarıda (tür bilinmiyor — TAHMİN)") if fiyat >= orta \
        else ("short", "bandın İÇİNDE, alt yarıda (tür bilinmiyor — TAHMİN)")


def seviye_metni(kayit):
    """'84.000' veya '16.500-17.000' — gosterim icin."""
    if kayit["_bant_mi"]:
        return f"{_tr(kayit['_alt'])}-{_tr(kayit['_ust'])}"
    return _tr(kayit["_alt"])


def _tr(sayi):
    """Turkce sayi bicimi; buyuklugune gore ondalik secer."""
    try:
        sayi = float(sayi)
    except (TypeError, ValueError):
        return "?"
    m = abs(sayi)
    ondalik = 0 if m >= 1000 else 2 if m >= 10 else 4
    return f"{sayi:,.{ondalik}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# --------------------------------------------------------------------------
# Aday bulma
# --------------------------------------------------------------------------

def adaylari_bul(fiyatlar, seviyeler=None, esik=ONEMLI_SEVIYE_ESIK_YUZDE, log=print):
    """Guncel fiyatlara gore esik icindeki onemli seviye adaylarini dondurur.

    fiyatlar : {sembol: fiyat} — telegram_alarm'in zaten cektigi sozluk
               (kod tekrari yok, ikinci kez fiyat cekilmez).
    Doner: [kayit, ...] — mesafeye gore sirali. Her kayit:
        sembol, fiyat, seviye_alt/ust, seviye_metni, tur, kaynak, aciklama,
        mesafe, yon, gerekce, seviye_id
    """
    if seviyeler is None:
        seviyeler, _ = seviyeleri_oku(log=log)
    adaylar = []
    for kayit in seviyeler:
        try:
            fiyat = fiyatlar.get(kayit["enstruman"])
            if not fiyat:
                continue
            fiyat = float(fiyat)
            mesafe = mesafe_hesapla(fiyat, kayit)
            if abs(mesafe) > esik:
                continue
            yon, gerekce = yon_belirle(fiyat, kayit)
            adaylar.append({
                "sembol": kayit["enstruman"],
                "fiyat": fiyat,
                "seviye_alt": kayit["_alt"],
                "seviye_ust": kayit["_ust"],
                "seviye_metni": seviye_metni(kayit),
                "seviye_orta": kayit["_orta"],
                "tur": kayit.get("tur", ""),
                "kaynak": kayit.get("kaynak", "?"),
                "aciklama": kayit.get("aciklama", ""),
                "tarih_eklendi": kayit.get("tarih_eklendi", ""),
                "mesafe": mesafe,
                "yon": yon,
                "gerekce": gerekce,
                "seviye_id": kayit["_id"],
            })
        except (TypeError, ValueError) as e:
            log(f"[ONEMLI][UYARI] {kayit.get('enstruman')} degerlendirilemedi: "
                f"{type(e).__name__}: {e}")
            continue
    adaylar.sort(key=lambda k: abs(k["mesafe"]))
    return adaylar


# --------------------------------------------------------------------------
# Mega-confluence
# --------------------------------------------------------------------------

def mega_confluence_bul(teknik_kayitlar, onemli_adaylar,
                        esik=MEGA_CONFLUENCE_ESIK_YUZDE, log=print):
    """Teknik MagicMA cizgisi ile onemli seviye AYNI fiyat bolgesinde mi?

    teknik_kayitlar : telegram_alarm.sonuclari_kayda_cevir() ciktisinin
        degerleri — her biri {sembol, cizgi_adi, cizgi, fiyat, yon, ...}.
        BURAYA yalnizca GIRIS esigine (%0,25) girmis teknik kayitlar verilmeli.
    onemli_adaylar : adaylari_bul() ciktisi (%0,5 icinde).

    Eslesme sarti: ayni sembol VE teknik cizgi degeri ile onemli seviye
    (band ise en yakin siniri) arasindaki fark <= esik.

    Doner: [mega_kayit, ...] — teknik + temel bilgiyi birlikte tasir.
    Ayni sembolde birden fazla eslesme olursa EN YAKIN olan tutulur; amac
    tek bir vurgulu bildirim, ayni sembol icin bir yigin mesaj degil.
    """
    if not teknik_kayitlar or not onemli_adaylar:
        return []

    onemli_sembol = {}
    for aday in onemli_adaylar:
        onemli_sembol.setdefault(aday["sembol"], []).append(aday)

    en_iyi = {}
    for teknik in teknik_kayitlar:
        sembol = teknik.get("sembol")
        cizgi = teknik.get("cizgi")
        if sembol not in onemli_sembol or not cizgi:
            continue
        for aday in onemli_sembol[sembol]:
            try:
                # Cizgi bandin ICINDEyse zaten ayni bolgedeler: fark 0.
                # Disindaysa cizgiye EN YAKIN sinir baz alinir (tek seviyede
                # iki sinir ayni sayidir, formul degismez).
                if aday["seviye_alt"] <= cizgi <= aday["seviye_ust"]:
                    fark = 0.0
                else:
                    yakin_sinir = min((aday["seviye_alt"], aday["seviye_ust"]),
                                      key=lambda s: abs(s - cizgi))
                    fark = abs(cizgi - yakin_sinir) / yakin_sinir * 100
            except (TypeError, ZeroDivisionError):
                continue
            if fark > esik:
                continue
            mega = {
                "sembol": sembol,
                "fiyat": teknik.get("fiyat") or aday["fiyat"],
                "teknik_cizgi_adi": teknik.get("cizgi_adi", "?"),
                "teknik_cizgi": cizgi,
                "teknik_mesafe": teknik.get("mesafe"),
                "teknik_yon": teknik.get("yon"),
                "teknik_anahtar": teknik.get("anahtar"),
                "seviye_metni": aday["seviye_metni"],
                "seviye_alt": aday["seviye_alt"],
                "seviye_ust": aday["seviye_ust"],
                "tur": aday["tur"],
                "kaynak": aday["kaynak"],
                "aciklama": aday["aciklama"],
                "onemli_mesafe": aday["mesafe"],
                "onemli_yon": aday["yon"],
                "seviye_id": aday["seviye_id"],
                "ayrim_yuzde": fark,
                # Yon: teknik yon esas alinir (bant mantigi daha olgun); ikisi
                # ayrisiyorsa bu bilgi mesajda gosterilmez ama logda tutulur.
                "yon": teknik.get("yon") or aday["yon"],
                "yon_uyusuyor": teknik.get("yon") == aday["yon"],
            }
            onceki = en_iyi.get(sembol)
            if onceki is None or fark < onceki["ayrim_yuzde"]:
                en_iyi[sembol] = mega

    sonuc = sorted(en_iyi.values(), key=lambda m: m["ayrim_yuzde"])
    if sonuc:
        log("[MEGA] " + str(len(sonuc)) + " mega-confluence: "
            + ", ".join(f"{m['sembol']}({m['kaynak'].split('(')[0].strip()})"
                        for m in sonuc))
        for m in sonuc:
            if not m["yon_uyusuyor"]:
                log(f"[MEGA][NOT] {m['sembol']}: teknik yön {m['teknik_yon']} ile "
                    f"seviye yönü {m['onemli_yon']} ayrışıyor; teknik yön kullanıldı.")
    return sonuc


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Onemli seviye kutuphanesi kontrolu")
    ap.add_argument("--dogrula", action="store_true",
                    help="sadece kutuphaneyi dogrula, fiyat cekme")
    ap.add_argument("--esik", type=float, default=ONEMLI_SEVIYE_ESIK_YUZDE,
                    help=f"mesafe esigi yuzde (varsayilan {ONEMLI_SEVIYE_ESIK_YUZDE})")
    args = ap.parse_args()

    def _yaz(*a):
        metin = " ".join(str(x) for x in a)
        try:
            print(metin)
        except UnicodeEncodeError:
            print(metin.encode("ascii", "replace").decode("ascii"))

    seviyeler, atlanan = seviyeleri_oku(log=_yaz)
    _yaz(f"Kutuphane: {len(seviyeler)} gecerli kayit, {len(atlanan)} atlandi.")
    enstrumanlar = sorted({k["enstruman"] for k in seviyeler})
    _yaz(f"Enstruman ({len(enstrumanlar)}): " + ", ".join(enstrumanlar))
    kaynaklar = sorted({k.get("kaynak", "?") for k in seviyeler})
    _yaz(f"Kaynak ({len(kaynaklar)}): " + " · ".join(kaynaklar))

    if args.dogrula:
        return 0

    v = fiyat_kontrol.adaylari_hesapla(esik=0.25, log=_yaz)
    fiyatlar = v.get("tum_fiyatlar", {})
    seviyeler, _ = kapsam_denetle(seviyeler, set(fiyatlar), log=_yaz)

    adaylar = adaylari_bul(fiyatlar, seviyeler, esik=args.esik, log=_yaz)
    _yaz(f"\n=== ONEMLI SEVIYE: %{args.esik} icinde {len(adaylar)} aday ===")
    for a in adaylar:
        _yaz(f"{a['sembol']:10s} fiyat={_tr(a['fiyat']):>12s}  seviye={a['seviye_metni']:>16s}  "
             f"mesafe=%{a['mesafe']:+.3f}  {a['yon'].upper():5s}  [{a['kaynak']}] {a['tur']}")

    # Mega-confluence: teknik kayitlar telegram_alarm'daki gibi kurulur.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import telegram_alarm
    teknik = list(telegram_alarm.sonuclari_kayda_cevir(v["sonuclar"]).values())
    mega = mega_confluence_bul(teknik, adaylar, log=_yaz)
    _yaz(f"\n=== MEGA-CONFLUENCE: {len(mega)} ===")
    for m in mega:
        _yaz(f"{m['sembol']}: teknik {m['teknik_cizgi_adi']} {_tr(m['teknik_cizgi'])} "
             f"+ {m['kaynak']} {m['seviye_metni']} (ayrim %{m['ayrim_yuzde']:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
