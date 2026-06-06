#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Abone tweetlerini jsonl'de isaretle; Claude locked=true aramasin diye."""
from __future__ import annotations

import json
import re
from pathlib import Path

ABONE_SINCE = "2026-04-01"
ABONE_RX = re.compile(r"abonelik|subscriber", re.I)
EKSIK_RX = re.compile(r"eksik\s*\(abonelik\)", re.I)


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return here


def _has_text(r: dict) -> bool:
    t = (r.get("text") or "").strip()
    return bool(t) and t != "[erişilemedi]"


def main() -> int:
    root = _project_root()
    path = root / "cekilen_tweetler.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    n_abone = n_fix = 0
    for r in rows:
        if r.get("is_quote") or not _has_text(r):
            continue
        dt = r.get("datetime") or ""
        if dt < ABONE_SINCE:
            continue
        tip = (r.get("kayit_tipi") or "").lower()
        bag = str(r.get("baglanti") or "") + " " + str(r.get("sonuc") or "")
        was_kilitli = tip == "kilitli" or ABONE_RX.search(bag)
        r["abone_donemi"] = True
        if _has_text(r) and not r.get("locked"):
            r["abone_metin"] = True
            r["kayit_tipi"] = "abone"
            n_abone += 1
            if EKSIK_RX.search(r.get("baglanti") or ""):
                r["baglanti"] = EKSIK_RX.sub("abone metin kaydedildi", r.get("baglanti") or "")
                n_fix += 1
            elif EKSIK_RX.search(r.get("sonuc") or ""):
                r["sonuc"] = EKSIK_RX.sub("abone metin kaydedildi", r.get("sonuc") or "")
                n_fix += 1
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    print(f"abone_metin isaretlendi: {n_abone} | baglanti duzeltildi: {n_fix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
