"""
magicma/telegram_alarm.py

Amac: magicma/fiyat_kontrol.py'nin hesapladigi "cizgiye yapisik" listeyi
(varsayilan esik %0,25 — CLAUDE.md MAGICMA RAPOR FORMAT KURALI) her calismada
bir onceki durumla karsilastirip, listeye YENI GIREN sembol/cizgi ciftlerini
Telegram'a bildirim olarak gonderir.

Tasarim kararlari:
  - Fiyat cekme mantigi TEKRAR YAZILMAZ; fiyat_kontrol.adaylari_hesapla()
    import edilir.
  - Durum dosyasi: magicma/alarm_son_durum.json. Anahtar = "SEMBOL|CIZGI_ADI".
  - ILK calistirmada durum dosyasi yoksa hicbir bildirim gonderilmez (her sey
    "yeni" gorunur, spam olur); sadece durum kaydedilir.
  - Yeni temas YOKSA hicbir mesaj gonderilmez (sessiz kalir).
  - Listeden cikanlar tek satirlik, daha sessiz bir bolumde ozetlenir ve
    yalnizca zaten gonderilecek bir mesaj varsa eklenir.
  - Her sey try/except icinde: fiyat cekme veya Telegram API basarisiz olursa
    script konsola log yazip sessizce cikar (bir sonraki turda tekrar dener).

Kullanim:
    py -3 magicma/telegram_alarm.py
    py -3 magicma/telegram_alarm.py --esik 0.4
    py -3 magicma/telegram_alarm.py --kuru      # Telegram'a gondermeden, ekrana yaz
    py -3 magicma/telegram_alarm.py --zorla     # ilk calistirma olsa bile gonder

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
    """Doner: (kayitlar_sozlugu, ilk_calistirma_mi)"""
    if not os.path.exists(yol):
        return {}, True
    try:
        with open(yol, encoding="utf-8") as f:
            veri = json.load(f)
        kayitlar = veri.get("kayitlar", {})
        if not isinstance(kayitlar, dict):
            raise ValueError("kayitlar sozluk degil")
        return kayitlar, False
    except (OSError, ValueError) as e:
        log(f"[UYARI] {yol} okunamadi ({type(e).__name__}: {e}); ilk calistirma sayiliyor.")
        return {}, True


def durum_yaz(kayitlar, esik, yol=DURUM_YOL):
    gecici = yol + ".tmp"
    veri = {
        "guncelleme": datetime.now().isoformat(timespec="seconds"),
        "esik": esik,
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
    yon = "SHORT adayi" if kayit["mesafe"] < 0 else "LONG adayi"
    return (f"{kayit['sembol']}  {_tr(kayit['fiyat'])} -> {kayit['cizgi_adi']} "
            f"{_tr(kayit['cizgi'])}  %{_tr(kayit['mesafe'], 2)}  {yon}")


def mesaj_olustur(yeniler, cikanlar):
    zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
    parcalar = [f"YENI MagicMA TEMAS ({zaman})", ""]
    parcalar += [satir_bicimle(k) for k in yeniler]
    if cikanlar:
        parcalar += ["", "Listeden cikti: " + ", ".join(cikanlar)]
    return "\U0001F514 " + _md_kacir("\n".join(parcalar))


def parcala(metin, sinir=TELEGRAM_MAX):
    """Telegram karakter sinirini asmasin diye satir sinirinda boler."""
    if len(metin) <= sinir:
        return [metin]
    parcalar, tampon = [], ""
    for satir in metin.split("\n"):
        if len(tampon) + len(satir) + 1 > sinir and tampon:
            parcalar.append(tampon)
            tampon = ""
        tampon = f"{tampon}\n{satir}" if tampon else satir
    if tampon:
        parcalar.append(tampon)
    return parcalar


# --------------------------------------------------------------------------
# Telegram
# --------------------------------------------------------------------------

def telegram_gonder(token, chat_id, metin):
    """Mesaji gonderir. Markdown ayristirma hatasinda duz metin olarak tekrar dener.
    Doner: True/False (basari)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    tamam = True
    for parca in parcala(metin):
        gonderildi = False
        for parse_mode in ("Markdown", None):
            govde = {"chat_id": chat_id, "text": parca,
                     "disable_web_page_preview": True}
            if parse_mode:
                govde["parse_mode"] = parse_mode
            try:
                r = requests.post(url, data=govde, timeout=20)
                if r.status_code == 200 and r.json().get("ok"):
                    gonderildi = True
                    break
                log(f"[UYARI] Telegram yaniti ({parse_mode or 'duz'}): "
                    f"{r.status_code} {r.text[:200]}")
            except Exception as e:
                log(f"[UYARI] Telegram istegi basarisiz ({parse_mode or 'duz'}): "
                    f"{type(e).__name__}: {e}")
        if not gonderildi:
            tamam = False
    return tamam


# --------------------------------------------------------------------------

def sonuclari_kayda_cevir(sonuclar):
    """adaylari_hesapla() tuple'larini {anahtar: kayit} sozlugune cevirir."""
    kayitlar = {}
    for _, sembol, canli, ad, deger, mesafe, _yon, kaynak in sonuclar:
        kayitlar[f"{sembol}|{ad}"] = {
            "sembol": sembol,
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
                    help="durum dosyasi yoksa bile mesaj gonder (ilk calistirma sessizligini atla)")
    args = ap.parse_args()

    cikis_esik = args.cikis_esik if args.cikis_esik is not None else args.esik * 2

    token = chat_id = None
    if not args.kuru:
        token, chat_id = telegram_bilgileri()

    try:
        # Genis bandi (cikis esigi) hesaplat; giris esigi bunun icinden suzulur.
        v = fiyat_kontrol.adaylari_hesapla(
            tarih=args.tarih, esik=cikis_esik, max_yas=args.max_yas, log=log)
    except SystemExit:
        raise
    except Exception as e:
        log(f"[HATA] Fiyat cekme basarisiz, bu tur atlaniyor: {type(e).__name__}: {e}")
        return 1

    genis = sonuclari_kayda_cevir(v["sonuclar"])                       # |mesafe| <= cikis_esik
    temas = {a: k for a, k in genis.items() if abs(k["mesafe"]) <= args.esik}

    onceki, ilk_calistirma = durum_oku()
    log(f"Giris esigi %{args.esik}: {len(temas)} kayit · "
        f"cikis esigi %{cikis_esik}: {len(genis)} kayit (onceki durum: {len(onceki)}).")

    if ilk_calistirma and not args.zorla:
        durum_yaz(temas, args.esik)
        log(f"ILK CALISTIRMA: bildirim gonderilmedi, durum kaydedildi -> {DURUM_YOL}")
        return 0

    # Histerezis: onceden listede olan kayit, cikis esigi icinde kaldigi surece
    # listede kalir (yeniden bildirilmez). Yeni bildirim yalnizca GIRIS esigine
    # ilk kez giren kayitlar icin uretilir.
    yeni_anahtarlar = [a for a in temas if a not in onceki]
    kalan_anahtarlar = [a for a in onceki if a in genis]
    cikan_anahtarlar = [a for a in onceki if a not in genis]

    yeni_durum = {a: genis[a] for a in kalan_anahtarlar}
    yeni_durum.update({a: temas[a] for a in yeni_anahtarlar})

    # En yakin en ustte
    yeniler = sorted((temas[a] for a in yeni_anahtarlar), key=lambda k: abs(k["mesafe"]))
    cikanlar = sorted({onceki[a].get("sembol", a.split("|")[0]) for a in cikan_anahtarlar})

    log(f"Yeni temas: {len(yeniler)} · listede kalan: {len(kalan_anahtarlar)} · "
        f"listeden cikan: {len(cikan_anahtarlar)}")

    if not yeniler:
        durum_yaz(yeni_durum, args.esik)
        log("Yeni temas yok — mesaj gonderilmedi (sessiz).")
        return 0

    metin = mesaj_olustur(yeniler, cikanlar)

    if args.kuru:
        print("\n--- GONDERILECEK MESAJ (kuru mod) ---")
        print(metin)
        print("--- son ---\n")
        durum_yaz(yeni_durum, args.esik)
        return 0

    if telegram_gonder(token, chat_id, metin):
        log(f"Telegram'a {len(yeniler)} yeni temas gonderildi.")
        durum_yaz(yeni_durum, args.esik)
        return 0

    # Gonderim basarisiz: YENI kayitlar durumda birakilmaz ki bir sonraki turda
    # tekrar denensin (bildirim kaybolmasin). Kalanlar guncellenir.
    log("[HATA] Telegram gonderimi basarisiz — yeni temaslar bir sonraki tura birakildi.")
    durum_yaz({a: genis[a] for a in kalan_anahtarlar}, args.esik)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        log(f"[HATA] Beklenmeyen hata: {type(e).__name__}: {e}")
        sys.exit(1)
