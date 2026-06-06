#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

from tara_nav import bind_safe_page
from tweet_tara import (
    JSONL_OUT,
    EXPAND_JS,
    RETRY_JS,
    load_existing_rows,
    goto_status,
    migrate_session_if_needed,
    pick_profile_page,
    status_url,
)


def main() -> int:
    rows = load_existing_rows(JSONL_OUT)
    locked = sorted(
        [
            (tid, r)
            for tid, r in rows.items()
            if r.get("locked") and not (r.get("text") or "").strip() and not r.get("isQuote")
        ],
        key=lambda x: x[1].get("datetime") or "",
        reverse=True,
    )
    tid, _ = locked[0]
    migrate_session_if_needed()
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = pick_profile_page(b.contexts[0])
        bind_safe_page(page, status_url(tid))
        goto_status(page, tid)
        page.wait_for_timeout(3000)
        page.evaluate(RETRY_JS)
        page.evaluate(EXPAND_JS)
        info = page.evaluate(
            """(targetId) => {
              const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
              const ids = [];
              for (const a of arts) {
                const found = [];
                for (const link of a.querySelectorAll('a[href*="/status/"]')) {
                  const m = (link.href.match(/status\\/(\\d+)/) || [])[1];
                  if (m) found.push(m);
                }
                const texts = [...a.querySelectorAll('[data-testid="tweetText"]')].map(e => e.innerText);
                ids.push({found: [...new Set(found)], text_len: (texts[0]||'').length, match: found.includes(targetId)});
              }
              return {url: location.href, targetId, articles: ids.length, detail: ids};
            }""",
            tid,
        )
        print(info)
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
