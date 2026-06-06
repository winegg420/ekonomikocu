#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025 ve oncesi tarama — SADECE 2026 %100 olduktan sonra calistir.

Sira:
  1) 2026 kapisi (degilse dur)
  2) 2025 haftalik X aramasi (2025-01-01 .. 2026-01-01)
  3) Profil kaydirma (2025-01-01'e kadar)
  4) Alinti + #FLOOD + abone
  5) kapsam_durum + paket
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

HEDEF = "2025-01-01"
CDP = ["--attach-port", "9222", "--require-cdp"]
COMMON = ["--skip-hafiza", "--pause", "4000", "--skip-media"]


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
KOD = Path(__file__).resolve().parent
PY = sys.executable


def run(label: str, cmd: list[str]) -> int:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def week_ranges(since: str, until: str) -> list[tuple[str, str]]:
    s = datetime.fromisoformat(since + "T00:00:00")
    e = datetime.fromisoformat(until + "T00:00:00")
    out: list[tuple[str, str]] = []
    cur = s
    while cur < e:
        nxt = min(cur + timedelta(days=7), e)
        out.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt
    return out


def kapsam_2026_tamam() -> bool:
    import importlib.util

    spec = importlib.util.spec_from_file_location("kapsam_2026", KOD / "kapsam_2026.py")
    if not spec or not spec.loader:
        return False
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return bool(mod.analyze().get("tamam"))


def main() -> int:
    if not kapsam_2026_tamam():
        print(
            "\nDURDURULDU: 2026 henuz %100 degil.\n"
            "Once calistir: tara_2026_bitir.py veya TARA_2026_BITIR.bat\n",
            flush=True,
        )
        subprocess.run([PY, str(KOD / "kapsam_2026.py")], cwd=ROOT, check=False)
        return 2

    print("\n2026 %100 — 2025 taramasina geciliyor...\n", flush=True)
    base = [PY, str(KOD / "tweet_tara.py"), *CDP]

    for a, b in week_ranges("2025-01-01", "2026-01-01"):
        run(
            f"2025 arama {a} .. {b}",
            base
            + [
                "--since-date",
                a,
                "--until-date",
                b,
                "--max-scroll",
                "50",
                "--pause",
                "2000",
                "--no-finish-quotes",
                "--fast-period",
                "--skip-media",
            ],
        )

    run(
        "Profil — 2025-01-01'e kadar",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "900",
            "--stop-before",
            HEDEF,
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    run("Alintilar", [PY, str(KOD / "alinti_tamamla.py"), "--max-rounds", "4", "--per-round", "50"])

    run(
        "Alinti flood (2025 — status sayfasi)",
        [
            PY,
            str(KOD / "alinti_flood_tara.py"),
            "--yil",
            "2025",
            "--attach-port",
            "9222",
            "--max-scroll",
            "45",
            "--discover",
            "0",
            "--no-pack",
        ],
    )

    run(
        "#FLOOD",
        base
        + [
            "--profile-only",
            "--max-scroll",
            "3",
            "--finish-threads",
            "--no-finish-quotes",
            *COMMON,
        ],
    )

    run(
        "#FLOOD takilanlari isaretle",
        [PY, str(KOD / "tara_ilerle.py"), "--give-up-flood"],
    )

    run(
        "Abone metin (2025+)",
        [
            PY,
            str(KOD / "abone_tamamla.py"),
            "--since",
            "2025-01-01",
            "--per-round",
            "300",
            "--max-rounds",
            "15",
            "--max-id-attempts",
            "5",
            "--max-stall-rounds",
            "2",
            "--no-pack",
        ],
    )

    subprocess.run([PY, str(KOD / "kapsam_2025.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "kapsam_durum.py")], cwd=ROOT, check=False)
    subprocess.run([PY, str(KOD / "claude_paket_olustur.py")], cwd=ROOT, check=False)
    print("\n2025 tarama turu bitti — TARAMA_DURUMU.md", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
