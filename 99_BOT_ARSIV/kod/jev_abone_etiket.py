#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jev (TypeSafe) ile abone metinlerinde imza/atif taramasi.
- 07_ABONE_TWEETLER.jsonl'deki metnin Koc'a mi aboneye mi ait oldugunu etiketler (Kural 3).
- Kaynaga DOKUNMAZ; sonuclar jev_abone_etiketler.jsonl'e EKLENIR.
- Seviye/cagri iceren ama yazari belirsiz kayitlar durum=kontrol olur, JEV_ABONE_KUYRUK.md'ye yazilir.
- Tarama hattina bagli DEGIL; elle calistirilir. Anahtar yoksa / API hatasinda 0 ile cikar."""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KOD = Path(__file__).resolve().parent
ROOT = KOD.parent.parent
KAYNAK = ROOT / "07_ABONE_TWEETLER.jsonl"
CIKTI = ROOT / "jev_abone_etiketler.jsonl"
KUYRUK = ROOT / "JEV_ABONE_KUYRUK.md"
MODEL = "jev-1.13.0"
URL = "https://api.typesafe.ai/v1/systemone"
ESIK = {"yazar": 0.85, "urun": 0.80}

BAGLAM = ("Bağlam: Bu metin @ekonomikocu'nun abonelere özel akışından. Bu akışta hem Koç "
          "(analist) hem de aboneleri yazar.")

SORULAR = {
    "yazar": {"type": "choice", "instructions": "Bu metni kim yazmış?", "criteria": {
        "koc": "Analistin (Koç) kendi yazısı: seviye/çağrı veriyor, soru cevaplıyor, abonelere hitap ediyor, öğretiyor",
        "abone": "Bir abonenin yazısı: Koç'a soru soruyor, ona hitap ediyor ('Koç', 'hocam'), teşekkür ediyor, görüş soruyor",
        "belirsiz": "Kimin yazdığı metinden anlaşılmıyor"}},
    "icerik": {"type": "choice", "instructions": "Metnin içeriği nedir?", "criteria": {
        "seviye_cagri": "Belirli bir fiyat seviyesi, hedef veya işlem çağrısı içeriyor",
        "soru": "Soru soruyor",
        "yorum": "Piyasa yorumu ama net seviye yok",
        "sohbet": "Teşekkür, selamlaşma, piyasa dışı sohbet"}},
    "btc": {"type": "noul", "instructions": "Tweet açıkça Bitcoin (BTC) hakkında konuşuyor"},
    "eth": {"type": "noul", "instructions": "Tweet açıkça Ethereum (ETH) hakkında konuşuyor"},
    "altin": {"type": "noul", "instructions": "Tweet açıkça altın (ons altın, XAUUSD, gram altın) hakkında konuşuyor"},
    "gumus": {"type": "noul", "instructions": "Tweet açıkça gümüş (XAGUSD) hakkında konuşuyor"},
    "petrol": {"type": "noul", "instructions": "Tweet açıkça petrol (Brent, WTI, USOIL) hakkında konuşuyor"},
    "nasdaq_abd": {"type": "noul", "instructions": "Tweet ABD hisse endeksleri (NASDAQ, S&P 500, Dow Jones) hakkında konuşuyor"},
    "bist": {"type": "noul", "instructions": "Tweet Borsa İstanbul (BIST) hakkında konuşuyor"},
    "dxy": {"type": "noul", "instructions": "Tweet dolar endeksi (DXY) veya genel dolar gücü hakkında konuşuyor"},
    "diger": {"type": "noul", "instructions": "Tweet yukarıdakiler dışında bir enstrüman hakkında konuşuyor (Çin A50, DAX, Nikkei, parite, altcoin vb.)"},
}
URUNLER = ["btc", "eth", "altin", "gumus", "petrol", "nasdaq_abd", "bist", "dxy", "diger"]


class AnahtarHatasi(Exception):
    pass


def anahtar_oku():
    k = os.environ.get("TYPESAFE_API_KEY")
    if k:
        return k
    try:
        with open(ROOT / ".env", encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()
                if satir.startswith("TYPESAFE_API_KEY="):
                    return satir.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None


def jev(anahtar, durum):
    govde = json.dumps({"state": durum, "model": MODEL, "questions": SORULAR},
                       ensure_ascii=False).encode("utf-8")
    for deneme in range(2):
        istek = urllib.request.Request(URL, data=govde, method="POST",
            headers={"Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(istek, timeout=30) as yanit:
                return json.loads(yanit.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise AnahtarHatasi(f"HTTP {e.code}")
            if e.code == 429 and deneme == 0:
                time.sleep(5)
                continue
            raise


def jsonl_oku(yol):
    kayitlar = []
    if not yol.is_file():
        return kayitlar
    with open(yol, encoding="utf-8") as f:
        for s in f:
            s = s.strip()
            if not s:
                continue
            try:
                kayitlar.append(json.loads(s))
            except json.JSONDecodeError:
                continue
    return kayitlar


def durum_hesapla(k):
    olas = k.get("urun_olasilik") or {}
    k["urun"] = [p for p, v in olas.items() if v >= ESIK["urun"]]
    if k.get("icerik") != "seviye_cagri":
        k["durum"], k["nedenler"] = "onemsiz", []
    elif (k.get("yazar_g") or 0.0) < ESIK["yazar"]:
        k["durum"], k["nedenler"] = "kontrol", ["yazar"]
    else:
        k["durum"], k["nedenler"] = "otomatik", []
    return k


def degerlendir(r, yanit):
    c = yanit.get("answers", {})
    def sec(alan):
        s = c.get(alan, {})
        g = s.get("confidence")
        return s.get("choice"), (round(g, 2) if isinstance(g, (int, float)) else 0.0)
    yazar, yazar_g = sec("yazar")
    icerik, icerik_g = sec("icerik")
    olas = {}
    for p in URUNLER:
        v = c.get(p, {}).get("noul")
        olas[p] = round(v, 2) if isinstance(v, (int, float)) else 0.0
    kayit = {
        "tweet_id": r.get("tweet_id"), "datetime": r.get("datetime"), "model": yanit.get("model", MODEL),
        "yazar": yazar, "yazar_g": yazar_g, "icerik": icerik, "icerik_g": icerik_g,
        "urun": [], "urun_olasilik": olas,
        "etiket_tarihi": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return durum_hesapla(kayit)


def kuyruk_yaz(metinler):
    try:
        etiketler = jsonl_oku(CIKTI)
        oto = sum(1 for e in etiketler if e.get("durum") == "otomatik")
        onemsiz = sum(1 for e in etiketler if e.get("durum") == "onemsiz")
        kontrol = [e for e in etiketler if e.get("durum") == "kontrol"]
        kontrol.sort(key=lambda e: e.get("datetime") or "", reverse=True)
        satirlar = [
            "# JEV ABONE KONTROL KUYRUĞU (otomatik üretilir)",
            "",
            f"Model: {MODEL} | Toplam: {len(etiketler)} | Otomatik: {oto} | Önemsiz: {onemsiz} | Kontrol: {len(kontrol)}",
            f"Eşikler: {ESIK} | Son güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "Seviye/çağrı içeren ama yazarı (Koç/abone) kesin olmayan kayıtlar. Hakemleme Claude sohbetinde yapılır.",
            "Aşağıda en yeni 100 kontrol kaydı:",
            "",
        ]
        for e in kontrol[:100]:
            metin = (metinler.get(e["tweet_id"], "") or "").replace("\n", " ")[:120]
            satirlar.append(
                f"- `{e['tweet_id']}` {str(e.get('datetime'))[:10]} | neden: {','.join(e['nedenler'])} | "
                f"yazar={e['yazar']}({e['yazar_g']}) icerik={e['icerik']}({e['icerik_g']}) | "
                f"urun={','.join(e['urun']) or 'yok'} | {metin}")
        KUYRUK.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    except Exception as ex:
        print(f"[jev-abone] kuyruk yazilamadi: {ex}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=200, help="bu calismada en fazla kac metin etiketlensin")
    ap.add_argument("--uyku", type=float, default=0.2)
    ap.add_argument("--yeniden", action="store_true", help="API cagirmadan kayitli skorlardan durumu yeniden hesapla")
    args = ap.parse_args()

    anahtar = anahtar_oku()
    if not anahtar:
        print("[jev-abone] TYPESAFE_API_KEY yok, etiketleme atlandi.", flush=True)
        return 0
    try:
        kaynak = jsonl_oku(KAYNAK)
    except Exception as ex:
        print(f"[jev-abone] 07_ABONE_TWEETLER.jsonl okunamadi: {ex}", flush=True)
        return 0
    metinler = {r.get("tweet_id"): r.get("text", "") for r in kaynak}
    if args.yeniden:
        try:
            etiketler = [durum_hesapla(e) for e in jsonl_oku(CIKTI)]
            gecici = CIKTI.with_suffix(".jsonl.tmp")
            with open(gecici, "w", encoding="utf-8") as f:
                for e in etiketler:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
            gecici.replace(CIKTI)
            print(f"[jev-abone] yeniden degerlendirildi: {len(etiketler)} kayit", flush=True)
        except Exception as ex:
            print(f"[jev-abone] yeniden degerlendirme hatasi: {ex}", flush=True)
        kuyruk_yaz(metinler)
        return 0
    etiketli = {e.get("tweet_id") for e in jsonl_oku(CIKTI)}
    bekleyen = [r for r in kaynak
                if r.get("tweet_id") and r.get("tweet_id") not in etiketli
                and (r.get("text") or "").strip() and (r.get("text") or "").strip() != "[erişilemedi]"]
    bekleyen.sort(key=lambda r: r.get("datetime") or "", reverse=True)
    bekleyen = bekleyen[: max(0, args.max)]
    if not bekleyen:
        print("[jev-abone] etiketlenecek yeni metin yok.", flush=True)
        kuyruk_yaz(metinler)
        return 0

    n = oto = kontrol = onemsiz = hata = ardisik_hata = tok_in = tok_out = 0
    with open(CIKTI, "a", encoding="utf-8") as cikti:
        for r in bekleyen:
            durum = f"{BAGLAM}\nTarih: {r.get('datetime')}\nMetin: {(r.get('text') or '')[:4000]}"
            try:
                yanit = jev(anahtar, durum)
            except AnahtarHatasi as ex:
                print(f"[jev-abone] anahtar reddedildi ({ex}), durduruldu.", flush=True)
                break
            except Exception as ex:
                hata += 1
                ardisik_hata += 1
                print(f"[jev-abone] {r.get('tweet_id')} hata: {type(ex).__name__}: {str(ex)[:150]}", flush=True)
                if ardisik_hata >= 5:
                    print("[jev-abone] 5 ardisik hata, durduruldu.", flush=True)
                    break
                continue
            ardisik_hata = 0
            u = yanit.get("usage", {})
            tok_in += u.get("input_tokens", 0)
            tok_out += u.get("output_tokens", 0)
            kayit = degerlendir(r, yanit)
            cikti.write(json.dumps(kayit, ensure_ascii=False) + "\n")
            cikti.flush()
            n += 1
            if kayit["durum"] == "otomatik":
                oto += 1
            elif kayit["durum"] == "kontrol":
                kontrol += 1
            else:
                onemsiz += 1
            if n % 100 == 0:
                print(f"[jev-abone] {n}/{len(bekleyen)} ...", flush=True)
            time.sleep(args.uyku)

    kuyruk_yaz(metinler)
    print(f"[jev-abone] etiketlenen: {n} | otomatik: {oto} | onemsiz: {onemsiz} | kontrol: {kontrol} | "
          f"hata: {hata} | token: {tok_in} girdi, {tok_out} cikti", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
