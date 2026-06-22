# -*- coding: utf-8 -*-
"""Canli: profil akisindaki her article'in TUM data-testid'lerini, aria-label'larini,
svg baslik/aria'larini ve 'subscrib/abone/ozel/lock' eslesmelerini dokar.
Amac: abonelere-ozel postun X DOM'undaki gercek isaretini bulmak. Salt-okunur."""
import json
from playwright.sync_api import sync_playwright

PROFILE = "https://x.com/ekonomikocu"
PROBE = r"""
() => {
  const out = [];
  const arts = document.querySelectorAll('article[data-testid="tweet"]');
  for (const a of arts) {
    let id = null;
    const tl = a.querySelector('a[href*="/status/"]');
    if (tl){const m=(tl.getAttribute('href')||'').match(/status\/(\d+)/); if(m) id=m[1];}
    const tEl = a.querySelector('time');
    const dt = tEl ? tEl.getAttribute('datetime') : null;
    const tt = a.querySelector('[data-testid="tweetText"]');
    const textLen = tt ? (tt.innerText||'').trim().length : 0;
    const testids = [...new Set([...a.querySelectorAll('[data-testid]')].map(e=>e.getAttribute('data-testid')))];
    const arias = [...new Set([...a.querySelectorAll('[aria-label]')].map(e=>e.getAttribute('aria-label')).filter(x=>x&&x.length<60))];
    const svgTitles = [...a.querySelectorAll('svg')].map(s=>{const t=s.querySelector('title'); return t?t.textContent:(s.getAttribute('aria-label')||'')}).filter(Boolean);
    const rx=/(abonel|abone|subscrib|özel|ozel|unlock|kilid|premium|crown|taç)/i;
    const hits=[];
    a.querySelectorAll('*').forEach(e=>{
      const t=(e.getAttribute&&e.getAttribute('aria-label'))||'';
      if(t&&rx.test(t)) hits.push('aria:'+t.slice(0,40));
    });
    const raw=(a.innerText||'');
    const rawHit = rx.test(raw) ? raw.split('\n').filter(l=>rx.test(l)).slice(0,3) : [];
    out.push({id,dt,textLen,testids,arias,svgTitles,hits:[...new Set(hits)],rawHit});
  }
  return out;
}
"""

def main():
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        page = ctx.new_page()
        page.goto(PROFILE, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        seen = {}
        for _ in range(6):
            for r in page.evaluate(PROBE):
                if r["id"]:
                    seen[r["id"]] = r
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2500)
        page.close()
    print(f"toplam article: {len(seen)}\n")
    # tum benzersiz testid ve aria havuzu
    allt = {}
    for r in seen.values():
        for t in r["testids"]:
            allt[t] = allt.get(t, 0) + 1
    print("=== TUM testid'ler (sayi) ===")
    for k, v in sorted(allt.items(), key=lambda x: -x[1]):
        print(f"  {v:>3}  {k}")
    print("\n=== abone/ozel/unlock IPUCU olan article'lar ===")
    any_hit = False
    for r in seen.values():
        if r["hits"] or r["rawHit"] or any('subscrib' in t.lower() or 'abone' in t.lower() for t in r["testids"]):
            any_hit = True
            print(f"\nid={r['id']} dt={r['dt']} textLen={r['textLen']}")
            print(f"  hits={r['hits']}")
            print(f"  rawHit={r['rawHit']}")
            print(f"  svgTitles={r['svgTitles'][:8]}")
    if not any_hit:
        print("  (HICBIRINDE abone/ozel/unlock isareti YOK)")
    print("\n=== ornek 3 article tam aria+svg ===")
    for r in list(seen.values())[:3]:
        print(f"\nid={r['id']} dt={r['dt']} len={r['textLen']}")
        print(f"  arias={r['arias'][:12]}")
        print(f"  svg={r['svgTitles'][:12]}")

if __name__ == "__main__":
    main()
