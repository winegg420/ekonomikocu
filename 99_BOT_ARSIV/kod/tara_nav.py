#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tek sekme, sadece @ekonomikocu — guvenli goto + bookmark."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return here


ROOT = _project_root()
BOOKMARK_PATH = ROOT / "tara_bookmark.json"
PROFILE_HANDLE = "ekonomikocu"

_HANDLE_RX = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/(?!search|i/|home|explore|notifications|messages|settings)([A-Za-z0-9_]+)",
    re.I,
)
_STATUS_RX = re.compile(r"/status/(\d+)", re.I)


def is_any_status_url(url: str) -> bool:
    return bool(_STATUS_RX.search(url or ""))


def status_nav_allowed(page, url: str) -> bool:
    """Alinti/flood taramada yabanci hesap status sayfasinda kal."""
    if not getattr(page, "_eko_status_mode", False):
        return False
    if getattr(page, "_eko_allow_foreign_status", False):
        return is_any_status_url(url)
    return is_any_status_url(url)


def period_key(since: str | None, until: str | None = None) -> str:
    if not since:
        return "genel"
    return f"{since}_{until or 'open'}"


def load_bookmarks() -> dict:
    if not BOOKMARK_PATH.exists():
        return {}
    try:
        return json.loads(BOOKMARK_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_bookmark(key: str) -> dict | None:
    return load_bookmarks().get(key)


def save_bookmark(
    key: str,
    *,
    feed_url: str,
    scroll_index: int = 0,
    last_tweet_id: str | None = None,
    extra: dict | None = None,
) -> None:
    data = load_bookmarks()
    row = {
        "feed_url": feed_url,
        "scroll_index": scroll_index,
        "last_tweet_id": last_tweet_id,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    if extra:
        row.update(extra)
    data[key] = row
    BOOKMARK_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


_TRAP_RX = re.compile(
    r"premium|/i/flow/|oauth|/account/access|/account/login|/login\b|"
    r"intent/follow|intent/user|/tos\b|/privacy\b|ads\.x\.com",
    re.I,
)


def _is_trap_url(url: str) -> bool:
    """Premium, giris, reklam — tweet tarama disi tuzak sayfalar."""
    u = (url or "").lower()
    if not u or "x.com" not in u and "twitter.com" not in u:
        return False
    return bool(_TRAP_RX.search(u))


def _trap_recovery_dest(page) -> str:
    st = getattr(page, "_eko_status_url", None)
    if getattr(page, "_eko_status_mode", False) and st:
        return st
    home = getattr(page, "_eko_home", None)
    if home and (url_allowed(home) or is_any_status_url(home)):
        return home
    return f"https://x.com/{PROFILE_HANDLE}"


def _is_x_home(url: str) -> bool:
    u = (url or "").lower().strip().rstrip("/")
    u = u.split("?")[0].split("#")[0].rstrip("/")
    return u in (
        "https://x.com",
        "http://x.com",
        "https://twitter.com",
        "http://twitter.com",
        "https://www.x.com",
        "https://www.twitter.com",
    )


def url_allowed(url: str) -> bool:
    u = (url or "").lower().strip()
    if not u or u == "about:blank":
        return True
    if _is_x_home(url):
        return False
    if not ("x.com" in u or "twitter.com" in u):
        return False
    if any(
        x in u
        for x in (
            "/explore",
            "/home",
            "/notifications",
            "/messages",
            "/settings",
            "/compose/",
            "/login",
            "/signup",
            "/premium",
            "premium_sign_up",
            "/i/flow/",
            "/account/access",
            "oauth",
        )
    ):
        return False
    if f"/{PROFILE_HANDLE}" in u or f"/{PROFILE_HANDLE.lower()}" in u:
        return True
    if "/i/status/" in u:
        return True
    if "/search" in u:
        if "failedscript" in u:
            return False
        q = unquote(u)
        return f"from:{PROFILE_HANDLE}" in q or f"from%3a{PROFILE_HANDLE}" in q
    return False


def foreign_handle_in_url(url: str) -> str | None:
    m = _HANDLE_RX.search(url or "")
    if not m:
        return None
    h = m.group(1).lower()
    if h in (PROFILE_HANDLE, "search", "i", "intent", "share"):
        return None
    return h


def _log(msg: str) -> None:
    print(msg, flush=True)


def safe_goto(page, url: str, *, reason: str = "") -> None:
    """Yalnizca ekonomikocu / arama — baska profile gitme."""
    if not url_allowed(url) and not status_nav_allowed(page, url):
        home = getattr(page, "_eko_home", None)
        fh = foreign_handle_in_url(url)
        tag = f" (@{fh})" if fh else ""
        _log(f"  >> URL engellendi{tag}: {(url or '')[:85]}")
        if reason:
            _log(f"      ({reason})")
        if home and url_allowed(home):
            url = home
        else:
            url = f"https://x.com/{PROFILE_HANDLE}"
    page._eko_guard = True  # type: ignore[attr-defined]
    try:
        page.goto(url, wait_until="commit", timeout=120_000)
    finally:
        page._eko_guard = False  # type: ignore[attr-defined]


def nav_quiet(page, sec: float = 10.0) -> None:
    """SPA ara navigasyonlarina mudahale etme (status yukleme)."""
    page._eko_quiet_until = time.monotonic() + sec  # type: ignore[attr-defined]


def nav_quiet_active(page) -> bool:
    return time.monotonic() < getattr(page, "_eko_quiet_until", 0.0)


def release_status_page(page) -> None:
    page._eko_status_mode = False  # type: ignore[attr-defined]
    page._eko_status_url = None  # type: ignore[attr-defined]
    page._eko_guard = False  # type: ignore[attr-defined]


def recover_quote_status(page, tweet_id: str) -> None:
    """Splash/hata — profile donme, ayni tweet status sayfasini yenile."""
    from tweet_tara import status_url as _status_url, x_clear_error

    if _is_trap_url(page.url or ""):
        _log(f"  >> Premium/tuzak sayfa — status'a donuluyor: {tweet_id}")
    url = _status_url(tweet_id)
    page._eko_status_mode = True  # type: ignore[attr-defined]
    page._eko_status_url = url  # type: ignore[attr-defined]
    _log(f"  >> Status yenileniyor (profil degil): {tweet_id}")
    page._eko_guard = True  # type: ignore[attr-defined]
    try:
        page.goto(url, wait_until="commit", timeout=60_000)
        nav_quiet(page, 10.0)
        page.wait_for_timeout(2500)
        x_clear_error(page)
    except Exception as e:
        _log(f"  >> Status yenileme hatasi: {e}")
    finally:
        page._eko_guard = False  # type: ignore[attr-defined]


def bind_safe_page(page, home_url: str) -> None:
    """page.goto + framenavigated — yabanci hesap sayfalarini geri al."""
    if not url_allowed(home_url) or "/explore" in (home_url or "").lower():
        home_url = f"https://x.com/{PROFILE_HANDLE}"
    page._eko_home = home_url  # type: ignore[attr-defined]
    page._eko_guard = False  # type: ignore[attr-defined]
    page._eko_nav_last = 0.0  # type: ignore[attr-defined]
    page._eko_quiet_until = 0.0  # type: ignore[attr-defined]
    # failedScript/ana sayfa otomatik redirect donguye sokar — sadece yabanci URL engelle
    page._eko_passive_nav = True  # type: ignore[attr-defined]
    orig_goto = page.goto

    def guarded_goto(url: str, **kwargs):
        if getattr(page, "_eko_guard", False):
            return orig_goto(url, **kwargs)
        if not url_allowed(url) and not status_nav_allowed(page, str(url)):
            fh = foreign_handle_in_url(url)
            _log(f"  >> goto engellendi{f' (@{fh})' if fh else ''}: {str(url)[:85]}")
            url = page._eko_home  # type: ignore[attr-defined]
        page._eko_guard = True  # type: ignore[attr-defined]
        try:
            return orig_goto(url, **kwargs)
        finally:
            page._eko_guard = False  # type: ignore[attr-defined]

    page.goto = guarded_goto  # type: ignore[method-assign]

    def on_frame(frame):
        if frame != page.main_frame:
            return
        if getattr(page, "_eko_guard", False):
            return
        u = frame.url or ""
        if _is_trap_url(u):
            now = time.time()
            if now - getattr(page, "_eko_nav_last", 0) < 2.0:
                return
            page._eko_nav_last = now  # type: ignore[attr-defined]
            dest = _trap_recovery_dest(page)
            _log(f"  >> Premium/tuzak engellendi — geri: {(u or '')[:65]}")
            page._eko_guard = True  # type: ignore[attr-defined]
            try:
                orig_goto(dest, wait_until="commit", timeout=45_000)
                nav_quiet(page, 8.0)
                page.wait_for_timeout(1500)
            except Exception:
                pass
            finally:
                page._eko_guard = False  # type: ignore[attr-defined]
            return
        if nav_quiet_active(page):
            return
        passive = getattr(page, "_eko_passive_nav", True)
        if not passive:
            if "failedscript" in u.lower():
                now = time.time()
                debounce = 8.0 if getattr(page, "_eko_status_mode", False) else 5.0
                if now - getattr(page, "_eko_nav_last", 0) < debounce:
                    return
                page._eko_nav_last = now  # type: ignore[attr-defined]
                st = getattr(page, "_eko_status_url", None)
                if getattr(page, "_eko_status_mode", False) and st:
                    dest = st
                    _log("  >> Status failedScript — tweet sayfasi yenileniyor...")
                else:
                    dest = getattr(page, "_eko_home", None) or f"https://x.com/{PROFILE_HANDLE}"
                    _log("  >> X failedScript — profile donuluyor...")
                page._eko_guard = True  # type: ignore[attr-defined]
                try:
                    orig_goto(dest, wait_until="commit", timeout=90_000)
                    nav_quiet(page, 6.0 if st else 3.0)
                    page.wait_for_timeout(2500)
                except Exception:
                    pass
                finally:
                    page._eko_guard = False  # type: ignore[attr-defined]
                return
            if _is_x_home(u) and not getattr(page, "_eko_status_mode", False):
                now = time.time()
                if now - getattr(page, "_eko_nav_last", 0) < 3.0:
                    return
                page._eko_nav_last = now  # type: ignore[attr-defined]
                dest = getattr(page, "_eko_home", None) or f"https://x.com/{PROFILE_HANDLE}"
                _log("  >> X ana sayfa — ekonomikocu profiline cekiliyor...")
                page._eko_guard = True  # type: ignore[attr-defined]
                try:
                    orig_goto(dest, wait_until="commit", timeout=60_000)
                except Exception:
                    pass
                finally:
                    page._eko_guard = False  # type: ignore[attr-defined]
                return
        elif _is_x_home(u) or "/home" in u.lower():
            if getattr(page, "_eko_status_mode", False):
                st = getattr(page, "_eko_status_url", None)
                if st:
                    now = time.time()
                    if now - getattr(page, "_eko_nav_last", 0) < 3.0:
                        return
                    page._eko_nav_last = now  # type: ignore[attr-defined]
                    _log("  >> Ana sayfa — tweet status'a donuluyor...")
                    page._eko_guard = True  # type: ignore[attr-defined]
                    try:
                        orig_goto(st, wait_until="commit", timeout=45_000)
                        nav_quiet(page, 8.0)
                    except Exception:
                        pass
                    finally:
                        page._eko_guard = False  # type: ignore[attr-defined]
            return
        elif "failedscript" in u.lower() or "/explore" in u.lower():
            return
        if url_allowed(u) or status_nav_allowed(page, u):
            if f"/{PROFILE_HANDLE}" in u.lower() and "/explore" not in u.lower():
                page._eko_home = u  # type: ignore[attr-defined]
            return

        status_url = getattr(page, "_eko_status_url", None)
        if getattr(page, "_eko_status_mode", False) and is_any_status_url(u):
            return

        now = time.time()
        if now - getattr(page, "_eko_nav_last", 0) < 2.5:
            return
        page._eko_nav_last = now  # type: ignore[attr-defined]
        fh = foreign_handle_in_url(u)
        tag = "explore" if "/explore" in u.lower() else (f"@{fh}" if fh else "yabanci")
        _log(f"  >> Geri alindi ({tag}): {u[:70]}")
        home = getattr(page, "_eko_home", None) or f"https://x.com/{PROFILE_HANDLE}"
        dest = status_url or home
        if not url_allowed(dest):
            dest = f"https://x.com/{PROFILE_HANDLE}"
        page._eko_guard = True  # type: ignore[attr-defined]
        try:
            orig_goto(dest, wait_until="commit", timeout=60_000)
        except Exception:
            pass
        finally:
            page._eko_guard = False  # type: ignore[attr-defined]

    page.on("framenavigated", on_frame)


def page_stuck_loading(page) -> bool:
    """Siyah X logosu — tweet/article yuklenmedi."""
    try:
        if _is_trap_url(page.url or ""):
            return True
        if page.locator('article[data-testid="tweet"]').count() >= 1:
            return False
        u = (page.url or "").lower()
        if "x.com" not in u and "twitter.com" not in u:
            return False
        body_len = page.evaluate(
            "() => (document.body && document.body.innerText || '').trim().length"
        )
        if body_len and body_len > 120:
            return False
        return True
    except Exception:
        return True


class StallWatchdog:
    """Tarama ilerlemiyorsa (splash / donma) otomatik kurtar."""

    def __init__(self, stall_sec: float = 180.0, label: str = "bot") -> None:
        self.stall_sec = stall_sec
        self.label = label
        self._last = time.monotonic()
        self.recoveries = 0
        self.failed_recoveries = 0

    def ping(self) -> None:
        self._last = time.monotonic()
        self.failed_recoveries = 0

    def note_activity(self) -> None:
        """Ilerleme var ama basarisiz kurtarma sayacini sifirlama."""
        self._last = time.monotonic()

    def idle_sec(self) -> float:
        return time.monotonic() - self._last

    def needs_recovery(self) -> bool:
        return self.idle_sec() >= self.stall_sec

    def recover(self, page, home: str | None = None) -> bool:
        """Splash / donma — once mevcut sayfayi yenile, sonra profil. True = tweet var."""
        from tweet_tara import timeline_tweet_count, x_clear_error

        self.recoveries += 1
        _log(
            f"  >> WATCHDOG ({self.label}): {self.idle_sec():.0f}s ilerleme yok "
            f"— kurtarma #{self.recoveries}"
        )
        u = (page.url or "").lower()
        try:
            nav_quiet(page, 12.0)
            if "/status/" in u or "/i/status/" in u or page_stuck_loading(page):
                try:
                    page.reload(wait_until="commit", timeout=60_000)
                    page.wait_for_timeout(4000)
                    x_clear_error(page)
                    if timeline_tweet_count(page) >= 1 and not page_stuck_loading(page):
                        self.ping()
                        return True
                except Exception:
                    pass
            release_status_page(page)
            recover_x_page(page, home)
            ok = timeline_tweet_count(page) >= 1 and not page_stuck_loading(page)
            if ok:
                self.ping()
                return True
        except Exception as e:
            _log(f"  >> WATCHDOG kurtarma hatasi: {e}")
        self.failed_recoveries += 1
        self.note_activity()
        return False


def wait_status_ready(
    page,
    tweet_id: str,
    *,
    max_sec: float = 75.0,
    reload_at: float = 25.0,
    recover_at: float = 50.0,
) -> bool:
    """Status sayfasi splash'ta kalirsa yenile / profil kurtarma. False = tweet atla."""
    from tweet_tara import x_clear_error

    deadline = time.monotonic() + max_sec
    reloaded = recovered = False
    while time.monotonic() < deadline:
        try:
            if page.locator('article[data-testid="tweet"]').count() >= 1:
                return True
            if not page_stuck_loading(page):
                page.wait_for_timeout(800)
                if page.locator('article[data-testid="tweet"]').count() >= 1:
                    return True
        except Exception:
            pass
        elapsed = max_sec - (deadline - time.monotonic())
        if not reloaded and elapsed >= reload_at:
            reloaded = True
            _log(f"  >> Status splash ({tweet_id}) — sayfa yenileniyor...")
            try:
                page.reload(wait_until="commit", timeout=45_000)
                page.wait_for_timeout(2500)
                x_clear_error(page)
            except Exception:
                pass
            continue
        if not recovered and elapsed >= recover_at:
            recovered = True
            st = getattr(page, "_eko_status_url", None) or f"https://x.com/i/status/{tweet_id}"
            _log(f"  >> Status splash ({tweet_id}) — tweet sayfasi tekrar...")
            page._eko_guard = True  # type: ignore[attr-defined]
            try:
                page.goto(st, wait_until="commit", timeout=45_000)
                nav_quiet(page, 8.0)
                page.wait_for_timeout(3000)
                x_clear_error(page)
                if page.locator('article[data-testid="tweet"]').count() >= 1:
                    return True
            except Exception:
                pass
            finally:
                page._eko_guard = False  # type: ignore[attr-defined]
            return False
        page.wait_for_timeout(1500)
    _log(f"  >> Status zaman asimi ({tweet_id}) — atlaniyor.")
    return False


def recover_x_page(page, home: str | None = None) -> None:
    """Takili /status veya splash -> ekonomikocu profil."""
    from tweet_tara import (
        PROFILE_URL_POSTS,
        click_posts_tab,
        timeline_tweet_count,
        wait_for_profile_feed,
        x_clear_error,
    )

    dest = home or getattr(page, "_eko_home", None) or PROFILE_URL_POSTS
    if "/search" in (dest or "").lower():
        _log("  >> X takildi (splash) — arama akisina donuluyor...")
    else:
        _log("  >> X takildi (splash) — profil akisina donuluyor...")
    page._eko_status_mode = False  # type: ignore[attr-defined]
    page._eko_status_url = None  # type: ignore[attr-defined]

    def _try_load(url: str, label: str) -> int:
        try:
            u = (page.url or "").lower()
            if PROFILE_HANDLE in u and "/status/" not in u and page_stuck_loading(page):
                page.reload(wait_until="commit", timeout=60_000)
            else:
                safe_goto(page, url, reason=label)
            page.wait_for_timeout(4000)
            x_clear_error(page)
            if "/search" not in (url or "").lower():
                click_posts_tab(page)
                page.wait_for_timeout(2500)
                x_clear_error(page)
            page._eko_home = url  # type: ignore[attr-defined]
            return timeline_tweet_count(page)
        except Exception:
            return 0

    # Kurtarma hep profil — arama (search) failedScript dongusune sokar
    prof = PROFILE_URL_POSTS
    if "/search" in (dest or "").lower() or "failedscript" in (dest or "").lower():
        dest = prof
    page._eko_home = dest  # type: ignore[attr-defined]

    n = _try_load(dest, "splash-kurtarma")
    if n < 1 or page_stuck_loading(page):
        page.wait_for_timeout(2000)
        n = _try_load(dest, "splash-retry")
    if n < 1 or page_stuck_loading(page):
        _log("  >> Splash devam — profil sert yenileme...")
        for attempt in range(2):
            try:
                safe_goto(page, prof, reason="splash-sert")
                page.wait_for_timeout(2500)
                page.reload(wait_until="commit", timeout=60_000)
                page.wait_for_timeout(3000)
                x_clear_error(page)
                click_posts_tab(page)
                page.wait_for_timeout(2000)
                x_clear_error(page)
                page._eko_home = prof  # type: ignore[attr-defined]
                n = timeline_tweet_count(page)
                if n >= 1 and not page_stuck_loading(page):
                    break
            except Exception:
                pass
            if attempt == 0 and n < 1:
                page.wait_for_timeout(4000)
    if n < 1:
        wait_for_profile_feed(page, tries=8)
        n = timeline_tweet_count(page)
    _log(f"  >> Kurtarma sonrasi ekranda: {n} tweet")


def close_foreign_tabs(context, keep_page) -> None:
    """Fazla sekmeleri kapat; keep_page=None ise yalnizca yabanci URL sekmeleri."""
    for pg in list(context.pages):
        if keep_page is not None and pg is keep_page:
            continue
        u = pg.url or ""
        if keep_page is None and url_allowed(u):
            continue
        try:
            pg.close()
        except Exception:
            pass
