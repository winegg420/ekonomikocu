#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ida ekran görüntüsü → mevcut dosyalara (ekstra AI dosyası YOK):
  cekilen_tweetler.jsonl, ekonomikocu_hafiza_v1.md (02),
  04_CLAUDE_GRAFIKLER.zip, 07_GRAFIKLER_GEMINI/ (medya/ ile aynı)

Kaynak (sadece geliştirici): _manuel_ekran/kayitlar.jsonl + gorseller/
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANUEL_DIR = ROOT / "_manuel_ekran"
KAYITLAR = MANUEL_DIR / "kayitlar.jsonl"
GORSEL_MAP = MANUEL_DIR / "gorsel_map.json"
GORSEL_DIR = MANUEL_DIR / "gorseller"
MEDYA = ROOT / "medya"

# Eski kök dosyalar (artık kullanılmıyor)
LEGACY = (
    ROOT / "manuel_ekran_kayitlari.jsonl",
    ROOT / "manuel_ekran_kronoloji.md",
)


def load_manual() -> list[dict]:
    src = KAYITLAR if KAYITLAR.is_file() else LEGACY[0]
    if not src.is_file():
        raise SystemExit(f"Eksik: {KAYITLAR}")
    rows = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def attach_screenshots(rows: list[dict]) -> int:
    """medya/TWEET_ID/graf_01.jpg — bot grafikleriyle aynı yapı."""
    if not GORSEL_MAP.is_file():
        return 0
    mapping = json.loads(GORSEL_MAP.read_text(encoding="utf-8"))
    n = 0
    GORSEL_DIR.mkdir(parents=True, exist_ok=True)
    for r in rows:
        tid = r.get("tweet_id") or ""
        fname = mapping.get(tid)
        if not fname:
            continue
        src = GORSEL_DIR / str(fname)
        if not src.is_file():
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                alt = GORSEL_DIR / (Path(str(fname)).stem + ext)
                if alt.is_file():
                    src = alt
                    break
            else:
                print(f"  >> Gorsel yok (atlandi): {tid} <- {fname}")
                continue
        dest_dir = MEDYA / tid
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "graf_01.jpg"
        if src.suffix.lower() in (".jpg", ".jpeg"):
            shutil.copy2(src, dest)
        else:
            try:
                from PIL import Image

                Image.open(src).convert("RGB").save(dest, "JPEG", quality=90)
            except ImportError:
                shutil.copy2(src, dest.with_suffix(src.suffix))
                dest = dest.with_suffix(src.suffix)
        rel = f"medya/{tid}/{dest.name}"
        r["media_files"] = [rel]
        r["media_urls"] = []
        n += 1
        print(f"  >> medya: {rel}")
    return n


def main() -> int:
    for p in LEGACY:
        if p.is_file():
            p.unlink()

    from tip_icerik import apply_to_record, record_from_json_obj
    from tweet_tara import JSONL_OUT, apply_to_hafiza, load_jsonl, save_jsonl

    manual = load_manual()
    g = attach_screenshots(manual)

    by_id = {r.tweet_id: r for r in load_jsonl(JSONL_OUT) if r.tweet_id}
    for o in manual:
        rec = record_from_json_obj(o)
        apply_to_record(rec)
        rec.analyzed = True
        if o.get("media_files"):
            rec.media_files = list(o["media_files"])
        if not (rec.baglanti or "").strip():
            rec.baglanti = "ekran görüntüsü (Ida); bot henüz bu tarihe inmedi"
        by_id[rec.tweet_id] = rec

    merged = sorted(by_id.values(), key=lambda r: r.sort_key(), reverse=True)
    save_jsonl(merged, JSONL_OUT)
    print(f"Manuel: {len(manual)} tweet | gorsel: {g} | JSONL: {len(merged)}")

    apply_to_hafiza(merged, ROOT / "ekonomikocu_hafiza_v1.md", False)
    try:
        from analiz_devam import run_full_analysis

        run_full_analysis(write_hafiza=True)
    except Exception as e:
        print(f"Analiz atlandi ({e})")

    subprocess.run([sys.executable, str(ROOT / "claude_paket_olustur.py")], check=False)
    print("Yapay zekaya AT: ayni 6+2 dosya (01,08,02,03,04,05 + 06,07) — yeni dosya yok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
