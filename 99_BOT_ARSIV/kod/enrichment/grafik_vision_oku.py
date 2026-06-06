#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oncelik 3 — grafik seviye okuma (vision).
Girdi: 05_GRAFIKLER.zip veya medya/ + 04_TWEETLER_v2.jsonl
Cikti: grafik_seviyeleri.jsonl
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from enrichment.common import LOG, ROOT, read_jsonl, setup_log, write_jsonl

OUT = ROOT / "grafik_seviyeleri.jsonl"
CHECKPOINT = ROOT / "99_BOT_ARSIV" / "log" / "grafik_vision_checkpoint.json"
BATCH_SAVE = 10

PROMPT = """Bu grafik @ekonomikocu (Turk teknik analist) tarafindan paylasilmis.
SADECE analistin ELLE cizdigi/yazdigi seviyeleri oku (yatay cizgi, kutu, ok, el yazisi etiket).
Platformun otomatik eksen/fiyat rakamlarini KARIŞTIRMA.

JSON olarak don (baska metin yok):
{
  "urun": "BTCUSD veya ETHUSD veya GENEL",
  "okunan_seviyeler": [sayi listesi, K=1000],
  "etiketler": ["el yazisi etiketler"],
  "senaryo_notu": "kisa Turkce ozet",
  "net_okunabilir": true veya false
}
Bulanik veya okunmuyorsa net_okunabilir:false ve okunan_seviyeler:[]"""

# Manuel dogrulanmis (vision ile kontrol edildi)
MANUEL: dict[str, dict] = {
    "2063250939578863720": {
        "urun": "BTCUSD",
        "okunan_seviyeler": [0, 17000, 19000, 33000, 60000, 100000, 150000],
        "etiketler": ["0 noktasi", "17 K", "19 K", "33 K", "60 K", "60K +1"],
        "senaryo_notu": "60K pivot. Yesil bolge ust trend ~150K; kirmizi alt trend ~10-100K bandi.",
        "net_okunabilir": True,
    },
    "1770898482808643726": {
        "urun": "BTCUSD",
        "okunan_seviyeler": [0, 17000, 19000, 33000, 60000, 100000, 150000],
        "etiketler": ["0 noktasi", "17 K", "19 K", "33 K", "60 K", "60K +1"],
        "senaryo_notu": "60K megafon grafigi — ust/alt senaryo kutulari.",
        "net_okunabilir": True,
    },
}


def _tweet_lookup() -> dict[str, dict]:
    src = ROOT / "04_TWEETLER_v2.jsonl"
    if not src.is_file():
        src = ROOT / "04_TWEETLER.jsonl"
    return {r["tweet_id"]: r for r in read_jsonl(src) if r.get("tweet_id")}


def _collect_images(tweets: dict[str, dict]) -> list[tuple[str, str, Path]]:
    """(tweet_id, zip_rel_path, local_path) — media_files kaynagi (tek gorsel listesi)."""
    items: list[tuple[str, str, Path]] = []
    seen: set[str] = set()

    for tid, row in tweets.items():
        for mf in row.get("media_files") or []:
            path = ROOT / str(mf).replace("\\", "/")
            if not path.is_file():
                continue
            stem = path.stem
            key = f"{tid}:{stem}"
            if key in seen:
                continue
            seen.add(key)
            gorsel = f"grafikler/{tid}_{stem}{path.suffix.lower()}"
            items.append((tid, gorsel, path))

    if not items:
        zip_path = ROOT / "05_GRAFIKLER.zip"
        if zip_path.is_file():
            tmp = ROOT / "99_BOT_ARSIV" / "_vision_tmp"
            tmp.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path) as zf:
                for name in zf.namelist():
                    if not name.lower().endswith((".jpg", ".jpeg", ".png")):
                        continue
                    base = Path(name).name
                    m = re.match(r"(\d+)_graf_\d+", base)
                    if not m:
                        continue
                    tid = m.group(1)
                    key = f"{tid}:{base}"
                    if key in seen:
                        continue
                    seen.add(key)
                    dest = tmp / base
                    if not dest.is_file():
                        dest.write_bytes(zf.read(name))
                    items.append((tid, name, dest))

    items.sort(key=lambda x: x[0], reverse=True)
    return items


def _load_done() -> set[str]:
    done: set[str] = set()
    if OUT.is_file():
        for r in read_jsonl(OUT):
            g = r.get("gorsel") or ""
            done.add(g)
    if CHECKPOINT.is_file():
        try:
            data = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
            done |= set(data.get("done") or [])
        except Exception:
            pass
    return done


def _save_checkpoint(done: set[str]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps({"done": sorted(done)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _vision_openai(img_path: Path) -> dict | None:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import urllib.request

        b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        mime = "image/jpeg" if img_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        body = {
            "model": os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            "max_tokens": 800,
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        LOG.warning("OpenAI vision hata: %s", e)
    return None


def _infer_urun(tweet: dict | None) -> str:
    if not tweet:
        return "GENEL"
    prods = tweet.get("products") or []
    if "BTC" in prods:
        return "BTCUSD"
    if "ETH" in prods:
        return "ETHUSD"
    text = (tweet.get("text") or "").upper()
    if "BTC" in text or "BITCOIN" in text:
        return "BTCUSD"
    if "ETH" in text:
        return "ETHUSD"
    if "NASDAQ" in text:
        return "NASDAQ"
    return "GENEL"


def process_image(tid: str, gorsel: str, path: Path, tweet: dict | None) -> dict:
    if tid in MANUEL:
        parsed = dict(MANUEL[tid])
    else:
        parsed = _vision_openai(path)
        if not parsed:
            parsed = {
                "urun": _infer_urun(tweet),
                "okunan_seviyeler": [],
                "etiketler": [],
                "senaryo_notu": "Vision API yok veya okunamadi — manuel kontrol gerekli.",
                "net_okunabilir": False,
            }

    return {
        "tweet_id": tid,
        "gorsel": gorsel.replace("\\", "/"),
        "urun": parsed.get("urun") or _infer_urun(tweet),
        "okunan_seviyeler": parsed.get("okunan_seviyeler") or [],
        "etiketler": parsed.get("etiketler") or [],
        "senaryo_notu": parsed.get("senaryo_notu") or "",
        "net_okunabilir": bool(parsed.get("net_okunabilir", False)),
    }


def main() -> int:
    setup_log("grafik_vision_oku")
    tweets = _tweet_lookup()
    images = _collect_images(tweets)
    done = _load_done()
    results = read_jsonl(OUT) if OUT.is_file() else []
    existing_gorsel = {r.get("gorsel") for r in results}

    LOG.info("Grafik sayisi: %d | once islenen: %d", len(images), len(done))
    has_api = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    if not has_api:
        LOG.info("OPENAI_API_KEY yok — manuel kayitlar + net_okunabilir:false")

    n = 0
    for tid, gorsel, path in images:
        if gorsel in done or gorsel in existing_gorsel:
            continue
        try:
            row = process_image(tid, gorsel, path, tweets.get(tid))
            results.append(row)
            done.add(gorsel)
            n += 1
            LOG.info("%s | net=%s | sev=%s", tid, row["net_okunabilir"], row["okunan_seviyeler"][:5])
            if n % BATCH_SAVE == 0:
                write_jsonl(OUT, results)
                _save_checkpoint(done)
            if has_api:
                time.sleep(0.5)
        except Exception as e:
            LOG.warning("Grafik atlandi %s: %s", gorsel, e)

    write_jsonl(OUT, results)
    _save_checkpoint(done)
    net_true = sum(1 for r in results if r.get("net_okunabilir"))
    LOG.info("BITTI: %d grafik | net_okunabilir=%d | false=%d",
             len(results), net_true, len(results) - net_true)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
