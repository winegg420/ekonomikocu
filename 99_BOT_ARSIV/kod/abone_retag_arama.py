# -*- coding: utf-8 -*-
"""TUM AY: X arama (Latest) ile @ekonomikocu tweetlerini gun-gun tarar.
Profil duvarina takilmaz; AMA X arama da ~birkac yuz sonuctan sonra hiz
sinirina (rate limit) girer. Bu yuzden DEVAM-EDEBILIR + THROTTLE-GUVENLI:

- Her gun checkpoint'e yazilir (log/arama_kumulatif.json: id -> {abone,dt,text}).
- Tamamlanan gunler log/arama_gunler.json'a yazilir; tekrar calistirinca ATLAR.
- Ust uste 2 gun 0 sonuc gelirse = throttle kabul edilir, DURUR (hesabi yormaz).
  Bir sure (cooldown) sonra tekrar calistir; kaldigi gunden devam eder.
- --merge: checkpoint'i cekilen_tweetler.jsonl'e isler (abone_ozel gunceller),
  eksikleri log/eksik_abone.jsonl'e yazar.

Kullanim:
  python abone_retag_arama.py          # tara (kaldigi yerden), throttle'da dur
  python abone_retag_arama.py --merge  # checkpoint -> arsiv
"""
import json
import sys
import urllib.parse
from datetime import date, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

JSONL = "cekilen_tweetler.jsonl"
CKPT = Path("log/arama_kumulatif.json")
DONE = Path("log/arama_gunler.json")
EKSIK_OUT = "log/eksik_abone.jsonl"
BASLA = date(2026, 2, 1)    # abone donemi ~Subat'ta basliyor; geriye uzatildi
BITIS = date(2026, 6, 23)   # until haric -> 22 Haz dahil
PORT = 9222

PROBE = r"""
() => {
  const out=[];
  document.querySelectorAll('article[data-testid="tweet"]').forEach(a=>{
    let id=null; const tl=a.querySelector('a[href*="/status/"]');
    if(tl){const m=(tl.getAttribute('href')||'').match(/status\/(\d+)/); if(m) id=m[1];}
    const tEl=a.querySelector('time'); const dt=tEl?tEl.getAttribute('datetime'):null;
    const abone=!!a.querySelector('[data-testid="icon-subscriber"]');
    const tt=a.querySelector('[data-testid="tweetText"]');
    const text=tt?(tt.innerText||''):'';
    out.push({id,dt,abone,text});
  });
  return out;
}
"""


def load_json(p, default):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def gun_tara(pg, gun: date) -> dict:
    q = f"from:ekonomikocu since:{gun.isoformat()} until:{(gun+timedelta(days=1)).isoformat()}"
    url = "https://x.com/search?q=" + urllib.parse.quote(q) + "&f=live"
    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)  # arama sonuclari yavas dolar
    seen = {}
    stag = 0
    for _ in range(70):
        before = len(seen)
        for r in pg.evaluate(PROBE):
            if r["id"]:
                seen[r["id"]] = {"abone": bool(r["abone"]), "dt": r["dt"], "text": r["text"]}
        if len(seen) == before:
            stag += 1
        else:
            stag = 0
        if stag >= 6:
            break
        pg.mouse.wheel(0, 2200)
        pg.wait_for_timeout(2000)
    return seen


def merge():
    ckpt = load_json(CKPT, {})
    arc_ids = set()
    lines = []
    upd = 0
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if not t:
                continue
            d = json.loads(t)
            tid = str(d.get("tweet_id"))
            arc_ids.add(tid)
            if tid in ckpt:
                nv = bool(ckpt[tid]["abone"])
                if d.get("abone_ozel") != nv:
                    d["abone_ozel"] = nv
                    upd += 1
            lines.append(json.dumps(d, ensure_ascii=False))
    with open(JSONL, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    eksik = {i: v for i, v in ckpt.items() if i not in arc_ids}
    with open(EKSIK_OUT, "w", encoding="utf-8") as f:
        for i, v in sorted(eksik.items(), key=lambda x: x[1].get("dt") or ""):
            f.write(json.dumps({"tweet_id": i, **v}, ensure_ascii=False) + "\n")
    ab = sum(1 for v in ckpt.values() if v["abone"])
    eab = sum(1 for v in eksik.values() if v["abone"])
    print(f"MERGE: checkpoint {len(ckpt)} tweet | abone {ab} | arsiv guncellenen {upd}")
    print(f"  ARSIVDE EKSIK: {len(eksik)} (abone {eab}) -> {EKSIK_OUT}")


def tara():
    ckpt = load_json(CKPT, {})
    done = set(load_json(DONE, []))
    sifir_ardisik = 0
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
        pg = b.contexts[0].new_page()
        # EN YENI GUNDEN GERIYE: throttle vurmadan once en guncel tweetler gelsin.
        g = BITIS - timedelta(days=1)
        while g >= BASLA:
            ds = g.isoformat()
            if ds in done:
                g -= timedelta(days=1)
                continue
            s = gun_tara(pg, g)
            if len(s) == 0:
                sifir_ardisik += 1
                print(f"{ds}: 0 tweet (sifir #{sifir_ardisik})", flush=True)
                if sifir_ardisik >= 2:
                    print(">> Ust uste 2 bos gun = THROTTLE. Duruyorum, cooldown sonra devam.", flush=True)
                    break
                g -= timedelta(days=1)
                continue
            sifir_ardisik = 0
            ckpt.update(s)
            done.add(ds)
            CKPT.write_text(json.dumps(ckpt, ensure_ascii=False), encoding="utf-8")
            DONE.write_text(json.dumps(sorted(done), ensure_ascii=False), encoding="utf-8")
            ab = sum(1 for v in s.values() if v["abone"])
            print(f"{ds}: {len(s)} tweet | abone {ab} | kumulatif {len(ckpt)}", flush=True)
            pg.wait_for_timeout(2500)  # gunler arasi nazik bekleme
            g -= timedelta(days=1)
        pg.close()
    kalan = [ (BASLA + timedelta(days=i)).isoformat()
              for i in range((BITIS-BASLA).days)
              if (BASLA+timedelta(days=i)).isoformat() not in done ]
    print(f"\nTARANAN gun: {len(done)} | KALAN gun: {len(kalan)}")
    if kalan:
        print("  kalan:", ", ".join(kalan))


if __name__ == "__main__":
    if "--merge" in sys.argv:
        merge()
    else:
        tara()
