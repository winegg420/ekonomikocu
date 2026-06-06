#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""medya/ + jsonl: hisse logosu, finance URL, alakasiz kartlari temizle; paketi yenile."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from grafik_filtre import filter_row_media

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"
PY = sys.executable


def main() -> int:
    lines = JSONL.read_text(encoding="utf-8").splitlines()
    out_lines: list[str] = []
    total_removed_files = 0
    tweets_touched = 0

    for ln in lines:
        if not ln.strip():
            continue
        r = json.loads(ln)
        urls_before = len(r.get("media_urls") or [])
        files_before = len(r.get("media_files") or [])
        if not urls_before and not files_before:
            out_lines.append(ln)
            continue
        new_urls, new_files, removed = filter_row_media(r, ROOT)
        if (
            removed
            or len(new_urls) != urls_before
            or len(new_files) != files_before
            or (new_urls and not r.get("media_files"))
        ):
            tweets_touched += 1
            total_removed_files += len(removed)
            r["media_urls"] = new_urls
            if new_files:
                r["media_files"] = new_files
            else:
                r.pop("media_files", None)
            if not new_urls:
                r.pop("media_urls", None)
        out_lines.append(json.dumps(r, ensure_ascii=False))

    JSONL.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    print(f"Tweet guncellendi: {tweets_touched} | Silinen dosya: {total_removed_files}")

    try:
        from tweet_tara import HAFIZA, apply_to_hafiza, load_jsonl

        print("Calistiriliyor: hafiza (jsonl)...")
        apply_to_hafiza(load_jsonl(JSONL), HAFIZA, False)
    except Exception as e:
        print(f"Hafiza guncellenemedi: {e}")

    import subprocess

    p = ROOT / "claude_paket_olustur.py"
    if p.is_file():
        print("Calistiriliyor: Claude/Gemini paket...")
        subprocess.run([PY, str(p)], cwd=ROOT, check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
