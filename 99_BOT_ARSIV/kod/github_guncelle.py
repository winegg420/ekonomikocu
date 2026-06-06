#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paket sonrasi degisiklikleri GitHub'a gonder."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _project_root() -> Path:
    here = Path(__file__).resolve().parent
    up = here.parent.parent
    if (up / "cekilen_tweetler.jsonl").is_file():
        return up
    return up


ROOT = _project_root()
REMOTE = "https://github.com/winegg420/ekonomikocu.git"


def run(cmd: list[str], cwd: Path) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=cwd).returncode


def main() -> int:
    if not (ROOT / ".git").is_dir():
        run(["git", "init"], ROOT)
        run(["git", "branch", "-M", "main"], ROOT)
    r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        run(["git", "remote", "add", "origin", REMOTE], ROOT)
    else:
        run(["git", "remote", "set-url", "origin", REMOTE], ROOT)

    run(["git", "add", "-A"], ROOT)
    if run(["git", "diff", "--cached", "--quiet"], ROOT) == 0:
        print("Degisiklik yok — push atlandi.")
        return 0

    msg = f"guncelleme {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if run(["git", "commit", "-m", msg], ROOT) != 0:
        print("Commit basarisiz (belki degisiklik yok).")
        return 1
    code = run(["git", "push", "-u", "origin", "main"], ROOT)
    if code != 0:
        run(["git", "push", "origin", "main"], ROOT)
    print("GitHub guncellendi:", REMOTE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
