# -*- coding: utf-8 -*-
"""Canli profildeki icon-subscriber (abonelere-ozel) postlari toplar,
arsivde var mi / metni dolu mu capraz kontrol eder. Salt-okunur."""
import json
from playwright.sync_api import sync_playwright

PROFILE = "https://x.com/ekonomikocu"
PROBE = r"""
() => {
  const out=[];
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a=>{
    let id=null; const tl=a.querySelector('a[href*="/status/"]');
    if(tl){const m=(tl.getAttribute('href')||'').match(/status\/(\d+)/); if(m) id=m[1];}
    const tEl=a.querySelector('time'); const dt=tEl?tEl.getAttribute('datetime'):null;
    const tt=a.querySelector('[data-testid="tweetText"]');
    const textLen=tt?(tt.innerText||'').trim().length:0;
    const abone=!!a.querySelector('[data-testid="icon-subscriber"]');
    out.push({id,dt,textLen,abone});
  });
  return out;
}
"""

def main():
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page=b.contexts[0].new_page()
        page.goto(PROFILE, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        seen={}
        for _ in range(25):
            for r in page.evaluate(PROBE):
                if r["id"]: seen[r["id"]]=r
            page.mouse.wheel(0,3200); page.wait_for_timeout(2200)
        page.close()
    arc={}
    for line in open("cekilen_tweetler.jsonl",encoding="utf-8"):
        line=line.strip()
        if line:
            d=json.loads(line); arc[str(d.get("tweet_id"))]=d
    abone=[r for r in seen.values() if r["abone"]]
    print(f"Canli gorulen tweet: {len(seen)} | abonelere-ozel (icon-subscriber): {len(abone)}")
    if abone:
        dts=[r['dt'] for r in abone if r['dt']]
        print(f"  abone post tarih araligi: {min(dts)} .. {max(dts)}")
    yok=[r for r in abone if r["id"] not in arc]
    bos=[r for r in abone if r["id"] in arc and len((arc[r['id']].get('text') or '').strip())<6]
    print(f"  arsivde YOK            : {len(yok)}")
    print(f"  arsivde var ama BOS    : {len(bos)}")
    for r in yok[:20]:
        print(f"   YOK -> {r['dt']} id={r['id']} canliTextLen={r['textLen']}")
    for r in bos[:20]:
        print(f"   BOS -> {r['dt']} id={r['id']}")
    print("\nSONUC:", "TUM canli abone postlari arsivde DOLU." if (not yok and not bos) else "EKSIK VAR (yukarida).")

if __name__=="__main__":
    main()
