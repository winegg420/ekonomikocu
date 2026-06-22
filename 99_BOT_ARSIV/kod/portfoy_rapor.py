#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portfoy-farkindali uyari/rapor motoru.

Her pozisyon icin:
  - canli fiyat (kripto: Binance REST; diger/basarisiz: magicma_ham.jsonl son tarama fiyati)
  - kar/zarar % (giris vs canli)
  - en yakin KOC seviyesi (grafik_seviyeleri.jsonl + cagrilar.jsonl)
  - en yakin MAGICMA cizgisi (magicma_ham.jsonl, sembol basina en yuksek ts)
  - UYARI: bir Koc seviyesine VEYA MagicMA cizgisine <= %YAKIN_ESIK yaklasinca,
    ya da kar/zarar esigi gecince
  - yon: fiyat cizgi/seviye ALTINDA = DIRENC, USTUNDE = DESTEK

Cikti markdown; UYARILAR en uste; uzun-vade ve taktik AYRI bolum.
Portfoy verisi BOSSA hata vermez, "veri yok" der.

Kullanim:
  python portfoy_rapor.py                      # portfoy_ozel.json (gercek, gitignore'lu)
  python portfoy_rapor.py --file portfoy_ornek.json   # ornek/test
  python portfoy_rapor.py --out rapor.md       # ayrica dosyaya yaz
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

# ============================ KONFIG (esikler) ============================
YAKIN_ESIK_YUZDE = 0.5     # bir seviye/cizgiye bu kadar veya daha yakinsa UYARI
KAR_ESIK_YUZDE = 20.0      # bu kar%'inda UYARI (kar al degerlendir)
ZARAR_ESIK_YUZDE = -10.0   # bu zarar%'inda UYARI (stop/gozden gecir)
FETCH_TIMEOUT = 6          # saniye

# Sembol normalizasyonu: kuyruk ekleri ve takma adlar.
# NOT: ".D" (orn. BTC.D = dominance) AYRI enstrumandir, soyulmaz — yoksa BTC ile cakisir.
KUYRUK_EKLERI = ("USDT", "USD", "TRY", "PERP")
TAKMA_AD = {
    "GUMUS": "XAG", "SILVER": "XAG",
    "ALTIN": "XAU", "GOLD": "XAU",
    "PETROL": "OIL", "BRENT": "OIL",
}
# Binance icin kripto tabanlari (canli fiyat denenecek)
KRIPTO_TABANLARI = {
    "BTC", "ETH", "SOL", "AVAX", "ARB", "NEAR", "AAVE", "UNI", "CAKE",
    "CHZ", "ENS", "IMX", "RENDER", "TAO", "BERA", "XRP", "ADA", "DOGE",
}
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price?symbol={}"

KOD = Path(__file__).resolve().parent


def _root() -> Path:
    up = KOD.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file() or (up / "portfoy_ornek.json").is_file():
        return up
    return up


ROOT = _root()
MAGICMA = KOD / "magicma_ham.jsonl"
GRAFIK = ROOT / "grafik_seviyeleri.jsonl"
CAGRI = ROOT / "cagrilar.jsonl"


# ============================ Yardimcilar ============================
def safe_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        return []
    return out


def safe_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def normalize(sym: str) -> str:
    if not sym:
        return ""
    s = sym.strip().upper().replace("/", "")
    s = TAKMA_AD.get(s, s)
    for ek in KUYRUK_EKLERI:
        if s.endswith(ek) and len(s) > len(ek):
            s = s[: -len(ek)]
            break
    return TAKMA_AD.get(s, s)


def fmt(x, ond: int = 2) -> str:
    try:
        return f"{float(x):,.{ond}f}"
    except Exception:
        return str(x)


# ============================ Fiyat ============================
def fetch_binance(base: str):
    """Kripto icin canli fiyat. Hata olursa None (try-catch zorunlu)."""
    if base not in KRIPTO_TABANLARI:
        return None
    try:
        import urllib.request

        url = BINANCE_URL.format(base + "USDT")
        with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
        return float(data["price"])
    except Exception:
        return None


def magicma_son(sembol: str, magicma: list[dict]):
    """Sembol icin EN YUKSEK ts'li magicma kaydi (fiyat + cizgiler)."""
    base = normalize(sembol)
    best = None
    for k in magicma:
        if normalize(k.get("sembol", "")) != base:
            continue
        if best is None or (k.get("ts", "") > best.get("ts", "")):
            best = k
    return best


def fiyat_getir(sembol: str, magicma: list[dict]):
    """(fiyat, kaynak) dondur. Once canli kripto, sonra magicma son tarama, sonra None."""
    base = normalize(sembol)
    live = fetch_binance(base)
    if live is not None:
        return live, "Binance (canli)"
    mg = magicma_son(sembol, magicma)
    if mg and isinstance(mg.get("fiyat"), (int, float)):
        return float(mg["fiyat"]), f"MagicMA son tarama {mg.get('ts', '')[:16]}"
    return None, None


# ============================ Seviyeler ============================
def koc_seviyeleri(sembol: str, grafik: list[dict], cagri: list[dict]) -> list[tuple[float, str]]:
    """Koc seviyeleri: (deger, kaynak). grafik_seviyeleri + cagrilar."""
    base = normalize(sembol)
    out: list[tuple[float, str]] = []
    for g in grafik:
        if normalize(g.get("urun", "")) != base:
            continue
        for s in g.get("okunan_seviyeler", []) or []:
            try:
                v = float(s)
                if v > 0:
                    out.append((v, f"grafik {g.get('tweet_id', '')}"))
            except Exception:
                continue
    for c in cagri:
        urunler = c.get("urun") or []
        if not any(normalize(u) == base for u in urunler):
            continue
        for s in c.get("seviyeler", []) or []:
            try:
                v = float(s)
                if v > 0:
                    out.append((v, f"cagri {c.get('tarih', '')}"))
            except Exception:
                continue
    return out


def magicma_cizgileri(sembol: str, magicma: list[dict]) -> list[tuple[float, str]]:
    mg = magicma_son(sembol, magicma)
    if not mg:
        return []
    out: list[tuple[float, str]] = []
    for s in mg.get("seviyeler", []) or []:
        try:
            out.append((float(s["deger"]), s.get("ad", "MagicMA")))
        except Exception:
            continue
    return out


def en_yakin(fiyat: float, items: list[tuple[float, str]]):
    """(deger, ad, mesafe_yuzde) — mesafe = (fiyat-deger)/deger*100.
    poz = fiyat seviyenin USTUNDE (seviye DESTEK); neg = ALTINDA (seviye DIRENC)."""
    best = None
    for deger, ad in items:
        if deger <= 0:
            continue
        mes = (fiyat - deger) / deger * 100.0
        if best is None or abs(mes) < abs(best[2]):
            best = (deger, ad, mes)
    return best


def yon_etiket(mesafe: float) -> str:
    return "DESTEK (long tarafi)" if mesafe >= 0 else "DIRENC (short tarafi)"


# ============================ Rapor ============================
def pozisyon_blok(pos: dict, magicma, grafik, cagri) -> tuple[list[str], list[str]]:
    """(satirlar, uyarilar) dondur."""
    sembol = pos.get("sembol", "")
    giris = pos.get("giris") or 0
    miktar = pos.get("miktar") or 0
    uyarilar: list[str] = []
    satir: list[str] = []

    fiyat, kaynak = fiyat_getir(sembol, magicma)
    if fiyat is None:
        satir.append(f"### {sembol}  —  fiyat alinamadi")
        satir.append(f"- giris: {fmt(giris)} | miktar: {fmt(miktar)} | not: {pos.get('not', '')}")
        satir.append("- canli/yedek fiyat bulunamadi (kripto degil veya veri yok).")
        return satir, uyarilar

    pnl = None
    if giris and float(giris) > 0:
        pnl = (fiyat - float(giris)) / float(giris) * 100.0

    satir.append(f"### {sembol}  —  {fmt(fiyat)}  ({kaynak})")
    pnl_str = f"{pnl:+.2f}%" if pnl is not None else "—"
    satir.append(
        f"- giris: {fmt(giris)} | miktar: {fmt(miktar)} | **kar/zarar: {pnl_str}** | not: {pos.get('not', '')}"
    )

    yk = en_yakin(fiyat, koc_seviyeleri(sembol, grafik, cagri))
    if yk:
        deger, ad, mes = yk
        satir.append(f"- en yakin KOÇ seviyesi: {fmt(deger)} ({ad}) | mesafe {mes:+.2f}% | {yon_etiket(mes)}")
        if abs(mes) <= YAKIN_ESIK_YUZDE:
            uyarilar.append(f"🔔 {sembol}: KOÇ seviyesi {fmt(deger)}'e %{abs(mes):.2f} yakin — {yon_etiket(mes)}")
    else:
        satir.append("- en yakin KOÇ seviyesi: (kayit yok)")

    ym = en_yakin(fiyat, magicma_cizgileri(sembol, magicma))
    if ym:
        deger, ad, mes = ym
        satir.append(f"- en yakin MAGICMA çizgisi: {fmt(deger)} ({ad}) | mesafe {mes:+.2f}% | {yon_etiket(mes)}")
        if abs(mes) <= YAKIN_ESIK_YUZDE:
            uyarilar.append(f"🔔 {sembol}: MAGICMA {ad} {fmt(deger)}'e %{abs(mes):.2f} yakin — {yon_etiket(mes)}")
    else:
        satir.append("- en yakin MAGICMA çizgisi: (kayit yok)")

    if pnl is not None:
        if pnl >= KAR_ESIK_YUZDE:
            uyarilar.append(f"🟢 {sembol}: kar %{pnl:.1f} — kar-al esigi ({KAR_ESIK_YUZDE}%) gecildi")
        elif pnl <= ZARAR_ESIK_YUZDE:
            uyarilar.append(f"🔴 {sembol}: zarar %{pnl:.1f} — zarar esigi ({ZARAR_ESIK_YUZDE}%) gecildi")

    satir.append("")
    return satir, uyarilar


def build_report(portfoy: dict) -> str:
    pozlar = [p for p in (portfoy.get("pozisyonlar") or []) if (p.get("sembol") or "").strip()]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not pozlar:
        return (
            f"# Portföy Raporu — {now}\n\n"
            "Portföy boş — veri yok. `portfoy_ozel.json` doldurulunca rapor üretilecek.\n"
        )

    magicma = safe_jsonl(MAGICMA)
    grafik = safe_jsonl(GRAFIK)
    cagri = safe_jsonl(CAGRI)

    uzun_satir: list[str] = []
    taktik_satir: list[str] = []
    tum_uyari: list[str] = []
    for p in pozlar:
        satir, uyari = pozisyon_blok(p, magicma, grafik, cagri)
        tum_uyari.extend(uyari)
        if (p.get("tip") or "").startswith("uzun"):
            uzun_satir.extend(satir)
        else:
            taktik_satir.extend(satir)

    out = [f"# Portföy Raporu — {now}", ""]
    out.append("## ⚠️ UYARILAR")
    if tum_uyari:
        out.extend(f"- {u}" for u in tum_uyari)
    else:
        out.append("- Tetiklenen uyarı yok (eşiklere yaklaşan seviye/çizgi veya kar/zarar yok).")
    out.append("")
    out.append(f"_Eşikler: yakınlık ≤%{YAKIN_ESIK_YUZDE} · kar ≥%{KAR_ESIK_YUZDE} · zarar ≤%{ZARAR_ESIK_YUZDE}_")
    out.append("")
    out.append("## 📌 Uzun-vade")
    out.extend(uzun_satir or ["(pozisyon yok)", ""])
    out.append("## ⚡ Taktik")
    out.extend(taktik_satir or ["(pozisyon yok)", ""])
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Portfoy uyari/rapor motoru")
    ap.add_argument("--file", default="portfoy_ozel.json", help="Portfoy json (vars. portfoy_ozel.json)")
    ap.add_argument("--out", default=None, help="Raporu bu dosyaya da yaz (opsiyonel)")
    args = ap.parse_args()

    path = (ROOT / args.file) if not Path(args.file).is_absolute() else Path(args.file)
    portfoy = safe_json(path)
    rapor = build_report(portfoy)
    print(rapor)
    if args.out:
        try:
            outp = (ROOT / args.out) if not Path(args.out).is_absolute() else Path(args.out)
            outp.write_text(rapor, encoding="utf-8")
            print(f"\n[yazildi: {outp}]")
        except Exception as e:
            print(f"\n[uyari: cikti yazilamadi: {e}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
