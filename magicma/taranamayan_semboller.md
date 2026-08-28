# MagicMA — taranamayan semboller (2026-08-26)

Tarama: 594 sembol denendi · **572 okundu** · 22 okunamadi · rapora giren 367.

Asagidaki 22 sembol TradingView'de deger vermedi ("okunamadi (timeout / deger 0)").
21'inin **hicbir taramada hic kaydi yok** (magicma_ham.jsonl bos) — yani gecici bir
ariza degil, kod TradingView'de karsiligi olmayan / gostergesi cizilmeyen bir kod.

## Kalici olarak veri vermeyenler

| Sembol | Kaynak liste | Islem |
|---|---|---|
| BINANCE:QQQBUSDT | kripto.txt | devre disi birakildi (yorum satiri) |
| BINANCE:NFPUSDT | kripto.txt | devre disi birakildi (yorum satiri) |
| MEXC:AIDOGEUSDT | kripto.txt | devre disi birakildi (yorum satiri) |
| NASDAQ:SPCX | abd_hisse.txt | listede birakildi — 2026-08-20 notu: yeni listelenme, MagicMA plotlari henuz bos |
| BINANCE:REUSDT · BYBIT:GRVTUSDT · BYBIT:KIIUSDT · BYBIT:SLXUSDT · MEXC:ALIGNUSDT · MEXC:ANSEMUSDT · MEXC:BASECATUSDT · MEXC:DGAIUSDT · MEXC:DRVUSDT · MEXC:HMMUSDT · MEXC:JIMOTHYUSDT · MEXC:JUGGERNAUTUSDT · MEXC:PODUSDT · MEXC:PONSUSDT · MEXC:QUIDUSDT · MEXC:STONKUSDT · MEXC:TENDIESUSDT | gunun_hareketlileri.txt | dokunulmadi — bu liste her taramada bubbles'tan yeniden uretiliyor, elle duzeltmenin kalicihgi yok |

## Gecici ariza

- **MEXC:CTRUSDT** — 2026-08-25T10:24'te okunmustu, bugun okunamadi. Kod dogru;
  ertesi taramada tekrar denenecek, listeden cikarilmadi.

## Not — tarama hizina etkisi (2026-08-26 dersi)

Okunamayan semboller sembol basina ~20 sn (3 deneme x timeout) harciyor ve
kosucu her yeniden basladiginda listenin **basindan** denendikleri icin, gozetmen
turu kisa tutuldugunda (5 dk) tur suresinin cogu bu olu sembollere gidiyordu:
5 dakikada sadece 3 sembol ilerlendi. Gozetmen tur suresi bu yuzden
`TUR_SN` (varsayilan 1500 sn) ile ayarlanabilir hale getirildi.

<!-- KARA-LISTE-OTOMATIK: BASLANGIC -->

## Kara liste (otomatik)

_Bu bolum `magicma_tara_dayanikli.py` tarafindan her taramada yeniden_
_yazilir — elle duzenleme burada KALICI DEGILDIR. Son guncelleme: 2026-08-28._

**Kara listede: 21 sembol (21'si bu hafta yeniden denenecek)**

- Denenmeden atlanan (esik 3 basarisiz): **21**
- Siradaki taramada yeniden denenecek (7 gun doldu): **0**
- Izlemede (henuz esigin altinda, hala her taramada deneniyor): **0**

| Sembol | Durum | Deneme | Ilk basarisiz | Son basarisiz |
|---|---|---:|---|---|
| BINANCE:NFPUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| BINANCE:QQQBUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| BINANCE:REUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| BYBIT:GRVTUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| BYBIT:KIIUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| BYBIT:SLXUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:AIDOGEUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:ALIGNUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:ANSEMUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:BASECATUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:DGAIUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:DRVUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:HMMUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:JIMOTHYUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:JUGGERNAUTUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:PODUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:PONSUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:QUIDUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:STONKUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:TENDIESUSDT | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |
| NASDAQ:SPCX | atlaniyor | 3 | 2026-08-26 | 2026-08-26 |

<!-- KARA-LISTE-OTOMATIK: BITIS -->
