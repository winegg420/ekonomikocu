#!/usr/bin/env python3
"""Chrome'da Retry ekrani yerine arama sonuclarini ac."""
from playwright.sync_api import sync_playwright

from tweet_tara import (
    SEARCH_URL,
    wait_for_cdp_port,
    x_clear_error,
    timeline_tweet_count,
    _log,
)


def main() -> int:
    if not wait_for_cdp_port(9222, 30):
        print("CHROME_X.bat calistir.")
        return 1
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        page = ctx.new_page()
        _log(f"Aciliyor: {SEARCH_URL}")
        page.goto(SEARCH_URL, wait_until="commit", timeout=120_000)
        page.wait_for_timeout(5000)
        x_clear_error(page)
        page.bring_to_front()
        n = timeline_tweet_count(page)
        print(f"Tweet listesi acildi. Ekranda: {n} tweet.")
        print("Bu sekmeyi kullan — Retry yazan eski sekmeyi kapatabilirsin.")
        try:
            page.wait_for_timeout(120_000)
        except KeyboardInterrupt:
            pass
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
