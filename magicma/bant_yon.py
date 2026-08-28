"""
magicma/bant_yon.py

MagicMA seviyelerini BANT (bolge) olarak yorumlar ve islem yonunu belirler.

NEDEN: Indikator her zaman dilimi icin IKI cizgi uretiyor
  - "Magicma Günlük Alt Çizgi" + "Magicma Günlük Üst Çizgi"  -> Gunluk bant
  - "Magicma Haftalık -1"      + "Magicma Haftalık -2"       -> Haftalik bant
Bu ikisi bagimsiz seviye DEGIL, bir bandin iki siniri. Cizgileri ayri ayri
"fiyat altinda = direnc / ustunde = destek" diye etiketlemek kendi icinde
celisik sonuc veriyordu: fiyat bandin ICINDEYKEN ayni sembol bir cizgiye gore
SHORT, digerine gore LONG cikiyordu.

DIKKAT — cizgi ADLARI guvenilir degil: olculdu, 744 sembolun yalnizca 289'unda
(%39) "Alt Çizgi" gercekten "Üst Çizgi"den kucuk. Bu yuzden bandin sinirlari
ADA gore degil, DEGERE gore (min/max) kurulur.

YON KURALI (kullanici tanimi):
  - Fiyat bandin USTUNDE  -> bant destek  -> LONG adayi
  - Fiyat bandin ALTINDA  -> bant direnc  -> SHORT adayi
  - Fiyat bandin ICINDE   -> banda hangi taraftan girildigi belirler:
        yukaridan indiyse  -> bant destek  -> LONG adayi
        asagidan ciktiysa  -> bant direnc  -> SHORT adayi

Bant ici yon, TradingView scanner ucunun cok zaman dilimli high/low
kolonlariyla bulunur (tek POST, her sembol tipi icin calisir: kripto, BIST,
forex, ABD, endeks, metal). En dar zaman diliminden (bugun) baslanir, net
cevap vermezse hafta, sonra ay denenir:
  - Periyodun en yuksegi bandin USTUNDE, en dusugu banda girmemis
        -> fiyat yukaridan indi -> LONG
  - Periyodun en dusugu bandin ALTINDA, en yuksegi banda girmemis
        -> fiyat asagidan cikti -> SHORT
Hicbir periyot net cevap vermezse (fiyat o periyotta bandin iki tarafina da
tasmis, ya da hic tasmamis) son care olarak bant ici konum kullanilir: fiyat
bandin ust yarisindaysa LONG, alt yarisindaysa SHORT — bu durum gerekce
metninde "tahmin" olarak isaretlenir.
"""

import concurrent.futures

try:
    import requests
except ImportError:                                     # fiyat_kontrol zaten uyariyor
    requests = None

# Bant adi -> o banda ait cizgi adlari
BANT_TANIMI = (
    ("Günlük", ("Magicma Günlük Alt Çizgi", "Magicma Günlük Üst Çizgi")),
    ("Haftalık", ("Magicma Haftalık -1", "Magicma Haftalık -2")),
)

TV_SCANNER_URL = "https://scanner.tradingview.com/global/scan"
TV_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://tr.tradingview.com",
    "Referer": "https://tr.tradingview.com/",
}
# (periyot etiketi, high kolonu, low kolonu) — dardan genise sirali
TV_PERIYOTLAR = (
    ("bugun", "high", "low"),
    ("bu hafta", "high|1W", "low|1W"),
    ("bu ay", "High.1M", "Low.1M"),
)
TV_KOLONLAR = [k for _, y, d in TV_PERIYOTLAR for k in (y, d)]


# --------------------------------------------------------------------------
# Bant kurma
# --------------------------------------------------------------------------

def bantlari_kur(seviyeler):
    """[(cizgi_adi, deger), ...] -> [bant, ...]

    bant: {"ad", "alt", "ust", "cizgiler": {cizgi_adi: deger}}
    Sinirlar cizgi ADINDAN degil DEGERDEN turetilir (adlar guvenilir degil).
    Tanimli bir banda girmeyen cizgi kendi basina tek-cizgilik bant olur
    (alt == ust); boyle bir "bant"ta fiyat asla "icinde" olamaz, davranis eski
    geometrik kuralla ayni kalir.
    """
    kalan = dict(seviyeler)
    bantlar = []

    for bant_adi, cizgi_adlari in BANT_TANIMI:
        uyeler = {ad: kalan.pop(ad) for ad in cizgi_adlari if ad in kalan}
        if not uyeler:
            continue
        degerler = list(uyeler.values())
        bantlar.append({
            "ad": bant_adi,
            "alt": min(degerler),
            "ust": max(degerler),
            "cizgiler": uyeler,
        })

    for ad, deger in kalan.items():
        bantlar.append({"ad": ad, "alt": deger, "ust": deger, "cizgiler": {ad: deger}})

    return bantlar


def bant_bul(bantlar, cizgi_adi):
    """Verilen cizginin ait oldugu bandi dondurur (yoksa None)."""
    for bant in bantlar:
        if cizgi_adi in bant["cizgiler"]:
            return bant
    return None


def konum_belirle(fiyat, bant):
    """'ustunde' | 'altinda' | 'icinde'"""
    if fiyat > bant["ust"]:
        return "ustunde"
    if fiyat < bant["alt"]:
        return "altinda"
    return "icinde"


# --------------------------------------------------------------------------
# TradingView cok zaman dilimli high/low
# --------------------------------------------------------------------------

def tv_gecmis_cek(ticker_haritasi, parca=200, log=print):
    """{sembol: 'BORSA:TICKER'} -> {sembol: {periyot: (high, low)}}

    Tek POST ile (200'luk parcalar halinde) tum sembollerin bugun/bu hafta/
    bu ay en yuksek-en dusuk degerlerini ceker. Hata halinde bos dondurur —
    cagiran taraf son care kuralina duser.
    """
    if not ticker_haritasi or requests is None:
        return {}

    ters = {}
    for sembol, ticker in ticker_haritasi.items():
        ters.setdefault(str(ticker).upper(), sembol)

    sonuc = {}
    tickerlar = sorted(ters)
    for i in range(0, len(tickerlar), parca):
        dilim = tickerlar[i:i + parca]
        try:
            r = requests.post(TV_SCANNER_URL, headers=TV_HEADERS, timeout=20,
                              json={"symbols": {"tickers": dilim}, "columns": TV_KOLONLAR})
            r.raise_for_status()
            for satir in r.json().get("data") or []:
                sembol = ters.get(str(satir.get("s", "")).upper())
                degerler = satir.get("d") or []
                if not sembol or len(degerler) < len(TV_KOLONLAR):
                    continue
                periyotlar = {}
                for sira, (etiket, _, _) in enumerate(TV_PERIYOTLAR):
                    yuksek, dusuk = degerler[sira * 2], degerler[sira * 2 + 1]
                    if yuksek and dusuk:
                        periyotlar[etiket] = (float(yuksek), float(dusuk))
                if periyotlar:
                    sonuc[sembol] = periyotlar
        except Exception as e:
            log(f"[UYARI] TradingView gecmis (high/low) cekilemedi: {type(e).__name__}: {e}")
    return sonuc


# --------------------------------------------------------------------------
# Saatlik kapanis serisi (gercek gelis yonu icin)
# --------------------------------------------------------------------------

# Birlesik ticker'i (DOGEUSDT) baz/karsi olarak ayirmak icin — uzundan kisaya
KARSI_BIRIMLER = ("USDT", "USDC", "FDUSD", "TUSD", "DAI", "TRY", "EUR", "BTC", "ETH", "USD")
SERI_SAAT = 240          # ~10 gun saatlik bar; bandi en son ne zaman terk ettigini bulmaya yeter
_ISTEK_ZAMAN_ASIMI = 15


def _parite_ayir(ticker):
    """'DOGEUSDT' -> ('DOGE', 'USDT'). Cozulemezse (ticker, '')."""
    ust = ticker.upper()
    for karsi in KARSI_BIRIMLER:
        if ust.endswith(karsi) and len(ust) > len(karsi):
            return ust[:-len(karsi)], karsi
    return ust, ""


def _get(url, timeout=_ISTEK_ZAMAN_ASIMI):
    r = requests.get(url, headers={"User-Agent": TV_HEADERS["User-Agent"]}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _seri_binance_uyumlu(temel, ticker, aralik="1h"):
    """Binance ve MEXC ayni v3 semasini kullanir ama saatlik aralik adi FARKLI:
    Binance '1h', MEXC '60m' bekler ('1h' MEXC'te 400 Bad Request doner)."""
    veri = _get(f"{temel}/api/v3/klines?symbol={ticker}&interval={aralik}&limit={SERI_SAAT}")
    return [float(m[4]) for m in veri]                       # eskiden yeniye


def _seri_bybit(ticker):
    veri = _get(f"https://api.bybit.com/v5/market/kline?category=spot&symbol={ticker}"
                f"&interval=60&limit={min(SERI_SAAT, 1000)}")
    liste = (veri.get("result") or {}).get("list") or []
    return [float(m[4]) for m in reversed(liste)]                    # API yeniden eskiye


def _seri_okx(ticker):
    baz, karsi = _parite_ayir(ticker)
    veri = _get(f"https://www.okx.com/api/v5/market/candles?instId={baz}-{karsi}"
                f"&bar=1H&limit={min(SERI_SAAT, 300)}")
    return [float(m[4]) for m in reversed(veri["data"])]             # yeniden eskiye


def _seri_gateio(ticker):
    baz, karsi = _parite_ayir(ticker)
    veri = _get(f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={baz}_{karsi}"
                f"&interval=1h&limit={min(SERI_SAAT, 1000)}")
    return [float(m[2]) for m in veri]                       # [ts, hacim, KAPANIS, h, l, o]


def _seri_kucoin(ticker):
    baz, karsi = _parite_ayir(ticker)
    veri = _get(f"https://api.kucoin.com/api/v1/market/candles?symbol={baz}-{karsi}&type=1hour")
    return [float(m[2]) for m in reversed(veri["data"])]      # [ts, o, KAPANIS, h, l, ...]


BORSA_SERI = {
    "BINANCE": lambda t: _seri_binance_uyumlu("https://api.binance.com", t, "1h"),
    "MEXC": lambda t: _seri_binance_uyumlu("https://api.mexc.com", t, "60m"),
    "BYBIT": _seri_bybit,
    "OKX": _seri_okx,
    "GATEIO": _seri_gateio,
    "KUCOIN": _seri_kucoin,
}


def _seri_yahoo(yahoo_kodu):
    veri = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_kodu}"
                f"?range=1mo&interval=1h")
    sonuc = (veri.get("chart") or {}).get("result")
    if not sonuc:
        return []
    kapanislar = sonuc[0]["indicators"]["quote"][0]["close"]
    return [float(k) for k in kapanislar if k is not None]


def seri_cek(istekler, max_worker=12, log=print):
    """Bant ici sembollerin saatlik kapanis serisini ceker.

    istekler: {sembol: {"borsa": "BINANCE"|..., "ticker": "DOGEUSDT",
                        "yahoo": "THYAO.IS" (borsa yoksa)}}
    Doner: {sembol: [kapanis, ...]}  (eskiden yeniye sirali)

    Her sembol icin TEK istek; yalnizca bant ICINDE olan adaylar icin cagrilir
    (olculdu: ~750 sembolun 15-20'si), bu yuzden paralel olarak birkac saniye.
    """
    if not istekler or requests is None:
        return {}

    def _cek(cift):
        sembol, bilgi = cift
        try:
            borsa = (bilgi.get("borsa") or "").upper()
            if borsa in BORSA_SERI:
                return sembol, BORSA_SERI[borsa](bilgi["ticker"])
            if bilgi.get("yahoo"):
                return sembol, _seri_yahoo(bilgi["yahoo"])
        except Exception:
            pass
        return sembol, []

    seriler = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_worker) as ex:
        for sembol, seri in ex.map(_cek, sorted(istekler.items())):
            if seri:
                seriler[sembol] = seri
    return seriler


def seriden_yon(seri, bant):
    """Seriyi SONDAN basa tarar, fiyatin bandi en son hangi taraftan terk
    ettigini bulur. Doner: ('long'|'short', kac_bar_once) veya (None, None)."""
    alt, ust = bant["alt"], bant["ust"]
    for geri, kapanis in enumerate(reversed(seri)):
        if kapanis > ust:
            return "long", geri            # en son bandin USTUNDEYDI -> yukaridan indi
        if kapanis < alt:
            return "short", geri           # en son bandin ALTINDAYDI -> asagidan cikti
    return None, None


# --------------------------------------------------------------------------
# Yon
# --------------------------------------------------------------------------

def _sure_metni(bar):
    """Kac saatlik bar once oldugunu okunur hale getirir."""
    if bar <= 1:
        return "1 saat önce"
    if bar < 24:
        return f"{bar} saat önce"
    gun = bar / 24
    return f"{gun:.0f} gün önce" if gun >= 2 else "1 gün önce"


def yon_belirle(fiyat, bant, seri=None, gecmis=None):
    """Doner: (yon, konum, gerekce)  — yon: 'long' | 'short'

    fiyat  : canli fiyat
    bant   : bantlari_kur() ciktisindan bir bant
    seri   : saatlik kapanis listesi (eskiden yeniye) — en guvenilir kaynak
    gecmis : {periyot: (high, low)} — seri yoksa/yetmezse yedek

    Oncelik sirasi: (1) gercek saatlik seri, (2) TV toplu high/low, (3) bant ici
    konum tahmini.
    """
    konum = konum_belirle(fiyat, bant)

    if konum == "ustunde":
        return "long", konum, f"fiyat {bant['ad']} bandın ÜSTÜNDE — band destek"
    if konum == "altinda":
        return "short", konum, f"fiyat {bant['ad']} bandın ALTINDA — band direnç"

    if seri:
        yon, bar = seriden_yon(seri, bant)
        if yon == "long":
            return yon, konum, (f"{bant['ad']} bandın İÇİNDE, banda YUKARIDAN indi "
                                f"({_sure_metni(bar)}) — band destek")
        if yon == "short":
            return yon, konum, (f"{bant['ad']} bandın İÇİNDE, banda AŞAĞIDAN çıktı "
                                f"({_sure_metni(bar)}) — band direnç")

    alt, ust = bant["alt"], bant["ust"]
    for etiket, _, _ in TV_PERIYOTLAR:
        if not gecmis or etiket not in gecmis:
            continue
        yuksek, dusuk = gecmis[etiket]
        ustunu_asti = yuksek > ust
        altini_asti = dusuk < alt
        if ustunu_asti and not altini_asti:
            return "long", konum, f"{bant['ad']} bandın İÇİNDE, banda YUKARIDAN indi ({etiket}) — band destek"
        if altini_asti and not ustunu_asti:
            return "short", konum, f"{bant['ad']} bandın İÇİNDE, banda AŞAĞIDAN çıktı ({etiket}) — band direnç"

    # Son care: bant ici konum (gecmis net cevap vermedi)
    orta = (alt + ust) / 2
    if fiyat >= orta:
        return "long", konum, f"{bant['ad']} bandın İÇİNDE, üst yarıda (geliş yönü bulunamadı — TAHMİN)"
    return "short", konum, f"{bant['ad']} bandın İÇİNDE, alt yarıda (geliş yönü bulunamadı — TAHMİN)"


def yon_etiketi(yon):
    """Rapor/mesaj icin kisa Turkce etiket."""
    return "LONG adayi" if yon == "long" else "SHORT adayi"
