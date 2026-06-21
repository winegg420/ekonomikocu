#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tarama oncesi kapi: CDP'ye bagli Chrome'da giris yapmis X hesabi
beklenen abone hesabi mi? Degilse tarama DURDURULUR (degistirilmez)."""
from __future__ import annotations
import sys
from datetime import datetime

BEKLENEN_HESAP = "420cryptofarmer"  # Ekonomi Kocu'na abone X hesabi

def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def aktif_hesap(port: int = 9222, timeout_ms: int = 15000):
    """Giris yapmis @handle'i dondur. Okunamazsa None."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        _log(f"playwright yuklenemedi: {e}")
        return None
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        except Exception as e:
            _log(f"CDP baglanamadi (port {port}): {e}. CHROME_X.bat acik mi?")
            return None
        ctx = browser.contexts[0] if browser.contexts else None
        if ctx is None:
            _log("Chrome context yok.")
            return None
        page = ctx.new_page()
        try:
            try:
                page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(2500)
            except Exception as e:
                _log(f"x.com acilamadi: {e}")
                return None
            handle = None
            try:  # 1) Sol menu profil linki: href = /<handle>
                el = page.query_selector('a[data-testid="AppTabBar_Profile_Link"]')
                if el:
                    href = (el.get_attribute("href") or "").strip("/")
                    if href:
                        handle = href.split("/")[0]
            except Exception:
                pass
            if not handle:  # 2) Yedek: hesap degistirici butonu
                try:
                    btn = page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]')
                    if btn:
                        for tok in (btn.inner_text() or "").split():
                            if tok.startswith("@"):
                                handle = tok[1:]; break
                except Exception:
                    pass
            return handle
        finally:
            try:
                page.close()
            except Exception:
                pass
            # CDP: bagli Chrome'u KAPATMA — sonraki faz icin acik kalsin

def dogrula(port: int = 9222) -> bool:
    h = aktif_hesap(port)
    if h is None:
        _log("HESAP OKUNAMADI — giris yok ya da Chrome kapali. Tarama DURDURULDU.")
        return False
    if h.lower() != BEKLENEN_HESAP.lower():
        _log(f"YANLIS HESAP: @{h} | beklenen: @{BEKLENEN_HESAP}. Tarama DURDURULDU.")
        _log(f"Chrome'da bu hesaptan cik, @{BEKLENEN_HESAP} ile gir, tekrar calistir.")
        return False
    _log(f"OK — aktif hesap @{h}. Tarama serbest.")
    return True

if __name__ == "__main__":
    sys.exit(0 if dogrula() else 4)
