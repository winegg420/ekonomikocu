#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 %100 tamamlama — ana tweet + abone + alinti + #FLOOD.

Tamamlaninca cikis 0. Degilse dongu (max 6 tur) veya cikis 1.
2025 taramasi BURADA YOK — once 2026 bitmeli (tara_2025_devam.py).

Chrome: CHROME_X.bat (9222), abone oturumu.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

YIL_SINCE = "2026-01-01"
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--pause", "4500", "--skip-media"]


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable
MAX_TUR = 6


def run(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def kapsam_tamam() -> bool:
    import importlib.util

    spec = importlib.util.spec_from_file_location("kapsam_2026", KOD / "kapsam_2026.py")
    if not spec or not spec.loader:
        return False
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return bool(mod.analyze().get("tamam"))


def tur_n(tur: int) -> None:
    base = [PY, str(KOD / "tweet_tara.py"), *CDP]

    run(
        f"TUR {tur}/6 — Onceki takilanlar (limit dolmus)",
        [
            PY,
            str(KOD / "tara_ilerle.py"),
            "--give-up-locked",
            "--since",
            YIL_SINCE,
        ],
    )

    run(
        f"TUR {tur}/6 — Abone metin (2026 bos kilitli)",
        [
            PY,
            str(KOD / "abone_tamamla.py"),
            "--since",
            YIL_SINCE,
            "--per-round",
            "400",
            "--max-rounds",
            "12",
            "--max-id-attempts",
            "5",
            "--max-stall-rounds",
            "2",
            "--profile-scroll",
            "120",
            "--stall-sec",
            "180",
            "--no-pack",
        ],
    )

    run(
        f"TUR {tur}/6 — #FLOOD thread parcalari",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "2",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    run(
        f"TUR {tur}/6 — Alintilar",
        [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "4", "--per-round", "40"],
    )

    run(
        f"TUR {tur}/6 — #FLOOD 2. tur",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "1",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    run(
        f"TUR {tur}/6 — #FLOOD takilanlari isaretle",
        [PY, str(KOD / "tara_ilerle.py"), "--give-up-flood"],
    )

    # Haziran kesif (yeni tweet)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    run(
        f"TUR {tur}/6 — Haziran kesif",
        base
        + [
            "--since-date",
            "2026-06-01",
            "--until-date",
            tomorrow,
            "--max-scroll",
            "35",
            "--pause",
            "2000",
            "--no-finish-quotes",
            "--fast-period",
            "--skip-media",
        ],
    )


def main() -> int:
    from tara_lock import acquire, release

    if not acquire("tara_2026_bitir"):
        return 3
    try:
        return _main()
    finally:
        release()


def _main() -> int:
    subprocess.run([PY, str(KOD / "kapsam_2026.py")], cwd=ROOT, check=False)

    if kapsam_tamam():
        print("\n2026 zaten %100 — 2025 icin: tara_2025_devam.py", flush=True)
        subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
        return 0

    for tur in range(1, MAX_TUR + 1):
        print(f"\n>>> 2026 TAMAMLAMA TURU {tur}/{MAX_TUR}", flush=True)
        tur_n(tur)
        subprocess.run([PY, str(KOD / "abone_etiketle.py")], cwd=ROOT, check=False)
        subprocess.run([PY, str(KOD / "alinti_dogrula.py")], cwd=ROOT, check=False)
        rc = subprocess.run([PY, str(KOD / "kapsam_2026.py")], cwd=ROOT).returncode
        if rc == 0:
            subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
            print("\n2026 %100 TAMAM — simdi 2025: tara_2025_devam.py", flush=True)
            return 0

    print(f"\n2026 hala eksik — {MAX_TUR} tur bitti. TARAMA_2026.md kontrol et.", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
