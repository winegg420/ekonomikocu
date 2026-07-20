# -*- coding: utf-8 -*-
"""Eksik (tarama stall'i yuzunden atlanan) belirli tweetleri status sayfasindan
dogrudan cekip cekilen_tweetler.jsonl'e ekler. Botun kendi scraped_to_records
hatti kullanilir -> sema birebir uyumlu. Sonra analiz_devam ile zenginlestirilir.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

import tweet_tara as tt
from tarayici_saglik import baglanti_hatasi, icerik_bekle, iyilestir, sayfa_canli

ROOT = Path(__file__).resolve().parent.parent.parent
JSONL = tt.JSONL_OUT
MEDYA = ROOT / "medya"

IDS = [
    "2076306286510035174",
    "2076305670823989256",
    "2076292056125751392",
    "2076080051838239065",
    "2076008474761105917",
    "2076007842994110900",
    "2076001081750913524",
    "2076000379561500899",
    "2075999676914860039",
]

JS = r"""
(wantId) => {
  const arts = Array.from(document.querySelectorAll('article'));
  // Ana tweet: status linki wantId olan ilk article
  let art = null;
  for (const a of arts) {
    const links = Array.from(a.querySelectorAll("a[href*='/status/']"));
    if (links.some(l => (l.getAttribute('href')||'').includes('/status/'+wantId))) { art = a; break; }
  }
  if (!art) art = arts[0];
  if (!art) return null;
  const timeEl = art.querySelector('time');
  const textEl = art.querySelector("div[data-testid='tweetText']");
  const imgs = Array.from(art.querySelectorAll("img[src*='pbs.twimg.com/media']"))
                 .map(i => i.getAttribute('src'));
  return {
    datetime: timeEl ? timeEl.getAttribute('datetime') : null,
    text: textEl ? textEl.innerText : '',
    imgs: imgs,
  };
}
"""


def norm_img(src: str) -> str:
    # .../media/ABC?format=jpg&name=small -> name=large
    m = re.search(r"/media/([A-Za-z0-9_\-]+)", src)
    if not m:
        return src
    key = m.group(1)
    return f"https://pbs.twimg.com/media/{key}?format=jpg&name=large"


def download(url: str, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"    medya inilemedi {url[:60]}: {e}")
        return False


def main() -> int:
    raw_rows = []
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        for tid in IDS:
            url = f"https://x.com/ekonomikocu/status/{tid}"
            try:
                pg.goto(url, wait_until="commit", timeout=60000)
                icerik_bekle(pg, 5000)
                data = pg.evaluate(JS, tid)
            except Exception as e:
                if not (baglanti_hatasi(e) or not sayfa_canli(pg)):
                    raise
                npage = iyilestir(pg, home_url=url, etiket="gap-ekle")
                if npage is None:
                    break
                pg = npage
                try:
                    pg.goto(url, wait_until="commit", timeout=60000)
                    icerik_bekle(pg, 5000)
                    data = pg.evaluate(JS, tid)
                except Exception:
                    print(f"[{tid}] baglanti sonrasi da okunamadi, atlandi")
                    continue
            if not data or not (data.get("text") or "").strip():
                print(f"[{tid}] metin bulunamadi, atlandi")
                continue
            text = data["text"].strip()
            dt = data.get("datetime")
            # medya
            media_urls, media_files = [], []
            folder = MEDYA / tid
            existing = sorted(folder.glob("*.jpg")) if folder.exists() else []
            if existing:
                media_files = [f"medya/{tid}/{f.name}" for f in existing]
            imgs = [norm_img(s) for s in (data.get("imgs") or []) if "media" in s]
            # tekille
            seen = set()
            imgs = [u for u in imgs if not (u in seen or seen.add(u))]
            if imgs:
                media_urls = imgs
                if not media_files:
                    for i, u in enumerate(imgs, 1):
                        dest = folder / f"graf_{i:02d}.jpg"
                        if download(u, dest):
                            media_files.append(f"medya/{tid}/{dest.name}")
            raw_rows.append({
                "id": tid,
                "text": text,
                "locked": False,
                "datetime": dt,
                "isQuote": False,
                "lang": "tr",  # Koc'un Turkce tweetleri — kisa/hashtag metinde en sanilip dusmesin
                "media": media_urls,
                "mediaFiles": media_files,
            })
            print(f"[{tid}] OK | {dt} | {len(text)} char | {len(media_files)} medya")

    if not raw_rows:
        print("Eklenecek tweet yok.")
        return 1

    existing = tt.load_jsonl(JSONL)
    by_id = {r.tweet_id: r for r in existing}
    new_recs = tt.scraped_to_records(raw_rows)
    added = 0
    for r in new_recs:
        if r.tweet_id not in by_id:
            added += 1
        by_id[r.tweet_id] = r
    merged = list(by_id.values())
    tt.save_jsonl(merged, JSONL)
    print(f"\nEklendi/guncellendi: {len(new_recs)} (yeni {added}) | toplam {len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
