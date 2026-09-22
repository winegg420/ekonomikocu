#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jev etiketlerinden temiz cagri listesi uretir.
Girdi : cekilen_tweetler.jsonl + jev_etiketler.jsonl (ana akis)
        07_ABONE_TWEETLER.jsonl + jev_abone_etiketler.jsonl (abone akisi)
Cikti : cagrilar_v2.jsonl (temiz cagrilar) + CAGRI_HAKEM.md (hakem bekleyenler + ornekleme)
Eski cagrilar.jsonl'ye DOKUNMAZ. Jev API cagrilmaz."""
import json, random, re, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
SEVIYE = re.compile(r"\d{1,3}[.,]\d{2,3}|\b\d{4,6}\b|\b\d{2,3}[.,]\d\b")

def oku(yol):
    k = []
    p = ROOT / yol
    if not p.is_file():
        return k
    with open(p, encoding="utf-8") as f:
        for s in f:
            s = s.strip()
            if not s:
                continue
            try:
                k.append(json.loads(s))
            except json.JSONDecodeError:
                continue
    return k

def _yil_mi(s):
    t = s.replace(".", "").replace(",", "")
    return t.isdigit() and len(t) == 4 and 1990 <= int(t) <= 2035

def seviyeler(metin):
    ham = list(dict.fromkeys(SEVIYE.findall(metin or "")))
    kesin = [s for s in ham if not _yil_mi(s)][:8]
    supheli = [s for s in ham if _yil_mi(s)][:4]
    return kesin, supheli

def _yil_eki(k):
    return f" | yil?={','.join(k['seviye_supheli'])}" if k.get("seviye_supheli") else ""

def main():
    ana_metin = {r.get("tweet_id"): (r.get("text") or "") for r in oku("cekilen_tweetler.jsonl")}
    abone_metin = {r.get("tweet_id"): (r.get("text") or "") for r in oku("07_ABONE_TWEETLER.jsonl")}
    cagrilar, hakem = [], []
    ana_etiket = oku("jev_etiketler.jsonl")
    abone_etiket = oku("jev_abone_etiketler.jsonl")

    for e in ana_etiket:
        metin = ana_metin.get(e.get("tweet_id"), "")
        sev, sev_supheli = seviyeler(metin)
        if e.get("zaman") != "beklenti" or not e.get("urun") or not sev:
            continue
        kayit = {
            "tweet_id": e.get("tweet_id"), "datetime": e.get("datetime"), "akis": "ana",
            "atif": e.get("atif"), "zaman_g": e.get("zaman_g"),
            "yon": e.get("yon"), "yon_kesin": e.get("yon_kesin", False),
            "urun": e.get("urun"), "seviyeler": sev,
            "seviye_supheli": sev_supheli, "metin": metin[:600],
        }
        if e.get("durum") == "otomatik":
            cagrilar.append(kayit)
        elif e.get("durum") == "kontrol":
            kayit["nedenler"] = e.get("nedenler", [])
            hakem.append(kayit)

    for e in abone_etiket:
        metin = abone_metin.get(e.get("tweet_id"), "")
        sev, sev_supheli = seviyeler(metin)
        if e.get("icerik") != "seviye_cagri" or not sev:
            continue
        kayit = {
            "tweet_id": e.get("tweet_id"), "datetime": e.get("datetime"), "akis": "abone",
            "yazar": e.get("yazar"), "yazar_g": e.get("yazar_g"),
            "urun": e.get("urun"), "seviyeler": sev,
            "seviye_supheli": sev_supheli, "metin": metin[:600],
        }
        if e.get("durum") == "otomatik" and e.get("yazar") == "koc":
            cagrilar.append(kayit)
        elif e.get("durum") == "kontrol":
            kayit["nedenler"] = e.get("nedenler", [])
            hakem.append(kayit)

    # Ana ve abone arsivi ortusuyor: ayni tweet iki akistan geldiyse yalnizca
    # "ana" kaydi kalir (atif/zaman/yon alanlari daha zengin).
    ana_idler = {c["tweet_id"] for c in cagrilar if c["akis"] == "ana"}
    tekil, gorulen = [], set()
    for c in cagrilar:
        if c["akis"] == "abone" and c["tweet_id"] in ana_idler:
            continue
        if c["tweet_id"] in gorulen:
            continue
        gorulen.add(c["tweet_id"])
        tekil.append(c)
    cagrilar = tekil

    # Iki arsivde ortak tweet'lerde ana "atif" ile abone "yazar" koc olup olmamada celisiyor mu?
    ana_e = {e.get("tweet_id"): e for e in ana_etiket}
    abone_e = {e.get("tweet_id"): e for e in abone_etiket}
    celiski = []
    for tid in set(ana_metin) & set(abone_metin):
        a, b = ana_e.get(tid), abone_e.get(tid)
        if not a or not b:
            continue
        if (a.get("atif") == "koc") != (b.get("yazar") == "koc"):
            celiski.append({"tweet_id": tid, "datetime": a.get("datetime") or b.get("datetime"),
                            "atif": a.get("atif"), "atif_g": a.get("atif_g"),
                            "yazar": b.get("yazar"), "yazar_g": b.get("yazar_g"),
                            "metin": ana_metin.get(tid) or abone_metin.get(tid) or ""})
    celiski.sort(key=lambda k: k.get("datetime") or "", reverse=True)

    cagrilar.sort(key=lambda k: k.get("datetime") or "", reverse=True)
    with open(ROOT / "cagrilar_v2.jsonl", "w", encoding="utf-8") as f:
        for k in cagrilar:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")

    hakem.sort(key=lambda k: k.get("datetime") or "", reverse=True)
    ana_h = [h for h in hakem if h["akis"] == "ana"]
    abone_h = [h for h in hakem if h["akis"] == "abone"]
    abone_oto = [c for c in cagrilar if c["akis"] == "abone"]
    random.seed(42)
    ornek = random.sample(abone_oto, min(40, len(abone_oto)))

    L = ["# CAGRI HAKEM DOSYASI (otomatik uretilir)", "",
         f"Temiz cagri: {len(cagrilar)} (ana {len(cagrilar)-len(abone_oto)}, abone {len(abone_oto)})",
         f"Hakem bekleyen: ana {len(ana_h)}, abone {len(abone_h)}", "",
         "## 1) ANA AKIS — hakem bekleyen", ""]
    for h in ana_h:
        L.append(f"- `{h['tweet_id']}` {str(h['datetime'])[:10]} | neden: {','.join(h.get('nedenler', []))} | "
                 f"atif={h['atif']} zaman_g={h['zaman_g']} yon={h['yon']} | urun={','.join(h['urun'])} | "
                 f"sev={','.join(h['seviyeler'])}{_yil_eki(h)} | {h['metin'][:160].replace(chr(10), ' ')}")
    L += ["", "## 2) ABONE AKIS — hakem bekleyen", ""]
    for h in abone_h:
        L.append(f"- `{h['tweet_id']}` {str(h['datetime'])[:10]} | yazar={h['yazar']}({h['yazar_g']}) | "
                 f"urun={','.join(h['urun'])} | sev={','.join(h['seviyeler'])}{_yil_eki(h)} | "
                 f"{h['metin'][:160].replace(chr(10), ' ')}")
    L += ["", "## 3) ABONE AKIS — dogrulama ornegi (40 kayit, yazar=koc kabul edilmis)", ""]
    for o in ornek:
        L.append(f"- `{o['tweet_id']}` {str(o['datetime'])[:10]} | yazar_g={o['yazar_g']} | "
                 f"urun={','.join(o['urun'])} | sev={','.join(o['seviyeler'])}{_yil_eki(o)} | "
                 f"{o['metin'][:160].replace(chr(10), ' ')}")
    L += ["", "## 4) CAPRAZ AKIS CELISKI (oncelikli hakem)", "",
          f"Iki arsivde ortak olup ana atif ile abone yazar 'koc' konusunda celisen: {len(celiski)}", ""]
    for c in celiski:
        L.append(f"- `{c['tweet_id']}` {str(c['datetime'])[:10]} | ana_atif={c['atif']}({c['atif_g']}) | "
                 f"abone_yazar={c['yazar']}({c['yazar_g']}) | {c['metin'][:160].replace(chr(10), ' ')}")
    (ROOT / "CAGRI_HAKEM.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"cagrilar_v2: {len(cagrilar)} (ana {len(cagrilar)-len(abone_oto)}, abone {len(abone_oto)})")
    print(f"hakem: ana {len(ana_h)}, abone {len(abone_h)} | ornek: {len(ornek)} | capraz celiski: {len(celiski)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
