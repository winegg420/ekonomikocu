"""
magicma/telegram_alarm.py

Amac: magicma/fiyat_kontrol.py'nin hesapladigi "cizgiye yapisik" listeyi
(varsayilan giris esigi %0,25 — CLAUDE.md MAGICMA RAPOR FORMAT KURALI) her
calismada Telegram'a bildirir.

DAVRANIS DEGISIKLIGI (2026-08-28, kullanici istegi):
  Bildirim artik SADECE yeni temaslari degil, O ANDA hala cizgiye yakin olan
  TUM adaylari her mesajda bastan listeler. Amac: her bildirimde guncel islem
  firsatlarinin tamamini tek listede gormek. Bu turda listeye YENI giren
  adaylarin basina 🆕 konur; digerleri de tekrar listelenir.

Tasarim kararlari:
  - Fiyat cekme mantigi TEKRAR YAZILMAZ; fiyat_kontrol.adaylari_hesapla()
    import edilir.
  - Durum dosyasi: magicma/alarm_son_durum.json. Anahtar = "SEMBOL|BANT_ADI".
    Durum artik "kimi bildirdim" icin degil, HISTEREZIS ve "yeni mi" isareti
    icin tutulur.
  - Histerezis: bir kayit giris esigine (%0,25) girince listeye alinir ve ancak
    cikis esigini (varsayilan giris x2) asinca listeden duser.
  - Yakin aday YOKSA hicbir mesaj gonderilmez (sessiz kalir).
  - Piyasasi kapali sembol (BIST/ABD) hic taranmaz; kapandigi icin listeden
    dusen kayit "listeden cikti" diye BILDIRILMEZ, sessizce duser.

TEK MESAJ (spam onleme):
  1. Tarama araligi 10 dk (Task Scheduler).
  2. Bir turun TUM adaylari TEK mesajda gider — mesaj asla parcalanmaz;
     sinira sigmazsa kesilir ve "+N aday daha" yazilir.
  3. Iki mesaj arasi EN AZ `--mesaj-araligi` dakika (varsayilan 10). Sure
     dolmadiysa o tur sessiz gecer; kuyruk BIRIKMEZ, cunku bir sonraki turun
     listesi zaten daha guncelini tasir.

Kullanim:
    py -3 magicma/telegram_alarm.py
    py -3 magicma/telegram_alarm.py --esik 0.4
    py -3 magicma/telegram_alarm.py --kuru             # gondermeden ekrana yaz
    py -3 magicma/telegram_alarm.py --mesaj-araligi 0  # bekletme yok (test)

Gizli bilgi: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID repo kokundeki .env
dosyasindan okunur (.gitignore'da, ASLA commit edilmez).
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
except ImportError:
    print("Once 'pip install requests' calistir.")
    sys.exit(1)

import fiyat_kontrol
import magicma_karne
import onemli_seviye
import gunluk_ozet
import koc_tetigi

REPO_KOK = fiyat_kontrol.REPO_KOK
ENV_YOL = os.path.join(REPO_KOK, ".env")
DURUM_YOL = os.path.join(REPO_KOK, "magicma", "alarm_son_durum.json")
LOG_YOL = os.path.join(REPO_KOK, "magicma", "telegram_alarm_log.txt")
LOG_MAX_BAYT = 512 * 1024    # log buyuyunce son yarisi tutulur
TELEGRAM_MAX = 3900          # Telegram siniri 4096; guvenli pay birakiliyor

# Mesaj araligi kontrolu icin PAY. Neden gerekli: gorev 10 dk'da bir baslar ama
# tarama ~25-35 sn surer ve suresi her turda birkac saniye oynar. Mesaj tarama
# BITTIKTEN sonra gonderildigi icin, bir sonraki turun kontrol ani bazen bir
# onceki gonderimden 9,9 dk sonraya dusuyordu; 10 dk esigi 5 saniyeyle kacinca
# bildirim BIR TUR DAHA bekliyor ve kullaniciya 20 dk sonra ulasiyordu
# (olculdu: 15:10:31 gonderim -> 15:20:26 kontrol = 9.9 dk -> bloke -> 15:30).
# Bu pay o sinir yarisini ortadan kaldirir; elle art arda calistirma yine bloke.
ARALIK_TOLERANS_DK = 2.0


def log(mesaj):
    """Konsola ve magicma/telegram_alarm_log.txt'ye yazar.

    Task Scheduler bu scripti penceresiz (pyw.exe) calistirdigi icin konsol
    ciktisi kayboluyor; dosya logu tek izlenebilir kayit.
    """
    satir = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {mesaj}"
    try:
        print(satir, flush=True)
    except Exception:
        pass
    try:
        if os.path.exists(LOG_YOL) and os.path.getsize(LOG_YOL) > LOG_MAX_BAYT:
            with open(LOG_YOL, encoding="utf-8", errors="replace") as f:
                kuyruk = f.read()[-LOG_MAX_BAYT // 2:]
            with open(LOG_YOL, "w", encoding="utf-8") as f:
                f.write(kuyruk)
        with open(LOG_YOL, "a", encoding="utf-8") as f:
            f.write(satir + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------
# .env
# --------------------------------------------------------------------------

def env_oku(yol=ENV_YOL):
    """Basit satir-satir .env ayristirici (ek bagimlilik istemiyoruz)."""
    degerler = {}
    if not os.path.exists(yol):
        return degerler
    try:
        with open(yol, encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()
                if not satir or satir.startswith("#") or "=" not in satir:
                    continue
                anahtar, _, deger = satir.partition("=")
                degerler[anahtar.strip()] = deger.strip().strip('"').strip("'")
    except OSError as e:
        log(f"[HATA] .env okunamadi: {type(e).__name__}: {e}")
    return degerler


def telegram_bilgileri():
    env = env_oku()
    token = env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = env.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        log("[HATA] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID bulunamadi.")
        log(f"       Beklenen dosya: {ENV_YOL}")
        log("       Icerik: TELEGRAM_BOT_TOKEN=...  ve  TELEGRAM_CHAT_ID=...")
        sys.exit(1)
    return token, chat


# --------------------------------------------------------------------------
# Durum dosyasi
# --------------------------------------------------------------------------

def durum_oku(yol=DURUM_YOL):
    """Doner: (kayitlar, bekleyen, son_mesaj, ilk_calistirma_mi)

    kayitlar          : {anahtar: kayit} — histerezis listesi
    bekleyen          : [kayit, ...] — bildirilmeyi bekleyen yeni temaslar
    bekleyen_cikanlar : [sembol, ...] — bildirilmeyi bekleyen "listeden cikti"
    son_mesaj         : en son Telegram mesajinin gonderildigi an veya None
    """
    if not os.path.exists(yol):
        return {}, [], [], None, True
    try:
        with open(yol, encoding="utf-8") as f:
            veri = json.load(f)
        kayitlar = veri.get("kayitlar", {})
        if not isinstance(kayitlar, dict):
            raise ValueError("kayitlar sozluk degil")
        bekleyen = veri.get("bekleyen") or []
        if not isinstance(bekleyen, list):
            bekleyen = []
        bekleyen_cikanlar = veri.get("bekleyen_cikanlar") or []
        if not isinstance(bekleyen_cikanlar, list):
            bekleyen_cikanlar = []
        son_mesaj = None
        if veri.get("son_mesaj"):
            try:
                son_mesaj = datetime.fromisoformat(veri["son_mesaj"])
            except ValueError:
                son_mesaj = None
        return kayitlar, bekleyen, bekleyen_cikanlar, son_mesaj, False
    except (OSError, ValueError) as e:
        log(f"[UYARI] {yol} okunamadi ({type(e).__name__}: {e}); ilk calistirma sayiliyor.")
        return {}, [], [], None, True


def durum_yaz(kayitlar, esik, bekleyen=None, son_mesaj=None, cikanlar=None, yol=DURUM_YOL):
    gecici = yol + ".tmp"
    veri = {
        "guncelleme": datetime.now().isoformat(timespec="seconds"),
        "esik": esik,
        "son_mesaj": son_mesaj.isoformat(timespec="seconds") if son_mesaj else None,
        "bekleyen": bekleyen or [],
        "bekleyen_cikanlar": sorted(set(cikanlar or [])),
        "kayitlar": kayitlar,
    }
    try:
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=1)
        os.replace(gecici, yol)
    except OSError as e:
        log(f"[HATA] durum dosyasi yazilamadi: {type(e).__name__}: {e}")


# --------------------------------------------------------------------------
# Bicimlendirme
# --------------------------------------------------------------------------

def _tr(sayi, ondalik=None):
    """1234.5678 -> '1.234,57' (Turkce). ondalik verilmezse buyuklukten secilir."""
    try:
        sayi = float(sayi)
    except (TypeError, ValueError):
        return "?"
    if ondalik is None:
        m = abs(sayi)
        ondalik = 2 if m >= 100 else 4 if m >= 1 else 6 if m >= 0.01 else 8
    metin = f"{sayi:,.{ondalik}f}"
    return metin.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _md_kacir(metin):
    """Telegram Markdown (v1) ozel karakterlerini kacirir."""
    for k in ("_", "*", "`", "["):
        metin = metin.replace(k, "\\" + k)
    return metin


def _cizgi_gosterim(ad):
    """'Magicma Günlük Üst Çizgi' -> 'Günlük Üst'; 'Magicma Haftalık -1' -> 'Haftalık-1'.

    Yalnizca CONFLUENCE satirlarinda kullanilir — tekil bildirimlerde cizgi adi
    gosterilmemeye devam eder (2026-08-28 sade format kurali).
    """
    a = (ad or "").replace("Magicma", "").replace("magicma", "").strip()
    a = a.replace("Çizgi", "").replace("Cizgi", "").strip()
    a = a.replace("Haftalık -", "Haftalık-").replace("Haftalik -", "Haftalik-")
    return a or (ad or "?")


def _yon_metni(kayit):
    yon = kayit.get("yon")
    if yon not in ("long", "short"):                      # eski durum dosyasi yedegi
        yon = "short" if kayit.get("mesafe", 0) < 0 else "long"
    return "LONG" if yon == "long" else "SHORT"


def satir_bicimle(kayit):
    """Bir aday icin TEK satir: SEMBOL · LONG/SHORT · fiyat.

    Bilerek sade: band araligi, "banda yukaridan indi" gibi gerekce metinleri
    ve cizgi adlari mesaja YAZILMAZ (kullanici istegi). Bu bilgiler yon
    hesabinda kullanilmaya devam eder ve durum dosyasi/logda saklanir; sadece
    bildirimde gosterilmez.

    ISTISNA: cakisan seviye (confluence) kaydi cok satirli ozel bicimde gider —
    orada cizgiler bilerek gosterilir, cunku sinyalin gucu tam olarak
    "birden fazla cizginin ayni yerde olmasi"ndan geliyor.
    """
    if kayit.get("kaynak_turu") == "mega_confluence":
        return mega_bicimle(kayit)
    if kayit.get("kaynak_turu") == "onemli_seviye":
        return onemli_bicimle(kayit)
    if kayit.get("confluence"):
        return confluence_bicimle(kayit)
    return f"{kayit['sembol']}  {_yon_metni(kayit)}  {_tr(kayit['fiyat'])}"


def mega_bicimle(kayit):
    """MEGA-CONFLUENCE: teknik MagicMA cizgisi VE Koc/dis kaynak seviyesi ayni
    fiyat bolgesinde. En yuksek oncelikli sinyal — teknik ve temel birlesiyor.

        🌟 MEGA-CONFLUENCE — BTCUSDT
        Fiyat: 83.450
        Teknik: Günlük Üst Çizgi 83.600 (MagicMA)
        Temel: Koç'un 84.000 pivotu (yılın pivotu — kırılmadan rally yok)
        LONG adayı
    """
    kaynak = kayit.get("kaynak", "?")
    tur = (kayit.get("tur") or "seviye").replace("_", " ")
    aciklama = (kayit.get("aciklama") or "").strip()
    satirlar = [
        "\U0001F31F MEGA-CONFLUENCE — " + kayit["sembol"],
        f"Fiyat: {_tr(kayit['fiyat'])}",
        f"Teknik: {_cizgi_gosterim(kayit.get('teknik_cizgi_adi'))} "
        f"{_tr(kayit.get('teknik_cizgi'))} (MagicMA)",
        f"Temel: {kaynak} · {kayit.get('seviye_metni', '?')} ({tur})",
    ]
    if aciklama:
        satirlar.append(aciklama if len(aciklama) <= 120 else aciklama[:117] + "…")
    satirlar.append(f"{_yon_metni(kayit)} adayı")
    return "\n".join(satirlar)


def onemli_bicimle(kayit):
    """Onemli seviye (Koc / dis kaynak) yakinligi — teknik cizgi eslesmesi YOK.

        📌 ÖNEMLİ SEVİYE — XAUUSD  SHORT
        4.460 → Cuneyt Paksoy · 4.400-4.500 (duvar) · %+0,000
    """
    kaynak = kayit.get("kaynak", "?")
    tur = (kayit.get("tur") or "seviye").replace("_", " ")
    mesafe = f"%{kayit.get('mesafe', 0):+.3f}".replace(".", ",")
    return ("\U0001F4CC ÖNEMLİ SEVİYE — " + kayit["sembol"] + "  " + _yon_metni(kayit) + "\n"
            + f"{_tr(kayit['fiyat'])} → {kaynak} · "
              f"{kayit.get('seviye_metni', '?')} ({tur}) · {mesafe}")


def confluence_bicimle(kayit):
    """Cakisan seviye grubu icin 3 satirlik vurgulu blok.

        🔥 ÇAKIŞAN SEVİYE — GARAN
        132,90 → Günlük Üst 132,94 + Haftalık-1 132,88 (2 çizgi çakışıyor)
        %-0,03 / %+0,015 mesafe · SHORT adayı

    Baslik, cakismanin TIPINE gore degisir:
      bantlar_arasi -> "🔥 ÇAKIŞAN SEVİYE" (Gunluk + Haftalik gibi FARKLI
          bantlar ayni bolgeyi isaretliyor — bagimsiz teyit, aranan sinyal bu)
      dar_band      -> "🔥 DAR BAND" (tek bandin alt+ust kenari cok yakin;
          cizgiler cakisiyor ama bagimsiz teyit degil, tek olcum)
    """
    uyeler = kayit.get("confluence_uyeler") or []
    fiyat = kayit["fiyat"]
    cizgiler = " + ".join(f"{_cizgi_gosterim(u['ad'])} {_tr(u['deger'])}" for u in uyeler)
    mesafeler = " / ".join(f"%{u['mesafe']:+.3f}".replace(".", ",") for u in uyeler)
    adet = kayit.get("confluence_sayisi") or len(uyeler)
    if kayit.get("confluence_tip") == "dar_band":
        bas, kuyruk = "\U0001F525 DAR BAND — ", f"({adet} çizgi çakışıyor · tek band)"
    else:
        bas, kuyruk = "\U0001F525 ÇAKIŞAN SEVİYE — ", f"({adet} çizgi çakışıyor)"
    return (bas + kayit["sembol"] + "\n"
            + f"{_tr(fiyat)} → {cizgiler} {kuyruk}\n"
            + f"{mesafeler} mesafe · {_yon_metni(kayit)} adayı")


def mesaj_olustur(bekleyen, cikanlar, simdi=None):
    """O ANDA cizgiye yapisik TUM adaylari TEK mesajda toplar.

    Kullanici istegi (2026-08-28): bildirim yalnizca YENI temaslari degil,
    hala yakin olan tum urunleri her mesajda bastan listeler — boylece her
    bildirimde guncel islem firsatlarinin tamami gorunur. Bu turda listeye
    YENI giren adaylarin basina 🆕 konur.

    Telegram sinirini asarsa mesaj parcalanmaz — kesilir ve kac adayin
    gosterilemedigi sona yazilir (amac: her turda en fazla bir bildirim).
    """
    simdi = simdi or datetime.now()
    son = ""
    if cikanlar:
        son = "\n\n" + _md_kacir("\U0001F4E4 Listeden çıktı: " + ", ".join(cikanlar))

    # Ayni sembol hem Gunluk hem Haftalik banda yakin olabilir; liste artik her
    # mesajda tam gonderildigi icin bu ayni satirin iki kez gorunmesi demek.
    # Sembol+yon basina EN YAKIN kayit tutulur (bekleyen zaten mesafeye sirali).
    # Cakisan seviyeler (confluence) EN USTE alinir: birden fazla bagimsiz
    # cizgi ayni bolgeyi isaretliyor, tekil temastan daha guclu bir sinyal
    # olmasi bekleniyor. `bekleyen` main()'de zaten confluence-once sirali
    # geliyor; burada blok tipine gore ayrilip aralarina bosluk konur.
    # DORT AYRI KATEGORI, oncelik sirasiyla (karistirilmamali):
    #   mega_confluence -> teknik MagicMA cizgisi VE Koc/dis kaynak seviyesi
    #                      ayni bolgede (teknik + temel birlesiyor)
    #   confluence      -> birden fazla MagicMA cizgisi cakisiyor
    #   onemli_seviye   -> yalnizca Koc/dis kaynak seviyesine yakinlik
    #   tekil           -> tek MagicMA cizgisine temas (eski, sade format)
    gorulen = set()
    kutular = {"mega_confluence": [], "confluence": [], "onemli_seviye": [], "tekil": []}
    for kayit in bekleyen:
        imza = (kayit.get("sembol"), kayit.get("yon"))
        if imza in gorulen:
            continue
        gorulen.add(imza)
        blok = satir_bicimle(kayit)
        if kayit.get("yeni"):
            blok = "\U0001F195 " + blok
        tur = kayit.get("kaynak_turu")
        if tur not in ("mega_confluence", "onemli_seviye"):
            tur = "confluence" if kayit.get("confluence") else "tekil"
        kutular[tur].append(_md_kacir(blok))

    toplam = sum(len(v) for v in kutular.values())
    ek = []
    if kutular["mega_confluence"]:
        ek.append(f"{len(kutular['mega_confluence'])} mega")
    if kutular["confluence"]:
        ek.append(f"{len(kutular['confluence'])} çakışan seviye")
    if kutular["onemli_seviye"]:
        ek.append(f"{len(kutular['onemli_seviye'])} önemli seviye")
    bas = "\U0001F4CA " + _md_kacir(
        f"MagicMA İŞLEM FIRSATLARI ({simdi:%d.%m.%Y %H:%M}) · {toplam} aday"
        + (" · " + " · ".join(ek) if ek else ""))

    # Cok satirli bloklarin arasina bos satir; tekiller alt alta tek satir.
    parcalar = []
    for tur in ("mega_confluence", "confluence", "onemli_seviye"):
        parcalar += [(b, "\n\n") for b in kutular[tur]]
    # Tekil listenin ILK ogesi de onceki bolumden bos satirla ayrilir.
    for sira, blok in enumerate(kutular["tekil"]):
        parcalar.append((blok, "\n\n" if sira == 0 and parcalar else "\n"))

    govde, atlanan = "", 0
    for sira, (blok, ayirac) in enumerate(parcalar):
        eklenecek = (ayirac if govde else "") + blok
        if len(bas) + len(govde) + len(eklenecek) + len(son) + 64 > TELEGRAM_MAX and govde:
            atlanan = len(parcalar) - sira
            break
        govde += eklenecek

    metin = bas + ("\n\n" + govde if govde else "")
    if atlanan:
        metin += f"\n… ve {atlanan} aday daha (mesaja sığmadı)"
    return metin + son


# --------------------------------------------------------------------------
# Telegram
# --------------------------------------------------------------------------

def telegram_gonder(token, chat_id, metin):
    """TEK mesaj gonderir. Markdown ayristirma hatasinda duz metne duser.

    Bilerek parcalamaz: amac "her turda EN FAZLA BIR bildirim". Metin sinirdan
    uzunsa kesilir ve kac aday gosterilemedigi sona yazilir — arka arkaya
    birden fazla mesaj dusmesindense tek mesajda ozet tercih edilir.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for parse_mode in ("Markdown", None):
        govde = {"chat_id": chat_id, "text": metin, "disable_web_page_preview": True}
        if parse_mode:
            govde["parse_mode"] = parse_mode
        try:
            r = requests.post(url, data=govde, timeout=20)
            if r.status_code == 200 and r.json().get("ok"):
                return True
            log(f"[UYARI] Telegram yaniti ({parse_mode or 'duz'}): "
                f"{r.status_code} {r.text[:200]}")
        except Exception as e:
            log(f"[UYARI] Telegram istegi basarisiz ({parse_mode or 'duz'}): "
                f"{type(e).__name__}: {e}")
    return False


# --------------------------------------------------------------------------

def sonuclari_kayda_cevir(sonuclar):
    """adaylari_hesapla() tuple'larini {anahtar: kayit} sozlugune cevirir.

    Anahtar SEMBOL|BANT_ADI'dir, SEMBOL|CIZGI_ADI degil: bir bandin iki sinirina
    da ayni anda yaklasilabiliyor ve bu tek bir olay — iki ayri bildirim degil.
    Ayni banttan birden fazla aday gelirse EN YAKIN olani tutulur (sonuclar
    zaten mesafeye gore sirali geldigi icin ilk gelen en yakindir).

    Cakisan seviye (confluence) grubu ISTISNA: grubun tum cizgileri TEK kayda
    duser (anahtar SEMBOL|CONFLUENCE|grup), cunku bu tek bir olay — "su bolge
    birden fazla cizgiyle isaretli". Grup dagilirsa (bir cizgi esikten cikarsa)
    anahtar degisir ve kalan cizgi yeni bir tekil kayit gibi 🆕 isaretlenir;
    sinyalin karakteri gercekten degistigi icin bu istenen davranistir.
    """
    kayitlar = {}
    for _, sembol, canli, ad, deger, mesafe, _yon, kaynak, bant in sonuclar:
        if bant.get("confluence"):
            anahtar = f"{sembol}|CONFLUENCE|{bant.get('confluence_grup')}"
            uyeler = bant.get("confluence_uyeler") or []
            if anahtar in kayitlar:
                continue
            # Grubu, cizgisine EN YAKIN uyesi temsil eder (mesafe/cizgi ondan).
            en_yakin = uyeler[0] if uyeler else {"ad": ad, "deger": deger, "mesafe": mesafe}
            kayitlar[anahtar] = {
                "sembol": sembol,
                "bant_adi": bant["ad"],
                "bant_alt": bant["alt"],
                "bant_ust": bant["ust"],
                "konum": bant["konum"],
                "yon": bant["yon"],
                "gerekce": bant["gerekce"],
                "cizgi_adi": en_yakin["ad"],
                "cizgi": en_yakin["deger"],
                "fiyat": canli,
                "mesafe": en_yakin["mesafe"],
                "kaynak": kaynak,
                "confluence": True,
                "confluence_tip": bant.get("confluence_tip", "bantlar_arasi"),
                "confluence_sayisi": bant.get("confluence_sayisi", len(uyeler)),
                "confluence_cizgiler": bant.get("confluence_cizgiler", []),
                "confluence_bantlar": bant.get("confluence_bantlar", []),
                "confluence_uyeler": uyeler,
            }
            continue

        anahtar = f"{sembol}|{bant['ad']}"
        if anahtar in kayitlar:
            continue
        kayitlar[anahtar] = {
            "sembol": sembol,
            "bant_adi": bant["ad"],
            "bant_alt": bant["alt"],
            "bant_ust": bant["ust"],
            "konum": bant["konum"],
            "yon": bant["yon"],
            "gerekce": bant["gerekce"],
            "cizgi_adi": ad,
            "cizgi": deger,
            "fiyat": canli,
            "mesafe": mesafe,
            "kaynak": kaynak,
            "confluence": False,
            "confluence_tip": "tekil",
        }
    return kayitlar


def main():
    ap = argparse.ArgumentParser(description="MagicMA temas alarmi -> Telegram")
    ap.add_argument("--esik", type=float, default=0.25,
                    help="GIRIS esigi yuzde: bu mesafeye ilk kez giren bildirilir (varsayilan 0.25 — CLAUDE.md kurali)")
    ap.add_argument("--cikis-esik", type=float, default=None,
                    help="CIKIS esigi yuzde (histerezis). Varsayilan: giris esiginin 2 kati. "
                         "Bir sembol listeden ancak bu mesafenin OTESINE gecince duser; "
                         "boylece esik sinirinda salinan semboller her turda yeniden bildirilmez.")
    ap.add_argument("--tarih", default=None, help="sadece bu gunun taramasini kullan (YYYY-AA-GG)")
    ap.add_argument("--max-yas", type=int, default=10, help="seviye yas siniri (gun)")
    ap.add_argument("--kuru", action="store_true", help="Telegram'a gonderme, sadece ekrana yaz")
    ap.add_argument("--zorla", action="store_true",
                    help="(artik etkisiz — liste her mesajda tam gonderiliyor)")
    ap.add_argument("--piyasa-saatini-yoksay", action="store_true",
                    help="BIST/ABD piyasa saati filtresini kapat (kapali piyasayi da tara)")
    ap.add_argument("--onemli-seviye-yok", action="store_true",
                    help="Koc/dis kaynak seviye katmanini kapat (mega-confluence de uretilmez)")
    ap.add_argument("--onemli-esik", type=float,
                    default=onemli_seviye.ONEMLI_SEVIYE_ESIK_YUZDE,
                    help=f"onemli seviye GIRIS esigi yuzde (varsayilan "
                         f"{onemli_seviye.ONEMLI_SEVIYE_ESIK_YUZDE} — MagicMA'dan genis, "
                         f"cunku bunlar hassas teknik cizgi degil kabaca hedef/pivot)")
    ap.add_argument("--karne-yok", action="store_true",
                    help="sinyal karnesi kancasini kapat (kayit acma/degerlendirme yapilmaz)")
    ap.add_argument("--mesaj-araligi", type=float, default=10.0,
                    help="iki Telegram mesaji arasindaki EN AZ dakika (varsayilan 10). "
                         "Bu sure dolmadan bulunan adaylar kuyruga alinir ve sonraki "
                         "mesajda TEK seferde gonderilir. 0 = bekletme yok.")
    args = ap.parse_args()

    cikis_esik = args.cikis_esik if args.cikis_esik is not None else args.esik * 2

    token = chat_id = None
    if not args.kuru:
        token, chat_id = telegram_bilgileri()

    try:
        # Genis bandi (cikis esigi) hesaplat; giris esigi bunun icinden suzulur.
        # piyasa_filtresi: BIST/ABD kapaliyken o sembollerin fiyati hic cekilmez.
        v = fiyat_kontrol.adaylari_hesapla(
            tarih=args.tarih, esik=cikis_esik, max_yas=args.max_yas, log=log,
            piyasa_filtresi=not args.piyasa_saatini_yoksay,
            confluence_esik=args.esik)   # cakisma yalnizca TEMAS eden cizgiler arasinda
    except SystemExit:
        raise
    except Exception as e:
        log(f"[HATA] Fiyat cekme basarisiz, bu tur atlaniyor: {type(e).__name__}: {e}")
        return 1

    genis = sonuclari_kayda_cevir(v["sonuclar"])                       # |mesafe| <= cikis_esik
    temas = {a: k for a, k in genis.items() if abs(k["mesafe"]) <= args.esik}

    # --- IKINCI SEVIYE KAYNAGI: Koc / dis analist seviyeleri ----------------
    # MagicMA cizgileri teknik; bunlar temel/soylem kaynakli hedef-pivot
    # seviyeler. Ayri esikle (%0,5) taranir ve teknik cizgiyle ayni bolgeye
    # denk gelirse MEGA-CONFLUENCE olur. Hata olursa alarm akisi kesilmez.
    genis_onemli, onemli_adaylar, mega_adaylar = [], [], []
    if not args.onemli_seviye_yok:
        try:
            fiyatlar = v.get("tum_fiyatlar") or {}
            kutuphane, _ = onemli_seviye.seviyeleri_oku(log=log)
            kutuphane, _eksik = onemli_seviye.kapsam_denetle(
                kutuphane, set(fiyatlar), log=log)
            # MagicMA ile ayni histerezis deseni: genis bant (cikis esigi)
            # hesaplanir, giris esigi onun icinden suzulur.
            onemli_cikis = args.onemli_esik * 2
            genis_onemli = onemli_seviye.adaylari_bul(
                fiyatlar, kutuphane, esik=onemli_cikis, log=log)
            onemli_adaylar = [a for a in genis_onemli
                              if abs(a["mesafe"]) <= args.onemli_esik]
            log(f"[ONEMLI] Giris %{args.onemli_esik}: {len(onemli_adaylar)} aday · "
                f"cikis %{onemli_cikis}: {len(genis_onemli)} "
                f"({len(kutuphane)} kayitlik kutuphaneden).")
            # Mega icin YALNIZCA giris esigine girmis teknik kayitlar verilir.
            mega_adaylar = onemli_seviye.mega_confluence_bul(
                list(temas.values()), onemli_adaylar, log=log)
        except Exception as e:
            log(f"[ONEMLI][UYARI] onemli seviye katmani atlandi: {type(e).__name__}: {e}")
            genis_onemli, onemli_adaylar, mega_adaylar = [], [], []

    def _onemli_kayda_cevir(adaylar, mega_listesi):
        """Onemli seviye/mega adaylarini alarm kayit sozlugune cevirir.

        Mega olan sembol, ayrica "onemli seviye" olarak TEKRAR listelenmez —
        ayni olay, iki bildirim degil.
        """
        mega_semboller = {m["sembol"] for m in mega_listesi}
        kayitlar = {}
        for m in mega_listesi:
            kayit = dict(m)
            kayit["kaynak_turu"] = "mega_confluence"
            kayit["mesafe"] = m.get("teknik_mesafe") or 0.0
            kayit["cizgi_adi"] = m.get("teknik_cizgi_adi")
            kayit["cizgi"] = m.get("teknik_cizgi")
            kayitlar[f"{m['sembol']}|MEGA|{m['seviye_id']}"] = kayit
        for a in adaylar:
            if a["sembol"] in mega_semboller:
                continue
            kayit = dict(a)
            kayit["kaynak_turu"] = "onemli_seviye"
            kayit["cizgi_adi"] = f"{a['kaynak']} · {a['seviye_metni']}"
            kayit["cizgi"] = a["seviye_orta"]
            kayitlar[f"{a['sembol']}|ONEMLI|{a['seviye_id']}"] = kayit
        return kayitlar

    # Onemli seviye katmani MagicMA akisina katilir: histerezis, "yeni temas"
    # isareti, karne kancasi ve mesaj olusturma hepsi ayni yoldan gecer.
    genis.update(_onemli_kayda_cevir(genis_onemli, mega_adaylar))
    temas.update(_onemli_kayda_cevir(onemli_adaylar, mega_adaylar))

    onceki, _eski_kuyruk, bekleyen_cikanlar, son_mesaj, _ilk = durum_oku()
    log(f"Giris esigi %{args.esik}: {len(temas)} kayit · "
        f"cikis esigi %{cikis_esik}: {len(genis)} kayit (onceki durum: {len(onceki)}"
        + ").")

    simdi_iso = datetime.now().isoformat(timespec="seconds")

    # Histerezis: onceden listede olan kayit, cikis esigi icinde kaldigi surece
    # listede kalir. Bildirime ise (2026-08-28 kullanici istegi) listenin
    # TAMAMI girer — yeni girenler 🆕 ile isaretlenir, digerleri de her
    # mesajda tekrar listelenir.
    yeni_anahtarlar = [a for a in temas if a not in onceki]
    kalan_anahtarlar = [a for a in onceki if a in genis]
    cikan_anahtarlar = [a for a in onceki if a not in genis]

    yeni_durum = {}
    for anahtar in kalan_anahtarlar:
        kayit = dict(genis[anahtar])
        kayit["ilk_gorulme"] = onceki[anahtar].get("ilk_gorulme") or simdi_iso
        yeni_durum[anahtar] = kayit
    for anahtar in yeni_anahtarlar:
        kayit = dict(temas[anahtar])
        kayit["ilk_gorulme"] = simdi_iso
        kayit["yeni"] = True
        yeni_durum[anahtar] = kayit

    # --- KARNE KANCASI ------------------------------------------------------
    # Her YENI TEMAS bir iddiadir; karneye "acik" kayit olarak dusulur ve
    # sonraki turlarda gercekten tutup tutmadigi olculur (magicma_karne.py).
    # Alarm mantigini etkilemez: hata olsa bile bildirim akisi surer.
    if not args.karne_yok:
        try:
            kanca_listesi = [temas[a] for a in yeni_anahtarlar]
            # Mega tespitleri, temas bu turda "yeni" OLMASA DA kancaya girer:
            # yeni kayit acilmaz (dedupe) ama acik teknik kayit mega'ya
            # YUKSELTILIR. Aksi halde sembol zaten listede oldugu icin mega
            # hic kaydedilmez ve karne karsilastirmasi olcusuz kalirdi.
            imzalar = {(t.get("sembol"), t.get("cizgi_adi")) for t in kanca_listesi}
            for kayit in temas.values():
                if (kayit.get("kaynak_turu") == "mega_confluence"
                        and (kayit.get("sembol"), kayit.get("cizgi_adi")) not in imzalar):
                    kanca_listesi.append(kayit)
            eklenen = magicma_karne.yeni_sinyalleri_kaydet(kanca_listesi)
            if eklenen:
                log(f"[KARNE] {eklenen} yeni sinyal karneye 'acik' olarak eklendi.")
        except Exception as e:
            log(f"[KARNE][UYARI] yeni sinyaller kaydedilemedi: {type(e).__name__}: {e}")

        # Acik kayitlari, bu turda zaten cekilmis fiyatlarla degerlendir
        # (ikinci kez fiyat cekilmez). Sadece gercekten durumu degisen kayit
        # varsa rapor yeniden yazilir — gereksiz dosya yazmayi onler.
        try:
            degisen = magicma_karne.acik_sinyalleri_degerlendir(
                fiyatlar=v.get("tum_fiyatlar") or {}, log=log)
            if degisen:
                magicma_karne.karne_raporu_uret(log=log)
                log(f"[KARNE] {len(degisen)} sinyal kapandi, KARNE_RAPOR.md guncellendi.")
        except Exception as e:
            log(f"[KARNE][UYARI] degerlendirme basarisiz: {type(e).__name__}: {e}")

        # Haftalik ozet: Pazartesi, gunun ilk calistirmasinda (son ozetten
        # 24 saatten fazla gectiyse) Telegram'a ayri bir mesaj olarak gider.
        try:
            if magicma_karne.haftalik_ozet_zamani_mi():
                ozet = magicma_karne.haftalik_ozet_metni()
                if args.kuru:
                    log("[KARNE] (kuru) Haftalik ozet gonderilecekti:\n" + ozet)
                elif telegram_gonder(token, chat_id, ozet):
                    magicma_karne.ozet_durum_yaz()
                    log("[KARNE] Haftalik karne ozeti Telegram'a gonderildi.")
                else:
                    log("[KARNE][UYARI] Haftalik ozet gonderilemedi; sonraki turda denenecek.")
        except Exception as e:
            log(f"[KARNE][UYARI] haftalik ozet basarisiz: {type(e).__name__}: {e}")

    # --- GUNLUK OZET (sabah 08:20-08:40 penceresinde gunde BIR kez) ----------
    # Ayri bir Task Scheduler gorevi ACILMADI: bu gorev zaten 7/24 her 10 dk
    # calisiyor, pencereye mutlaka denk geliyor. Tekrar gonderme korumasi
    # gunluk_ozet.py'nin kendi durum dosyasinda (haftalik ozet pattern'i).
    # Karneden bagimsiz: --karne-yok bunu KAPATMAZ.
    try:
        if args.kuru:
            pass                                      # kuru turda ozet gonderilmez
        elif gunluk_ozet.gonderim_zamani_mi():
            ozet = gunluk_ozet.ozet_metni(log=log)
            if telegram_gonder(token, chat_id, ozet):
                gunluk_ozet.son_gonderim_yaz()
                log("[OZET] Gunluk ozet Telegram'a gonderildi.")
            else:
                log("[OZET][UYARI] Gunluk ozet gonderilemedi; pencere icindeki "
                    "sonraki turda tekrar denenecek.")
    except Exception as e:
        log(f"[OZET][UYARI] gunluk ozet atlandi: {type(e).__name__}: {e}")

    # --- KOC'UN BOGA TETIGI -------------------------------------------------
    # Aktif kosul SAYISI degistiyse bildir, degismediyse sessiz kal (spam yok).
    # Fiyatlar bu turda zaten cekildi; ikinci fiyat cagrisi YAPILMAZ.
    try:
        aktif_sayi, tetik_metni, tetik_ozet = koc_tetigi.degerlendir(
            fiyatlar=v.get("tum_fiyatlar") or {}, log=log)
        onceki_tetik = koc_tetigi.son_durum_oku()
        onceki_sayi = onceki_tetik.get("aktif_sayi") if onceki_tetik else None
        if onceki_sayi != aktif_sayi:
            if args.kuru:
                log(f"[TETIK] (kuru) {onceki_sayi} -> {aktif_sayi}/3, gonderilecekti.")
            elif telegram_gonder(token, chat_id, tetik_metni):
                log(f"[TETIK] Bildirim gonderildi ({onceki_sayi} -> {aktif_sayi}/3).")
                koc_tetigi.son_durum_yaz(aktif_sayi, tetik_ozet)
            else:
                log("[TETIK][UYARI] gonderilemedi; durum GUNCELLENMEDI, "
                    "sonraki turda tekrar denenecek.")
        else:
            koc_tetigi.son_durum_yaz(aktif_sayi, tetik_ozet)
    except Exception as e:
        log(f"[TETIK][UYARI] tetik kontrolu atlandi: {type(e).__name__}: {e}")

    # Piyasasi kapandigi icin listeden dusenler SESSIZCE dusurulur: bunlarin
    # "listeden cikti" diye bildirilmesi gercek bir sinyal degil, kafa karistirir.
    # (Durum dosyasindan zaten dusuyorlar, cunku `genis` icinde yoklar.)
    kapali_semboller = v.get("kapali_semboller") or set()

    def _sembol(anahtar):
        return onceki[anahtar].get("sembol", anahtar.split("|")[0])

    piyasa_dusenleri = [a for a in cikan_anahtarlar if _sembol(a) in kapali_semboller]

    # Anahtar DEGISTIGI icin dusenler "listeden cikti" SAYILMAZ: bir sembol
    # cakisan seviye grubuna girip cikinca anahtari SEMBOL|BAND <->
    # SEMBOL|CONFLUENCE|grup arasinda degisiyor. Sembol hala listedeyse bu bir
    # cikis degil, yalnizca ayni sinyalin baska bir anahtarla temsili.
    hala_listede = {k.get("sembol") for k in yeni_durum.values()}
    gercek_cikanlar = [a for a in cikan_anahtarlar
                       if _sembol(a) not in kapali_semboller
                       and _sembol(a) not in hala_listede]

    simdi = datetime.fromisoformat(simdi_iso)

    # --- Bildirilecek liste = O ANDA yakin olan TUM adaylar --------------------
    # Eski davranis (yalnizca yeni temaslar) 2026-08-28'de birakildi: kullanici
    # her mesajda guncel islem firsatlarinin tamamini gormek istiyor. Bu yuzden
    # kuyruk birikmez, her turda bastan kurulur; mesaj gidemezse bir sonraki
    # turun listesi zaten daha guncelini tasir.
    bekleyen = []
    for anahtar, kayit in yeni_durum.items():
        kayit = dict(kayit)
        kayit["anahtar"] = anahtar
        bekleyen.append(kayit)

    cikanlar = sorted(set(bekleyen_cikanlar) | {_sembol(a) for a in gercek_cikanlar})

    log(f"Yeni temas: {len(yeni_anahtarlar)} · listede kalan: {len(kalan_anahtarlar)} · "
        f"listeden cikan: {len(gercek_cikanlar)}"
        + (f" · piyasa kapandigi icin sessizce dusen: {len(piyasa_dusenleri)}"
           if piyasa_dusenleri else ""))

    if not bekleyen:
        durum_yaz(yeni_durum, args.esik, [], son_mesaj)
        log("Yakin aday yok — mesaj gonderilmedi (sessiz).")
        return 0

    # Siralama onceligi (en guclu sinyal en ustte):
    #   0 MEGA-CONFLUENCE (teknik + temel ayni noktada)
    #   1 bantlar arasi cakisma (bagimsiz teknik teyit)
    #   2 dar band cakismasi
    #   3 onemli seviye (yalniz temel)
    #   4 tekil MagicMA temasi
    # Her grup kendi icinde en yakin mesafe ustte.
    def _oncelik(kayit):
        tur = kayit.get("kaynak_turu")
        if tur == "mega_confluence":
            return 0
        if tur == "onemli_seviye":
            return 3
        return {"bantlar_arasi": 1, "dar_band": 2}.get(kayit.get("confluence_tip"), 4)

    bekleyen.sort(key=lambda k: (_oncelik(k), abs(k.get("mesafe", 0))))
    metin = mesaj_olustur(bekleyen, cikanlar, simdi)

    if args.kuru:
        # Windows konsolu cp1252 olabilir; emoji yuzunden cokmesin.
        def _yaz(x):
            try:
                print(x)
            except UnicodeEncodeError:
                print(x.encode("ascii", "replace").decode("ascii"))

        _yaz("\n--- GONDERILECEK MESAJ (kuru mod) ---")
        _yaz(metin)
        _yaz("--- son ---\n")
        durum_yaz(yeni_durum, args.esik, [], son_mesaj)
        return 0

    # --- Mesaj araligi: son mesajdan bu yana yeterli sure gecti mi? ----------
    gecen_dk = (simdi - son_mesaj).total_seconds() / 60 if son_mesaj else None
    alt_sinir = max(0.0, args.mesaj_araligi - ARALIK_TOLERANS_DK)
    if gecen_dk is not None and gecen_dk < alt_sinir:
        durum_yaz(yeni_durum, args.esik, [], son_mesaj, cikanlar=cikanlar)
        log(f"{len(bekleyen)} aday BEKLETILIYOR — son mesajdan bu yana "
            f"{gecen_dk:.1f} dk gecti, gereken {alt_sinir:.1f} dk "
            f"({args.mesaj_araligi} dk - {ARALIK_TOLERANS_DK:.0f} dk tarama payi). "
            f"~{alt_sinir - gecen_dk:.0f} dk sonra hepsi TEK mesajda gidecek.")
        return 0

    if telegram_gonder(token, chat_id, metin):
        log(f"Telegram'a TEK mesajda {len(bekleyen)} guncel aday gonderildi.")
        durum_yaz(yeni_durum, args.esik, [], simdi)              # kuyruk bosaltilir
        return 0

    # Gonderim basarisiz: kuyruk DOKUNULMADAN birakilir, son_mesaj guncellenmez;
    # bir sonraki tur ayni adaylarla tekrar dener (bildirim kaybolmaz).
    log("[HATA] Telegram gonderimi basarisiz — sonraki turda guncel listeyle tekrar denenecek.")
    durum_yaz(yeni_durum, args.esik, [], son_mesaj, cikanlar=cikanlar)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        log(f"[HATA] Beklenmeyen hata: {type(e).__name__}: {e}")
        sys.exit(1)
