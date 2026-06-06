#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X (Twitter) "Verilerini indir" ZIP arsivini cekilen_tweetler.jsonl'e aktarir.

ZIP: X ayarlarindan istenen e-posta linkindeki paket (tum tweetlerin dosyasi).
@ekonomikocu arsivi icin o hesapla giris yapip indirmen gerekir.

Kullanim:
  python arsiv_import.py
  python arsiv_import.py --zip "C:\\Users\\...\\Downloads\\twitter-....zip"
  python arsiv_import.py --dir "C:\\...\\extracted_archive"
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARSIV_DIR = ROOT / "x_arsiv"
JSONL_OUT = ROOT / "cekilen_tweetler.jsonl"
HAFIZA = ROOT / "ekonomikocu_hafiza_v1.md"
PROFILE_HANDLE = "ekonomikocu"

from hafiza_guncelle import (
    FLOOD_MARKERS,
    TweetRecord,
    classify_products,
    classify_tip,
    detect_lang,
    rebuild_hafiza_md,
    update_section_7_date,
)
from tweet_tara import format_date_label, save_jsonl, scraped_to_records


def _log(msg: str) -> None:
    print(msg, flush=True)


def parse_ytd_js(text: str) -> list:
    start = text.find("[")
    if start < 0:
        return []
    blob = text[start:].strip().rstrip(";").strip()
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        end = blob.rfind("]")
        if end > 0:
            return json.loads(blob[: end + 1])
        raise


def parse_twitter_date(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S %z"):
        try:
            return datetime.strptime(s.strip(), fmt).astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            continue
    return None


def unwrap_tweet(obj: dict) -> dict | None:
    if "tweet" in obj and isinstance(obj["tweet"], dict):
        return obj["tweet"]
    if "id_str" in obj or "full_text" in obj:
        return obj
    return None


def is_retweet(t: dict) -> bool:
    if t.get("retweeted"):
        return True
    txt = (t.get("full_text") or "").strip()
    return txt.startswith("RT @")


def tweet_to_row(t: dict, *, quoted_by: str | None = None) -> dict | None:
    tid = str(t.get("id_str") or t.get("id") or "").strip()
    if not tid:
        return None
    text = (t.get("full_text") or "").strip()
    if is_retweet(t):
        return None
    dt = parse_twitter_date(t.get("created_at") or "")
    iso = dt.isoformat(timespec="seconds") if dt else None
    withheld = (t.get("withheld_text") or t.get("withheld_in_countries")) and not text
    locked = bool(withheld) or bool(t.get("possibly_sensitive") and not text)
    quote_of = str(t.get("quoted_status_id_str") or t.get("quoted_status_id") or "") or None
    in_reply = str(t.get("in_reply_to_status_id_str") or t.get("in_reply_to_status_id") or "") or None
    thread_root = None
    if in_reply:
        thread_root = in_reply
    if FLOOD_MARKERS.search(text):
        thread_root = tid
    return {
        "id": tid,
        "datetime": iso,
        "text": "" if locked else text,
        "locked": locked,
        "isQuote": bool(quoted_by),
        "quotedBy": quoted_by,
        "quoteOf": quote_of if quoted_by else None,
        "threadRoot": thread_root,
        "lang": (t.get("lang") or "tr")[:2],
    }


def rows_from_tweets_js_content(raw: str) -> list[dict]:
    items = parse_ytd_js(raw)
    rows: list[dict] = []
    by_id: dict[str, dict] = {}
    for item in items:
        t = unwrap_tweet(item if isinstance(item, dict) else {})
        if not t:
            continue
        row = tweet_to_row(t)
        if row:
            by_id[row["id"]] = row
    # Alinti satirlari: quoted_status_id var, metin ana tweette; ayri satir stub
    for item in items:
        t = unwrap_tweet(item if isinstance(item, dict) else {})
        if not t:
            continue
        parent_id = str(t.get("id_str") or "")
        qid = str(t.get("quoted_status_id_str") or t.get("quoted_status_id") or "")
        if not parent_id or not qid or qid in by_id:
            continue
        qt = t.get("quoted_status") or {}
        if isinstance(qt, dict) and "full_text" in qt:
            qrow = tweet_to_row(qt, quoted_by=parent_id)
            if qrow:
                qrow["isQuote"] = True
                qrow["quotedBy"] = parent_id
                qrow["quoteOf"] = qid
                by_id[qid] = qrow
        else:
            by_id[qid] = {
                "id": qid,
                "datetime": None,
                "text": "",
                "locked": False,
                "isQuote": True,
                "quotedBy": parent_id,
                "quoteOf": qid,
                "threadRoot": None,
                "lang": "tr",
            }
    return list(by_id.values())


def rows_from_tweets_js(path: Path) -> list[dict]:
    return rows_from_tweets_js_content(path.read_text(encoding="utf-8", errors="replace"))


def rows_from_csv(path: Path) -> list[dict]:
    import csv

    rows = []
    with path.open(encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            tid = (r.get("tweet_id") or r.get("id") or "").strip()
            text = (r.get("text") or "").strip()
            if not tid or text.startswith("RT @"):
                continue
            ts = (r.get("timestamp") or r.get("created_at") or "").strip()
            dt = parse_twitter_date(ts) if ts else None
            rows.append(
                {
                    "id": tid,
                    "datetime": dt.isoformat(timespec="seconds") if dt else None,
                    "text": text,
                    "locked": False,
                    "isQuote": False,
                    "quotedBy": None,
                    "quoteOf": None,
                    "threadRoot": None,
                    "lang": detect_lang(text),
                }
            )
    return rows


def read_account_username(base: Path) -> str | None:
    for rel in ("data/account.js", "data/js/account.js", "data/account.json"):
        p = base / rel
        if not p.exists():
            continue
        try:
            data = parse_ytd_js(p.read_text(encoding="utf-8", errors="replace"))
            for item in data:
                acc = item.get("account") if isinstance(item, dict) else None
                if isinstance(acc, dict):
                    u = acc.get("username") or acc.get("screen_name")
                    if u:
                        return str(u).lower()
        except Exception:
            pass
    return None


def collect_from_tree(base: Path) -> list[dict]:
    all_rows: dict[str, dict] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        name = path.name.lower()
        try:
            if name.endswith(".js") and "tweet" in name:
                for row in rows_from_tweets_js(path):
                    all_rows[row["id"]] = row
            elif name.endswith(".csv") and re.search(r"\d{4}.*\.csv$|tweet", name):
                for row in rows_from_csv(path):
                    all_rows[row["id"]] = row
        except Exception as e:
            _log(f"  atla ({path.name}): {e}")
    return list(all_rows.values())


def collect_from_zip(zip_path: Path) -> list[dict]:
    all_rows: dict[str, dict] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            low = info.filename.lower().replace("\\", "/")
            if not (low.endswith(".js") or low.endswith(".csv")):
                continue
            if "tweet" not in low and not re.search(r"data/.*\.csv$", low):
                continue
            try:
                text = zf.read(info).decode("utf-8", errors="replace")
            except Exception:
                continue
            try:
                if low.endswith(".js") and "tweet" in low:
                    for row in rows_from_tweets_js_content(text):
                        all_rows[row["id"]] = row
                elif low.endswith(".csv"):
                    import csv
                    import io

                    for r in csv.DictReader(io.StringIO(text)):
                        tid = (r.get("tweet_id") or "").strip()
                        body = (r.get("text") or "").strip()
                        if not tid or body.startswith("RT @"):
                            continue
                        ts = (r.get("timestamp") or "").strip()
                        dt = parse_twitter_date(ts) if ts else None
                        all_rows[tid] = {
                            "id": tid,
                            "datetime": dt.isoformat(timespec="seconds") if dt else None,
                            "text": body,
                            "locked": False,
                            "isQuote": False,
                            "quotedBy": None,
                            "quoteOf": None,
                            "threadRoot": None,
                            "lang": detect_lang(body),
                        }
            except Exception as e:
                _log(f"  zip icinde atla {info.filename}: {e}")
    return list(all_rows.values())


def find_archive_zip() -> Path | None:
    candidates: list[Path] = []
    search_dirs = [
        ARSIV_DIR,
        ROOT,
        Path.home() / "Downloads",
        Path.home() / "OneDrive" / "İndirilenler",
        Path.home() / "OneDrive" / "Downloads",
    ]
    for d in search_dirs:
        if not d.exists():
            continue
        for pat in ("*twitter*.zip", "*Twitter*.zip", "*x-archive*.zip", "*tweet*.zip", "*.zip"):
            candidates.extend(d.glob(pat))
    if not candidates:
        return None
    def is_x_archive(zpath: Path) -> bool:
        try:
            with zipfile.ZipFile(zpath) as zf:
                names = [n.lower().replace("\\", "/") for n in zf.namelist()]
                if any("data/tweets" in n or n.endswith("/tweets.js") for n in names):
                    return True
                if any(re.search(r"data/(?:js/)?tweets.*\.js$", n) for n in names):
                    return True
                if any(re.search(r"data/.*tweet.*\.csv$", n) for n in names):
                    return True
        except zipfile.BadZipFile:
            return False
        return False

    candidates = [p for p in candidates if is_x_archive(p)]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def merge_into_jsonl(rows: list[dict]) -> list[TweetRecord]:
    from tweet_tara import load_jsonl

    existing_recs = load_jsonl(JSONL_OUT) if JSONL_OUT.exists() else []
    by_id = {r.tweet_id: r for r in existing_recs if r.tweet_id}
    new_recs = scraped_to_records(rows)
    for rec in new_recs:
        if not rec.tweet_id:
            continue
        prev = by_id.get(rec.tweet_id)
        if prev and (prev.text or "").strip() and not (rec.text or "").strip():
            continue
        if prev and prev.lang == "tr" and rec.lang == "en":
            continue
        by_id[rec.tweet_id] = rec
    merged = sorted(by_id.values(), key=lambda r: r.sort_key(), reverse=True)
    save_jsonl(merged, JSONL_OUT)
    return merged


def run_import(*, zip_path: Path | None, dir_path: Path | None) -> int:
    ARSIV_DIR.mkdir(exist_ok=True)
    source = dir_path
    z = zip_path
    user = None
    rows: list[dict] = []
    if z and not z.exists():
        _log(f"ZIP yok: {z}")
        return 1
    if not source and not z:
        z = find_archive_zip()
        if z:
            _log(f"Bulunan arsiv: {z}")
        else:
            _log(
                "ZIP bulunamadi. x_arsiv klasorune koy veya ARSIV_AL.bat ile X'ten iste."
            )
            return 1

    if z and not source:
        rows = collect_from_zip(z)
        with zipfile.ZipFile(z) as zf:
            # kullanici adi kontrolu icin account.js zip icinden
            user = None
            for info in zf.infolist():
                if "account.js" in info.filename.lower():
                    try:
                        data = parse_ytd_js(zf.read(info).decode("utf-8", errors="replace"))
                        for item in data:
                            acc = item.get("account") if isinstance(item, dict) else None
                            if isinstance(acc, dict):
                                user = (acc.get("username") or acc.get("screen_name") or "").lower()
                    except Exception:
                        pass
                    break
    else:
        source = source or ARSIV_DIR
        if not source.exists():
            _log(f"Klasor yok: {source}")
            return 1
        rows = collect_from_tree(source)
        user = read_account_username(source)

    if user and user != PROFILE_HANDLE:
        _log(
            f"UYARI: Arsiv @{user} hesabina ait. @{PROFILE_HANDLE} icin o hesapla indirmen gerekir."
        )
    elif user:
        _log(f"Arsiv hesabi: @{user}")

    if not rows:
        _log("Tweet dosyasi okunamadi (tweets.js / csv bos).")
        return 1

    merged = merge_into_jsonl(rows)
    _log(f"JSONL: {len(merged)} tweet -> {JSONL_OUT.name}")

    try:
        from analiz_devam import run_full_analysis

        run_full_analysis(write_hafiza=True)
        _log("Analiz + hafiza guncellendi.")
    except Exception as e:
        md = HAFIZA.read_text(encoding="utf-8")
        HAFIZA.write_text(rebuild_hafiza_md(update_section_7_date(md), merged), encoding="utf-8")
        _log(f"Analiz atlandi ({e}), hafiza yine guncellendi.")

    main_n = sum(1 for r in merged if not r.is_quote)
    oldest = min((r.dt for r in merged if r.dt), default=None)
    _log(f"Ana tweet: {main_n} | En eski: {oldest}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="X arsiv ZIP -> cekilen_tweetler.jsonl")
    parser.add_argument("--zip", type=Path, help="Arsiv .zip yolu")
    parser.add_argument("--dir", type=Path, help="Acilmis arsiv klasoru")
    args = parser.parse_args()
    return run_import(zip_path=args.zip, dir_path=args.dir)


if __name__ == "__main__":
    raise SystemExit(main())
