#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jev (TypeSafe) ile tweet etiketleme.
- Eski etiketlere (cekilen_tweetler.jsonl) DOKUNMAZ; sonuclar jev_etiketler.jsonl'e EKLENIR.
- Dusuk guvenli kayitlar durum=kontrol olur, JEV_KUYRUK.md'ye yazilir (Claude sohbetinde hakemlenir).
- Anahtar yoksa / API hatasinda tarama hattini BOZMAZ, 0 ile cikar."""
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
KAYNAK = ROOT / "cekilen_tweetler.jsonl"
CIKTI = ROOT / "jev_etiketler.jsonl"
KUYRUK = ROOT / "JEV_KUYRUK.md"
MODEL = "jev-1.13.0"
URL = "https://api.typesafe.ai/v1/systemone"
ESIK = {"atif": 0.90, "zaman": 0.70, "yon": 0.70, "urun": 0.80}

BAGLAM = ("Yazar: @ekonomikocu (Koç). Bağlam notu: Koç ürün adı yazmadan verdiği 22.000-30.000 arası "
          "seviyeleri genellikle NASDAQ için, 60.000-130.000 arası seviyeleri genellikle Bitcoin (BTC) için kullanır.")

SORULAR = {
    "atif": {"type": "choice", "instructions": "Bu tweetteki piyasa görüşü kime ait?", "criteria": {
        "koc": "Tweeti yazan hesabın (Koç) kendi görüşü, yorumu, analizi veya çağrısı",
        "aktarim": "Başka bir kişinin (analist, trader, politikacı, kurum) sözü, postu veya görüşü aktarılıyor ('demiş', 'diyor', tırnak içinde çeviri gibi)",
        "haber": "Yorum katmadan bir haber veya son dakika bilgisi aktarılıyor",
        "yok": "Tweet piyasa görüşü veya bilgisi içermiyor"}},
    "zaman": {"type": "choice", "instructions": "Tweet fiyat hakkında hangi zamana dair konuşuyor?", "criteria": {
        "beklenti": "Gelecekte fiyatın ne yapacağına dair beklenti, hedef, kritik seviye veya koşullu senaryo (olursa/olmazsa)",
        "simdiki": "Şu anda olan fiyat hareketini veya seviyeyi tasvir ediyor, ileriye dönük tahmin yok",
        "gecmis": "Geçmişte olmuş bir hareketi anlatıyor veya 'şöyle olsaydı şu olurdu' türünden karşı-olgusal senaryo kuruyor",
        "yok": "Fiyat hareketinden bahsetmiyor"}},
    "yon": {"type": "choice", "instructions": "Tweet ileriye dönük olarak fiyattan hangi yönü bekliyor?", "criteria": {
        "yukari": "Gelecekte yükseliş beklentisi",
        "asagi": "Gelecekte düşüş beklentisi",
        "kosullu": "Gelecek yön bir koşula bağlı (şu olursa yukarı, olmazsa aşağı)",
        "belirsiz": "İleriye dönük net bir yön beklentisi yok"}},
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
    urun_var = any(v >= 0.5 for v in olas.values())
    zaman_g = k.get("zaman_g") or 0.0
    aday = k.get("zaman") == "beklenti" or (zaman_g < ESIK["zaman"] and urun_var)
    if not aday:
        k["durum"], k["nedenler"] = "cagri_degil", []
        return k
    n = []
    if (k.get("atif_g") or 0.0) < ESIK["atif"]:
        n.append("atif")
    if zaman_g < ESIK["zaman"]:
        n.append("zaman")
    if k.get("zaman") == "beklenti" and (k.get("yon_g") or 0.0) < ESIK["yon"]:
        n.append("yon")
    if any(0.5 <= v < ESIK["urun"] for v in olas.values()):
        n.append("urun")
    k["durum"] = "kontrol" if n else "otomatik"
    k["nedenler"] = n
    return k


def degerlendir(r, yanit):
    c = yanit.get("answers", {})
    def sec(alan):
        s = c.get(alan, {})
        g = s.get("confidence")
        return s.get("choice"), (round(g, 2) if isinstance(g, (int, float)) else 0.0)
    atif, atif_g = sec("atif")
    zaman, zaman_g = sec("zaman")
    yon, yon_g = sec("yon")
    if zaman != "beklenti":
        yon, yon_g = None, None
    olas = {}
    for p in URUNLER:
        v = c.get(p, {}).get("noul")
        olas[p] = round(v, 2) if isinstance(v, (int, float)) else 0.0
    kayit = {
        "tweet_id": r.get("tweet_id"), "datetime": r.get("datetime"), "model": yanit.get("model", MODEL),
        "atif": atif, "atif_g": atif_g, "zaman": zaman, "zaman_g": zaman_g, "yon": yon, "yon_g": yon_g,
        "urun": [p for p, v in olas.items() if v >= 0.5], "urun_olasilik": olas,
        "etiket_tarihi": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return durum_hesapla(kayit)


def kuyruk_yaz(metinler):
    try:
        etiketler = jsonl_oku(CIKTI)
        oto = sum(1 for e in etiketler if e.get("durum") == "otomatik")
        degil = sum(1 for e in etiketler if e.get("durum") == "cagri_degil")
        kontrol = [e for e in etiketler if e.get("durum") == "kontrol"]
        kontrol.sort(key=lambda e: e.get("datetime") or "", reverse=True)
        satirlar = [
            "# JEV KONTROL KUYRUĞU (otomatik üretilir, elle düzenleme)",
            "",
            f"Model: {MODEL} | Toplam: {len(etiketler)} | Otomatik: {oto} | Çağrı değil: {degil} | Kontrol: {len(kontrol)}",
            f"Eşikler: {ESIK} | Son güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "Hakemleme Claude sohbetinde yapılır. Aşağıda en yeni 100 kontrol kaydı:",
            "",
        ]
        for e in kontrol[:100]:
            yon = f"{e['yon']}({e['yon_g']})" if e.get("yon") else "-"
            metin = (metinler.get(e["tweet_id"], "") or "").replace("\n", " ")[:120]
            satirlar.append(
                f"- `{e['tweet_id']}` {str(e.get('datetime'))[:10]} | neden: {','.join(e['nedenler'])} | "
                f"atif={e['atif']}({e['atif_g']}) zaman={e['zaman']}({e['zaman_g']}) yon={yon} | "
                f"urun={','.join(e['urun']) or 'yok'} | {metin}")
        KUYRUK.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    except Exception as ex:
        print(f"[jev] kuyruk yazilamadi: {ex}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=200, help="bu calismada en fazla kac tweet etiketlensin")
    ap.add_argument("--uyku", type=float, default=0.2)
    ap.add_argument("--yeniden", action="store_true", help="API cagirmadan kayitli skorlardan durumu yeniden hesapla")
    args = ap.parse_args()

    anahtar = anahtar_oku()
    if not anahtar:
        print("[jev] TYPESAFE_API_KEY yok, etiketleme atlandi.", flush=True)
        return 0
    try:
        kaynak = jsonl_oku(KAYNAK)
    except Exception as ex:
        print(f"[jev] cekilen_tweetler.jsonl okunamadi: {ex}", flush=True)
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
            print(f"[jev] yeniden degerlendirildi: {len(etiketler)} kayit", flush=True)
        except Exception as ex:
            print(f"[jev] yeniden degerlendirme hatasi: {ex}", flush=True)
        kuyruk_yaz(metinler)
        return 0
    etiketli = {e.get("tweet_id") for e in jsonl_oku(CIKTI)}
    bekleyen = [r for r in kaynak
                if r.get("tweet_id") and r.get("tweet_id") not in etiketli
                and (r.get("text") or "").strip() and (r.get("text") or "").strip() != "[erişilemedi]"]
    bekleyen.sort(key=lambda r: r.get("datetime") or "", reverse=True)
    bekleyen = bekleyen[: max(0, args.max)]
    if not bekleyen:
        print("[jev] etiketlenecek yeni tweet yok.", flush=True)
        kuyruk_yaz(metinler)
        return 0

    n = oto = kontrol = hata = ardisik_hata = tok_in = tok_out = 0
    with open(CIKTI, "a", encoding="utf-8") as cikti:
        for r in bekleyen:
            durum = f"{BAGLAM}\nTarih: {r.get('datetime')}\n"
            if r.get("is_quote") or r.get("quote_of"):
                durum += "Not: Bu tweet başka bir tweeti alıntılıyor.\n"
            durum += f"Tweet: {(r.get('text') or '')[:4000]}"
            try:
                yanit = jev(anahtar, durum)
            except AnahtarHatasi as ex:
                print(f"[jev] anahtar reddedildi ({ex}), durduruldu.", flush=True)
                break
            except Exception as ex:
                hata += 1
                ardisik_hata += 1
                print(f"[jev] {r.get('tweet_id')} hata: {type(ex).__name__}: {str(ex)[:150]}", flush=True)
                if ardisik_hata >= 5:
                    print("[jev] 5 ardisik hata, durduruldu.", flush=True)
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
            if n % 100 == 0:
                print(f"[jev] {n}/{len(bekleyen)} ...", flush=True)
            time.sleep(args.uyku)

    kuyruk_yaz(metinler)
    print(f"[jev] etiketlenen: {n} | otomatik: {oto} | kontrol: {kontrol} | hata: {hata} | "
          f"token: {tok_in} girdi, {tok_out} cikti", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
