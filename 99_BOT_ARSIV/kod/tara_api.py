# -*- coding: utf-8 -*-
"""HIZLI TARAMA — X dahili veri akisini (GraphQL JSON) yakalar.

Tarayici with_replies sayfasini yukler; her kaydirmada X ~20 tweetlik JSON
sayfa getirir (ana tweet + flood self-reply parcalari + alinti bilgisi +
medya). Biz bu JSON yanitlarini yakalayip parse ederiz — thread basina ayri
sayfa ACMAYIZ. 3-4 gunluk pencere = birkac kaydirma = dakikalar.

Kullanim: python tara_api.py [--since 2026-06-08] [--max-scroll 30]
Chrome: sessiz (CHROME_X_SESSIZ.bat, 9222) acik olmali.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

import tweet_tara as tt

ROOT = Path(__file__).resolve().parent.parent.parent
JSONL = tt.JSONL_OUT
MEDYA = ROOT / "medya"
HANDLE = "ekonomikocu"


def walk_results(obj):
    """JSON icinde tum tweet_results.result objelerini bul."""
    if isinstance(obj, dict):
        if "tweet_results" in obj and isinstance(obj["tweet_results"], dict):
            r = obj["tweet_results"].get("result")
            if isinstance(r, dict):
                yield r
        for v in obj.values():
            yield from walk_results(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_results(v)


def created_to_iso(s):
    try:
        dt = parsedate_to_datetime(s)  # "Wed Jun 11 14:56:18 +0000 2026"
        return dt.astimezone(timezone.utc).replace(tzinfo=None).isoformat()
    except Exception:
        return None


def parse_tweet(r, quoted_by=None):
    """Bir tweet_results.result -> [ana kayit, (varsa) alinti kaydi...].

    quoted_status_result icindeki alintinin TAM icerigi (metin+medya+tarih)
    zaten JSON gecisinde mevcut; onu ikinci bir isQuote kaydi olarak rekursif
    cikartiriz. Boylece cogu alinti, crawl_quote sayfa navigasyonu OLMADAN
    tamamlanmis olur (rate-limit koken duzeltmesi)."""
    if not isinstance(r, dict):
        return []
    if r.get("__typename") == "TweetWithVisibilityResults":
        r = r.get("tweet", r)
    rid = r.get("rest_id")
    leg = r.get("legacy")
    if not rid or not isinstance(leg, dict):
        return []
    user = (((r.get("core") or {}).get("user_results") or {}).get("result") or {})
    uleg = user.get("legacy") or {}
    handle = (uleg.get("screen_name") or (user.get("core") or {}).get("screen_name") or "").lower()
    text = leg.get("full_text") or ""
    note = (((r.get("note_tweet") or {}).get("note_tweet_results") or {}).get("result") or {})
    if note.get("text"):
        text = note["text"]
    text = re.sub(r"https://t\.co/\w+$", "", text).strip()
    conv = leg.get("conversation_id_str")
    is_quote = bool(leg.get("is_quote_status"))
    quoted = (r.get("quoted_status_result") or {}).get("result")
    quoted_id = quoted.get("rest_id") if isinstance(quoted, dict) else None
    media = []
    ent = (leg.get("extended_entities") or leg.get("entities") or {}).get("media") or []
    for m in ent:
        u = m.get("media_url_https")
        if u:
            media.append(u + "?name=large" if "?" not in u else u)
    rec = {
        "id": rid, "handle": handle, "text": text,
        "datetime": created_to_iso(leg.get("created_at")),
        "conv": conv,
        # Alinti kaydi (quoted_by dolu) her zaman isQuote; ana tweet kendi
        # is_quote_status'unu korur (mevcut davranis degismez).
        "is_quote": True if quoted_by else is_quote,
        "quoted_id": quoted_id,
        "in_reply_to": leg.get("in_reply_to_screen_name"),
        "media": media,
        "quoted_by": quoted_by,
        "json_full": bool(text),  # metin JSON'dan tam geldi -> ADIM 2 ziyaret gerekmez
    }
    out = [rec]
    if isinstance(quoted, dict):
        out.extend(parse_tweet(quoted, quoted_by=rid))
    return out


def download(url, dest):
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None, help="YYYY-MM-DD; bossa en yeni kayit - 3 gun")
    ap.add_argument("--max-scroll", type=int, default=40)
    args = ap.parse_args()

    existing = tt.load_jsonl(JSONL)
    have = {r.tweet_id for r in existing}
    if args.since:
        since = args.since
    else:
        newest = max((r.dt for r in existing if r.dt), default=None)
        base = newest or datetime.now()
        since = (base.fromisoformat((newest.isoformat() if newest else base.isoformat())[:10])).isoformat()[:10]
        # 3 gun tampon
        from datetime import timedelta
        since = (datetime.fromisoformat(since) - timedelta(days=3)).isoformat()[:10]
    print(f"HIZLI TARAMA | since={since} | mevcut {len(have)} tweet", flush=True)

    found = {}  # id -> parsed
    pages = {"n": 0}

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()

        def on_resp(resp):
            u = resp.url
            if "UserTweets" in u or "UserTweetsAndReplies" in u:
                try:
                    data = resp.json()
                except Exception:
                    return
                pages["n"] += 1
                for r in walk_results(data):
                    for t in parse_tweet(r):
                        if t["id"] not in found:
                            found[t["id"]] = t

        pg.on("response", on_resp)
        pg.goto(f"https://x.com/{HANDLE}/with_replies", wait_until="commit", timeout=60000)
        pg.wait_for_timeout(4000)
        # Durma: pencere icindeki (since+) Koc tweet sayisi 3 kaydirma artmazsa
        # bittik demektir. Sabit (pinned) eski tweet bu sayima girmez.
        prev, stagnant = -1, 0
        for i in range(args.max_scroll):
            pg.mouse.wheel(0, 4000)
            pg.wait_for_timeout(1500)
            inwin = sum(1 for t in found.values()
                        if t["handle"] == HANDLE and t["datetime"] and t["datetime"][:10] >= since)
            if inwin == prev:
                stagnant += 1
                if stagnant >= 3:
                    break
            else:
                stagnant = 0
            prev = inwin
        print(f"Yakalanan JSON sayfa: {pages['n']} | toplam obje: {len(found)} | pencere-ici: {prev}", flush=True)

    def media_files_for(t):
        if not t["media"]:
            return []
        folder = MEDYA / t["id"]
        if folder.exists():
            return [f"medya/{t['id']}/{f.name}" for f in sorted(folder.glob('*.jpg'))]
        out = []
        for j, u in enumerate(t["media"], 1):
            dest = folder / f"graf_{j:02d}.jpg"
            if download(u, dest):
                out.append(f"medya/{t['id']}/{dest.name}")
        return out

    # Koc tweetlerini ham satira cevir (since+ ve yeni olanlar)
    raw_rows = []
    koc_ids = set()
    quote_recs = []
    for t in found.values():
        if t.get("quoted_by"):
            quote_recs.append(t)  # ADIM 1: JSON'dan on-cikan alinti; ayrica islenir
            continue
        if t["handle"] != HANDLE or not t["datetime"]:
            continue
        if t["datetime"][:10] < since:
            continue
        row = {
            "id": t["id"], "text": t["text"], "locked": False,
            "datetime": t["datetime"], "lang": "tr",
            "isQuote": t["is_quote"], "media": t["media"],
            "mediaFiles": media_files_for(t),
        }
        if t["quoted_id"]:
            row["quoteOf"] = t["quoted_id"]
        if t["conv"] and t["conv"] != t["id"]:
            row["threadRoot"] = t["conv"]
        koc_ids.add(t["id"])
        raw_rows.append(row)

    # ADIM 1: alinti kayitlarini JSON'dan tam satir olarak ekle (parent Koc
    # tweet bu taramada kaydedildiyse). Bos/kilitli alintilar json_full olmaz
    # ve asama 2 (crawl_quote) tarafindan ziyaret edilmek uzere birakilir.
    pre_quote = 0
    for t in quote_recs:
        if t["quoted_by"] not in koc_ids:
            continue
        if not t.get("json_full") or not t["datetime"]:
            continue
        raw_rows.append({
            "id": t["id"], "text": t["text"], "locked": False,
            "datetime": t["datetime"], "lang": "tr",
            "isQuote": True, "quotedBy": t["quoted_by"],
            "quoteStub": False, "jsonFull": True,
            "media": t["media"], "mediaFiles": media_files_for(t),
        })
        pre_quote += 1

    new_recs = tt.scraped_to_records(raw_rows)
    by_id = {r.tweet_id: r for r in existing}
    added = sum(1 for r in new_recs if r.tweet_id not in by_id)
    for r in new_recs:
        by_id[r.tweet_id] = r
    tt.save_jsonl(list(by_id.values()), JSONL)
    print(f"\nIslenen satir: {len(raw_rows)} (JSON'dan on-cikan alinti: {pre_quote}) | "
          f"YENI eklenen: {added} | toplam {len(by_id)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
