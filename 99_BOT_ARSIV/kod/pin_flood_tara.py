#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profilde sabitlenmis (pinned) tweeti cek; #FLOOD ise thread parcalarini tamamla.
Varsa gomulu alinti kartini is_quote olarak kaydet.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


def _root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _root()
KOD = Path(__file__).resolve().parent
LOG = ROOT / "pin_flood_tara_log.txt"

PINNED_JS = """
() => {
  const out = [];
  for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {
    const raw = (article.innerText || '').slice(0, 6000);
    const social = article.querySelector('[data-testid="socialContext"]');
    const socialTxt = social ? (social.innerText || '') : '';
    const pinned = /pinned|sabitlendi/i.test(raw) || /pinned|sabitlendi/i.test(socialTxt);
    if (!pinned) continue;
    const links = [...article.querySelectorAll('a[href*="/status/"]')];
    const ids = links.map(a => (a.href.match(/status\\/(\\d+)/) || [])[1]).filter(Boolean);
    const mainId = ids[0] || null;
    if (!mainId) continue;
    const timeEl = article.querySelector('time');
    const texts = [...article.querySelectorAll('[data-testid="tweetText"]')].map(e => e.innerText);
    const mainText = texts[0] || '';
    const quoteBox = article.querySelector('[data-testid="quoteTweet"]');
    let qId = null, qText = '';
    if (quoteBox) {
      const qLink = quoteBox.querySelector('a[href*="/status/"]');
      qId = qLink ? (qLink.href.match(/status\\/(\\d+)/) || [])[1] : null;
      const qEl = quoteBox.querySelector('[data-testid="tweetText"]');
      qText = qEl ? qEl.innerText : '';
    }
    out.push({
      id: mainId,
      datetime: timeEl ? timeEl.getAttribute('datetime') : null,
      text: mainText,
      locked: false,
      isQuote: false,
      quotedBy: null,
      quoteOf: null,
      threadRoot: null,
      needsThread: /#FLOOD|\\/flood\\b/i.test(mainText),
      pinned: true,
      media: [],
      role: 'pinned',
      nestedQuoteId: qId,
      nestedQuoteText: qText,
    });
    break;
  }
  return out;
}
"""


def _log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    from tara_lock import acquire, release

    parser = argparse.ArgumentParser(description="Sabitle (pinned) tweet + flood")
    parser.add_argument("--attach-port", type=int, default=9222)
    args = parser.parse_args()

    if not acquire("pin_flood"):
        return 3

    from playwright.sync_api import sync_playwright

    from tweet_tara import (
        JSONL_OUT,
        PROFILE_URL_POSTS,
        close_foreign_tabs,
        finish_threads_loop,
        load_existing_rows,
        merge_rows,
        pick_profile_page,
        save_jsonl,
        scraped_to_records,
        wait_for_cdp_port,
    )
    from tara_nav import bind_safe_page, safe_goto

    all_rows = load_existing_rows(JSONL_OUT)
    if not all_rows:
        _log(f"Bos: {JSONL_OUT}")
        release()
        return 1

    def persist() -> None:
        save_jsonl(scraped_to_records(list(all_rows.values())), JSONL_OUT)

    with sync_playwright() as p:
        if not args.attach_port or not wait_for_cdp_port(args.attach_port, 90):
            _log("Chrome yok — CHROME_X.bat ac (9222)")
            release()
            return 2
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{args.attach_port}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = pick_profile_page(context)
        bind_safe_page(page, PROFILE_URL_POSTS)
        close_foreign_tabs(context, page)

        safe_goto(page, PROFILE_URL_POSTS, reason="pin-profil")
        page.wait_for_timeout(3500)
        pinned = page.evaluate(PINNED_JS) or []
        if not pinned:
            _log("Sabitle tweet bulunamadi (profilde Pin yok veya DOM degisti)")
            release()
            return 0

        row = pinned[0]
        pin_id = str(row.get("id") or "")
        _log(f"Sabitle: {pin_id} | flood:{bool(row.get('needsThread'))} | metin:{(row.get('text') or '')[:60]}")
        merge_rows(all_rows, [row], page=None)
        nested = row.get("nestedQuoteId")
        if nested and str(nested) != pin_id:
            merge_rows(
                all_rows,
                [
                    {
                        "id": str(nested),
                        "datetime": None,
                        "text": row.get("nestedQuoteText") or "",
                        "locked": False,
                        "isQuote": True,
                        "quotedBy": pin_id,
                        "quoteStub": True,
                        "media": [],
                        "role": "quote-pinned",
                    }
                ],
                page=None,
            )
            _log(f"  Gomulu alinti: {nested}")
        persist()

        if row.get("needsThread"):
            _log(f"  #FLOOD thread cekiliyor: {pin_id}")
            before = len(all_rows)
            finish_threads_loop(page, all_rows, set(), limit=5)
            added = len(all_rows) - before
            _log(f"  #FLOOD +{added} parca")
            persist()

        try:
            browser.close()
        except Exception:
            pass

    _log("BITTI")
    release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
