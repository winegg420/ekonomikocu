#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ortak IO ve log yardimcilari."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterator

LOG = logging.getLogger("enrichment")


def project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent.parent
    if (up / "04_TWEETLER.jsonl").is_file():
        return up
    return up


ROOT = project_root()


def setup_log(name: str) -> Path:
    log_dir = ROOT / "99_BOT_ARSIV" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{name}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[
            logging.FileHandler(path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    return path


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            LOG.warning("JSON hata %s satir %d: %s", path.name, i, e)
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict]]:
    if not path.is_file():
        return iter(())
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            yield i, json.loads(line)
        except json.JSONDecodeError as e:
            LOG.warning("JSON hata %s satir %d: %s", path.name, i, e)
