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


def satir_bicimle(kayit):
    """Bir aday icin TEK satir: SEMBOL · LONG/SHORT · fiyat.

    Bilerek sade: band araligi, "banda yukaridan indi" gibi gerekce metinleri
    ve cizgi adlari mesaja YAZILMAZ (kullanici istegi). Bu bilgiler yon
    hesabinda kullanilmaya devam eder ve durum dosyasi/logda saklanir; sadece
    bildirimde gosterilmez.
    """
    yon = kayit.get("yon")
    if yon not in ("long", "short"):                      # eski durum dosyasi yedegi
        yon = "short" if kayit.get("mesafe", 0) < 0 else "long"
    return f"{kayit['sembol']}  {'LONG' if yon == 'long' else 'SHORT'}  {_tr(kayit['fiyat'])}"


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
    gorulen = set()
    bloklar = []
    for kayit in bekleyen:
        imza = (kayit.get("sembol"), kayit.get("yon"))
        if imza in gorulen:
            continue
        gorulen.add(imza)
        blok = satir_bicimle(kayit)
        if kayit.get("yeni"):
            blok = "\U0001F195 " + blok
        bloklar.append(_md_kacir(blok))

    bas = "\U0001F4CA " + _md_kacir(
        f"MagicMA İŞLEM FIRSATLARI ({simdi:%d.%m.%Y %H:%M}) · {len(bloklar)} aday")

    govde, atlanan = [], 0
    for sira, blok in enumerate(bloklar):
        deneme = len(bas) + len("\n".join(govde + [blok])) + len(son) + 64
        if deneme > TELEGRAM_MAX and govde:
            atlanan = len(bloklar) - sira
            break
        govde.append(blok)

    metin = bas + ("\n\n" + "\n".join(govde) if govde else "")
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
    """
    kayitlar = {}
    for _, sembol, canli, ad, deger, mesafe, _yon, kaynak, bant in sonuclar:
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
            piyasa_filtresi=not args.piyasa_saatini_yoksay)
    except SystemExit:
        raise
    except Exception as e:
        log(f"[HATA] Fiyat cekme basarisiz, bu tur atlaniyor: {type(e).__name__}: {e}")
        return 1

    genis = sonuclari_kayda_cevir(v["sonuclar"])                       # |mesafe| <= cikis_esik
    temas = {a: k for a, k in genis.items() if abs(k["mesafe"]) <= args.esik}

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

    # Piyasasi kapandigi icin listeden dusenler SESSIZCE dusurulur: bunlarin
    # "listeden cikti" diye bildirilmesi gercek bir sinyal degil, kafa karistirir.
    # (Durum dosyasindan zaten dusuyorlar, cunku `genis` icinde yoklar.)
    kapali_semboller = v.get("kapali_semboller") or set()

    def _sembol(anahtar):
        return onceki[anahtar].get("sembol", anahtar.split("|")[0])

    piyasa_dusenleri = [a for a in cikan_anahtarlar if _sembol(a) in kapali_semboller]
    gercek_cikanlar = [a for a in cikan_anahtarlar if _sembol(a) not in kapali_semboller]

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

    # En yakin en ustte
    bekleyen.sort(key=lambda k: abs(k.get("mesafe", 0)))
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
