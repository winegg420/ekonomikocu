#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDP ile acik Chrome sekmesinde X sayfasini toparla:
- profile'a git
- Retry / reload butonlarini tikla
- Posts tab'ini tikla
- tweet yuklenene kadar bekle
"""
from __future__ import annotations

from playwright.sync_api import sync_playwright

from tweet_tara import (
    PROFILE_URL_POSTS,
    click_posts_tab,
    migrate_session_if_needed,
    pick_profile_page,
    timeline_tweet_count,
    wait_for_cdp_port,
    wait_for_profile_feed,
    x_clear_error,
)
from tara_nav import bind_safe_page


def main() -> int:
    port = 9222
    migrate_session_if_needed()
    if not wait_for_cdp_port(port, 5):
        print("CDP yok (9222).")
        return 2
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = b.contexts[0] if b.contexts else b.new_context()
        page = pick_profile_page(ctx)
        bind_safe_page(page, PROFILE_URL_POSTS)
        try:
            page.goto(PROFILE_URL_POSTS, wait_until="domcontentloaded", timeout=90_000)
        except Exception:
            pass
        page.wait_for_timeout(2500)
        x_clear_error(page)
        click_posts_tab(page)
        ok = wait_for_profile_feed(page, tries=25)
        n = timeline_tweet_count(page)
        url = page.url
        body = page.evaluate("() => (document.body.innerText || '').slice(0, 180)")
        print("url:", url)
        print("tweets:", n)
        print("ok:", ok)
        print("body:", (body or "").replace("\n", " | "))
        b.close()
        return 0 if ok and n >= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())

