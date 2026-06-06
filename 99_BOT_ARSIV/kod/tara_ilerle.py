#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Takilma onleme: ayni tweet/flood uzerinde gunlerce kalma.

Her basarisiz ziyaret `tara_deneme.json` sayacini artirir.
Limit asilinca [erisilemedi] / flood-atlandi isaretlenir; bot ilerler.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ERISILEMEDI = "[erişilemedi]"
DEFAULT_MAX_ATTEMPTS = 5


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
DENEME_FILE = ROOT / "tara_deneme.json"


def _empty_state() -> dict:
    return {"version": 1, "attempts": {}, "skipped": {}}


def load_state() -> dict:
    if not DENEME_FILE.is_file():
        return _empty_state()
    try:
        st = json.loads(DENEME_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _empty_state()
    st.setdefault("attempts", {})
    st.setdefault("skipped", {})
    return st


def save_state(st: dict) -> None:
    st["guncelleme"] = datetime.now().isoformat(timespec="seconds")
    DENEME_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def get_attempts(tid: str) -> int:
    return int(load_state()["attempts"].get(str(tid), 0))


def bump_attempt(tid: str) -> int:
    st = load_state()
    tid = str(tid)
    n = int(st["attempts"].get(tid, 0)) + 1
    st["attempts"][tid] = n
    save_state(st)
    return n


def clear_attempts(tid: str) -> None:
    st = load_state()
    tid = str(tid)
    if tid in st["attempts"]:
        del st["attempts"][tid]
        save_state(st)


def is_skipped(tid: str, reason: str | None = None) -> bool:
    sk = load_state()["skipped"].get(str(tid))
    if not sk:
        return False
    if reason and sk.get("reason") != reason:
        return False
    return True


def skipped_ids(reason: str | None = None) -> set[str]:
    out: set[str] = set()
    for tid, sk in load_state()["skipped"].items():
        if reason and sk.get("reason") != reason:
            continue
        out.add(str(tid))
    return out


def mark_skipped(tid: str, reason: str) -> None:
    st = load_state()
    tid = str(tid)
    st["skipped"][tid] = {
        "reason": reason,
        "at": datetime.now().isoformat(timespec="seconds"),
        "attempts": int(st["attempts"].get(tid, 0)),
    }
    save_state(st)


def should_give_up(tid: str, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> bool:
    return get_attempts(tid) >= max_attempts


def mark_locked_unavailable(all_rows: dict[str, dict], tid: str) -> bool:
    """Bos kilitli abone tweet -> [erisilemedi], tekrar denenmez."""
    row = all_rows.get(str(tid))
    if not row:
        mark_skipped(tid, "locked_empty")
        return False
    text = (row.get("text") or "").strip()
    if text and text != ERISILEMEDI:
        return False
    row = dict(row)
    row["locked"] = False
    row["text"] = ERISILEMEDI
    row["abone_metin"] = False
    note = "abone metin erisilemedi (deneme limiti)"
    prev = (row.get("baglanti") or "").strip()
    row["baglanti"] = f"{prev} {note}".strip() if prev else note
    all_rows[str(tid)] = row
    mark_skipped(tid, "locked_empty")
    return True


def count_thread_parts(all_rows: dict[str, dict], root_id: str) -> int:
    root_id = str(root_id)
    n = 0
    for tid, row in all_rows.items():
        if row.get("isQuote"):
            continue
        root = str(row.get("threadRoot") or row.get("thread_root") or tid)
        if root == root_id or tid == root_id:
            n += 1
    return n


def mark_thread_unavailable(all_rows: dict[str, dict], root_id: str) -> bool:
    """#FLOOD parcalari alinamadi — kok isaretlenir, tekrar denenmez."""
    root_id = str(root_id)
    row = all_rows.get(root_id)
    if row:
        row = dict(row)
        row["needsThread"] = False
        row["threadSkip"] = True
        note = "#FLOOD parcalari erisilemedi (deneme limiti)"
        prev = (row.get("baglanti") or "").strip()
        row["baglanti"] = f"{prev} {note}".strip() if prev else note
        all_rows[root_id] = row
    mark_skipped(root_id, "flood")
    return True


def give_up_locked_batch(
    all_rows: dict[str, dict],
    *,
    since: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    force: bool = False,
) -> int:
    """Limiti dolmus (veya force) bos kilitli tweetleri isaretle."""
    n = 0
    for tid, row in list(all_rows.items()):
        if not row.get("locked"):
            continue
        text = (row.get("text") or "").strip()
        if text:
            continue
        if since:
            d = row.get("datetime") or ""
            if d and d < since:
                continue
        if is_skipped(tid, "locked_empty"):
            continue
        if force or should_give_up(tid, max_attempts):
            if mark_locked_unavailable(all_rows, tid):
                n += 1
    return n


def note_thread_result(
    all_rows: dict[str, dict],
    root_id: str,
    parts_before: int,
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> bool:
    """Basarisiz flood denemesini say; limitte atla. True = atlandi."""
    root_id = str(root_id)
    if is_skipped(root_id, "flood"):
        return True
    parts_after = count_thread_parts(all_rows, root_id)
    if parts_after > parts_before:
        clear_attempts(root_id)
        return False
    n = bump_attempt(root_id)
    if n >= max_attempts:
        mark_thread_unavailable(all_rows, root_id)
        return True
    return False


def give_up_flood_batch(
    all_rows: dict[str, dict],
    root_ids: list[str],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    force: bool = False,
) -> int:
    n = 0
    for root_id in root_ids:
        if is_skipped(root_id, "flood"):
            continue
        if force or should_give_up(root_id, max_attempts):
            if mark_thread_unavailable(all_rows, root_id):
                n += 1
    return n


def summary() -> dict:
    st = load_state()
    by_reason: dict[str, int] = {}
    for sk in st["skipped"].values():
        r = sk.get("reason") or "?"
        by_reason[r] = by_reason.get(r, 0) + 1
    pending_high = sum(1 for _tid, c in st["attempts"].items() if int(c) >= DEFAULT_MAX_ATTEMPTS)
    return {
        "skipped": len(st["skipped"]),
        "by_reason": by_reason,
        "pending_give_up": pending_high,
        "tracked_attempts": len(st["attempts"]),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Takilma sayaci / zorla ilerle")
    parser.add_argument("--give-up-locked", action="store_true")
    parser.add_argument("--give-up-flood", action="store_true")
    parser.add_argument("--force", action="store_true", help="Limit beklemeden tum eksikleri isaretle")
    parser.add_argument("--since", default="2026-01-01")
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.summary:
        print(json.dumps(summary(), ensure_ascii=False, indent=2))
        return 0

    from tweet_tara import JSONL_OUT, load_existing_rows, save_jsonl, scraped_to_records

    if args.give_up_locked:
        rows = load_existing_rows(JSONL_OUT)
        n = give_up_locked_batch(
            rows,
            since=args.since,
            max_attempts=args.max_attempts,
            force=args.force,
        )
        if n:
            save_jsonl(scraped_to_records(list(rows.values())), JSONL_OUT)
        print(f"Atlandi (bos kilitli): {n}")
        return 0

    if args.give_up_flood:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "kapsam_2026", Path(__file__).resolve().parent / "kapsam_2026.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        eksik = mod.analyze().get("flood", {}).get("eksik_kok_id") or []
        rows = load_existing_rows(JSONL_OUT)
        n = give_up_flood_batch(
            rows,
            eksik,
            max_attempts=args.max_attempts,
            force=args.force,
        )
        if n:
            save_jsonl(scraped_to_records(list(rows.values())), JSONL_OUT)
        print(f"Atlandi (#FLOOD kok): {n}")
        return 0

    print(summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
