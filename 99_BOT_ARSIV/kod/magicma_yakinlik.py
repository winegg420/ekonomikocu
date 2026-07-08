# -*- coding: utf-8 -*-
"""MagicMA yakinlik raporu (TradingView CDP 9222).

Acik TradingView grafigindeki sembolun ANLIK fiyatini ve "Doğu Block Sistem 2.0"
indikatorundeki MagicMA SEVIYE plotlarini okur; fiyat ile her seviye arasindaki
yuzde mesafeyi hesaplar, yakinlik etiketi verir ve filtreli rapor uretir.

KURALLAR (kullanici tanimi):
  1) Sadece adi "Magicma" ile baslayan SEVIYE plotlari alinir
     (Magicma Haftalik -1/-2, Magicma Gunluk Ust/Alt). Degeri 0 olanlar ve
     sinyaller (Magicma SAT/AL "Gösterge", DBS, Golden/Silver Cross,
     Destek Bolgesi, Dinamik Destek-Direnc) ALINMAZ.
  2) mesafe% = (fiyat - seviye) / seviye * 100   (neg=fiyat altinda, poz=ustunde)
  3) Sembol, EN AZ BIR seviyeye |mesafe%| <= 15 ise rapora girer; degilse rapora
     yazilmaz (ham jsonl'e yine de kaydedilir).
  4) Etiket:  |m|<=5 TEMAS  | <=10 YAKIN | <=15 IZLEME ; alt/ust (destek/direnc).
  5) Rapor en yakindan uzaga sirali.

Kullanim:
    python magicma_yakinlik.py            # acik grafigin sembolu: ham kayit + rapor
    python magicma_yakinlik.py --tara     # tum SEMBOLLER listesini gez -> birlesik .md rapor
    python magicma_yakinlik.py --rapor    # bugunku ham jsonl'den tum sembolleri sirali rapor
    python magicma_yakinlik.py --json     # tek sembol icin ham JSON

Onkosul: 9222'li Chrome acik + TradingView sekmesi (indikator yuklu, giris yapilmis).
"""
import sys, os, json, re, datetime, glob

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PORT = 9222
_KOD_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(os.path.dirname(_KOD_DIR))  # 99_BOT_ARSIV/kod -> repo koku
HAM_JSONL = os.path.join(_KOD_DIR, "magicma_ham.jsonl")
RAPOR_DIR = os.path.join(_REPO_DIR, "magicma")
RAPOR_FLAG = "--rapor" in sys.argv
JSON_FLAG = "--json" in sys.argv
TARA_FLAG = "--tara" in sys.argv

ESIK_TEMAS, ESIK_YAKIN, ESIK_IZLE = 5.0, 10.0, 15.0
INTERVAL = "240"  # 4 saatlik (kullanici: 4sa korunsun)

LISTE_DIR = os.path.join(_REPO_DIR, "magicma", "sembol_listesi")
# Dosya okuma sirasi (kripto once; geri kalan alfabetik ek .txt'ler sona eklenir).
_LISTE_SIRA = ["kripto.txt", "forex_emtia.txt", "endeks_faiz.txt",
               "abd_hisse.txt", "bist.txt"]


def sembolleri_yukle():
    """magicma/sembol_listesi/*.txt dosyalarindan sembol listesini oku.
    '#' yorum ve bos satir atlanir; sira korunur, tekrarlar elenir.
    Dizin/dosya yoksa bos doner (cagiran gomulu yedege duser)."""
    if not os.path.isdir(LISTE_DIR):
        return []
    dosyalar = [os.path.join(LISTE_DIR, d) for d in _LISTE_SIRA
                if os.path.exists(os.path.join(LISTE_DIR, d))]
    for p in sorted(glob.glob(os.path.join(LISTE_DIR, "*.txt"))):
        if p not in dosyalar:
            dosyalar.append(p)
    out, gorulen = [], set()
    for p in dosyalar:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith("#") or s in gorulen:
                        continue
                    gorulen.add(s); out.append(s)
        except Exception:
            continue
    return out


# Coklu tarama sembol listesi. "magicma taramasi yap" dendiginde bu listenin
# TAMAMI her seferinde taranir. Oncelik: sembol_listesi/*.txt dosyalari (duzenlenebilir,
# kripto otomatik uretilir). Dosyalar yoksa asagidaki gomulu yedek kullanilir.
_SEMBOLLER_YEDEK = [
    # --- Kripto (Binance) ---
    "BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:ETHBTC", "BINANCE:SOLUSDT",
    "BINANCE:AVAXUSDT", "BINANCE:NEARUSDT", "BINANCE:ARBUSDT", "BINANCE:AAVEUSDT",
    "BINANCE:UNIUSDT", "BINANCE:RENDERUSDT", "BINANCE:TAOUSDT", "BINANCE:IMXUSDT",
    "BINANCE:ENSUSDT", "BINANCE:CHZUSDT", "BINANCE:CAKEUSDT",
    "CRYPTOCAP:TOTAL", "CRYPTOCAP:BTC.D",
    # --- FX: en populer ilk 20 parite + DXY + USDTRY ---
    "TVC:DXY",
    "FX:EURUSD", "FX:USDJPY", "FX:GBPUSD", "FX:USDCHF", "FX:AUDUSD", "FX:USDCAD",
    "FX:NZDUSD", "FX:EURGBP", "FX:EURJPY", "FX:GBPJPY", "FX:EURCHF", "FX:AUDJPY",
    "FX:EURAUD", "FX:EURCAD", "FX:GBPCHF", "FX:AUDNZD", "FX:NZDJPY", "FX:GBPCAD",
    "FX:CADJPY", "FX:CHFJPY",
    "OANDA:USDTRY",
    # --- Emtia / metal ---
    "OANDA:XAUUSD", "OANDA:XAGUSD", "OANDA:XPTUSD", "OANDA:XPDUSD", "FX_IDC:XAUTRY",
    "TVC:USOIL", "TVC:UKOIL", "COMEX:HG1!",
    # --- Endeks / faiz ---
    "SP:SPX", "NASDAQ:NDX", "DJ:DJI", "TVC:VIX", "TVC:US10Y", "BIST:XU100", "BIST:XU030",
    # --- ABD hisse (en buyuk ~40) ---
    "NASDAQ:NVDA", "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:AMZN", "NASDAQ:GOOGL",
    "NASDAQ:META", "NASDAQ:TSLA", "NASDAQ:AVGO", "NASDAQ:NFLX", "NASDAQ:AMD",
    "NASDAQ:ADBE", "NASDAQ:COST", "NASDAQ:PEP", "NASDAQ:CSCO", "NASDAQ:INTC",
    "NASDAQ:QCOM", "NASDAQ:TXN", "NASDAQ:AMAT", "NASDAQ:MU", "NASDAQ:INTU",
    "NYSE:BRK.B", "NYSE:JPM", "NYSE:V", "NYSE:MA", "NYSE:WMT", "NYSE:UNH",
    "NYSE:XOM", "NYSE:JNJ", "NYSE:PG", "NYSE:HD", "NYSE:CVX", "NYSE:KO",
    "NYSE:BAC", "NYSE:ORCL", "NYSE:CRM", "NYSE:MRK", "NYSE:ABBV", "NYSE:PFE",
    "NYSE:DIS", "NYSE:NKE",
    # --- BIST 100 (tamami; gecersiz/degisen olursa "Okunamayanlar"a duser) ---
    "BIST:AEFES", "BIST:AGHOL", "BIST:AGROT", "BIST:AHGAZ", "BIST:AKBNK", "BIST:AKFGY",
    "BIST:AKSA", "BIST:AKSEN", "BIST:ALARK", "BIST:ALBRK", "BIST:ALFAS", "BIST:ANSGR",
    "BIST:ARCLK", "BIST:ASELS", "BIST:ASTOR", "BIST:BERA", "BIST:BIMAS", "BIST:BRSAN",
    "BIST:BRYAT", "BIST:BSOKE", "BIST:BTCIM", "BIST:CANTE", "BIST:CCOLA", "BIST:CIMSA",
    "BIST:CLEBI", "BIST:CWENE", "BIST:DOAS", "BIST:DOHOL", "BIST:ECILC", "BIST:ECZYT",
    "BIST:EGEEN", "BIST:EKGYO", "BIST:ENERY", "BIST:ENJSA", "BIST:ENKAI", "BIST:EREGL",
    "BIST:EUPWR", "BIST:FROTO", "BIST:GARAN", "BIST:GESAN", "BIST:GUBRF", "BIST:HALKB",
    "BIST:HEKTS", "BIST:ISCTR", "BIST:ISMEN", "BIST:IZENR", "BIST:KARSN", "BIST:KCAER",
    "BIST:KCHOL", "BIST:KONTR", "BIST:KONYA", "BIST:KOZAA", "BIST:TRALT", "BIST:KRDMD",
    "BIST:MAVI", "BIST:MGROS", "BIST:MIATK", "BIST:MPARK", "BIST:ODAS", "BIST:OTKAR",
    "BIST:OYAKC", "BIST:PETKM", "BIST:PGSUS", "BIST:REEDR", "BIST:SAHOL", "BIST:SASA",
    "BIST:SDTTR", "BIST:SISE", "BIST:SKBNK", "BIST:SMRTG", "BIST:SOKM", "BIST:TABGD",
    "BIST:TAVHL", "BIST:TCELL", "BIST:THYAO", "BIST:TKFEN", "BIST:TMSN", "BIST:TOASO",
    "BIST:TSKB", "BIST:TTKOM", "BIST:TTRAK", "BIST:TUKAS", "BIST:TUPRS", "BIST:TURSG",
    "BIST:ULKER", "BIST:VAKBN", "BIST:VESTL", "BIST:YEOTK", "BIST:YKBNK", "BIST:YYLGD",
    "BIST:ZOREN", "BIST:DAPGM", "BIST:GSRAY", "BIST:KLSER", "BIST:PASEU", "BIST:TUREX",
    "BIST:OBASE", "BIST:KOTON", "BIST:AVPGY", "BIST:PEKGY", "BIST:LMKDC",
]

SEMBOLLER = sembolleri_yukle() or _SEMBOLLER_YEDEK


def tr_sayi_parse(s):
    """Sayi metnini float'a cevir. Hem TR (64.802,00) hem EN (64,802.00 / 68.48)
    formatini destekler. TradingView'in dil/locale ayarina gore ',' veya '.'
    ondalik olabilir; bu yuzden formatdan bagimsiz oku. '∅'/bos -> None."""
    if not s:
        return None
    s = s.strip()
    if s in ("∅", "—", "-", ""):
        return None
    s = re.sub(r"[^0-9.,\-]", "", s)
    if not s:
        return None
    has_c, has_d = "," in s, "." in s
    if has_c and has_d:
        # iki ayirici da var: SONUNCUSU ondalik, digeri binliktir
        if s.rfind(",") > s.rfind("."):      # TR: ',' ondalik
            s = s.replace(".", "").replace(",", ".")
        else:                                 # EN: '.' ondalik
            s = s.replace(",", "")
    elif has_c:
        # sadece ',' : ondalik kabul (TR). 'binlik' tek ',' senaryosu indikator
        # degerlerinde olusmaz (hep ondalik basamak var).
        s = s.replace(",", ".")
    # sadece '.' veya ayirici yok: oldugu gibi (nokta ondalik)
    try:
        return float(s)
    except ValueError:
        return None


def tr_goster(x, ond=2):
    """1234.5 -> '1.234,50' (turk gosterimi)"""
    if x is None:
        return "—"
    neg = x < 0
    x = abs(x)
    tam = f"{x:,.{ond}f}"  # 1,234.50
    tam = tam.replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if neg else "") + tam


def etiket(m):
    a = abs(m)
    if a <= ESIK_TEMAS:
        return "TEMAS"
    if a <= ESIK_YAKIN:
        return "YAKIN"
    if a <= ESIK_IZLE:
        return "IZLEME"
    return "UZAK"


def yon_metin(m):
    # mesafe<0: fiyat seviyenin ALTINDA -> seviye direnc; >0: ustunde -> destek
    if m < 0:
        return "fiyat altinda (DIRENC)"
    return "fiyat ustunde (DESTEK)"


def seviyeleri_hesapla(fiyat, plots):
    """plots: [{ad, deger}] -> kural 1 filtreli MagicMA seviyeleri + mesafe."""
    out = []
    for p in plots:
        ad = (p.get("ad") or "").strip()
        if not ad.lower().startswith("magicma"):
            continue
        if "gösterge" in ad.lower() or "gosterge" in ad.lower():  # sinyal, atla
            continue
        deger = p.get("deger")
        if deger is None or deger == 0:
            continue
        m = (fiyat - deger) / deger * 100.0
        out.append({
            "ad": ad,
            "deger": deger,
            "mesafe_yuzde": round(m, 4),
            "etiket": etiket(m),
            "yon": yon_metin(m),
        })
    out.sort(key=lambda r: abs(r["mesafe_yuzde"]))
    return out


def kaydet_ham(kayit):
    with open(HAM_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def rapor_blok(kayit):
    """Tek sembol rapor metni (kural 3 gecmis sembol icin)."""
    s = kayit["sembol"]
    f = kayit["fiyat"]
    sat = [f"{s}   fiyat: {tr_goster(f)}"]
    for r in kayit["seviyeler"]:
        if abs(r["mesafe_yuzde"]) > ESIK_IZLE:
            continue
        m = r["mesafe_yuzde"]
        isar = "+" if m >= 0 else ""
        sat.append(
            f"   [{r['etiket']:6s}] {r['ad']:28s} {tr_goster(r['deger']):>14s}"
            f"   mesafe {isar}{tr_goster(m,1)}%  {r['yon']}"
        )
    return "\n".join(sat)


# ---- ANA SERI: --rapor (jsonl'den) ----
if RAPOR_FLAG:
    if not os.path.exists(HAM_JSONL):
        print("Ham jsonl yok, once sembol okut.")
        sys.exit(0)
    bugun = datetime.date.today().isoformat()
    # sembol basina en son kayit
    son = {}
    with open(HAM_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                k = json.loads(line)
            except Exception:
                continue
            if not k.get("ts", "").startswith(bugun):
                continue
            son[k["sembol"]] = k
    # kural 3: en az bir seviye |m|<=15 olanlar
    girenler = [k for k in son.values()
                if any(abs(r["mesafe_yuzde"]) <= ESIK_IZLE for r in k["seviyeler"])]
    # kural 5: en yakindan uzaga (sembolun en kucuk |mesafe|si)
    def enyakin(k):
        return min((abs(r["mesafe_yuzde"]) for r in k["seviyeler"]), default=9e9)
    girenler.sort(key=enyakin)
    print(f"=== MagicMA YAKINLIK RAPORU  ({bugun})  —  {len(girenler)} sembol ===\n")
    if not girenler:
        print("15% icinde sembol yok.")
    for k in girenler:
        print(rapor_blok(k))
        print()
    sys.exit(0)


# ---- Grafikten okuma (tek/coklu ortak) ----
try:
    from playwright.sync_api import sync_playwright
except Exception:
    print("Playwright kurulu degil.")
    sys.exit(1)
import time
from urllib.parse import quote

JS = r"""() => {
  const out = {};
  const sym = document.querySelector('[class*="symbolNameText"]');
  out.sembol = sym ? (sym.innerText||'').trim() : null;
  out.title = document.title;  // "BTCUSDT 64.802,000... ▼ -1.33% ..."
  const studies = Array.from(document.querySelectorAll('[class*="study"]'));
  let t=null; for(const el of studies) if((el.innerText||'').includes('Block')){t=el;break;}
  out.plots = [];
  if (t) {
    out.plots = Array.from(t.querySelectorAll('[class*="valueValue"]')).map(e => ({
      ad: (e.getAttribute('title')||'').trim(),
      ham: (e.innerText||'').trim()
    }));
  }
  return JSON.stringify(out);
}"""


def oku_data(tv):
    try:
        tv.mouse.move(5, 5)  # crosshair temizle -> son mum
    except Exception:
        pass
    return json.loads(tv.evaluate(JS))


# Sembol arama kutusu (sayfa yenilemeden hizli gecis)
_INP_SEL = ('input[placeholder*="Sembol"], input[placeholder*="Symbol"], '
            'input[placeholder*="ISIN"], input[class*="search"]')


def sembol_gecis(tv, sym):
    """Grafik icinde sembolu degistir (sayfa yenilemeden -> ~4x hizli)."""
    tv.keyboard.press("Escape")  # acik kalmis diyalog varsa kapat
    time.sleep(0.12)
    tv.click("#header-toolbar-symbol-search", timeout=8000)
    inp = tv.wait_for_selector(_INP_SEL, timeout=5000)
    inp.fill(sym)
    time.sleep(0.45)
    tv.keyboard.press("Enter")


def parse_title(title):
    # Isim + ilk sayi blogu (TR '64.802,00' veya EN '68.4800000000' fark etmez)
    mm = re.search(r"^(.*?)\s+([\d][\d.,]*)", title or "")
    if mm:
        return mm.group(1).strip(), tr_sayi_parse(mm.group(2))
    return None, None


def magicma_seviye_degerleri(data):
    """Sinyal olmayan MagicMA seviye plotlarinin parse edilmis degerleri."""
    out = []
    for p in data.get("plots", []):
        ad = (p.get("ad") or "").strip().lower()
        if not ad.startswith("magicma"):
            continue
        if "gösterge" in ad or "gosterge" in ad:
            continue
        v = tr_sayi_parse(p.get("ham"))
        if v is not None:
            out.append(v)
    return out


def data_to_kayit(data, kaynak):
    sembol, fiyat = parse_title(data.get("title", ""))
    if not sembol:
        sembol = (data.get("sembol") or kaynak).strip()
    if fiyat is None:
        return None
    plots = [{"ad": p["ad"], "deger": tr_sayi_parse(p["ham"])} for p in data.get("plots", [])]
    seviyeler = seviyeleri_hesapla(fiyat, plots)
    return {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "kaynak": kaynak,
        "sembol": sembol,
        "fiyat": fiyat,
        "seviyeler": seviyeler,
        "rapora_girdi": any(abs(r["mesafe_yuzde"]) <= ESIK_IZLE for r in seviyeler),
    }


def sembol_eslesir(tsym, ticker):
    if not tsym:
        return False
    a, b = tsym.upper(), ticker.upper()
    return a == b or b in a or a in b


def bekle_hesap(tv, ticker, timeout=20):
    """Sembol degisene + en az bir MagicMA seviye 0'dan cikana kadar bekle."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            data = oku_data(tv)
        except Exception:
            time.sleep(0.4); continue
        tsym, fiyat = parse_title(data.get("title", ""))
        nonzero = [v for v in magicma_seviye_degerleri(data) if abs(v) > 1e-9]
        if sembol_eslesir(tsym, ticker) and fiyat and nonzero:
            time.sleep(0.6)  # kisa oturma (degerler tam yerlessin)
            try:
                return oku_data(tv)
            except Exception:
                return data
        time.sleep(0.35)
    return None


def rapor_md_uret(kayitlar, okunamadi):
    bugun = datetime.date.today().isoformat()
    def enyakin(k):
        return min((abs(r["mesafe_yuzde"]) for r in k["seviyeler"]), default=9e9)
    girenler = [k for k in kayitlar
                if any(abs(r["mesafe_yuzde"]) <= ESIK_IZLE for r in k["seviyeler"])]
    girenler.sort(key=enyakin)  # kural 5: en kritik (TEMAS) en ustte
    L = [f"# MagicMA Yakınlık Raporu — {bugun}", ""]
    L.append("- Zaman dilimi: **4 saat (4H)**")
    L.append(f"- Taranan: {len(kayitlar)} · Rapora giren (≤%15): {len(girenler)} · Okunamayan: {len(okunamadi)}")
    L.append("- Eşik: TEMAS ≤%5 · YAKIN ≤%10 · İZLEME ≤%15")
    L.append("")
    for k in girenler:
        L.append(f"## {k['sembol']} — fiyat {tr_goster(k['fiyat'])}")
        L.append("")
        L.append("| Etiket | Seviye | Değer | Mesafe | Yön |")
        L.append("|---|---|---|---:|---|")
        for r in sorted(k["seviyeler"], key=lambda x: abs(x["mesafe_yuzde"])):
            if abs(r["mesafe_yuzde"]) > ESIK_IZLE:
                continue
            m = r["mesafe_yuzde"]; isar = "+" if m >= 0 else ""
            L.append(f"| {r['etiket']} | {r['ad']} | {tr_goster(r['deger'])} | "
                     f"{isar}{tr_goster(m,1)}% | {r['yon']} |")
        L.append("")
    if okunamadi:
        L.append("## Okunamayanlar")
        L.append("")
        L.append(", ".join(okunamadi))
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    with sync_playwright() as p:
        try:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
        except Exception as e:
            print(f"CDP baglanti hata (port {PORT}). Chrome acik mi? (CHROME_X.bat)\n{e}")
            sys.exit(1)
        pages = [pg for ctx in b.contexts for pg in ctx.pages]
        tv = next((pg for pg in pages if "tradingview.com" in (pg.url or "")), None)
        if not tv:
            print("TradingView sekmesi acik degil.")
            sys.exit(0)

        if TARA_FLAG:
            # ---- COKLU SEMBOL DONGUSU (sayfa-ici hizli gecis) ----
            base = (tv.url or "").split("?")[0]
            kayitlar, okunamadi = [], []
            toplam = len(SEMBOLLER)

            def url_ile_ac(sym):
                tv.goto(f"{base}?symbol={quote(sym)}&interval={INTERVAL}",
                        wait_until="domcontentloaded", timeout=45000)

            # Ilk sembol: URL ile ac -> 4H (interval) kilitlenir, indikator yuklenir.
            # Sonraki sembol gecisleri bu interval'i korur.
            ilk_ok = False
            for i, sym in enumerate(SEMBOLLER, 1):
                ticker = sym.split(":")[-1].strip()
                print(f"[{i}/{toplam}] {sym} ...", flush=True)
                try:
                    if not ilk_ok:
                        url_ile_ac(sym)         # ilk basarili yukleme URL ile
                    else:
                        sembol_gecis(tv, sym)   # gerisi sayfa-ici (~4x hizli)
                except Exception as e:
                    # gecis patladiysa URL yedegi dene
                    try:
                        url_ile_ac(sym)
                    except Exception:
                        print(f"   okunamadi (acilmadi: {str(e)[:50]})"); okunamadi.append(sym); continue

                data = bekle_hesap(tv, ticker, timeout=20)
                if data is None:
                    # son care: URL ile bir kez daha dene
                    try:
                        url_ile_ac(sym)
                        data = bekle_hesap(tv, ticker, timeout=25)
                    except Exception:
                        data = None
                if data is None:
                    print("   okunamadi (timeout / deger 0)"); okunamadi.append(sym); continue

                kayit = data_to_kayit(data, sym)
                if kayit is None:
                    print("   okunamadi (fiyat yok)"); okunamadi.append(sym); continue
                ilk_ok = True
                kaydet_ham(kayit)  # kural: her sembol ham jsonl'e append
                kayitlar.append(kayit)
                en = min((abs(r["mesafe_yuzde"]) for r in kayit["seviyeler"]), default=None)
                dur = f"en yakin {tr_goster(en,1)}%" if en is not None else "seviye yok"
                print(f"   OK {kayit['sembol']} {tr_goster(kayit['fiyat'])} ({dur})")

            os.makedirs(RAPOR_DIR, exist_ok=True)
            yol = os.path.join(RAPOR_DIR, f"magicma_rapor_{datetime.date.today().isoformat()}.md")
            with open(yol, "w", encoding="utf-8") as f:
                f.write(rapor_md_uret(kayitlar, okunamadi))
            giren = sum(1 for k in kayitlar if k["rapora_girdi"])
            print(f"\nBitti. {len(kayitlar)}/{toplam} okundu, {giren} rapora girdi, "
                  f"{len(okunamadi)} okunamadi.\nRapor: {yol}")
            sys.exit(0)

        # ---- TEK SEMBOL (acik grafik) ----
        data = oku_data(tv)

    kayit = data_to_kayit(data, (data.get("sembol") or "?"))
    if kayit is None:
        print(f"Anlik fiyat okunamadi. title='{data.get('title')}'")
        sys.exit(1)
    kaydet_ham(kayit)  # kural 3: her zaman ham kayit

    if JSON_FLAG:
        print(json.dumps(kayit, ensure_ascii=False, indent=1))
        sys.exit(0)

    if not kayit["seviyeler"]:
        print(f"{kayit['sembol']}: gecerli MagicMA seviyesi yok (hepsi 0 / bulunamadi).")
    elif not kayit["rapora_girdi"]:
        en = min(abs(r["mesafe_yuzde"]) for r in kayit["seviyeler"])
        print(f"{kayit['sembol']}: hicbir MagicMA seviyesine %15 kadar yakin degil "
              f"(en yakin {tr_goster(en,1)}%). Rapora yazilmadi, ham kayit alindi.")
    else:
        print(rapor_blok(kayit))
