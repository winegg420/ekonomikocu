#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

from tara_nav import bind_safe_page
from tweet_tara import (
    EXTRACT_JS,
    EXPAND_JS,
    JSONL_OUT,
    QUOTE_STATUS_EXTRACT_JS,
    RETRY_JS,
    goto_status,
    load_existing_rows,
    merge_rows,
    migrate_session_if_needed,
    pick_profile_page,
    status_url,
)

TID = "2061734756543320297"


def main() -> int:
    rows = load_existing_rows(JSONL_OUT)
    print("before locked", rows[TID].get("locked"), "text", repr((rows[TID].get("text") or "")[:50]))
    migrate_session_if_needed()
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = pick_profile_page(b.contexts[0])
        bind_safe_page(page, status_url(TID))
        goto_status(page, TID)
        page.wait_for_timeout(2500)
        page.evaluate(RETRY_JS)
        page.evaluate(EXPAND_JS)
        batch1 = page.evaluate(EXTRACT_JS)
        batch2 = page.evaluate(QUOTE_STATUS_EXTRACT_JS, TID)
        print("EXTRACT batch", len(batch1))
        for r in batch1:
            if r.get("id") == TID:
                print(" EXTRACT hit", r.get("locked"), len(r.get("text") or ""))
        print("TARGET batch", len(batch2))
        for r in batch2:
            if r.get("id") == TID:
                print(" TARGET hit", r.get("locked"), len(r.get("text") or ""), (r.get("text") or "")[:80])
        merge_rows(rows, batch2, page=None)
        got = (rows[TID].get("text") or "").strip()
        print("after merge text_len", len(got), "locked", rows[TID].get("locked"))
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
