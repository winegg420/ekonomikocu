#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

from tara_nav import bind_safe_page
from tweet_tara import (
    EXPAND_JS,
    RETRY_JS,
    goto_status,
    migrate_session_if_needed,
    pick_profile_page,
    status_url,
)

TIDS = ["2061888738112717021", "2061734756543320297", "2061187452321284361"]


def inspect(page, tid: str) -> None:
    goto_status(page, tid)
    page.wait_for_timeout(2500)
    page.evaluate(RETRY_JS)
    page.evaluate(EXPAND_JS)
    page.wait_for_timeout(1000)
    data = page.evaluate(
        """(targetId) => {
          for (const a of document.querySelectorAll('article[data-testid="tweet"]')) {
            let hit = false;
            for (const link of a.querySelectorAll('a[href*="/status/"]')) {
              const m = (link.href.match(/status\\/(\\d+)/) || [])[1];
              if (m === targetId) { hit = true; break; }
            }
            if (!hit) continue;
            const texts = [...a.querySelectorAll('[data-testid="tweetText"]')].map(e => e.innerText);
            const imgs = [...a.querySelectorAll('img[src]')].map(i => i.src).filter(s => /twimg/.test(s));
            return {
              texts,
              text_len: (texts.join('\\n') || '').length,
              imgs: imgs.length,
              raw: (a.innerText||'').slice(0,500),
            };
          }
          return {missing: true, url: location.href};
        }""",
        tid,
    )
    print(tid, data)


def main() -> int:
    migrate_session_if_needed()
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = pick_profile_page(b.contexts[0])
        for tid in TIDS:
            bind_safe_page(page, status_url(tid))
            inspect(page, tid)
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
