#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alinti (quote) ID toplama, eksiklik kontrolu, ortak sabitler."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"
PENDING = ROOT / "alinti_bekleyen.jsonl"

ERISILEMEDI = "[erişilemedi]"
TRUNC_RE = re.compile(
    r"x\.com/\S*…|sta…\s*$|status/\d+…|\.\.\.\s*$|…\s*$",
    re.I,
)


def quote_status_url(tweet_id: str) -> str:
    return f"https://x.com/i/status/{tweet_id}"


def load_jsonl_dicts(path: Path = JSONL) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def row_from_jsonl(o: dict) -> dict:
    """tweet_tara ic satir formatina."""
    return {
        "id": o.get("tweet_id"),
        "datetime": o.get("datetime"),
        "text": o.get("text") or "",
        "locked": o.get("locked", False),
        "isQuote": o.get("is_quote", False),
        "quotedBy": o.get("quoted_by"),
        "quoteOf": o.get("quote_of"),
        "quoteStub": o.get("quote_stub", False),
    }


def quote_text_incomplete(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if t == ERISILEMEDI:
        return False
    # Sonda sadece x.com link kirpintisi — govde yeterliyse tam say (X UI limiti)
    if len(t) >= 150 and re.search(r"x\.com/\S+…?\s*$", t) and t.count("…") <= 1:
        return False
    if TRUNC_RE.search(t):
        return True
    if len(t) < 80 and ("…" in t or "..." in t):
        return True
    if len(t) < 220 and (t.endswith("…") or "sta…" in t):
        return True
    return False


def reset_erisilemedi_rows(all_rows: dict[str, dict]) -> int:
    """Yanlis [erisilemedi] isaretlerini tekrar ziyaret icin ac."""
    n = 0
    for tid, row in all_rows.items():
        if row.get("isQuote") and (row.get("text") or "").strip() == ERISILEMEDI:
            row["text"] = ""
            row["quoteStub"] = True
            n += 1
    return n


def row_quote_needs_visit(row: dict) -> bool:
    """Asama 2: status sayfasina gitmeli mi?"""
    tid = row.get("id") or row.get("tweet_id")
    if not tid:
        return False
    if not row.get("isQuote") and not row.get("is_quote"):
        return False
    if row.get("locked"):
        return False
    text = (row.get("text") or "").strip()
    if text == ERISILEMEDI:
        return False
    if row.get("quoteStub") or row.get("quote_stub"):
        return True
    if quote_text_incomplete(text):
        return True
    if not row.get("datetime"):
        return True
    return False


def row_quote_complete(row: dict) -> bool:
    if not (row.get("isQuote") or row.get("is_quote")):
        return True
    if row.get("locked"):
        return True
    if (row.get("text") or "").strip() == ERISILEMEDI:
        return True
    return not row_quote_needs_visit(row)


def find_incomplete_quotes(rows: list[dict] | None = None) -> list[dict]:
    """Eksik alinti listesi (rapor icin)."""
    if rows is None:
        rows = load_jsonl_dicts()
    bad = []
    for o in rows:
        if not o.get("is_quote"):
            continue
        r = row_from_jsonl(o)
        if row_quote_needs_visit(r):
            bad.append(
                {
                    "quote_id": o.get("tweet_id"),
                    "quoted_by": o.get("quoted_by"),
                    "datetime": o.get("datetime"),
                    "text_len": len((o.get("text") or "")),
                    "locked": o.get("locked", False),
                    "reason": _incomplete_reason(r),
                }
            )
    return bad


def _incomplete_reason(row: dict) -> str:
    if row.get("quoteStub") or row.get("quote_stub"):
        return "stub (sadece ID)"
    if not (row.get("text") or "").strip():
        return "metin bos"
    if not row.get("datetime"):
        return "tarih yok"
    if quote_text_incomplete(row.get("text") or ""):
        return "metin kesik"
    return "bilinmiyor"


def save_pending_list(all_rows: dict[str, dict], path: Path = PENDING) -> int:
    """Asama 1: bekleyen alinti ID listesi."""
    lines = []
    for tid, row in sorted(all_rows.items()):
        if not row.get("isQuote"):
            continue
        if not row_quote_needs_visit(row):
            continue
        lines.append(
            json.dumps(
                {
                    "quote_id": tid,
                    "quoted_by": row.get("quotedBy"),
                    "datetime": row.get("datetime"),
                    "found_at": datetime.now().isoformat(timespec="seconds"),
                },
                ensure_ascii=False,
            )
        )
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)
