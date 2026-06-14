# -*- coding: utf-8 -*-
"""Son donem flood serilerini + parcalarini tamamla.

Profil taramasi flood'larin sadece kok/yuzey tweetini aliyor; devam
parcalari status sayfasinda. Bu script son donem (varsayilan 7 Haz+)
tweetlerinin status sayfalarini gezip eksik Koc tweetlerini ceker ve
flood-parca olarak etiketler (thread_root set). Sonra analiz_devam calistir.

Kullanim:
  python flood_tamamla_yeni.py [--since 2026-06-07] [--cap 140]
"""
from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

import tweet_tara as tt

ROOT = Path(__file__).resolve().parent.parent.parent
JSONL = tt.JSONL_OUT
MEDYA = ROOT / "medya"

# Bir status sayfasindaki TUM article'lari oku (her birinin kendi id'si,
# zaman, metin, yazar, alinti mi, medya). Tweet'in kendi id'si = zaman
# damgasinin sarildigi linkten.
JS_PAGE = r"""
() => {
  const arts = Array.from(document.querySelectorAll('article'));
  const out = [];
  for (const a of arts) {
    const timeEl = a.querySelector('time');
    let id = null, dt = null;
    if (timeEl) {
      dt = timeEl.getAttribute('datetime');
      const link = timeEl.closest('a');
      const href = link ? link.getAttribute('href') : '';
      const m = href ? href.match(/\/status\/(\d+)/) : null;
      if (m) id = m[1];
    }
    // yazar handle
    let handle = '';
    const al = a.querySelector("a[href^='/']");
    // daha guvenli: tweet permalink handle
    const links = Array.from(a.querySelectorAll("a[href*='/status/']"));
    for (const l of links) {
      const mm = (l.getAttribute('href')||'').match(/^\/([^\/]+)\/status\//);
      if (mm) { handle = mm[1]; break; }
    }
    const txtEl = a.querySelector("div[data-testid='tweetText']");
    const isQuote = !!a.querySelector("div[role='link'] div[data-testid='tweetText']");
    const imgs = Array.from(a.querySelectorAll("img[src*='pbs.twimg.com/media']"))
                   .map(i => i.getAttribute('src'));
    out.push({ id, dt, handle, text: txtEl ? txtEl.innerText : '', isQuote, imgs });
  }
  return out;
}
"""


def norm_img(src):
    m = re.search(r"/media/([A-Za-z0-9_\-]+)", src)
    return f"https://pbs.twimg.com/media/{m.group(1)}?format=jpg&name=large" if m else src


def download(url, dest):
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-06-07")
    ap.add_argument("--cap", type=int, default=140)
    args = ap.parse_args()

    existing = tt.load_jsonl(JSONL)
    have = {r.tweet_id for r in existing}

    # tohum: since+ tarihli mevcut tweetler
    seeds = []
    for r in existing:
        iso = r.dt.isoformat() if r.dt else ""
        if iso[:10] >= args.since:
            seeds.append(r.tweet_id)
    print(f"Tohum (>= {args.since}): {len(seeds)} tweet | cap {args.cap} sayfa")

    have_set = set(have)
    visited_pages = set()
    seen_on_page = set()
    queue = list(seeds)
    staged = {}  # id -> raw row

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pages = 0
        qi = 0
        while qi < len(queue) and pages < args.cap:
            tid = queue[qi]; qi += 1
            if tid in visited_pages:
                continue
            visited_pages.add(tid); pages += 1
            try:
                pg.goto(f"https://x.com/ekonomikocu/status/{tid}",
                        wait_until="commit", timeout=45000)
                pg.wait_for_timeout(3800)
                arts = []
                for _ in range(6):
                    arts = pg.evaluate(JS_PAGE)
                    pg.mouse.wheel(0, 2600)
                    pg.wait_for_timeout(1100)
                # son tam okuma
                arts = pg.evaluate(JS_PAGE)
            except Exception as e:
                print(f"  [{tid}] sayfa hata: {str(e)[:60]}")
                continue
            page_root = None
            for a in arts:
                if a.get("handle", "").lower() == "ekonomikocu" and a.get("id"):
                    page_root = a["id"]
                    break
            new_here = 0
            for a in arts:
                aid = a.get("id")
                if not aid or a.get("handle", "").lower() != "ekonomikocu":
                    continue
                seen_on_page.add(aid)
                text = (a.get("text") or "").strip()
                # yeni ve metinli ise stage et
                if aid not in have_set and aid not in staged and text:
                    media_urls = [norm_img(s) for s in (a.get("imgs") or []) if "media" in s]
                    folder = MEDYA / aid
                    media_files = []
                    if folder.exists():
                        media_files = [f"medya/{aid}/{f.name}" for f in sorted(folder.glob('*.jpg'))]
                    elif media_urls:
                        for i, u in enumerate(dict.fromkeys(media_urls), 1):
                            dest = folder / f"graf_{i:02d}.jpg"
                            if download(u, dest):
                                media_files.append(f"medya/{aid}/{dest.name}")
                    row = {
                        "id": aid, "text": text, "locked": False,
                        "datetime": a.get("dt"), "isQuote": bool(a.get("isQuote")),
                        "lang": "tr",
                        "media": list(dict.fromkeys(media_urls)), "mediaFiles": media_files,
                    }
                    if page_root and page_root != aid:
                        row["threadRoot"] = page_root
                    staged[aid] = row
                    new_here += 1
                # BFS: son donem tarihli ve sayfasi gezilmemisse kuyruga
                if (a.get("dt") or "")[:10] >= args.since and aid not in visited_pages:
                    queue.append(aid)
            if new_here:
                print(f"  [{tid}] +{new_here} yeni (sayfa {pages})")

    if not staged:
        print("Yeni flood/parca bulunmadi.")
        return 0

    new_recs = tt.scraped_to_records(list(staged.values()))
    by_id = {r.tweet_id: r for r in existing}
    added = 0
    for r in new_recs:
        if r.tweet_id not in by_id:
            added += 1
        by_id[r.tweet_id] = r
    tt.save_jsonl(list(by_id.values()), JSONL)
    print(f"\nEklendi: {added} yeni tweet | gezilen sayfa: {len(visited_pages)} | toplam {len(by_id)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
