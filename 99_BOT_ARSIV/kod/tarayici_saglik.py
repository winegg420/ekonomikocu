#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tarayici/CDP saglik yardimcilari — TEK modul, tum tarama scriptleri buradan import eder.

Icerik:
  baglanti_hatasi(err)   — olu baglanti/sekme hatasi mi?
  sayfa_canli(page)      — sayfa hala kullanilabilir mi?
  iyilestir(page, ...)   — kopan CDP baglantisini tazele, canli sayfa dondur
  RateLimitBackoff       — 30->60->120->240 sn ustel bekleme, 300 sn tavan
  rate_limit_var(page)   — sayfa govdesinde rate-limit izi
  icerik_bekle(page,...) — kor uyku yerine kosullu bekleme (ust sinir ayni)
"""
from __future__ import annotations

import time

CDP_PORT = 9222

# Playwright olu-baglanti mesaj izleri (kucuk harf)
_KOPMA_IZLERI = (
    "has been closed",
    "target closed",
    "connection closed",
    "browser closed",
    "not connected",
    "disconnected",
    "reading from the driver",
    "pipe closed",
)

_RATE_LIMIT_IZLERI = (
    "rate limit",
    "too many requests",
    "cok fazla istek",
    "çok fazla istek",
    "limit asildi",
    "limit aşıldı",
    "daha sonra tekrar dene",
    "try again later",
    # X'in hata/crash sayfasi da fiilen rate-limit gostergesi
    "bir sorun oluştu",
    "bir sorun olustu",
    "bir şeyler ters gitti",
    "bir seyler ters gitti",
    "something went wrong",
    "yeniden yüklemeyi dene",
    "yeniden yuklemeyi dene",
    "try reloading",
)

# Taze Playwright surucusu (eskisi olduyse) — GC olmasin diye modul seviyesinde tut
_taze_pw = None


def _log(msg: str) -> None:
    print(msg, flush=True)


def baglanti_hatasi(err: BaseException | str) -> bool:
    """Sayfa/context/tarayici/driver olumu mu? (SPA 'destroyed' hatasi DEGIL)"""
    s = str(err).lower()
    return any(iz in s for iz in _KOPMA_IZLERI)


def sayfa_canli(page) -> bool:
    """Hizli saglik kontrolu: sekme acik ve evaluate calisiyor mu?"""
    try:
        if page is None or page.is_closed():
            return False
        page.evaluate("1")
        return True
    except Exception:
        return False


def _sayfa_sec(context):
    """Context icinden kullanilabilir sayfa sec (tercih: ekonomikocu sekmesi)."""
    try:
        from tweet_tara import pick_profile_page

        return pick_profile_page(context)
    except Exception:
        try:
            return context.pages[0] if context.pages else context.new_page()
        except Exception:
            return None


def _bagla_ve_don(page, home_url: str | None):
    try:
        from tara_nav import bind_safe_page

        bind_safe_page(page, home_url or "https://x.com/ekonomikocu")
    except Exception:
        pass
    return page


def _cdp_baglan(port: int):
    """Once taze surucu varsa onu, yoksa yeni sync_playwright ile CDP baglantisi."""
    global _taze_pw
    if _taze_pw is None:
        from playwright.sync_api import sync_playwright

        _taze_pw = sync_playwright().start()
    browser = _taze_pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    return browser, context


def iyilestir(page, *, port: int = CDP_PORT, home_url: str | None = None,
              deneme: int = 4, etiket: str = "saglik"):
    """Canli sayfa dondur: once mevcut, sonra context, sonra CDP'ye yeniden baglan.

    Basarisizsa None — cagiran taraf turu kesip toplananlari kaydetmeli.
    """
    if sayfa_canli(page):
        return page
    _log(f"  >> [{etiket}] Baglanti kopuk — yeniden baglaniliyor (port {port})...")
    # 1) Ayni context/tarayici hala ayaktaysa yeni/mevcut sekme al
    try:
        ctx = page.context
        br = getattr(ctx, "browser", None)
        if br is not None and br.is_connected():
            npage = _sayfa_sec(ctx)
            if npage is not None and sayfa_canli(npage):
                _log(f"  >> [{etiket}] Ayni tarayicidan sekme kurtarildi.")
                return _bagla_ve_don(npage, home_url)
    except Exception:
        pass
    # 2) CDP portuna yeniden baglan (driver da olduyse taze surucuyle)
    try:
        from tweet_tara import wait_for_cdp_port
    except Exception:
        wait_for_cdp_port = None
    for n in range(1, deneme + 1):
        try:
            if wait_for_cdp_port is not None and not wait_for_cdp_port(port, 45):
                _log(f"  >> [{etiket}] Port {port} kapali ({n}/{deneme}) — Chrome acik mi?")
                time.sleep(min(5 * n, 20))
                continue
            _browser, context = _cdp_baglan(port)
            npage = _sayfa_sec(context)
            if npage is not None and sayfa_canli(npage):
                _log(f"  >> [{etiket}] CDP'ye yeniden baglandi (deneme {n}).")
                return _bagla_ve_don(npage, home_url)
        except Exception as e:
            _log(f"  >> [{etiket}] Yeniden baglanma {n}/{deneme}: {e}")
            # Surucu bozulduysa sonraki denemede sifirdan baslat
            global _taze_pw
            try:
                if _taze_pw is not None and baglanti_hatasi(e):
                    _taze_pw.stop()
            except Exception:
                pass
            if baglanti_hatasi(e):
                _taze_pw = None
            time.sleep(min(5 * n, 20))
    _log(f"  >> [{etiket}] Baglanti KURTARILAMADI — tur kesilmeli, veriler kaydedilmeli.")
    return None


class RateLimitBackoff:
    """429/'rate limit' tespitinde ustel bekleme: 30->60->120->240, tavan 300 sn."""

    def __init__(self, taban_sn: int = 30, tavan_sn: int = 300) -> None:
        self.taban_sn = taban_sn
        self.tavan_sn = tavan_sn
        self.n = 0

    def bekle(self, neden: str = "") -> None:
        sn = min(self.taban_sn * (2 ** self.n), self.tavan_sn)
        self.n += 1
        _log(f"  >> RATE-LIMIT backoff: {sn} sn bekleniyor"
             + (f" ({neden})" if neden else "") + "...")
        time.sleep(sn)

    def sifirla(self) -> None:
        self.n = 0


def rate_limit_var(page) -> bool:
    """Sayfa govdesinde rate-limit izi (X, 429'u UI metniyle gosterir)."""
    try:
        body = (page.locator("body").inner_text(timeout=3000) or "").lower()
    except Exception:
        return False
    return any(iz in body for iz in _RATE_LIMIT_IZLERI)


def icerik_bekle(page, max_ms: int = 5000,
                 selector: str = 'article[data-testid="tweet"]',
                 settle_ms: int = 300) -> None:
    """Kor wait_for_timeout yerine: icerik gelirse erken don, ust sinir AYNI.

    Selector gelmezse toplam bekleme eski sabit sureye esittir (davranis korunur).
    """
    try:
        page.wait_for_selector(selector, timeout=max_ms)
        if settle_ms:
            page.wait_for_timeout(settle_ms)
    except Exception:
        pass
