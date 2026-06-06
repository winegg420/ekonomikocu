#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHROME_X oturumunda X 'Verilerini indir' sayfasini acar."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tweet_tara import CDP_DEFAULT_PORT, wait_for_cdp_port, pick_profile_page, _log  # noqa: E402

DOWNLOAD_URL = "https://x.com/settings/download_your_data"


def main() -> int:
    port = CDP_DEFAULT_PORT
    if not wait_for_cdp_port(port, 60):
        print("Once CHROME_X.bat calistir.")
        return 1
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("pip install -r requirements.txt")
        return 1

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = pick_profile_page(ctx)
        try:
            page.bring_to_front()
        except Exception:
            pass
        _log(f"Aciliyor: {DOWNLOAD_URL}")
        page.goto(DOWNLOAD_URL, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(3000)
        print(
            "\n>>> 1) 'Verilerini indir' / 'Download archive' butonuna bas\n"
            ">>> 2) E-postadaki linke tikla, ZIP indir\n"
            ">>> 3) ZIP'i x_arsiv klasorune kopyala veya Indirilenler'de birak\n"
            ">>> 4) ARSIV_YUKLE.bat calistir\n"
        )
        try:
            page.wait_for_timeout(300_000)
        except KeyboardInterrupt:
            pass
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
