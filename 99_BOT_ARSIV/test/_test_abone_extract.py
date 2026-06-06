#!/usr/bin/env python3
"""Tek kilitli tweet + profil scroll testi."""
from playwright.sync_api import sync_playwright

from tara_nav import bind_safe_page
from tweet_tara import (
    EXTRACT_JS,
    EXPAND_JS,
    JSONL_OUT,
    PROFILE_URL_POSTS,
    RETRY_JS,
    aggressive_timeline_scroll,
    click_posts_tab,
    load_existing_rows,
    merge_rows,
    goto_status,
    migrate_session_if_needed,
    pick_profile_page,
    status_url,
    timeline_tweet_count,
    wait_for_profile_feed,
    x_clear_error,
)


def main() -> int:
    rows = load_existing_rows(JSONL_OUT)
    locked = [
        (tid, r)
        for tid, r in rows.items()
        if r.get("locked") and not (r.get("text") or "").strip() and not r.get("isQuote")
    ]
    locked.sort(key=lambda x: x[1].get("datetime") or "", reverse=True)
    print(f"locked empty: {len(locked)}")
    if not locked:
        return 0
    tid, _ = locked[0]
    print(f"test id: {tid}")

    migrate_session_if_needed()
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        page = pick_profile_page(ctx)

        # Status test
        bind_safe_page(page, status_url(tid))
        goto_status(page, tid)
        page.wait_for_timeout(2500)
        n_art = page.locator('article[data-testid="tweet"]').count()
        body_len = page.evaluate("() => (document.body.innerText || '').length")
        page.evaluate(RETRY_JS)
        page.evaluate(EXPAND_JS)
        batch = page.evaluate(EXTRACT_JS)
        print(f"STATUS articles={n_art} body_len={body_len} batch={len(batch)}")
        for row in batch[:3]:
            print(
                f"  id={row.get('id')} locked={row.get('locked')} "
                f"text_len={len(row.get('text') or '')}"
            )
        tmp = dict(rows)
        merge_rows(tmp, batch, page=None)
        got = (tmp.get(tid, {}).get("text") or "").strip()
        print(f"STATUS merged text_len={len(got)}")
        if got:
            print(f"  preview: {got[:150]}")

        # Profile scroll test (3 scroll)
        bind_safe_page(page, PROFILE_URL_POSTS)
        page.goto(PROFILE_URL_POSTS, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(2000)
        x_clear_error(page)
        click_posts_tab(page)
        wait_for_profile_feed(page, tries=10)
        filled = 0
        for i in range(5):
            page.evaluate(RETRY_JS)
            page.evaluate(EXPAND_JS)
            batch = page.evaluate(EXTRACT_JS)
            before = sum(
                1
                for t, r in rows.items()
                if r.get("locked") and not (r.get("text") or "").strip()
            )
            merge_rows(rows, batch, page=None)
            after = sum(
                1
                for t, r in rows.items()
                if r.get("locked") and not (r.get("text") or "").strip()
            )
            filled += before - after
            locked_in_batch = sum(1 for r in batch if r.get("locked"))
            text_in_batch = sum(1 for r in batch if (r.get("text") or "").strip())
            print(
                f"PROFILE scroll {i+1}: tw={timeline_tweet_count(page)} "
                f"batch={len(batch)} locked_in_batch={locked_in_batch} "
                f"text_in_batch={text_in_batch} filled_so_far={filled}"
            )
            aggressive_timeline_scroll(page)
            page.wait_for_timeout(2000)
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
