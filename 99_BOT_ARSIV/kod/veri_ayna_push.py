#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ham veri aynasi: 3 veri dosyasini public ekonomikocu-veri reposuna gonderir.

Ayna calisma klasoru ana repo DISINDA tutulur (%LOCALAPPDATA%), boylece ana
repoya hicbir sey sizmaz. LFS KULLANILMAZ - dosyalar birkac MB, duz blob.

Kullanim:  python veri_ayna_push.py
Cikis: 0 basarili/degisiklik yok, 1 hata. Ana tarama akisini BOZMAZ.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
REMOTE = "https://github.com/winegg420/ekonomikocu-veri.git"

# (ana repodaki kaynak yol, ayna repodaki hedef ad)
DOSYALAR = [
    ("04_TWEETLER.jsonl", "04_TWEETLER.jsonl"),
    ("07_ABONE_TWEETLER.jsonl", "07_ABONE_TWEETLER.jsonl"),
    ("99_BOT_ARSIV/kod/magicma_ham.jsonl", "magicma_ham.jsonl"),
]


def _ayna_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "ekonomikocu_veri_ayna"


def run(cmd: list[str], cwd: Path, sessiz: bool = False) -> int:
    """Komutu calistir, cikis kodunu dondur. Sessizde ciktiyi yutar."""
    try:
        if sessiz:
            return subprocess.run(cmd, cwd=str(cwd), capture_output=True).returncode
        print("+", " ".join(cmd), flush=True)
        return subprocess.run(cmd, cwd=str(cwd)).returncode
    except Exception as e:
        print(f"[ayna] komut hatasi ({' '.join(cmd)}): {e}", flush=True)
        return 1


def _depo_hazirla(ayna: Path) -> bool:
    """Ayna klasorunu ve git deposunu kur, uzaktaki gecmisin ustune otur."""
    try:
        ayna.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[ayna] klasor olusturulamadi: {e}", flush=True)
        return False

    if not (ayna / ".git").is_dir():
        if run(["git", "init", "-q"], ayna) != 0:
            return False
        run(["git", "branch", "-M", "main"], ayna, sessiz=True)

    if run(["git", "remote", "get-url", "origin"], ayna, sessiz=True) != 0:
        run(["git", "remote", "add", "origin", REMOTE], ayna, sessiz=True)
    else:
        run(["git", "remote", "set-url", "origin", REMOTE], ayna, sessiz=True)

    # Uzakta gecmis varsa onun ustune otur (yoksa ilk push olur).
    if run(["git", "fetch", "-q", "--no-tags", "origin", "main"], ayna, sessiz=True) == 0:
        run(["git", "reset", "--soft", "origin/main"], ayna, sessiz=True)
    return True


def main() -> int:
    ayna = _ayna_dir()
    if not _depo_hazirla(ayna):
        print("[ayna] depo hazirlanamadi - push atlandi", flush=True)
        return 1

    kopyalanan = 0
    for kaynak_rel, hedef_ad in DOSYALAR:
        kaynak = ROOT / kaynak_rel
        if not kaynak.is_file():
            print(f"[ayna] UYARI: {kaynak_rel} yok, atlandi", flush=True)
            continue
        try:
            shutil.copy2(kaynak, ayna / hedef_ad)
            kopyalanan += 1
        except Exception as e:
            print(f"[ayna] {kaynak_rel} kopyalanamadi: {e}", flush=True)

    if kopyalanan == 0:
        print("[ayna] kopyalanacak dosya yok - push atlandi", flush=True)
        return 1

    if run(["git", "add", "-A"], ayna, sessiz=True) != 0:
        print("[ayna] git add basarisiz", flush=True)
        return 1

    if run(["git", "diff", "--cached", "--quiet"], ayna, sessiz=True) == 0:
        print("[ayna] Degisiklik yok - push atlandi.", flush=True)
        return 0

    msg = f"veri guncelleme {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if run(["git", "commit", "-q", "-m", msg], ayna) != 0:
        print("[ayna] commit basarisiz", flush=True)
        return 1

    code = run(["git", "push", "-u", "origin", "main"], ayna)
    if code != 0:
        code = run(["git", "push", "origin", "main"], ayna)
    if code != 0:
        print("[ayna] HATA: push basarisiz, ayna repo guncellenmedi", flush=True)
        return 1

    print(f"[ayna] Guncellendi ({kopyalanan} dosya): {REMOTE}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:  # beklenmeyen her sey - akisi bozma
        print(f"[ayna] beklenmeyen hata: {e}", flush=True)
        raise SystemExit(1)
