# magicma/ — Fiyat yakınlık motoru, alarm ve karne

Bu klasör, MagicMA taramasından çıkan seviyeleri güncel fiyatlarla karşılaştırıp
Telegram'a işlem fırsatı bildiren sistemi barındırır.

## Dosyalar

| Dosya | İş |
|---|---|
| `fiyat_kontrol.py` | Seviyeleri okur, canlı fiyat çeker, eşik içindeki adayları + **çakışan seviye (confluence)** tespitini üretir. Diğer scriptler bunu import eder. |
| `bant_yon.py` | Çizgileri banda çevirir, LONG/SHORT yönünü belirler. |
| `piyasa_saati.py` | Her varlık sınıfı yalnızca kendi açık saatinde taranır. |
| `telegram_alarm.py` | 10 dakikada bir çalışır (Task Scheduler), tüm katmanları birleştirip **tek** Telegram mesajı gönderir. |
| `onemli_seviye.py` | Koç + dış analist seviyelerini karşılaştırır, **mega-confluence** tespit eder. |
| `onemli_seviyeler.json` | **Elle bakımlı** seviye kütüphanesi (aşağıya bak). |
| `magicma_karne.py` | Botun kendi sinyallerinin tutup tutmadığını ölçer, `KARNE_RAPOR.md` üretir. |
| `gunluk_ozet.py` | Her sabah 08:20-08:40 arası tek "Günlük Özet" mesajı. |
| `koc_tetigi.py` | Koç'un 3 koşullu boğa tetiğini izler, koşul sayısı değişince bildirir. |
| `koc_tetigi_durum.json` | **Elle bakımlı** Çin-ABD anlaşma bayrağı (aşağıya bak). |

## Sinyal kategorileri (karıştırılmamalı)

Dördü de aynı mesajda, bu öncelik sırasıyla görünür:

1. **🌟 MEGA-CONFLUENCE** — aynı sembolde MagicMA teknik çizgisi **VE** Koç/dış
   kaynak seviyesi aynı fiyat bölgesinde (fark ≤ `MEGA_CONFLUENCE_ESIK_YUZDE`,
   %0,3). Teknik ve temel aynı noktada birleşiyor — en güçlü sinyal.
2. **🔥 ÇAKIŞAN SEVİYE** — birden fazla **MagicMA** çizgisi çakışıyor
   (≤ `CONFLUENCE_ESIK_YUZDE`, %0,15). İki alt tipi var:
   *bantlar arası* (Günlük + Haftalık = bağımsız teyit) ve *dar band*
   (tek bandın iki kenarı — teyit değil).
3. **📌 ÖNEMLİ SEVİYE** — yalnızca Koç/dış kaynak seviyesine yakınlık
   (≤ `ONEMLI_SEVIYE_ESIK_YUZDE`, %0,5).
4. Tekil MagicMA teması (≤ %0,25) — sade tek satır.

Eşikler ilgili dosyaların başında sabit değişken olarak durur.

## ⚠️ `onemli_seviyeler.json` OTOMATİK GÜNCELLENMEZ

Bu dosya **elle** bakımlıdır. Kaynağı `06_ANALIZ.md` (Koç) ve
`11_DIS_KAYNAKLAR.md` (dış analistler).

**Kural:** `11_DIS_KAYNAKLAR.md` veya `06_ANALIZ.md`'ye yeni bir dış kaynak
girişi ya da Koç tweet'i eklendiğinde, içindeki **somut sayısal seviyeler de
`onemli_seviyeler.json`'a elle eklenmelidir.** Bu adım otomatik değildir;
gelecekteki Claude Code oturumlarının unutmaması için buraya not düşüldü.

Ne eklenir / eklenmez:

- ✅ **Eklenir:** tek sayı veya dar aralık, açıkça bir enstrümana bağlı
  ("BTC 84K pivot", "US10Y %4,75 tavan", "BIST 16.500-17.000 direnç bandı").
- ❌ **Eklenmez:** yorumsal/belirsiz ifadeler ("yükseliş potansiyeli var",
  "temkinli"), enstrümana bağlanmayan makro görüşler, fon/hisse önerileri.

Kayıt formatı:

```json
{
  "kaynak": "Berk Dincturk",
  "enstruman": "US10Y",
  "seviye": 4.75,
  "tur": "tavan",
  "aciklama": "Bessent tolerans tavani - Hazine burada devreye girer",
  "tarih_eklendi": "2026-08-20"
}
```

Bant için `seviye` yerine `seviye_alt` + `seviye_ust` kullanılır.

- `enstruman`, `magicma/sembol_listesi/*.txt` dosyalarındaki kısa sembol adıyla
  **birebir** aynı olmalı (`BTCUSDT`, `XAUUSD`, `US10Y`, `XU100`, `NDX`, `DXY`…),
  yoksa fiyat karşılaştırması yapılamaz. Karşılığı olmayan enstrüman sessizce
  atlanmaz — log'a `[ONEMLI] Taramada karsiligi olmayan ... atlandi` düşer.
  (Bu yüzden GBPTRY kaydı bilerek girilmedi: taranan evrende yok.)
- `tur`, yön tespitinde kullanılır: fiyat bandın **içindeyken** geometri yön
  veremez, tür belirler (`direnc_bandi` → short, `kritik_destek` → long).
  Tanınan türler `onemli_seviye.py` içindeki `DIRENC_TURLERI` / `DESTEK_TURLERI`
  kümelerinde; yeni bir tür eklerken oraya da yazın, yoksa yön TAHMİN'e düşer.

Ekledikten sonra doğrula:

```bash
py -3 magicma/onemli_seviye.py --dogrula   # sadece kütüphane doğrulaması
py -3 magicma/onemli_seviye.py             # canlı fiyatlarla aday + mega listesi
```

## ⚠️ `koc_tetigi_durum.json` da ELLE bakımlı

Koç'un boğa tetiğinin 3. koşulu (Çin/ABD emtia-ticaret anlaşması) ikili bir
olay; sürekli taranamaz. Bu yüzden bir bayrak olarak tutulur:

```json
{"cin_abd_anlasma": false, "son_guncelleme": "2026-08-29", "dayanak": ""}
```

**`koc_tetigi.py` bu dosyayı ASLA kendisi değiştirmez — sadece okur.**
`11_DIS_KAYNAKLAR.md`'ye böyle bir anlaşmayı **doğrulayan** bir kaynak
eklendiğinde `cin_abd_anlasma` elle `true` yapılır ve `dayanak` alanına kaynak
yazılır. Bu, yeni kaynağı ekleyen oturumun görevidir.

Diğer iki koşulun otomasyon seviyesi farklıdır ve mesajda böyle sunulur:
**DXY** tam otomatik (canlı fiyat), **faiz** ise canlı değil — ücretsiz bir
FedWatch ucu olmadığı için `11_DIS_KAYNAKLAR.md`'de en son geçen faiz ifadesi
vekil olarak kullanılır ve mesajda kaynak adı + tarihiyle etiketlenir.

## Sık kullanılan komutlar

```bash
py -3 magicma/fiyat_kontrol.py              # mentor için tam yakınlık raporu
py -3 magicma/telegram_alarm.py --kuru      # göndermeden mesajı ekrana yaz
py -3 magicma/magicma_karne.py              # açık sinyalleri değerlendir + rapor
py -3 magicma/magicma_karne.py --haftalik   # haftalık özet metni (göndermez)
py -3 magicma/gunluk_ozet.py --kuru         # günlük özeti göndermeden yaz
py -3 magicma/gunluk_ozet.py --zorla        # pencereyi/tekrar korumasını atlayıp gönder
py -3 magicma/koc_tetigi.py --kuru          # boğa tetiği durumunu göndermeden yaz
py -3 magicma/onemli_seviye.py --dogrula    # seviye kütüphanesini doğrula
```

**Zamanlama:** Windows Task Scheduler'daki tek görev **"MagicMA Telegram Alarm"**
7/24 her 10 dakikada `telegram_alarm.py` çalıştırır. Günlük özet, Koç tetiği ve
haftalık karne özeti bu görevin akışına bağlıdır — ayrı görev açılmadı.

Kapatma bayrakları: `--karne-yok`, `--onemli-seviye-yok`,
`--piyasa-saatini-yoksay`, `--mesaj-araligi 0`.
