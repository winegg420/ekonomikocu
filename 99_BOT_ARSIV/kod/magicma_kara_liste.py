# -*- coding: utf-8 -*-
"""MagicMA — TradingView'de okunamayan sembollerin KALICI kara listesi.

SORUN: `gunun_hareketlileri.txt` her calistirmada cryptobubbles'tan yeniden
uretiliyor, yani "yorum satirina al" seklindeki elle duzeltmeler kaliciligi
yok. Uretici script yalnizca borsanin REST API'sinde USDT paritesinin VAR
oldugunu dogruluyor; TradingView'de MagicMA gostergesinin gercekten cizilip
cizilmedigini dogrulamiyor. Sonuc: her taramada ayni ~17 "olu" sembole sembol
basina ~20 sn (3 deneme x timeout) harcaniyordu.

COZUM: Kendi kendini guncelleyen kara liste (`magicma/okunamayan_kara_liste.json`).

    {
      "BYBIT:GRVTUSDT": {"ilk_basarisiz": "2026-08-24",
                         "son_basarisiz": "2026-08-28",
                         "deneme_sayisi": 5}
    }

KURALLAR
  1. Sembol okunamazsa   -> kara listeye eklenir / `son_basarisiz` yenilenir,
                            `deneme_sayisi` artar.
  2. Sembol OKUNURSA     -> kara listeden TAMAMEN CIKARILIR. Gecici arizalar
                            (MEXC:CTRUSDT ornegi) kalici engellenmez.
  3. `deneme_sayisi` >= KARA_LISTE_ESIK -> sonraki taramalarda TradingView'e
                            hic gidilmez, dogrudan "okunamayanlar"a yazilir.
  4. Atlanan sembol, `son_basarisiz`'dan YENIDEN_DENE_GUN gun sonra bir kez
                            daha denenir (yeni coin'ler zamanla MagicMA verisi
                            kazanabilir). O deneme de basarisizsa `son_basarisiz`
                            yenilenir ve sayac sifirdan baslar.

SAYIM BIRIMI: `deneme_sayisi` TARAMA KOSUMU basina en fazla 1 artar (her kosumda
sembol zaten kendi icinde MAX_DENEME kez denenmis olur). Yani esik 3, "art arda
3 ayri tarama kosumunda basarisiz" demektir — tek seferlik ag arizasi sembolu
kara listeye dusurmez.
"""
from __future__ import annotations

import datetime
import json
import os

_KOD_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(os.path.dirname(_KOD_DIR))   # 99_BOT_ARSIV/kod -> repo koku
KARA_LISTE_YOL = os.path.join(_REPO_DIR, "magicma", "okunamayan_kara_liste.json")

# --- Ayarlar (degistirmek icin tek yer) -----------------------------------
KARA_LISTE_ESIK = 3      # kac basarisiz taramadan sonra sembol denenmeden atlanir
YENIDEN_DENE_GUN = 7     # atlanan sembol kac gunde bir yeniden denenir
# --------------------------------------------------------------------------


def _bugun() -> str:
    return datetime.date.today().isoformat()


def _tarih(metin):
    """'2026-08-24' -> date. Cozulemezse None."""
    try:
        return datetime.date.fromisoformat(str(metin)[:10])
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Dosya
# --------------------------------------------------------------------------

def yukle(yol: str = KARA_LISTE_YOL) -> dict:
    """Kara listeyi okur. Dosya yoksa/bozuksa BOS sozluk doner (tarama durmaz)."""
    if not os.path.exists(yol):
        return {}
    try:
        with open(yol, encoding="utf-8") as f:
            veri = json.load(f)
        if not isinstance(veri, dict):
            return {}
        # Bicimi bozuk satirlari sessizce at
        return {s: k for s, k in veri.items() if isinstance(k, dict)}
    except (OSError, ValueError):
        return {}


def kaydet(kara_liste: dict, yol: str = KARA_LISTE_YOL) -> None:
    """Atomik yazim (gecici dosya + replace) — tarama cokerse dosya bozulmasin."""
    gecici = yol + ".tmp"
    try:
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(kara_liste.items())), f,
                      ensure_ascii=False, indent=1)
        os.replace(gecici, yol)
    except OSError as e:
        print(f"   [KARA LISTE] yazilamadi: {type(e).__name__}: {e}", flush=True)


# --------------------------------------------------------------------------
# Guncelleme
# --------------------------------------------------------------------------

def basarisiz(kara_liste: dict, sembol: str, bugun: str | None = None) -> dict:
    """Sembolu kara listeye ekler / gunceller. Guncellenen kaydi doner.

    Ayni gun icinde birden fazla kosum olursa `deneme_sayisi` yine artar —
    her kosum ayri bir 'tarama' sayilir (bkz. modul basligi).
    """
    bugun = bugun or _bugun()
    kayit = kara_liste.get(sembol)
    if not kayit:
        kayit = {"ilk_basarisiz": bugun, "son_basarisiz": bugun, "deneme_sayisi": 1}
        kara_liste[sembol] = kayit
        return kayit
    kayit["son_basarisiz"] = bugun
    kayit["deneme_sayisi"] = int(kayit.get("deneme_sayisi", 0)) + 1
    kayit.setdefault("ilk_basarisiz", bugun)
    return kayit


def basarili(kara_liste: dict, sembol: str) -> bool:
    """Sembol okunduysa kara listeden cikarir. Listede miydi -> True/False."""
    return kara_liste.pop(sembol, None) is not None


# --------------------------------------------------------------------------
# Karar
# --------------------------------------------------------------------------

def atlanmali_mi(kara_liste: dict, sembol: str, bugun: str | None = None):
    """Doner: (atlanmali_mi, sebep_metni)

    Atlanma sarti: kayit var VE deneme_sayisi >= KARA_LISTE_ESIK VE son
    basarisizliktan bu yana YENIDEN_DENE_GUN gun GECMEMIS.
    """
    kayit = kara_liste.get(sembol)
    if not kayit:
        return False, ""
    adet = int(kayit.get("deneme_sayisi", 0))
    if adet < KARA_LISTE_ESIK:
        return False, ""

    son = _tarih(kayit.get("son_basarisiz"))
    if son is None:
        return True, f"kara listede ({adet} basarisiz)"

    bu_gun = _tarih(bugun) or datetime.date.today()
    gecen = (bu_gun - son).days
    if gecen >= YENIDEN_DENE_GUN:
        return False, f"kara listede ama {gecen} gun gecmis — yeniden deneniyor"
    return True, f"kara listede ({adet} basarisiz, son {kayit['son_basarisiz']}, " \
                 f"{YENIDEN_DENE_GUN - gecen} gun sonra yeniden denenecek)"


def yeniden_denenecek_mi(kara_liste: dict, sembol: str, bugun: str | None = None) -> bool:
    """Esigi asmis ama yeniden deneme penceresi acilmis mi (bugun denenecek mi)?"""
    kayit = kara_liste.get(sembol)
    if not kayit or int(kayit.get("deneme_sayisi", 0)) < KARA_LISTE_ESIK:
        return False
    atlanir, _ = atlanmali_mi(kara_liste, sembol, bugun)
    return not atlanir


# --------------------------------------------------------------------------
# Ozet / rapor
# --------------------------------------------------------------------------

def ozet(kara_liste: dict, bugun: str | None = None) -> dict:
    """Rapor satiri icin sayilar.

    toplam            : kara listedeki tum semboller (esigi asmayanlar dahil)
    aktif             : su an denenmeden atlananlar
    hemen_denenecek   : yeniden deneme penceresi ACIK — siradaki taramada denenir
    bu_hafta_denenecek: onumuzdeki 7 gun icinde yeniden denenecekler
                        (penceresi bugun acik olanlar dahil)
    izleniyor         : henuz esige ulasmamis — zaten her taramada deneniyor
    """
    bu_gun = _tarih(bugun) or datetime.date.today()
    aktif, hemen, bu_hafta, izleniyor = [], [], [], []

    for sembol, kayit in kara_liste.items():
        if int(kayit.get("deneme_sayisi", 0)) < KARA_LISTE_ESIK:
            izleniyor.append(sembol)
            continue
        son = _tarih(kayit.get("son_basarisiz"))
        # Tarih okunamiyorsa guvenli taraf: siradaki taramada dene
        kalan = 0 if son is None else YENIDEN_DENE_GUN - (bu_gun - son).days
        if kalan <= 0:
            hemen.append(sembol)
        else:
            aktif.append(sembol)
        if kalan <= 7:
            bu_hafta.append(sembol)

    return {
        "toplam": len(kara_liste),
        "aktif": sorted(aktif),
        "hemen_denenecek": sorted(hemen),
        "bu_hafta_denenecek": sorted(bu_hafta),
        "izleniyor": sorted(izleniyor),
    }


def ozet_satiri(kara_liste: dict, bugun: str | None = None) -> str:
    o = ozet(kara_liste, bugun)
    return (f"Kara listede: {o['toplam']} sembol "
            f"({len(o['bu_hafta_denenecek'])}'si bu hafta yeniden denenecek)")


def tohumla(kara_liste: dict, bugun: str | None = None):
    """Gecmis TARAMA KANITINDAN kara listeyi doldurur (bir kerelik / gerektikce).

    Kanit kurali — bir sembol ancak SU IKISI birden dogruysa tohumlanir:
      1. En son magicma raporunun "## Okunamayanlar" bolumunde geciyor
         (yani gercekten DENENMIS ve okunamamis), VE
      2. magicma_ham.jsonl'de HIC kaydi yok (yani gecici ariza degil, hicbir
         taramada okunamamis).
    Boylece "bugun eklenmis, henuz hic denenmemis" yeni semboller yanlislikla
    kara listeye girmez; MEXC:CTRUSDT gibi bir kez okunmus olanlar da girmez.

    Zaten kara listede olan sembole DOKUNULMAZ (sayaci geri almayalim).
    Doner: (eklenenler, atlananlar_sebep)
    """
    import glob
    import re

    _rapor_dir = os.path.join(_REPO_DIR, "magicma")
    raporlar = sorted(glob.glob(os.path.join(_rapor_dir, "magicma_rapor_*.md")))
    if not raporlar:
        return [], "magicma_rapor_*.md bulunamadi"

    metin = ""
    try:
        with open(raporlar[-1], encoding="utf-8") as f:
            metin = f.read()
    except OSError as e:
        return [], f"{os.path.basename(raporlar[-1])} okunamadi: {e}"

    m = re.search(r"##\s*Okunamayanlar\s*\n+(.+?)(?:\n##|\Z)", metin, re.S)
    if not m:
        return [], f"{os.path.basename(raporlar[-1])} icinde Okunamayanlar bolumu yok"
    okunamayanlar = [p.strip() for p in m.group(1).replace("\n", " ").split(",") if p.strip()]

    ham = os.path.join(_KOD_DIR, "magicma_ham.jsonl")
    hic_okunmus = set()
    if os.path.exists(ham):
        with open(ham, encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                try:
                    k = json.loads(satir)
                except ValueError:
                    continue
                if k.get("kaynak"):
                    hic_okunmus.add(k["kaynak"])

    rapor_tarihi = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(raporlar[-1]))
    tarih = rapor_tarihi.group(1) if rapor_tarihi else (bugun or _bugun())

    eklenen = []
    for sembol in okunamayanlar:
        if sembol in kara_liste or sembol in hic_okunmus:
            continue
        kara_liste[sembol] = {"ilk_basarisiz": tarih, "son_basarisiz": tarih,
                              "deneme_sayisi": KARA_LISTE_ESIK}
        eklenen.append(sembol)
    return eklenen, os.path.basename(raporlar[-1])


if __name__ == "__main__":
    import sys as _sys

    kl = yukle()
    if "--tohumla" in _sys.argv:
        eklenen, kaynak = tohumla(kl)
        if eklenen:
            kaydet(kl)
            print(f"{kaynak} kanitiyla {len(eklenen)} sembol kara listeye tohumlandi:")
            for s in eklenen:
                print(f"  + {s}")
        else:
            print(f"Tohumlanacak yeni sembol yok ({kaynak}).")
        print()

    o = ozet(kl)
    print(f"Dosya: {KARA_LISTE_YOL}")
    print(f"Esik: {KARA_LISTE_ESIK} basarisiz · yeniden deneme: {YENIDEN_DENE_GUN} gun")
    print(ozet_satiri(kl))
    print(f"  denenmeden atlanan : {len(o['aktif'])}")
    print(f"  bu hafta denenecek : {len(o['bu_hafta_denenecek'])}")
    print(f"  izlemede (<esik)   : {len(o['izleniyor'])}")
    for sembol, kayit in sorted(kl.items()):
        atlanir, sebep = atlanmali_mi(kl, sembol)
        print(f"  {'ATLA' if atlanir else 'DENE'}  {sembol:28s} "
              f"{kayit.get('deneme_sayisi')}x  ilk={kayit.get('ilk_basarisiz')} "
              f"son={kayit.get('son_basarisiz')}  {sebep}")
