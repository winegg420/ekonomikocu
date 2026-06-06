#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sadece onemli yanitlar:
  1) @ekonomikocu'nun verdigi yanitlar (profil > Yanitlar sekmesi)
  2) Eko'nun cevap verdigi sorular (@ekonomikocu'ya yoneltilen, eko cevaplamis)

Cevap verilmemis ucuncu taraf mesajlari KAYDEDILMEZ.

Cikti: cekilen_yanitlar.jsonl (kayit_tipi: eko_yanit | soru)
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "yanit_tara_log.txt"


def _log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Eko yanitlari ve cevaplanan sorular")
    parser.add_argument("--attach-port", type=int, default=9222)
    parser.add_argument("--since", type=str, default="2026-04-01")
    parser.add_argument("--max-scroll", type=int, default=200)
    parser.add_argument("--status-limit", type=int, default=60)
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    from tara_nav import bind_safe_page
    from tweet_tara import (
        EXTRACT_JS,
        EXPAND_JS,
        JSONL_OUT,
        PROFILE_URL,
        RETRY_JS,
        YANITLAR_OUT,
        aggressive_timeline_scroll,
        click_replies_tab,
        close_foreign_tabs,
        force_turkish_on_page,
        goto_status,
        load_existing_replies,
        load_existing_rows,
        merge_conversation_page,
        merge_eko_profile_replies,
        merge_rows,
        migrate_session_if_needed,
        pick_profile_page,
        save_jsonl,
        save_replies_jsonl,
        scraped_to_records,
        wait_for_cdp_port,
        wait_for_profile_feed,
        x_clear_error,
    )

    since_dt = datetime.fromisoformat(args.since)
    all_rows = load_existing_rows(JSONL_OUT)
    all_replies = load_existing_replies(YANITLAR_OUT)
    rep0 = len(all_replies)
    eko_yanit0 = sum(1 for r in all_replies.values() if r.get("kayitTipi") == "eko_yanit")
    soru0 = sum(1 for r in all_replies.values() if r.get("kayitTipi") == "soru")

    def persist_tweets() -> None:
        save_jsonl(scraped_to_records(list(all_rows.values())), JSONL_OUT)

    def persist_replies() -> None:
        save_replies_jsonl(list(all_replies.values()), YANITLAR_OUT)

    migrate_session_if_needed()
    with sync_playwright() as p:
        if not wait_for_cdp_port(args.attach_port, 90):
            _log("Chrome yok (9222). CHROME_X.bat ac.")
            return 2
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{args.attach_port}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = pick_profile_page(context)
        bind_safe_page(page, PROFILE_URL)
        close_foreign_tabs(context, page)
        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(3000)
        x_clear_error(page)
        click_replies_tab(page)
        if not wait_for_profile_feed(page, tries=20):
            _log("Yanitlar sekmesi yuklenmedi.")
            return 3

        _log(f"Eko yanitlari (Yanitlar sekmesi) — max {args.max_scroll} scroll...")
        for i in range(args.max_scroll):
            page.evaluate(RETRY_JS)
            force_turkish_on_page(page)
            page.evaluate(EXPAND_JS)
            batch = page.evaluate(EXTRACT_JS)
            merge_rows(all_rows, batch, page=None, period_since=since_dt)
            merge_eko_profile_replies(all_replies, batch)
            if (i + 1) % 10 == 0:
                persist_replies()
                persist_tweets()
                eko_n = sum(1 for r in all_replies.values() if r.get("kayitTipi") == "eko_yanit")
                _log(f"  Scroll {i + 1}/{args.max_scroll} | eko_yanit: {eko_n} | soru: {len(all_replies) - eko_n}")
            aggressive_timeline_scroll(page)
            page.wait_for_timeout(2200)

        jobs = sorted(
            [
                tid
                for tid, row in all_rows.items()
                if tid.isdigit()
                and (row.get("datetime") or "") >= args.since
                and (row.get("text") or "").strip()
                and not row.get("isQuote")
            ],
            key=int,
            reverse=True,
        )[: args.status_limit]
        _log(f"Cevaplanan sorular icin konusma taramasi: {len(jobs)} tweet...")
        for i, tid in enumerate(jobs, 1):
            try:
                goto_status(page, tid)
                page.wait_for_timeout(1200)
                page.evaluate(RETRY_JS)
                force_turkish_on_page(page)
                page.evaluate(EXPAND_JS)
                merge_conversation_page(page, tid, all_rows, all_replies)
                if i % 20 == 0:
                    persist_replies()
                    _log(
                        f"  Konusma {i}/{len(jobs)} | eko_yanit: "
                        f"{sum(1 for r in all_replies.values() if r.get('kayitTipi') == 'eko_yanit')} | "
                        f"soru: {sum(1 for r in all_replies.values() if r.get('kayitTipi') == 'soru')}"
                    )
            except Exception as e:
                _log(f"  Atlandi ({tid}): {e}")

        persist_tweets()
        persist_replies()
        try:
            browser.close()
        except Exception:
            pass

    eko_n = sum(1 for r in all_replies.values() if r.get("kayitTipi") == "eko_yanit")
    soru_n = sum(1 for r in all_replies.values() if r.get("kayitTipi") == "soru")
    _log(
        f"BITTI | eko_yanit +{eko_n - eko_yanit0} (toplam {eko_n}) | "
        f"soru +{soru_n - soru0} (toplam {soru_n}) | dosya: {YANITLAR_OUT.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
