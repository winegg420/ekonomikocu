# Veri Semasi — ekonomikocu (zenginlestirme sonrasi)

## Orijinal (degismedi)

- `04_TWEETLER.jsonl` — public tweetler
- `07_ABONE_TWEETLER.jsonl` — abone akisi

## Zenginlestirilmis tweet dosyalari

`04_TWEETLER_v2.jsonl` / `07_ABONE_TWEETLER_v2.jsonl` — orijinal + yeni alan:

| Alan | Tip | Degerler |
|------|-----|----------|
| `kaynak` | string | `koc`, `alinti:cowen`, `alinti:trump`, `alinti:green`, `alinti:dd_finance`, `alinti:saylor`, `belirsiz`, ... |

## Yeni cikti dosyalari

| Dosya | Icerik |
|-------|--------|
| `kaynak_raporu.md` | Kaynak dagilim ozeti |
| `cagrilar.jsonl` | Sayisal seviye cagrilari (karne temeli) |
| `grafik_seviyeleri.jsonl` | Vision ile okunan grafik seviyeleri |

### cagrilar.jsonl

```json
{
  "tweet_id": "...",
  "tarih": "YYYY-MM-DD",
  "urun": ["BTC"],
  "seviyeler": [124000, 128000],
  "yon": "yukari|asagi|belirsiz",
  "vade_tarihi": "YYYY-MM-DD|null",
  "kaynak": "koc|alinti:...",
  "metin": "...",
  "fiyat_dogrulama": "BEKLIYOR"
}
```

### grafik_seviyeleri.jsonl

```json
{
  "tweet_id": "...",
  "gorsel": "grafikler/..._graf_01.jpg",
  "urun": "BTCUSD",
  "okunan_seviyeler": [60000, 150000],
  "etiketler": ["60 K", "60K +1"],
  "senaryo_notu": "...",
  "net_okunabilir": true
}
```

## Calistirma

```
python 99_BOT_ARSIV/kod/enrichment/calistir_hepsi.py
```

Adim adim:
```
python 99_BOT_ARSIV/kod/enrichment/kaynak_etiketle.py
python 99_BOT_ARSIV/kod/enrichment/cagri_cikar.py
python 99_BOT_ARSIV/kod/enrichment/grafik_vision_oku.py
```

Vision icin (opsiyonel): `OPENAI_API_KEY` ortam degiskeni.
