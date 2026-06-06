#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

from tara_nav import bind_safe_page
from tweet_tara import (
    EXPAND_JS,
    LOCKED_RX_JS,
    PROFILE_URL_POSTS,
    RETRY_JS,
    aggressive_timeline_scroll,
    click_posts_tab,
    migrate_session_if_needed,
    pick_profile_page,
    wait_for_profile_feed,
    x_clear_error,
)


def main() -> int:
    migrate_session_if_needed()
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = pick_profile_page(b.contexts[0])
        bind_safe_page(page, PROFILE_URL_POSTS)
        page.goto(PROFILE_URL_POSTS, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(2500)
        x_clear_error(page)
        click_posts_tab(page)
        wait_for_profile_feed(page, tries=15)
        for i in range(30):
            page.evaluate(RETRY_JS)
            page.evaluate(EXPAND_JS)
            info = page.evaluate(
                f"""() => {{
                  const rx = /{LOCKED_RX_JS}/i;
                  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
                  let sub = 0, locked = 0, short = 0;
                  const samples = [];
                  for (const a of arts) {{
                    const raw = (a.innerText || '').slice(0, 1500);
                    const links = [...a.querySelectorAll('a[href*="/status/"]')];
                    const id = (links[0]?.href.match(/status\\/(\\d+)/) || [])[1] || '';
                    const texts = [...a.querySelectorAll('[data-testid="tweetText"]')].map(e => e.innerText);
                    const t = (texts[0] || '').trim();
                    if (/subscriber|abonelere|abone ol/i.test(raw)) sub++;
                    if (rx.test(raw) && t.length < 40) locked++;
                    if (t.length > 0 && t.length < 40) short++;
                    if (samples.length < 3 && (rx.test(raw) || /subscriber/i.test(raw))) {{
                      samples.push({{id, text: t.slice(0,80), raw_head: raw.slice(0,200)}});
                    }}
                  }}
                  return {{scroll: {i}+1, arts: arts.length, sub, locked, short, samples}};
                }}"""
            )
            if info["sub"] or info["locked"] or info["short"]:
                print(info)
            aggressive_timeline_scroll(page)
            page.wait_for_timeout(1800)
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
