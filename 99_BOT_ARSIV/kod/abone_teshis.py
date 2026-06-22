# -*- coding: utf-8 -*-
"""Canli teshis: @ekonomikocu profilinde abonelere-ozel post var mi?
DOM'da her article icin id/tarih/metin-uzunlugu + abone/subscriber/unlock
isaretlerini dokar. Salt-okunur; hicbir sey yazmaz."""
import json
import re
from playwright.sync_api import sync_playwright

PROFILE = "https://x.com/ekonomikocu"
PROBE_JS = r"""
() => {
  const out = [];
  const arts = document.querySelectorAll('article[data-testid="tweet"]');
  for (const a of arts) {
    let id = null;
    const tl = a.querySelector('a[href*="/status/"]');
    if (tl) { const m = (tl.getAttribute('href')||'').match(/status\/(\d+)/); if (m) id = m[1]; }
    const tEl = a.querySelector('time');
    const dt = tEl ? tEl.getAttribute('datetime') : null;
    const textEl = a.querySelector('[data-testid="tweetText"]');
    const text = textEl ? (textEl.innerText||'') : '';
    const raw = (a.innerText||'');
    const rxAbone = /(abonelere|abone ol|subscribe to unlock|unlock this post|subscribers only|subscriber|kilidi|bu gönderinin tamamı|read full|özel)/i;
    const aboneHit = rxAbone.test(raw);
    // sosyal baglam / rozet basligi
    const sc = a.querySelector('[data-testid="socialContext"]');
    out.push({
      id: id,
      dt: dt,
      textLen: text.trim().length,
      aboneHit: aboneHit,
      social: sc ? (sc.innerText||'').slice(0,60) : '',
      rawHead: raw.slice(0,80).replace(/\n/g,' ')
    });
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
        page.wait_for_timeout(4000)
        seen = {}
        for i in range(12):
            rows = page.evaluate(PROBE_JS)
            for r in rows:
                if r["id"]:
                    seen[r["id"]] = r
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(2500)
        page.close()

    # arsivle karsilastir
    arsiv = set()
    for line in open("cekilen_tweetler.jsonl", encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            arsiv.add(str(json.loads(line).get("tweet_id")))
        except Exception:
            pass

    abone_hits = [r for r in seen.values() if r["aboneHit"]]
    kilitli = [r for r in seen.values() if r["textLen"] < 6]
    print(f"Profilde gorulen tweet : {len(seen)}")
    print(f"  abone/unlock isareti  : {len(abone_hits)}")
    print(f"  metni bos/kisa (<6)   : {len(kilitli)}")
    print(f"  arsivde OLMAYAN       : {sum(1 for i in seen if i not in arsiv)}")
    print("\n--- abone/unlock isaretli olanlar ---")
    for r in abone_hits[:30]:
        inarc = "ARSIVDE" if r["id"] in arsiv else "YOK!"
        print(f"{r['dt']} len={r['textLen']:>4} {inarc} social='{r['social']}' | {r['rawHead']}")
    print("\n--- metni bos/kisa olanlar (kilitli olabilir) ---")
    for r in kilitli[:30]:
        inarc = "ARSIVDE" if r["id"] in arsiv else "YOK!"
        print(f"{r['dt']} len={r['textLen']:>4} {inarc} social='{r['social']}' | {r['rawHead']}")

if __name__ == "__main__":
    main()
