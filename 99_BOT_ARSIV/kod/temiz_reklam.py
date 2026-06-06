#!/usr/bin/env python3
"""cekilen_tweetler.jsonl icinden reklam/Keşfet kirini sil."""
from __future__ import annotations

import json
from pathlib import Path

from eko_filtre import is_spam_row

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "cekilen_tweetler.jsonl"


def main() -> int:
    lines = JSONL.read_text(encoding="utf-8").splitlines()
    kept, removed = [], []
    for ln in lines:
        if not ln.strip():
            continue
        r = json.loads(ln)
        if is_spam_row(r):
            removed.append(r.get("tweet_id"))
        else:
            kept.append(ln)
    JSONL.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    print(f"Kalan: {len(kept)} | Silinen reklam/kirli: {len(removed)}")
    if removed[:8]:
        print("Ornek silinen:", ", ".join(removed[:8]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
