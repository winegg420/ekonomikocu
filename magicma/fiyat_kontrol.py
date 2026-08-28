"""
magicma/fiyat_kontrol.py

Amac: Mentor oturumunun (claude.ai Project) yapamadigi seyi yapmak - YUZLERCE
sembolun guncel fiyatini SANIYELER icinde, tek/az sayida toplu API cagrisiyla
cekip, en son MagicMA taramasindaki cizgilere gore mesafeyi hesaplamak.

Neden mentor oturumu bunu yapamiyor: o ayri bir bulut sandbox, agi kisitli
(api.binance.com / raw API'lere dogrudan erisemiyor, sadece WebFetch/WebSearch
ile TEK TEK sayfa okuyabiliyor - 500 sembol icin 500 ayri istek demek, cok yavas).

Bu script SENIN bilgisayarindan (veya Claude Code'dan) calisir, bu kisitlar
yok, dogrudan API'lere erisebilir:
  - Kripto: Binance / MEXC / Gate.io / Bybit / OKX / KuCoin toplu ticker uclari.
    Her borsa TEK istek -> ~450 kripto sembolu birkac saniyede. Sembolun kendi
    borsasi (magicma_ham.jsonl'deki `kaynak` alani) once denenir, bulunamazsa
    diger borsalara dusulur.
  - Hisse / endeks / forex: Yahoo Finance v8 chart ucu, ThreadPoolExecutor ile
    PARALEL (varsayilan 12 is parcacigi) -> ~300 sembol birkac saniyede.
    BIST icin `.IS` soneki (THYAO -> THYAO.IS), forex icin `=X` soneki
    (AUDNZD -> AUDNZD=X), endeksler icin el ile eslesme (SPX -> ^GSPC vb).
  - Degerli metal (XAUUSD/XAGUSD/XPTUSD/XPDUSD/XAUTRY): api.gold-api.com
    (ucretsiz, anahtarsiz, anlik spot). Yahoo'da bu spot semboller YOK.
    DIKKAT: bu uc bazen saatlerce eski fiyat donduruyor (olculdu: platin 15 sa,
    gumus 17 sa). Bu yuzden yanittaki `updatedAt` okunur; METAL_MAX_YAS_DK
    (varsayilan 15 dk) esiginden yasli fiyat BAYAT sayilir, sonuca ALINMAZ ve
    hem konsolda hem fiyat_kontrol_son.md'de tek satirlik [METAL] ozetinde
    kac sembolun atlandigi bildirilir.
  - Forex yedegi: Frankfurter (ECB, ucretsiz/anahtarsiz) TEK istekte EUR bazli
    tum kurlar -> capraz parite matematikle hesaplanir. Yahoo bir pariteyi
    donduremezse devreye girer. DIKKAT: ECB gunluk referans kuru, gun ici degil.

NOT: infoyatirim.com denendi ve BIST icin BIRAKILDI - site python-requests
baglantisini TLS el sikismasinda resetliyor (WinError 10054), tarayici disindan
cekilemiyor. BIST fiyatlari Yahoo `.IS` uzerinden geliyor (MPARK.IS = 437,25 ile
tarama fiyati birebir dogrulandi).

Seviyeler VARSAYILAN olarak `99_BOT_ARSIV/kod/magicma_ham.jsonl` icinden, her
sembol icin en yuksek ts'li kayittan okunur (CLAUDE.md MAGICMA kurali). Markdown
rapor 2 ondaliga yuvarladigi icin (AUDNZD 1,1946 -> "1,19") forexte %0,3 esigi
anlamsizlasiyordu; ham dosya tam hassasiyeti tasiyor. Markdown rapordan okumak
icin `--rapordan` bayragi var.

Kullanim:
    pip install requests
    py -3 magicma/fiyat_kontrol.py
    py -3 magicma/fiyat_kontrol.py --esik 0.5          # mesafe esigini genislet (%)
    py -3 magicma/fiyat_kontrol.py --tarih 2026-08-26  # sadece o gunun taramasi
    py -3 magicma/fiyat_kontrol.py --rapordan          # seviyeleri markdown rapordan al
    py -3 magicma/fiyat_kontrol.py --eksikler          # canli fiyati bulunamayanlari listele

Cikti: konsola, mesafeye gore siralanmis, DIREKT mentor'a yapistirilabilir
duz metin liste. Ayni zamanda magicma/fiyat_kontrol_son.md dosyasina da yazar.
"""

import argparse
import concurrent.futures
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("Once 'pip install requests' calistir.")
    sys.exit(1)

REPO_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAPOR_KLASOR = os.path.join(REPO_KOK, "magicma")
HAM_YOL = os.path.join(REPO_KOK, "99_BOT_ARSIV", "kod", "magicma_ham.jsonl")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) fiyat_kontrol.py"}
YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}

# TradingView sembolu -> Yahoo Finance kodu (birebir esleme gerekenler)
YAHOO_OZEL = {
    "SPX": "^GSPC",
    "NDX": "^NDX",
    "DJI": "^DJI",
    "VIX": "^VIX",
    "US10Y": "^TNX",
    "DXY": "DX-Y.NYB",
    "USOIL": "CL=F",
    "UKOIL": "BZ=F",
    "HG1!": "HG=F",
    "XU100": "XU100.IS",
    "XU030": "XU030.IS",
}
# Yahoo'da spot karsiligi olmayan metaller -> api.gold-api.com kodu
METAL = {"XAUUSD": "XAU", "XAGUSD": "XAG", "XPTUSD": "XPT", "XPDUSD": "XPD"}
KRIPTO_BORSA = {"BINANCE", "MEXC", "GATEIO", "BYBIT", "OKX", "KUCOIN", "COINBASE", "CRYPTOCAP"}
FOREX_BORSA = {"FX", "OANDA", "FX_IDC", "FOREXCOM"}


# --------------------------------------------------------------------------
# Seviye kaynaklari
# --------------------------------------------------------------------------

def en_son_tarih():
    dosyalar = glob.glob(os.path.join(RAPOR_KLASOR, "magicma_rapor_*.md"))
    if not dosyalar:
        print("magicma/magicma_rapor_*.md bulunamadi. Once magicma_yakinlik.py --tara calistirilmis olmali.")
        sys.exit(1)
    tarihler = []
    for d in dosyalar:
        m = re.search(r"magicma_rapor_(\d{4}-\d{2}-\d{2})\.md$", d)
        if m:
            tarihler.append(m.group(1))
    return max(tarihler)


def ham_oku(tarih=None, max_yas_gun=10):
    """magicma_ham.jsonl'den her sembol icin EN YUKSEK ts'li kaydi dondurur.

    Donen: {sembol: {"kaynak", "ts", "fiyat", "seviyeler": [(ad, deger), ...]}}
    tarih verilirse yalnizca o gunun kayitlari; verilmezse en yeni kayittan
    max_yas_gun gun geriye kadar olanlar kullanilir (bayat seviye filtresi).
    """
    if not os.path.exists(HAM_YOL):
        print(f"{HAM_YOL} bulunamadi. --rapordan ile markdown rapordan okuyabilirsin.")
        sys.exit(1)

    son = {}
    with open(HAM_YOL, encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            try:
                kayit = json.loads(satir)
            except (ValueError, TypeError):
                continue
            sembol = kayit.get("sembol")
            ts = kayit.get("ts") or ""
            if not sembol or not kayit.get("seviyeler"):
                continue
            if tarih and not ts.startswith(tarih):
                continue
            if sembol not in son or ts > son[sembol].get("ts", ""):
                son[sembol] = kayit

    if not son:
        print("magicma_ham.jsonl'de uygun kayit yok" + (f" (tarih={tarih})" if tarih else "") + ".")
        sys.exit(1)

    if not tarih and max_yas_gun:
        en_yeni = max(k.get("ts", "") for k in son.values())
        try:
            sinir = (datetime.fromisoformat(en_yeni) - timedelta(days=max_yas_gun)).isoformat()
            son = {s: k for s, k in son.items() if k.get("ts", "") >= sinir}
        except ValueError:
            pass

    sonuc = {}
    for sembol, kayit in son.items():
        seviyeler = []
        for sv in kayit["seviyeler"]:
            try:
                deger = float(sv["deger"])
            except (KeyError, TypeError, ValueError):
                continue
            if deger:
                seviyeler.append((str(sv.get("ad", "?")), deger))
        if seviyeler:
            sonuc[sembol] = {
                "kaynak": kayit.get("kaynak", ""),
                "ts": kayit.get("ts", ""),
                "fiyat": kayit.get("fiyat"),
                "seviyeler": seviyeler,
            }
    return sonuc


def raporu_oku(tarih):
    """magicma_rapor_TARIH.md icindeki her sembol icin ham_oku ile ayni yapiyi dondurur.

    Yedek yol: ham jsonl yoksa / --rapordan verilirse. Rapordaki degerler 2
    ondaliga yuvarlanmistir, forexte hassasiyet kaybi olur.
    """
    yol = os.path.join(RAPOR_KLASOR, f"magicma_rapor_{tarih}.md")
    if not os.path.exists(yol):
        print(f"{yol} bulunamadi.")
        sys.exit(1)
    with open(yol, encoding="utf-8") as f:
        metin = f.read()

    sonuc = {}
    for b in re.split(r"\n## ", metin)[1:]:
        baslik, _, gerisi = b.partition("\n")
        m = re.match(r"([A-Za-z0-9_.!]+)\s+—\s+fiyat\s+([\d.,]+)", baslik)
        if not m:
            continue
        sembol = m.group(1)
        satirlar = re.findall(
            r"\|\s*(?:TEMAS|YAKIN|İZLEME|IZLEME)\s*\|\s*([^|]+)\|\s*([\d.,]+)\s*\|\s*[+-][\d.,]+%\s*\|",
            gerisi,
        )
        seviyeler = []
        for ad, deger_str in satirlar:
            deger = _tr_sayi(deger_str)
            if deger:
                seviyeler.append((ad.strip(), deger))
        if seviyeler:
            sonuc[sembol] = {
                "kaynak": "",
                "ts": tarih,
                "fiyat": _tr_sayi(m.group(2)),
                "seviyeler": seviyeler,
            }
    return sonuc


def _tr_sayi(metin):
    """'437,25' / '1.234,56' -> float. Cevrilemezse 0.0."""
    try:
        return float(metin.strip().replace(".", "").replace(",", "."))
    except (AttributeError, ValueError):
        return 0.0


# --------------------------------------------------------------------------
# Siniflandirma
# --------------------------------------------------------------------------

def sembol_listesi_oku(dosya_adi):
    yol = os.path.join(RAPOR_KLASOR, "sembol_listesi", dosya_adi)
    semboller = set()
    if not os.path.exists(yol):
        return semboller
    with open(yol, encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir or satir.startswith("#"):
                continue
            semboller.add(satir.split(":")[-1])
    return semboller


def _borsa(kaynak, sembol, listeler):
    """kaynak 'BINANCE:BTCUSDT' -> 'BINANCE'. kaynak bossa (markdown rapor yolu)
    magicma/sembol_listesi/*.txt dosyalarindan tahmin eder."""
    if kaynak and ":" in kaynak:
        return kaynak.split(":")[0].upper()
    if sembol in listeler["bist"]:
        return "BIST"
    if sembol in listeler["kripto"] or sembol.endswith("USDT"):
        return "BINANCE"
    if sembol in listeler["forex"]:
        return "FX"
    if sembol in listeler["abd"]:
        return "NASDAQ"
    return ""


def siniflandir(seviye_haritasi):
    """Sembolleri fiyat kaynagina gore ayirir.

    Donen: (kripto {sembol: borsa}, yahoo {sembol: yahoo_kodu},
            metal {sembol: metal_kodu}, forex_yedek set, kapsanmayan set)
    """
    listeler = {
        "kripto": sembol_listesi_oku("kripto.txt") | sembol_listesi_oku("gunun_hareketlileri.txt"),
        "forex": sembol_listesi_oku("forex_emtia.txt"),
        "bist": sembol_listesi_oku("bist.txt"),
        "abd": sembol_listesi_oku("abd_hisse.txt"),
    }
    forex_liste = listeler["forex"]

    kripto, yahoo, metal, forex_yedek, kapsanmayan = {}, {}, {}, set(), set()

    for sembol, veri in seviye_haritasi.items():
        borsa = _borsa(veri.get("kaynak", ""), sembol, listeler)

        if sembol in METAL:
            metal[sembol] = METAL[sembol]
        elif sembol == "XAUTRY":
            metal[sembol] = "XAU_TRY"          # XAU/USD * USD/TRY olarak hesaplanir
        elif sembol in YAHOO_OZEL:
            yahoo[sembol] = YAHOO_OZEL[sembol]
        elif borsa == "CRYPTOCAP":
            kapsanmayan.add(sembol)            # TOTAL / BTC.D: ucretsiz canli kaynak yok
        elif borsa in KRIPTO_BORSA:
            kripto[sembol] = borsa
        elif borsa == "BIST":
            yahoo[sembol] = f"{sembol}.IS"
        elif borsa in FOREX_BORSA or (sembol in forex_liste and len(sembol) == 6):
            yahoo[sembol] = f"{sembol}=X"
            forex_yedek.add(sembol)
        elif borsa in ("NASDAQ", "NYSE", "AMEX", "SP", "DJ", "TVC", "COMEX"):
            yahoo[sembol] = sembol.replace(".", "-")
        elif sembol.endswith("USDT"):
            kripto[sembol] = "BINANCE"
        else:
            yahoo[sembol] = sembol.replace(".", "-")

    return kripto, yahoo, metal, forex_yedek, kapsanmayan


# --------------------------------------------------------------------------
# Fiyat kaynaklari
# --------------------------------------------------------------------------

def _json_cek(url, timeout=15):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _binance_uyumlu(url):
    return {row["symbol"]: float(row["price"]) for row in _json_cek(url)}


def _gateio():
    return {row["currency_pair"].replace("_", ""): float(row["last"])
            for row in _json_cek("https://api.gateio.ws/api/v4/spot/tickers") if row.get("last")}


def _bybit():
    veri = _json_cek("https://api.bybit.com/v5/market/tickers?category=spot")
    return {row["symbol"]: float(row["lastPrice"])
            for row in veri["result"]["list"] if row.get("lastPrice")}


def _okx():
    veri = _json_cek("https://www.okx.com/api/v5/market/tickers?instType=SPOT")
    return {row["instId"].replace("-", ""): float(row["last"])
            for row in veri["data"] if row.get("last")}


def _kucoin():
    veri = _json_cek("https://api.kucoin.com/api/v1/market/allTickers")
    return {row["symbol"].replace("-", ""): float(row["last"])
            for row in veri["data"]["ticker"] if row.get("last")}


BORSA_CEKICI = {
    "BINANCE": lambda: _binance_uyumlu("https://api.binance.com/api/v3/ticker/price"),
    "MEXC": lambda: _binance_uyumlu("https://api.mexc.com/api/v3/ticker/price"),
    "GATEIO": _gateio,
    "BYBIT": _bybit,
    "OKX": _okx,
    "KUCOIN": _kucoin,
}


def kripto_fiyatlari_cek(sembol_borsa):
    """Her borsadan TEK toplu istek (paralel), sonra sembolu once kendi borsasinda arar."""
    if not sembol_borsa:
        return {}, {}

    gerekli = {b for b in sembol_borsa.values() if b in BORSA_CEKICI}
    gerekli |= {"BINANCE"}                      # her zaman genel yedek olarak dursun
    tablolar = {}

    def _cek(borsa):
        try:
            return borsa, BORSA_CEKICI[borsa]()
        except Exception as e:
            print(f"[UYARI] {borsa} toplu fiyat cekilemedi: {type(e).__name__}: {e}")
            return borsa, {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(gerekli)) as ex:
        for borsa, tablo in ex.map(_cek, sorted(gerekli)):
            tablolar[borsa] = tablo

    sira = ["BINANCE", "MEXC", "GATEIO", "BYBIT", "OKX", "KUCOIN"]
    fiyatlar, kaynaklar = {}, {}
    for sembol, borsa in sembol_borsa.items():
        # COINBASE:AEROUSD gibi USD pariteleri cogu borsada USDT olarak listeli
        adaylar = [sembol] + ([sembol[:-3] + "USDT"] if sembol.endswith("USD") else [])
        bulundu = False
        for borsa_adi in [borsa] + [b for b in sira if b != borsa]:
            tablo = tablolar.get(borsa_adi)
            if not tablo:
                continue
            for parite in adaylar:
                if parite in tablo:
                    fiyatlar[sembol] = tablo[parite]
                    kaynaklar[sembol] = borsa_adi
                    bulundu = True
                    break
            if bulundu:
                break
    return fiyatlar, kaynaklar


def _yahoo_tek(cift):
    sembol, kod = cift
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{kod}?range=1d&interval=1d"
    try:
        r = requests.get(url, headers=YAHOO_HEADERS, timeout=15)
        r.raise_for_status()
        sonuc = (r.json().get("chart") or {}).get("result")
        if not sonuc:
            return sembol, None
        fiyat = sonuc[0].get("meta", {}).get("regularMarketPrice")
        return sembol, (float(fiyat) if fiyat else None)
    except Exception:
        return sembol, None


def yahoo_fiyatlari_cek(kod_haritasi, max_worker=16):
    if not kod_haritasi:
        return {}
    fiyatlar = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_worker) as ex:
        for sembol, fiyat in ex.map(_yahoo_tek, sorted(kod_haritasi.items())):
            if fiyat:
                fiyatlar[sembol] = fiyat
    return fiyatlar


METAL_MAX_YAS_DK = 15   # gold-api.com bazen saatlerce eski veri donduruyor;
                        # bu esikten yasli fiyat "bayat" sayilir ve KULLANILMAZ.
_METAL_TS_ALANLARI = ("updatedAt", "updated_at", "timestamp", "time", "date")


def _zaman_ayristir(deger):
    """gold-api.com zaman damgasini timezone-aware datetime'a cevirir.
    ISO 8601 (Z sonekli) veya epoch saniye/milisaniye kabul eder. Cozemezse None."""
    if deger is None:
        return None
    try:
        if isinstance(deger, (int, float)):
            sn = float(deger)
            if sn > 1e11:          # milisaniye
                sn /= 1000.0
            return datetime.fromtimestamp(sn, tz=timezone.utc)
        metin = str(deger).strip()
        if not metin:
            return None
        if metin.isdigit():
            return _zaman_ayristir(int(metin))
        dt = datetime.fromisoformat(metin.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def metal_fiyatlari_cek(metal_haritasi, usdtry=None, max_yas_dk=METAL_MAX_YAS_DK):
    """api.gold-api.com - anahtarsiz spot. XAUTRY = XAUUSD * USDTRY.

    Yanittaki `updatedAt` zaman damgasi okunur; fiyat `max_yas_dk` dakikadan
    eskiyse BAYAT sayilir ve sonuc sozlugune ALINMAZ (yanlis "yakin aday"
    sinyali uretmesin diye). Zaman damgasi hic yoksa/cozulemezse fiyat kabul
    edilir ama yasi bilinmiyor olarak isaretlenir.

    Doner: (fiyatlar, bayatlar) — bayatlar: {sembol: yas_dakika}
    """
    if not metal_haritasi:
        return {}, {}
    kodlar = {k for k in metal_haritasi.values() if k != "XAU_TRY"}
    if "XAU_TRY" in metal_haritasi.values():
        kodlar.add("XAU")

    ham = {}          # kod -> fiyat
    yas_dk = {}       # kod -> yas (dakika) veya None (bilinmiyor)

    def _cek(kod):
        try:
            veri = _json_cek(f"https://api.gold-api.com/price/{kod}", timeout=12)
            fiyat = float(veri["price"])
            ts = None
            for alan in _METAL_TS_ALANLARI:
                if alan in veri:
                    ts = _zaman_ayristir(veri[alan])
                    if ts:
                        break
            yas = None
            if ts:
                yas = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
            return kod, fiyat, yas
        except Exception:
            return kod, None, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(kodlar))) as ex:
        for kod, fiyat, yas in ex.map(_cek, sorted(kodlar)):
            if fiyat:
                ham[kod] = fiyat
                yas_dk[kod] = yas

    fiyatlar, bayatlar = {}, {}
    for sembol, kod in metal_haritasi.items():
        temel = "XAU" if kod == "XAU_TRY" else kod
        if not ham.get(temel):
            continue
        yas = yas_dk.get(temel)
        if yas is not None and yas > max_yas_dk:
            bayatlar[sembol] = yas
            continue
        if kod == "XAU_TRY":
            if usdtry:
                fiyatlar[sembol] = ham["XAU"] * usdtry
        else:
            fiyatlar[sembol] = ham[kod]
    return fiyatlar, bayatlar


def forex_fiyatlari_cek(semboller):
    """Frankfurter (ECB, ucretsiz) TEK istekte EUR bazli tum kurlari ceker,
    istenen capraz paritelere donusturur. Metal/petrol/DXY burada YOK.
    Gunluk referans kuru - yalnizca Yahoo dondurmezse yedek olarak kullanilir."""
    if not semboller:
        return {}, ""
    try:
        veri = _json_cek("https://api.frankfurter.dev/v1/latest?base=EUR", timeout=12)
        oranlar = dict(veri["rates"])
        oranlar["EUR"] = 1.0
        tarih = veri.get("date", "")
    except Exception as e:
        print(f"[UYARI] Frankfurter forex verisi cekilemedi: {type(e).__name__}: {e}")
        return {}, ""

    sonuc = {}
    for sembol in semboller:
        if len(sembol) != 6:
            continue
        baz, karsi = sembol[:3], sembol[3:]
        if baz in oranlar and karsi in oranlar:
            # 1 EUR = oranlar[X] X  =>  1 baz = oranlar[karsi] / oranlar[baz] karsi
            sonuc[sembol] = oranlar[karsi] / oranlar[baz]
    return sonuc, tarih


# --------------------------------------------------------------------------

def adaylari_hesapla(tarih=None, esik=0.3, rapordan=False, max_yas=10, log=print):
    """Seviyeleri okur, canli fiyatlari ceker, esik icindeki adaylari dondurur.

    main() ve magicma/telegram_alarm.py ayni mantigi paylassin diye ayrildi;
    davranis main()'in eski hali ile birebir aynidir.

    Doner: sonuclarin ve yardimci meta bilgilerin bulundugu sozluk.
      sonuclar: [(mutlak_mesafe, sembol, canli, cizgi_adi, cizgi_degeri,
                  mesafe, yon, fiyat_kaynagi), ...] — mesafeye gore sirali.
    """
    if rapordan:
        tarih = tarih or en_son_tarih()
        seviyeler = raporu_oku(tarih)
        seviye_kaynagi = f"magicma_rapor_{tarih}.md"
    else:
        seviyeler = ham_oku(tarih, max_yas)
        tarih = max(v["ts"] for v in seviyeler.values())[:10]
        seviye_kaynagi = "magicma_ham.jsonl"

    log(f"Seviye kaynagi: {seviye_kaynagi} · en yeni tarama: {tarih} · sembol: {len(seviyeler)}")

    kripto, yahoo, metal, forex_yedek, kapsanmayan = siniflandir(seviyeler)
    log(f"Kripto: {len(kripto)} · Yahoo (BIST/ABD/endeks/forex): {len(yahoo)} · "
        f"Metal: {len(metal)} · Kaynaksiz: {len(kapsanmayan)}")

    basla = datetime.now(timezone.utc)
    kripto_fiyat, kripto_kaynak = kripto_fiyatlari_cek(kripto)
    yahoo_fiyat = yahoo_fiyatlari_cek(yahoo)
    metal_fiyat, metal_bayat = metal_fiyatlari_cek(metal, usdtry=yahoo_fiyat.get("USDTRY"))

    eksik_forex = {s for s in forex_yedek if s not in yahoo_fiyat}
    forex_fiyat, forex_tarih = forex_fiyatlari_cek(eksik_forex)

    tum_fiyatlar, fiyat_kaynagi = {}, {}
    for sembol, fiyat in forex_fiyat.items():
        tum_fiyatlar[sembol], fiyat_kaynagi[sembol] = fiyat, f"ECB {forex_tarih}"
    for sembol, fiyat in yahoo_fiyat.items():
        tum_fiyatlar[sembol], fiyat_kaynagi[sembol] = fiyat, "YAHOO"
    for sembol, fiyat in metal_fiyat.items():
        tum_fiyatlar[sembol], fiyat_kaynagi[sembol] = fiyat, "GOLDAPI"
    for sembol, fiyat in kripto_fiyat.items():
        tum_fiyatlar[sembol], fiyat_kaynagi[sembol] = fiyat, kripto_kaynak.get(sembol, "KRIPTO")

    sure = (datetime.now(timezone.utc) - basla).total_seconds()
    log(f"Canli fiyat cekilebilen: {len(tum_fiyatlar)} / {len(seviyeler)}  ({sure:.1f} sn)")
    if forex_fiyat:
        log(f"[NOT] {len(forex_fiyat)} parite Yahoo'dan gelmedi, Frankfurter/ECB "
            f"{forex_tarih} gunluk referans kuru kullanildi (gun ici degil).")

    if metal_bayat:
        bayat_ozet = (
            f"{len(metal_bayat)} metal sembolu BAYAT VERI oldugu icin atlandi "
            f"(gold-api.com {METAL_MAX_YAS_DK} dk esigi): "
            + ", ".join(f"{sem} ~{yas / 60:.1f} saat eski"
                        for sem, yas in sorted(metal_bayat.items())))
    else:
        bayat_ozet = (f"Bayat metal verisi yok — atlanan metal sembolu: 0 "
                      f"(esik {METAL_MAX_YAS_DK} dk).")
    if metal or metal_bayat:
        log(f"[METAL] {bayat_ozet}")

    sonuclar = []
    for sembol, veri in seviyeler.items():
        canli = tum_fiyatlar.get(sembol)
        if not canli:
            continue
        for ad, deger in veri["seviyeler"]:
            mesafe = (canli - deger) / deger * 100
            if abs(mesafe) <= esik:
                yon = "long adayi (destek)" if canli > deger else "short adayi (direnc)"
                sonuclar.append((abs(mesafe), sembol, canli, ad, deger, mesafe, yon,
                                 fiyat_kaynagi.get(sembol, "?")))

    sonuclar.sort(key=lambda x: x[0])

    return {
        "sonuclar": sonuclar,
        "seviyeler": seviyeler,
        "tum_fiyatlar": tum_fiyatlar,
        "tarih": tarih,
        "seviye_kaynagi": seviye_kaynagi,
        "sure": sure,
        "metal": metal,
        "metal_bayat": metal_bayat,
        "bayat_ozet": bayat_ozet,
        "esik": esik,
    }


def main():
    ap = argparse.ArgumentParser(description="MagicMA cizgilerine guncel fiyat mesafesi")
    ap.add_argument("--tarih", default=None, help="sadece bu gunun taramasini kullan (YYYY-AA-GG)")
    ap.add_argument("--esik", type=float, default=0.3, help="mesafe esigi yuzde (varsayilan 0.3)")
    ap.add_argument("--rapordan", action="store_true",
                    help="seviyeleri ham jsonl yerine markdown rapordan oku (2 ondalik, daha kaba)")
    ap.add_argument("--max-yas", type=int, default=10,
                    help="ham jsonl'de en yeni taramaya gore kac gun geriye kadar seviye kabul edilsin (0=sinirsiz)")
    ap.add_argument("--eksikler", action="store_true", help="canli fiyati bulunamayan sembolleri de listele")
    args = ap.parse_args()

    v = adaylari_hesapla(tarih=args.tarih, esik=args.esik, rapordan=args.rapordan,
                         max_yas=args.max_yas, log=print)
    sonuclar = v["sonuclar"]
    seviyeler = v["seviyeler"]
    tum_fiyatlar = v["tum_fiyatlar"]

    print(f"\n=== ESIK: %{args.esik} ICINDE {len(sonuclar)} ADAY (guncel fiyatla) ===\n")
    satirlar_cikti = []
    for _, sembol, canli, ad, deger, mesafe, yon, kaynak in sonuclar:
        satir = (f"{sembol:14s} canli={canli:>14.6g}  {ad:24s} cizgi={deger:>14.6g}  "
                 f"mesafe=%{mesafe:+.2f}  {yon:20s} [{kaynak}]")
        print(satir)
        satirlar_cikti.append(satir)

    eksik = sorted(s for s in seviyeler if s not in tum_fiyatlar)
    if args.eksikler and eksik:
        print(f"\n--- Canli fiyati bulunamayan {len(eksik)} sembol ---")
        print(", ".join(eksik))

    cikti_yolu = os.path.join(RAPOR_KLASOR, "fiyat_kontrol_son.md")
    with open(cikti_yolu, "w", encoding="utf-8") as f:
        f.write(f"# Fiyat Kontrol Sonucu — {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write(f"- Seviye kaynagi: `{v['seviye_kaynagi']}` · en yeni tarama: {v['tarih']}\n")
        f.write(f"- Esik: %{args.esik} · canli fiyat cekilebilen: "
                f"{len(tum_fiyatlar)}/{len(seviyeler)} ({v['sure']:.1f} sn)\n")
        f.write("- Canli fiyat kaynaklari: Binance/MEXC/Gate/Bybit/OKX/KuCoin (kripto), "
                "Yahoo Finance (BIST `.IS` / ABD / endeks / forex `=X`), "
                "api.gold-api.com (metal), Frankfurter-ECB (forex yedegi)\n")
        if v["metal"] or v["metal_bayat"]:
            f.write(f"- METAL: {v['bayat_ozet']}\n")
        f.write("\n")
        if satirlar_cikti:
            f.write("```\n" + "\n".join(satirlar_cikti) + "\n```\n")
        else:
            f.write("_Esik icinde aday yok._\n")
        if eksik:
            f.write(f"\n<details><summary>Canli fiyati bulunamayan {len(eksik)} sembol</summary>\n\n")
            f.write(", ".join(eksik) + "\n\n</details>\n")
    print(f"\nAyrica yazildi: {cikti_yolu}")


if __name__ == "__main__":
    main()
