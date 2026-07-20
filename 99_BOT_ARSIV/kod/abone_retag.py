# -*- coding: utf-8 -*-
"""Profil akisini NAZIK kaydirip her tweet'i X'in GERCEK abonelere-ozel
isaretiyle (data-testid='icon-subscriber') yeniden etiketler.
- Gorulen her tweet icin abone_ozel = True/False kesin yazilir.
- Splash/Retry cikarsa tiklar, bekler (hizli kaydirma splash'i tetikler).
- 22 May 2026'ya gelince ya da uzun sure ilerleme olmazsa durur.
- Arsivi yerinde gunceller (sadece abone_ozel; diger alanlara dokunmaz).
Salt mantik: hicbir dolu metni silmez."""
import json
import sys
import time
from playwright.sync_api import sync_playwright

from tarayici_saglik import baglanti_hatasi, icerik_bekle, iyilestir, sayfa_canli

PROFILE = "https://x.com/ekonomikocu"
JSONL = "cekilen_tweetler.jsonl"
DUR_TARIH = "2026-05-22"  # buraya (UTC) inince yeter

PROBE = r"""
() => {
  const out=[];
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a=>{
    let id=null; const tl=a.querySelector('a[href*="/status/"]');
    if(tl){const m=(tl.getAttribute('href')||'').match(/status\/(\d+)/); if(m) id=m[1];}
    const tEl=a.querySelector('time'); const dt=tEl?tEl.getAttribute('datetime'):null;
    const abone=!!a.querySelector('[data-testid="icon-subscriber"]');
    const sc=a.querySelector('[data-testid="socialContext"]');
    const pinned=/pinned|sabitlen/i.test(sc?(sc.innerText||''):'');
    out.push({id,dt,abone,pinned});
  });
  return out;
}
"""
RETRY = r"""
() => {
  const rx=/^(retry|yeniden dene|try again|tekrar dene|yeniden yükle)$/i;
  for(const el of document.querySelectorAll('button,div[role="button"],a')){
    const t=(el.innerText||'').trim();
    if(rx.test(t)){ try{el.click(); return true;}catch(e){} }
  }
  return false;
}
"""

def main():
    seen = {}  # id -> abone(bool)
    oldest = None
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = b.contexts[0].new_page()
        page.goto(PROFILE, wait_until="domcontentloaded", timeout=60000)
        icerik_bekle(page, 4000)
        stagnant = 0
        for i in range(200):
            try:
                rows = page.evaluate(PROBE)
                before = len(seen)
                for r in rows:
                    if r["id"]:
                        seen[r["id"]] = bool(r["abone"])
                        # Pinned (sabitlenmis) tweet eski tarihli olabilir; durdurma
                        # olcusunde HARIC tut, yoksa 1. turda yanlis durur.
                        if r["dt"] and not r.get("pinned") and (oldest is None or r["dt"] < oldest):
                            oldest = r["dt"]
                yeni = len(seen) - before
                ab = sum(1 for v in seen.values() if v)
                print(f"tur {i+1:>3}: gorulen={len(seen)} (+{yeni}) | abone_ozel={ab} | en_eski={oldest}", flush=True)
                if oldest and oldest[:10] <= DUR_TARIH:
                    print(">> 22 May'a ulasildi, duruyor.", flush=True)
                    break
                if yeni == 0:
                    stagnant += 1
                    # splash olabilir: Retry'a tikla
                    try:
                        if page.evaluate(RETRY):
                            print("  >> Retry tiklandi", flush=True)
                            page.wait_for_timeout(3500)
                    except Exception:
                        pass
                else:
                    stagnant = 0
                if stagnant >= 12:
                    print(">> 12 tur ilerleme yok (X duvari). Buraya kadar.", flush=True)
                    break
                # NAZIK kaydirma: kucuk adim + uzun bekleme (splash'i tetiklememek icin)
                page.mouse.wheel(0, 1600)
                page.wait_for_timeout(2600)
            except Exception as e:
                if not (baglanti_hatasi(e) or not sayfa_canli(page)):
                    raise
                npage = iyilestir(page, home_url=PROFILE, etiket="abone-retag")
                if npage is None:
                    print(">> Baglanti kurtarilamadi, buraya kadar.", flush=True)
                    break
                page = npage
                page.goto(PROFILE, wait_until="domcontentloaded", timeout=60000)
                icerik_bekle(page, 4000)
        page.close()

    # arsivi guncelle
    lines = []
    upd = 0
    abone_yazilan = 0
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            d = json.loads(s)
            tid = str(d.get("tweet_id"))
            if tid in seen:
                yeni_val = seen[tid]
                if d.get("abone_ozel") != yeni_val:
                    d["abone_ozel"] = yeni_val
                    upd += 1
                if yeni_val:
                    abone_yazilan += 1
            lines.append(json.dumps(d, ensure_ascii=False))
    with open(JSONL, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nGORULEN tweet         : {len(seen)}")
    print(f"  abonelere-ozel       : {sum(1 for v in seen.values() if v)}")
    print(f"ARSIVDE guncellenen    : {upd}")
    print(f"  abone_ozel=True yazil : {abone_yazilan}")
    print(f"en eski gorulen tarih  : {oldest}")

if __name__ == "__main__":
    main()
