#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tek seferlik: abone etiketini GERCEK sinyale (abone_ozel = X icon-subscriber) gore duzelt.

- abone_ozel=true ana tweet  -> kayit_tipi=abone, abone_metin=true  (etiket kazanir)
- abone_ozel YOK ama abone etiketli -> public'e dondurulur (kayit_tipi yeniden hesaplanir)

Tarih bazli sahte etiketleme TAMAMEN kalkar. Quote'lar abone sayilmaz.

Kullanim:
  python abone_temizle.py --dry-run            # tum repo onizleme (yazmaz)
  python abone_temizle.py --dry-run --day 2026-06-19   # tek gun onizleme
  python abone_temizle.py                       # uygula (.bak yedek alir)
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from hafiza_guncelle import classify_tip, FLOOD_MARKERS


def _root() -> Path:
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


def _recompute_tip(r: dict) -> str:
    """tweet_tara.py ile ayni siniflama (flood thread mantigi dahil)."""
    text = (r.get("text") or "").strip()
    locked = bool(r.get("locked"))
    is_quote = bool(r.get("is_quote"))
    tid = r.get("tweet_id") or r.get("id")
    thread_root = r.get("thread_root") or r.get("threadRoot")
    quoted_by = r.get("quoted_by") or r.get("quotedBy")
    if is_quote and quoted_by:
        return "asıl (alıntı — ayrı satır)"
    if thread_root and thread_root != tid:
        return "flood" if FLOOD_MARKERS.search(text) else "flood-parça"
    if thread_root == tid and FLOOD_MARKERS.search(text):
        return "flood"
    return classify_tip(text, locked, is_quote)


def _is_abone(r: dict) -> bool:
    return bool(r.get("abone_ozel")) and not r.get("is_quote") and _has_text(r) and not r.get("locked")


def _labeled_abone(r: dict) -> bool:
    return bool(r.get("abone_metin")) or (r.get("kayit_tipi") == "abone")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Yazma, sadece raporla")
    ap.add_argument("--day", default=None, help="Sadece bu gun (YYYY-MM-DD) — onizleme")
    args = ap.parse_args()

    root = _root()
    path = root / "cekilen_tweetler.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    sel = rows
    if args.day:
        sel = [r for r in rows if (r.get("datetime") or "").startswith(args.day)]

    gained = []   # etiket kazanan (gercek abone)
    reverted = []  # public'e donen (sahte etiket)
    for r in sel:
        if _is_abone(r):
            if not _labeled_abone(r):
                gained.append(r)
            r["abone_metin"] = True
            r["kayit_tipi"] = "abone"
        else:
            if _labeled_abone(r):
                reverted.append((r, r.get("kayit_tipi"), _recompute_tip(r)))
                r.pop("abone_metin", None)
                if r.get("kayit_tipi") == "abone":
                    r["kayit_tipi"] = _recompute_tip(r)

    scope = f"GUN {args.day}" if args.day else "TUM REPO"
    main_sel = [r for r in sel if not r.get("is_quote")]
    final_abone = sum(1 for r in sel if _is_abone(r))
    print(f"=== {scope} ===")
    print(f"Incelenen kayit: {len(sel)} (ana tweet: {len(main_sel)})")
    print(f"Etiket KAZANAN (gercek abone, onceden etiketsiz): {len(gained)}")
    print(f"PUBLIC'e DONEN (sahte abone etiketi): {len(reverted)}")
    print(f"Son durum: abone_ozle (gercek abone) = {final_abone} | public = {len(main_sel) - final_abone}")

    if reverted[:6]:
        print("\n-- public'e donen ornekler (eski_kayit_tipi -> yeni) --")
        for r, old, new in reverted[:6]:
            txt = (r.get("text") or "").replace("\n", " ")[:50]
            print(f"  {(r.get('datetime') or '')[:16]} | {old} -> {new} | {txt}")
    if gained[:6]:
        print("\n-- etiket kazanan ornekler --")
        for r in gained[:6]:
            txt = (r.get("text") or "").replace("\n", " ")[:50]
            print(f"  {(r.get('datetime') or '')[:16]} | {txt}")

    if args.dry_run:
        print("\n[DRY-RUN] Dosya YAZILMADI.")
        return 0
    if args.day:
        print("\n[--day] Tek gun modunda yazim yapilmaz (onizleme). Tum repo icin --day'siz calistir.")
        return 0

    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    print(f"\nYAZILDI: {path.name} (yedek: {bak.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
