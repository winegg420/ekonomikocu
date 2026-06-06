#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@ekonomikocu profilini Playwright ile otomatik tarar (sizin X oturumunuz).

İlk çalıştırma:
  pip install -r requirements.txt
  playwright install chromium

Kullanım:
  python tweet_tara.py              # tarayıcı açılır, gerekirse X'e giriş yapın
  python tweet_tara.py --login-only # sadece giriş için pencere açık kalır
  python tweet_tara.py --dry-run      # hafızaya yazmaz, sadece önizleme
  python tweet_tara.py --max-scroll 80

Oturum klasörü: .x_session/ (bir kez giriş yeter, tekrar sormaz)
Ham çıktı: cekilen_tweetler.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import quote
from datetime import datetime, timezone
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
LEGACY_SESSION = ROOT / ".x_session"
SESSION_DIR = Path(os.environ.get("LOCALAPPDATA", str(ROOT))) / "ekonomikocu_x_session"
CDP_DEFAULT_PORT = 9222
PROFILE_HANDLE = "ekonomikocu"
PROFILE_URL = f"https://x.com/{PROFILE_HANDLE}/with_replies"
PROFILE_URL_POSTS = f"https://x.com/{PROFILE_HANDLE}"
SEARCH_URL = f"https://x.com/search?q=from%3A{PROFILE_HANDLE}&src=typed_query&f=live"


def search_period_url(since: str, until: str | None = None) -> str:
    """Ornek: since=2026-01-01 until=2026-02-01 -> Ocak 2026 tweetleri."""
    q = f"from:{PROFILE_HANDLE} since:{since}"
    if until:
        q += f" until:{until}"
    return f"https://x.com/search?q={quote(q)}&src=typed_query&f=live"


def status_url(tweet_id: str) -> str:
    """i/status — handle'siz; splash ve SPA redirect daha az takilir."""
    return f"https://x.com/i/status/{tweet_id}"


from alinti_common import (
    ERISILEMEDI,
    reset_erisilemedi_rows,
    row_quote_needs_visit,
    save_pending_list,
)
from tara_nav import (
    StallWatchdog,
    bind_safe_page,
    close_foreign_tabs,
    load_bookmark,
    page_stuck_loading,
    period_key,
    recover_x_page,
    safe_goto,
    save_bookmark,
    url_allowed,
    wait_status_ready,
)

JSONL_OUT = ROOT / "cekilen_tweetler.jsonl"
YANITLAR_OUT = ROOT / "cekilen_yanitlar.jsonl"
HAFIZA = ROOT / "ekonomikocu_hafiza_v1.md"
MEDYA_DIR = ROOT / "medya"

# hafiza_guncelle ile aynı güncelleme mantığı
from hafiza_guncelle import (
    FLOOD_MARKERS,
    LOCKED_MARKERS,
    TweetRecord,
    classify_products,
    classify_tip,
    detect_lang,
    rebuild_hafiza_md,
    try_parse_date,
    update_section_7_date,
)

CHROME_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=Translate,TranslateUI,TranslateBubble",
    "--disable-translate",
    "--lang=tr-TR",
    "--accept-lang=tr-TR",
    "--no-default-browser-check",
]

INIT_TR_JS = """
Object.defineProperty(navigator, 'language', { get: () => 'tr-TR' });
Object.defineProperty(navigator, 'languages', { get: () => ['tr-TR', 'tr'] });
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
"""

PLAYWRIGHT_IGNORE_ARGS = [
    "--enable-automation",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

ACCEPT_LANGUAGE = {"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.1"}


def purge_english_jsonl() -> int:
    kept = []
    for line in JSONL_OUT.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        if o.get("lang") == "en":
            continue
        kept.append(line)
    JSONL_OUT.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    print(f"Ingilizce silindi. Kalan: {len(kept)}")
    return len(kept)


def migrate_session_if_needed() -> None:
    """OneDrive icindeki eski .x_session -> LOCALAPPDATA (X kilitlenmesini azaltir)."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    if not LEGACY_SESSION.exists():
        return
    marker = SESSION_DIR / ".migrated_from_onedrive"
    if marker.exists():
        return
    try:
        for item in LEGACY_SESSION.iterdir():
            dest = SESSION_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        marker.write_text("ok", encoding="utf-8")
        _log(f"Oturum tasindi: {SESSION_DIR}")
    except OSError as e:
        _log(f"Oturum tasima atlandi: {e}")


def wipe_session() -> None:
    for p in (SESSION_DIR, LEGACY_SESSION):
        if p.exists():
            shutil.rmtree(p)
    print(f"Temizlendi: {SESSION_DIR} (yeni profil — cevirisi kapali giris)")


def _log(msg: str) -> None:
    print(msg, flush=True)


def wait_for_cdp_port(port: int, timeout_s: int = 90) -> bool:
    import urllib.error
    import urllib.request

    url = f"http://127.0.0.1:{port}/json/version"
    for i in range(timeout_s):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except (urllib.error.URLError, OSError, TimeoutError):
            if i and i % 10 == 0:
                _log(f"Chrome debug bekleniyor ({i}/{timeout_s}s)...")
            time.sleep(1)
    return False


def prepare_session_dir() -> None:
    """Kilitli script Chrome oturumunu kapat."""
    migrate_session_if_needed()
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    ps = (
        "$p = Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object { "
        "$_.Name -in @('chrome.exe','chromium.exe') -and ("
        "$_.CommandLine -like '*ekonomikocu_x_session*' -or $_.CommandLine -like '*x_session*' -or "
        "($_.CommandLine -like '*remote-debugging-port=9222*')"
        ") }; $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
    time.sleep(3)
    for base in (SESSION_DIR, SESSION_DIR / "Default"):
        if not base.is_dir():
            continue
        for name in ("SingletonLock", "SingletonCookie", "lockfile"):
            p = base / name
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
    _log("Profil hazir (oturum kilidi temizlendi).")


STATUS_ID_IN_TEXT = re.compile(r"(?:x\.com|twitter\.com)[^\s]*/status/(\d+)|/status/(\d+)", re.I)


def status_ids_in_text(text: str) -> list[str]:
    ids = []
    for m in STATUS_ID_IN_TEXT.finditer(text or ""):
        ids.append(m.group(1) or m.group(2))
    return ids


def x_clear_error(page) -> None:
    try:
        page.evaluate(RETRY_JS)
        page.evaluate(RECOVER_CLICK_JS)
        for label in (
            "Retry",
            "Yeniden dene",
            "Try again",
            "Tekrar dene",
            "Reload",
            "Yeniden yükle",
        ):
            loc = page.get_by_role("button", name=re.compile(label, re.I))
            if loc.count() > 0:
                loc.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                break
        for sel in (
            '[data-testid="empty_state"] button',
            '[data-testid="primaryColumn"] button',
            'a[href*="retry"]',
        ):
            loc = page.locator(sel)
            if loc.count() > 0:
                try:
                    loc.first.click(timeout=2000)
                    page.wait_for_timeout(1500)
                except Exception:
                    pass
        for txt in ("Retry", "Yeniden dene", "Try reloading", "Yeniden yükleyin"):
            loc = page.get_by_text(txt, exact=False)
            if loc.count() > 0:
                try:
                    loc.first.click(timeout=2000)
                    page.wait_for_timeout(2000)
                except Exception:
                    pass
    except Exception:
        pass


def page_shows_x_crash(page) -> bool:
    """Sadece akista tweet yokken hata say (yanlis alarmda surekli yenileme yapma)."""
    try:
        if timeline_tweet_count(page) >= 3:
            return False
        col = page.locator('[data-testid="primaryColumn"]')
        scope = col if col.count() > 0 else page
        for txt in (
            "Something went wrong",
            "Bir şeyler ters gitti",
            "Try reloading",
            "Yeniden yükleyin",
        ):
            if scope.get_by_text(txt, exact=False).count() > 0:
                return True
    except Exception:
        pass
    return False


def feed_needs_recovery(page) -> bool:
    return page_stuck_loading(page) or (
        timeline_tweet_count(page) < 2 and page_shows_x_crash(page)
    )


def ensure_feed_page(
    page, *, prefer_search: bool = False, search_url: str | None = None, profile_only: bool = False
) -> None:
    if profile_only or not prefer_search:
        ensure_profile_timeline(page)
        return
    feed = search_url or SEARCH_URL
    if not is_search_feed(page) or feed_needs_recovery(page):
        safe_goto(page, feed, reason="arama-akis")
        page.wait_for_timeout(5000)
        x_clear_error(page)
        page._eko_home = feed  # type: ignore[attr-defined]


def is_search_feed(page) -> bool:
    u = (page.url or "").lower()
    return "search" in u and PROFILE_HANDLE in u


def open_working_feed(
    context, page, *, first_url: str | None = None, feed_url: str | None = None
) -> object:
    """Ayni sekmede akisi yenile — sadece donem aramasi veya ekonomikocu profil."""
    close_foreign_tabs(context, page)
    u = (page.url or "").lower()
    on_eko = PROFILE_HANDLE in u and "/status/" not in u
    if not page_shows_x_crash(page) and timeline_tweet_count(page) >= 2:
        if on_eko:
            scroll_feed_deeper(page, passes=4)
            return page
        return page
    _log("Akis yenileniyor (tek sekme, sadece ekonomikocu)...")
    urls: list[str] = []
    if first_url and url_allowed(first_url):
        urls.append(first_url)
    if feed_url and feed_url not in urls and url_allowed(feed_url):
        urls.append(feed_url)
    if PROFILE_URL_POSTS not in urls:
        urls.append(PROFILE_URL_POSTS)
    for url in urls:
        try:
            safe_goto(page, url, reason="akis-yenile")
            page.wait_for_timeout(5000)
            click_posts_tab(page)
            x_clear_error(page)
            page.wait_for_timeout(2500)
            if timeline_tweet_count(page) >= 1 and not page_shows_x_crash(page):
                _log(f"Akis OK: {url[:70]}")
                try:
                    page.bring_to_front()
                except Exception:
                    pass
                return page
        except Exception as e:
            _log(f"  atla {url}: {e}")
    return page


def fix_x_crash(page, context=None) -> bool:
    if not page_shows_x_crash(page) and timeline_tweet_count(page) >= 2:
        return True
    _log("X hata — otomatik duzeltme...")
    x_clear_error(page)
    page.wait_for_timeout(2000)
    if timeline_tweet_count(page) >= 2 and not page_shows_x_crash(page):
        return True
    if context is not None:
        return False
    try:
        page.reload(wait_until="commit", timeout=90_000)
        page.wait_for_timeout(5000)
        x_clear_error(page)
    except Exception:
        pass
    return timeline_tweet_count(page) >= 1 and not page_shows_x_crash(page)


def click_posts_tab(page) -> None:
    try:
        for name in ("Posts", "Gönderiler", "Postlar"):
            tab = page.get_by_role("tab", name=re.compile(name, re.I))
            if tab.count() > 0:
                tab.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                return
    except Exception:
        pass


def click_replies_tab(page) -> None:
    try:
        for name in ("Replies", "Yanıtlar", "Yanitlar", "Cevaplar"):
            tab = page.get_by_role("tab", name=re.compile(name, re.I))
            if tab.count() > 0:
                tab.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                return
    except Exception:
        pass


def pick_profile_page(context) -> object:
    """CDP: en cok tweet olan ekonomikocu sekmesini sec."""
    best = None
    best_n = -1
    profile_status = None
    x_tab = None
    for pg in context.pages:
        u = (pg.url or "").lower()
        if "ekonomikocu" not in u:
            if "x.com" in u or "twitter.com" in u:
                x_tab = x_tab or pg
            continue
        if "/status/" in u:
            profile_status = profile_status or pg
            continue
        try:
            n = pg.locator('article[data-testid="tweet"]').count()
        except Exception:
            n = 0
        if n > best_n:
            best_n = n
            best = pg
    if best:
        return best
    if profile_status and "ekonomikocu" in (profile_status.url or "").lower():
        return profile_status
    _log("Ekonomikocu sekmesi yok — profil aciliyor (tek sekme).")
    close_foreign_tabs(context, None)
    pg = None
    for p in context.pages:
        if PROFILE_HANDLE in (p.url or "").lower():
            pg = p
            break
    if not pg:
        pg = x_tab or (context.pages[0] if context.pages else None)
    if not pg:
        try:
            pg = context.new_page()
        except Exception:
            raise RuntimeError(
                "Chrome sekmesi acilamadi — CHROME_X.bat ile tek pencere acik birakin."
            )
    try:
        safe_goto(pg, PROFILE_URL_POSTS, reason="profil-ac")
    except Exception:
        pass
    return pg


def profile_feed_ready(page) -> bool:
    return timeline_tweet_count(page) >= 1


def wait_for_profile_feed(page, tries: int = 12) -> bool:
    """Retry tikla; sayfayi yenileme (ustteki abone tweetlerinde takilmayi bozar)."""
    for i in range(tries):
        n = timeline_tweet_count(page)
        if n >= 1:
            if i > 0:
                _log(f"Akis hazir ({n} tweet ekranda).")
            return True
        if i == 0 or (i + 1) % 4 == 0:
            _log(f"Akis bekleniyor ({i + 1}/{tries})...")
        x_clear_error(page)
        click_posts_tab(page)
        page.wait_for_timeout(2000)
    return timeline_tweet_count(page) >= 1


def ensure_profile_timeline(page) -> None:
    """Tek tweet (/status/) sayfasina sapmissa profil/arama akisina don."""
    url = (page.url or "").lower()
    if is_search_feed(page):
        return
    if "/status/" in url or "/statuses/" in url:
        safe_goto(page, PROFILE_URL_POSTS, reason="status-don")
        page.wait_for_timeout(3500)
        return
    if "ekonomikocu" not in url:
        safe_goto(page, PROFILE_URL_POSTS, reason="yabanci-don")
        page.wait_for_timeout(3500)


def timeline_tweet_count(page) -> int:
    try:
        col = page.locator('[data-testid="primaryColumn"]')
        if col.count() > 0:
            return col.locator('article[data-testid="tweet"]').count()
        return page.locator('article[data-testid="tweet"]').count()
    except Exception:
        return 0


def page_has_x_error(page) -> bool:
    """Sadece akista tweet yokken hata say (girisli ama yanlis alarm olmasin)."""
    try:
        n = timeline_tweet_count(page)
        if n >= 3:
            return False
        col = page.locator('[data-testid="primaryColumn"]')
        scope = col if col.count() > 0 else page
        for txt in ("Something went wrong", "Bir şeyler ters gitti", "Try reloading", "Yeniden yükleyin"):
            if scope.locator(f"text={txt}").count() > 0:
                return True
    except Exception:
        pass
    return False


def is_on_login_screen(page) -> bool:
    try:
        url = (page.url or "").lower()
        if "i/flow/login" in url:
            return True
        if re.search(r"(?:x|twitter)\.com/login(?:/|$|\?)", url):
            return True
        return page.locator('[data-testid="loginButton"]').count() > 0 and (
            page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count() == 0
        )
    except Exception:
        return False


def is_logged_in(page, *, trust_session: bool = False) -> bool:
    """CDP oturumunda X zaten acik — login ekrani disinda girisli kabul et."""
    try:
        if is_on_login_screen(page):
            return False
        if trust_session:
            url = (page.url or "").lower()
            return "x.com" in url or "twitter.com" in url
        if page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count() > 0:
            return True
        if page.locator('[data-testid="AppTabBar_Profile_Link"]').count() > 0:
            return True
        if page.locator('article[data-testid="tweet"]').count() > 0:
            return True
        if page.locator('[data-testid="primaryColumn"]').count() > 0:
            return True
        return trust_session
    except Exception:
        return trust_session

ORIGINAL_JS = """
() => {
  document.querySelectorAll('button, a, span, div[role="button"], [role="menuitem"]').forEach(el => {
    const t = (el.innerText || '').trim();
    if (/orijinal|original|çeviriyi göster|show original|view original|never translate|hiç çevirme|cevirme/i.test(t)) {
      try { el.click(); } catch(e) {}
    }
  });
}
"""


def force_turkish_on_page(page) -> None:
    try:
        page.evaluate(ORIGINAL_JS)
        page.wait_for_timeout(400)
    except Exception:
        pass

EXPAND_JS = """
() => {
  // Abonelik duvarini asmak icin: kart uzerinde "Subscribe to unlock / Abonelere özel" benzeri butonlari tıkla.
  const rxUnlock = /(abonelere|abone ol|subscribe to unlock|unlock this post|subscribers only|kilidi|bu gönderinin tamamı|read full)/i;
  const nodes = document.querySelectorAll('button, a, [role="button"], div[role="button"]');
  for (const el of nodes) {
    const t = (el.innerText || '').trim();
    if (!t) continue;
    if (/^subscribed$/i.test(t) || /^subscribers$/i.test(t)) continue;
    if (rxUnlock.test(t)) {
      try { el.click(); } catch(e) {}
    }
  }

  document.querySelectorAll('article[data-testid="tweet"]').forEach(a => {
    a.querySelectorAll('[role="button"], span').forEach(b => {
      const t = (b.innerText || '').toLowerCase();
      if (t === 'show more' || t === 'daha fazla göster') try { b.click(); } catch(e) {}
    });
  });
}
"""

RETRY_JS = """
() => {
  const rx = /^\\s*(retry|yeniden dene|try again|tekrar dene)\\s*$/i;
  document.querySelectorAll('[role="alert"] button, [data-testid="empty_state_body_text"] ~ * button').forEach(el => {
    const t = (el.innerText || '').trim();
    if (rx.test(t)) try { el.click(); } catch(e) {}
  });
}
"""

RECOVER_CLICK_JS = """
() => {
  const rx = /^(retry|yeniden dene|try again|reload|yeniden yükleyin)$/i;
  const nodes = document.querySelectorAll(
    'button, a, [role="button"], div[role="button"]'
  );
  for (const el of nodes) {
    const t = (el.innerText || '').trim();
    if (rx.test(t) || /^retry$/i.test(t)) {
      try { el.click(); return true; } catch (e) {}
    }
  }
  const primary = document.querySelector('[data-testid="primaryColumn"]');
  if (primary) {
    for (const el of primary.querySelectorAll('button')) {
      const t = (el.innerText || '').trim();
      if (/retry|yeniden/i.test(t)) {
        try { el.click(); return true; } catch (e) {}
      }
    }
  }
  return false;
}
"""

SCROLL_JS = """
() => {
  const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
  if (arts.length) {
    arts[arts.length - 1].scrollIntoView({ block: 'end', behavior: 'instant' });
  }
  const col = document.querySelector('[data-testid="primaryColumn"]')
    || document.querySelector('main[role="main"]')
    || document.querySelector('main');
  const scrollers = [];
  let p = col;
  while (p) {
    if (p.scrollHeight > p.clientHeight + 60) scrollers.push(p);
    p = p.parentElement;
  }
  const targets = scrollers.length ? scrollers : (col ? [col] : []);
  const step = (t) => {
    for (let i = 0; i < 3; i++) {
      t.scrollBy(0, 900);
    }
    t.scrollTop = t.scrollHeight;
  };
  for (const t of targets) step(t);
  if (arts.length) {
    arts[Math.min(arts.length - 1, 2)].scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
}
"""

LOCKED_RX_JS = (
    "subscriber|subscribers only|abonelere|abone ol|subscribe to unlock|"
    "abone only|unlock this post|kilidi|bu gönderinin tamamı"
)

# Abone oturumunda tweetText doluysa kilitli sayma (ust bant "Abonelere ozel" kirintisi)
LOCKED_DETECT_JS = """
const isLockedArticle = (raw, mainText) => {
  const t = (mainText || '').trim();
  // Abone oturumunda metin DOM'da varsa kilit sayma (kisa basliklar dahil).
  if (t.length >= 6) return false;
  return lockedRx.test(raw || '');
};
"""


def feed_mostly_locked(page) -> bool:
    try:
        return bool(
            page.evaluate(
                f"""() => {{
          const rx = /{LOCKED_RX_JS}/i;
          const arts = [...document.querySelectorAll('article[data-testid="tweet"]')];
          if (arts.length < 2) return false;
          const locked = arts.filter(a => rx.test((a.innerText || '').slice(0, 2000))).length;
          return locked >= Math.max(2, arts.length - 1);
        }}"""
            )
        )
    except Exception:
        return False


def aggressive_timeline_scroll(page) -> None:
    """Yavas insan kaydirma — X 'Something went wrong' azalir, daha cok tweet yuklenir."""
    page.evaluate(SCROLL_JS)
    for _ in range(3):
        try:
            page.mouse.wheel(0, 1100)
        except Exception:
            break
        page.wait_for_timeout(900)


def scroll_feed_deeper(page, *, passes: int = 8) -> None:
    """Profil basina DONMEDEN asagi in (durak #3 dongusunu kirar)."""
    page.evaluate(RETRY_JS)
    for _ in range(passes):
        aggressive_timeline_scroll(page)
        page.wait_for_timeout(2800)
        page.evaluate(EXPAND_JS)
    try:
        page.keyboard.press("PageDown")
        page.keyboard.press("PageDown")
        page.keyboard.press("End")
    except Exception:
        pass

EXTRACT_JS = f"""
() => {{
  const lockedRx = /{LOCKED_RX_JS}/i;
  {LOCKED_DETECT_JS}
  const out = [];
  const seen = new Set();
  const pickMedia = (root) => {{
    if (!root) return [];
    const urls = [];
    const seenU = new Set();
    for (const img of root.querySelectorAll('img[src]')) {{
      let src = (img.src || '').trim();
      if (!src || seenU.has(src)) continue;
      if (!/twimg\\.com|pbs\\.twimg/i.test(src)) continue;
      if (/profile_images|emoji|verified|twemoji|card_icon/i.test(src)) continue;
      src = src.replace(/&name=\\w+$/, '&name=large');
      seenU.add(src);
      urls.push(src);
    }}
    return urls;
  }};
  const push = (row) => {{
    if (!row.id || seen.has(row.id)) return;
    seen.add(row.id);
    out.push(row);
  }};
  const isEkoArticle = (article) => {{
    for (const a of article.querySelectorAll('a[href]')) {{
      const h = (a.getAttribute('href') || '');
      if (/\\/ekonomikocu(\\/|$|\\?)/i.test(h)) return true;
      if (/x\\.com\\/ekonomikocu|twitter\\.com\\/ekonomikocu/i.test(h)) return true;
    }}
    return false;
  }};
  for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {{
    if (!isEkoArticle(article)) continue;
    const raw = (article.innerText || '').slice(0, 8000);
    const links = [...article.querySelectorAll('a[href*="/status/"]')];
    const ids = links.map(a => (a.href.match(/status\\/(\\d+)/) || [])[1]).filter(Boolean);
    const timeEl = article.querySelector('time');
    const mainId = ids[0] || null;
    const texts = [...article.querySelectorAll('[data-testid="tweetText"]')].map(e => e.innerText);
    const mainText = texts[0] || '';
    const locked = isLockedArticle(raw, mainText);
    const socialEl = article.querySelector('[data-testid="socialContext"]');
    const socialTxt = socialEl ? (socialEl.innerText || '') : '';
    let inReplyToHandle = null;
    if (/replying to|yanıt olarak|yanit olarak|cevap olarak/i.test(socialTxt)) {{
      const m = socialTxt.match(/@([\\w_]+)/i);
      if (m) inReplyToHandle = m[1].toLowerCase();
    }}
    const needsThread = !locked && (
      /#FLOOD|\\/flood\\b/i.test(mainText) ||
      /show this thread|bu konuyu göster|diğer gönderiler|more posts from/i.test(socialTxt)
    );
    if (mainId) {{
      push({{
        id: mainId,
        datetime: timeEl ? timeEl.getAttribute('datetime') : null,
        text: locked ? '' : mainText,
        locked,
        isQuote: false,
        quoteOf: null,
        quotedBy: null,
        threadRoot: null,
        inReplyToHandle,
        needsThread,
        media: pickMedia(article),
        role: 'main'
      }});
    }}
    const quoteBox = article.querySelector('[data-testid="quoteTweet"]')
      || article.querySelector('[data-testid="card.wrapper"]')
      || article.querySelector('div[role="link"][tabindex="0"]');
    let qId = null, qTime = null, qText = null, qLocked = false;
    if (quoteBox) {{
      const qRaw = (quoteBox.innerText || '').slice(0, 4000);
      const qLink = quoteBox.querySelector('a[href*="/status/"]');
      qId = qLink ? (qLink.href.match(/status\\/(\\d+)/) || [])[1] : null;
      qTime = quoteBox.querySelector('time');
      const qEl = quoteBox.querySelector('[data-testid="tweetText"]');
      qText = qEl ? qEl.innerText : '';
      qLocked = isLockedArticle(qRaw, qText);
    }}
    const uniqIds = [...new Set(ids)];
    if (!qId && uniqIds.length >= 2 && mainId) {{
      qId = uniqIds.find(x => x !== mainId) || null;
      if (qId && texts.length > 1) qText = texts[1];
    }}
    if (qId && qId !== mainId) {{
      if (qText === null) qText = '';
      qLocked = isLockedArticle('', qText);
      push({{
        id: qId,
        datetime: qTime ? qTime.getAttribute('datetime') : null,
        text: qLocked ? '' : qText,
        locked: qLocked,
        isQuote: true,
        quoteOf: null,
        quotedBy: mainId,
        threadRoot: null,
        needsThread: false,
        quoteStub: true,
        media: [],
        role: 'quote'
      }});
    }}
  }}
  return out;
}}
"""

UNAVAILABLE_JS = """
() => {
  const articles = document.querySelectorAll('article[data-testid="tweet"]');
  if (articles.length > 0) return false;
  const t = (document.body.innerText || '').slice(0, 12000);
  return /doesn't exist|does not exist|Tweet yok|bulunamıyor|bulunamadi|unavailable|Account suspended/i.test(t);
}
"""

THREAD_EXTRACT_JS = f"""
(rootId) => {{
  const HANDLE = '{PROFILE_HANDLE}';
  const lockedRx = /{LOCKED_RX_JS}/i;
  {LOCKED_DETECT_JS}
  const out = [];
  const seen = new Set();
  const pickMedia = (root) => {{
    if (!root) return [];
    const urls = [];
    const seenU = new Set();
    for (const img of root.querySelectorAll('img[src]')) {{
      let src = (img.src || '').trim();
      if (!src || seenU.has(src)) continue;
      if (!/twimg\\.com|pbs\\.twimg/i.test(src)) continue;
      if (/profile_images|emoji|verified|twemoji|card_icon/i.test(src)) continue;
      src = src.replace(/&name=\\w+$/, '&name=large');
      seenU.add(src);
      urls.push(src);
    }}
    return urls;
  }};
  const push = (row) => {{
    if (!row.id || seen.has(row.id)) return;
    seen.add(row.id);
    out.push(row);
  }};
  const isAuthor = (article) => {{
    return !!article.querySelector(
      `a[href="/${{HANDLE}}"], a[href*="/${{HANDLE}}/"], a[href$="/${{HANDLE}}"]`
    );
  }};
  for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {{
    if (!isAuthor(article)) continue;
    const raw = (article.innerText || '').slice(0, 8000);
    const timeEl = article.querySelector('time');
    let mainId = null;
    for (const a of article.querySelectorAll('a[href*="/status/"]')) {{
      const m = a.href.match(/{PROFILE_HANDLE}\\/status\\/(\\d+)/);
      if (m) {{ mainId = m[1]; break; }}
    }}
    if (!mainId) {{
      const a = article.querySelector('a[href*="/status/"]');
      const m = a ? (a.href.match(/status\\/(\\d+)/) || [])[1] : null;
      mainId = m;
    }}
    const texts = [...article.querySelectorAll('[data-testid="tweetText"]')];
    const mainText = texts[0] ? texts[0].innerText : '';
    const locked = isLockedArticle(raw, mainText);
    if (!mainId) continue;
    push({{
      id: mainId,
      datetime: timeEl ? timeEl.getAttribute('datetime') : null,
      text: locked ? '' : mainText,
      locked,
      isQuote: false,
      quoteOf: null,
      quotedBy: null,
      threadRoot: rootId,
      needsThread: false,
      media: pickMedia(article),
      role: 'thread'
    }});
  }}
  return out;
}}
"""

QUOTE_STATUS_EXTRACT_JS = f"""
(targetId) => {{
  const lockedRx = /{LOCKED_RX_JS}/i;
  {LOCKED_DETECT_JS}
  const out = [];
  const seen = new Set();
  const pickMedia = (root) => {{
    if (!root) return [];
    const urls = [];
    const seenU = new Set();
    for (const img of root.querySelectorAll('img[src]')) {{
      let src = (img.src || '').trim();
      if (!src || seenU.has(src)) continue;
      if (!/twimg\\.com|pbs\\.twimg/i.test(src)) continue;
      if (/profile_images|emoji|verified|twemoji|card_icon/i.test(src)) continue;
      src = src.replace(/&name=\\w+$/, '&name=large');
      seenU.add(src);
      urls.push(src);
    }}
    return urls;
  }};
  const push = (row) => {{
    if (!row.id || seen.has(row.id)) return;
    seen.add(row.id);
    out.push(row);
  }};
  const articleHasId = (article, id) => {{
    for (const a of article.querySelectorAll('a[href*="/status/"]')) {{
      const m = (a.href.match(/status\\/(\\d+)/) || [])[1];
      if (m === id) return true;
    }}
    return false;
  }};
  for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {{
    if (!articleHasId(article, targetId)) continue;
    const raw = (article.innerText || '').slice(0, 12000);
    const timeEl = article.querySelector('time');
    const texts = [...article.querySelectorAll('[data-testid="tweetText"]')].map(e => e.innerText);
    const mainText = texts[0] || '';
    const locked = isLockedArticle(raw, mainText);
    push({{
      id: targetId,
      datetime: timeEl ? timeEl.getAttribute('datetime') : null,
      text: locked ? '' : mainText,
      locked,
      isQuote: true,
      quoteOf: null,
      quotedBy: null,
      threadRoot: null,
      needsThread: !locked && /#FLOOD|\\/flood\\b/i.test(mainText),
      media: pickMedia(article),
      role: 'quote-deep'
    }});
    const quoteBox = article.querySelector('[data-testid="quoteTweet"]');
    if (quoteBox) {{
      const qRaw = (quoteBox.innerText || '').slice(0, 4000);
      const qLink = quoteBox.querySelector('a[href*="/status/"]');
      const qId = qLink ? (qLink.href.match(/status\\/(\\d+)/) || [])[1] : null;
      const qTime = quoteBox.querySelector('time');
      const qText = quoteBox.querySelector('[data-testid="tweetText"]');
      const qBody = qText ? qText.innerText : '';
      const qLocked = isLockedArticle(qRaw, qBody);
      if (qId && qId !== targetId) {{
        push({{
          id: qId,
          datetime: qTime ? qTime.getAttribute('datetime') : null,
          text: qLocked ? '' : qBody,
          locked: qLocked,
          isQuote: true,
          quoteOf: targetId,
          quotedBy: targetId,
          threadRoot: null,
          needsThread: false,
          media: pickMedia(quoteBox || article),
          role: 'quote-nested'
        }});
      }}
    }}
    break;
  }}
  return out;
}}
"""

MAIN_STATUS_EXTRACT_JS = f"""
(targetId) => {{
  const lockedRx = /{LOCKED_RX_JS}/i;
  {LOCKED_DETECT_JS}
  const pickMedia = (root) => {{
    if (!root) return [];
    const urls = [];
    const seenU = new Set();
    for (const img of root.querySelectorAll('img[src]')) {{
      let src = (img.src || '').trim();
      if (!src || seenU.has(src)) continue;
      if (!/twimg\\.com|pbs\\.twimg/i.test(src)) continue;
      if (/profile_images|emoji|verified|twemoji|card_icon/i.test(src)) continue;
      src = src.replace(/&name=\\w+$/, '&name=large');
      seenU.add(src);
      urls.push(src);
    }}
    return urls;
  }};
  const articleHasId = (article, id) => {{
    for (const a of article.querySelectorAll('a[href*="/status/"]')) {{
      const m = (a.href.match(/status\\/(\\d+)/) || [])[1];
      if (m === id) return true;
    }}
    return false;
  }};
  for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {{
    if (!articleHasId(article, targetId)) continue;
    const raw = (article.innerText || '').slice(0, 12000);
    const timeEl = article.querySelector('time');
    const quoteBox = article.querySelector('[data-testid="quoteTweet"]');
    const texts = [...article.querySelectorAll('[data-testid="tweetText"]')]
      .filter(e => !quoteBox || !quoteBox.contains(e))
      .map(e => e.innerText);
    const mainText = texts.join('\\n\\n').trim();
    const locked = isLockedArticle(raw, mainText);
    return [{{
      id: targetId,
      datetime: timeEl ? timeEl.getAttribute('datetime') : null,
      text: locked ? '' : mainText,
      locked,
      isQuote: false,
      quoteOf: null,
      quotedBy: null,
      threadRoot: null,
      needsThread: !locked && /#FLOOD|\\/flood\\b/i.test(mainText),
      media: pickMedia(article),
      role: 'status-target'
    }}];
  }}
  return [];
}}
"""

CONVERSATION_EXTRACT_JS = f"""
(rootId) => {{
  const EKO = '{PROFILE_HANDLE}';
  const lockedRx = /{LOCKED_RX_JS}/i;
  {LOCKED_DETECT_JS}
  const out = [];
  const seen = new Set();
  const pickAuthor = (article) => {{
    const nameBox = article.querySelector('[data-testid="User-Name"]');
    if (nameBox) {{
      for (const a of nameBox.querySelectorAll('a[href^="/"]')) {{
        const h = (a.getAttribute('href') || '').replace(/^\\//, '').split('/')[0].split('?')[0];
        if (h && !/^(status|i|search|hashtag|home|explore)$/i.test(h)) return h.toLowerCase();
      }}
    }}
    for (const a of article.querySelectorAll('a[href^="/"]')) {{
      const h = (a.getAttribute('href') || '').replace(/^\\//, '').split('/')[0].split('?')[0];
      if (h && h.length > 1 && !/^(status|i|search|hashtag|home|explore|compose)$/i.test(h))
        return h.toLowerCase();
    }}
    return '';
  }};
  const pickId = (article) => {{
    for (const a of article.querySelectorAll('a[href*="/status/"]')) {{
      const m = (a.href.match(/status\\/(\\d+)/) || [])[1];
      if (m) return m;
    }}
    return null;
  }};
  for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {{
    const id = pickId(article);
    if (!id || seen.has(id)) continue;
    const quoteBox = article.querySelector('[data-testid="quoteTweet"]');
    const texts = [...article.querySelectorAll('[data-testid="tweetText"]')]
      .filter(e => !quoteBox || !quoteBox.contains(e))
      .map(e => e.innerText);
    const text = texts.join('\\n\\n').trim();
    if (!text) continue;
    const author = pickAuthor(article);
    const raw = (article.innerText || '').slice(0, 6000);
    const locked = author === EKO ? isLockedArticle(raw, text) : false;
    const timeEl = article.querySelector('time');
    const socialEl = article.querySelector('[data-testid="socialContext"]');
    const social = socialEl ? (socialEl.innerText || '') : '';
    let inReplyToHandle = null;
    if (/replying to|yanıt olarak|yanit olarak|cevap olarak/i.test(social)) {{
      const m = social.match(/@([\\w_]+)/i);
      if (m) inReplyToHandle = m[1].toLowerCase();
    }}
    seen.add(id);
    out.push({{
      id,
      author,
      datetime: timeEl ? timeEl.getAttribute('datetime') : null,
      text: locked ? '' : text,
      locked,
      conversationRoot: rootId,
      inReplyToHandle,
      isEko: author === EKO,
      isQuote: false,
      role: 'conversation'
    }});
  }}
  return out;
}}
"""

PARENT_QUOTE_EXTRACT_JS = f"""
(args) => {{
  const parentId = args[0];
  const quoteId = args[1];
  const lockedRx = /{LOCKED_RX_JS}/i;
  {LOCKED_DETECT_JS}
  const pickMedia = (root) => {{
    if (!root) return [];
    const urls = [];
    const seenU = new Set();
    for (const img of root.querySelectorAll('img[src]')) {{
      let src = (img.src || '').trim();
      if (!src || seenU.has(src)) continue;
      if (!/twimg\\.com|pbs\\.twimg/i.test(src)) continue;
      if (/profile_images|emoji|verified|twemoji|card_icon/i.test(src)) continue;
      src = src.replace(/&name=\\w+$/, '&name=large');
      seenU.add(src);
      urls.push(src);
    }}
    return urls;
  }};
  const articleHasId = (article, id) => {{
    for (const a of article.querySelectorAll('a[href*="/status/"]')) {{
      const m = (a.href.match(/status\\/(\\d+)/) || [])[1];
      if (m === id) return true;
    }}
    return false;
  }};
  for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {{
    if (!articleHasId(article, parentId)) continue;
    const quoteBox = article.querySelector('[data-testid="quoteTweet"]')
      || article.querySelector('[data-testid="card.wrapper"]');
    if (!quoteBox) return null;
    const qLink = quoteBox.querySelector('a[href*="/status/"]');
    const qId = qLink ? (qLink.href.match(/status\\/(\\d+)/) || [])[1] : null;
    if (qId !== quoteId) return null;
    const qRaw = (quoteBox.innerText || '').slice(0, 12000);
    const qTime = quoteBox.querySelector('time');
    const qEl = quoteBox.querySelector('[data-testid="tweetText"]');
    const qText = qEl ? qEl.innerText : '';
    const qLocked = isLockedArticle(qRaw, qText);
    return {{
      id: quoteId,
      datetime: qTime ? qTime.getAttribute('datetime') : null,
      text: qLocked ? '' : qText,
      locked: qLocked,
      isQuote: true,
      quotedBy: parentId,
      quoteStub: false,
      media: pickMedia(quoteBox),
      role: 'quote-from-koc-page'
    }};
  }}
  return null;
}}
"""


def load_existing_rows(path: Path) -> dict[str, dict]:
    """Mevcut jsonl -> tarama sozlugu (kaldigi yerden devam)."""
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        tid = o.get("tweet_id")
        if not tid:
            continue
        out[tid] = {
            "id": tid,
            "datetime": o.get("datetime"),
            "text": o.get("text") or "",
            "locked": o.get("locked", False),
            "isQuote": o.get("is_quote", False),
            "quotedBy": o.get("quoted_by"),
            "quoteOf": o.get("quote_of"),
            "quoteStub": o.get("quote_stub", False),
            "threadRoot": o.get("thread_root"),
            "media": o.get("media_urls") or [],
            "mediaFiles": o.get("media_files") or [],
            "needsThread": False,
            "role": "saved",
        }
    return out


def load_existing_replies(path: Path = YANITLAR_OUT) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        rid = o.get("reply_id") or o.get("tweet_id") or o.get("id")
        if not rid:
            continue
        out[rid] = {
            "id": rid,
            "author": (o.get("author") or "").lower(),
            "datetime": o.get("datetime"),
            "text": o.get("text") or "",
            "conversationRoot": o.get("conversation_root"),
            "inReplyToHandle": o.get("in_reply_to_handle"),
            "isEko": bool(o.get("is_eko")),
            "locked": o.get("locked", False),
            "kayitTipi": o.get("kayit_tipi") or "yanit",
            "role": "saved-reply",
        }
    return out


def _is_eko_author(row: dict) -> bool:
    return (row.get("author") or "").lower() == PROFILE_HANDLE or bool(row.get("isEko"))


def filter_eko_yanit_ve_sorular(batch: list[dict], root_id: str) -> list[dict]:
    """Yalnizca eko yanitlari + eko'nun cevap verdigi sorular (digerleri atlanir)."""
    if not batch:
        return []
    eko_yanitlar = [
        r
        for r in batch
        if _is_eko_author(r)
        and (
            r.get("inReplyToHandle")
            or (r.get("id") != root_id and r.get("id") != r.get("conversationRoot"))
        )
    ]
    if not eko_yanitlar:
        return []
    answered_handles = {
        (r.get("inReplyToHandle") or "").lower()
        for r in eko_yanitlar
        if r.get("inReplyToHandle")
    }
    out: list[dict] = []
    seen: set[str] = set()
    for raw in batch:
        r = dict(raw)
        rid = r.get("id")
        if not rid or rid in seen:
            continue
        if _is_eko_author(r):
            if r.get("id") == root_id and not r.get("inReplyToHandle"):
                continue
            r["kayitTipi"] = "eko_yanit"
            r["isEko"] = True
            r["author"] = PROFILE_HANDLE
            out.append(r)
            seen.add(rid)
        elif (r.get("inReplyToHandle") or "").lower() == PROFILE_HANDLE:
            r["kayitTipi"] = "soru"
            r["isEko"] = False
            out.append(r)
            seen.add(rid)
        elif (r.get("author") or "").lower() in answered_handles:
            r["kayitTipi"] = "soru"
            r["isEko"] = False
            out.append(r)
            seen.add(rid)
    return out


def merge_eko_profile_replies(all_replies: dict[str, dict], batch: list[dict]) -> int:
    """Yanitlar sekmesindeki @ekonomikocu cevap tweetlerini kaydet."""
    rows: list[dict] = []
    for raw in batch:
        if raw.get("isQuote"):
            continue
        text = (raw.get("text") or "").strip()
        tid = raw.get("id")
        if not tid or not text:
            continue
        rows.append(
            {
                "id": tid,
                "author": PROFILE_HANDLE,
                "datetime": raw.get("datetime"),
                "text": text,
                "conversationRoot": raw.get("threadRoot"),
                "inReplyToHandle": raw.get("inReplyToHandle"),
                "isEko": True,
                "locked": bool(raw.get("locked")),
                "kayitTipi": "eko_yanit",
                "role": "eko-yanit-profil",
            }
        )
    return merge_replies(all_replies, rows)


def merge_replies(all_replies: dict[str, dict], batch: list[dict]) -> int:
    new_n = 0
    for raw in batch:
        rid = raw.get("id")
        text = (raw.get("text") or "").strip()
        if not rid or not text:
            continue
        row = {
            "id": rid,
            "author": (raw.get("author") or "").lower(),
            "datetime": raw.get("datetime"),
            "text": text,
            "conversationRoot": raw.get("conversationRoot"),
            "inReplyToHandle": raw.get("inReplyToHandle"),
            "isEko": bool(raw.get("isEko")),
            "locked": bool(raw.get("locked")),
            "kayitTipi": raw.get("kayitTipi") or raw.get("kayit_tipi") or "yanit",
            "role": raw.get("role") or "conversation",
        }
        prev = all_replies.get(rid)
        if prev:
            if len((prev.get("text") or "")) > len(text):
                row["text"] = prev.get("text") or text
            row["author"] = row["author"] or prev.get("author")
            row["conversationRoot"] = row.get("conversationRoot") or prev.get("conversationRoot")
            row["inReplyToHandle"] = row.get("inReplyToHandle") or prev.get("inReplyToHandle")
        else:
            new_n += 1
        all_replies[rid] = row
    return new_n


def save_replies_jsonl(rows: list[dict], path: Path = YANITLAR_OUT) -> None:
    records = []
    for row in rows:
        records.append(
            {
                "reply_id": row.get("id"),
                "author": row.get("author") or "",
                "datetime": row.get("datetime"),
                "date_label": format_date_label(dt_from_iso(row.get("datetime"))),
                "text": row.get("text") or "",
                "conversation_root": row.get("conversation_root") or row.get("conversationRoot"),
                "in_reply_to_handle": row.get("in_reply_to_handle") or row.get("inReplyToHandle"),
                "is_eko": bool(row.get("is_eko") if "is_eko" in row else row.get("isEko")),
                "locked": bool(row.get("locked")),
                "kayit_tipi": row.get("kayitTipi") or row.get("kayit_tipi") or "yanit",
                "lang": detect_lang(row.get("text") or ""),
            }
        )
    records.sort(key=lambda r: r.get("datetime") or "", reverse=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + ("\n" if records else ""),
        encoding="utf-8",
    )


def merge_conversation_page(
    page,
    root_id: str,
    all_rows: dict[str, dict],
    all_replies: dict[str, dict],
) -> int:
    """Eko yanitlari + cevaplanan sorular; cevapsiz ucuncu taraf mesajlari atlanir."""
    try:
        batch = page.evaluate(CONVERSATION_EXTRACT_JS, root_id)
    except Exception:
        return 0
    batch = filter_eko_yanit_ve_sorular(batch, root_id)
    if not batch:
        return 0
    n_rep = merge_replies(all_replies, batch)
    eko_rows = []
    for raw in batch:
        if not _is_eko_author(raw):
            continue
        tid = raw.get("id")
        text = (raw.get("text") or "").strip()
        if not tid or not text:
            continue
        prev = all_rows.get(tid)
        if prev and (prev.get("text") or "").strip():
            continue
        eko_rows.append(
            {
                "id": tid,
                "datetime": raw.get("datetime"),
                "text": text,
                "locked": False,
                "isQuote": False,
                "quotedBy": None,
                "quoteOf": None,
                "threadRoot": root_id if tid != root_id else None,
                "needsThread": False,
                "media": [],
                "role": "eko-reply",
            }
        )
    if eko_rows:
        merge_rows(all_rows, eko_rows, page=None)
    return n_rep


def read_stop_from_hafiza(md: str) -> datetime | None:
    """Hafızadaki 'işlenen aralık' satırının SON tarihini oku (yıl dahil)."""
    m = re.search(
        r"işlenen aralık:\*\*\s*[^→]+→\s*([^\n(]+)",
        md,
        re.I,
    )
    if not m:
        return None
    label = m.group(1).strip()
    dt, _ = try_parse_date(label)
    if dt:
        return dt
    # Yedek: dört haneli yıl ara
    ym = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", label)
    if ym:
        day, mon, year = int(ym.group(1)), ym.group(2), int(ym.group(3))
        from hafiza_guncelle import normalize_month

        month = normalize_month(mon)
        if month:
            return datetime(year, month, day)
    return None


def dt_from_iso(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        s = iso.replace("Z", "+00:00")
        return datetime.fromisoformat(s).astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None


def format_date_label(dt: datetime | None) -> str:
    if not dt:
        return "tarih-belirsiz"
    tr_months = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    mon = tr_months[dt.month - 1]
    return f"{dt.day} {mon} {dt.hour:02d}:{dt.minute:02d}"


def normalize_scraped_row(row: dict) -> dict:
    """Kilitli: metin bos; uydurma yok."""
    locked = bool(row.get("locked"))
    text = (row.get("text") or "").strip()
    if len(text) >= 6:
        locked = False
    elif not locked and text:
        locked = bool(LOCKED_MARKERS.search(text))
    if locked:
        text = ""
    row = dict(row)
    row["locked"] = locked
    row["text"] = text
    return row


def row_needs_thread(row: dict) -> bool:
    if row.get("isQuote") or row.get("role") == "quote":
        return False
    if row.get("needsThread"):
        return True
    return bool(re.search(r"#FLOOD|/flood\b", row.get("text") or "", re.I))


def download_tweet_media(page, tweet_id: str, urls: list) -> list[str]:
    """Her grafik/foto -> medya/{tweet_id}/graf_01.jpg"""
    if not urls or not tweet_id:
        return []
    out_dir = MEDYA_DIR / tweet_id
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    try:
        from grafik_filtre import is_irrelevant_media_url
    except ImportError:
        is_irrelevant_media_url = lambda _u: False  # type: ignore[misc, assignment]

    for i, url in enumerate(urls[:24], 1):
        if not url or not isinstance(url, str):
            continue
        if is_irrelevant_media_url(url):
            continue
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        path = out_dir / f"graf_{i:02d}{ext}"
        if path.exists() and path.stat().st_size > 800:
            saved.append(str(path.relative_to(ROOT)).replace("\\", "/"))
            continue
        try:
            resp = page.request.get(url, timeout=45_000)
            if resp.ok and len(resp.body()) > 400:
                path.write_bytes(resp.body())
                saved.append(str(path.relative_to(ROOT)).replace("\\", "/"))
                _log(f"  >> Medya: {path.name} ({tweet_id})")
        except Exception as e:
            _log(f"  >> Medya atlandi ({tweet_id} graf_{i:02d}): {e}")
    return saved


def persist_media_for_rows(page, rows: dict[str, dict], only_ids: set[str] | None = None) -> None:
    for tid, row in rows.items():
        if only_ids is not None and tid not in only_ids:
            continue
        urls = row.get("media") or []
        if not urls:
            continue
        files = download_tweet_media(page, tid, urls)
        if files:
            row["mediaFiles"] = files


def _merge_media_fields(prev: dict | None, row: dict) -> None:
    pm = list(prev.get("media") or []) if prev else []
    nm = list(row.get("media") or [])
    merged: list[str] = []
    seen: set[str] = set()
    for u in pm + nm:
        if u and u not in seen:
            seen.add(u)
            merged.append(u)
    if merged:
        row["media"] = merged
    if prev and prev.get("mediaFiles"):
        row["mediaFiles"] = prev.get("mediaFiles")


def _ids_needing_media_download(all_rows: dict[str, dict], tids: set[str]) -> set[str]:
    need: set[str] = set()
    for tid in tids:
        row = all_rows.get(tid) or {}
        urls = row.get("media") or []
        if not urls:
            continue
        files = row.get("mediaFiles") or []
        if len(files) < len(urls):
            need.add(tid)
    return need


def merge_rows(
    all_rows: dict[str, dict],
    batch: list[dict],
    page=None,
    *,
    period_since: datetime | None = None,
    period_until: datetime | None = None,
) -> int:
    new_n = 0
    touched: set[str] = set()
    for raw in batch:
        row = normalize_scraped_row(raw)
        tid = row.get("id")
        if not tid:
            continue
        if period_since or period_until:
            d = dt_from_iso(row.get("datetime"))
            if d:
                dn = d.replace(tzinfo=None) if d.tzinfo else d
                if period_since and dn < period_since.replace(tzinfo=None):
                    continue
                if period_until and dn >= period_until.replace(tzinfo=None):
                    continue
        prev = all_rows.get(tid)
        _merge_media_fields(prev, row)
        if prev:
            if prev.get("locked") and (row.get("text") or "").strip():
                row["locked"] = False
            if prev.get("text") and not row.get("text") and not row.get("locked"):
                row["text"] = prev["text"]
            pt, nt = (prev.get("text") or "").strip(), (row.get("text") or "").strip()
            if len(nt) > len(pt):
                pass
            elif len(pt) > len(nt):
                row["text"] = prev["text"]
            row["quotedBy"] = row.get("quotedBy") or prev.get("quotedBy")
            row["isQuote"] = bool(row.get("isQuote") or prev.get("isQuote"))
            if not row.get("datetime"):
                row["datetime"] = prev.get("datetime")
            if not row.get("threadRoot"):
                row["threadRoot"] = prev.get("threadRoot")
            if prev.get("quoteStub") and not row.get("quoteStub") and (row.get("text") or "").strip():
                row["quoteStub"] = False
            elif (row.get("text") or "").strip() and len((row.get("text") or "")) >= 80:
                row["quoteStub"] = False
        else:
            new_n += 1
        touched.add(tid)
        all_rows[tid] = row
    if page and touched:
        need = _ids_needing_media_download(all_rows, touched)
        if need:
            persist_media_for_rows(page, all_rows, need)
    return new_n


def collect_quote_jobs(
    all_rows: dict[str, dict], batch: list[dict], quotes_done: set[str]
) -> list[tuple[str, str | None]]:
    jobs: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for row in batch:
        row = normalize_scraped_row(row)
        tid = row.get("id")
        if tid and row.get("isQuote") and row_quote_needs_visit(row) and tid not in quotes_done:
            if tid not in seen:
                seen.add(tid)
                jobs.append((tid, row.get("quotedBy")))
    for tid, row in all_rows.items():
        if tid in quotes_done:
            continue
        if row_quote_needs_visit(row) and tid not in seen:
            seen.add(tid)
            jobs.append((tid, row.get("quotedBy")))
    return jobs


def run_period_profile_fallback(
    page,
    all_rows: dict[str, dict],
    since_dt: datetime,
    until_dt: datetime,
    *,
    max_scroll: int = 280,
) -> int:
    """Profil kaydir: yalnizca [since, until) tweetleri al (Mart/Ocak gibi bos donemler)."""
    _log(
        f"Profil donem modu: {since_dt.date()} — {until_dt.date()} "
        f"(max {max_scroll} scroll)"
    )
    safe_goto(page, PROFILE_URL_POSTS, reason="donem-profil")
    page.wait_for_timeout(4000)
    click_posts_tab(page)
    x_clear_error(page)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1500)
    wait_for_profile_feed(page, tries=15)
    added_before = len(all_rows)
    total_in_period = 0
    stale = 0
    since_naive = since_dt.replace(tzinfo=None)
    until_naive = until_dt.replace(tzinfo=None)
    for i in range(max_scroll):
        if page_stuck_loading(page):
            recover_x_page(page)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(2000)
        page.evaluate(RETRY_JS)
        force_turkish_on_page(page)
        page.evaluate(EXPAND_JS)
        batch = page.evaluate(EXTRACT_JS)
        merge_rows(
            all_rows,
            batch,
            page=page,
            period_since=since_dt,
            period_until=until_dt,
        )
        batch_oldest = batch_newest = None
        in_period = 0
        for raw in batch:
            d = dt_from_iso(raw.get("datetime"))
            if not d:
                continue
            dn = d.replace(tzinfo=None)
            if since_naive <= dn < until_naive:
                in_period += 1
            if batch_oldest is None or dn < batch_oldest:
                batch_oldest = dn
            if batch_newest is None or dn > batch_newest:
                batch_newest = dn
        total_in_period += in_period
        stale = 0 if in_period else stale + 1
        _log(
            f"  Donem profil {i + 1}/{max_scroll}: +{len(all_rows) - added_before} toplam | "
            f"ekranda donem: {in_period} | en eski: {batch_oldest} | en yeni: {batch_newest}"
        )
        # Donemden cikildi: once donemde tweet gorduk, simdi daha eski batch
        if batch_oldest and batch_oldest < since_naive and total_in_period > 0:
            _log(f"  >> {since_dt.date()} oncesine ulasildi — donem profil bitti.")
            break
        # Feed basta 2020 vb. takili — uste cek, kaydirmaya devam (erken cikma yok)
        if batch_oldest and batch_oldest < since_naive and total_in_period == 0:
            if (i + 1) % 12 == 0:
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(2000)
                scroll_feed_deeper(page, passes=6)
        if stale >= 50 and total_in_period > 0:
            _log("  >> 50 scroll donemde yeni yok — sonraki adima geciliyor.")
            break
        aggressive_timeline_scroll(page)
        page.wait_for_timeout(2800)
    return len(all_rows) - added_before


def goto_status(page, tweet_id: str, *, fast: bool = False) -> None:
    """Status sayfasi — SPA kesintilerine karsi deneme."""
    url = status_url(tweet_id)
    page._eko_status_mode = True  # type: ignore[attr-defined]
    page._eko_status_url = url  # type: ignore[attr-defined]
    page._eko_guard = True  # type: ignore[attr-defined]
    last_err: Exception | None = None
    wait_until = "domcontentloaded"
    timeout = 60_000 if fast else 90_000
    tries = 3
    pause = 1000 if fast else 1500
    try:
        for attempt in range(tries):
            try:
                page.goto(url, wait_until=wait_until, timeout=timeout)
                page.wait_for_timeout(pause)
                x_clear_error(page)
                if page_stuck_loading(page) and attempt < tries - 1:
                    _log(f"  >> Status splash ({tweet_id}) — reload ({attempt + 1})")
                    page.reload(wait_until=wait_until, timeout=timeout)
                    page.wait_for_timeout(pause)
                    x_clear_error(page)
                cur = page.url or ""
                if tweet_id in cur or page.locator('article[data-testid="tweet"]').count() >= 1:
                    return
            except Exception as e:
                last_err = e
                page.wait_for_timeout(1200)
        if last_err:
            raise last_err
    finally:
        page._eko_guard = False  # type: ignore[attr-defined]


def _locked_empty_count(all_rows: dict[str, dict]) -> int:
    return sum(
        1
        for r in all_rows.values()
        if r.get("locked") and not (r.get("text") or "").strip()
    )


def refill_locked_profile_scroll(
    page,
    all_rows: dict[str, dict],
    *,
    since: datetime,
    max_scroll: int = 450,
    save_cb=None,
) -> int:
    """Profil kaydirarak abone tweet metinlerini toplu kaydet (status'tan daha guvenilir)."""
    safe_goto(page, PROFILE_URL_POSTS, reason="abone-profil")
    page.wait_for_timeout(3000)
    click_posts_tab(page)
    x_clear_error(page)
    if not wait_for_profile_feed(page, tries=20):
        _log("Abone profil akisi hazir degil.")
        return 0
    done = 0
    stale = 0
    _log(f"Abone profil kaydirma: max {max_scroll} scroll (>= {since.date()})...")
    for i in range(max_scroll):
        if page_stuck_loading(page):
            recover_x_page(page)
            if not wait_for_profile_feed(page, tries=8):
                _log("  >> Profil splash — kaydirma durdu.")
                break
        locked_before = _locked_empty_count(all_rows)
        page.evaluate(RETRY_JS)
        force_turkish_on_page(page)
        page.evaluate(EXPAND_JS)
        page.wait_for_timeout(500)
        batch = page.evaluate(EXTRACT_JS)
        merge_rows(all_rows, batch, page=None, period_since=since)
        locked_after = _locked_empty_count(all_rows)
        gained = locked_before - locked_after
        if gained:
            done += gained
            stale = 0
            if save_cb:
                save_cb(all_rows)
        else:
            stale += 1
        if (i + 1) % 10 == 0:
            _log(
                f"  Abone profil {i + 1}/{max_scroll}: +{done} metin | "
                f"kalan bos kilitli: {locked_after}"
            )
        if locked_after == 0:
            _log("  >> Tum abone tweetleri profil kaydirmada metin alindi.")
            break
        if stale >= 40:
            _log("  >> 40 scroll metin gelmedi — status adimina gecilecek.")
            break
        aggressive_timeline_scroll(page)
        page.wait_for_timeout(2200)
    if save_cb:
        save_cb(all_rows)
    return done


def refill_locked_since(
    page,
    all_rows: dict[str, dict],
    *,
    since: datetime,
    limit: int = 800,
    return_url: str | None = None,
    only_locked: bool = False,
    save_cb=None,
    reply_rows: dict[str, dict] | None = None,
    save_reply_cb=None,
    capture_conversation: bool = False,
    fast: bool = True,
    watchdog: StallWatchdog | None = None,
) -> int:
    """Abone oturumunda kilitli/bos tweet metnini status sayfasindan kaydet."""
    if reply_rows is None:
        reply_rows = {}
    if watchdog is None:
        watchdog = StallWatchdog(stall_sec=180.0, label="abone")
    jobs: list[str] = []
    for tid, row in all_rows.items():
        if not tid or not tid.isdigit():
            continue
        d = dt_from_iso(row.get("datetime"))
        if not d or d.replace(tzinfo=None) < since.replace(tzinfo=None):
            continue
        text = (row.get("text") or "").strip()
        if only_locked:
            if row.get("locked") and not text:
                jobs.append(tid)
        elif row.get("locked") or not text or text == ERISILEMEDI:
            jobs.append(tid)
    jobs = sorted(set(jobs), key=int, reverse=True)[:limit]
    if not jobs:
        return 0
    back = return_url or PROFILE_URL_POSTS
    done = 0
    _log(f"Abone tweet metni: {len(jobs)} adet (>= {since.date()})...")
    for i, tid in enumerate(jobs, 1):
        try:
            if watchdog.needs_recovery():
                watchdog.recover(page, back)
            goto_status(page, tid, fast=fast)
            if page_stuck_loading(page):
                if not wait_status_ready(page, tid, max_sec=75.0):
                    watchdog.note_activity()
                    continue
            else:
                try:
                    page.wait_for_selector('article[data-testid="tweet"]', timeout=6_000)
                except Exception:
                    if page_stuck_loading(page) and not wait_status_ready(page, tid, max_sec=45.0):
                        watchdog.note_activity()
                        continue
            page.wait_for_timeout(700 if fast else 900)
            page.evaluate(RETRY_JS)
            if not fast or i % 5 == 1:
                force_turkish_on_page(page)
            page.evaluate(EXPAND_JS)
            if not fast:
                page.wait_for_timeout(400)
                page.evaluate(EXPAND_JS)
            batch = page.evaluate(MAIN_STATUS_EXTRACT_JS, tid)
            if not batch:
                batch = page.evaluate(EXTRACT_JS)
            if batch:
                merge_rows(all_rows, batch, page=None)
            if capture_conversation and reply_rows is not None:
                merge_conversation_page(page, tid, all_rows, reply_rows)
            row = all_rows.get(tid) or {}
            got = (row.get("text") or "").strip()
            if got and len(got) >= 5:
                row["locked"] = False
                row["abone_metin"] = True
                row["kayit_tipi"] = "abone"
                all_rows[tid] = row
                done += 1
                if save_cb and (done % 15 == 0 or i == len(jobs)):
                    save_cb(all_rows)
                if save_reply_cb and reply_rows and (done % 15 == 0 or i == len(jobs)):
                    save_reply_cb(reply_rows)
                watchdog.ping()
            if i % 15 == 0:
                _log(f"  >> Abone metin: {done}/{i} ({tid})")
            watchdog.ping()
        except Exception as e:
            _log(f"  >> Abone atlandi ({tid}): {e}")
            err = str(e).lower()
            if page_stuck_loading(page) or "execution context was destroyed" in err:
                watchdog.recover(page, back)
            watchdog.ping()
    page._eko_status_mode = False  # type: ignore[attr-defined]
    page._eko_status_url = None  # type: ignore[attr-defined]
    if save_cb:
        save_cb(all_rows)
    if save_reply_cb and reply_rows:
        save_reply_cb(reply_rows)
    try:
        page.goto(back, wait_until="commit", timeout=60_000)
        page.wait_for_timeout(800)
    except Exception:
        pass
    return done


def backfill_missing_media(
    page,
    all_rows: dict[str, dict],
    *,
    limit: int = 200,
    return_url: str | None = None,
) -> int:
    """Eksik grafikleri tek sekmede ekonomikocu/status ile indir."""
    jobs = _ids_needing_media_download(all_rows, set(all_rows.keys()))
    jobs = sorted(jobs, key=lambda x: int(x) if x.isdigit() else 0, reverse=True)[:limit]
    if not jobs:
        return 0
    back = return_url or PROFILE_URL_POSTS
    done = 0
    _log(f"Medya geri indirme: {len(jobs)} tweet...")
    for tid in jobs:
        try:
            page.goto(status_url(tid), wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(2000)
            page.evaluate(RETRY_JS)
            page.evaluate(EXPAND_JS)
            merge_rows(all_rows, page.evaluate(EXTRACT_JS), page=page)
            merge_rows(
                all_rows,
                page.evaluate(THREAD_EXTRACT_JS, all_rows.get(tid, {}).get("threadRoot") or tid),
                page=page,
            )
            done += 1
        except Exception as e:
            _log(f"  >> Medya atlandi ({tid}): {e}")
    try:
        page.goto(back, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(1500)
    except Exception:
        pass
    return done


def crawl_thread(page, root_id: str, all_rows: dict[str, dict]) -> int:
    """#FLOOD / thread kok tweet -> status sayfasindan tum parcalar."""
    _log(f"  >> Thread: {root_id}")
    try:
        if page_stuck_loading(page):
            recover_x_page(page)
        safe_goto(page, status_url(root_id), reason="thread")
        page.wait_for_timeout(2500)
        if page_stuck_loading(page):
            recover_x_page(page)
            return 0
        page.evaluate(RETRY_JS)
        page.evaluate(EXPAND_JS)
        for _ in range(4):
            page.evaluate(SCROLL_JS)
            page.wait_for_timeout(800)
        merge_rows(all_rows, page.evaluate(EXTRACT_JS), page=page)
        n = merge_rows(all_rows, page.evaluate(THREAD_EXTRACT_JS, root_id), page=page)
        ensure_profile_timeline(page)
        wait_for_profile_feed(page, tries=8)
        return n
    except Exception as e:
        _log(f"  >> Thread hata ({root_id}): {e}")
        try:
            ensure_profile_timeline(page)
        except Exception:
            pass
        return 0


def _finalize_quote_if_still_empty(
    page, quote_id: str, quoted_by: str | None, all_rows: dict[str, dict]
) -> None:
    """Ziyaret sonrasi hala bos/kesikse kilitle veya erisilemedi isaretle."""
    row = all_rows.get(quote_id) or {}
    if not row_quote_needs_visit(row):
        return
    text = (row.get("text") or "").strip()
    if text and text != ERISILEMEDI:
        return
    locked = False
    try:
        locked = bool(
            page.evaluate(
                f"""() => {{
                  const rx = /{LOCKED_RX_JS}/i;
                  const a = document.querySelector('article[data-testid="tweet"]');
                  return a ? rx.test((a.innerText || '').slice(0, 6000)) : false;
                }}"""
            )
        )
    except Exception:
        pass
    merge_rows(
        all_rows,
        [
            {
                "id": quote_id,
                "datetime": row.get("datetime"),
                "text": "" if locked else ERISILEMEDI,
                "locked": locked,
                "isQuote": True,
                "quotedBy": quoted_by,
                "quoteStub": False,
                "role": "quote-finalize",
            }
        ],
    )
    _log(f"  >> Alinti isaretlendi ({'kilitli' if locked else 'erisilemedi'}): {quote_id}")


def _extract_quote_on_page(page, quote_id: str, quoted_by: str | None) -> dict | None:
    page.evaluate(RETRY_JS)
    page.evaluate(EXPAND_JS)
    try:
        page.wait_for_selector('article[data-testid="tweet"]', timeout=15_000)
    except Exception:
        pass
    for _ in range(3):
        page.evaluate(EXPAND_JS)
        page.wait_for_timeout(400)
    if quoted_by:
        row = page.evaluate(PARENT_QUOTE_EXTRACT_JS, [quoted_by, quote_id])
        if row:
            return row
    parts = page.evaluate(QUOTE_STATUS_EXTRACT_JS, quote_id)
    for p in parts:
        if p.get("id") == quote_id:
            p["isQuote"] = True
            p["quoteStub"] = False
            if quoted_by:
                p["quotedBy"] = quoted_by
            return p
    return None


def crawl_quote(
    page,
    quote_id: str,
    quoted_by: str | None,
    all_rows: dict[str, dict],
    threads_done: set[str],
    *,
    return_to_feed: bool = True,
    allow_foreign: bool = False,
) -> int:
    """Asama 2: once Koç'un tweet sayfasi; baska hesaba gitme (varsayilan kapali)."""
    try:
        if page_stuck_loading(page):
            recover_x_page(page)
        if quoted_by:
            _log(f"  >> Alinti {quote_id} — sadece ekonomikocu/status/{quoted_by}")
            safe_goto(page, status_url(quoted_by), reason="alinti-ana")
            page.wait_for_timeout(3500)
            if page_stuck_loading(page):
                recover_x_page(page)
                safe_goto(page, status_url(quoted_by), reason="alinti-retry")
                page.wait_for_timeout(3500)
            row = _extract_quote_on_page(page, quote_id, quoted_by)
            if row:
                merge_rows(all_rows, [row], page=page)
                if not row_quote_needs_visit(all_rows.get(quote_id, row)):
                    return 1
            if not allow_foreign:
                _finalize_quote_if_still_empty(page, quote_id, quoted_by, all_rows)
                _log(f"  >> Baska hesap sayfasi acilmadi (Koç sayfasindaki metin kullanildi)")
                return 1

        return 0
    except Exception as e:
        _log(f"  >> Alinti hata ({quote_id}): {e}")
        if return_to_feed:
            try:
                ensure_profile_timeline(page)
            except Exception:
                pass
        return 0


def flush_quotes(
    page,
    all_rows: dict[str, dict],
    quotes_done: set[str],
    threads_done: set[str],
    limit: int = 15,
    *,
    return_to_feed: bool = True,
    allow_foreign: bool = False,
) -> int:
    jobs = collect_quote_jobs(all_rows, [], quotes_done)[:limit]
    if not jobs:
        return 0
    visited = 0
    for qid, qb in jobs:
        if not row_quote_needs_visit(all_rows.get(qid, {"id": qid, "isQuote": True})):
            quotes_done.add(qid)
            continue
        crawl_quote(
            page,
            qid,
            qb,
            all_rows,
            threads_done,
            return_to_feed=return_to_feed,
            allow_foreign=allow_foreign,
        )
        visited += 1
        row = all_rows.get(qid, {})
        if not row_quote_needs_visit(row):
            quotes_done.add(qid)
    save_pending_list(all_rows)
    return visited


def finish_threads_loop(
    page,
    all_rows: dict[str, dict],
    threads_done: set[str],
    *,
    limit: int = 200,
    return_url: str | None = None,
) -> None:
    """#FLOOD — ayni sekmede sadece ekonomikocu/status."""
    jobs = [
        r.get("id")
        for r in all_rows.values()
        if r.get("id") and row_needs_thread(r) and r.get("id") not in threads_done
    ][:limit]
    if not jobs:
        return
    back = return_url or PROFILE_URL_POSTS
    for root_id in jobs:
        threads_done.add(root_id)
        _log(f"  >> #FLOOD thread: {root_id}")
        try:
            crawl_thread(page, root_id, all_rows)
        except Exception as e:
            _log(f"  >> Thread atlandi ({root_id}): {e}")
    try:
        page.goto(back, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(2000)
    except Exception:
        pass


def finish_quotes_loop(
    page,
    all_rows: dict[str, dict],
    quotes_done: set[str],
    threads_done: set[str],
    *,
    max_rounds: int = 12,
    per_round: int = 35,
    allow_foreign: bool = False,
    return_url: str | None = None,
) -> None:
    """Alintilar — ayni sekme, sadece ekonomikocu/status (baska hesap yok)."""
    back = return_url or PROFILE_URL_POSTS
    for rnd in range(1, max_rounds + 1):
        pending = len(collect_quote_jobs(all_rows, [], quotes_done))
        if not pending:
            _log("Alintilar tamam (bekleyen yok).")
            break
        _log(f"Asama 2 tur {rnd}: {pending} alinti bekliyor...")
        n = flush_quotes(
            page,
            all_rows,
            quotes_done,
            threads_done,
            limit=per_round,
            return_to_feed=False,
            allow_foreign=allow_foreign,
        )
        pending_after = len(collect_quote_jobs(all_rows, [], quotes_done))
        _log(f"  >> Bu turda ziyaret: {n} | kalan: {pending_after}")
        if pending_after == 0:
            break
        if pending_after >= pending:
            _log("  >> Ilerleme yok — kalanlar isaretleniyor.")
            for qid, qb in collect_quote_jobs(all_rows, [], quotes_done):
                _finalize_quote_if_still_empty(page, qid, qb, all_rows)
                quotes_done.add(qid)
            break
    try:
        page.goto(back, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(2000)
    except Exception:
        pass


def scraped_to_records(rows: list[dict]) -> list[TweetRecord]:
    by_id: dict[str, TweetRecord] = {}
    for row in rows:
        row = normalize_scraped_row(row)
        tid = row.get("id")
        if not tid:
            continue
        text = (row.get("text") or "").strip()
        locked = bool(row.get("locked"))
        dt = dt_from_iso(row.get("datetime"))
        is_quote = bool(row.get("isQuote"))
        quoted_by = row.get("quotedBy")
        thread_root = row.get("threadRoot")
        if is_quote and quoted_by:
            tip = "asıl (alıntı — ayrı satır)"
        elif thread_root and thread_root != tid:
            tip = "flood" if FLOOD_MARKERS.search(text) else "flood-parça"
        elif thread_root == tid and FLOOD_MARKERS.search(text):
            tip = "flood"
        else:
            tip = classify_tip(text, locked, is_quote)
        lang = detect_lang(text)
        if lang == "en" and re.search(r"[ğıüşöçİĞÜŞÖÇ]", text):
            lang = "tr"
        products = classify_products(text)
        rec = TweetRecord(
            tweet_id=tid,
            dt=dt,
            date_label=format_date_label(dt),
            locked=locked,
            text=text,
            products=products,
            tip=tip,
            icerik_tip=[],
            is_quote=is_quote,
            quoted_by=quoted_by,
            quote_of=row.get("quoteOf"),
            thread_root=row.get("threadRoot"),
            lang=row.get("lang") or detect_lang(text),
            analyzed=bool(row.get("analyzed")),
            fiyat=row.get("fiyat") or "—",
            sonra=row.get("sonra") or "—",
            sonuc=row.get("sonuc") or "",
            baglanti=row.get("baglanti") or "",
            media_urls=row.get("media") or [],
            media_files=row.get("mediaFiles") or [],
        )
        from tip_icerik import apply_to_record

        apply_to_record(rec)
        by_id[tid] = rec
    records = list(by_id.values())
    records.sort(key=lambda r: r.sort_key(), reverse=True)
    return records


def load_jsonl(path: Path) -> list[TweetRecord]:
    from tip_icerik import record_from_json_obj

    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(record_from_json_obj(json.loads(line)))
    records.sort(key=lambda r: r.sort_key(), reverse=True)
    return records


def save_jsonl(records: list[TweetRecord], path: Path) -> None:
    existing: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                obj = json.loads(line)
                existing[obj["tweet_id"]] = obj
    for rec in records:
        if not rec.tweet_id:
            continue
        prev = existing.get(rec.tweet_id, {})
        if rec.lang == "en" and prev.get("lang") == "tr" and (prev.get("text") or "").strip():
            continue
        if rec.lang == "en" and not (prev.get("text") or "").strip():
            continue
        from tip_icerik import apply_to_record

        apply_to_record(rec)
        existing[rec.tweet_id] = {
            "tweet_id": rec.tweet_id,
            "datetime": rec.dt.isoformat() if rec.dt else None,
            "date_label": rec.date_label,
            "locked": rec.locked,
            "text": rec.text,
            "products": rec.products,
            "tip": rec.icerik_tip or ["yorum"],
            "kayit_tipi": rec.tip or prev.get("kayit_tipi") or "yorum",
            "lang": rec.lang,
            "analyzed": rec.analyzed or prev.get("analyzed", False),
            "is_quote": rec.is_quote or prev.get("is_quote", False),
            "quoted_by": rec.quoted_by or prev.get("quoted_by"),
            "quote_of": rec.quote_of or prev.get("quote_of"),
            "quote_stub": (
                prev.get("quote_stub", False)
                if rec.is_quote
                and row_quote_needs_visit(
                    {
                        "id": rec.tweet_id,
                        "isQuote": True,
                        "text": rec.text,
                        "datetime": rec.dt.isoformat() if rec.dt else None,
                        "locked": rec.locked,
                    }
                )
                else False
            ),
            "thread_root": rec.thread_root or prev.get("thread_root"),
            "fiyat": rec.fiyat or prev.get("fiyat", "—"),
            "sonra": rec.sonra or prev.get("sonra", "—"),
            "sonuc": rec.sonuc or prev.get("sonuc", ""),
            "baglanti": rec.baglanti or prev.get("baglanti", ""),
            "media_urls": rec.media_urls or prev.get("media_urls") or [],
            "media_files": rec.media_files or prev.get("media_files") or [],
            "abone_metin": bool(prev.get("abone_metin") or getattr(rec, "abone_metin", False)),
            "abone_donemi": bool(
                prev.get("abone_donemi")
                or (rec.dt and rec.dt.isoformat() >= "2026-04-01")
            ),
        }
        if prev.get("kayit_tipi") == "abone" or prev.get("abone_metin"):
            existing[rec.tweet_id]["kayit_tipi"] = "abone"
            existing[rec.tweet_id]["abone_metin"] = True
    ordered = sorted(
        existing.values(),
        key=lambda x: x.get("datetime") or "",
        reverse=True,
    )
    path.write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in ordered) + "\n",
        encoding="utf-8",
    )
    try:
        from tip_icerik import write_vizyon_seviye

        write_vizyon_seviye(records)
    except Exception:
        pass


def run_quotes_pass(
    *,
    attach_port: int | None = 9222,
    require_cdp: bool = True,
    limit_per_round: int = 40,
    skip_hafiza: bool = False,
    max_rounds: int = 15,
) -> int:
    """Sadece Asama 2: jsonl'deki eksik alintilari status sayfasindan tamamla."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright kurulu degil.")
        return 1

    all_rows = load_existing_rows(JSONL_OUT)
    if not all_rows:
        print(f"Bos: {JSONL_OUT}")
        return 1

    n_retry = reset_erisilemedi_rows(all_rows)
    if n_retry:
        print(f"[erisilemedi] yeniden denenecek: {n_retry}")

    quotes_done: set[str] = {tid for tid, r in all_rows.items() if r.get("isQuote") and not row_quote_needs_visit(r)}
    threads_done: set[str] = set()
    pending = len(collect_quote_jobs(all_rows, [], quotes_done))
    print(f"Bekleyen alinti: {pending}")
    if not pending:
        return 0

    migrate_session_if_needed()
    with sync_playwright() as p:
        context = None
        cdp_browser = None
        if attach_port and wait_for_cdp_port(attach_port, 90 if require_cdp else 25):
            try:
                cdp_browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{attach_port}")
                context = cdp_browser.contexts[0] if cdp_browser.contexts else cdp_browser.new_context()
                _log(f"Chrome CDP (port {attach_port})")
            except Exception as e:
                _log(f"CDP hata: {e}")
                if require_cdp:
                    return 1
        if not context:
            if require_cdp:
                _log("CHROME_X.bat acik olmali.")
                return 1
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_DIR),
                headless=False,
                viewport={"width": 1400, "height": 900},
                locale="tr-TR",
            )
        try:
            page = pick_profile_page(context)
            close_foreign_tabs(context, page)
            finish_quotes_loop(
                page,
                all_rows,
                quotes_done,
                threads_done,
                max_rounds=max_rounds,
                per_round=limit_per_round,
                return_url=PROFILE_URL_POSTS,
            )
        finally:
            save_jsonl(scraped_to_records(list(all_rows.values())), JSONL_OUT)
            save_pending_list(all_rows)
            try:
                if cdp_browser:
                    cdp_browser.close()
                else:
                    context.close()
            except Exception:
                pass

    records = load_jsonl(JSONL_OUT)
    print(f"JSONL guncellendi: {len(records)} tweet")
    if not skip_hafiza:
        apply_to_hafiza(records, HAFIZA, False)
        try:
            from analiz_devam import run_full_analysis

            run_full_analysis(write_hafiza=True)
        except Exception as e:
            _log(f"Analiz atlandi: {e}")
    return 0


def apply_to_hafiza(records: list[TweetRecord], hafiza: Path, dry_run: bool) -> int:
    import shutil

    md = hafiza.read_text(encoding="utf-8")
    new_md = rebuild_hafiza_md(md, records)
    new_md = update_section_7_date(new_md)
    en_n = sum(1 for r in records if r.lang == "en")
    bek = sum(1 for r in records if not r.analyzed)
    print(f"Hafiza: {len(records)} tweet | Ingilizce(kirli): {en_n} | Analiz bekliyor: {bek}")
    if en_n:
        print("UYARI: Chrome cevirisini KAPAT (x.com) ve tekrar tara.")

    if dry_run:
        print("[--dry-run] yazilmadi")
        return len(records)

    backup = hafiza.with_suffix(".md.bak")
    shutil.copy2(hafiza, backup)
    hafiza.write_text(new_md, encoding="utf-8")
    print(f"OK: {hafiza}")
    return len(records)


def run_scrape(
    *,
    login_only: bool,
    dry_run: bool,
    max_scroll: int,
    scroll_pause_ms: int,
    stop_before: datetime | None,
    headless: bool,
    purge_en_after: bool = False,
    deep_links: bool = False,
    attach_port: int | None = None,
    require_cdp: bool = False,
    skip_hafiza: bool = False,
    finish_quotes: bool = True,
    finish_threads: bool = False,
    feed_url: str | None = None,
    since_date: str | None = None,
    until_date: str | None = None,
    resume: bool = False,
    profile_period_only: bool = False,
    profile_only: bool = False,
    refill_locked_since_date: str | None = None,
    fast_period: bool = False,
    skip_media: bool = False,
) -> int:
    # deep_links varsayilan kapali (status sayfasi X'i coker)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright kurulu değil:")
        print("  pip install -r requirements.txt")
        print("  playwright install chromium")
        return 1

    all_rows: dict[str, dict] = load_existing_rows(JSONL_OUT)
    quotes_done_boot: set[str] = set()
    for tid, row in all_rows.items():
        if row.get("isQuote") and not row_quote_needs_visit(row):
            quotes_done_boot.add(tid)
    if all_rows:
        _log(
            f"Mevcut jsonl: {len(all_rows)} tweet | "
            f"alinTi tam: {len(quotes_done_boot)} | bekleyen alinti: "
            f"{sum(1 for r in all_rows.values() if r.get('isQuote')) - len(quotes_done_boot)}"
        )

    migrate_session_if_needed()
    cdp_browser = None
    attached_cdp = False

    with sync_playwright() as p:
        context = None
        if attach_port:
            if not wait_for_cdp_port(attach_port, 90 if require_cdp else 25):
                msg = (
                    f"Chrome debug port {attach_port} yok. Once CHROME_X.bat calistir; "
                    "tweetler gorunene kadar bekle, sonra BASLAT_TARA.bat"
                )
                _log(msg)
                if require_cdp:
                    return 1
            else:
                try:
                    cdp_browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{attach_port}")
                    context = cdp_browser.contexts[0] if cdp_browser.contexts else cdp_browser.new_context()
                    attached_cdp = True
                    _log(f"Senin Chrome'una baglandi (port {attach_port}).")
                except Exception as e:
                    _log(f"CDP baglanti hata: {e}")
                    if require_cdp:
                        return 1

        if not context:
            if require_cdp:
                _log("CDP zorunlu — Playwright Chrome X'i coker. CHROME_X.bat kullan.")
                return 1
            _log(f"Tarayici aciliyor ({SESSION_DIR})...")
            launch_kw = dict(
                user_data_dir=str(SESSION_DIR),
                headless=headless,
                viewport={"width": 1400, "height": 900},
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                extra_http_headers=ACCEPT_LANGUAGE,
                args=CHROME_ARGS,
                ignore_default_args=PLAYWRIGHT_IGNORE_ARGS,
            )
            last_err = None
            for attempt in range(1, 4):
                if attempt > 1:
                    prepare_session_dir()
                    time.sleep(3)
                for browser_name, launch_fn in (
                    ("Chrome", lambda: p.chromium.launch_persistent_context(channel="chrome", **launch_kw)),
                    ("Chromium", lambda: p.chromium.launch_persistent_context(**launch_kw)),
                ):
                    try:
                        context = launch_fn()
                        _log(f"Acildi: {browser_name}")
                        break
                    except Exception as e:
                        last_err = e
                if context:
                    break
                if attempt >= 3:
                    _log("Tarayici acilamadi. CHROME_X.bat ile Chrome ac veya pencereleri kapat.")
                    raise last_err
            try:
                context.set_extra_http_headers(ACCEPT_LANGUAGE)
                context.add_init_script(INIT_TR_JS)
            except Exception:
                pass

        page = pick_profile_page(context)
        close_foreign_tabs(context, page)
        active_search = feed_url or SEARCH_URL
        feed_home = active_search if feed_url else PROFILE_URL_POSTS
        bind_safe_page(page, feed_home)
        try:
            page.bring_to_front()
        except Exception:
            pass
        if "about:blank" in (page.url or "") or "ekonomikocu" not in (page.url or "").lower():
            safe_goto(page, PROFILE_URL_POSTS, reason="baslangic")

        since_dt = (
            datetime.fromisoformat(since_date + "T00:00:00") if since_date else None
        )
        until_dt = (
            datetime.fromisoformat(until_date + "T00:00:00") if until_date else None
        )
        pkey = period_key(since_date, until_date)

        if profile_period_only and since_dt and until_dt:
            run_period_profile_fallback(
                page, all_rows, since_dt, until_dt, max_scroll=max_scroll
            )
            save_jsonl(scraped_to_records(list(all_rows.values())), JSONL_OUT)
            save_pending_list(all_rows)
            if not skip_hafiza:
                apply_to_hafiza(load_jsonl(JSONL_OUT), HAFIZA, dry_run)
            try:
                if cdp_browser:
                    cdp_browser.close()
                else:
                    context.close()
            except Exception:
                pass
            return 0

        if login_only:
            page.goto("https://x.com/login", wait_until="domcontentloaded")
            print("\n>>> X'e giriş yapın. Bitince pencereyi kapatın veya Ctrl+C.\n")
            try:
                page.wait_for_event("close", timeout=0)
            except Exception:
                input("Giriş bittiyse Enter'a basın...")
            context.close()
            return 0

        active_search = feed_url or SEARCH_URL
        use_search_feed = bool(feed_url) and not profile_period_only and not profile_only
        if use_search_feed:
            label = feed_url or "from:ekonomikocu"
            _log(f"Arama modu (tek sekme): {label}")
            page.goto(active_search, wait_until="commit", timeout=120_000)
            page.wait_for_timeout(6000)
            x_clear_error(page)
            page._eko_home = active_search  # type: ignore[attr-defined]
            bind_safe_page(page, active_search)
            try:
                page.bring_to_front()
            except Exception:
                pass
        elif attached_cdp and (
            page_shows_x_crash(page)
            or not profile_feed_ready(page)
            or timeline_tweet_count(page) < 5
        ):
            _log("Profil yuklenmiyor — arama akisina geciliyor...")
            page = open_working_feed(context, page, feed_url=active_search)
        elif profile_feed_ready(page) and "ekonomikocu" in (page.url or "").lower():
            _log("Profil acik — devam (ustte abone tweetleri normal).")
            click_posts_tab(page)
            x_clear_error(page)
            page.wait_for_timeout(2000)
        elif page_shows_x_crash(page) or not profile_feed_ready(page):
            page = open_working_feed(context, page, feed_url=active_search)
        else:
            _log(f"Profil aciliyor: {PROFILE_URL_POSTS}")
            for nav_try in range(2):
                try:
                    page.goto(PROFILE_URL_POSTS, wait_until="commit", timeout=120_000)
                    page.wait_for_timeout(5000)
                    click_posts_tab(page)
                    x_clear_error(page)
                    if profile_feed_ready(page) and not page_shows_x_crash(page):
                        break
                except Exception:
                    pass
                if nav_try >= 1 or page_shows_x_crash(page):
                    page = open_working_feed(context, page, feed_url=active_search)
                    break
        force_turkish_on_page(page)
        feed_home_url = page.url or active_search

        if is_on_login_screen(page):
            _log("UYARI: Login sayfasi acik — CHROME_X sekmesinde ekonomikocu profiline gec.")
            page.wait_for_timeout(8000)
        elif not attached_cdp and not is_logged_in(page):
            page.wait_for_timeout(15_000)

        if not wait_for_profile_feed(page, tries=25 if attached_cdp else 12):
            _log("UYARI: Akis gecikiyor — ayni sekmede yenileniyor...")
            page = open_working_feed(context, page, feed_url=active_search)
            page.wait_for_timeout(8000)

        stale = 0
        recoveries = 0
        reloads = 0
        tried_replies = False
        tried_search = use_search_feed
        stagnation_oldest: datetime | None = None
        stagnation_hits = 0
        period_mode = bool(feed_url)
        period_fail = 0
        period_zero_streak = 0
        period_filter = period_mode and since_dt and until_dt
        threads_done: set[str] = set()
        quotes_done: set[str] = set(quotes_done_boot)
        scroll_start = 0
        if resume:
            bm = load_bookmark(pkey)
            if bm:
                scroll_start = int(bm.get("scroll_index") or 0)
                fu = bm.get("feed_url")
                if fu and url_allowed(fu):
                    _log(f"Bookmark devam: scroll {scroll_start} | {fu[:70]}")
                    safe_goto(page, fu, reason="bookmark")
                    page.wait_for_timeout(5000)
                    x_clear_error(page)

        def persist_partial() -> None:
            if all_rows:
                save_jsonl(scraped_to_records(list(all_rows.values())), JSONL_OUT)
                _log(f"  >> DISKE YAZILDI: {len(all_rows)} tweet -> {JSONL_OUT.name}")

        def feed_recover(phase: str) -> None:
            nonlocal recoveries, stale
            tw = timeline_tweet_count(page)
            u = (page.url or "").lower()
            on_profile = PROFILE_HANDLE in u and "/status/" not in u
            print(f"  >> Kurtarma ({phase})...")
            if on_profile and tw >= 2 and not page_shows_x_crash(page):
                _log("  >> Sayfa basina donulmuyor — sadece asagi kaydiriliyor...")
                if feed_mostly_locked(page):
                    _log("  >> Ustte abone tweetleri — geciliyor...")
                scroll_feed_deeper(page, passes=10)
            elif use_search_feed:
                safe_goto(page, active_search, reason=f"kurtarma-{phase}")
                page.wait_for_timeout(4000)
                x_clear_error(page)
                scroll_feed_deeper(page, passes=6)
            elif profile_only:
                safe_goto(page, PROFILE_URL_POSTS, reason=f"kurtarma-{phase}")
                page.wait_for_timeout(3000)
                click_posts_tab(page)
                scroll_feed_deeper(page, passes=6)
            else:
                ensure_profile_timeline(page)
                scroll_feed_deeper(page, passes=4)
            stale = max(0, stale - 1)
            recoveries += 1

        try:
          for i in range(scroll_start, max_scroll):
            try:
              ensure_feed_page(
                  page,
                  prefer_search=use_search_feed,
                  search_url=active_search,
                  profile_only=profile_only,
              )
              if feed_needs_recovery(page):
                page = open_working_feed(
                    context,
                    page,
                    first_url=PROFILE_URL_POSTS if profile_only else None,
                    feed_url=active_search if feed_url else None,
                )
                use_search_feed = is_search_feed(page) and not profile_only
              page.evaluate(RETRY_JS)
              force_turkish_on_page(page)
              page.evaluate(EXPAND_JS)
              page.wait_for_timeout(600)
              batch = page.evaluate(EXTRACT_JS)
            except Exception as e:
              err = str(e).lower()
              if "closed" in err:
                _log("Tarayici kapatildi — toplananlar kaydediliyor.")
                break
              if "execution context was destroyed" in err or "navigation" in err:
                _log("  >> Sayfa yenilendi — arama akisina donuluyor...")
                page.wait_for_timeout(2000)
                if use_search_feed:
                  safe_goto(page, active_search, reason="nav-retry")
                  page.wait_for_timeout(4000)
                continue
              raise
            kw = {}
            if period_filter:
                kw = {"period_since": since_dt, "period_until": until_dt}
            # Donem aramasinda medya indirme search akisini bozar (splash / ERR_ABORTED)
            merge_page = page
            if period_filter and use_search_feed:
                merge_page = None
            new_in_batch = merge_rows(all_rows, batch, page=merge_page, **kw)
            if batch:
                newest_id = batch[0].get("id")
                save_bookmark(
                    pkey,
                    feed_url=page.url or active_search,
                    scroll_index=i + 1,
                    last_tweet_id=newest_id,
                )

            # Scroll sirasinda status sayfasina GITME (X "Something went wrong" yapar)

            n_quotes = sum(1 for r in all_rows.values() if r.get("isQuote"))
            oldest_dt = None
            for row in all_rows.values():
                d = dt_from_iso(row.get("datetime"))
                if d and (oldest_dt is None or d < oldest_dt):
                    oldest_dt = d

            err_txt = " | X akis hatasi" if page_has_x_error(page) else ""
            tw = timeline_tweet_count(page)

            _log(
                f"Scroll {i + 1}/{max_scroll}: toplam {len(all_rows)} tweet "
                f"(+{new_in_batch} yeni) | ekranda: {tw} | alinti: {n_quotes}"
                + (f" | en eski: {oldest_dt}" if oldest_dt else "")
                + err_txt
            )
            if (i + 1) % 3 == 0 and all_rows:
                persist_partial()
                save_pending_list(all_rows)

            if stop_before and batch:
                batch_oldest = None
                for raw in batch:
                    d = dt_from_iso(raw.get("datetime"))
                    if d and (batch_oldest is None or d < batch_oldest):
                        batch_oldest = d
                if batch_oldest and batch_oldest <= stop_before:
                    print(f"Durduruldu (akista {batch_oldest.date()}): {stop_before}")
                    break

            if feed_needs_recovery(page):
                page = open_working_feed(
                    context,
                    page,
                    first_url=PROFILE_URL_POSTS if profile_only else None,
                    feed_url=active_search if (period_mode and feed_url) else None,
                )
                use_search_feed = is_search_feed(page) and not profile_only
                stale = max(0, stale - 3)
                continue
            if err_txt and tw < 2 and recoveries < 12:
                feed_recover("hata")
                if period_mode:
                    try:
                        page.goto(active_search, wait_until="commit", timeout=90_000)
                        page.wait_for_timeout(4000)
                        x_clear_error(page)
                    except Exception:
                        pass
                continue

            if period_mode and tw < 1:
                period_fail += 1
            elif period_mode:
                period_fail = max(0, period_fail - 2)

            if period_mode and new_in_batch == 0:
                period_zero_streak += 1
            else:
                period_zero_streak = 0

            if (
                period_mode
                and since_dt
                and until_dt
                and (period_fail >= 5 or period_zero_streak >= 8)
            ):
                if fast_period:
                    _log("Donem aramasi bitti (hizli mod — sonraki haftaya gec).")
                    break
                _log("Donem aramasi bos — profil kaydirma (sadece bu ay)...")
                run_period_profile_fallback(
                    page, all_rows, since_dt, until_dt, max_scroll=min(320, max_scroll * 2)
                )
                save_bookmark(
                    pkey,
                    feed_url=PROFILE_URL_POSTS,
                    scroll_index=i + 1,
                    extra={"mode": "profile_fallback"},
                )
                period_mode = False
                period_fail = 0
                period_zero_streak = 0
                stale = 0
                recoveries = 0
                use_search_feed = False
                continue

            batch_oldest_scroll = None
            for raw in batch or []:
                d = dt_from_iso(raw.get("datetime"))
                if d and (batch_oldest_scroll is None or d < batch_oldest_scroll):
                    batch_oldest_scroll = d
            if batch_oldest_scroll:
                if stagnation_oldest and batch_oldest_scroll >= stagnation_oldest:
                    stagnation_hits += 1
                else:
                    stagnation_oldest = batch_oldest_scroll
                    stagnation_hits = 0
            if stagnation_hits >= 6 and batch_oldest_scroll and recoveries < 8:
                if period_filter and use_search_feed:
                    _log(
                        f"  >> Takilma ({batch_oldest_scroll.date()}) — "
                        f"donem aramasina donuluyor"
                    )
                    safe_goto(page, active_search, reason="stagnation-mart")
                    page.wait_for_timeout(5000)
                    x_clear_error(page)
                    page._eko_home = active_search  # type: ignore[attr-defined]
                else:
                    y, m = batch_oldest_scroll.year, batch_oldest_scroll.month
                    since_m = f"{y}-{m:02d}-01"
                    until_m = f"{y}-{m + 1:02d}-01" if m < 12 else f"{y + 1}-01-01"
                    surl = search_period_url(since_m, until_m)
                    _log(
                        f"  >> Takilma ({batch_oldest_scroll.date()}) — "
                        f"ay aramasi: {since_m} .. {until_m}"
                    )
                    safe_goto(page, surl, reason="stagnation-ay")
                    page.wait_for_timeout(5000)
                    x_clear_error(page)
                    for _si in range(12):
                        merge_rows(all_rows, page.evaluate(EXTRACT_JS), page=page)
                        scroll_feed_deeper(page, passes=2)
                    safe_goto(page, PROFILE_URL_POSTS, reason="stagnation-profil")
                    page.wait_for_timeout(4000)
                    click_posts_tab(page)
                stagnation_hits = 0
                stale = 0
                recoveries += 1
                continue

            if new_in_batch == 0:
                stale += 1
                if stale in (4, 8, 12) and recoveries < 12:
                    feed_recover(f"durak #{stale}")
                elif stale == 5 and not tried_replies:
                    tried_replies = True
                    _log("  >> Profil (Gonderiler) — yanitlar sekmesi yok...")
                    safe_goto(page, PROFILE_URL_POSTS, reason="stale-profil")
                    page.wait_for_timeout(5000)
                    click_posts_tab(page)
                    stale = max(0, stale - 2)
                elif stale == 8 and not tried_search and not profile_only and feed_url:
                    tried_search = True
                    _log("  >> Arama: from:ekonomikocu (profil takilinca)...")
                    safe_goto(page, active_search, reason="stale-arama")
                    page.wait_for_timeout(5000)
                    x_clear_error(page)
                    for _si in range(30):
                        force_turkish_on_page(page)
                        page.evaluate(EXPAND_JS)
                        merge_rows(all_rows, page.evaluate(EXTRACT_JS), page=page)
                        aggressive_timeline_scroll(page)
                        page.wait_for_timeout(2200)
                    added = len(all_rows)
                    _log(f"  >> Arama bitti, toplam {added} tweet.")
                    safe_goto(page, PROFILE_URL_POSTS, reason="stale-don")
                    page.wait_for_timeout(4000)
                    stale = 0
                elif stale in (14, 18) and reloads < 1 and not attached_cdp:
                    print("  >> Sayfa yenileniyor...")
                    ensure_profile_timeline(page)
                    safe_goto(page, PROFILE_URL_POSTS, reason="stale-don")
                    page.wait_for_timeout(5000)
                    reloads += 1
                    stale = 0
                elif stale >= (12 if (fast_period and period_filter) else 20):
                    print("Daha fazla tweet yuklenmiyor (limit veya X takildi).")
                    break
            else:
                stale = 0

            ensure_feed_page(
                page,
                prefer_search=use_search_feed,
                search_url=active_search,
                profile_only=profile_only,
            )
            if fast_period and period_filter:
                scroll_feed_deeper(page, passes=6)
            else:
                aggressive_timeline_scroll(page)
            try:
                page.wait_for_timeout(
                    min(scroll_pause_ms, 2000) if fast_period and period_filter else scroll_pause_ms
                )
            except Exception as e:
              if "closed" in str(e).lower():
                _log("Tarayici kapatildi — toplananlar kaydediliyor.")
                break
              raise
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
        finally:
            if deep_links or finish_threads:
                try:
                    _log("Asama: #FLOOD thread parcalari...")
                    finish_threads_loop(
                        page, all_rows, threads_done, limit=200, return_url=feed_home_url
                    )
                except Exception as e:
                    _log(f"FLOOD asamasi atlandi: {e}")
            if finish_quotes and all_rows:
                try:
                    _log("Asama 2: alintilar (tek sekme, ekonomikocu/status)...")
                    finish_quotes_loop(
                        page,
                        all_rows,
                        quotes_done,
                        threads_done,
                        max_rounds=12,
                        per_round=40,
                        return_url=feed_home_url,
                    )
                except Exception as e:
                    _log(f"Alinti asamasi atlandi: {e}")
            if all_rows and not skip_media:
                try:
                    _log("Asama: eksik grafikler (medya/)...")
                    backfill_missing_media(
                        page, all_rows, limit=250, return_url=feed_home_url
                    )
                except Exception as e:
                    _log(f"Medya asamasi atlandi: {e}")
            if refill_locked_since_date:
                try:
                    since_dt = datetime.fromisoformat(refill_locked_since_date)
                    refill_locked_since(
                        page,
                        all_rows,
                        since=since_dt,
                        limit=800,
                        return_url=feed_home_url,
                    )
                except Exception as e:
                    _log(f"Abonelik yenileme atlandi: {e}")
            save_pending_list(all_rows)
            persist_partial()
            try:
                if attached_cdp and cdp_browser:
                    cdp_browser.close()
                else:
                    context.close()
            except Exception:
                pass

    if not all_rows:
        print("Hic tweet toplanamadi. Profil acik mi? X akisinda Retry dene.")
        return 1

    records = scraped_to_records(list(all_rows.values()))
    save_jsonl(records, JSONL_OUT)
    if purge_en_after and JSONL_OUT.exists():
        purge_english_jsonl()
    all_records = load_jsonl(JSONL_OUT)
    en_n = sum(1 for r in all_records if r.lang == "en")
    print(f"\n=== ASIL DOSYA: {JSONL_OUT.resolve()} ===")
    print(f"Toplam: {len(all_records)} | Ingilizce(kirli): {en_n}")
    if en_n:
        print("Chrome cevirisini kapat, --fresh-profile --login-only, tekrar tara.")

    if dry_run:
        return 0
    if not skip_hafiza:
        apply_to_hafiza(all_records, HAFIZA, False)
        try:
            from analiz_devam import run_full_analysis

            run_full_analysis(write_hafiza=True)
        except Exception as e:
            _log(f"Analiz atlandi: {e}")
    else:
        _log("Hafiza atlandi (--skip-hafiza). JSONL kaydedildi.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="X profil tarayıcı + hafıza güncelleme")
    parser.add_argument("--login-only", action="store_true", help="Sadece X giriş penceresi")
    parser.add_argument("--dry-run", action="store_true", help="Hafızaya yazma")
    parser.add_argument("--max-scroll", type=int, default=300, help="Kaydırma turu")
    parser.add_argument(
        "--purge-en",
        action="store_true",
        help="Ingilizce (ceviri kirli) tweetleri jsonl'den sil — sonra cevirisiz tekrar tara",
    )
    parser.add_argument("--pause", type=int, default=5500, help="Kaydırma arası ms (varsayilan: yavas/insan)")
    parser.add_argument(
        "--stop-before",
        type=str,
        default=None,
        help='Bu tarihe gelince dur (ör. "2 Haz 2026"). Boşsa hafızadaki "en eski işlenen"',
    )
    parser.add_argument("--headless", action="store_true", help="Görünmez tarayıcı (giriş zor)")
    parser.add_argument(
        "--jsonl-only",
        action="store_true",
        help="Sadece cekilen_tweetler.jsonl dosyasından hafızayı güncelle (yeniden tarama yok)",
    )
    parser.add_argument(
        "--fresh-profile",
        action="store_true",
        help=".x_session sil — Chrome cevirisi acik kalmis profili temizler",
    )
    parser.add_argument(
        "--skip-hafiza",
        action="store_true",
        help="Sadece jsonl kaydet, hafiza md guncelleme",
    )
    parser.add_argument(
        "--fast-period",
        action="store_true",
        help="Donem aramasi: hizli kaydirma (haftalik tarama icin)",
    )
    parser.add_argument(
        "--skip-media",
        action="store_true",
        help="Tarama sonu medya geri indirme atlansin (hizli tur)",
    )
    parser.add_argument("--prep", action="store_true", help="Kilitli Chrome temizle, cik")
    parser.add_argument(
        "--attach-port",
        type=int,
        default=None,
        help=f"Açık Chrome debug portu (ör. {CDP_DEFAULT_PORT}) — senin X oturumun",
    )
    parser.add_argument(
        "--deep-links",
        action="store_true",
        help="Alinti + #FLOOD thread icin status sayfasina git",
    )
    parser.add_argument(
        "--require-cdp",
        action="store_true",
        help="Sadece CHROME_X.bat (port 9222) — Playwright Chrome kullanma",
    )
    parser.add_argument(
        "--quotes-only",
        action="store_true",
        help="Tarama yok — sadece Asama 2 (alinti status sayfalari)",
    )
    parser.add_argument(
        "--no-finish-quotes",
        action="store_true",
        help="Tarama bitince alinti ziyareti yapma",
    )
    parser.add_argument(
        "--finish-threads",
        action="store_true",
        help="Tarama bitince tum #FLOOD thread parcalarini cek",
    )
    parser.add_argument(
        "--since-date",
        type=str,
        default=None,
        help="Arama: since YYYY-MM-DD (ornek 2026-01-01)",
    )
    parser.add_argument(
        "--until-date",
        type=str,
        default=None,
        help="Arama: until YYYY-MM-DD (ornek 2026-02-01)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="tara_bookmark.json — kaldigi scroll/URL'den devam",
    )
    parser.add_argument(
        "--profile-period-only",
        action="store_true",
        help="Sadece profil kaydir (since/until araligi) — arama yok",
    )
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="Sadece x.com/ekonomikocu profil — arama/explore yok (ustten yeni icin)",
    )
    parser.add_argument(
        "--refill-locked-since",
        type=str,
        default=None,
        help="Abonelik: bu tarihten (YYYY-MM-DD) itibaren kilitli/bos tweetleri status'tan yenile",
    )
    args = parser.parse_args()

    if args.fresh_profile:
        wipe_session()

    if getattr(args, "prep", False):
        prepare_session_dir()
        return 0

    if args.purge_en and args.jsonl_only and JSONL_OUT.exists():
        purge_english_jsonl()
        records = load_jsonl(JSONL_OUT)
        apply_to_hafiza(records, HAFIZA, args.dry_run)
        return 0

    if args.jsonl_only:
        records = load_jsonl(JSONL_OUT)
        if not records:
            print(f"Boş veya yok: {JSONL_OUT}")
            return 1
        return 0 if apply_to_hafiza(records, HAFIZA, args.dry_run) >= 0 else 1

    if args.quotes_only:
        return run_quotes_pass(
            attach_port=args.attach_port or CDP_DEFAULT_PORT,
            require_cdp=args.require_cdp,
            skip_hafiza=args.skip_hafiza,
        )

    stop_dt = None
    if args.stop_before:
        stop_dt, _ = try_parse_date(args.stop_before + " 12:00 2026")

    feed_url = None
    if args.since_date:
        feed_url = search_period_url(args.since_date, args.until_date)

    code = run_scrape(
        login_only=args.login_only,
        dry_run=args.dry_run,
        max_scroll=args.max_scroll,
        scroll_pause_ms=args.pause,
        stop_before=stop_dt,
        headless=args.headless,
        purge_en_after=args.purge_en,
        deep_links=args.deep_links,
        attach_port=args.attach_port,
        require_cdp=args.require_cdp,
        skip_hafiza=args.skip_hafiza,
        finish_quotes=not args.no_finish_quotes,
        finish_threads=args.finish_threads,
        feed_url=feed_url,
        since_date=args.since_date,
        until_date=args.until_date,
        resume=args.resume,
        profile_period_only=args.profile_period_only,
        profile_only=args.profile_only,
        refill_locked_since_date=args.refill_locked_since,
        fast_period=args.fast_period,
        skip_media=args.skip_media,
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
