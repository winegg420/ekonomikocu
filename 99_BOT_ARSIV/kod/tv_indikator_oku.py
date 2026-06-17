# -*- coding: utf-8 -*-
"""TradingView grafik indikator okuyucu (CDP 9222).

Acik Chrome'a (CHROME_X.bat ile baslatilan, port 9222) baglanir, TradingView
sekmesini bulur ve grafik legend'indeki indikator ("Dogu Block" gibi) degerlerini
okur. Tum probe denemelerinin (legend_dump, probe..probe5) birlesik/temiz hali.

Kullanim:
    python tv_indikator_oku.py            # ozet: ana fiyat + Block study degerleri
    python tv_indikator_oku.py --dump     # tum legend ham dokumu (teshis)
    python tv_indikator_oku.py --ad Block # hangi indikatoru arayacagini sec (varsayilan: Block)

Onkosul: 9222 portunda Chrome acik ve icinde TradingView sekmesi (indikator yuklu,
giris yapilmis) acik olmali. Chrome'u CHROME_X.bat / CHROME_X_SESSIZ.bat baslatir.
"""
import sys, json

# Windows konsolu (cp1254) Unicode basamiyor -> ciktiyi UTF-8'e zorla
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PORT = 9222
AD = "Block"          # legend'de aranacak indikator adi (kismi eslesme)
DUMP = "--dump" in sys.argv
JSON_CIK = "--json" in sys.argv
if "--ad" in sys.argv:
    try:
        AD = sys.argv[sys.argv.index("--ad") + 1]
    except IndexError:
        pass

try:
    from playwright.sync_api import sync_playwright
except Exception:
    print("Playwright kurulu degil.")
    sys.exit(1)

# Tum legend metnini ham dok (teshis modu)
JS_DUMP = r"""() => {
  const out = [];
  const seen = new Set();
  const push = (label, el) => {
    const t = (el.innerText||'').replace(/\s*\n\s*/g,' | ').trim();
    if (t && !seen.has(label+t)) { seen.add(label+t); out.push("["+label+"] "+t); }
  };
  document.querySelectorAll('[class*="sources"]').forEach(el => push('sources', el));
  document.querySelectorAll('[class*="study"]').forEach(el => push('study', el));
  return out.length ? out.join("\n----\n") : "hicbir legend metni yok";
}"""

# Ozet: ana fiyat + hedef indikator hucreleri (index + metin + renk)
JS_OKU = r"""(ad) => {
  const res = {};
  // ana fiyat serisi (sources legend'i)
  const src = document.querySelector('[class*="sources"]');
  res.mainText = src ? (src.innerText||'').replace(/\s*\n\s*/g,' | ') : null;
  // hedef indikator study'sini bul
  const studies = Array.from(document.querySelectorAll('[class*="study"]'));
  let t = null;
  for (const el of studies) if ((el.innerText||'').includes(ad)) { t = el; break; }
  if (!t) { res.bulundu = false; return JSON.stringify(res, null, 1); }
  res.bulundu = true;
  const title = t.querySelector('[class*="title"]');
  res.title = title ? (title.innerText||'').trim() : null;
  // Her deger hucresini, ayni satirdaki plot adi (valueTitle) ile esle
  const vals = Array.from(t.querySelectorAll('[class*="valueValue"]'));
  res.cells = vals.map((e,i) => {
    // plot adi: valueValue'nun title attribute'unda (ya da wrapper'in data-test-id-value-title'inda)
    let ad = e.getAttribute('title');
    if (!ad) {
      const wrap = e.closest('[class*="valueItem"]');
      if (wrap) ad = wrap.getAttribute('data-test-id-value-title');
    }
    ad = (ad||'').trim() || null;
    return { i, ad, text: (e.innerText||'').trim(), color: getComputedStyle(e).color };
  });
  return JSON.stringify(res, null, 1);
}"""

with sync_playwright() as p:
    try:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
    except Exception as e:
        print(f"CDP baglanti hata (port {PORT}). Chrome acik mi? (CHROME_X.bat)\n{e}")
        sys.exit(1)

    pages = [pg for ctx in b.contexts for pg in ctx.pages]
    tv = next((pg for pg in pages if "tradingview.com" in (pg.url or "")), None)
    if not tv:
        print("TradingView sekmesi bu Chrome'da acik degil.")
        print("Acik sekmeler:")
        for i, pg in enumerate(pages):
            print(f"  [{i}] {getattr(pg,'url','?')}")
        sys.exit(0)

    # Crosshair'i temizle: fareyi grafik disina tasi -> legend SON mum degerini gosterir
    try:
        tv.mouse.move(5, 5)
    except Exception:
        pass

    if DUMP:
        print(tv.evaluate(JS_DUMP))
        sys.exit(0)

    ham = tv.evaluate(JS_OKU, AD)
    if JSON_CIK:
        print(ham)
        sys.exit(0)

    data = json.loads(ham)
    if not data.get("bulundu"):
        print(f"'{AD}' iceren indikator legend'de bulunamadi.")
        sys.exit(0)

    print(f"=== {data.get('title','').strip()} ===")
    for c in data.get("cells", []):
        ad = c.get("ad") or f"plot {c['i']}"
        deger = c.get("text", "")
        # ∅ = o mumda deger yok (cizilmemis)
        not_ = "  (deger yok)" if deger == "∅" else ""
        print(f"  {ad:48s} {deger}{not_}")
