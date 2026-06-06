#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abone tweetlerini tek tek status sayfasindan metin olarak kaydet.
Sart: CHROME_X.bat acik, x.com abone oturumu, pencere KAPATILMAZ.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return here


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable
LOG = ROOT / "abone_tamamla_log.txt"


def _log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def count_abone(rows: dict) -> tuple[int, int, int]:
    """(bos kilitli, nisan+ metinli ana, kilitli+metin)"""
    empty = saved = locked_with_text = 0
    for row in rows.values():
        text = (row.get("text") or "").strip()
        if row.get("locked") and not text:
            empty += 1
        elif row.get("locked") and text:
            locked_with_text += 1
        d = row.get("datetime") or ""
        if d >= "2026-04-01" and not row.get("isQuote") and text:
            saved += 1
    return empty, saved, locked_with_text


def main() -> int:
    from tara_lock import acquire, release

    if not acquire("abone_tamamla"):
        return 3

    parser = argparse.ArgumentParser(description="Abone tweet metinlerini kaydet")
    parser.add_argument("--attach-port", type=int, default=9222)
    parser.add_argument("--since", type=str, default="2026-04-01")
    parser.add_argument("--per-round", type=int, default=300)
    parser.add_argument("--max-rounds", type=int, default=20)
    parser.add_argument("--profile-scroll", type=int, default=450)
    parser.add_argument("--skip-profile", action="store_true")
    parser.add_argument("--no-pack", action="store_true")
    parser.add_argument("--stall-sec", type=int, default=180, help="Ilerleme yoksa kurtarma (sn)")
    parser.add_argument("--max-auto-restart", type=int, default=8)
    parser.add_argument(
        "--max-id-attempts",
        type=int,
        default=5,
        help="Ayni tweet icin max deneme; sonra [erisilemedi] ve ilerle",
    )
    parser.add_argument(
        "--max-stall-rounds",
        type=int,
        default=3,
        help="Arka arkaya ilerleme yoksa kalanlari isaretle ve cik",
    )
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    from tara_ilerle import give_up_locked_batch
    from tara_nav import StallWatchdog, bind_safe_page, page_stuck_loading, recover_x_page
    from tweet_tara import (
        click_posts_tab,
        HAFIZA,
        JSONL_OUT,
        PROFILE_URL_POSTS,
        apply_to_hafiza,
        close_foreign_tabs,
        load_existing_rows,
        migrate_session_if_needed,
        pick_profile_page,
        refill_locked_since,
        refill_locked_profile_scroll,
        save_jsonl,
        scraped_to_records,
        wait_for_cdp_port,
        wait_for_profile_feed,
        x_clear_error,
    )

    since_dt = datetime.fromisoformat(args.since)
    all_rows = load_existing_rows(JSONL_OUT)
    if not all_rows:
        _log(f"Bos: {JSONL_OUT}")
        return 1

    empty0, saved0, lwt0 = count_abone(all_rows)
    locked_empty = empty0
    _log(
        f"BASLA | bos kilitli: {locked_empty} | Nisan+ metinli ana: {saved0} | "
        f"kilitli+metin: {lwt0}"
    )

    def persist(rows: dict) -> None:
        save_jsonl(scraped_to_records(list(rows.values())), JSONL_OUT)

    port = args.attach_port
    total_done = 0
    auto_restarts = int(os.environ.get("ABONE_AUTO_RESTART", "0"))
    watchdog = StallWatchdog(stall_sec=float(args.stall_sec), label="abone")
    migrate_session_if_needed()
    with sync_playwright() as p:
        cdp_browser = None
        context = None
        if port and wait_for_cdp_port(port, 90):
            try:
                cdp_browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
                context = cdp_browser.contexts[0] if cdp_browser.contexts else cdp_browser.new_context()
                _log(f"Chrome baglandi (port {port})")
            except Exception as e:
                _log(f"CDP hata: {e}")
        if not context:
            _log("Chrome yok. CHROME_X.bat ac, abone oturumu gir, tekrar calistir.")
            return 2
        page = pick_profile_page(context)
        bind_safe_page(page, PROFILE_URL_POSTS)
        close_foreign_tabs(context, page)
        from tara_nav import safe_goto

        safe_goto(page, PROFILE_URL_POSTS, reason="abone-baslangic")
        page.wait_for_timeout(3000)
        x_clear_error(page)
        if not wait_for_profile_feed(page, tries=20):
            _log(
                "HATA: Chrome'da @ekonomikocu tweetleri GORUNMUYOR. "
                "CHROME_X.bat ac, x.com giris + abone oturumu, profilde Retry tikla, tekrar calistir."
            )
            return 3
        _log("Profil hazir — abone tweet metinleri cekiliyor...")
        watchdog.ping()
        should_restart = False
        stall_rounds = 0
        n_pre = give_up_locked_batch(
            all_rows, since=args.since, max_attempts=args.max_id_attempts
        )
        if n_pre:
            persist(all_rows)
            _log(f"Onceki oturumlardan atlandi: {n_pre} bos kilitli")
        try:
            if not args.skip_profile and locked_empty > 0:
                prof_done = refill_locked_profile_scroll(
                    page,
                    all_rows,
                    since=since_dt,
                    max_scroll=args.profile_scroll,
                    save_cb=persist,
                )
                total_done += prof_done
                locked_empty = sum(
                    1
                    for r in all_rows.values()
                    if r.get("locked") and not (r.get("text") or "").strip()
                )
                _, saved_now, lwt_now = count_abone(all_rows)
                _log(
                    f"Profil kaydirma bitti: +{prof_done} metin | kalan bos: {locked_empty} | "
                    f"Nisan+ metinli: {saved_now} | kilitli+metin: {lwt_now}"
                )
            for rnd in range(1, args.max_rounds + 1):
                locked_now = sum(
                    1
                    for r in all_rows.values()
                    if r.get("locked") and not (r.get("text") or "").strip()
                )
                if locked_now == 0:
                    _log("Tum abone tweetleri metin olarak kaydedildi.")
                    break
                _log(f"Tur {rnd}/{args.max_rounds} | kalan bos kilitli: {locked_now}")
                if page_stuck_loading(page) or watchdog.needs_recovery():
                    watchdog.recover(page, PROFILE_URL_POSTS)
                done = refill_locked_since(
                    page,
                    all_rows,
                    since=since_dt,
                    limit=args.per_round,
                    return_url=PROFILE_URL_POSTS,
                    only_locked=True,
                    save_cb=persist,
                    capture_conversation=False,
                    fast=True,
                    watchdog=watchdog,
                    max_id_attempts=args.max_id_attempts,
                )
                total_done += done
                locked_after = sum(
                    1
                    for r in all_rows.values()
                    if r.get("locked") and not (r.get("text") or "").strip()
                )
                _, saved_now, lwt_now = count_abone(all_rows)
                _log(
                    f"Tur {rnd} bitti: +{done} metin | kalan bos: {locked_after} | "
                    f"Nisan+ metinli ana: {saved_now} | kilitli+metin: {lwt_now}"
                )
                if done == 0:
                    stall_rounds += 1
                else:
                    stall_rounds = 0
                if done == 0 and stall_rounds >= args.max_stall_rounds:
                    n_skip = give_up_locked_batch(
                        all_rows,
                        since=args.since,
                        max_attempts=args.max_id_attempts,
                        force=True,
                    )
                    if n_skip:
                        persist(all_rows)
                    locked_left = sum(
                        1
                        for r in all_rows.values()
                        if r.get("locked") and not (r.get("text") or "").strip()
                    )
                    _log(
                        f"Ilerleme yok ({stall_rounds} tur) — "
                        f"atlandi: {n_skip} | kalan bos: {locked_left} | devam ediliyor"
                    )
                    break
                if done == 0 and (page_stuck_loading(page) or watchdog.needs_recovery()):
                    _log("Turda metin gelmedi — splash / takilma kontrolu...")
                    ok = watchdog.recover(page, PROFILE_URL_POSTS)
                    if not ok:
                        try:
                            x_clear_error(page)
                            click_posts_tab(page)
                            recover_x_page(page, PROFILE_URL_POSTS)
                        except Exception:
                            pass
                elif done == 0:
                    page.wait_for_timeout(4000)
                    if watchdog.failed_recoveries >= 2:
                        auto_restarts += 1
                        if auto_restarts <= args.max_auto_restart:
                            _log(
                                f"WATCHDOG: {watchdog.idle_sec():.0f}s takilma — "
                                f"bot yeniden baslatiliyor ({auto_restarts}/{args.max_auto_restart})..."
                            )
                            persist(all_rows)
                            should_restart = True
                            break
                    continue
        finally:
            try:
                if cdp_browser:
                    cdp_browser.close()
            except Exception:
                pass

    persist(all_rows)
    if should_restart and auto_restarts <= args.max_auto_restart:
        env = os.environ.copy()
        env["ABONE_AUTO_RESTART"] = str(auto_restarts)
        cmd = [PY, str(Path(__file__).resolve())]
        cmd += [
            f"--since={args.since}",
            f"--per-round={args.per_round}",
            f"--max-rounds={args.max_rounds}",
            f"--attach-port={args.attach_port}",
            f"--stall-sec={args.stall_sec}",
            f"--max-auto-restart={args.max_auto_restart}",
            f"--max-id-attempts={args.max_id_attempts}",
            f"--max-stall-rounds={args.max_stall_rounds}",
        ]
        if args.skip_profile:
            cmd.append("--skip-profile")
        if args.no_pack:
            cmd.append("--no-pack")
        _log("Yeni surec baslatiliyor (Chrome acik kalsin)...")
        subprocess.Popen(cmd, cwd=ROOT, env=env)
        return 0

    _log("Analiz + hafiza yaziliyor...")
    subprocess.run([PY, str(ROOT / "analiz_devam.py")], cwd=ROOT, check=False)
    apply_to_hafiza(scraped_to_records(list(all_rows.values())), HAFIZA, False)
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    if not args.no_pack:
        subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)

    locked_end = sum(
        1 for r in all_rows.values() if r.get("locked") and not (r.get("text") or "").strip()
    )
    _, saved_end, lwt_end = count_abone(all_rows)
    _log(
        f"BITTI | bu oturumda +{total_done} metin | kalan bos kilitli: {locked_end} | "
        f"Nisan+ metinli ana: {saved_end} | kilitli+metin: {lwt_end}"
    )
    try:
        return 0 if total_done > 0 or locked_end < locked_empty else 1
    finally:
        release()


if __name__ == "__main__":
    raise SystemExit(main())
