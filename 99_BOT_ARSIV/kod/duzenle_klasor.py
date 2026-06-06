#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kök klasörü sadeleştir: Claude 00-06 üstte, geri kalan 99_BOT_ARSIV."""
from __future__ import annotations

import shutil
from pathlib import Path

def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "cekilen_tweetler.jsonl").is_file():
        return here
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return here.parent.parent


ROOT = _project_root()
ARSIV = ROOT / "99_BOT_ARSIV"
KOD = ARSIV / "kod"
CALISTIR = ARSIV / "calistir"
GEMINI = ARSIV / "gemini"
VERI = ARSIV / "veri_yedek"

CLAUDE_ROOT = {
    "00_OKU_YUKLEME_SIRASI.txt",
    "01_BURADAN_BASLA.md",
    "02_MENTOR_REHBERI.md",
    "03_HAFIZA.md",
    "04_TWEETLER.jsonl",
    "05_GRAFIKLER.zip",
    "06_ANALIZ.md",
    "07_ABONE_TWEETLER.jsonl",
    "08_TWEETLER_GEMINI.md",
    "09_GRAFIKLER_GEMINI",
    "10_ABONE_TWEETLER_GEMINI.md",
    "TARAMA_DURUMU.md",
    "tara_kapsam.json",
    "tara_bookmark.json",
}

KEEP_ROOT = CLAUDE_ROOT | {
    "cekilen_tweetler.jsonl",
    "ekonomikocu_hafiza_v1.md",
    "duzenle_klasor.py",
    "CLAUDE_AT_BURADAN.bat",
    "GEMINI_AT_BURADAN.bat",
    "medya",
}

MOVE_DIRS = (
    "00_CLAUDE_YUKLE",
    "claude_yukle",
    "_claude_zip_build",
    "_manuel_ekran",
    "x_arsiv",
)

OLD_CLAUDE_NAMES = (
    "00_CLAUDE_ATMA_SIRASI.md",
    "01_CLAUDE_BURADAN_BASLA.md",
    "02_ekonomikocu_hafiza_CLAUDE.md",
    "03_cekilen_tweetler_CLAUDE.jsonl",
    "04_CLAUDE_GRAFIKLER.zip",
    "05_CLAUDE_ANALIZ.md",
    "08_AI_MENTOR_REHBERI.md",
    "06_tweetler_GEMINI.md",
    "07_GRAFIKLER_GEMINI",
)


def _ensure_dirs() -> None:
    for d in (ARSIV, KOD, CALISTIR, GEMINI, VERI, ARSIV / "test", ARSIV / "log"):
        d.mkdir(parents=True, exist_ok=True)


def _move(path: Path, dest_dir: Path) -> None:
    if not path.exists():
        return
    dest = dest_dir / path.name
    if dest.exists():
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        return
    shutil.move(str(path), str(dest))


def main() -> int:
    _ensure_dirs()

    for name in MOVE_DIRS:
        _move(ROOT / name, ARSIV)

    for name in OLD_CLAUDE_NAMES:
        _move(ROOT / name, VERI / "eski_claude_adlari")

    for p in ROOT.glob("_test_*.py"):
        _move(p, ARSIV / "test")
    for p in ROOT.glob("_debug_*.py"):
        _move(p, ARSIV / "test")
    for name in ("_heal_x_page.py",):
        _move(ROOT / name, ARSIV / "test")

    for p in ROOT.glob("*.bat"):
        if p.name == "CLAUDE_AT_BURADAN.bat":
            continue
        _move(p, CALISTIR)

    for p in ROOT.glob("*.ps1"):
        _move(p, CALISTIR)

    for p in ROOT.glob("*log*.txt"):
        _move(p, ARSIV / "log")
    for name in (
        "tarama_log.txt",
        "CLAUDE_AT.txt",
        "GEMINI_AT.txt",
        "IDA_YENI_SOHBET.txt",
        "ALINTI_TAMAMLA_OKU.txt",
        "ham_veri.txt",
        "ham_veri_ornek.txt",
    ):
        _move(ROOT / name, ARSIV / "log")

    for name in ("vizyon_seviye.jsonl", "alinti_bekleyen.jsonl", "tara_bookmark.json"):
        _move(ROOT / name, VERI)

    if (ROOT / "ekonomikocu_hafiza_v1.md.bak").exists():
        _move(ROOT / "ekonomikocu_hafiza_v1.md.bak", VERI)

    for p in ROOT.glob("*.py"):
        if p.name in KEEP_ROOT:
            continue
        _move(p, KOD)

    if (ROOT / ".cursor").exists():
        _move(ROOT / ".cursor", ARSIV)

    for name in ("requirements.txt", "vizyon_seviye.jsonl", "abone_tamamla_log.txt"):
        _move(ROOT / name, ARSIV / "log" if name.endswith(".txt") and "log" in name else ARSIV)

    if (ROOT / ".x_session").exists():
        _move(ROOT / ".x_session", ARSIV)

    me = ROOT / "duzenle_klasor.py"
    if me.exists():
        _move(me, KOD)

    # Kökte tek tık: paket yenile
    bat = ROOT / "CLAUDE_AT_BURADAN.bat"
    for name, msg in (
        (
            "CLAUDE_AT_BURADAN.bat",
            "echo Claude + Gemini dosyalari guncellendi — 00_OKU_YUKLEME_SIRASI.txt bak.\n",
        ),
        (
            "GEMINI_AT_BURADAN.bat",
            "echo Gemini dosyalari guncellendi — 08, 09, 10 (+ once 01-06).\n",
        ),
    ):
        (ROOT / name).write_text(
            "@echo off\n"
            f"cd /d \"%~dp0\"\n"
            "python \"99_BOT_ARSIV\\kod\\claude_paket_olustur.py\"\n"
            "echo.\n"
            f"{msg}"
            "pause\n",
            encoding="utf-8",
        )

    print("Temizlendi. Kok klasorde yukleme dosyalari:")
    for n in sorted(CLAUDE_ROOT):
        ok = (ROOT / n).exists()
        print(f"  {'OK' if ok else 'YOK'} {n}")
    print(f"Diger her sey: {ARSIV.name}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
