#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gunun hareketli coinlerini cryptobubbles.net'ten cek, gunun_hareketlileri.txt'e yaz.

- Kaynak: https://cryptobubbles.net/backend/data/bubbles1000.usd.json (public GET).
- Filtre: stablecoin atlanir, performance.day yoksa atlanir, |day| < %5 atlanir.
- Sembol: `symbols` objesinde BORSA_SIRA onceligiyle ilk bulunan borsanin USDT
  paritesi normalize edilip TradingView formatina cevrilir (BINANCE:BTCUSDT).
  Hicbir borsada USDT paritesi yoksa coin atlanir (log'a yazilir).
- Dosya HER CALISTIRMADA komple uzerine yazilir (biriktirme yok; dun firlayan coin
  bugun sakinlesmis olabilir).
- Ag/parse hatasinda mevcut gunun_hareketlileri.txt'e DOKUNULMAZ (bozma pattern'i).
- KARA LISTE: TradingView'de kalici olarak okunamayan semboller
  (magicma/okunamayan_kara_liste.json) listeye HIC YAZILMAZ. Bu script yalnizca
  borsanin REST API'sinde USDT paritesinin var oldugunu dogrular; TV'de MagicMA
  gostergesinin cizilip cizilmedigini bilemez. Kara liste o boslugu kapatir:
  tarama neyin olu oldugunu ogrenir, uretim de onu bir daha yazmaz. Yeniden
  deneme penceresi (7 gun) acilan semboller listeye YENIDEN eklenir.

KULLANIM NOTU: Bu script MagicMA taramasindan (magicma_tara_dayanikli.py) ONCE
calistirilmalidir; boylece o gunun hareketli coinleri ayni taramaya dahil olur.
Otomatik zincirleme yok — elle calistirilir:

    py -3 99_BOT_ARSIV/kod/gunun_hareketlileri_guncelle.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

KOD = Path(__file__).resolve().parent
if str(KOD) not in sys.path:
    sys.path.insert(0, str(KOD))
import magicma_kara_liste as kl
REPO = KOD.parent.parent
LISTE_DIR = REPO / "magicma" / "sembol_listesi"
CIKTI_TXT = LISTE_DIR / "gunun_hareketlileri.txt"

KAYNAK = "https://cryptobubbles.net/backend/data/bubbles1000.usd.json"
ESIK = 5.0  # |performance.day| >= %5
ZAMAN_ASIMI = 15

# Borsa onceligi: ilk bulunan kullanilir. Anahtarlar cryptobubbles `symbols` alani,
# degerler TradingView borsa on eki.
BORSA_SIRA = [
    ("binance", "BINANCE"),
    ("bybit", "BYBIT"),
    ("mexc", "MEXC"),
    ("gateio", "GATEIO"),
    ("okx", "OKX"),
    ("bitget", "BITGET"),
    ("kucoin", "KUCOIN"),
]


# TradingView'de otomatik secilen borsa veri vermeyen coinler icin ELLE dogrulanmis
# borsa. Kural: "TV'nin veri verdigi kod" — canli test edilmeden buraya satir eklenmez.
#   GRAM: 2026-08-23 taramasinda BINANCE:GRAMUSDT timeout verdi, MEXC:GRAMUSDT okundu.
ELLE_BORSA = {
    "GRAM": "mexc",
}

# Hicbir borsada USDT paritesi olmayan ama TV'de BASKA bir parite/borsa ile veri
# veren coinler icin TAM TradingView sembolu. BORSA_SIRA'dan da once denenir.
# Kural: ELLE_BORSA ile ayni — canli test edilmeden buraya satir eklenmez.
#   AERO: 2026-08-25 taramasinda BINANCE:AEROUSDT veri vermedi; COINBASE/MEXC/BYBIT/
#         GATEIO/OKX/KUCOIN USDT pariteleri de yok, COINBASE:AEROUSD okundu (0,54363).
ELLE_SEMBOL = {
    "AERO": "COINBASE:AEROUSD",
}


def veri_cek(url: str = KAYNAK) -> list | None:
    """Tek JSON GET; her turlu hata None doner (script kirilmasin)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=ZAMAN_ASIMI) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"CryptoBubbles cekilemedi ({e}).")
        return None
    if not isinstance(data, list) or not data:
        print("CryptoBubbles bos/beklenmeyen yanit dondu.")
        return None
    return data


def parite_normalize(ham: str) -> str | None:
    """'BTC_USDT' / 'btc-usdt' / 'BTC/USDT' -> 'BTCUSDT'. USDT degilse None."""
    if not isinstance(ham, str) or not ham:
        return None
    t = ham.upper().replace("_", "").replace("/", "").replace("-", "").strip()
    if not t.endswith("USDT") or len(t) <= len("USDT"):
        return None
    if not (t.isascii() and t.isalnum()):
        return None
    return t


def sembol_uret(coin: dict) -> tuple[str, str] | None:
    """Coin icin (TradingView sembolu, borsa adi) dondur; bulunamazsa None."""
    borsalar = coin.get("symbols") or {}
    if not isinstance(borsalar, dict):
        return None
    # Elle dogrulanmis TAM sembol varsa (USDT paritesi olmayan coinler) once o kullanilir.
    tam = ELLE_SEMBOL.get((coin.get("symbol") or "").upper())
    if tam:
        return tam, tam.split(":")[0]
    # Elle dogrulanmis borsa varsa once o denenir; paritesi yoksa normal siraya dusulur.
    zorla = ELLE_BORSA.get((coin.get("symbol") or "").upper())
    if zorla:
        t = parite_normalize(borsalar.get(zorla))
        if t:
            return f"{zorla.upper()}:{t}", zorla.upper()
    for anahtar, on_ek in BORSA_SIRA:
        t = parite_normalize(borsalar.get(anahtar))
        if t:
            return f"{on_ek}:{t}", on_ek
    return None


def main() -> int:
    data = veri_cek()
    if data is None:
        print(f"{CIKTI_TXT.name} KORUNDU (degistirilmedi).")
        return 1

    kara_liste = kl.yukle()
    aday, secilen, atlanan_parite, atlanan_kara = 0, [], [], []
    gorulen = set()
    for coin in data:
        if not isinstance(coin, dict):
            continue
        if coin.get("stable") is True:
            continue
        gun = (coin.get("performance") or {}).get("day")
        if gun is None:
            continue
        try:
            gun = float(gun)
        except (TypeError, ValueError):
            continue
        if abs(gun) < ESIK:
            continue
        aday += 1
        sonuc = sembol_uret(coin)
        if sonuc is None:
            atlanan_parite.append(coin.get("symbol") or coin.get("slug") or "?")
            continue
        sembol, borsa = sonuc
        if sembol in gorulen:
            continue
        atla, sebep = kl.atlanmali_mi(kara_liste, sembol)
        if atla:
            atlanan_kara.append(f"{sembol} ({sebep})")
            continue
        gorulen.add(sembol)
        secilen.append((sembol, borsa, gun))

    if not secilen:
        print(f"Esigi ({ESIK}%) gecen coin bulunamadi — {CIKTI_TXT.name} KORUNDU.")
        return 1

    # En hareketliden en sakine (mutlak degisim)
    secilen.sort(key=lambda x: abs(x[2]), reverse=True)

    damga = datetime.now().strftime("%Y-%m-%dT%H:%M")
    satirlar = [f"# Gunun hareketlileri (cryptobubbles.net, |day| >= %{ESIK:g}) — uretim: {damga}",
                "#   (gunun_hareketlileri_guncelle.py uretir — her calistirmada uzerine yazilir)"]
    satirlar += [s for s, _, _ in secilen]
    LISTE_DIR.mkdir(parents=True, exist_ok=True)
    CIKTI_TXT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")

    borsa_sayim: dict[str, int] = {}
    for _, b, _ in secilen:
        borsa_sayim[b] = borsa_sayim.get(b, 0) + 1
    dagilim = ", ".join(f"{b}={n}" for b, n in
                        sorted(borsa_sayim.items(), key=lambda kv: -kv[1]))
    print(f"{CIKTI_TXT.name} yazildi: {len(secilen)} sembol -> {CIKTI_TXT}")
    print(f"Taranan coin: {len(data)} | esigi gecen: {aday} | eklenen: {len(secilen)}")
    print(f"Borsa dagilimi: {dagilim}")
    if atlanan_kara:
        print(f"KARA LISTE nedeniyle yazilmadi ({len(atlanan_kara)}): "
              + ", ".join(atlanan_kara[:20])
              + (" ..." if len(atlanan_kara) > 20 else ""))
    print(f"Kara liste durumu: {kl.ozet_satiri(kara_liste)}")
    if atlanan_parite:
        print(f"USDT paritesi bulunamadi, atlandi ({len(atlanan_parite)}): "
              + ", ".join(atlanan_parite[:30])
              + (" ..." if len(atlanan_parite) > 30 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
