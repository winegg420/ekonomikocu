# -*- coding: utf-8 -*-
"""X arama (Latest) ile @ekonomikocu tweetleri profil duvarina takilmadan
daha derine inebiliyor mu? Salt-okunur test."""
import urllib.parse
from playwright.sync_api import sync_playwright

q = "from:ekonomikocu since:2026-05-22 until:2026-06-16"
URL = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=live"

PROBE = r"""
() => {
  const out=[];
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a=>{
    let id=null; const tl=a.querySelector('a[href*="/status/"]');
    if(tl){const m=(tl.getAttribute('href')||'').match(/status\/(\d+)/); if(m) id=m[1];}
    const tEl=a.querySelector('time'); const dt=tEl?tEl.getAttribute('datetime'):null;
    const abone=!!a.querySelector('[data-testid="icon-subscriber"]');
    out.push({id,dt,abone});
  });
  return out;
}
"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    pg = b.contexts[0].new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(5000)
    seen = {}
    oldest = None
    stag = 0
    for i in range(25):
        before = len(seen)
        for r in pg.evaluate(PROBE):
            if r["id"]:
                seen[r["id"]] = r["abone"]
                if r["dt"] and (oldest is None or r["dt"] < oldest):
                    oldest = r["dt"]
        print(f"tur {i+1}: gorulen={len(seen)} (+{len(seen)-before}) en_eski={oldest}", flush=True)
        if len(seen) == before:
            stag += 1
        else:
            stag = 0
        if stag >= 8:
            print(">> ilerleme yok, dur", flush=True)
            break
        pg.mouse.wheel(0, 2000)
        pg.wait_for_timeout(2200)
    ab = sum(1 for v in seen.values() if v)
    print(f"\nARAMA SONUC: gorulen={len(seen)} abone_ozel={ab} en_eski={oldest}")
    pg.close()
