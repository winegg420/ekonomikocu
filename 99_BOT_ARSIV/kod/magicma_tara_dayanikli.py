# -*- coding: utf-8 -*-
"""MagicMA DAYANIKLI tarama (CDP 9222).

magicma_yakinlik.py --tara ile ayni isi yapar ama CDP baglantisi koptugunda
(socket.send / Connection closed) ASILI KALMAZ: baglantiyi kapatir, yeniden
baglanir ve o sembolden devam eder. Ayrica bugun zaten taranmis sembolleri
atlar -> kaldigi yerden surdurur (resume). Her cagri zaman asimli oldugundan
sonsuz takilma olmaz.

Kullanim:
    python magicma_tara_dayanikli.py           # kaldigi yerden devam
    python magicma_tara_dayanikli.py --bastan   # bugunku ilerlemeyi yok say, bastan

Onkosul: 9222 Chrome acik + giris yapili TradingView sekmesi (indikator yuklu).
"""
import sys, os, time, json, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_KOD_DIR = os.path.dirname(os.path.abspath(__file__))
if _KOD_DIR not in sys.path:
    sys.path.insert(0, _KOD_DIR)

import magicma_yakinlik as m  # __main__ guard sayesinde tarama tetiklenmez

try:
    from playwright.sync_api import sync_playwright
except Exception:
    print("Playwright kurulu degil.")
    sys.exit(1)

from urllib.parse import quote

CDP_URL = f"http://127.0.0.1:{m.PORT}"
BASTAN = "--bastan" in sys.argv
MAX_DENEME = 3           # sembol basina okuma denemesi
MAX_RECONNECT = 12       # Chrome kapaliysa yeniden baglanma denemesi


def bugun():
    return datetime.date.today().isoformat()


def taranmis_bugun():
    """Bugun ham jsonl'e yazilmis 'kaynak' (BINANCE:BTCUSDT gibi) kumesi."""
    s = set()
    if not os.path.exists(m.HAM_JSONL):
        return s
    g = bugun()
    with open(m.HAM_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                k = json.loads(line)
            except Exception:
                continue
            if k.get("ts", "").startswith(g) and k.get("kaynak"):
                s.add(k["kaynak"])
    return s


def yeni_baglanti():
    """Playwright baslat, CDP'ye baglan, TV sekmesini dondur. (p, b, tv)."""
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP_URL)
    pages = [pg for ctx in b.contexts for pg in ctx.pages]
    tv = next((pg for pg in pages if "tradingview.com" in (pg.url or "")), None)
    return p, b, tv


def kapat(p, b):
    try:
        if b:
            b.close()
    except Exception:
        pass
    try:
        if p:
            p.stop()
    except Exception:
        pass


def baglan_saglam():
    """TV sekmesi bulunana kadar (Chrome yeniden acilincaya kadar) dener."""
    for deneme in range(1, MAX_RECONNECT + 1):
        try:
            p, b, tv = yeni_baglanti()
            if tv is not None:
                return p, b, tv
            kapat(p, b)
            print(f"   TV sekmesi yok, bekleniyor... ({deneme}/{MAX_RECONNECT})", flush=True)
        except Exception as e:
            print(f"   CDP bagli degil ({str(e)[:40]}), bekleniyor... ({deneme}/{MAX_RECONNECT})", flush=True)
        time.sleep(5)
    return None, None, None


def url_ile_ac(tv, base, sym):
    tv.goto(f"{base}?symbol={quote(sym)}&interval={m.INTERVAL}",
            wait_until="domcontentloaded", timeout=45000)


def rapor_yaz(okunamadi):
    """Bugunku TUM ham kayitlardan (sembol basina en son) rapor .md uret."""
    g = bugun()
    son = {}
    with open(m.HAM_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                k = json.loads(line)
            except Exception:
                continue
            if k.get("ts", "").startswith(g):
                son[k["sembol"]] = k
    kayitlar = list(son.values())
    os.makedirs(m.RAPOR_DIR, exist_ok=True)
    yol = os.path.join(m.RAPOR_DIR, f"magicma_rapor_{g}.md")
    with open(yol, "w", encoding="utf-8") as f:
        f.write(m.rapor_md_uret(kayitlar, okunamadi))
    giren = sum(1 for k in kayitlar
                if any(abs(r["mesafe_yuzde"]) <= m.ESIK_IZLE for r in k["seviyeler"]))
    return yol, len(kayitlar), giren


def main():
    zaten = set() if BASTAN else taranmis_bugun()
    todo = [s for s in m.SEMBOLLER if s not in zaten]
    toplam = len(m.SEMBOLLER)
    print(f"Toplam {toplam} sembol. Bugun taranmis: {len(zaten)}. "
          f"Kalan: {len(todo)}.", flush=True)
    if not todo:
        yol, n, giren = rapor_yaz([])
        print(f"Hepsi bugun taranmis. Rapor: {yol} ({n} sembol, {giren} rapora girdi)")
        return

    p, b, tv = baglan_saglam()
    if tv is None:
        print("HATA: TradingView sekmesi bulunamadi. CHROME_X.bat calisip TV acik mi?")
        sys.exit(1)
    base = (tv.url or "").split("?")[0]
    taze = True  # yeni baglanti sonrasi ilk sembolu URL ile ac

    okunamadi, okunan = [], 0
    for i, sym in enumerate(todo, 1):
        ticker = sym.split(":")[-1].strip()
        print(f"[{i}/{len(todo)}] {sym} ...", flush=True)
        basari = False
        for deneme in range(1, MAX_DENEME + 1):
            try:
                if taze:
                    url_ile_ac(tv, base, sym)
                    taze = False
                else:
                    m.sembol_gecis(tv, sym)
                data = m.bekle_hesap(tv, ticker, timeout=12)
                if data is None:
                    url_ile_ac(tv, base, sym)
                    data = m.bekle_hesap(tv, ticker, timeout=10)
                if data is None:
                    print("   okunamadi (timeout / deger 0)", flush=True)
                    break  # veri sorunu, baglanti degil -> tekrar deneme
                kayit = m.data_to_kayit(data, sym)
                if kayit is None:
                    print("   okunamadi (fiyat yok)", flush=True)
                    break
                m.kaydet_ham(kayit)
                okunan += 1
                en = min((abs(r["mesafe_yuzde"]) for r in kayit["seviyeler"]), default=None)
                dur = f"en yakin {m.tr_goster(en,1)}%" if en is not None else "seviye yok"
                print(f"   OK {kayit['sembol']} {m.tr_goster(kayit['fiyat'])} ({dur})", flush=True)
                basari = True
                break
            except Exception as e:
                # Baglanti koptu / sayfa cokti -> yeniden baglan, ayni sembolu tekrar dene
                print(f"   ! baglanti/oturum hatasi ({str(e)[:60]}) -> yeniden baglaniliyor "
                      f"(deneme {deneme}/{MAX_DENEME})", flush=True)
                kapat(p, b)
                time.sleep(3)
                p, b, tv = baglan_saglam()
                if tv is None:
                    print("HATA: Chrome/TV geri gelmedi. Durdu.", flush=True)
                    yol, n, giren = rapor_yaz(okunamadi + [sym])
                    print(f"Kismi rapor: {yol} ({n} sembol)")
                    sys.exit(1)
                base = (tv.url or base).split("?")[0]
                taze = True
        if not basari:
            okunamadi.append(sym)

    yol, n, giren = rapor_yaz(okunamadi)
    print(f"\nBitti. Bu kosumda {okunan} okundu, {len(okunamadi)} okunamadi.")
    print(f"Rapor: {yol}  (bugun toplam {n} sembol, {giren} rapora girdi)")


if __name__ == "__main__":
    main()
