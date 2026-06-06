#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flood / alinti parcalarinda media_urls var ama media_files bos olanlari indir.

Ornek:
  python flood_medya_indir.py
  python flood_medya_indir.py --quote-of 1770898482808643726
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _root()
KOD = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"


def load_records() -> list[dict]:
    rows: list[dict] = []
    if not JSONL.is_file():
        return rows
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def save_records(rows: list[dict]) -> None:
    from tweet_tara import scraped_to_records, save_jsonl

    by_id: dict[str, dict] = {}
    for r in rows:
        tid = r.get("tweet_id")
        if tid:
            by_id[tid] = {
                "id": tid,
                "datetime": r.get("datetime"),
                "text": r.get("text") or "",
                "locked": r.get("locked", False),
                "isQuote": r.get("is_quote", False),
                "quotedBy": r.get("quoted_by"),
                "quoteOf": r.get("quote_of"),
                "threadRoot": r.get("thread_root"),
                "media": r.get("media_urls") or [],
                "mediaFiles": r.get("media_files") or [],
            }
    save_jsonl(scraped_to_records(list(by_id.values())), JSONL)


def needs_download(r: dict) -> bool:
    urls = r.get("media_urls") or []
    if not urls:
        return False
    files = r.get("media_files") or []
    if not files:
        return True
    for f in files:
        p = ROOT / str(f).replace("/", "\\")
        if not p.is_file() or p.stat().st_size < 400:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Eksik flood gorsellerini indir")
    parser.add_argument("--attach-port", type=int, default=9222)
    parser.add_argument("--quote-of", default="", help="Sadece bu alinti kokunun parcalari")
    parser.add_argument("--no-pack", action="store_true")
    args = parser.parse_args()

    rows = load_records()
    targets = [r for r in rows if needs_download(r)]
    if args.quote_of.strip():
        qo = args.quote_of.strip()
        targets = [
            r
            for r in targets
            if r.get("tweet_id") == qo
            or str(r.get("quote_of") or "") == qo
            or str(r.get("thread_root") or "") == qo
        ]

    if not targets:
        print("Indirilecek eksik gorsel yok.", flush=True)
        return 0

    print(f"Eksik gorsel: {len(targets)} tweet", flush=True)
    for r in targets:
        print(
            f"  {r.get('tweet_id')} | {r.get('kayit_tipi','')} | "
            f"urls={len(r.get('media_urls') or [])}",
            flush=True,
        )

    from tweet_tara import JSONL_OUT, download_tweet_media, load_existing_rows, save_jsonl, scraped_to_records

    all_rows = load_existing_rows(JSONL_OUT)
    ok = 0
    for r in targets:
        tid = r.get("tweet_id")
        urls = r.get("media_urls") or []
        if not tid or not urls:
            continue
        files = download_tweet_media(None, tid, urls)
        if files and tid in all_rows:
            all_rows[tid]["media"] = urls
            all_rows[tid]["mediaFiles"] = files
            ok += 1
            print(f"  OK {tid}: {files}", flush=True)

    save_jsonl(scraped_to_records(list(all_rows.values())), JSONL_OUT)
    print(f"Bitti: {ok}/{len(targets)} indirildi", flush=True)

    if not args.no_pack:
        import subprocess

        subprocess.run([sys.executable, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
