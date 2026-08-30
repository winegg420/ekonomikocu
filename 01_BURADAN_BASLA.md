# CLAUDE — BURADAN BAŞLA

**Kaynak (birincil):** [https://github.com/winegg420/ekonomikocu](https://github.com/winegg420/ekonomikocu) — dosyalari yerel yukleme yerine repodan cek. Claude Project: GitHub entegrasyonu veya repo clone.

**Claude:** `01` → `02` (**makro sentez — ZORUNLU**) → `03` → `04` → `05` → `06` (+ opsiyonel `07`)

**Gemini:** ayni `01-06`, sonra `08` → `09` klasor → `10`

**Tarama:** `TARAMA_DURUMU.md` — su tarihe kadar kayit tamam (`python 99_BOT_ARSIV/kod/kapsam_durum.py`)

`00_OKU_YUKLEME_SIRASI.txt` · Paket: `99_BOT_ARSIV/kod/claude_paket_olustur.py` · GitHub: `99_BOT_ARSIV/kod/github_guncelle.py`

---

## ⚠️ KALICI KURAL — bu dosyayı güncel tut

Yeni dış kaynak eklendiğinde, yeni bir `magicma/` script'i/sistemi eklendiğinde, önemli
bir dosya sayısı/durum değiştiğinde: **commit atmadan ÖNCE bu dosyanın ilgili bölümünü de
güncelle** — ayrı bir hatırlatma beklenmeden, o işin doğal parçası olarak. Bu dosya
projenin haritası; bayatlarsa yeni oturumlar eksik resimle başlar.

*(Aynı kural `PROGRESS.md`'nin en üstünde de duruyor — oturumlar önce orayı okuyor.)*

---

## Amaç
Ida'yı **mentorlük** ile yönlendir: Koç'un **Trump / ABD / Fed makro yorumları** ile **teknik analiz ve grafiklerini birleştirerek** makro resmi okut. Bot değil; **kanıt defteri**. Detay: **02** bölüm «Makro sentez».

## Öncelik (yapay zeka)
Makro (Trump, Fed, ABD politikası, jeopolitik) + teknik (seviye, grafik) **ayrı değil — tek anlatı**. Haber botu değilsin; sadece Koç'un söylediklerini sentezle. **02 ★ Kalıcı mentor kuralları** (grafik, güncel fiyat, atıf, iletişim).

## Veri (30 Ağustos 2026)
Arşiv `cekilen_tweetler.jsonl`: **7.365** tweet (**3.879** public + **3.486** abone dönemi).
Yükleme paketi: `04_TWEETLER.jsonl` **3.884** kayıt · `07_ABONE_TWEETLER.jsonl` **3.434** kayıt.
Görsel: `medya/` **1.388** tweet klasörü / **1.457** dosya · işlenmiş görsel defteri
`gorsel_analiz.jsonl` **674** kayıt. Detay: **08** + **05**

## Abonelik (Nisan 2026+)
**3.434** abone tweeti metinli (`07_ABONE_TWEETLER.jsonl` veya **04**'te `kayit_tipi: abone`) · **0** hâlâ boş.

**ÖNEMLİ:** Abone metinleri `locked: false`. `locked: true` arama = yanlış. Önce **07** dosyasını oku veya `kayit_tipi: abone` filtrele.

---

## KOÇ DIŞI ANALİSTLER — `11_DIS_KAYNAKLAR.md`

**Bu dosyadaki hiçbir görüş Koç'a atfedilmez**; Koç'un kendi çerçevesi `06_ANALIZ.md`'dedir.

**23 kaynak** (`grep -n "^## " 11_DIS_KAYNAKLAR.md` ile eşleştirildi, elle yazılmadı):

Sellcoin · Atilla Yeşilada · Berk Dinçtürk · Tunç Şatıroğlu · Emrah Lafçı & Ali Perşembe ·
Baki Atılal · Emrah Altınocağı · Erol Polat (Money Talks — Üç Harfler) · **Cüneyt Paksoy** ·
Ferhat Yükseltürk & Uraz Çay · Cihat E. Çiçek · Barış Soydan ·
**Integral FX TV (Erhan Aslanoğlu / panel)** · Şant Manukyan · Turhan Bozkurt · Bora Özkent ·
Fiba Bank ("Parayı Ne Yapalım?") · **Kemal Hiçyılmaz (cryptokemal)** · **Kripto Teknik (Oytun & Altun)** ·
**Erkan Öz**

Ayrıca 24 Ağustos derlemesi içinde ayrı bölümü olmayan üç kaynak:
**Onur Duygu** (Font Turkey) · **Doruk İşmen** · **Prof. Dr. Daron Acemoğlu**
*(Acemoğlu fiyat/seviye vermediği için karneye alınmaz.)*

### Dış kaynak analiz katmanı (12–18)

| Dosya | Ne tutar |
|---|---|
| `12_KAYNAK_PERFORMANS.md` | Kaynak başına TUTTU/TUTMADI sayımı + isabet sıralaması. **EK A:** hedef büyüklüğü (cesaret) ağırlıklı karne · **EK B:** piyasa rejimine göre performans |
| `13_KONSENSUS.md` + `magicma/kaynak_konsensus.json` | 2+ kaynağın ±%2 içinde buluştuğu **18** sayısal konsensüs, ağırlıklı skorla sıralı |
| `14_CELISKI_PANELI.md` | 7 analist↔analist + 6 Koç↔dış kaynak çelişkisi |
| `15_KOC_TUTARLILIK.md` | Koç'un kendi arşiviyle tutarlılığı (3 tutarsızlık, 5 tutarlı) |
| `16_ZAMANLAMA_KARNESI.md` | Tarih penceresi karnesi — fiyat karnesinden AYRI (46 pencere, 9 kapandı) |
| `17_SECICI_HAFIZA.md` | Kendi geçmiş çağrılarını alıntılama seçiciliği (140 kendi-atıf, 0 hata itirafı) |
| `18_ONCU_TAKIPCI.md` | Her konsensüs konusunu ilk kim söyledi (15 öncülük, 41 takipçilik) |

**Kural:** `11_DIS_KAYNAKLAR.md`'ye yeni giriş eklenince yukarıdaki dosyalar da
güncellenmeli — ayrıntılı eşleştirme tablosu o dosyanın **sonundaki** "🔗 Türetilmiş
analiz dosyaları" bölümünde.

---

## MAGICMA BOT SİSTEMİ

TradingView'den okunan MagicMA band seviyelerini canlı fiyatla karşılaştırıp
Telegram'a işlem adayı bildiren, kendi isabetini ölçen otonom sistem.
Ayrıntılı kullanım: `magicma/README.md` · kurallar: `CLAUDE.md`.

### Akış
```
gunun_hareketlileri_guncelle.py   (cryptobubbles → günün hareketlileri tazelenir)
        ↓
magicma_gozetmen.py → magicma_tara_dayanikli.py   (TradingView, CDP 9222; Chrome ölürse self-heal)
        ↓  99_BOT_ARSIV/kod/magicma_ham.jsonl
telegram_alarm.py   (10 dk'da bir, Windows Task Scheduler "MagicMA Telegram Alarm")
        ├── fiyat_kontrol.py     → Binance/MEXC/Gate/Bybit/OKX/KuCoin + Yahoo + gold-api
        ├── bant_yon.py          → band içi LONG/SHORT yönü (saatlik kapanış serisiyle)
        ├── piyasa_saati.py      → her varlık sınıfı yalnız kendi seansında taranır
        ├── onemli_seviye.py     → Koç + dış analist seviyeleri, mega-confluence
        └── magicma_karne.py     → her bildirim bir iddia; başarı/başarısızlık ölçülür
```

### Dosya haritası
| Dosya | Görev |
|---|---|
| `magicma/telegram_alarm.py` | Ana bildirim motoru. Her mesajda **tüm** yakın adaylar listelenir; yeni girenlerde 🆕 |
| `magicma/fiyat_kontrol.py` | Toplu canlı fiyat (747 sembolün ~744'ü, ~30 sn). `adaylari_hesapla()` imzasını bozma |
| `magicma/bant_yon.py` | MagicMA çizgileri bağımsız seviye değil **bandın iki sınırı**; yön band konumundan |
| `magicma/piyasa_saati.py` | BIST / ABD / FX seansları (DST `zoneinfo` ile, tarih hardcode yok); kripto 7/24 |
| `magicma/magicma_karne.py` | Sinyal karnesi → `karne_kayitlari.json` (commit edilir), rapor `KARNE_RAPOR.md` |
| `magicma/onemli_seviye.py` + `onemli_seviyeler.json` | Koç ve dış analistlerin **somut** seviyeleri (elle doldurulur) |
| `magicma/gunluk_ozet.py` | Her sabah 08:20-08:40 TSI tek özet: açık adaylar, karne, Koç takvimi, hareketliler |
| `magicma/koc_tetigi.py` + `koc_tetigi_durum.json` | Koç'un 3 boğa şartı (DXY 110→95 · faiz indirimi · Çin/emtia anlaşması) |
| `99_BOT_ARSIV/kod/magicma_kara_liste.py` | TradingView'de okunamayan "ölü" semboller; kendi kendini günceller |

### Güncel durum (30 Ağustos 2026)
- **Sembol listesi: 546** — kripto 114 · BIST 183 · ABD 92 · forex/emtia 30 · endeks/faiz 7 · günün hareketlileri 120
- **Sinyal karnesi: 274 kayıt** — 111 başarılı · 133 başarısız · 30 açık (**başarı oranı %45,5**)
  → kaynak türü: 267 teknik · 6 önemli seviye · 1 mega-confluence
- **Önemli seviyeler kütüphanesi: 126 kayıt** — 20 enstrüman, 16 kaynak
- Son MagicMA taraması: 30 Ağustos 2026, **457 sembol**, 28 işlem adayı
  (`magicma/magicma_islem_adaylari_2026-08-30.md`)

### Sık kullanılan komutlar
```bash
py -3 99_BOT_ARSIV/kod/gunun_hareketlileri_guncelle.py   # önce bubbles tazele
py -3 99_BOT_ARSIV/kod/magicma_gozetmen.py               # sonra tara (gözetmenli)
py -3 99_BOT_ARSIV/kod/magicma_islem_adaylari.py         # ≤ %0,25 işlem adayları
py -3 magicma/fiyat_kontrol.py                           # çizgileri taramadan hızlı fiyat kontrolü
py -3 magicma/telegram_alarm.py --kuru                   # bildirimi göndermeden ekrana yaz
py -3 magicma/magicma_karne.py                           # karneyi değerlendir + rapor
```

**Kritik kural:** MagicMA taraması ile X (tweet) taraması **aynı anda çalıştırılamaz** —
ikisi de aynı Chrome'u (CDP 9222) kullanıyor ve X tarayıcı TradingView sekmesini kapatıyor.
