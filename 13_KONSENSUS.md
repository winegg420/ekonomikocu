# 13 — KAYNAKLAR ARASI KONSENSÜS

_Güncelleme: 2026-08-30_

> **Kaynak:** `11_DIS_KAYNAKLAR.md`'deki sayısal iddialar. Makine + elle doğrulama
> karışımı; şüpheli eşleşmeler yanlış pozitif üretmemek için **bilerek atlandı**
> (atlananların gerekçesi aşağıda "Kasıtlı olarak sayılmayanlar" bölümünde).
> Ham veri: `magicma/kaynak_konsensus.json`.
>
> **Tolerans:** ±%2, sayı büyüklüğüne orantılı. Bir grubun içindeki en uzak iki
> değer bu farkı aşıyorsa grup **bölünür veya atlanır** — birleştirilmez.
>
> **SIRALAMA AĞIRLIKLI SKORA GÖREDİR**, ham kaynak sayısına göre değil.
> `ağırlıklı_skor = kaynak_sayısı × (ortalama_isabet_oranı / 100)`
> İsabet oranı `12_KAYNAK_PERFORMANS.md`'den gelir; orada "henüz değerlendirilemez"
> olan kaynak **nötr %50** sayılır. Parantez içindeki sayı ham kaynak sayısıdır.
>
> **BU DOSYA NASIL GÜNCELLENİR:**
> 1. `11_DIS_KAYNAKLAR.md`'ye yeni giriş eklenince yeni sayısal iddialar buraya taranır.
> 2. `12_KAYNAK_PERFORMANS.md`'deki isabet oranları değişirse **buradaki tüm
>    `agirlikli_skor` değerleri ve sıralama yeniden hesaplanmalıdır.**
> 3. Yeni bir konsensüs kaydı `magicma/onemli_seviyeler.json`'a girmeye aday
>    olabilir — somut sayısal seviye içeriyorsa oraya da ELLE eklenmeli
>    (alarm motoru bu dosyayı okumaz, `onemli_seviyeler.json`'u okur).


## SIRALAMA

| # | Konu | Değer aralığı | Ağırlıklı skor | Ham kaynak | Kaynaklar | İlk tespit |
|---|---|---|---|---|---|---|
| 1 | Altın kısa vade taban/biriktirme bandı (ons $) | 4000 – 4500 | **3,5** | (7) | Sellcoin, Berk Dinçtürk, Emrah Lafçı & Ali Perşembe, Baki Atılal, Cüneyt Paksoy, Tunç Şatıroğlu, Integral FX TV | 2026-08-06 |
| 2 | Fed Eylül 2026 toplantısında faiz ARTIRMAZ | 35 – 36,4 | **3,0** | (6) | Sellcoin, Emrah Lafçı & Ali Perşembe, Barış Soydan, Onur Duygu, Tunç Şatıroğlu, Berk Dinçtürk | 2026-08-10 |
| 3 | TCMB gevşeme yönü — politika faizi 40 -> 37, haftalık repoya dönüş | 37 – 40 | **2,5** | (5) | Cüneyt Paksoy, Ferhat Yükseltürk & Uraz Çay, Emrah Lafçı & Ali Perşembe, Barış Soydan, Integral FX TV | 2026-08-13 |
| 4 | Gümüş Ağustos toparlanma bandı (ons $) | 66 – 67 | **2,5** | (4) | Şant Manukyan, Barış Soydan, Turhan Bozkurt, Erkan Öz | 2026-08-17 |
| 5 | Altın uzun vade hedef bandı (ons $) | 5000 – 6500 | **2,0** | (4) | Cüneyt Paksoy, Tunç Şatıroğlu, Turhan Bozkurt, Emrah Lafçı & Ali Perşembe | 2026-08-13 |
| 6 | ABD kamu borcu 40 trilyon $ eşiğini geçti | 40 – 42 | **2,0** | (4) | Barış Soydan, Bora Özkent, Emrah Altınocağı, Integral FX TV | 2026-08-20 |
| 7 | BIST100 kritik eşik bölgesi | 14000 – 14500 | **2,0** | (4) | Cüneyt Paksoy, Atilla Yeşilada, Tunç Şatıroğlu, Barış Soydan | 2026-08-13 |
| 8 | BIST yukarı kırılım hedef bandı | 16000 – 17000 | **1,5** | (3) | Emrah Lafçı & Ali Perşembe, Integral FX TV, Cüneyt Paksoy | 2026-08-25 |
| 9 | Fed'in yönü ŞAHİN — Eylül'de/seçim sonrası faiz ARTIRIMI | 35 – 40 | **1,5** | (3) | Integral FX TV, Erkan Öz, Emrah Lafçı & Ali Perşembe | 2026-08-25 |
| 10 | Japon yen carry-trade çözülmesi = piyasanın en büyük riski | 4,05 | **1,5** | (3) | Erol Polat / Money Talks, Cihat E. Çiçek, Integral FX TV | 2026-08-18 |
| 11 | USDTRY yıl sonu bandı | 50 – 55 | **1,5** | (3) | Integral FX TV, Cüneyt Paksoy, Turhan Bozkurt | 2026-08-17 |
| 12 | BTC direnç/tetik seviyesi | 67000 – 67300 | **1,5** | (3) | Sellcoin, Kemal Hiçyılmaz, Emrah Lafçı & Ali Perşembe | 2026-08-10 |
| 13 | BTC 200 günlük ortalama / alım bölgesi | 69000 – 69350 | **1,5** | (3) | Emrah Lafçı & Ali Perşembe, Erkan Öz, Kripto Teknik | 2026-08-27 |
| 14 | US10Y alarm seviyesi | 5 | **1,0** | (2) | Cüneyt Paksoy, Integral FX TV | 2026-08-25 |
| 15 | Türkiye CDS risk primi (baz puan) | 217 – 219 | **1,0** | (2) | Cüneyt Paksoy, Emrah Lafçı (solo) | 2026-08-27 |
| 16 | MSCI / endeks çıkarma riski (BIST) | 50 | **1,0** | (2) | Atilla Yeşilada, Erol Polat / Money Talks | 2026-08-19 |
| 17 | Gıda enflasyonu yapısal risk | — | **1,0** | (2) | Atilla Yeşilada, Fiba Bank | 2026-08-19 |
| 18 | CLARITY Act Eylül 2026'da gündeme gelir | — | **1,0** | (2) | Berk Dinçtürk, Kemal Hiçyılmaz | 2026-08-20 |

---

## KAYIT NOTLARI

**1. Altın kısa vade taban/biriktirme bandı (ons $)** — 4000 – 4500 · ağırlıklı skor 3,5 (7 kaynak)  
Dosyadaki en geniş yakınsama. Band %12,5 geniş olduğu için nokta konsensüsü değil; her kaynak bandın farklı bir kenarını vurguluyor (Atılal 4.000 destek, Paksoy 4.400-4.500 duvar).

**2. Fed Eylül 2026 toplantısında faiz ARTIRMAZ** — 35 – 36,4 · ağırlıklı skor 3,0 (6 kaynak)  
Değer aralığı, artırım ihtimalinin fiyatlanan yüzdesidir (%36,4 CPI sonrası, %35 Jackson Hole günü). Aynı dosyada bunun TERSİ yönde 3 kaynaklı bir grup da var — bkz. 14_CELISKI_PANELI.md.

**3. TCMB gevşeme yönü — politika faizi 40 -> 37, haftalık repoya dönüş** — 37 – 40 · ağırlıklı skor 2,5 (5 kaynak)  
Dosyadaki tek GERÇEKLEŞMİŞ konsensüs: Integral FX TV 10 Eylül dedi, 25 Ağustos'ta oldu (16 gün erken).

**4. Gümüş Ağustos toparlanma bandı (ons $)** — 66 – 67 · ağırlıklı skor 2,5 (4 kaynak)  
Manukyan 66,0 · Soydan 66,5 · Bozkurt 67,0 · Erkan Öz 66,35 — aralarındaki fark %1,5, tolerans içinde. Koç'un Temmuz'daki 54-62 bandının ÜSTÜNDE (bkz. 14_CELISKI_PANELI.md).

**5. Altın uzun vade hedef bandı (ons $)** — 5000 – 6500 · ağırlıklı skor 2,0 (4 kaynak)  
Yalnızca kaynakların KENDİ hedefleri sayıldı. UBS $5.000 ve Citibank $6.000 aktarım olduğu için kaynak sayısına dahil edilmedi (Soydan ve Integral FX TV aktarıyor). Berk Dinçtürk'ün $10.000'i bandın dışında — bkz. çelişki paneli.

**6. ABD kamu borcu 40 trilyon $ eşiğini geçti** — 40 – 42 · ağırlıklı skor 2,0 (4 kaynak)  
Trilyon $. Dört kaynak aynı olguyu bağımsız aktarıyor; üçü bundan aynı sonucu (para arzı artışı mecburiyeti) çıkarıyor.

**7. BIST100 kritik eşik bölgesi** — 14000 – 14500 · ağırlıklı skor 2,0 (4 kaynak)  
DİKKAT — aynı sayı, ZIT yön: Paksoy 14.000-14.500'ü 'asla kırılmamalı' destek sayarken Yeşilada 14.000'i güçlü DİRENÇ sayıyor. Sayısal örtüşme gerçek, yorum örtüşmesi yok. Bkz. 14_CELISKI_PANELI.md.

**8. BIST yukarı kırılım hedef bandı** — 16000 – 17000 · ağırlıklı skor 1,5 (3 kaynak)  
Üç kaynak üç FARKLI yöntemle aynı sayıya geliyor: haftalık sıkışma formasyonu (Lafçı/Perşembe), USDTRY çarpanı x hisse başı ~$300 (Aslanoğlu), bankacılık endeksi direnci (Paksoy). Dosyadaki en güçlü yöntem-bağımsız kesişim.

**9. Fed'in yönü ŞAHİN — Eylül'de/seçim sonrası faiz ARTIRIMI** — 35 – 40 · ağırlıklı skor 1,5 (3 kaynak)  
Bu, yukarıdaki 'Fed artırmaz' konsensüsünün TERSİ. İkisi aynı dosyada yan yana duruyor; Lafçı & Perşembe her iki listede de var çünkü aynı program hem 'artırmaz' hem '~%35 artırım ihtimali' diyor. Ayrışma Koç'un boğa şartını doğrudan tehdit ediyor.

**10. Japon yen carry-trade çözülmesi = piyasanın en büyük riski** — 4,05 · ağırlıklı skor 1,5 (3 kaynak)  
Değer, Cihat E. Çiçek'in dayanak yaptığı Japon 30 yıllık tahvil faizi (%4,05). Diğer iki kaynak sayı vermeden aynı riski işaretliyor. 18 Ağustos Japon borsası çöküşüyle kısmen teyitli.

**11. USDTRY yıl sonu bandı** — 50 – 55 · ağırlıklı skor 1,5 (3 kaynak)  
Aslanoğlu 50-55 (muhtemel 53-54) · Paksoy 52-55 · Bozkurt 52-55 iyimser (60+ kötümser). Üç bandın kesişimi 52-55.

**12. BTC direnç/tetik seviyesi** — 67000 – 67300 · ağırlıklı skor 1,5 (3 kaynak)  
Sellcoin 67.300 · Kemal Hiçyılmaz 67.000 · Lafçı/Perşembe 67.265. Aralarındaki fark %0,45 — dosyadaki EN DAR sayısal örtüşme. Seviye Ağustos sonunda yukarı kırıldı.

**13. BTC 200 günlük ortalama / alım bölgesi** — 69000 – 69350 · ağırlıklı skor 1,5 (3 kaynak)  
Lafçı/Perşembe 69.170 (alım) · Erkan Öz ~69.350 (200 GO) · Kripto Teknik 69.000 (200 GO). Fark %0,5. MagicMA'nın BTCUSDT Günlük bandı (68.450-69.244) ile ÇAKIŞIYOR — mega-confluence adayı, alarm motoru bunu yıldızlı bildirmeli.

**14. US10Y alarm seviyesi** — 5 · ağırlıklı skor 1,0 (2 kaynak)  
Berk Dinçtürk'ün %4,75 'Hazine tolerans tavanı' bu gruba DAHİL EDİLMEDİ: 4,75 ile 5,00 arasındaki fark %5,3, artı/eksi %2 toleransının dışında. Kaynak dosyası bunu 'üçlü kesişim' diye anıyor ama sayısal olarak üç ayrı eşik. Barış Soydan'ın aktardığı Hartnett %5'i 30 YILLIK için veriyor — farklı vade, o da sayılmadı.

**15. Türkiye CDS risk primi (baz puan)** — 217 – 219 · ağırlıklı skor 1,0 (2 kaynak)  
Fark %0,9. Farklı tarihte iki bağımsız ölçüm; dosyada 'DOĞRULANDI (çapraz kaynak)' olarak karneye geçmiş.

**16. MSCI / endeks çıkarma riski (BIST)** — 50 · ağırlıklı skor 1,0 (2 kaynak)  
Değer, Yeşilada'nın verdiği ~50 milyar $ pasif fon çıkışı riski. Erol Polat aynı riski (gelişmekte olan -> sınır piyasa) sayı vermeden işaretliyor.

**17. Gıda enflasyonu yapısal risk** — — · ağırlıklı skor 1,0 (2 kaynak)  
Sayısal değer yok. İki kaynak birbirinden habersiz, gerekçeleri farklı (arz/lojistik vs fiyat yapışkanlığı), sonuç aynı. Koç bu temayı hiç takip etmiyor — çerçevesindeki bir boşluk.

**18. CLARITY Act Eylül 2026'da gündeme gelir** — — · ağırlıklı skor 1,0 (2 kaynak)  
Kemal Hiçyılmaz somut tarih veriyor (15 Eylül oylama, Senatör Lummis), Berk Dinçtürk sadece 'Eylül' diyor. Emrah Altınocağı aynı olaya dolaylı değiniyor ama Clarity'nin asıl gündem olmadığını savunduğu için kaynak sayısına katılmadı.

---

## AĞIRLIKLANDIRMA ÇALIŞIYOR MU? — örnek hesap

Formülün ham kaynak sayısını gerçekten değiştirdiğini gösteren tek somut örnek
şu an dosyada iki satır arasındaki yer değişimidir:

| Konu | Ham kaynak | Ortalama isabet | Ağırlıklı skor |
|---|---|---|---|
| TCMB gevşeme yönü | **5** | %50 (5 kaynağın 5'i de "henüz değerlendirilemez") | 5 × 0,50 = **2,50** |
| Gümüş Ağustos toparlanma bandı | **4** | %62,5 → (100 + 50 + 50 + 50) / 4 | 4 × 0,625 = **2,50** |

Açık hesap (gümüş satırı):

```
kaynaklar        = Şant Manukyan (%100) + Barış Soydan (nötr %50)
                   + Turhan Bozkurt (nötr %50) + Erkan Öz (nötr %50)
ortalama_isabet  = (100 + 50 + 50 + 50) / 4 = %62,5
agirlikli_skor   = 4 × (62,5 / 100) = 2,34 değil, 2,50
```

Yani **4 kaynaklı bir grup, 5 kaynaklı bir grupla eşitlendi** — çünkü içindeki bir
kaynağın kapanmış karnesi var. Ham sayıya göre sıralasaydık TCMB tek başına
önde olurdu.

**Ama dürüst uyarı:** bugün 23 kaynaktan **yalnızca 1'inin** (Şant Manukyan)
değerlendirilebilir karnesi olduğu için ağırlıklandırma pratikte neredeyse hiç
ayrım üretmiyor — 18 kaydın 17'sinde skor basitçe `kaynak_sayısı × 0,50`. Formül
doğru çalışıyor, **girdi yetersiz.** `12_KAYNAK_PERFORMANS.md`'deki "kapatılmayı
bekleyen iddialar" listesi işlendikçe bu sıralama gerçekten anlam kazanacak.

---

## KASITLI OLARAK SAYILMAYANLAR (yanlış pozitif önleme)

Aşağıdaki eşleşmeler ilk bakışta konsensüs gibi duruyor ama sayılmadı:

- **US10Y %4,75 (Berk Dinçtürk) + %5,00 (Paksoy, Aslanoğlu).** Aradaki fark %5,3 —
  ±%2 toleransının dışında. Kaynak dosyası bunu "üçlü kesişim" diye anıyor;
  sayısal olarak **üç ayrı eşik**. Yalnızca birebir eşleşen %5,00 çifti kaydedildi.
- **Hartnett'in 30 yıllık %5 kırmızı çizgisi.** Aynı sayı ama **farklı vade**
  (30Y ≠ 10Y). Vade karıştırılırsa sahte kesişim üretir.
- **Petrol 89 – 93,7 $ (Yeşilada, Fiba, Manukyan, Lafçı, Berk).** Bunlar tez değil,
  **farklı günlerdeki spot fiyat gözlemleri**. Aynı fiyatı görmek konsensüs değildir.
- **Platin 1.629,5 → 1.830 ve 1.770 / 1.710.** İkisi de aynı kaynaktan
  (Emrah Lafçı & Ali Perşembe) — tek kaynak, konsensüs olmaz.
- **Freeport-McMoRan $85-90** ve **NASA hisse hedefi 52.** Tek kaynaklı somut
  hedefler; karnede takipteler ama konsensüs değiller.
- **Eylül'ün "kırılma ayı" olması.** Beş kaynak Eylül'ü işaretliyor ama
  **yönleri zıt** (Şatıroğlu düşüş, Koç yukarı kırılım, Kripto Teknik golden cross).
  Ortak olan tarih, iddia değil — bu yüzden `16_ZAMANLAMA_KARNESI.md`'ye taşındı.
