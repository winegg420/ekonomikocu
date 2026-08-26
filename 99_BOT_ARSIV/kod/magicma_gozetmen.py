# -*- coding: utf-8 -*-
"""MagicMA gozetmeni: dayanikli kosucuyu calistirir; Chrome olurse SADECE
ekonomikocu_x_session profilinin chrome.exe sureclerini oldurup yeniden acar,
TradingView layout sekmesini yukler ve kosucuyu resume ile surdurur.
2 tur ust uste ilerleme yoksa durur."""
from __future__ import annotations
import json, os, subprocess, sys, time, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(r"C:\Users\ida\Desktop\ekonomikocu")
KOD = ROOT / "99_BOT_ARSIV" / "kod"
HAM = KOD / "magicma_ham.jsonl"
TV = "https://tr.tradingview.com/chart/zOsq3cIW/"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SESS = os.path.join(os.environ["LOCALAPPDATA"], "ekonomikocu_x_session")
PY = sys.executable
BUGUN = date.today().isoformat()
# Bir kosucu turunun ust siniri (sn). Kisa tutulursa (5 dk) listenin basindaki
# okunamayan semboller her turda bastan denenir ve tur suresinin cogu orada
# harcanir: 2026-08-26'da 5 dk'lik turda sadece 3 sembol ilerlenebildi.
TUR_SN = int(os.environ.get("MAGICMA_TUR_SN", "1500"))


def log(m: str) -> None:
    print(f"[gozetmen {time.strftime('%H:%M:%S')}] {m}", flush=True)


def bugun_sayisi() -> int:
    if not HAM.exists():
        return 0
    n = 0
    with HAM.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                if (json.loads(line).get("ts") or "").startswith(BUGUN):
                    n += 1
            except Exception:
                pass
    return n


def cdp_var() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5):
            return True
    except Exception:
        return False


def chrome_yenile() -> None:
    """SADECE tarama profilinin Chrome'unu oldur, yeniden ac."""
    ps = (
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
        "Where-Object { $_.CommandLine -like '*ekonomikocu_x_session*' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
    time.sleep(4)
    subprocess.Popen(
        [CHROME, "--remote-debugging-port=9222", f"--user-data-dir={SESS}",
         "--lang=tr-TR", "--disable-features=Translate,TranslateUI",
         "--no-first-run", "--no-default-browser-check", "about:blank", TV],
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
    )
    for _ in range(20):
        time.sleep(2)
        if cdp_var():
            break
    time.sleep(20)  # TradingView layout + gostergeler yuklensin
    log("Chrome yenilendi.")


def tv_saglik() -> bool:
    """TradingView sekmesi bos mu? Bos ise yeniden yukle.
    2026-08-26: TV sayfasi cokunce body bombos kaliyor ve TUM semboller
    'okunamadi (timeout)' veriyor — ABD hisselerinin tamami bu yuzden atlandi."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return True
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            ctx = b.contexts[0]
            tvs = [q for q in ctx.pages if "tradingview.com" in (q.url or "")]
            if not tvs:
                pg = ctx.new_page()
                pg.goto(TV, wait_until="domcontentloaded", timeout=90_000)
                pg.wait_for_timeout(25_000)
                log("TV sekmesi yoktu — acildi.")
                return True
            pg = tvs[0]
            txt = pg.evaluate("()=>(document.body&&document.body.innerText||'').length")
            if txt and txt > 60:
                return True
            log(f"TV sayfasi bos (innerText={txt}) — yeniden yukleniyor.")
            pg.goto(TV, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(25_000)
            txt = pg.evaluate("()=>(document.body&&document.body.innerText||'').length")
            log(f"TV yeniden yuklendi (innerText={txt}).")
            return bool(txt and txt > 60)
    except Exception as e:
        log(f"TV saglik kontrolu yapilamadi: {e}")
        return True


def main() -> int:
    tur = 0
    ilerlemesiz = 0
    onceki = bugun_sayisi()
    log(f"Baslangic: bugun taranmis {onceki} sembol")
    while tur < 90:
        tur += 1
        if not cdp_var():
            log("CDP yok — Chrome yenileniyor.")
            chrome_yenile()
        tv_saglik()
        log(f"Tur {tur}: kosucu baslatiliyor...")
        try:
            subprocess.run([PY, str(KOD / "magicma_tara_dayanikli.py")],
                           cwd=str(ROOT), check=False, timeout=TUR_SN)
        except subprocess.TimeoutExpired:
            log(f"Kosucu {TUR_SN // 60} dk turunu doldurdu — TV kontrolu icin donuluyor.")
        simdi = bugun_sayisi()
        log(f"Tur {tur} bitti: bugun taranmis {simdi} sembol (+{simdi - onceki})")
        if simdi <= onceki:
            ilerlemesiz += 1
            if ilerlemesiz >= 2:
                log("2 tur ust uste ilerleme yok — duruluyor.")
                return 1
            chrome_yenile()
        else:
            ilerlemesiz = 0
        onceki = simdi
        # Kosucu kendi kendine bitti mi? Kalan sembol yoksa cik.
        if simdi > 0 and _kalan_yok():
            log("Tum semboller tarandi.")
            return 0
    log("Tur siniri doldu.")
    return 1


def _kalan_yok() -> bool:
    """Kosucu 'tamamlandi' isaretini birakti mi — son ciktisindan anlasilmazsa
    sembol listesi ile bugunku kayitlari karsilastir."""
    try:
        sys.path.insert(0, str(KOD))
        import magicma_yakinlik as my  # noqa
        semboller = my.sembolleri_yukle() if hasattr(my, "sembolleri_yukle") else None
        if not semboller:
            return False
        bugunku = set()
        with HAM.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if (d.get("ts") or "").startswith(BUGUN):
                        bugunku.add(d.get("sembol"))
                except Exception:
                    pass
        return len(bugunku) >= len(set(semboller))
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
