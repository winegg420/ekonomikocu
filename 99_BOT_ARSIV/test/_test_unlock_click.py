#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

from tara_nav import bind_safe_page
from tweet_tara import (
    EXPAND_JS,
    JSONL_OUT,
    RETRY_JS,
    goto_status,
    load_existing_rows,
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
        buttons = page.evaluate(
            """() => {
              const out = [];
              for (const el of document.querySelectorAll('button, a, [role="button"], span')) {
                const t = (el.innerText || '').trim();
                if (!t || t.length > 80) continue;
                if (/abone|subscribe|unlock|kilidi|göster|view|read|tamam/i.test(t)) {
                  out.push(t);
                }
              }
              return [...new Set(out)].slice(0, 30);
            }"""
        )
        print("buttons:", buttons)
        # try click all subscription related
        page.evaluate(
            """() => {
              for (const el of document.querySelectorAll('button, a, [role="button"], div[role="button"], span')) {
                const t = (el.innerText || '').trim();
                if (/abone|subscribe|unlock|kilidi|read full|tamamını|gönderinin tamamı/i.test(t)) {
                  try { el.click(); } catch(e) {}
                }
              }
            }"""
        )
        page.wait_for_timeout(2000)
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
                return {texts, joined: texts.join('\\n'), raw: (a.innerText||'').slice(0,3000)};
              }
              return null;
            }""",
            tid,
        )
        print("after click:", data)
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
