#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chrome X splash takildiysa profil akisina cek (CDP 9222)."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

from tara_nav import bind_safe_page, page_stuck_loading, recover_x_page
from tweet_tara import (
    PROFILE_URL_POSTS,
    timeline_tweet_count,
    wait_for_cdp_port,
)

CDP = 9222


def main() -> int:
    if not wait_for_cdp_port(CDP, 15):
        print("CHROME_X.bat ac — port 9222 yok.")
        return 1
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP}")
        if not browser.contexts:
            print("Chrome baglami yok.")
            return 1
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if "ekonomikocu" in (pg.url or "").lower():
                page = pg
                break
        page = page or (ctx.pages[0] if ctx.pages else None)
        if not page:
            print("Sekme yok.")
            return 1
        bind_safe_page(page, PROFILE_URL_POSTS)
        u = (page.url or "").lower()
        if "failedscript" in u or page_stuck_loading(page) or timeline_tweet_count(page) < 2:
            from tweet_tara import safe_goto, x_clear_error

            recover_x_page(page, home=PROFILE_URL_POSTS)
            if page_stuck_loading(page) or timeline_tweet_count(page) < 2:
                safe_goto(page, PROFILE_URL_POSTS, reason="x-duzelt")
                page.wait_for_timeout(6000)
                x_clear_error(page)
                page.reload(wait_until="commit", timeout=60_000)
                page.wait_for_timeout(4000)
                x_clear_error(page)
        else:
            print(f"OK — zaten yuklu ({timeline_tweet_count(page)} tweet ekranda).")
        print(f"URL: {page.url}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
