#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Binance 24s hacme gore TOP-100 USDT paritesini cek, kripto.txt'e yaz.

- Stablecoin pariteleri ve kaldiracli token'lar (UP/DOWN/BULL/BEAR) elenir.
- MANUEL_SABIT tabanlar top-100'e girmese de her zaman listede kalir; Binance'te
  paritesi yoksa Bybit/MEXC'e otomatik remap edilir.
- CRYPTOCAP:TOTAL ve CRYPTOCAP:BTC.D her zaman basta tutulur (kripto evreni makro).
- Tum ag cagrilari try-catch; basarisizsa mevcut kripto.txt'e DOKUNMAZ (bozma).
- Periyodik calistirilabilir: python kripto_liste_guncelle.py
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

KOD = Path(__file__).resolve().parent
REPO = KOD.parent.parent
LISTE_DIR = REPO / "magicma" / "sembol_listesi"
KRIPTO_TXT = LISTE_DIR / "kripto.txt"

TOP_N = 100
BINANCE_24H = "https://api.binance.com/api/v3/ticker/24hr"
BYBIT_TICKER = "https://api.bybit.com/v5/market/tickers?category=spot&symbol={b}USDT"
MEXC_TICKER = "https://api.mexc.com/api/v3/ticker/price?symbol={b}USDT"

# Parite olarak istemedigimiz tabanlar (stablecoin) ve kaldiracli kuyruklar
STABLE = {"USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDP", "UST", "EUR", "TRY", "GBP",
          "AEUR", "USD1", "USDE", "PYUSD", "USDD", "FRAX", "GUSD", "USDS",
          "RLUSD", "BFUSD", "XUSD", "USDR", "USDX"}
KALDIRAC = ("UP", "DOWN", "BULL", "BEAR")
# Binance tokenlestirilmis hisseler / on-piyasa (kripto degil; exchangeInfo'da normal
# SPOT gorundugu icin bayrakla ayrilamaz). Yeni cikanlar burada elle eklenebilir.
HARIC_BASE = {"SPCXB", "SNDKB", "CRCLB", "FIGRB", "MSTRB", "COINB", "NVDAB", "OPENB"}
# Hicbir borsada "Dogu Block" MagicMA seviyesi uretmeyen (kisa gecmisli) tabanlar;
# hacim top-100'e girse de taramada bos dondukleri icin haric tutulur (2026-07-08).
# Veri olgunlasinca bu setten cikarilabilir.
MAGICMA_YOK = {"RE", "TON", "UTK", "OPG", "MUB", "CHIP"}
MAKRO_BASLIK = ["CRYPTOCAP:TOTAL", "CRYPTOCAP:BTC.D"]

# Ida'nin portfoy tabanlari (CoinGecko, 2026-08-23): hacim top-100'e girmese de
# listede HER ZAMAN kalir. Binance'te USDT paritesi yoksa Bybit -> MEXC sirasiyla
# aranir, bulunan borsa calisma aninda REMAP'e eklenir; hicbirinde yoksa atlanir.
MANUEL_SABIT = ("NST", "ENS", "CAKE", "CRV", "IMX", "NOS", "ATOM", "SSTR", "STRK", "ZK",
                "POPCAT", "MOCA", "GRASS", "AKT", "MINA", "DYDX", "PIXEL", "GME",
                "AIDOGE", "XTZ")

# Binance'te kisa gecmis nedeniyle "Dogu Block" MagicMA seviye plotlari bos (∅) donen,
# ayni varligin daha uzun gecmisli oldugu borsaya yonlendirilen semboller (2026-07-08
# ampirik test). BINANCE:X hacim listesine girse de burada yeniden yazilir.
REMAP = {
    "BINANCE:MEGAUSDT": "MEXC:MEGAUSDT",
    "BINANCE:XAUTUSDT": "BYBIT:XAUTUSDT",
    "BINANCE:LRCUSDT":  "BYBIT:LRCUSDT",
}


def fetch_top_usdt(n: int = TOP_N, tum_bazlar: set[str] | None = None) -> list[str]:
    """Binance'tan 24s quoteVolume'a gore top-n USDT tabanini dondur (ham taban kodu).

    tum_bazlar verilirse, filtrelerden bagimsiz olarak Binance'teki TUM USDT
    tabanlari bu sete yazilir (MANUEL_SABIT parite kontrolu icin; ek API cagrisi yok).
    """
    req = urllib.request.Request(BINANCE_24H, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    adaylar = []
    for d in data:
        sym = d.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        base = sym[: -len("USDT")]
        if tum_bazlar is not None and base:
            tum_bazlar.add(base)
        if base in STABLE or base in HARIC_BASE or base in MAGICMA_YOK or not base:
            continue
        # Sadece duz ASCII harf/rakam tabanlari (cince meme token'lar vs. elenir)
        if not (base.isascii() and base.isalnum() and any(c.isalpha() for c in base)):
            continue
        if any(base.endswith(k) for k in KALDIRAC):
            continue
        try:
            qv = float(d.get("quoteVolume", 0))
        except Exception:
            qv = 0.0
        adaylar.append((qv, base))
    adaylar.sort(reverse=True)
    return [b for _, b in adaylar[:n]]


def _json_cek(url: str) -> dict | None:
    """Tek JSON GET; her turlu hata None doner (script kirilmasin)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def borsa_bul(base: str, binance_bazlar: set[str]) -> str | None:
    """Manuel sabit taban icin USDT paritesinin bulundugu ilk borsayi dondur.

    Sira: BINANCE (zaten cekilmis 24h verisinden) -> BYBIT -> MEXC. Yoksa None.
    """
    if base in binance_bazlar:
        return "BINANCE"
    d = _json_cek(BYBIT_TICKER.format(b=base))
    if d and d.get("retCode") == 0 and (d.get("result") or {}).get("list"):
        return "BYBIT"
    d = _json_cek(MEXC_TICKER.format(b=base))
    if d and d.get("symbol") and d.get("price"):
        return "MEXC"
    return None


def main() -> int:
    binance_bazlar: set[str] = set()
    try:
        bazlar = fetch_top_usdt(TOP_N, binance_bazlar)
    except Exception as e:
        print(f"Binance cekilemedi ({e}). kripto.txt KORUNDU (degistirilmedi).")
        return 1
    if not bazlar:
        print("Bos sonuc — kripto.txt KORUNDU.")
        return 1

    # Manuel sabit portfoy tabanlari: top-100'de yoksa sona eklenir; Binance'te
    # paritesi yoksa Bybit/MEXC'e remap edilir, hicbirinde yoksa atlanir.
    mevcut = set(bazlar)
    eklenen, bulunamayan = [], []
    for b in MANUEL_SABIT:
        if b in mevcut:
            continue
        try:
            borsa = borsa_bul(b, binance_bazlar)
        except Exception as e:
            print(f"  ! {b}: borsa kontrolu basarisiz ({e}) — atlandi.")
            bulunamayan.append(b)
            continue
        if borsa is None:
            bulunamayan.append(b)
            continue
        if borsa != "BINANCE":
            REMAP[f"BINANCE:{b}USDT"] = f"{borsa}:{b}USDT"
        bazlar.append(b)
        mevcut.add(b)
        eklenen.append(f"{b}({borsa})")

    LISTE_DIR.mkdir(parents=True, exist_ok=True)
    satirlar = ["# Kripto evreni — Binance 24s hacim TOP-100 + manuel sabit portfoy",
                "#   (kripto_liste_guncelle.py uretir)",
                "# CRYPTOCAP makro basliklari el ile sabit; gerisi otomatik."]
    satirlar += MAKRO_BASLIK
    satirlar += [REMAP.get(f"BINANCE:{b}USDT", f"BINANCE:{b}USDT") for b in bazlar]
    KRIPTO_TXT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print(f"kripto.txt yazildi: {len(bazlar)} USDT paritesi + {len(MAKRO_BASLIK)} makro -> {KRIPTO_TXT}")
    if eklenen:
        print(f"Manuel sabit eklendi ({len(eklenen)}): " + ", ".join(eklenen))
    if bulunamayan:
        print("Manuel sabit — hicbir borsada (Binance/Bybit/MEXC) USDT paritesi yok, "
              "atlandi: " + ", ".join(bulunamayan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
