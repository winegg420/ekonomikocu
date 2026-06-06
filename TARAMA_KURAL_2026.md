# 2026 TARAMA KURALI (kalici)

## Hedef — %100

**2026 yilinda atilmis olan her sey** kayit altinda olmali:

1. **Ana tweetler** (public + abone metinli)
2. **Bos kilitli abone tweet kalmamali**
3. **Alintilanan gecmis tweetler** (Koç'un 2026 tweetlerinde referans verdigi)
4. **#FLOOD thread parcalari** (kok + tum devam tweetleri)
5. **Flood icindeki alintilar** ve onlarin metinleri

**Genel tamamlanma %100 olmadan tarama bitmis sayilmaz.**

## Yeni tweet — hemen kayit

Koç yeni tweet attiginda veya gun sonu:

```
99_BOT_ARSIV\calistir\CHROME_X.bat   (Chrome acik, abone oturumu)
99_BOT_ARSIV\calistir\TARA_2026_GUNCEL.bat
```

Bu script: ustten kesif → bu ay aramasi → abone → flood → alinti → rapor.

## 2026 %100 bitir (eksik abone + alinti + FLOOD)

```
99_BOT_ARSIV\calistir\TARA_2026_BITIR.bat
```

2025 taramasi **ancak 2026 %100 olduktan sonra**:

```
99_BOT_ARSIV\calistir\TARA_2025_DEVAM.bat
```

Ikisi sirayla (otomatik kapı):

```
99_BOT_ARSIV\calistir\TARA_SIRA.bat
```

## Tam derin tarama (aylik / eksik coksa)

```
99_BOT_ARSIV\calistir\TARA_2026_ABONE_FLOOD.bat
```

## Durum raporu

```bash
python 99_BOT_ARSIV/kod/kapsam_2026.py
```

Cikti: **TARAMA_2026.md** — genel %, ana / alinti / flood ayri.

## Claude paketi

%100 oldugunda `tara_2026_guncel.py` otomatik `claude_paket_olustur.py` calistirir.
Degisiklikleri Claude Project'e elle yukle (04, 07, 03).
