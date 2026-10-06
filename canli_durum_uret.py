#!/usr/bin/env python3
"""CANLI_DURUM.json (tek kaynak, elle duzenlenir) -> CANLI_DURUM.md (otomatik uretilir, elle duzenlenmez).

Kullanim (py -3):
  python canli_durum_uret.py              # MD uret
  python canli_durum_uret.py --dogrula    # JSON/MD kontrolu (tweet_id arsivde var mi, fiyat yok mu, <=150 satir)

Uretim deterministiktir: ayni JSON -> bayt-bayt ayni MD (zaman damgasi JSON'dan gelir, 'simdi' kullanilmaz).
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent
JSON_YOL = KOK / "CANLI_DURUM.json"
MD_YOL = KOK / "CANLI_DURUM.md"
MAX_SATIR = 150
ETIKET = {"gecerli": "GEÇERLİ", "tetiklendi": "TETİKLENDİ", "bozuldu": "BOZULDU", "belirsiz": "BELİRSİZ"}


def yukle():
    try:
        return json.loads(JSON_YOL.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"HATA: {JSON_YOL.name} okunamadi/gecersiz: {e}")


def damgala(d):
    """last_updated = simdi (TSI, yerel saat dilimi), source_commit = git HEAD kisa SHA. Git yoksa 'bilinmiyor'."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=KOK, capture_output=True,
                             text=True, timeout=15, check=True).stdout.strip() or "bilinmiyor"
    except (OSError, subprocess.SubprocessError):
        sha = "bilinmiyor"
    d["source_commit"] = sha
    d["last_updated"] = datetime.now().astimezone().replace(microsecond=0).isoformat()
    try:
        JSON_YOL.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    except OSError as e:
        sys.exit(f"HATA: {JSON_YOL.name} yazilamadi: {e}")


def kimlik(tid):
    return f"[{tid}]" if tid else "[tweet_id yok]"


def uret(d):
    L = []
    a = L.append
    s = d.get("son_islenen_tweet", {})
    a("# CANLI DURUM (otomatik üretilir — elle düzenleme; kaynak: CANLI_DURUM.json)")
    a(f"- last_updated: {d.get('last_updated')}")
    a(f"- source_commit: {d.get('source_commit')}")
    a(f"- Son işlenen tweet: {s.get('son_tweet_zamani')} (tur {s.get('son_tur')})")
    a(f"- Kapsam: {d.get('kapsam_notu', '')}")
    a("- Okuma sırası: " + " → ".join(x.split(") ", 1)[-1] for x in d.get("okuma_sirasi", [])))
    a("")
    a("## KOÇ (yalnız @ekonomikocu'nun kendi sözü)")
    a("Durumlar: " + "; ".join(f"{ETIKET[k]} = {v}" for k, v in d.get("durum_sozlugu", {}).items()))
    a("")
    a("### Çağrılar (son 14 gün, yeniden eskiye)")
    for c in d.get("koc_cagrilari", []):
        g = "görsel okundu" if c.get("gorsel_dogrulandi") else ("görsel var, okunmadı" if "gorsel" in c.get("kaynak_turu", "") else "metin")
        nt = f" — {c['not']}" if c.get("not") else ""
        a(f"- {c['tarih']} {c['urun']}: {c['seviye']} → {ETIKET.get(c['durum'], c['durum'])} ({g}) {kimlik(c.get('tweet_id'))}{nt}")
    a("")
    a("### Muhtemel varlık (kesin değil)")
    for m in d.get("muhtemel_varlik", []):
        a(f"- {m['seviye']} → {m['muhtemel_varlik']}, kesinlik: {m['kesinlik']} {kimlik(m.get('tweet_id'))}")
        a(f"  - Gerekçe: {m.get('gerekce', '')}")
        a(f"  - {m.get('not', '')}")
    a("")
    o = d.get("koc_ogreti", {})
    a("### Öğreti sayıları")
    for x in o.get("ogreti_sayilari", []):
        a(f"- {x['sayi']} ({x['kesinlik']}): {x['kural']} {kimlik(x.get('tweet_id'))} — {x.get('not', '')}")
    a("")
    e = o.get("eski_tepe_kurali", {})
    a("### Eski tepe kuralı")
    a(f"- {e.get('ozet', '')} ({e.get('tarih')}) {kimlik(e.get('tweet_id'))}")
    for x in e.get("seviyeler", []):
        a(f"  - {x['urun']}: {x['seviye']} ({x['kesinlik']}){(' ' + kimlik(x['tweet_id'])) if x.get('tweet_id') else ''}")
    a(f"- {e.get('not', '')}")
    a(f"- Zaman tezi: {o.get('zaman_tezi', '')}")
    a("")
    a("### Takvim")
    for t in d.get("takvim", []):
        a(f"- {t['tarih']}: {t['olay']} {kimlik(t.get('tweet_id'))}")
    a("")
    k = d.get("KULLANICI_DURUSU", {})
    a("## KULLANICI DURUŞU (Ida — analist görüşü DEĞİL)")
    a(f"- {k.get('uyari', '')}")
    for m in k.get("maddeler", []):
        a(f"- {m}")
    a("")
    mm = d.get("magicma_notu", {})
    a("## MAGICMA")
    a(f"- {mm.get('ozet', '')}")
    a(f"- Backtest: {mm.get('backtest', '')}")
    a(f"- {mm.get('kullanim', '')}")
    a("")
    dk = d.get("dis_kaynaklar", {})
    a("## DIŞ KAYNAKLAR (Koç'a atfedilmez)")
    a(f"- {dk.get('uyari', '')}")
    a(f"- Dosya: {dk.get('dosya')} — kaynaklar: {', '.join(dk.get('kaynaklar', []))}")
    ab = dk.get("abone_imza_kontrolu", {})
    a(f"- Abone/imza kuralı: {ab.get('kural', '')}")
    for b in ab.get("bilinen_atiflar", []):
        a(f"  - {b['kisi']}: {b['icerik']} {kimlik(b.get('tweet_id'))} — {b.get('not', '')}")
    a(f"- Çin-ABD anlaşması: {dk.get('cin_abd_anlasmasi', '')}")
    return "\n".join(L) + "\n"


def yaz(metin):
    try:
        MD_YOL.write_text(metin, encoding="utf-8", newline="\n")
    except OSError as e:
        sys.exit(f"HATA: {MD_YOL.name} yazilamadi: {e}")


def tum_idler(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "tweet_id" and v:
                acc.add(str(v))
            else:
                tum_idler(v, acc)
    elif isinstance(o, list):
        for v in o:
            tum_idler(v, acc)
    return acc


def dogrula(d):
    hata = []
    try:
        md = MD_YOL.read_text(encoding="utf-8")
    except OSError as e:
        sys.exit(f"HATA: MD okunamadi: {e}")
    n = len(md.splitlines())
    if n > MAX_SATIR:
        hata.append(f"MD {n} satir (> {MAX_SATIR})")
    for alan in ("last_updated", "source_commit"):
        if f"- {alan}: {d.get(alan)}" not in md:
            hata.append(f"MD'de {alan} JSON ile ayni degil")
    if md != uret(d):
        hata.append("MD, JSON'dan uretilenden farkli (elle degismis veya uretilmemis)")
    # tweet_id: her cagrida var + arsivde var
    for c in d.get("koc_cagrilari", []):
        if not c.get("tweet_id"):
            hata.append(f"cagri tweet_id yok: {c.get('urun')} {c.get('seviye')}")
        if c.get("durum") not in ETIKET:
            hata.append(f"gecersiz durum: {c.get('tweet_id')}")
        if not isinstance(c.get("gorsel_dogrulandi"), bool):
            hata.append(f"gorsel_dogrulandi bool degil: {c.get('tweet_id')}")
    idler = tum_idler(d, set())
    bulunan, kayit_tip = set(), {}
    try:
        with open(KOK / "cekilen_tweetler.jsonl", encoding="utf-8") as f:
            for satir in f:
                m = re.search(r'"tweet_id": "(\d+)"', satir)
                if m and m.group(1) in idler:
                    bulunan.add(m.group(1))
                    try:
                        r = json.loads(satir)
                        kayit_tip[m.group(1)] = r
                    except json.JSONDecodeError:
                        pass
    except OSError as e:
        hata.append(f"cekilen_tweetler.jsonl okunamadi: {e}")
    for i in sorted(idler - bulunan):
        hata.append(f"tweet_id arsivde yok: {i}")
    for c in d.get("koc_cagrilari", []):
        r = kayit_tip.get(c.get("tweet_id"))
        if r and (r.get("kayit_tipi") == "abone" or r.get("abone_ozel")):
            hata.append(f"abone tweet'i Koç cagrisi olmus: {c['tweet_id']}")
        if r and r.get("datetime", "")[:10] != c.get("tarih"):
            hata.append(f"tarih uyusmuyor: {c['tweet_id']}")
    # gorsel bayragi gorsel_analiz.jsonl ile tutarli mi
    try:
        gor = set()
        with open(KOK / "gorsel_analiz.jsonl", encoding="utf-8") as f:
            for satir in f:
                m = re.search(r'"tweet_id": "(\d+)"', satir)
                if m:
                    gor.add(m.group(1))
        for c in d.get("koc_cagrilari", []):
            if bool(c.get("gorsel_dogrulandi")) != (c.get("tweet_id") in gor):
                hata.append(f"gorsel_dogrulandi gorsel_analiz.jsonl ile celisiyor: {c.get('tweet_id')}")
    except OSError as e:
        hata.append(f"gorsel_analiz.jsonl okunamadi: {e}")
    # fiyat yasak: guncel fiyat alani/ifadesi olmamali
    ham = json.dumps(d, ensure_ascii=False).lower()
    for yasak in ("guncel_fiyat", "güncel fiyat", "anlik_fiyat", "anlık fiyat", "\"fiyat\""):
        if yasak in ham:
            hata.append(f"fiyat ifadesi bulundu: {yasak}")
    # sizinti: kullanici durusu / dis kaynak anahtar kelimeleri Koc bolumunde olmamali
    koc = json.dumps({k: d.get(k) for k in ("koc_cagrilari", "koc_ogreti", "muhtemel_varlik", "takvim")}, ensure_ascii=False)
    for kelime in ("primexbt", "10.000$", "kademeli", "Sellcoin", "Yeşilada", "Şatıroğlu"):
        if kelime in koc:
            hata.append(f"Koç bölümüne sızıntı: {kelime}")
    if hata:
        print("DOGRULAMA BASARISIZ:")
        for h in hata:
            print(" -", h)
        return 1
    print(f"TAMAM: {n} satir, {len(idler)} tweet_id arsivde, last_updated/source_commit esit, fiyat yok, sizinti yok")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dogrula", action="store_true", help="uretmeden kontrol et")
    a = ap.parse_args()
    d = yukle()
    if a.dogrula:
        sys.exit(dogrula(d))
    damgala(d)
    metin = uret(d)
    yaz(metin)
    print(f"{MD_YOL.name} yazildi ({len(metin.splitlines())} satir)")
    sys.exit(dogrula(d))


if __name__ == "__main__":
    main()
