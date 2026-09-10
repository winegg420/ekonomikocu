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
_yazilir — elle duzenleme burada KALICI DEGILDIR. Son guncelleme: 2026-09-10._

**Kara listede: 55 sembol (55'si bu hafta yeniden denenecek)**

- Denenmeden atlanan (esik 3 basarisiz): **43**
- Siradaki taramada yeniden denenecek (7 gun doldu): **12**
- Izlemede (henuz esigin altinda, hala her taramada deneniyor): **0**

| Sembol | Durum | Deneme | Ilk basarisiz | Son basarisiz |
|---|---|---:|---|---|
| BINANCE:CRCLBUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| BINANCE:GENIUSUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| BINANCE:GMEBUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| BINANCE:ICXUSDT | atlaniyor | 3 | 2026-09-04 | 2026-09-04 |
| BINANCE:MARSCOINUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| BINANCE:NFPUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| BINANCE:QQQBUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| BINANCE:REUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| BINANCE:SPYBUSDT | atlaniyor | 4 | 2026-09-01 | 2026-09-10 |
| BITGET:DEBITUSDT | atlaniyor | 3 | 2026-09-04 | 2026-09-04 |
| BYBIT:GRVTUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| BYBIT:KIIUSDT | atlaniyor | 4 | 2026-08-26 | 2026-09-10 |
| BYBIT:SLXUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| KUCOIN:LAPTOPUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:4STOCKUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:AIDOGEUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:ALIGNUSDT | atlaniyor | 4 | 2026-08-26 | 2026-09-10 |
| MEXC:ANTFUNUSDT | atlaniyor | 3 | 2026-09-04 | 2026-09-04 |
| MEXC:BALUSDT | atlaniyor | 3 | 2026-09-04 | 2026-09-04 |
| MEXC:BONERUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:CASHCATUSDT | atlaniyor | 3 | 2026-09-04 | 2026-09-04 |
| MEXC:CATEUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:CNPYUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:CPUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:DELTAUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:DGAIUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:DOSUSDT | atlaniyor | 3 | 2026-09-04 | 2026-09-04 |
| MEXC:DRBUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:DRVUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:FAIUSDT | atlaniyor | 3 | 2026-09-04 | 2026-09-04 |
| MEXC:FATCOINUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:FONEUSDT | atlaniyor | 3 | 2026-08-30 | 2026-09-04 |
| MEXC:FRONGUSDT | atlaniyor | 3 | 2026-08-30 | 2026-09-04 |
| MEXC:HMMUSDT | atlaniyor | 4 | 2026-08-26 | 2026-09-10 |
| MEXC:HOOKRUSDT | atlaniyor | 3 | 2026-08-30 | 2026-09-04 |
| MEXC:JIMOTHYUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:JUGGERNAUTUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:KISHUUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:KNOTSUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:MARSCOINUSDT | atlaniyor | 3 | 2026-08-30 | 2026-09-04 |
| MEXC:MICRODUCKUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:MOOUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:NESUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:ORBIOUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:PIPEDOGUSDT | atlaniyor | 3 | 2026-08-30 | 2026-09-04 |
| MEXC:PODUSDT | atlaniyor | 4 | 2026-08-26 | 2026-09-10 |
| MEXC:PONSUSDT | atlaniyor | 4 | 2026-08-26 | 2026-09-10 |
| MEXC:QUIDUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:ROBINUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:STONKBROKERUSDT | atlaniyor | 3 | 2026-08-30 | 2026-09-04 |
| MEXC:STONKEXUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| MEXC:STONKUSDT | yeniden denenecek | 3 | 2026-08-26 | 2026-08-26 |
| MEXC:TENDIESUSDT | atlaniyor | 4 | 2026-08-26 | 2026-09-10 |
| MEXC:UBIKUSDT | atlaniyor | 3 | 2026-09-10 | 2026-09-10 |
| NASDAQ:SPCX | atlaniyor | 4 | 2026-08-26 | 2026-09-04 |

<!-- KARA-LISTE-OTOMATIK: BITIS -->
