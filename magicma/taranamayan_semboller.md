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
