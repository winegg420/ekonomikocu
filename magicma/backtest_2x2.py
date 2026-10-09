#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MagicMA temas -> stop %2 / TP %2 raporu. backtest.py'ye DOKUNMAZ, onu import eder.

  py -3 magicma/backtest_2x2.py   # magicma/backtest_2x2_rapor.md uret (yalniz yerel onbellek backtest_veri/, indirme YOK)
Kurallar backtest.py ile AYNI: giris = karne giris_fiyati/zamani, yon karnedeki etiket
(fiyat cizgi ustunde=long, altinda=short), ayni mumda ikisi de vurursa STOP once.
"""
import datetime as dt
import os
import random
import sys
import time
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as B  # noqa: E402

STOP = TP = 0.02
MALIYET = 0.001            # gidis-donus %0,1
MIN_OLAY = 100
RASTGELE_TEKRAR = 2000
SEED = 20261009
GUN7 = 7 * 86400
PENCERELER = [("48 saat", 48 * 3600)]
ONCE_SAAT = (24, 48, 72)


def hazirla(olaylar, simdi, pencere_sn):
    """backtest.olaylari_hazirla ile ayni giris/eleme kurallari; pencere parametreli, temas oncesi 72s eklendi."""
    cache, hz, elenen = {}, [], Counter()
    for o in olaylar:
        if o["ts"] + pencere_sn > simdi - B.MUM_SN:
            elenen["pencere kesik"] += 1
            continue
        vekil = False
        if B.kaynak_tipi(o) == "kripto":
            tip, ad = "kripto", o["sembol"]
        else:
            ad, vekil = B.yahoo_kodu(o)
            tip = "yahoo"
            if not ad:
                elenen["sembol eslenemedi"] += 1
                continue
        if (tip, ad) not in cache:
            cache[(tip, ad)] = B.cache_oku(tip, ad)[0]
        arr = cache[(tip, ad)]
        if arr is None or len(arr) == 0:
            elenen["veri gelmedi"] += 1
            continue
        ts = arr[:, 0]
        i0 = int(np.searchsorted(ts, o["ts"], "right")) - 1
        if i0 < 0 or o["ts"] - ts[i0] >= B.MUM_SN:
            j = i0 + 1
            if j < len(ts) and ts[j] - o["ts"] <= 3600:
                i0 = j
            else:
                elenen["giris mumu yok"] += 1
                continue
        c0 = arr[i0, 4]
        k = o["giris"] / c0 if vekil else 1.0
        if not vekil and abs(c0 / o["giris"] - 1) > B.TOLERANS_FIYAT:
            elenen["giris fiyati mumla uyusmuyor"] += 1
            continue
        bit = int(np.searchsorted(ts, o["ts"] + pencere_sn, "left"))
        sl = arr[i0:bit]
        if len(sl) < 2:
            elenen["pencerede mum yok"] += 1
            continue
        # temas oncesi: yalniz GIRIS ANINDAN ONCEKI mumlar (gelecek sizintisi yok);
        # t-24/48/72s'te son kapanis, en fazla 5 gun eski
        once = {}
        for sa in ONCE_SAAT:
            hedef = o["ts"] - sa * 3600
            j = int(np.searchsorted(ts, hedef, "right")) - 1
            if j >= 0 and hedef - ts[j] <= 5 * 86400 and ts[j] < o["ts"]:
                once[sa] = o["giris"] / (arr[j, 4] * k) - 1
        hz.append({"o": o, "h": sl[:, 2] * k, "l": sl[:, 3] * k, "c": sl[:, 4] * k,
                   "e": o["giris"], "once": once or None})
    return hz, elenen


def sim_yon(d, yon):
    """-> (sonuc 'tp'|'stop'|'yok', ayni_mum, brut_getiri_kesir). Ayni mumda ikisi: STOP."""
    e = d["e"]
    if yon == "long":
        adv, fav, tout = 1 - d["l"] / e, d["h"] / e - 1, d["c"][-1] / e - 1
    else:
        adv, fav, tout = d["h"] / e - 1, 1 - d["l"] / e, 1 - d["c"][-1] / e
    si = np.nonzero(adv >= STOP)[0]
    ti = np.nonzero(fav >= TP)[0]
    si = si[0] if len(si) else None
    ti = ti[0] if len(ti) else None
    if si is None and ti is None:
        return "yok", False, tout
    if ti is None or (si is not None and si <= ti):
        return "stop", (ti is not None and si == ti), -STOP
    return "tp", False, TP


def ozet(sonuclar):
    n = len(sonuclar)
    if n == 0:
        return None
    c = Counter(s[0] for s in sonuclar)
    ret = np.array([s[2] for s in sonuclar])
    coz = c["tp"] + c["stop"]
    return {"n": n, "tp": c["tp"], "stop": c["stop"], "yok": c["yok"], "coz": coz,
            "ayni": sum(1 for s in sonuclar if s[1]),
            "vur": c["tp"] / coz if coz else float("nan"),
            "R": float(ret.mean() / STOP), "brut": float(ret.mean()) * 100,
            "net": float(ret.mean() - MALIYET) * 100,
            "Rcoz": (sum(s[2] for s in sonuclar if s[0] != "yok") / STOP / coz) if coz else float("nan")}


BASLIK = ("| grup | temas | sonuclanan | vurma (TP/sonuclanan) | stop % | sonuc yok % | ort. R | "
          "ort. brut % | ort. net % (-0,1) |\n|---|---|---|---|---|---|---|---|---|")


def satir(ad, z):
    if not z:
        return f"| {ad} | 0 | - | - | - | - | - | - | - |"
    notu = " ⚠" if z["coz"] < MIN_OLAY else ""
    return (f"| {ad} | {z['n']} | {z['coz']} ({z['coz'] / z['n']:.0%}) | {z['vur']:.1%}{notu} | "
            f"{z['stop'] / z['n']:.1%} | {z['yok'] / z['n']:.1%} | {z['R']:+.3f} | {z['brut']:+.3f} | {z['net']:+.3f} |")


def kat(o):
    k = o["kategori"]
    return "kripto" if k in ("kripto", "gunun_hareketlileri") else k


def kirilim(hz, sonuc, anahtar):
    g = defaultdict(list)
    for d, s in zip(hz, sonuc):
        g[anahtar(d["o"])].append(s)
    return [satir(k, ozet(v)) for k, v in sorted(g.items())]


def rastgele_taban(hz):
    """Ayni girisler, yon her olayda yazi-tura. -> (vurma listesi, net% listesi)"""
    rng = random.Random(SEED)
    L = [sim_yon(d, "long") for d in hz]
    S = [sim_yon(d, "short") for d in hz]
    vur, net = [], []
    for _ in range(RASTGELE_TEKRAR):
        z = ozet([(L[i] if rng.random() < 0.5 else S[i]) for i in range(len(hz))])
        vur.append(z["vur"])
        net.append(z["net"])
    return vur, net


def hareket(d):
    return max(d["once"].values(), key=abs)


def pencere_raporu(ad, sn, olaylar, simdi):
    hz, elenen = hazirla(olaylar, simdi, sn)
    sonuc = [sim_yon(d, d["o"]["yon"]) for d in hz]
    z = ozet(sonuc)
    out = [f"## Pencere: {ad}\n"]
    out.append(f"Karne temasi {len(olaylar)}; simulasyona giren **{z['n']}**. Elenenler: "
               + ", ".join(f"{k}={v}" for k, v in elenen.most_common()) + ".\n")
    out.append(f"- Sonuclanan (TP veya stop vurmus): **{z['coz']}** ({z['coz'] / z['n']:.1%}); "
               f"sonuclanmayan: **{z['yok']}** ({z['yok'] / z['n']:.1%}) — pencere sonu kapanisinda cikildi varsayildi.")
    out.append(f"- TP {z['tp']} ({z['tp'] / z['n']:.1%}) + stop {z['stop']} ({z['stop'] / z['n']:.1%}) + "
               f"sonuc yok {z['yok']} ({z['yok'] / z['n']:.1%}) = {(z['tp'] + z['stop'] + z['yok']) / z['n']:.1%}.")
    out.append(f"- Vurma orani (TP / sonuclanan): **{z['vur']:.1%}** (basabas %50). Ort. R (hepsi, sonuclanmayan kapanisla): "
               f"**{z['R']:+.3f}**; yalniz sonuclananlarda {z['Rcoz']:+.3f}.")
    out.append(f"- Beklenen deger: brut {z['brut']:+.3f}% / islem; maliyet sonrasi (-%0,1) **{z['net']:+.3f}%** / islem.")
    out.append(f"- Ayni mumda hem TP hem stop vuran: **{z['ayni']}** olay (hepsi STOP sayildi, muhafazakar); "
               f"sonuclananlarin {z['ayni'] / max(z['coz'], 1):.1%}'i.\n")
    v, nt = rastgele_taban(hz)
    p_v = float(np.mean([x >= z["vur"] for x in v]))
    p_n = float(np.mean([x >= z["net"] for x in nt]))
    out.append(f"**Rastgele yon tabani** ({RASTGELE_TEKRAR} tekrar, ayni girisler, yon yazi-tura): vurma "
               f"{np.mean(v):.1%} (SS {np.std(v):.1%}), ort. net {np.mean(nt):+.3f}%. MagicMA: vurma {z['vur']:.1%} / net {z['net']:+.3f}% "
               f"→ p(rastgele >= MagicMA): vurma={p_v:.3f}, net={p_n:.3f}.\n")
    out.append("### Yon / urun turu / cizgi turu\n")
    out.append(BASLIK)
    out += kirilim(hz, sonuc, lambda o: f"yon: {o['yon']}")
    out += kirilim(hz, sonuc, lambda o: f"urun: {kat(o)}")
    out += kirilim(hz, sonuc, lambda o: f"cizgi: {o['grup']}")
    out.append("\n(⚠ = sonuclanan < 100: orneklem yetersiz)\n")
    out.append("### Train / test\n")
    out.append(BASLIK)
    for nm_, f in (("train 28 Agu-18 Eyl", lambda t: t < B.EGITIM_BITIS), ("test 19 Eyl-bugun", lambda t: t >= B.EGITIM_BITIS)):
        idx = [i for i, d in enumerate(hz) if f(d["o"]["ts"])]
        zz = ozet([sonuc[i] for i in idx])
        out.append(satir(nm_, zz))
        if zz:
            vt, ntt = rastgele_taban([hz[i] for i in idx])
            out.append(f"| ↳ rastgele yon tabani | {zz['n']} | | {np.mean(vt):.1%} | | | | | {np.mean(ntt):+.3f} |")
    out.append("")
    out.append("### Temastan once 24-72 saatte sert hareket\n")
    out.append("**Veri yok** — yerel onbellek her temasin yalniz girisinden sonrasini kapsar (ust uste binen pencereler disinda); onceki 72 saat indirilmedi, bu turda kapsam disi.\n")
    return "\n".join(out), z


def main():
    simdi = time.time()
    olaylar = B.olaylari_yukle()
    parcalar, ozetler = [], []
    for ad, sn in PENCERELER:
        txt, z = pencere_raporu(ad, sn, olaylar, simdi)
        assert z["coz"] <= z["n"] <= len(olaylar)
        assert z["tp"] + z["stop"] + z["yok"] == z["n"]
        parcalar.append(txt)
        ozetler.append(f"- {ad}: n={z['n']}, vurma {z['vur']:.1%}, net {z['net']:+.3f}%/islem, sonuclanan {z['coz']}.")
    bas = ["# MagicMA Backtest — Stop %2 / TP %2\n",
           f"_Uretim: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} · kod: `magicma/backtest_2x2.py`"
           "(backtest.py'yi import eder, ona dokunmaz) · saf simulasyon, gercek hesap yok._\n",
           "**Varsayimlar (backtest.py ile ayni):** olay = karnedeki temas (giris fiyati/zamani, yon etiketi: fiyat cizgi ustunde=long, "
           "altinda=short); giris, giris anini iceren 5 dk mumdan baslar; stop/TP girisin %2'si; ayni mumda ikisi de degerse STOP once; "
           "sonuclanmayan olay pencere sonu kapanisinda kapatilir; maliyet %0,1 gidis-donus; 1R = %2. 7 gunluk pencere ve temas-oncesi sert hareket kirilimi bu turda KAPSAM DISI (veri yok). Metaller (XAU/XAG/XPT/XPD) "
           "vadeli kontrat getiri vekili ile simule edildi. Karne temaslari ayni sembolde ust uste binebilir "
           "(bagimsiz olay sayisi gorunenden dusuktur). Giris mumunun giristen ONCEKI wick'i simulasyona dahildir (stop/TP'yi hafif fazla tetikler; backtest_rapor.md bir sonraki mumdan baslamanin sonucu cok degistirdigini gosteriyor) — bu raporda duyarlilik testi yok.\n",
           "## Ozet\n", *ozetler, ""]
    yol = os.path.join(B.KOK, "magicma", "backtest_2x2_rapor.md")
    with open(yol, "w", encoding="utf-8") as f:
        f.write("\n".join(bas) + "\n" + "\n".join(parcalar))
    print("yazildi", yol)


if __name__ == "__main__":
    main()
