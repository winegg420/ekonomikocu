#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jsonl'deki her is_quote satiri icin tam metin var mi kontrol eder.
Cikis kodu: 0 = tum alintilar tam, 1 = eksik var.
"""
from __future__ import annotations

import argparse
import sys

from pathlib import Path

from alinti_common import JSONL, find_incomplete_quotes


def run_check(jsonl_path: Path | str = JSONL) -> int:
    """Argparse kullanmadan kontrol (alinti_tamamla icinden cagrilir)."""
    import json

    path = Path(jsonl_path)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    rows = [json.loads(l) for l in lines if l.strip()]
    bad = find_incomplete_quotes(rows)
    quotes = sum(1 for r in rows if r.get("is_quote"))

    print(f"Dosya: {path}")
    print(f"Toplam satir: {len(rows)} | alinti (is_quote): {quotes}")
    if not bad:
        print("OK — tum alintilar dolu veya kilitli/erisilemedi isaretli.")
        return 0

    print(f"EKSIK: {len(bad)} alinti — tekrar: ALINTI_TAMAMLA.bat")
    for item in bad:
        print(
            f"  {item['quote_id']} <- ana {item['quoted_by']} | "
            f"{item['reason']} | metin={item['text_len']} char"
        )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Alinti eksiklik kontrolu")
    parser.add_argument("--jsonl", type=str, default=str(JSONL))
    args = parser.parse_args()
    return run_check(args.jsonl)


if __name__ == "__main__":
    raise SystemExit(main())
