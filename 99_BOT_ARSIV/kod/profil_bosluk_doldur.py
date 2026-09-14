# -*- coding: utf-8 -*-
"""Tarama sonrasi bosluk doldurma: @ekonomikocu Yanitlar (with_replies) akisini
verilen tarihe kadar kaydirir, arsivde olmayan tweetleri article'dan DOGRUDAN
kaydeder. Status sayfasi tek tek ACILMAZ -> X'in ~100 sayfa / 15 dk kisitina
takilmaz.

Neden (2026-09-14): tweet_tara profil kaydirmasi kronolojik olmayan akista
birkac scroll'da "yeni yok" deyip durabiliyor; 4-13 Eylul arasi 672 tweet
sessizce kacti (exit 0). Bu kosucu ayni gun elle calistirildiginda 50 scroll'da
337 eksigin tamamini kisitsiz topladi.

Kullanim:
  py -3 profil_bosluk_doldur.py --alt-sinir 2026-09-10
  py -3 profil_bosluk_doldur.py --alt-sinir 2026-09-10 --max-scroll 300

Cikis: 0 = tamam, 1 = CDP/sayfa hatasi (arsive yazilan korunur).
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KOD = Path(__file__).resolve().parent
if str(KOD) not in sys.path:
    sys.path.insert(0, str(KOD))

import tweet_tara as tt  # noqa: E402

ROOT = KOD.parent.parent
JSONL = tt.JSONL_OUT
MEDYA = ROOT / "medya"
URL = "https://x.com/ekonomikocu/with_replies"
BOS_SCROLL_LIMIT = 10
KAYIT_PARTI = 20

# Yalnizca @ekonomikocu'nun kendi tweetleri: zaman damgasi linki
# /ekonomikocu/status/<id> olan article'lar (alinti/yanitlanan baskalari atlanir).
JS = r"""
() => Array.from(document.querySelectorAll('article')).map(art => {
  const t = art.querySelector('time');
  const a = t ? t.closest('a') : null;
  const href = a ? (a.getAttribute('href') || '') : '';
  const m = href.match(/^\/ekonomikocu\/status\/(\d+)/i);
  if (!m) return null;
  const textEl = art.querySelector("div[data-testid='tweetText']");
  return {
    id: m[1],
    datetime: t.getAttribute('datetime'),
    text: textEl ? textEl.innerText : '',
    kesik: !!art.querySelector("[data-testid='tweet-text-show-more-link']"),
    imgs: Array.from(art.querySelectorAll("img[src*='pbs.twimg.com/media']")).map(i => i.getAttribute('src')),
  };
}).filter(Boolean)
"""


def _log(msg: str) -> None:
    print(f"[bosluk] {msg}", flush=True)


def norm_img(src: str) -> str:
    m = re.search(r"/media/([A-Za-z0-9_\-]+)", src or "")
    return f"https://pbs.twimg.com/media/{m.group(1)}?format=jpg&name=large" if m else src


def indir(url: str, hedef: Path) -> bool:
    try:
        hedef.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            hedef.write_bytes(r.read())
        return True
    except Exception as e:
        _log(f"medya inmedi {url[:60]}: {e}")
        return False


def satir(d: dict) -> dict:
    tid = d["id"]
    klasor = MEDYA / tid
    dosyalar = [f"medya/{tid}/{f.name}" for f in sorted(klasor.glob("*.jpg"))] if klasor.exists() else []
    gorulen: set[str] = set()
    imgs = [u for u in (norm_img(s) for s in (d.get("imgs") or [])) if not (u in gorulen or gorulen.add(u))]
    if imgs and not dosyalar:
        for i, u in enumerate(imgs, 1):
            hedef = klasor / f"graf_{i:02d}.jpg"
            if indir(u, hedef):
                dosyalar.append(f"medya/{tid}/{hedef.name}")
    return {"id": tid, "text": d["text"].strip(), "locked": False, "datetime": d.get("datetime"),
            "isQuote": False, "lang": "tr", "media": imgs, "mediaFiles": dosyalar}


def kaydet(rows: list[dict]) -> int:
    if not rows:
        return 0
    try:
        mevcut = tt.load_jsonl(JSONL)
        by_id = {r.tweet_id: r for r in mevcut}
        yeni = 0
        for r in tt.scraped_to_records(rows):
            if r.tweet_id not in by_id:
                by_id[r.tweet_id] = r
                yeni += 1
        tt.save_jsonl(list(by_id.values()), JSONL)
        return yeni
    except Exception as e:
        _log(f"KAYIT HATASI: {type(e).__name__}: {e}")
        return 0


def kesikleri_tamamla(ids: list[str]) -> None:
    """Akista 'daha fazla goster' ile kesik gelen uzun tweetlerin tam metni.
    Az sayida oldugu icin status sayfasi kisitina takilmaz."""
    if not ids:
        return
    import subprocess
    _log(f"{len(ids)} kesik uzun tweet tam metin icin gap_ekle'ye veriliyor")
    try:
        subprocess.run([sys.executable, str(KOD / "gap_ekle.py"), *ids[:60]],
                       cwd=str(KOD), check=False, timeout=1800)
    except Exception as e:
        _log(f"gap_ekle calismadi: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="with_replies akisindan bosluk doldur")
    ap.add_argument("--alt-sinir", required=True, help="YYYY-MM-DD (UTC) — bu tarihe inince dur")
    ap.add_argument("--max-scroll", type=int, default=250)
    args = ap.parse_args()
    alt = datetime.fromisoformat(args.alt_sinir).replace(tzinfo=timezone.utc)

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        _log("Playwright yok")
        return 1

    try:
        arsiv = {r.tweet_id for r in tt.load_jsonl(JSONL)}
    except Exception as e:
        _log(f"arsiv okunamadi: {e}")
        return 1
    _log(f"basliyor | alt sinir {alt:%Y-%m-%d} | arsiv {len(arsiv)}")

    bekleyen: list[dict] = []
    kesikler: list[str] = []
    toplam_yeni = 0
    en_eski = None
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=15000)
            ctx = b.contexts[0]
            pg = next((q for q in ctx.pages if "x.com" in (q.url or "")), None) or ctx.new_page()
            for deneme in range(1, 4):
                try:
                    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
                    break
                except Exception as e:
                    _log(f"goto kesildi ({deneme}/3): {str(e)[:90]}")
                    pg.wait_for_timeout(3000)
            try:
                pg.wait_for_selector("article", timeout=25000)
            except Exception:
                _log("article gelmedi: " + pg.evaluate("()=>(document.body.innerText||'').slice(0,160)").replace("\n", " | "))
            gorulen: set[str] = set()
            bos = 0
            for i in range(1, args.max_scroll + 1):
                try:
                    veri = pg.evaluate(JS)
                except Exception as e:
                    _log(f"evaluate hatasi: {str(e)[:80]}")
                    veri = []
                yeni_gorulen = 0
                for d in veri:
                    if d["id"] in gorulen:
                        continue
                    gorulen.add(d["id"])
                    yeni_gorulen += 1
                    try:
                        t = datetime.fromisoformat((d.get("datetime") or "").replace("Z", "+00:00"))
                        # Sabitlenmis eski tweet en ustte cikar: ilk ekranda durma hesabina katma
                        if i > 2 and (en_eski is None or t < en_eski):
                            en_eski = t
                    except Exception:
                        pass
                    if d["id"] in arsiv or not (d.get("text") or "").strip():
                        continue
                    if d.get("kesik"):
                        kesikler.append(d["id"])
                    bekleyen.append(satir(d))
                    arsiv.add(d["id"])
                bos = bos + 1 if yeni_gorulen == 0 else 0
                if len(bekleyen) >= KAYIT_PARTI:
                    toplam_yeni += kaydet(bekleyen)
                    bekleyen = []
                if i % 10 == 0:
                    _log(f"scroll {i} | goruldu {len(gorulen)} | en eski "
                         f"{en_eski:%Y-%m-%d %H:%M} | yeni {toplam_yeni + len(bekleyen)}" if en_eski
                         else f"scroll {i} | goruldu {len(gorulen)}")
                if en_eski and en_eski < alt:
                    _log(f"alt sinira inildi ({en_eski:%Y-%m-%d %H:%M})")
                    break
                if bos >= BOS_SCROLL_LIMIT:
                    _log(f"{bos} scroll'dur yeni article yok — akis sonu/kisit, duruluyor")
                    break
                pg.mouse.wheel(0, 3500)
                pg.wait_for_timeout(2500)
    except Exception as e:
        _log(f"HATA: {type(e).__name__}: {str(e)[:150]}")
        toplam_yeni += kaydet(bekleyen)
        _log(f"kismi bitis | yeni {toplam_yeni}")
        return 1
    toplam_yeni += kaydet(bekleyen)
    _log(f"TAMAM | akistan yeni {toplam_yeni} | kesik {len(kesikler)}")
    kesikleri_tamamla(kesikler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
