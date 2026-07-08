#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Binance 24s hacme gore TOP-100 USDT paritesini cek, kripto.txt'e yaz.

- Stablecoin pariteleri ve kaldiracli token'lar (UP/DOWN/BULL/BEAR) elenir.
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

# Binance'te kisa gecmis nedeniyle "Dogu Block" MagicMA seviye plotlari bos (∅) donen,
# ayni varligin daha uzun gecmisli oldugu borsaya yonlendirilen semboller (2026-07-08
# ampirik test). BINANCE:X hacim listesine girse de burada yeniden yazilir.
REMAP = {
    "BINANCE:MEGAUSDT": "MEXC:MEGAUSDT",
    "BINANCE:XAUTUSDT": "BYBIT:XAUTUSDT",
    "BINANCE:LRCUSDT":  "BYBIT:LRCUSDT",
}


def fetch_top_usdt(n: int = TOP_N) -> list[str]:
    """Binance'tan 24s quoteVolume'a gore top-n USDT tabanini dondur (ham taban kodu)."""
    req = urllib.request.Request(BINANCE_24H, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    adaylar = []
    for d in data:
        sym = d.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        base = sym[: -len("USDT")]
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


def main() -> int:
    try:
        bazlar = fetch_top_usdt(TOP_N)
    except Exception as e:
        print(f"Binance cekilemedi ({e}). kripto.txt KORUNDU (degistirilmedi).")
        return 1
    if not bazlar:
        print("Bos sonuc — kripto.txt KORUNDU.")
        return 1

    LISTE_DIR.mkdir(parents=True, exist_ok=True)
    satirlar = ["# Kripto evreni — Binance 24s hacim TOP-100 (kripto_liste_guncelle.py uretir)",
                "# CRYPTOCAP makro basliklari el ile sabit; gerisi otomatik."]
    satirlar += MAKRO_BASLIK
    satirlar += [REMAP.get(f"BINANCE:{b}USDT", f"BINANCE:{b}USDT") for b in bazlar]
    KRIPTO_TXT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print(f"kripto.txt yazildi: {len(bazlar)} USDT paritesi + {len(MAKRO_BASLIK)} makro -> {KRIPTO_TXT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
