#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grafik paketinden cikarilacak alakasiz medya (hisse logosu, kart, profil)."""
from __future__ import annotations

import re
from pathlib import Path

IRRELEVANT_URL_RX = re.compile(
    r"abs\.twimg\.com/finance|/finance/v1/stock/|profile_images|emoji|card_img",
    re.I,
)

# X link onizleme / konu disi dekoratif foto (drone-PLTR tweetleri)
BLOCKED_MEDIA_ID_RX = re.compile(r"HJ-8ZGrXsAAaPSb", re.I)

GRAF_IDX_RX = re.compile(r"graf_(\d+)", re.I)


def graf_index(rel_path: str) -> int:
    m = GRAF_IDX_RX.search(rel_path or "")
    return int(m.group(1)) if m else 0


def is_irrelevant_media_url(url: str) -> bool:
    u = url or ""
    return bool(IRRELEVANT_URL_RX.search(u) or BLOCKED_MEDIA_ID_RX.search(u))


def is_stock_logo_file(path: Path) -> bool:
    """X hisse karti: ~128x128 kucuk PNG."""
    if not path.is_file():
        return False
    if path.suffix.lower() != ".png" or path.stat().st_size > 20_000:
        return False
    try:
        from PIL import Image

        with Image.open(path) as im:
            w, h = im.size
            return max(w, h) <= 200 and min(w, h) <= 160
    except Exception:
        return path.stat().st_size < 8_000


def should_drop_media(url: str, file_rel: str | None, root: Path | None = None) -> bool:
    if is_irrelevant_media_url(url):
        return True
    if file_rel and root is not None:
        p = root / Path(str(file_rel).replace("\\", "/"))
        if is_stock_logo_file(p):
            return True
    return False


def filter_row_media(
    r: dict, root: Path
) -> tuple[list[str], list[str], list[str]]:
    """(yeni_urls, yeni_files, silinen_dosya_yollari)"""
    urls = list(r.get("media_urls") or [])
    files = list(r.get("media_files") or [])
    by_idx = {graf_index(f): f for f in files if graf_index(f)}
    tid = str(r.get("tweet_id") or "")
    new_urls: list[str] = []
    new_files: list[str] = []
    removed_paths: list[str] = []

    for i, url in enumerate(urls, 1):
        rel = by_idx.get(i)
        if should_drop_media(url, rel, root):
            if rel:
                p = root / Path(rel.replace("\\", "/"))
                if p.is_file():
                    removed_paths.append(rel)
                    p.unlink()
            continue
        new_urls.append(url)
        if rel:
            new_files.append(rel)

    kept_idx = {graf_index(f) for f in new_files}
    for idx, rel in by_idx.items():
        if idx in kept_idx:
            continue
        p = root / Path(rel.replace("\\", "/"))
        if p.is_file() and is_stock_logo_file(p):
            removed_paths.append(rel)
            p.unlink()

    # URL var, dosya eslesmedi (graf_04 gibi) — diskten grafikleri bagla
    if new_urls and len(new_files) < len(new_urls):
        medya_dir = root / "medya" / tid
        if medya_dir.is_dir():
            on_disk = sorted(
                [
                    f
                    for f in medya_dir.iterdir()
                    if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
                    and f.stat().st_size > 800
                    and not is_stock_logo_file(f)
                ],
                key=lambda p: graf_index(p.name) or 999,
            )
            have = {Path(x).name for x in new_files}
            for f in on_disk:
                rel = f"medya/{tid}/{f.name}".replace("\\", "/")
                if f.name not in have and rel not in new_files:
                    new_files.append(rel)
                    have.add(f.name)
                if len(new_files) >= len(new_urls):
                    break

    return new_urls, new_files, removed_paths
