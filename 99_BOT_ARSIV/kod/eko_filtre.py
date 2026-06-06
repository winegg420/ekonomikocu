#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""@ekonomikocu disi reklam / yabanci akis kirini filtrele."""
from __future__ import annotations

import re

# Kesin reklam / baska hesap (Keşfet, promote)
SPAM_RX = re.compile(
    r"nevada\s+coff|turna'da|ziraat\s+katılım|bmw\s+3\s+serisi|"
    r"mill[iî]\s+takım|clemta\s+ile|turkishexporter|infox\s+merak|"
    r"%50'ye\s+varan\s+indirimle\s+kirala|dj\s+ve\s+prodüktör|"
    r"evlilik\s+yüzüğü\s+nasıl\s+ömür|parmağa\s+takılan\s+evlilik|"
    r"aracınızı\s+planlayın|öngörülerinize\s+uygun\s+varant|"
    r"yüzyüzeyken\s+konuşuruz\s+.*sahtek|dünya\s+kupası\s+yolunda\s+tüm\s+türkiye",
    re.I,
)

KOC_TAG_RX = re.compile(
    r"#(?:bitcoin|btc|eth|altın|altin|gumus|gümüş|petrol|faiz|flood|zaman|"
    r"emtia|enflasyon|dolar|kritik|bitc[oö]in)|"
    r"\b(?:btc|bitcoin|eth|altın|gümüş|petrol|faiz|emtia|enflasyon|dolar)\b|"
    r"ekonomikocu|puştu|oyalama|zaman\s+geçir|NATO|jeopolitik|putin|trump|"
    r"Fibonacci|madenci|boğa|ayı\s+piyas|barış|hormuz|madenc",
    re.I,
)

NOT_EKO_RX = re.compile(
    r"arda\s+g|real\s+madrid|algobot|fenerbahçe\s+başkan|karagümrük\s+maçı|"
    r"forvet\s+olsa|forma ile\s+kamera|milli\s+takımımızın\s+her\s+adım",
    re.I,
)


def is_spam_row(r: dict) -> bool:
    text = (r.get("text") or "").strip()
    if not text:
        return False
    if SPAM_RX.search(text):
        return True
    if r.get("datetime") is None and r.get("date_label") == "tarih-belirsiz":
        if not KOC_TAG_RX.search(text) and len(text) > 120:
            return True
    return False


def is_eko_media_row(r: dict) -> bool:
    """Grafik pakete sadece Koç tweetleri (reklam / bos alinti degil)."""
    tid = str(r.get("tweet_id") or "")
    if tid.startswith("MANUEL-") and (r.get("media_files") or []):
        return True
    if is_spam_row(r):
        return False
    if not (r.get("media_files") or []):
        return False
    text = (r.get("text") or "").strip()
    if NOT_EKO_RX.search(text):
        return False
    if r.get("is_quote") and r.get("quote_stub") and not text:
        return False
    if not r.get("datetime"):
        return False
    # Flood / alinti zinciri parcalari — metinde hashtag olmasa da Koç gorseli
    if r.get("quote_of") or (r.get("kayit_tipi") or "") in ("flood-parça", "flood"):
        return True
    if not KOC_TAG_RX.search(text):
        return False
    return True
