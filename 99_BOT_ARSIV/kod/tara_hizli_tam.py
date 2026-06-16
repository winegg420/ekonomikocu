# -*- coding: utf-8 -*-
"""TEK KOMUT — HIZLI + EKSIKSIZ tarama.

Son taramadan bugune: yeni tweet + flood + alinti + ABONE metin — dakikalar icinde.
Yavas adimlari (haftalik arama, 300-scroll profil) ATLAR; cunku abone oturumlu
hizli API taramasi zaten tum metni ceker.

Akis:
  0) Chrome 9222 (ABONE profili) canli mi? Degilse SESSIZ otomatik acar.
  1) tara_api.py      -> yeni tweet + flood + alinti baglantisi (GraphQL, hizli)
  2) alinti_tamamla   -> bekleyen alinti metinleri (tek tur)
  3) abone_etiketle   -> abone tweetleri isaretle
  4) claude_paket     -> 04/07 vb. yeniden uret
  5) kapsam_2026      -> rapor
  6) KAPSAM OZETI     -> normal + ABONE en yeni tarih ACIKCA yazilir

Kullanim: python kod/tara_hizli_tam.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
PY = sys.executable
SESS = Path(os.environ.get("LOCALAPPDATA", "")) / "ekonomikocu_x_session"
PORT = 9222

CEKILEN = ROOT / "cekilen_tweetler.jsonl"
ABONE = ROOT / "07_ABONE_TWEETLER.jsonl"


def _chrome_exe() -> str | None:
    for c in (
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ):
        if Path(c).is_file():
            return c
    return None


def _port_alive() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=4):
            return True
    except Exception:
        return False


def ensure_chrome() -> bool:
    """ABONE profilli sessiz Chrome'u garanti et (kapanmissa yeniden ac)."""
    if _port_alive():
        print(f"[chrome] 9222 zaten canli (abone oturumu).", flush=True)
        return True
    exe = _chrome_exe()
    if not exe:
        print("[chrome] chrome.exe bulunamadi!", flush=True)
        return False
    SESS.mkdir(parents=True, exist_ok=True)
    args = [
        exe,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={SESS}",
        "--lang=tr-TR",
        "--disable-features=Translate,TranslateUI,CalculateNativeWinOcclusion",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--window-position=-32000,-32000",
        "--window-size=1400,1000",
        "https://x.com/ekonomikocu",
    ]
    print("[chrome] 9222 kapali — sessiz ABONE Chrome aciliyor...", flush=True)
    subprocess.Popen(args, creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    for i in range(1, 19):  # ~90s
        time.sleep(5)
        if _port_alive():
            print(f"[chrome] canli ({i*5}s).", flush=True)
            time.sleep(4)  # feed otursun
            return True
        print(f"[chrome] bekleniyor ({i*5}/90s)...", flush=True)
    print("[chrome] ACILAMADI — abone oturumu icin CHROME_X.bat ile giris gerekebilir.", flush=True)
    return False


def step(title: str, cmd: list[str]) -> int:
    print("\n" + "=" * 56 + f"\n{title}\n" + "=" * 56, flush=True)
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def _newest(path: Path) -> tuple[int, str | None]:
    if not path.is_file():
        return 0, None
    dates = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            dt = json.loads(line).get("datetime")
            if dt and str(dt)[:1].isdigit():
                dates.append(str(dt))
        except Exception:
            pass
    dates.sort()
    return len(dates), (dates[-1] if dates else None)


def main() -> int:
    t0 = time.time()
    if not ensure_chrome():
        print("\n!! Chrome/abone oturumu yok — tarama yarim kalabilir.", flush=True)

    base = [PY, str(KOD / "tara_api.py")]
    step("1/5 Yeni tweet + flood + alinti (hizli API)", base)
    step("2/5 Bekleyen alinti metinleri", [
        PY, str(KOD / "alinti_tamamla.py"), "--attach-port", str(PORT),
        "--require-cdp", "--max-rounds", "2", "--per-round", "40", "--no-loop",
    ])
    step("3/5 Abone tweetleri isaretle", [PY, str(KOD / "abone_etiketle.py")])
    step("4/5 Paket yeniden uret (04/07)", [PY, str(KOD / "claude_paket_olustur.py")])
    step("5/5 Kapsam raporu", [PY, str(KOD / "kapsam_2026.py")])

    n_all, d_all = _newest(CEKILEN)
    n_ab, d_ab = _newest(ABONE)
    dur = int(time.time() - t0)
    print("\n" + "#" * 56)
    print("# KAPSAM OZETI")
    print("#" * 56)
    print(f"# Normal tweet : {n_all:>6}  | en yeni: {d_all}")
    print(f"# ABONE tweet  : {n_ab:>6}  | en yeni: {d_ab}")
    print(f"# Sure: {dur}s")
    if d_all and d_ab and d_ab[:10] < d_all[:10]:
        print("# !! UYARI: ABONE tweetler normalden GERIDE — abone oturumu eksik olabilir.")
    else:
        print("# OK: abone tweetler gunceli yakaladi.")
    print("#" * 56, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
