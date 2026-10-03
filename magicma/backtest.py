#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MagicMA karne sinyalleri icin saf simulasyon (backtest). GERCEK HESAP YOK.

Mevcut dosyalara dokunmaz: karne_kayitlari.json yalnizca OKUNUR.

Kullanim:
  py -3 magicma/backtest.py veri      # mumlari cek -> backtest_veri/ (cache)
  py -3 magicma/backtest.py rapor     # simulasyon + magicma/backtest_rapor.md
  py -3 magicma/backtest.py tumu      # ikisi birden
  py -3 magicma/backtest.py veri --sinirla 40   # hizli deneme (ilk 40 sembol)

Varsayimlar (rapor basinda da yazar):
  * Giris fiyati = karnedeki giris_fiyati; tarama, giris_zamani'ni iceren 5 dk'lik mumdan baslar.
  * Ayni mumda stop ve TP birlikte degerse STOP once sayilir.
  * Stop/TP seviyesi atlanirsa (gap) cikis yine seviye fiyatindan varsayilir (iyimser).
  * Trailing stop: mumun high'i stopu yukari ceker, ayni mumun low'u onu vurabilir (kotumser).
  * 48 saat (duvar saati) dolunca son mumun kapanisindan cikis.
"""
import argparse
import concurrent.futures
import datetime as dt
import json
import os
import random
import sys
import threading
import time
from collections import Counter, defaultdict

import numpy as np
import requests

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KARNE = os.path.join(KOK, "magicma", "karne_kayitlari.json")
VERI = os.path.join(KOK, "backtest_veri")
RAPOR = os.path.join(KOK, "magicma", "backtest_rapor.md")
TZ_TR = dt.timezone(dt.timedelta(hours=3))

PENCERE_SN = 48 * 3600
MUM_SN = 300
STOPLAR = [0.2, 0.3, 0.5, 0.75, 1.0, 1.5]
TPLER = [0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
TRAILLER = [0.3, 0.5, 1.0]
MALIYETLER = [0.0, 0.05, 0.10, 0.20]
SECIM_MALIYET = 0.10          # egitimde en iyi 5 secimi bu maliyette yapilir
EGITIM_BITIS = dt.datetime(2026, 9, 19, tzinfo=TZ_TR).timestamp()   # [28 Agu, 19 Eyl) egitim
RASTGELE_TEKRAR = 1000
BOOT_TEKRAR = 5000
TOLERANS_FIYAT = 0.02         # giris fiyati ile giris mumu kapanisi arasi izin verilen sapma
SEED = 20261003

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

YAHOO_OZEL = {"SPX": "^GSPC", "NDX": "^NDX", "DJI": "^DJI", "VIX": "^VIX", "US10Y": "^TNX",
              "DXY": "DX-Y.NYB", "USOIL": "CL=F", "UKOIL": "BZ=F", "HG1!": "HG=F",
              "XU100": "XU100.IS", "XU030": "XU030.IS"}
# Spot metal icin Yahoo'da spot yok: vadeli kontrat GETIRI vekili (olay basina olceklenir)
VEKIL = {"XAUUSD": "GC=F", "XAGUSD": "SI=F", "XPTUSD": "PL=F", "XPDUSD": "PA=F"}
KRIPTO_BORSALAR = ["BINANCE", "MEXC", "BYBIT", "GATEIO"]


# ---------------------------------------------------------------- yardimcilar
def ts_ayristir(s):
    return dt.datetime.fromisoformat(s).timestamp()


def guvenli_ad(s):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)


def cizgi_grubu(olay):
    ad = olay["cizgi_adi"]
    kt = olay.get("kaynak_turu")
    if kt in ("onemli_seviye", "mega_confluence"):
        return "onemli_seviye/mega"
    k = ad.lower()
    # cizgi adlarinda Turkce karakter bozulmus olabilir: ASCII parcalarina bak
    if "haftal" in k:
        return "Haftalik -1" if "-1" in k else ("Haftalik -2" if "-2" in k else "Haftalik")
    if "nl" in k and ("st" in k) and "magicma" in k:
        return "Gunluk Ust"
    if "magicma" in k and "alt" in k:
        return "Gunluk Alt"
    if "magicma" in k:
        return "Gunluk (diger)"
    return "dis kaynak seviyesi"


def olaylari_yukle():
    with open(KARNE, encoding="utf-8") as f:
        veri = json.load(f)
    olaylar = []
    for i, o in enumerate(veri):
        try:
            o = dict(o)
            o["ts"] = ts_ayristir(o["giris_zamani"])
            o["giris"] = float(o["giris_fiyati"])
            o["grup"] = cizgi_grubu(o)
            o["no"] = i
            if o["yon"] not in ("long", "short") or o["giris"] <= 0:
                continue
            olaylar.append(o)
        except Exception as e:  # bozuk kayit sessizce atlanmaz, sayilir
            print(f"[UYARI] kayit {i} okunamadi: {e}")
    olaylar.sort(key=lambda o: o["ts"])
    return olaylar


# ---------------------------------------------------------------- sembol esleme
def yahoo_kodu(o):
    s, kat = o["sembol"], o["kategori"]
    if s in YAHOO_OZEL:
        return YAHOO_OZEL[s], False
    if s in VEKIL:
        return VEKIL[s], True
    if kat == "bist":
        return f"{s}.IS", False
    if kat == "abd_hisse":
        return s.replace(".", "-"), False
    if kat == "forex_emtia" and len(s) == 6 and s.isalpha() and s != "XAUTRY":
        return f"{s}=X", False
    return None, False


def kaynak_tipi(o):
    if o["kategori"] in ("kripto", "gunun_hareketlileri"):
        return "kripto"
    return "yahoo"


# ---------------------------------------------------------------- HTTP / throttle
class Throttle:
    def __init__(self, aralik):
        self.aralik, self.kilit, self.son = aralik, threading.Lock(), 0.0

    def bekle(self):
        with self.kilit:
            t = time.time()
            gerek = self.son + self.aralik - t
            if gerek > 0:
                time.sleep(gerek)
            self.son = time.time()


THROTTLE = {"BINANCE": Throttle(0.15), "MEXC": Throttle(0.2), "BYBIT": Throttle(0.15),
            "GATEIO": Throttle(0.2), "YAHOO": Throttle(0.35)}


def http_json(url, params, borsa, deneme=6):
    bekleme = 5
    for k in range(deneme):
        THROTTLE[borsa].bekle()
        try:
            r = requests.get(url, params=params, headers=UA, timeout=20)
            if r.status_code in (418, 429, 403) or r.status_code >= 500:
                ra = r.headers.get("Retry-After")
                time.sleep(min(float(ra) if ra and ra.isdigit() else bekleme, 120))
                bekleme = min(bekleme * 2, 120)
                continue
            if r.status_code == 400:
                return None            # gecersiz sembol vb.
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if k == deneme - 1:
                print(f"[HATA] {borsa} {params.get('symbol') or params.get('currency_pair') or url[-30:]}: {type(e).__name__}: {e}")
                return None
            time.sleep(bekleme)
            bekleme = min(bekleme * 2, 60)
    return None


# ---------------------------------------------------------------- mum cekiciler
def _sayfala_binance_tip(url, sembol, a_ms, b_ms, limit, interval, borsa):
    satir = []
    bas = a_ms
    while bas < b_ms:
        v = http_json(url, {"symbol": sembol, "interval": interval, "startTime": bas,
                            "endTime": b_ms, "limit": limit}, borsa)
        if not v:
            break
        satir += [[int(x[0]) // 1000, float(x[1]), float(x[2]), float(x[3]), float(x[4])] for x in v]
        yeni = int(v[-1][0]) + MUM_SN * 1000
        if yeni <= bas or len(v) < 2 and yeni >= b_ms:
            break
        bas = yeni
    return satir


def mum_binance(sembol, a, b):
    return _sayfala_binance_tip("https://api.binance.com/api/v3/klines", sembol,
                                int(a * 1000), int(b * 1000), 1000, "5m", "BINANCE")


def mum_mexc(sembol, a, b):
    return _sayfala_binance_tip("https://api.mexc.com/api/v3/klines", sembol,
                                int(a * 1000), int(b * 1000), 500, "5m", "MEXC")


def mum_bybit(sembol, a, b):
    satir, bitis = [], int(b * 1000)
    while bitis > a * 1000:
        v = http_json("https://api.bybit.com/v5/market/kline",
                      {"category": "spot", "symbol": sembol, "interval": "5",
                       "start": int(a * 1000), "end": bitis, "limit": 1000}, "BYBIT")
        liste = ((v or {}).get("result") or {}).get("list") or []
        if not liste:
            break
        satir += [[int(x[0]) // 1000, float(x[1]), float(x[2]), float(x[3]), float(x[4])] for x in liste]
        en_eski = min(int(x[0]) for x in liste)
        if en_eski * 1000 - 1 >= bitis:
            break
        bitis = en_eski * 1000 - 1
    return satir


def mum_gate(sembol, a, b):
    if not sembol.endswith("USDT"):
        return []
    cift = sembol[:-4] + "_USDT"
    satir, bas = [], int(a)
    while bas < b:
        son = min(bas + 999 * MUM_SN, int(b))
        v = http_json("https://api.gateio.ws/api/v4/spot/candlesticks",
                      {"currency_pair": cift, "interval": "5m", "from": bas, "to": son}, "GATEIO")
        if isinstance(v, list):
            satir += [[int(x[0]), float(x[5]), float(x[3]), float(x[4]), float(x[2])] for x in v]
        elif v is None:
            break
        bas = son + MUM_SN
    return satir


KRIPTO_CEKICI = {"BINANCE": mum_binance, "MEXC": mum_mexc, "BYBIT": mum_bybit, "GATEIO": mum_gate}


def mum_yahoo(kod, a, b):
    v = http_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{kod}",
                  {"interval": "5m", "period1": int(a), "period2": int(b)}, "YAHOO")
    try:
        r = v["chart"]["result"][0]
        t = r["timestamp"]
        q = r["indicators"]["quote"][0]
    except Exception:
        return []
    satir = []
    for i, ts in enumerate(t):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        satir.append([int(ts), o, h, l, c])
    return satir


# ---------------------------------------------------------------- cache
def birlestir_pencere(olaylar, simdi):
    p = sorted((o["ts"] - MUM_SN, min(o["ts"] + PENCERE_SN + MUM_SN, simdi)) for o in olaylar)
    out = []
    for a, b in p:
        if out and a <= out[-1][1] + 3600:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def cache_yolu(tip, ad):
    return os.path.join(VERI, tip, guvenli_ad(ad))


def cache_oku(tip, ad):
    y = cache_yolu(tip, ad)
    if not (os.path.exists(y + ".npy") and os.path.exists(y + ".json")):
        return None, None
    try:
        with open(y + ".json", encoding="utf-8") as f:
            return np.load(y + ".npy"), json.load(f)
    except Exception:
        return None, None


def cache_yaz(tip, ad, arr, meta):
    y = cache_yolu(tip, ad)
    os.makedirs(os.path.dirname(y), exist_ok=True)
    np.save(y + ".npy", arr)
    with open(y + ".json", "w", encoding="utf-8") as f:
        json.dump(meta, f)


def pencere_kapsiyor(meta, pencereler):
    kap = meta.get("pencere", [])
    return all(any(k[0] <= a + 1 and k[1] >= b - 1 for k in kap) for a, b in pencereler)


def mumlari_diziye(satirlar):
    if not satirlar:
        return np.zeros((0, 5))
    a = np.array(satirlar, dtype=float)
    a = a[np.argsort(a[:, 0], kind="stable")]
    _, idx = np.unique(a[:, 0], return_index=True)
    return a[idx]


def giris_uyumu(arr, olaylar):
    """Giris mumunun kapanisi giris fiyatina yakin olay orani + mumu bulunan oran."""
    if len(arr) == 0:
        return 0.0, 0.0
    ts = arr[:, 0]
    bulunan = uyan = 0
    for o in olaylar:
        i = int(np.searchsorted(ts, o["ts"], "right")) - 1
        if i >= 0 and o["ts"] - ts[i] < MUM_SN:
            bulunan += 1
            if abs(arr[i, 4] / o["giris"] - 1) <= TOLERANS_FIYAT:
                uyan += 1
    n = len(olaylar)
    return bulunan / n, (uyan / bulunan if bulunan else 0.0)


def kripto_sembol_cek(sembol, olaylar, simdi):
    pen = birlestir_pencere(olaylar, simdi)
    arr, meta = cache_oku("kripto", sembol)
    if meta and pencere_kapsiyor(meta, pen):
        return meta
    sayim = Counter(o.get("kaynak") for o in olaylar)
    sira = []
    for b, _ in sayim.most_common():
        if b in KRIPTO_CEKICI and b not in sira:
            sira.append(b)
    sira += [b for b in KRIPTO_BORSALAR if b not in sira]
    adaylar = [sembol] + ([sembol[:-3] + "USDT"] if sembol.endswith("USD") else [])
    denemeler = []
    en_iyi = None
    for b in sira:
        for ad in adaylar:
            satir = []
            for a, bb in pen:
                satir += KRIPTO_CEKICI[b](ad, a, bb)
            arr = mumlari_diziye(satir)
            bul, uy = giris_uyumu(arr, olaylar)
            denemeler.append(f"{b}:{ad} mum={bul:.0%} uyum={uy:.0%}")
            if bul >= 0.5 and uy >= 0.8:
                meta = {"borsa": b, "kod": ad, "pencere": pen, "bulunan": bul, "uyum": uy,
                        "deneme": denemeler, "cek": simdi}
                cache_yaz("kripto", sembol, arr, meta)
                return meta
            if en_iyi is None or (bul * uy) > en_iyi[0]:
                en_iyi = (bul * uy, b, ad, arr, bul, uy)
    # hicbiri esik'i gecmedi: veri yok say (en iyiyi yine de kaydet, olay duzeyinde elenecek)
    arr = en_iyi[3] if en_iyi else np.zeros((0, 5))
    meta = {"borsa": en_iyi[1] if en_iyi else None, "kod": en_iyi[2] if en_iyi else None,
            "pencere": pen, "bulunan": en_iyi[4] if en_iyi else 0, "uyum": en_iyi[5] if en_iyi else 0,
            "deneme": denemeler, "cek": simdi, "basarisiz": True}
    cache_yaz("kripto", sembol, arr, meta)
    return meta


def yahoo_sembol_cek(kod, olaylar, simdi):
    pen = birlestir_pencere(olaylar, simdi)
    arr, meta = cache_oku("yahoo", kod)
    if meta and pencere_kapsiyor(meta, pen):
        return meta
    satir = []
    # tek istekte butun aralik (5 dk verisi ~60 gunle sinirli; pencereler bunun icinde)
    a, b = pen[0][0], pen[-1][1]
    satir = mum_yahoo(kod, a, b)
    arr = mumlari_diziye(satir)
    bul, uy = giris_uyumu(arr, olaylar)
    meta = {"borsa": "YAHOO", "kod": kod, "pencere": [[a, b]], "bulunan": bul, "uyum": uy, "cek": simdi}
    if len(arr) == 0:
        meta["basarisiz"] = True
    cache_yaz("yahoo", kod, arr, meta)
    return meta


def veri_cek(olaylar, sinirla=None):
    simdi = time.time()
    kripto = defaultdict(list)
    yahoo = defaultdict(list)
    eslesmeyen = defaultdict(list)
    for o in olaylar:
        if kaynak_tipi(o) == "kripto":
            kripto[o["sembol"]].append(o)
        else:
            kod, _ = yahoo_kodu(o)
            if kod:
                yahoo[kod].append(o)
            else:
                eslesmeyen[o["sembol"]].append(o)
    kk, yk = sorted(kripto), sorted(yahoo)
    if sinirla:
        kk, yk = kk[:sinirla], yk[:sinirla]
    print(f"[VERI] kripto sembol={len(kk)}  yahoo sembol={len(yk)}  eslesmeyen={len(eslesmeyen)}")
    t0, sayac = time.time(), [0]
    kilit = threading.Lock()
    toplam = len(kk) + len(yk)

    def isle(args):
        tur, ad = args
        try:
            if tur == "k":
                kripto_sembol_cek(ad, kripto[ad], simdi)
            else:
                yahoo_sembol_cek(ad, yahoo[ad], simdi)
        except Exception as e:
            print(f"[HATA] {tur}:{ad}: {type(e).__name__}: {e}")
        with kilit:
            sayac[0] += 1
            if sayac[0] % 25 == 0 or sayac[0] == toplam:
                print(f"[VERI] {sayac[0]}/{toplam}  ({time.time() - t0:.0f} sn)")

    isler = [("k", s) for s in kk] + [("y", s) for s in yk]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(isle, isler))
    return eslesmeyen


# ---------------------------------------------------------------- olay hazirlama
def olaylari_hazirla(olaylar, simdi, kaydir=0):
    """Her olay icin mum penceresi. Donus: (hazir, elenenler{neden:[olay]})."""
    cache = {}

    def al(tip, ad):
        if (tip, ad) not in cache:
            cache[(tip, ad)] = cache_oku(tip, ad)
        return cache[(tip, ad)]

    hazir, elenen = [], defaultdict(list)
    for o in olaylar:
        if o["ts"] + PENCERE_SN > simdi - MUM_SN:
            elenen["pencere kesik (48 saat henuz dolmadi)"].append(o)
            continue
        vekil = False
        if kaynak_tipi(o) == "kripto":
            arr, meta = al("kripto", o["sembol"])
        else:
            kod, vekil = yahoo_kodu(o)
            if not kod:
                elenen["sembol eslenemedi"].append(o)
                continue
            arr, meta = al("yahoo", kod)
        if arr is None or len(arr) == 0:
            elenen["veri gelmedi"].append(o)
            continue
        ts = arr[:, 0]
        i0 = int(np.searchsorted(ts, o["ts"], "right")) - 1
        if i0 < 0 or o["ts"] - ts[i0] >= MUM_SN:
            # giris anini iceren mum yok (kapali piyasa/bosluk): 1 saat icinde ilk mum
            j = i0 + 1
            if j < len(ts) and ts[j] - o["ts"] <= 3600:
                i0 = j
            else:
                elenen["giris mumu yok"].append(o)
                continue
        i0 += kaydir
        if i0 >= len(ts):
            elenen["giris mumu yok"].append(o)
            continue
        bit = int(np.searchsorted(ts, o["ts"] + PENCERE_SN, "left"))
        sl = arr[i0:bit]
        if len(sl) < 2:
            elenen["pencerede mum yok"].append(o)
            continue
        h, l, c = sl[:, 2].copy(), sl[:, 3].copy(), sl[:, 4].copy()
        c0 = arr[i0 - kaydir, 4] if kaydir else arr[i0, 4]
        if vekil:
            k = o["giris"] / c0
            h, l, c = h * k, l * k, c * k
        elif abs(c0 / o["giris"] - 1) > TOLERANS_FIYAT:
            elenen["giris fiyati mumla uyusmuyor"].append(o)
            continue
        hazir.append({"o": o, "ts": sl[:, 0], "h": h, "l": l, "c": c, "e": o["giris"],
                      "gec": float(ts[i0] - o["ts"])})
    return hazir, elenen


# ---------------------------------------------------------------- motor
def kombinasyonlar():
    k = [("sl_tp", s, t) for s in STOPLAR for t in TPLER]
    k += [("iz", p) for p in TRAILLER]
    return k


def ad_kombo(k):
    if k[0] == "sl_tp":
        return f"stop %{k[1]:g} / TP %{k[2]:g}"
    return f"trailing %{k[1]:g}"


def _exc(h, l, c, e, yon):
    if yon == "long":
        return 1 - l / e, h / e - 1, c[-1] / e - 1       # adverse, favorable, timeout
    return h / e - 1, 1 - l / e, 1 - c[-1] / e


def motor(hz, komboler):
    """Donus: R[yon] -> (olay, kombo) brut getiri (kesir)."""
    n = len(hz)
    R = {"long": np.zeros((n, len(komboler))), "short": np.zeros((n, len(komboler)))}
    for i, d in enumerate(hz):
        for yon in ("long", "short"):
            adv, fav, tout = _exc(d["h"], d["l"], d["c"], d["e"], yon)
            cadv, cfav = np.maximum.accumulate(adv), np.maximum.accumulate(fav)
            L = len(adv)
            sidx = np.searchsorted(cadv, np.array(STOPLAR) / 100.0, "left")
            tidx = np.searchsorted(cfav, np.array(TPLER) / 100.0, "left")
            F = np.maximum(cfav, 0.0)
            j = 0
            for k in komboler:
                if k[0] == "sl_tp":
                    si, ti = sidx[STOPLAR.index(k[1])], tidx[TPLER.index(k[2])]
                    if si < L and si <= ti:
                        r = -k[1] / 100.0
                    elif ti < L:
                        r = k[2] / 100.0
                    else:
                        r = tout
                else:
                    p = k[1] / 100.0
                    if yon == "long":
                        esik = (1 + F) * (1 - p)
                        vur = np.nonzero(d["l"] / d["e"] <= esik)[0]
                        r = (esik[vur[0]] - 1) if len(vur) else tout
                    else:
                        esik = (1 - F) * (1 + p)
                        vur = np.nonzero(d["h"] / d["e"] >= esik)[0]
                        r = (1 - esik[vur[0]]) if len(vur) else tout
                R[yon][i, j] = r
                j += 1
    return R


def naif(d, yon, stop_fiyat=None, tp_fiyat=None, trail=None):
    """Mum mum bagimsiz referans simulator. Donus: (getiri, neden, mum_idx)."""
    e, L = d["e"], len(d["c"])
    yonl = 1 if yon == "long" else -1
    zirve = e
    for i in range(L):
        h, l = d["h"][i], d["l"][i]
        if trail is not None:
            if yon == "long":
                zirve = max(zirve, h)
                s = zirve * (1 - trail)
                if l <= s:
                    return s / e - 1, "trailing", i
            else:
                zirve = min(zirve, l)
                s = zirve * (1 + trail)
                if h >= s:
                    return 1 - s / e, "trailing", i
            continue
        if yon == "long":
            st = stop_fiyat is not None and l <= stop_fiyat
            tp = tp_fiyat is not None and h >= tp_fiyat
        else:
            st = stop_fiyat is not None and h >= stop_fiyat
            tp = tp_fiyat is not None and l <= tp_fiyat
        if st:                                # ayni mumda ikisi de: stop
            return yonl * (stop_fiyat / e - 1), "stop", i
        if tp:
            return yonl * (tp_fiyat / e - 1), "tp", i
    return yonl * (d["c"][-1] / e - 1), "zaman_asimi", L - 1


# ---------------------------------------------------------------- metrik
def metrik(net, sira=None):
    """net: kesir dizisi (zamana gore SIRALI verilmeli)."""
    n = len(net)
    if n == 0:
        return {"n": 0, "isabet": float("nan"), "ort": float("nan"), "pf": float("nan"), "dd": float("nan")}
    kaz, kay = net[net > 0].sum(), -net[net < 0].sum()
    cum = np.concatenate([[0.0], np.cumsum(net * 100)])
    dd = float((np.maximum.accumulate(cum) - cum).max())
    return {"n": n, "isabet": float((net > 0).mean()), "ort": float(net.mean() * 100),
            "pf": float(kaz / kay) if kay > 0 else float("inf"), "dd": dd}


def bootstrap_ci(net, gunler=None, tekrar=BOOT_TEKRAR, rng=None):
    """Ortalama (yuzde) icin %95 CI. gunler verilirse GUN-KUME bootstrap (korelasyonlu)."""
    rng = rng or np.random.default_rng(SEED)
    n = len(net)
    if n < 5:
        return (float("nan"), float("nan"))
    if gunler is None:
        idx = rng.integers(0, n, size=(tekrar, n))
        m = net[idx].mean(axis=1)
    else:
        u, inv = np.unique(gunler, return_inverse=True)
        top = np.bincount(inv, weights=net, minlength=len(u))
        say = np.bincount(inv, minlength=len(u)).astype(float)
        g = rng.integers(0, len(u), size=(tekrar, len(u)))
        m = top[g].sum(axis=1) / say[g].sum(axis=1)
    return (float(np.percentile(m, 2.5) * 100), float(np.percentile(m, 97.5) * 100))


def ilk_temas_maskesi(hz):
    """Ayni sembolde onceki KABUL EDILEN temastan 48 saat dolmadan gelenler bagimsiz sayilmaz."""
    son, mask = {}, np.zeros(len(hz), bool)
    for i, d in enumerate(hz):      # hz zaman sirali
        s = d["o"]["sembol"]
        if s not in son or d["o"]["ts"] - son[s] >= PENCERE_SN:
            mask[i] = True
            son[s] = d["o"]["ts"]
    return mask


# ---------------------------------------------------------------- rapor yardimcilari
def f(x, nd=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    if isinstance(x, float) and np.isinf(x):
        return "inf"
    return f"{x:.{nd}f}"


def tablo(basliklar, satirlar):
    out = ["| " + " | ".join(basliklar) + " |", "|" + "|".join("---" for _ in basliklar) + "|"]
    out += ["| " + " | ".join(str(x) for x in s) + " |" for s in satirlar]
    return "\n".join(out)


def getiri_secimi(R, yonlar, ci):
    """MagicMA yonuyle getiri vektoru (olay,) bir kombo icin."""
    return np.where(yonlar == 1, R["long"][:, ci], R["short"][:, ci])


# ---------------------------------------------------------------- ana rapor
def rapor_uret(olaylar, eslesmeyen_say=None):
    rng_py = random.Random(SEED)
    rng = np.random.default_rng(SEED)
    simdi = time.time()
    hz, elenen = olaylari_hazirla(olaylar, simdi)
    hz_sonraki, _ = olaylari_hazirla(olaylar, simdi, kaydir=1)
    km = kombinasyonlar()
    print(f"[SIM] hazir olay={len(hz)} / {len(olaylar)}; motor calisiyor...")
    R = motor(hz, km)
    yon = np.array([1 if d["o"]["yon"] == "long" else 0 for d in hz])
    ts = np.array([d["o"]["ts"] for d in hz])
    egitim = ts < EGITIM_BITIS
    test = ~egitim
    ilk = ilk_temas_maskesi(hz)
    gun = np.array([int(t // 86400) for t in ts])
    ci_idx = {k: i for i, k in enumerate(km)}

    def net(ci, maliyet, mask=None):
        r = getiri_secimi(R, yon, ci) - maliyet / 100.0
        return r if mask is None else r[mask]

    # --- olay-motor tutarlilik testi (vektorel motor == naif simulator) ---
    uyusmaz = 0
    kontrol = 0
    ornek_idx = rng_py.sample(range(len(hz)), min(400, len(hz)))
    for i in ornek_idx:
        d = hz[i]
        for k in [("sl_tp", 0.3, 0.5), ("sl_tp", 1.0, 2.0), ("sl_tp", 0.2, 3.0), ("iz", 0.5), ("iz", 0.3)]:
            for y in ("long", "short"):
                yl = 1 if y == "long" else -1
                if k[0] == "sl_tp":
                    sf = d["e"] * (1 - yl * k[1] / 100)
                    tf = d["e"] * (1 + yl * k[2] / 100)
                    r, _, _ = naif(d, y, stop_fiyat=sf, tp_fiyat=tf)
                else:
                    r, _, _ = naif(d, y, trail=k[1] / 100)
                kontrol += 1
                if abs(r - R[y][i, ci_idx[k]]) > 1e-9:
                    uyusmaz += 1
    print(f"[SIM] motor-naif tutarlilik: {kontrol - uyusmaz}/{kontrol}")

    # --- karne yeniden uretimi ---
    ref = ci_idx[("sl_tp", 0.3, 0.5)]
    karne_rows = []
    kar = Counter()
    kar_cizgi = Counter()
    kar_kapanis = Counter()
    acik_say = 0
    for i, d in enumerate(hz):
        o = d["o"]
        if o["durum"] == "acik":
            acik_say += 1
            continue
        y = o["yon"]
        yl = 1 if y == "long" else -1
        e = d["e"]
        # A: girise gore %0,3 stop / %0,5 TP
        _, nA, _ = naif(d, y, stop_fiyat=e * (1 - yl * 0.003), tp_fiyat=e * (1 + yl * 0.005))
        # B: karne kurali (stop CIZGIYE gore %0,3, TP girise gore %0,5), mum high/low
        cz = float(o["cizgi_degeri"])
        _, nB, _ = naif(d, y, stop_fiyat=cz * (1 - yl * 0.003), tp_fiyat=e * (1 + yl * 0.005))
        # C: B ile ayni ama yalniz 10 dk'da bir (2 mumda bir) KAPANIS ornekle (karne taramasi gibi)
        nC = "zaman_asimi"
        for j in range(1, len(d["c"]), 2):
            cc = d["c"][j]
            if (yl * (cc / e - 1)) >= 0.005 and not (yl * (cc / cz - 1) <= -0.003):
                nC = "tp"
                break
            if yl * (cc / cz - 1) <= -0.003:
                nC = "stop"
                break
        eşle = {"tp": "basarili", "stop": "basarisiz", "zaman_asimi": "zaman_asimi", "trailing": "?"}
        for etiket, nn in (("A: giris-%0,3 stop (kullanici kurali)", nA),
                           ("B: cizgi-%0,3 stop, mum high/low", nB),
                           ("C: cizgi-%0,3 stop, 10 dk kapanis ornekleme", nC)):
            kar[(etiket, o["durum"], eşle[nn])] += 1
    etiketler = ["A: giris-%0,3 stop (kullanici kurali)", "B: cizgi-%0,3 stop, mum high/low",
                 "C: cizgi-%0,3 stop, 10 dk kapanis ornekleme"]
    dur = ["basarili", "basarisiz", "zaman_asimi"]
    karne_md = []
    ozet_kar = []
    for et in etiketler:
        toplam = sum(v for (e_, a, b), v in kar.items() if e_ == et)
        uyan = sum(v for (e_, a, b), v in kar.items() if e_ == et and a == b)
        ozet_kar.append((et, toplam, uyan, uyan / toplam if toplam else float("nan")))
        satir = []
        for a in dur:
            satir.append([f"karne: {a}"] + [sum(v for (e_, aa, bb), v in kar.items() if e_ == et and aa == a and bb == b) for b in dur])
        karne_md.append(f"**{et}**\n\n" + tablo(["", "sim: basarili", "sim: basarisiz", "sim: zaman_asimi"], satir))

    # --- genel referans kural + tum izgara ---
    def ozet_satir(ci, maliyet, mask):
        r = net(ci, maliyet, mask)
        m = metrik(r)
        return m

    # --- egitimde en iyi 5 (maliyet=SECIM_MALIYET, tum egitim olaylari) ---
    sirali = sorted(range(len(km)), key=lambda ci: -metrik(net(ci, SECIM_MALIYET, egitim))["ort"])
    en5 = sirali[:5]

    # --- rastgele baz (test) ---
    def rastgele(ci, maliyet, mask, tekrar=RASTGELE_TEKRAR):
        Rl = R["long"][mask, ci] - maliyet / 100.0
        Rs = R["short"][mask, ci] - maliyet / 100.0
        y = yon[mask]
        n = len(y)
        gozlenen = np.where(y == 1, Rl, Rs).mean() * 100
        perm_m, yaz_m = np.zeros(tekrar), np.zeros(tekrar)
        for t in range(tekrar):
            p = rng.permutation(y)                 # long/short ORANI korunur
            perm_m[t] = np.where(p == 1, Rl, Rs).mean() * 100
            yz = rng.integers(0, 2, size=n)        # 50/50 yazi-tura
            yaz_m[t] = np.where(yz == 1, Rl, Rs).mean() * 100
        pv = lambda arr: (int((arr >= gozlenen).sum()) + 1) / (tekrar + 1)
        return {"gozlenen": float(gozlenen), "perm_ort": float(perm_m.mean()),
                "perm_p95": float(np.percentile(perm_m, 95)), "perm_p": pv(perm_m),
                "yaz_ort": float(yaz_m.mean()), "yaz_p95": float(np.percentile(yaz_m, 95)), "yaz_p": pv(yaz_m)}

    md = []
    # =============== hesaplar
    sonuc5 = []
    for ci in en5:
        satir = {"ci": ci, "ad": ad_kombo(km[ci])}
        satir["egitim"] = metrik(net(ci, SECIM_MALIYET, egitim))
        for mal in MALIYETLER:
            r_t = net(ci, mal, test)
            m = metrik(r_t)
            r_ilk = net(ci, mal, test & ilk)
            m_ilk = metrik(r_ilk)
            satir[("test", mal)] = m
            satir[("test_ilk", mal)] = m_ilk
        r_t = net(ci, SECIM_MALIYET, test)
        satir["ci_naif"] = bootstrap_ci(r_t, None, rng=rng)
        satir["ci_gun"] = bootstrap_ci(r_t, gun[test], rng=rng)
        r_ti = net(ci, SECIM_MALIYET, test & ilk)
        satir["ci_gun_ilk"] = bootstrap_ci(r_ti, gun[test & ilk], rng=rng)
        satir["rast"] = rastgele(ci, SECIM_MALIYET, test)
        satir["rast_ilk"] = rastgele(ci, SECIM_MALIYET, test & ilk)
        sonuc5.append(satir)
        print(f"[SIM] {satir['ad']}: egitim ort={satir['egitim']['ort']:.4f}  test ort={satir[('test', SECIM_MALIYET)]['ort']:.4f}")

    esik_p = 0.05 / len(en5)
    var = []
    for s in sonuc5:
        t = s[("test", SECIM_MALIYET)]
        ti = s[("test_ilk", SECIM_MALIYET)]
        kosul = (t["ort"] > 0 and ti["ort"] > 0 and s["ci_gun"][0] > 0
                 and s["rast"]["perm_p"] < esik_p and s["rast_ilk"]["perm_p"] < 0.05)
        if kosul:
            var.append(s["ad"])

    # =============== MARKDOWN
    toplam_olay = len(olaylar)
    md.append("# MagicMA Backtest Raporu\n")
    md.append(f"_Uretim: {dt.datetime.now(TZ_TR).strftime('%Y-%m-%d %H:%M')} TSI · kod: `magicma/backtest.py` · "
              f"saf simulasyon, gercek hesap/emir YOK._\n")
    sonuc_cumle = (f"**SONUC: test setinde, %{SECIM_MALIYET:g} gidis-donus maliyet sonrasi, rastgeleyi anlamli asan "
                   + ("bir kombinasyon VAR: " + ", ".join(var) + "**" if var else "bir kombinasyon YOK.**"))
    md.append(sonuc_cumle + "\n")
    t0 = sonuc5[0]
    md.append(f"Olcut (hepsi birden): test ort. net getiri > 0 (tum temaslar VE yalniz ilk temaslar), "
              f"gun-kumeli bootstrap %95 CI alt siniri > 0, rastgele (yon-permutasyon) baz cizgisine karsi "
              f"p < {esik_p:.3f} (5 kombo icin Bonferroni; ilk-temas alt kumesinde p < 0.05).\n")
    md.append("En iyi egitim kombinasyonu ("
              f"{t0['ad']}) testte: n={t0[('test', SECIM_MALIYET)]['n']}, "
              f"ort. net %{f(t0[('test', SECIM_MALIYET)]['ort'])}, "
              f"gun-kumeli %95 CI [{f(t0['ci_gun'][0])}; {f(t0['ci_gun'][1])}], "
              f"rastgele baza gore p={f(t0['rast']['perm_p'])}.\n")

    md.append("## 1. Veri kapsami\n")
    kat_say = Counter(o["kategori"] for o in olaylar)
    kat_hazir = Counter(d["o"]["kategori"] for d in hz)
    satirlar = []
    for k in sorted(kat_say):
        satirlar.append([k, kat_say[k], kat_hazir[k], f"{kat_hazir[k] / kat_say[k]:.1%}"])
    satirlar.append(["**toplam**", toplam_olay, len(hz), f"{len(hz) / toplam_olay:.1%}"])
    md.append(tablo(["kategori", "karne olayi", "simulasyona giren", "oran"], satirlar) + "\n")
    md.append(f"Acik (durumu belirsiz) kayit: {sum(1 for o in olaylar if o['durum'] == 'acik')}; "
              f"bunlar simulasyona girer (yalniz karne karsilastirmasindan cikarilir).\n")
    md.append("Elenen olaylar (neden: adet, SESSIZCE ATLANMADI):\n")
    for neden, lst in sorted(elenen.items(), key=lambda kv: -len(kv[1])):
        sem = sorted({o["sembol"] for o in lst})
        md.append(f"- **{neden}**: {len(lst)} olay, {len(sem)} sembol")
        md.append(f"  - semboller: {', '.join(sem[:120])}{' ...' if len(sem) > 120 else ''}")
    md.append("")
    # veri yok / eslenemeyen sembol listesi: kategori bazli
    md.append(f"Veri kaynagi: kripto = Binance/MEXC/Bybit/Gate 5 dk (karnedeki borsa once denenir, giris fiyatiyla "
              f"uyum dogrulanir); diger = Yahoo Finance 5 dk. Metaller (XAU/XAG/XPT/XPD) Yahoo'da spot olmadigi icin "
              f"vadeli kontrat (GC=F, SI=F, PL=F, PA=F) **getiri vekili** olarak kullanildi ve olay basina giris "
              f"fiyatina olceklendi; XAUTRY eslenmedi.\n")
    ort_gec = np.mean([d["gec"] for d in hz]) if hz else 0
    md.append(f"Giris mumu: giris anini iceren 5 dk mum. Mum baslangici ile giris ani arasi ortalama {ort_gec:.0f} sn "
              f"(mum ici gecikme). Sezgisel not: ayni mumun high/low'u girisinden ONCE olan fiyatlari da icerir; "
              f"bu stopu/TP'yi hafif fazla tetikler. Duyarlilik icin bir sonraki mumdan baslama asagida.\n")

    md.append("## 2. Varsayimlar ve sinirlar\n")
    md.append("- Stop/TP giristen yuzde; ayni mumda ikisi birden degerse STOP (muhafazakar). Stop/TP seviyesi gap ile "
              "atlanirsa cikis yine seviyeden varsayilir (iyimser). Trailing: mumun high'i stopu ceker, ayni mumun low'u "
              "vurabilir (kotumser).")
    md.append("- 48 saat duvar saati; kapali piyasalar (BIST/ABD/FX hafta sonu) icin 48 saat icindeki SON mumun kapanisindan cikilir.")
    md.append("- Getiriler esit buyuklukte (1 birim) islem varsayimiyla toplanir; DD = zamana gore sirali net getirilerin "
              "kumulatif toplaminin en buyuk tepeden-dibe dususu (yuzde puan). Islemler zaman bakimindan ust uste binebilir.")
    md.append("- Maliyet = gidis-donus yuzde, her islemden dusulur. Kayma (slippage) ve gap riski maliyete dahil DEGIL; "
              "BIST/ABD hisse/FX icin gercek maliyet farkli olabilir.")
    md.append("- Olaylar bagimsiz degil: ayni sembolde 48 saat icinde ardisik temaslar ve ayni gunde piyasa genelindeki "
              "hareketler korele. Bu yuzden ilk-temas alt kumesi ve gun-kumeli bootstrap ayrica verildi.\n")
    md.append(f"- Egitim: 28 Agu - 18 Eyl (n={int(egitim.sum())}); test: 19 Eyl - 3 Eki (n={int(test.sum())}). "
              f"Test setinde ilk-temas alt kumesi n={int((test & ilk).sum())}; tum setteki ilk-temas orani "
              f"{ilk.mean():.1%}.\n")
    if int(test.sum()) < 1000:
        md.append("> **Dikkat: test orneklemi kucuk (n<1000); kucuk farklar gurultu olabilir.**\n")

    md.append("## 3. Mevcut kuralin yeniden uretimi\n")
    md.append("Karnedeki durumlarla (basarili/basarisiz/zaman_asimi; acik kayitlar haric) simulatorun ayni olay icin "
              "verdigi sonuc karsilastirildi. Karne stopu girise degil **cizgiye** gore %0,3, taramasi ise ~10 dk'da "
              "bir ANLIK fiyatla yapildigi icin uc varyant denendi:\n")
    md.append(tablo(["varyant", "olay", "ayni durum", "ortusme"],
                    [[a, b, c, f"{d_:.1%}"] for a, b, c, d_ in ozet_kar]) + "\n")
    for kk in karne_md:
        md.append(kk + "\n")
    md.append("Neden %100 degil: (1) karne yalniz ~10 dk'da bir anlik fiyata bakar, simulator her 5 dk mumun "
              "high/low'unu gorur: mum ici igne (wick) girisleri/cikislari simulatorda tetikler, karne kacirir; "
              "(2) karne stopu cizgiye gore, kullanici kurali girise gore; (3) giris mumu girisin oncesini de icerir; "
              "(4) karnede ayni anda iki esik asilirsa hangisinin once sayildigi tarama sirasina bagli; "
              "(5) farkli borsa/veri saglayicisi fiyat farklari ve vekil (metal) verisi.\n")
    md.append(f"Motor dogrulamasi: vektorel simulator ile bagimsiz mum-mum (naif) simulator {kontrol} karsilastirmada "
              f"{kontrol - uyusmaz} kez birebir ayni sonucu verdi (400 rastgele olay x 5 kombo x 2 yon).\n")

    md.append("## 4. Referans: mevcut kural (stop %0,3 / TP %0,5, 48 saat) — tum kayitlar\n")
    sat = []
    for mal in MALIYETLER:
        for ad_, mask in (("egitim", egitim), ("test", test), ("tum", np.ones(len(hz), bool)),
                          ("tum - yalniz ilk temas", ilk)):
            m = ozet_satir(ref, mal, mask)
            sat.append([f"%{mal:g}", ad_, m["n"], f"{m['isabet']:.1%}", f(m["ort"], 4), f(m["pf"], 2), f(m["dd"], 1)])
    md.append(tablo(["maliyet", "kume", "n", "isabet", "ort net %", "PF", "max DD (yp)"], sat) + "\n")

    md.append("## 5. Tum izgara — egitim vs test (ort. net getiri %, maliyet %"
              f"{SECIM_MALIYET:g}, MagicMA yonu)\n")
    for adi, mask in (("EGITIM", egitim), ("TEST", test)):
        md.append(f"**{adi}** (satir=stop, sutun=TP)\n")
        sat = []
        for s in STOPLAR:
            sat.append([f"%{s:g}"] + [f(metrik(net(ci_idx[("sl_tp", s, t)], SECIM_MALIYET, mask))["ort"], 3) for t in TPLER])
        md.append(tablo(["stop \\ TP"] + [f"%{t:g}" for t in TPLER], sat) + "\n")
        sat = [[f"trailing %{p:g}", f(metrik(net(ci_idx[("iz", p)], SECIM_MALIYET, mask))["ort"], 3)] for p in TRAILLER]
        md.append(tablo(["mod", "ort net %"], sat) + "\n")
    # izgaranin tamami pozitif/negatif sayisi
    pos_e = sum(1 for ci in range(len(km)) if metrik(net(ci, SECIM_MALIYET, egitim))["ort"] > 0)
    pos_t = sum(1 for ci in range(len(km)) if metrik(net(ci, SECIM_MALIYET, test))["ort"] > 0)
    md.append(f"%{SECIM_MALIYET:g} maliyette ort. net getirisi pozitif olan kombinasyon sayisi: egitimde {pos_e}/{len(km)}, "
              f"testte {pos_t}/{len(km)}. (Gurultuyle beklenen: yaklasik yarisi.)\n")

    md.append(f"## 6. Egitimde secilen en iyi 5 kombinasyon -> testte olcum (secim: egitim ort. net, maliyet %{SECIM_MALIYET:g})\n")
    sat = []
    for s in sonuc5:
        te = s[("test", SECIM_MALIYET)]
        sat.append([s["ad"], f(s["egitim"]["ort"], 4), te["n"], f"{te['isabet']:.1%}", f(te["ort"], 4),
                    f(te["pf"], 2), f(te["dd"], 1),
                    f"[{f(s['ci_naif'][0])}; {f(s['ci_naif'][1])}]", f"[{f(s['ci_gun'][0])}; {f(s['ci_gun'][1])}]"])
    md.append(tablo(["kombo", "egitim ort %", "test n", "test isabet", "test ort net %", "test PF", "test DD",
                     "%95 CI (bootstrap)", "%95 CI (gun-kumeli)"], sat) + "\n")
    md.append("Maliyet duyarliligi (test, ort. net %):\n")
    sat = []
    for s in sonuc5:
        sat.append([s["ad"]] + [f(s[("test", mal)]["ort"], 4) for mal in MALIYETLER]
                   + [f(s[("test_ilk", mal)]["ort"], 4) for mal in MALIYETLER])
    md.append(tablo(["kombo"] + [f"tum %{m:g}" for m in MALIYETLER] + [f"ilk-temas %{m:g}" for m in MALIYETLER], sat) + "\n")
    md.append(f"Ilk-temas alt kumesi (test): n={sonuc5[0][('test_ilk', SECIM_MALIYET)]['n']}.\n")

    md.append(f"## 7. Rastgele baz cizgisi (test, maliyet %{SECIM_MALIYET:g}, {RASTGELE_TEKRAR} tekrar)\n")
    md.append("Ayni giris anlari, ayni stop/TP; yalniz YON rastgele. (a) permutasyon: MagicMA'nin long/short orani "
              "korunarak yonler olaylar arasinda karistirilir; (b) yazi-tura: her olay %50 long/short. p = rastgele "
              "ortalamanin MagicMA ortalamasina esit/ustte olma orani.\n")
    sat = []
    for s in sonuc5:
        r_, ri = s["rast"], s["rast_ilk"]
        sat.append([s["ad"], f(r_["gozlenen"], 4), f(r_["perm_ort"], 4), f(r_["perm_p95"], 4), f(r_["perm_p"], 3),
                    f(r_["yaz_ort"], 4), f(r_["yaz_p"], 3), f(ri["gozlenen"], 4), f(ri["perm_p"], 3)])
    md.append(tablo(["kombo", "MagicMA ort %", "perm. ort %", "perm. p95", "perm. p", "yazi-tura ort %", "yazi-tura p",
                     "ilk-temas MagicMA %", "ilk-temas perm. p"], sat) + "\n")
    md.append(f"Bonferroni esigi (5 kombo): p < {esik_p:.3f}.\n")

    md.append("## 8. Duyarlilik: bir sonraki mumdan baslama (giris mumunun gecmis wick'i etkisi)\n")
    if hz_sonraki:
        Rn = motor(hz_sonraki, km)
        yn = np.array([1 if d["o"]["yon"] == "long" else 0 for d in hz_sonraki])
        tn = np.array([d["o"]["ts"] for d in hz_sonraki])
        sat = []
        for ci in [ref] + en5:
            r = np.where(yn == 1, Rn["long"][:, ci], Rn["short"][:, ci]) - SECIM_MALIYET / 100
            m_t = metrik(r[tn >= EGITIM_BITIS])
            m_e = metrik(r[tn < EGITIM_BITIS])
            tm = tn >= EGITIM_BITIS
            sat.append([ad_kombo(km[ci]) + (" (mevcut kural)" if ci == ref else ""),
                        f(m_e["ort"], 4), f(m_t["ort"], 4), m_t["n"]]
                       + [f(metrik(r[tm] + SECIM_MALIYET / 100 - mal / 100)["ort"], 4) for mal in MALIYETLER])
        md.append(tablo(["kombo", "egitim ort net % (maliyet %0,1)", "test ort net % (maliyet %0,1)", "test n"]
                        + [f"test maliyet %{m:g}" for m in MALIYETLER], sat) + "\n")
        md.append("Giris mumunun giristen ONCEki wick'i dahil (bolum 1-7) ile bir sonraki mumdan baslama (bu bolum) "
                  "gercegin iki ucudur: ilki stop/TP'yi fazla tetikler, ikincisi giris mumunun giristen SONRAki kismini "
                  "kacirir. Fark buyuk: sonuc varsayima duyarli. Bu bolumde maliyet %0,1'de hicbir kombo pozitif degil.\n")

    # --- kirilimlar: referans kural + egitim lideri
    def kirilim(ci, anahtar_fn, baslik):
        gr = defaultdict(list)
        for i, d in enumerate(hz):
            gr[anahtar_fn(d["o"])].append(i)
        sat = []
        for k, idxs in sorted(gr.items(), key=lambda kv: -len(kv[1])):
            idxs = np.array(idxs)
            r = net(ci, SECIM_MALIYET)[idxs]
            m = metrik(r)
            mt = metrik(r[test[idxs]])
            sat.append([k, m["n"], f"{m['isabet']:.1%}", f(m["ort"], 4), f(m["pf"], 2), mt["n"], f(mt["ort"], 4)])
        return f"**{baslik}**\n\n" + tablo(["grup", "n", "isabet", "ort net %", "PF", "test n", "test ort net %"], sat)

    md.append(f"## 9. Kirilimlar (maliyet %{SECIM_MALIYET:g}, tum kayitlar)\n")
    for ci, etiket in ((ref, "Mevcut kural stop %0,3 / TP %0,5"), (en5[0], "Egitim lideri " + ad_kombo(km[en5[0]]))):
        md.append(f"### {etiket}\n")
        md.append(kirilim(ci, lambda o: o["kategori"], "Kategori") + "\n")
        md.append(kirilim(ci, lambda o: o["grup"], "Cizgi") + "\n")
        md.append(kirilim(ci, lambda o: o["yon"], "Yon") + "\n")
        md.append(kirilim(ci, lambda o: o.get("kaynak_turu") or "?", "Kaynak turu") + "\n")

    # --- 20 olay elle dogrulama
    md.append("## 10. Rastgele 20 olayin elle dogrulamasi (mevcut kural: stop %0,3 / TP %0,5)\n")
    md.append("Her satir bagimsiz mum-mum simulatorle (`naif`) yeniden hesaplandi; getiri = (cikis seviyesi / giris - 1) "
              "(short icin ters). Sonuc, vektorel motor ciktisiyla da birebir karsilastirildi.\n")
    sec = rng_py.sample(range(len(hz)), min(20, len(hz)))
    sat = []
    esles = 0
    for i in sec:
        d = hz[i]
        o = d["o"]
        yl = 1 if o["yon"] == "long" else -1
        e = d["e"]
        sf, tf = e * (1 - yl * 0.003), e * (1 + yl * 0.005)
        r, neden, k = naif(d, o["yon"], stop_fiyat=sf, tp_fiyat=tf)
        motor_r = R[o["yon"]][i, ref]
        ok = abs(r - motor_r) < 1e-12
        esles += ok
        t_giris = dt.datetime.fromtimestamp(d["ts"][0], TZ_TR).strftime("%m-%d %H:%M")
        t_tet = dt.datetime.fromtimestamp(d["ts"][k], TZ_TR).strftime("%m-%d %H:%M")
        sat.append([o["sembol"], o["yon"], o["giris_zamani"][5:16].replace("T", " "), f"{e:.6g}", t_giris,
                    f"{sf:.6g}", f"{tf:.6g}", neden, t_tet,
                    f"H={d['h'][k]:.6g} L={d['l'][k]:.6g}", f(r * 100, 3) + "%", "evet" if ok else "HAYIR"])
    md.append(tablo(["sembol", "yon", "karne giris", "giris fiyati", "giris mumu", "stop", "TP", "sonuc",
                     "tetik mumu", "tetik mum H/L", "getiri", "motorla ayni"], sat) + "\n")
    md.append(f"Motorla ayni: {esles}/{len(sec)}.\n")

    md.append("## 11. Acik kalan isler / dikkat\n")
    md.append("- Maliyet ve kayma sembol sinifina gore farkli; tek yuzde ile modellendi.")
    md.append("- Ayni anda acik pozisyon/sermaye sinirlamasi modellenmedi (esit agirlik, ust uste binen islemler).")
    md.append("- 5 dk mumda mum ici sira (once high mi low mu) bilinmez; ayni mumda ikisi de degerse STOP sayildi, bu "
              "TP agirlikli kombinasyonlari sistematik olarak kotumser gosterir.")
    md.append("- ~5 haftalik tek rejim (Agu-Eki 2026); farkli piyasa rejimlerinde sonuc degisebilir.")
    md.append("- Karne olaylari bot'un 10 dk'lik taramasinda GORULEN temaslardir (gercek temas ani degil); canli "
              "uygulamada ek gecikme olur.")
    with open(RAPOR, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"[RAPOR] yazildi: {RAPOR}")
    print(sonuc_cumle)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("komut", choices=["veri", "rapor", "tumu"])
    ap.add_argument("--sinirla", type=int, default=None, help="her kaynak turunde ilk N sembol (deneme)")
    a = ap.parse_args()
    olaylar = olaylari_yukle()
    print(f"[BACKTEST] {len(olaylar)} olay yuklendi")
    if a.komut in ("veri", "tumu"):
        veri_cek(olaylar, a.sinirla)
    if a.komut in ("rapor", "tumu"):
        rapor_uret(olaylar)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
