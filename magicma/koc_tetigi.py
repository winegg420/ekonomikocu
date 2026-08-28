"""
magicma/koc_tetigi.py

Koc'un BTC icin verdigi UC KOSULLU boga tetigini takip eder
(06_ANALIZ.md, "2. Yukselis tetigi (3 kosul)"):

    DXY 110 -> 95  ·  faiz indirimi  ·  Cin/emtia anlasmasi
    Koc: "Once anlasmalar gelmeli."

Aktif kosul SAYISI degistiginde (orn. 1/3 -> 2/3) Telegram'a bildirim gider;
degismediyse SESSIZ kalir (spam olmasin).

DURUSTLUK NOTU — uc kosulun otomasyon seviyesi FARKLI, mesajda da boyle sunulur:

  1. DXY        : TAM OTOMATIK. Canli fiyatla olculur.
  2. Faiz       : CANLI DEGIL. Ucretsiz/kolay bir FedWatch ucu yok. Vekil olarak
                  11_DIS_KAYNAKLAR.md'de EN SON gecen faiz ifadesi okunur. Bu,
                  "son eklenen kaynagin o anki gorusu"dur — mesajda kaynak adi ve
                  tarihiyle etiketlenir, gercek zamanliymis gibi SUNULMAZ.
  3. Cin/ABD    : Ikili olay, surekli taranamaz. koc_tetigi_durum.json icinde
                  ELLE guncellenen bayrak. Script bunu ASLA kendisi degistirmez.

Kullanim:
    py -3 magicma/koc_tetigi.py --kuru     # gondermeden ekrana yaz
    py -3 magicma/koc_tetigi.py            # durum degistiyse Telegram'a gonder
    py -3 magicma/koc_tetigi.py --zorla    # degismese de gonder
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fiyat_kontrol
import magicma_karne

REPO_KOK = fiyat_kontrol.REPO_KOK
DURUM_YOL = os.path.join(REPO_KOK, "magicma", "koc_tetigi_durum.json")
SON_DURUM_YOL = os.path.join(REPO_KOK, "magicma", "koc_tetigi_son_durum.json")
KAYNAK_MD = os.path.join(REPO_KOK, "11_DIS_KAYNAKLAR.md")
TSI = magicma_karne.TSI

# --- Kosul 1: DXY ---------------------------------------------------------
DXY_BASLANGIC = 110.0       # Koc'un verdigi baslangic
DXY_HEDEF = 95.0            # Koc'un verdigi hedef
DXY_ESIK_YUZDE = 80         # yolun >= %80'i kat edildiyse kosul AKTIF

# --- Kosul 2: faiz --------------------------------------------------------
# Basit anahtar kelime eslestirmesi; mukemmel NLP gerekmiyor ama OLUMSUZLAMA
# ele alinmak ZORUNDA: "Fed faiz ARTIRMAZ" cumlesi icinde "faiz artır" gecer ve
# duz eslestirme bunu sahin sanip yon TERS okur (olculdu, gercek satirda oldu).
# Cozum: olumsuz cekimler AYRI kalip olarak ve ters kutuya yazilir; ayni
# konumda eslesen kaliplardan EN UZUNU kazanir ("faiz artırmaz" > "faiz artır").
INDIRIM_KALIPLARI = (
    "faiz indir", "faizi indir", "faiz indirimi", "indirim ihtimal",
    "güvercin", "guvercin",
    # olumsuz artirim = indirim yonu
    "faiz artırmaz", "faiz artirmaz", "faiz artıramaz", "faiz artiramaz",
    "faiz artırmayacak", "artırmayacak", "artıramazlar", "artirmaz",
)
ARTIRIM_KALIPLARI = (
    "faiz artır", "faiz artir", "faizi artır", "faiz artırımı", "artırım ihtimal",
    "şahin", "sahin",
    # olumsuz indirim = artirim yonu
    "faiz indirmez", "faiz indiremez", "indiremezler", "faiz indirmeyecek",
    "indiremez", "indirmez",
    "inmez", "inmeyecek",                  # "37'nin ALTINA inmez" — bkz. SART_ARANAN
)

# Bu kaliplar tek baslarina cok genel ("80 $ altına inmez" petrol icin de gecer);
# yalnizca satirda "faiz" kelimesi de geciyorsa sayilirlar.
SART_ARANAN = ("inmez", "inmeyecek", "indiremez", "indirmez",
               "artirmaz", "artıramazlar", "artırmayacak")

# Koc'un kosulu ABD/Fed faiz indirimi. TCMB / TR politika faizi cumleleri bu
# tetigin konusu DEGILDIR; en sonda gecen faiz ifadesi TR'ye aitse atlanip bir
# oncekine bakilir. (Olculdu: "Politika faizi 37'nin ALTINA inmez" satiri Fed
# tetigini yanlislikla 'artirim' yonune cekiyordu.)
TR_KALIPLARI = ("tcmb", "politika faizi", "haftalık repo", "haftalik repo",
                "merkez bankası başkan", "karahan")


def log_yap(sessiz=False):
    def _log(*a):
        if sessiz:
            return
        metin = " ".join(str(x) for x in a)
        try:
            print(metin)
        except UnicodeEncodeError:
            print(metin.encode("ascii", "replace").decode("ascii"))
    return _log


# --------------------------------------------------------------------------
# Kosul 1 — DXY (tam otomatik)
# --------------------------------------------------------------------------

def dxy_ilerleme(dxy):
    """110'dan 95'e olan yolun yuzde kaci kat edildi?

    (110 - guncel) / (110 - 95) * 100. 110 uzerinde negatif, 95 altinda %100+.
    """
    try:
        return (DXY_BASLANGIC - float(dxy)) / (DXY_BASLANGIC - DXY_HEDEF) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def kosul_dxy(fiyatlar, log=print):
    """Doner: (aktif_mi, ayrinti_sozlugu)."""
    dxy = fiyatlar.get("DXY")
    if not dxy:
        log("[TETIK][UYARI] DXY fiyati alinamadi — kosul 1 'aktif degil' sayiliyor.")
        return False, {"dxy": None, "ilerleme": None, "kalan": None}
    ilerleme = dxy_ilerleme(dxy)
    kalan = float(dxy) - DXY_HEDEF          # 95'e kac puan kaldi
    return (ilerleme is not None and ilerleme >= DXY_ESIK_YUZDE), {
        "dxy": float(dxy), "ilerleme": ilerleme, "kalan": kalan}


# --------------------------------------------------------------------------
# Kosul 2 — faiz (CANLI DEGIL, dis kaynak vekili)
# --------------------------------------------------------------------------

def _basliklari_haritala(satirlar):
    """{satir_no: (kaynak_adi, tarih_basligi)} — o satirin ait oldugu kaynak.

    Iki basamakli: `## ISIM` bolum kaynagi verir. Ancak "## EK — ... OTURUMU"
    derleme bolumlerinde TEK basligin altinda BIRDEN FAZLA kaynak var ve bunlar
    `### 3) ONUR DUYGU — ...` seklinde numarali alt basliklarla ayriliyor;
    o durumda kaynak alt basliktan alinir. (Olculdu: bu olmadan Onur Duygu'nun
    cumlesi Kemal Hicyilmaz'a atfediliyordu.)
    """
    harita, bolum, alt_kaynak, tarih = {}, "?", None, ""
    for no, satir in enumerate(satirlar):
        s = satir.strip()
        if s.startswith("## "):
            baslik = s[3:].strip()
            tarih, alt_kaynak = "", None
            if not baslik.startswith(("EK", "ÖZET")):
                bolum = baslik.split("(")[0].split("—")[0].strip()
            else:
                bolum = None                     # derleme bolumu: kaynak alt basliktan
        elif s.startswith("### "):
            baslik = s[4:].strip()
            # "3) ONUR DUYGU (Font Turkey kurucusu) — ForInvest ..." -> ONUR DUYGU
            numarali = re.match(r"^\d+\)\s*(.+)$", baslik)
            if numarali:
                alt_kaynak = numarali.group(1).split("(")[0].split("—")[0].strip()
                tarih = ""
            else:
                tarih = baslik.split("—")[0].split("(")[0].strip()
        harita[no] = (alt_kaynak or bolum or "?", tarih)
    return harita


def kosul_faiz(yol=KAYNAK_MD, log=print):
    """11_DIS_KAYNAKLAR.md'de EN SON gecen faiz ifadesini bulur.

    "Faiz indirimi" temaliysa kosul AKTIF, "faiz artirimi" temaliysa DEGIL.
    Ayni satirda ikisi de geciyorsa satirdaki SON gecen kalip belirler
    (metin genelde "artirim degil indirim" gibi ilerliyor).

    Doner: (aktif_mi, {ifade, kaynak, tarih, satir_no})
    """
    bos = {"ifade": "", "kaynak": "?", "tarih": "", "satir_no": None}
    try:
        with open(yol, encoding="utf-8") as f:
            satirlar = f.read().splitlines()
    except OSError as e:
        log(f"[TETIK][UYARI] {yol} okunamadi: {type(e).__name__}: {e}")
        return False, bos

    harita = _basliklari_haritala(satirlar)
    bulunan, atlanan_tr = None, 0
    for no in range(len(satirlar) - 1, -1, -1):        # DOSYADA EN SONDA gecen
        yon = _satir_yonu(satirlar[no])
        if yon is None:
            continue
        if _tr_faizi_mi(satirlar[no]):                 # TCMB/TR faizi: konu disi
            atlanan_tr += 1
            continue
        bulunan = (no, satirlar[no].strip(), yon)
        break

    if atlanan_tr:
        log(f"[TETIK] {atlanan_tr} TCMB/TR faiz satiri atlandi (Koc'un kosulu Fed faizi).")

    if bulunan is None:
        log("[TETIK] 11_DIS_KAYNAKLAR.md'de (Fed baglaminda) faiz ifadesi bulunamadi.")
        return False, bos

    no, metin, yon = bulunan
    kaynak, tarih = harita.get(no, ("?", ""))
    # KARNE tablolari kaynagi KENDI satirlarinda tasir
    # (`| Onur Duygu | 24 Ağu | Fed faiz ARTIRMAZ | İZLENİYOR |`). Basliktan
    # gelen kaynak burada YANLIS olur (tablonun ustundeki son alt basligi verir);
    # bu yuzden tablo satirinda hucreler esas alinir.
    hucre_kaynak, hucre_tarih, hucre_ifade = _tablo_satiri_coz(metin)
    if hucre_kaynak:
        kaynak, tarih, metin = hucre_kaynak, hucre_tarih or tarih, hucre_ifade or metin
    return yon == "indirim", {"ifade": _ifade_kisalt(metin), "kaynak": kaynak,
                              "tarih": tarih, "satir_no": no + 1}


def _tablo_satiri_coz(satir):
    """Markdown tablo satirindan (kaynak, tarih, ifade) cikarir; degilse (None,)*3.

    Bu dosyadaki KARNE tablolari iki bicimde:
      | Kaynak | Tarih | Iddia | Sonuc |     (derleme tablolari)
      | Tarih  | Iddia | Sonuc |             (tek kaynagin kendi tablosu)
    Ilk hucre tarih gibi duruyorsa birinci bicim degildir — kaynak basliktan
    gelmeye devam eder.
    """
    s = satir.strip()
    if not (s.startswith("|") and s.count("|") >= 3):
        return None, None, None
    hucreler = [h.strip() for h in s.strip("|").split("|")]
    if len(hucreler) < 3 or set(hucreler[0]) <= set("-: "):      # ayirici satir
        return None, None, None
    if _tarih_gibi(hucreler[0]):
        return None, hucreler[0], hucreler[1]                    # kaynaksiz bicim
    return hucreler[0], hucreler[1], " · ".join(hucreler[2:-1]) or hucreler[2]


_AY = ("oca", "şub", "sub", "mar", "nis", "may", "haz", "tem",
       "ağu", "agu", "eyl", "eki", "kas", "ara")


def _tarih_gibi(metin):
    """'24 Ağu', '13-14 Ağu', 'Ağu 2026', '?' gibi tarih hucresi mi?"""
    t = (metin or "").lower()
    if not t or t == "?":
        return True
    return any(ay in t for ay in _AY) or bool(re.match(r"^[\d\s\-/.]+$", t))


def _satir_yonu(satir):
    """Satirdaki faiz ifadesinin yonu: 'indirim' | 'artirim' | None.

    Kural: satirdaki EN SON konumda eslesen kalip belirler; ayni konumda
    birden fazla kalip eslesirse EN UZUN olani kazanir — boylece
    "faiz artırmaz" (indirim yonu), icinde gecen "faiz artır" (artirim yonu)
    tarafindan ezilmez.
    """
    alt = satir.lower()
    faiz_var = "faiz" in alt
    en_iyi = None                                    # (konum, uzunluk, yon)
    for kaliplar, yon in ((INDIRIM_KALIPLARI, "indirim"), (ARTIRIM_KALIPLARI, "artirim")):
        for kalip in kaliplar:
            k = kalip.lower()
            if k in SART_ARANAN and not faiz_var:
                continue                             # cok genel kalip, baglam yok
            konum = alt.rfind(k)
            if konum < 0:
                continue
            aday = (konum, len(kalip), yon)
            if en_iyi is None or aday[:2] > en_iyi[:2]:
                en_iyi = aday
    return en_iyi[2] if en_iyi else None


def _tr_faizi_mi(satir):
    """Satir TCMB / TR politika faizi hakkinda mi? (Koc'un kosulu Fed faizi.)"""
    alt = (satir or "").lower()
    return any(k in alt for k in TR_KALIPLARI)


def _ifade_kisalt(metin, azami=150):
    """Markdown suslerini temizler, mesaja sigacak uzunluga kisaltir."""
    t = re.sub(r"[|*_>#`]", " ", metin)
    t = re.sub(r"\s+", " ", t).strip(" -")
    return t if len(t) <= azami else t[:azami - 1].rstrip() + "…"


# --------------------------------------------------------------------------
# Kosul 3 — Cin/ABD anlasmasi (ELLE bayrak)
# --------------------------------------------------------------------------

def kosul_cin(yol=DURUM_YOL, log=print):
    """koc_tetigi_durum.json'daki elle bayragi OKUR — asla yazmaz."""
    if not os.path.exists(yol):
        log(f"[TETIK] {yol} yok — Cin/ABD kosulu 'henuz yok' sayiliyor.")
        return False, {"dayanak": "", "son_guncelleme": ""}
    try:
        with open(yol, encoding="utf-8") as f:
            veri = json.load(f)
        return bool(veri.get("cin_abd_anlasma")), {
            "dayanak": veri.get("dayanak", ""),
            "son_guncelleme": veri.get("son_guncelleme", "")}
    except (OSError, ValueError) as e:
        log(f"[TETIK][UYARI] {yol} okunamadi: {type(e).__name__}: {e}")
        return False, {"dayanak": "", "son_guncelleme": ""}


# --------------------------------------------------------------------------
# Durum karsilastirma
# --------------------------------------------------------------------------

def son_durum_oku(yol=SON_DURUM_YOL):
    if not os.path.exists(yol):
        return None
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def son_durum_yaz(aktif_sayi, kosullar, an=None, yol=SON_DURUM_YOL):
    an = an or datetime.now(TSI)
    try:
        with open(yol, "w", encoding="utf-8") as f:
            json.dump({"aktif_sayi": aktif_sayi, "kosullar": kosullar,
                       "guncelleme": an.isoformat(timespec="seconds")},
                      f, ensure_ascii=False, indent=1)
    except OSError as e:
        print(f"[TETIK][UYARI] durum yazilamadi: {type(e).__name__}: {e}")


# --------------------------------------------------------------------------
# Mesaj
# --------------------------------------------------------------------------

def _tr(sayi, ondalik=2):
    try:
        return f"{float(sayi):,.{ondalik}f}".replace(",", "\x00").replace(
            ".", ",").replace("\x00", ".")
    except (TypeError, ValueError):
        return "?"


def mesaj_olustur(aktif_sayi, dxy_aktif, dxy_bilgi, faiz_aktif, faiz_bilgi,
                  cin_aktif, cin_bilgi, btc):
    im = lambda x: "✅" if x else "❌"
    s = [f"\U0001F3AF KOÇ'UN BOĞA TETİĞİ — {aktif_sayi}/3 KOŞUL AKTİF", ""]

    if dxy_bilgi.get("dxy") is None:
        s.append(f"{im(dxy_aktif)} DXY: fiyat alınamadı")
    else:
        s.append(f"{im(dxy_aktif)} DXY {_tr(dxy_bilgi['dxy'])} "
                 f"(110→95 yolunun %{_tr(dxy_bilgi['ilerleme'], 1)}'i katedildi, "
                 f"95'e {_tr(dxy_bilgi['kalan'])} puan kaldı)")

    faiz_metin = faiz_bilgi.get("ifade") or "ifade bulunamadı"
    kaynak = faiz_bilgi.get("kaynak") or "?"
    tarih = faiz_bilgi.get("tarih") or ""
    s.append(f"{im(faiz_aktif)} Faiz: {faiz_metin}")
    s.append(f"   ↳ kaynak: {kaynak}" + (f", {tarih}" if tarih else "")
             + " (canlı veri DEĞİL — son eklenen kaynağın görüşü)")

    cin_metin = "var" if cin_aktif else "henüz yok"
    s.append(f"{im(cin_aktif)} Çin-ABD anlaşması: {cin_metin}"
             + (f" — {cin_bilgi['dayanak']}" if cin_aktif and cin_bilgi.get("dayanak") else ""))

    s.append("")
    btc_metin = _tr(btc, 0) if btc else "?"
    durum = "devrede" if aktif_sayi >= 3 else "henüz tamamlanmadı"
    s.append(f"BTC şu an {btc_metin} — {aktif_sayi}/3 koşulla Koç'un tezi {durum}.")
    return "\n".join(s)


# --------------------------------------------------------------------------

def degerlendir(fiyatlar=None, log=print):
    """Uc kosulu olcup (aktif_sayi, metin, kosul_ozeti) dondurur."""
    if fiyatlar is None:
        v = fiyat_kontrol.adaylari_hesapla(esik=0.0, log=lambda *a, **k: None)
        fiyatlar = v.get("tum_fiyatlar", {})

    dxy_aktif, dxy_bilgi = kosul_dxy(fiyatlar, log=log)
    faiz_aktif, faiz_bilgi = kosul_faiz(log=log)
    cin_aktif, cin_bilgi = kosul_cin(log=log)
    aktif_sayi = sum((dxy_aktif, faiz_aktif, cin_aktif))

    log(f"[TETIK] DXY: {'AKTIF' if dxy_aktif else 'pasif'} "
        f"({_tr(dxy_bilgi.get('dxy'))}, ilerleme %{_tr(dxy_bilgi.get('ilerleme'), 1)}, "
        f"esik %{DXY_ESIK_YUZDE}) · "
        f"Faiz: {'AKTIF' if faiz_aktif else 'pasif'} (satir {faiz_bilgi.get('satir_no')}, "
        f"{faiz_bilgi.get('kaynak')}) · "
        f"Cin/ABD: {'AKTIF' if cin_aktif else 'pasif'} (elle bayrak) "
        f"-> {aktif_sayi}/3")

    metin = mesaj_olustur(aktif_sayi, dxy_aktif, dxy_bilgi, faiz_aktif, faiz_bilgi,
                          cin_aktif, cin_bilgi, fiyatlar.get("BTCUSDT"))
    ozet = {"dxy": dxy_aktif, "faiz": faiz_aktif, "cin_abd": cin_aktif}
    return aktif_sayi, metin, ozet


def main():
    ap = argparse.ArgumentParser(description="Koc'un 3 kosullu boga tetigi takibi")
    ap.add_argument("--kuru", action="store_true",
                    help="Telegram'a gonderme, sadece ekrana yaz")
    ap.add_argument("--zorla", action="store_true",
                    help="aktif kosul sayisi degismese de gonder")
    args = ap.parse_args()
    log = log_yap()

    aktif_sayi, metin, ozet = degerlendir(log=log)
    onceki = son_durum_oku()
    onceki_sayi = onceki.get("aktif_sayi") if onceki else None
    degisti = onceki_sayi is None or onceki_sayi != aktif_sayi

    if args.kuru:
        log(f"\nOnceki: {onceki_sayi} · simdi: {aktif_sayi} · "
            f"{'DEGISTI -> gonderilirdi' if degisti else 'degismedi -> sessiz kalinirdi'}")
        log("\n--- MESAJ (kuru mod) ---")
        log(metin)
        log("--- son ---")
        return 0

    if not degisti and not args.zorla:
        log(f"Aktif kosul sayisi degismedi ({aktif_sayi}/3) — sessiz kalindi.")
        son_durum_yaz(aktif_sayi, ozet)          # kosul detayi degismis olabilir
        return 0

    import telegram_alarm
    token, chat_id = telegram_alarm.telegram_bilgileri()
    if telegram_alarm.telegram_gonder(token, chat_id, metin):
        log(f"Tetik bildirimi gonderildi ({onceki_sayi} -> {aktif_sayi}).")
        son_durum_yaz(aktif_sayi, ozet)
        return 0
    log("[HATA] Tetik bildirimi gonderilemedi — durum GUNCELLENMEDI, "
        "sonraki turda tekrar denenecek.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
