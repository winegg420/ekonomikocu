# -*- coding: utf-8 -*-
"""MagicMA islem adayi raporu (CLAUDE.md kurali: SADECE mesafe <= %0,25).

magicma_ham.jsonl icinden verilen gunun kayitlarini okur (sembol basina en
yuksek ts), cizgiye yapisik seviyeleri yakinliga gore siralar ve
magicma/magicma_islem_adaylari_TARIH.md dosyasini uretir.

Kullanim:
    py -3 magicma_islem_adaylari.py            # bugun
    py -3 magicma_islem_adaylari.py 2026-07-22 # belirli gun
"""
import sys, os, json, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_KOD_DIR = os.path.dirname(os.path.abspath(__file__))
if _KOD_DIR not in sys.path:
    sys.path.insert(0, _KOD_DIR)

import magicma_yakinlik as m

ESIK_ADAY = 0.25  # CLAUDE.md: <= %0,25 yapisik sayilir

KISA_AD = {
    "Magicma Günlük Alt Çizgi": "G-Alt",
    "Magicma Günlük Üst Çizgi": "G-Üst",
    "Magicma Haftalık -1": "H-1",
    "Magicma Haftalık -2": "H-2",
}


def gunun_kayitlari(gun):
    """Sembol basina o gunun EN SON ham kaydi."""
    son = {}
    if not os.path.exists(m.HAM_JSONL):
        return []
    with open(m.HAM_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                k = json.loads(line)
            except Exception:
                continue
            ts = k.get("ts", "")
            if not ts.startswith(gun):
                continue
            onceki = son.get(k["sembol"])
            if onceki is None or ts >= onceki["ts"]:
                son[k["sembol"]] = k
    return list(son.values())


def ondalik(x):
    """Fiyat buyuklugune gore makul ondalik basamak."""
    a = abs(x)
    if a >= 100:
        return 2
    if a >= 1:
        return 4
    return 6


def main():
    gun = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    kayitlar = gunun_kayitlari(gun)
    if not kayitlar:
        print(f"{gun} icin ham kayit yok.")
        sys.exit(1)

    adaylar = []
    for k in kayitlar:
        for r in k["seviyeler"]:
            mes = r["mesafe_yuzde"]
            if abs(mes) <= ESIK_ADAY:
                adaylar.append({
                    "sembol": k["sembol"],
                    "fiyat": k["fiyat"],
                    "cizgi": KISA_AD.get(r["ad"], r["ad"]),
                    "deger": r["deger"],
                    "mesafe": mes,
                    # mesafe<0: fiyat cizginin ALTINDA -> DIRENC -> short adayi
                    "aday": "short adayı" if mes < 0 else "long adayı",
                })
    adaylar.sort(key=lambda a: abs(a["mesafe"]))

    os.makedirs(m.RAPOR_DIR, exist_ok=True)
    yol = os.path.join(m.RAPOR_DIR, f"magicma_islem_adaylari_{gun}.md")
    with open(yol, "w", encoding="utf-8") as f:
        f.write(f"# MagicMA İşlem Adayları — {gun}\n\n")
        f.write("- Zaman dilimi: **4 saat (4H)**\n")
        f.write(f"- Kriter: çizgiye yapışık ürünler (**mesafe ≤ %{ESIK_ADAY:.2f}".replace(".", ",")
                + "**), en yakın en üstte\n")
        f.write(f"- Taranan sembol: {len(kayitlar)} · İşlem adayı: {len(adaylar)}\n")
        f.write("- Fiyat çizginin ALTINDA = DİRENÇ = short adayı · ÜSTÜNDE = DESTEK = long adayı\n\n")
        f.write("| Sembol | Fiyat | Çizgi | Değer | Mesafe | Aday |\n")
        f.write("|---|---:|---|---:|---:|---|\n")
        for a in adaylar:
            o = ondalik(a["fiyat"])
            f.write(f"| {a['sembol']} | {m.tr_goster(a['fiyat'], o)} | {a['cizgi']} | "
                    f"{m.tr_goster(a['deger'], o)} | %{a['mesafe']:+.2f} | {a['aday']} |\n")
        if not adaylar:
            f.write("| — | — | — | — | — | yapışık ürün yok |\n")

    print(f"Rapor: {yol}")
    print(f"{len(kayitlar)} sembol tarandi, {len(adaylar)} islem adayi (<= %{ESIK_ADAY}).")
    for a in adaylar:
        o = ondalik(a["fiyat"])
        print(f"  {a['sembol']} | {m.tr_goster(a['fiyat'], o)} | {a['cizgi']} "
              f"{m.tr_goster(a['deger'], o)} | %{a['mesafe']:+.2f} | {a['aday']}")


if __name__ == "__main__":
    main()
