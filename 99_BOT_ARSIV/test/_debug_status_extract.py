#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kilitle (abonelik) sayfasinda DOM gercekten tweet article veriyor mu?
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from tweet_tara import EXTRACT_JS, RETRY_JS, EXPAND_JS, status_url

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"


def main() -> int:
    rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    locked = [r for r in rows if r.get("locked") and not r.get("is_quote")]
    if not locked:
        print("No locked main tweets found.")
        return 0
    tids = [r["tweet_id"] for r in locked[:5]]
    print("locked tids:", tids)

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0] if b.contexts else b.new_context()
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        for tid in tids:
            print("\n--- tid:", tid)
            page.goto(status_url(tid), wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(6000)
            n = page.locator('article[data-testid="tweet"]').count()
            body_len = page.evaluate(
                "() => (document.body && document.body.innerText ? document.body.innerText.trim().length : 0)"
            )
            title = page.title()
            preview = page.evaluate(
                "() => (document.body && document.body.innerText ? document.body.innerText.trim().slice(0,200) : '')"
            )
            other = page.evaluate(
                "() => ({\n"
                "  articles: document.querySelectorAll('article').length,\n"
                "  tweet_articles: document.querySelectorAll('article[data-testid=\"tweet\"]').length,\n"
                "  tweetText_nodes: document.querySelectorAll('[data-testid=\"tweetText\"]').length,\n"
                "  mainColumn: document.querySelectorAll('[data-testid=\"primaryColumn\"]').length,\n"
                "  loginBtn: document.querySelectorAll('[data-testid=\"loginButton\"]').length,\n"
                "  bodyHead: (document.body && document.body.innerText ? document.body.innerText.trim().slice(0,120) : '')\n"
                "})"
            )
            print("after 6s title:", title[:60].replace('\\n',' '), "articles:", n, "body_len:", body_len)
            print("dom:", other)
            print("preview:", (preview or '').replace('\\n',' | '))

            page.evaluate(RETRY_JS)
            page.evaluate(EXPAND_JS)
            page.wait_for_timeout(3000)
            n2 = page.locator('article[data-testid="tweet"]').count()
            batch = page.evaluate(EXTRACT_JS)
            print("after retry articles:", n2, "extract_batch_len:", len(batch))
            if batch:
                r = batch[0]
                text = (r.get("text") or "").strip()
                print("first id:", r.get("id"), "locked:", r.get("locked"), "text_len:", len(text))
                print("text_head:", text[:200].replace("\\n", " | "))

        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
