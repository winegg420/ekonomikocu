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
import magicma_kara_liste as kl

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
# Kara liste esikleri tek yerde: magicma_kara_liste.py
#   KARA_LISTE_ESIK  = kac basarisiz taramadan sonra sembol denenmeden atlanir
#   YENIDEN_DENE_GUN = atlanan sembol kac gunde bir yeniden denenir
KARA_LISTE_ESIK = kl.KARA_LISTE_ESIK
YENIDEN_DENE_GUN = kl.YENIDEN_DENE_GUN


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


TARANAMAYAN_MD = os.path.join(m.RAPOR_DIR, "taranamayan_semboller.md")
_OTO_BAS = "<!-- KARA-LISTE-OTOMATIK: BASLANGIC -->"
_OTO_BIT = "<!-- KARA-LISTE-OTOMATIK: BITIS -->"


def _kara_liste_bolumu(kara_liste):
    o = kl.ozet(kara_liste)
    L = [_OTO_BAS,
         "",
         "## Kara liste (otomatik)",
         "",
         f"_Bu bolum `magicma_tara_dayanikli.py` tarafindan her taramada yeniden_",
         f"_yazilir — elle duzenleme burada KALICI DEGILDIR. Son guncelleme: {bugun()}._",
         "",
         f"**{kl.ozet_satiri(kara_liste)}**",
         "",
         f"- Denenmeden atlanan (esik {kl.KARA_LISTE_ESIK} basarisiz): "
         f"**{len(o['aktif'])}**",
         f"- Siradaki taramada yeniden denenecek ({kl.YENIDEN_DENE_GUN} gun doldu): "
         f"**{len(o['hemen_denenecek'])}**",
         f"- Izlemede (henuz esigin altinda, hala her taramada deneniyor): "
         f"**{len(o['izleniyor'])}**",
         ""]
    if kara_liste:
        L += ["| Sembol | Durum | Deneme | Ilk basarisiz | Son basarisiz |",
              "|---|---|---:|---|---|"]
        for sembol in sorted(kara_liste):
            kayit = kara_liste[sembol]
            atla, _ = kl.atlanmali_mi(kara_liste, sembol)
            if atla:
                durum = "atlaniyor"
            elif int(kayit.get("deneme_sayisi", 0)) >= kl.KARA_LISTE_ESIK:
                durum = "yeniden denenecek"
            else:
                durum = "izlemede"
            L.append(f"| {sembol} | {durum} | {kayit.get('deneme_sayisi', '?')} | "
                     f"{kayit.get('ilk_basarisiz', '?')} | {kayit.get('son_basarisiz', '?')} |")
        L.append("")
    else:
        L += ["_Kara liste bos._", ""]
    L.append(_OTO_BIT)
    return "\n".join(L)


def taranamayan_raporu_guncelle(kara_liste):
    """taranamayan_semboller.md icindeki OTOMATIK blogu yeniler.

    Elle yazilmis bolumlere (gecici ariza notlari, tarama hizi dersi vb.)
    DOKUNMAZ — yalnizca isaretcilerle sinirlanmis blok degisir. Isaretciler
    yoksa blok dosyanin sonuna eklenir.
    """
    blok = _kara_liste_bolumu(kara_liste)
    try:
        os.makedirs(m.RAPOR_DIR, exist_ok=True)
        eski = ""
        if os.path.exists(TARANAMAYAN_MD):
            with open(TARANAMAYAN_MD, encoding="utf-8") as f:
                eski = f.read()
        if _OTO_BAS in eski and _OTO_BIT in eski:
            bas = eski.index(_OTO_BAS)
            bit = eski.index(_OTO_BIT) + len(_OTO_BIT)
            yeni = eski[:bas] + blok + eski[bit:]
        else:
            yeni = (eski.rstrip() + "\n\n" if eski.strip() else "") + blok + "\n"
        with open(TARANAMAYAN_MD, "w", encoding="utf-8") as f:
            f.write(yeni)
    except OSError as e:
        print(f"   [RAPOR] taranamayan_semboller.md yazilamadi: "
              f"{type(e).__name__}: {e}", flush=True)


def main():
    zaten = set() if BASTAN else taranmis_bugun()
    kara_liste = kl.yukle()
    aday = [s for s in m.SEMBOLLER if s not in zaten]
    toplam = len(m.SEMBOLLER)

    # --- Kara liste: kalici olarak veri vermeyen sembolleri HIC DENEME --------
    # Bunlar TradingView'e gonderilmez; sembol basina ~20 sn (MAX_DENEME x
    # timeout) tasarruf. Yine de "okunamayanlar" listesine yazilirlar ki rapor
    # sayilari eksilmesin.
    todo, atlanan = [], []
    for s in aday:
        atla, sebep = kl.atlanmali_mi(kara_liste, s)
        (atlanan if atla else todo).append((s, sebep) if atla else s)

    print(f"Toplam {toplam} sembol. Bugun taranmis: {len(zaten)}. "
          f"Kalan: {len(todo)}"
          + (f" · kara listeden atlanan: {len(atlanan)}" if atlanan else "")
          + ".", flush=True)
    for s, sebep in atlanan:
        print(f"   kara listeden atlandi: {s} — {sebep}", flush=True)
    yeniden = [s for s in todo if kl.yeniden_denenecek_mi(kara_liste, s)]
    for s in yeniden:
        print(f"   kara listede ama {YENIDEN_DENE_GUN} gun doldu -> yeniden deneniyor: {s}",
              flush=True)

    atlanan_semboller = [s for s, _ in atlanan]
    # Rapor blogunu bagLANMADAN once de tazele: Chrome/TV yoksa kosum erken
    # bitse bile kara liste durumu dosyada guncel kalsin.
    taranamayan_raporu_guncelle(kara_liste)

    if not todo:
        yol, n, giren = rapor_yaz(atlanan_semboller)
        taranamayan_raporu_guncelle(kara_liste)
        print(f"Hepsi bugun taranmis/atlanmis. Rapor: {yol} ({n} sembol, {giren} rapora girdi)")
        print(f"   {kl.ozet_satiri(kara_liste)}")
        return

    p, b, tv = baglan_saglam()
    if tv is None:
        print("HATA: TradingView sekmesi bulunamadi. CHROME_X.bat calisip TV acik mi?")
        sys.exit(1)
    base = (tv.url or "").split("?")[0]
    taze = True  # yeni baglanti sonrasi ilk sembolu URL ile ac

    okunamadi, okunan = list(atlanan_semboller), 0
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
                if kl.basarili(kara_liste, sym):
                    print("   kara listeden CIKARILDI (artik okunuyor)", flush=True)
                    kl.kaydet(kara_liste)
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
            kayit = kl.basarisiz(kara_liste, sym)
            kl.kaydet(kara_liste)
            adet = kayit["deneme_sayisi"]
            if adet >= KARA_LISTE_ESIK:
                print(f"   kara listeye alindi ({adet}. basarisizlik) — bundan sonra "
                      f"denenmeden atlanacak, {YENIDEN_DENE_GUN} gunde bir yeniden denenecek",
                      flush=True)
            else:
                print(f"   kara liste sayaci: {adet}/{KARA_LISTE_ESIK}", flush=True)

    yol, n, giren = rapor_yaz(okunamadi)
    taranamayan_raporu_guncelle(kara_liste)
    print(f"\nBitti. Bu kosumda {okunan} okundu, {len(okunamadi)} okunamadi"
          + (f" ({len(atlanan_semboller)}'i kara listeden denenmeden atlandi)"
             if atlanan_semboller else "") + ".")
    print(f"Rapor: {yol}  (bugun toplam {n} sembol, {giren} rapora girdi)")
    print(kl.ozet_satiri(kara_liste))


if __name__ == "__main__":
    main()
