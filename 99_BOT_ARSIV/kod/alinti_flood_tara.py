#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yil kapsami (2025/2026) alintilarinin status sayfasindan TUM flood/thread parcalarini cek.

Her alinti ID -> x.com/i/status/{id} -> kaydir -> eko + konusma tweetleri jsonl'e.
Ic ice alinti kartlari kuyruga eklenir (BFS).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def _root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _root()
KOD = Path(__file__).resolve().parent
YIL = "2026"
LOG = ROOT / "alinti_flood_tara_log.txt"
DONE_FILE = ROOT / "alinti_flood_done.json"


def _paths_for_yil(yil: str) -> tuple[Path, Path]:
    if yil == "2026":
        return ROOT / "alinti_flood_tara_log.txt", ROOT / "alinti_flood_done.json"
    return ROOT / f"alinti_flood_tara_{yil}.log", ROOT / f"alinti_flood_done_{yil}.json"


def _log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_progress() -> tuple[set[str], dict[str, int]]:
    if not DONE_FILE.is_file():
        return set(), {}
    try:
        data = json.loads(DONE_FILE.read_text(encoding="utf-8"))
        done = {str(x) for x in (data.get("done") or []) if x}
        attempts = {str(k): int(v) for k, v in (data.get("attempts") or {}).items()}
        return done, attempts
    except Exception:
        return set(), {}


def save_progress(done: set[str], attempts: dict[str, int]) -> None:
    DONE_FILE.write_text(
        json.dumps(
            {
                "done": sorted(done, key=lambda x: int(x) if x.isdigit() else 0, reverse=True),
                "attempts": attempts,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def collect_yil_quotes(all_rows: dict[str, dict], yil: str) -> list[tuple[str, str | None]]:
    """(quote_id, quoted_by) — yil kapsami."""
    main_yil = {
        tid
        for tid, r in all_rows.items()
        if not r.get("isQuote") and (r.get("datetime") or "").startswith(yil)
    }
    jobs: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for tid, row in all_rows.items():
        if not row.get("isQuote"):
            continue
        qb = row.get("quotedBy") or row.get("quoted_by")
        in_scope = (row.get("datetime") or "").startswith(yil) or str(qb or "") in main_yil
        if not in_scope or tid in seen:
            continue
        seen.add(tid)
        jobs.append((tid, str(qb) if qb else None))
    return sorted(jobs, key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=True)


def _safe_eval(page, script: str, arg=None, *, quote_id: str | None = None, tries: int = 4):
    """SPA navigasyonunda evaluate kirilirsa status sayfasini yenile."""
    from tara_nav import nav_quiet, recover_quote_status

    last: Exception | None = None
    for n in range(tries):
        try:
            if arg is None:
                return page.evaluate(script)
            return page.evaluate(script, arg)
        except Exception as e:
            last = e
            err = str(e).lower()
            if "closed" in err:
                raise
            if "destroyed" in err or "navigation" in err:
                page.wait_for_timeout(1500 + n * 500)
                if quote_id:
                    recover_quote_status(page, quote_id)
                    nav_quiet(page, 12.0)
                    page.wait_for_timeout(2000)
                continue
            raise
    if last:
        raise last
    return None


def _flood_root_from_rows(rows: list[dict], fallback: str) -> str:
    for raw in rows:
        t = raw.get("text") or ""
        if re.search(r"#FLOOD|/flood\b", t, re.I):
            return str(raw.get("id") or fallback)
    return fallback


def crawl_quote_flood_deep(
    page,
    quote_id: str,
    quoted_by: str | None,
    all_rows: dict[str, dict],
    *,
    max_scroll: int = 45,
    skip_media: bool = True,
) -> tuple[int, list[str], int]:
    """Status sayfasindan flood/thread parcalarini cek. (eklenen, yeni_alinti_id, konusma_sayisi)"""
    from tweet_tara import (
        CONVERSATION_EXTRACT_JS,
        EXPAND_JS,
        EXTRACT_JS,
        PROFILE_HANDLE,
        QUOTE_STATUS_EXTRACT_JS,
        RETRY_JS,
        SCROLL_JS,
        THREAD_EXTRACT_JS,
        goto_status,
        merge_rows,
        page_stuck_loading,
        release_status_page,
    )
    from tara_nav import _is_trap_url, nav_quiet, recover_quote_status, wait_status_ready

    new_quote_ids: list[str] = []
    _log(f"  >> Alinti flood: {quote_id} (ana: {quoted_by or '—'})")
    try:
        if _is_trap_url(page.url or ""):
            recover_quote_status(page, quote_id)
        if page_stuck_loading(page):
            recover_quote_status(page, quote_id)
        for attempt in range(1, 4):
            try:
                goto_status(page, quote_id, fast=False)
                nav_quiet(page, 10.0)
                page.wait_for_timeout(2500)
                if page_stuck_loading(page):
                    wait_status_ready(page, quote_id, max_sec=45.0)
                break
            except Exception as e:
                if attempt >= 3 or "destroyed" not in str(e).lower():
                    raise
                page.wait_for_timeout(2000)
                recover_quote_status(page, quote_id)
        if page_stuck_loading(page):
            recover_quote_status(page, quote_id)
            if page_stuck_loading(page):
                return 0, [], 0
        nav_quiet(page, 12.0)
        _safe_eval(page, RETRY_JS, quote_id=quote_id)
        for _ in range(3):
            _safe_eval(page, EXPAND_JS, quote_id=quote_id)
            page.wait_for_timeout(500)
        before = len(all_rows)
        for i in range(max_scroll):
            _safe_eval(page, SCROLL_JS, quote_id=quote_id)
            page.wait_for_timeout(700 if i < 15 else 500)
            if i % 8 == 7:
                _safe_eval(page, EXPAND_JS, quote_id=quote_id)
        merge_rows(
            all_rows,
            _safe_eval(page, EXTRACT_JS, quote_id=quote_id) or [],
            page=None if skip_media else page,
        )
        conv = _safe_eval(page, CONVERSATION_EXTRACT_JS, quote_id, quote_id=quote_id) or []
        thread_root = _flood_root_from_rows(conv, quote_id)
        merge_rows(
            all_rows,
            _safe_eval(page, THREAD_EXTRACT_JS, thread_root, quote_id=quote_id) or [],
            page=None,
        )
        # Konusmadaki tum tweetler (eko + baska hesap) — flood arsivi
        eko_batch = []
        foreign_batch = []
        for raw in conv:
            tid = str(raw.get("id") or "")
            text = (raw.get("text") or "").strip()
            if not tid or not text:
                continue
            author = (raw.get("author") or "").lower()
            is_eko = author == PROFILE_HANDLE or raw.get("isEko")
            row = {
                "id": tid,
                "datetime": raw.get("datetime"),
                "text": text,
                "locked": bool(raw.get("locked")),
                "isQuote": False,
                "quotedBy": None,
                "quoteOf": quote_id,
                "threadRoot": thread_root,
                "needsThread": False,
                "media": [],
                "role": "alinti-flood-eko" if is_eko else "alinti-flood",
                "baglanti": f"alıntı flood (kök:{thread_root} alıntı:{quote_id})",
            }
            if is_eko:
                eko_batch.append(row)
            else:
                foreign_batch.append(row)
        if eko_batch:
            merge_rows(all_rows, eko_batch, page=None)
        if foreign_batch:
            merge_rows(all_rows, foreign_batch, page=None)
        # Alinti satirini guncelle
        qparts = _safe_eval(page, QUOTE_STATUS_EXTRACT_JS, quote_id, quote_id=quote_id) or []
        for p in qparts:
            p["isQuote"] = True
            p["quoteStub"] = False
            if quoted_by:
                p["quotedBy"] = quoted_by
            p["threadRoot"] = thread_root
            merge_rows(all_rows, [p], page=None)
            nested = p.get("id")
            if nested and nested != quote_id:
                new_quote_ids.append(str(nested))
        for p in qparts:
            for nested in (p.get("quoteOf"),):
                if nested and str(nested) != quote_id:
                    new_quote_ids.append(str(nested))
        added = len(all_rows) - before
        _log(f"     +{added} kayit | kok:{thread_root} | konusma:{len(conv)}")
        return added, new_quote_ids, len(conv)
    except Exception as e:
        _log(f"  >> Hata ({quote_id}): {e}")
        if "closed" in str(e).lower():
            raise
        return 0, [], 0
    finally:
        release_status_page(page)


def discover_quotes_on_main_status(
    page,
    all_rows: dict[str, dict],
    *,
    limit: int = 500,
    max_scroll: int = 8,
) -> list[str]:
    """Ana tweet status sayfalarinda gomulu alinti karti ara."""
    from tweet_tara import EXTRACT_JS, EXPAND_JS, RETRY_JS, goto_status, merge_rows, release_status_page

    main_ids = [
        tid
        for tid, r in all_rows.items()
        if not r.get("isQuote") and (r.get("datetime") or "").startswith(YIL) and tid.isdigit()
    ]
    main_ids = sorted(main_ids, key=int, reverse=True)[:limit]
    found: list[str] = []
    _log(f"Keşif: {len(main_ids)} ana tweet status (alinti karti)...")
    for i, tid in enumerate(main_ids, 1):
        try:
            goto_status(page, tid, fast=True)
            page.wait_for_timeout(1200)
            page.evaluate(RETRY_JS)
            page.evaluate(EXPAND_JS)
            batch = page.evaluate(EXTRACT_JS) or []
            merge_rows(all_rows, batch, page=None)
            for raw in batch:
                if raw.get("isQuote") and raw.get("id"):
                    qid = str(raw["id"])
                    if qid not in found:
                        found.append(qid)
                        merge_rows(
                            all_rows,
                            [
                                {
                                    **raw,
                                    "quotedBy": tid,
                                    "quoteStub": False,
                                }
                            ],
                            page=None,
                        )
        except Exception as e:
            _log(f"  >> Keşif atlandi ({tid}): {e}")
        finally:
            release_status_page(page)
        if i % 25 == 0:
            _log(f"  >> Keşif {i}/{len(main_ids)} | yeni alinti: {len(found)}")
    return found


def main() -> int:
    global YIL, LOG, DONE_FILE
    from tara_lock import acquire, release

    parser = argparse.ArgumentParser(description="Alintilarin flood/thread tam taramasi")
    parser.add_argument("--yil", default="2026", help="2025 veya 2026")
    parser.add_argument("--attach-port", type=int, default=9222)
    parser.add_argument("--max-scroll", type=int, default=45)
    parser.add_argument("--discover", type=int, default=0, help="N ana tweet status tara (0=kapali)")
    parser.add_argument("--skip-media", action="store_true", default=True)
    parser.add_argument("--no-pack", action="store_true")
    args = parser.parse_args()

    YIL = str(args.yil).strip()
    LOG, DONE_FILE = _paths_for_yil(YIL)

    if not acquire(f"alinti_flood_{YIL}"):
        return 3

    from playwright.sync_api import sync_playwright

    from tweet_tara import (
        JSONL_OUT,
        PROFILE_URL_POSTS,
        close_foreign_tabs,
        load_existing_rows,
        pick_profile_page,
        save_jsonl,
        scraped_to_records,
        wait_for_cdp_port,
    )
    from tara_nav import bind_safe_page

    all_rows = load_existing_rows(JSONL_OUT)
    if not all_rows:
        _log(f"Bos: {JSONL_OUT}")
        release()
        return 1

    def persist() -> None:
        save_jsonl(scraped_to_records(list(all_rows.values())), JSONL_OUT)

    queue: list[tuple[str, str | None]] = collect_yil_quotes(all_rows, YIL)
    done, attempts = load_progress()
    total_added = 0
    pending = [j for j in queue if j[0] not in done]
    _log(
        f"BASLA | kuyruk: {len(queue)} alinti ({YIL} kapsami)"
        + (f" | atlanan (once): {len(done)}" if done else "")
        + f" | kalan: {len(pending)}"
    )
    queue = pending

    with sync_playwright() as p:
        if not args.attach_port or not wait_for_cdp_port(args.attach_port, 90):
            _log("Chrome yok — CHROME_X.bat ac (9222)")
            release()
            return 2
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{args.attach_port}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = pick_profile_page(context)
        page._eko_allow_foreign_status = True  # type: ignore[attr-defined]
        bind_safe_page(page, PROFILE_URL_POSTS)
        close_foreign_tabs(context, page)

        if args.discover > 0 and not done:
            extra = discover_quotes_on_main_status(
                page, all_rows, limit=args.discover
            )
            persist()
            for qid in extra:
                if qid not in done:
                    queue.append((qid, None))
            _log(f"Keşif bitti: +{len(extra)} alinti ID")

        while queue:
            quote_id, quoted_by = queue.pop(0)
            if quote_id in done:
                continue
            attempts[quote_id] = attempts.get(quote_id, 0) + 1
            try:
                added, nested, conv_n = crawl_quote_flood_deep(
                    page,
                    quote_id,
                    quoted_by,
                    all_rows,
                    max_scroll=args.max_scroll,
                    skip_media=args.skip_media,
                )
            except Exception as e:
                if "closed" in str(e).lower():
                    _log(
                        f"Chrome/sekme kapandi — durduruluyor. CHROME_X.bat acip "
                        f"TARA_ALINTI_FLOOD_{YIL}.bat tekrar calistir."
                    )
                    break
                raise
            total_added += added
            if added:
                persist()
            if conv_n > 0 or added > 0:
                done.add(quote_id)
                save_progress(done, attempts)
            elif attempts[quote_id] >= 3:
                done.add(quote_id)
                save_progress(done, attempts)
                _log(f"  >> Vazgecildi (3 deneme): {quote_id}")
            else:
                queue.append((quote_id, quoted_by))
                save_progress(done, attempts)
                _log(f"  >> Bos sayfa — tekrar ({attempts[quote_id]}/3): {quote_id}")
            for nid in nested:
                if nid not in done and (nid, quote_id) not in queue:
                    queue.append((nid, quote_id))
            if len(done) % 5 == 0:
                _log(f"Ilerleme: {len(done)} alinti islendi | kuyruk: {len(queue)} | +{total_added} kayit")

        try:
            browser.close()
        except Exception:
            pass

    persist()
    _log(f"BITTI | islenen alinti: {len(done)} | +{total_added} yeni/guncel kayit")
    subprocess_run = __import__("subprocess").run
    kapsam = KOD / f"kapsam_{YIL}.py"
    if kapsam.is_file():
        subprocess_run([sys.executable, str(kapsam)], cwd=ROOT, check=False)
    if not args.no_pack:
        subprocess_run([sys.executable, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
