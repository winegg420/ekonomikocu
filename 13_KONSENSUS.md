# 13 — KAYNAKLAR ARASI KONSENSÜS

_Güncelleme: 2026-09-07_ (5 video: **4 yeni kayıt** — ECB 10 Eylül, gram altın 10.000 TL, TCMB yıl sonu %35, BIST 14.000 destek; altın 4.800-5.000 kaydı **4 kaynağa** çıktı; Fed ve gümüş kayıtlarına not düşüldü; **sıralama tablosu JSON'dan yeniden üretildi**)
_Önceki: 2026-09-06 (Berk Tavsan **yeni kaynak** + Cihat E. Çiçek 6 Eylül girişi işlendi: 4 yeni kayıt, altın 4.800 kaydı 3 kaynağa çıktı)_
_Ondan önceki: 2026-09-04 (4 Eylül NFP günü: 3 yeni kayıt, 1 kayıt genişletildi)_

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
| 1 | Fed Eylül 2026 toplantısında faiz ARTIRMAZ | 35 – 59,4 | **4,0** | (7) | Sellcoin, Emrah Lafçı & Ali Perşembe, Barış Soydan, Onur Duygu, Tunç Şatıroğlu, Berk Dinçtürk, Selçuk Geçer | 2026-08-10 |
| 2 | Altın kısa vade taban/biriktirme bandı (ons $) | 4000 – 4500 | **3,5** | (7) | Sellcoin, Berk Dinçtürk, Emrah Lafçı & Ali Perşembe, Baki Atılal, Cüneyt Paksoy, Tunç Şatıroğlu, Integral FX TV | 2026-08-06 |
| 3 | TCMB gevşeme yönü — politika faizi 40 -> 37, haftalık repoya dönüş | 37 – 40 | **3,0** | (5) | Cüneyt Paksoy, Ferhat Yükseltürk & Uraz Çay, Emrah Lafçı & Ali Perşembe, Barış Soydan, Integral FX TV | 2026-08-13 |
| 4 | Gümüş Ağustos toparlanma bandı (ons $) | 66 – 67 | **3,0** | (4) | Şant Manukyan, Barış Soydan, Turhan Bozkurt, Erkan Öz | 2026-08-17 |
| 5 | Gumus yapisal YUKARI yon (Koc'un negatif okumasinin karsisindaki kamp) | — | **2,5** | (5) | Sellcoin, Tunc Satiroglu, Emrah Lafci & Ali Persembe, Berk Dincturk, Berk Tavsan | 2026-08-10 |
| 6 | BIST100 kritik eşik bölgesi | 14000 – 14500 | **2,5** | (4) | Cüneyt Paksoy, Atilla Yeşilada, Tunç Şatıroğlu, Barış Soydan | 2026-08-13 |
| 7 | ABD kamu borcu 40 trilyon $ eşiğini geçti | 40 – 42 | **2,5** | (4) | Barış Soydan, Bora Özkent, Emrah Altınocağı, Integral FX TV | 2026-08-20 |
| 8 | ABD CPI (11 Eylul haftasi) yonu belirleyecek - 'son kayip parca' | — | **2,5** | (4) | Berk Tavsan, Selcuk Gecer, Baris Soydan, Tunc Satiroglu | 2026-09-04 |
| 9 | Altın uzun vade hedef bandı (ons $) | 5000 – 6500 | **2,0** | (4) | Cüneyt Paksoy, Tunç Şatıroğlu, Turhan Bozkurt, Emrah Lafçı & Ali Perşembe | 2026-08-13 |
| 10 | Altin 4.800 - 5.000 tepki hedefi (4 Eylul) | 4800 – 5000 | **2,0** | (4) | Cüneyt Paksoy, Selçuk Geçer, Berk Tavsan, Turhan Bozkurt | 2026-09-04 |
| 11 | ECB 10 Eylul'de faiz ARTIRIR **YENİ** | — | **2,0** | (3) | Selçuk Geçer, Barış Soydan, Integral FX TV | 2026-09-07 |
| 12 | BTC direnç/tetik seviyesi | 67000 – 67300 | **1,5** | (3) | Sellcoin, Kemal Hiçyılmaz, Emrah Lafçı & Ali Perşembe | 2026-08-10 |
| 13 | USDTRY yıl sonu bandı | 50 – 55 | **1,5** | (3) | Integral FX TV, Cüneyt Paksoy, Turhan Bozkurt | 2026-08-17 |
| 14 | Gram altin 10.000 TL hedefi | 10000 | **1,5** | (3) | Turhan Bozkurt, Cihat E. Çiçek, Selçuk Geçer | 2026-08-17 |
| 15 | Japon yen carry-trade çözülmesi = piyasanın en büyük riski | 4,05 | **1,5** | (3) | Erol Polat / Money Talks, Cihat E. Çiçek, Integral FX TV | 2026-08-18 |
| 16 | BIST yukarı kırılım hedef bandı | 16000 – 17000 | **1,5** | (3) | Emrah Lafçı & Ali Perşembe, Integral FX TV, Cüneyt Paksoy | 2026-08-25 |
| 17 | Fed'in yönü ŞAHİN — Eylül'de/seçim sonrası faiz ARTIRIMI | 35 – 40 | **1,5** | (3) | Integral FX TV, Erkan Öz, Emrah Lafçı & Ali Perşembe | 2026-08-25 |
| 18 | BTC 200 günlük ortalama / alım bölgesi | 69000 – 69350 | **1,5** | (3) | Emrah Lafçı & Ali Perşembe, Erkan Öz, Kripto Teknik | 2026-08-27 |
| 19 | BIST 14.000 = DESTEK (direnc degil) **YENİ** | 14000 | **1,5** | (2) | Integral FX TV, Barış Soydan | 2026-09-07 |
| 20 | MSCI / endeks çıkarma riski (BIST) | 50 | **1,0** | (2) | Atilla Yeşilada, Erol Polat / Money Talks | 2026-08-19 |
| 21 | Gıda enflasyonu yapısal risk | — | **1,0** | (2) | Atilla Yeşilada, Fiba Bank | 2026-08-19 |
| 22 | CLARITY Act Eylül 2026'da gündeme gelir | — | **1,0** | (2) | Berk Dinçtürk, Kemal Hiçyılmaz | 2026-08-20 |
| 23 | US10Y alarm seviyesi | 5 | **1,0** | (2) | Cüneyt Paksoy, Integral FX TV | 2026-08-25 |
| 24 | Türkiye CDS risk primi (baz puan) | 217 – 219 | **1,0** | (2) | Cüneyt Paksoy, Emrah Lafçı (solo) | 2026-08-27 |
| 25 | S&P 500 kritik destek esigi | 7600 – 7670 | **1,0** | (2) | Cüneyt Paksoy, Tunç Şatıroğlu | 2026-09-04 |
| 26 | Brent 100 $ ust sinir / esik | 100 | **1,0** | (2) | Selçuk Geçer, Tunç Şatıroğlu | 2026-09-04 |
| 27 | Altin 4.200 stop/savunma bolgesi (ons $) | 4200 | **1,0** | (2) | Cuneyt Paksoy, Berk Tavsan | 2026-09-04 |
| 28 | BTC 100.000 $ hedefi | 100000 | **1,0** | (2) | Cuneyt Paksoy, Berk Tavsan | 2026-09-04 |
| 29 | TCMB yil sonu politika faizi %35 **YENİ** | 35 | **1,0** | (2) | Integral FX TV, Selçuk Geçer | 2026-09-07 |

---

## KAYIT NOTLARI

> **NUMARA UYARISI (2026-09-07'de güncellendi):** Aşağıdaki not başlıklarındaki
> numaralar **4 Eylül'deki sıralamaya** aittir. Tablo 7 Eylül'de JSON'dan
> **tamamen yeniden üretildi** (29 kayıt), yani numaralar artık **hiçbir kayıt için**
> geçerli değil — **notları KONU BAŞLIĞINA göre eşleştir.** Her kaydın gerekçesi
> ayrıca `magicma/kaynak_konsensus.json`'un `not` alanında tam metin olarak duruyor;
> aşağıdaki markdown notları yalnızca daha uzun anlatım gerektirenler için. 6 Eylül'de 4 yeni kayıt eklenip sıralama
> yeniden hesaplandığı için 7. sıradan sonrası kaydı. **Notları numaraya göre
> değil KONU BAŞLIĞINA göre eşleştir.** 6 Eylül'de eklenen kayıtların notları
> dosyanın sonundaki ayrı bölümdedir.

**1. Fed Eylül 2026 toplantısında faiz ARTIRMAZ** — 35 – 59,4 · ağırlıklı skor 4,0 (7 kaynak)   
Değer aralığı, artırım ihtimalinin **fiyatlanan yüzdesidir**: %35 (Jackson Hole günü) → %36,4 (CPI sonrası) → **%59,4 (CME FedWatch, 4 Eylül NFP sonrası)**.
**4 Eylül'de Selçuk Geçer eklendi** ("Fed artırmaz, indirmez; sabit — Fed sıkılaşması intihar gibi") ve Tunç Şatıroğlu iddiasını yineledi ("CME %59,4 fiyatlıyor ama ben artırım beklemiyorum").
**Kaydın en önemli özelliği:** fiyatlanan ihtimal %35'ten %59,4'e çıkarken **kaynakların görüşü değişmedi** — grup artık piyasaya karşı pozisyonda. 16 Eylül FOMC bunu tek seferde ölçecek. Aynı dosyada TERSİ yönde 3 kaynaklı bir grup da var — bkz. `14_CELISKI_PANELI.md` A5.

**2. Altın kısa vade taban/biriktirme bandı (ons $)** — 4000 – 4500 · ağırlıklı skor 3,5 (7 kaynak)  
Dosyadaki en geniş yakınsama. Band %12,5 geniş olduğu için nokta konsensüsü değil; her kaynak bandın farklı bir kenarını vurguluyor (Atılal 4.000 destek, Paksoy 4.400-4.500 duvar).

**3. TCMB gevşeme yönü — politika faizi 40 -> 37, haftalık repoya dönüş** — 37 – 40 · ağırlıklı skor 3,0 (5 kaynak)  
Dosyadaki tek GERÇEKLEŞMİŞ konsensüs: Integral FX TV 10 Eylül dedi, 25 Ağustos'ta oldu (16 gün erken).

**4. Gümüş Ağustos toparlanma bandı (ons $)** — 66 – 67 · ağırlıklı skor 3,0 (4 kaynak)  
Manukyan 66,0 · Soydan 66,5 · Bozkurt 67,0 · Erkan Öz 66,35 — aralarındaki fark %1,5, tolerans içinde. Koç'un Temmuz'daki 54-62 bandının ÜSTÜNDE (bkz. 14_CELISKI_PANELI.md).

**5. ABD kamu borcu 40 trilyon $ eşiğini geçti** — 40 – 42 · ağırlıklı skor 2,5 (4 kaynak)  
Trilyon $. Dört kaynak aynı olguyu bağımsız aktarıyor; üçü bundan aynı sonucu (para arzı artışı mecburiyeti) çıkarıyor.

**6. BIST100 kritik eşik bölgesi** — 14000 – 14500 · ağırlıklı skor 2,5 (4 kaynak)  
DİKKAT — aynı sayı, ZIT yön: Paksoy 14.000-14.500'ü 'asla kırılmamalı' destek sayarken Yeşilada 14.000'i güçlü DİRENÇ sayıyor. Sayısal örtüşme gerçek, yorum örtüşmesi yok. Bkz. 14_CELISKI_PANELI.md.  
**4 Eylül güncellemesi:** BIST gün içi **13.895** gördü, kapanış **14.057** — Paksoy'un eşiği **gün içi kırıldı, kapanışta tutuldu**. Karne satırı bu yüzden TUTMADI değil, **"İZLENİYOR (ZEDELENDİ)"** olarak işaretlendi. Paksoy aynı gün eşiği **14.100-14.200'e (21/55 günlük) yukarı revize etti** — yani kaynak kendi seviyesini kaydırdı, bu da izlenmesi gereken bir davranış.

**7. Altın uzun vade hedef bandı (ons $)** — 5000 – 6500 · ağırlıklı skor 2,0 (4 kaynak)  
Yalnızca kaynakların KENDİ hedefleri sayıldı. UBS $5.000 ve Citibank $6.000 aktarım olduğu için kaynak sayısına dahil edilmedi (Soydan ve Integral FX TV aktarıyor). Berk Dinçtürk'ün $10.000'i bandın dışında — bkz. çelişki paneli.

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

**19. Altın 4.800 – 5.000 tepki hedefi (4 Eylül)** — 4800 – 5000 · ağırlıklı skor 1,0 (2 kaynak) · **YENİ**
Aynı gün, iki bağımsız video, aynı iki rakam. **Paksoy:** 4.450 pivotun üstünde kalınırsa 4.700-4.800 → 5.000 "minimum tepki". **Selçuk Geçer:** 4.500 tutulursa 4.800 (Citi vb. banka hedefi aktarımı) → 5.000.
Citi hedefi **aktarım** olduğu için üçüncü kaynak sayılmadı (kayıt 7'deki UBS/Citibank kuralıyla aynı ilke).
Kayıt 7'deki **5.000 – 6.500 uzun vade bandından AYRI** tutuldu: bu kısa-orta vadeli bir tepki hedefi, o ise yapısal hedef. İkisi 5.000'de değiyor ama vadeleri farklı, birleştirilirse sahte bir 6 kaynaklı grup üretirdi.

**20. S&P 500 kritik destek eşiği** — 7600 – 7670 · ağırlıklı skor 1,0 (2 kaynak) · **YENİ**
İki **farklı yöntem** aynı eşiği veriyor: Paksoy **21/55 günlük ortalama** (7.670-7.600, "altına inilmedikçe stres yok"), Şatıroğlu **supertrend** (7.600 sağlam, gösterge AL). Yöntem bağımsızlığı bu kaydın değerini artırıyor — kayıt 8'deki (BIST 16-17.000) üç-yöntem kesişimiyle aynı türden.
**Karıştırma uyarısı:** Paksoy'un `onemli_seviyeler.json`'daki **SPX 7.000-7.500 "sert düzeltme pivot bandı"** kaydı bundan AYRI bir senaryodur.

**21. Brent 100 $ üst sınır / eşik** — 100 · ağırlıklı skor 1,0 (2 kaynak) · **YENİ**
Aynı sayı, **farklı gerekçe** — bu yüzden gerçek bir kesişim.
**Selçuk Geçer (temel):** petrol 100 $ üstü kalıcı olursa enflasyon ve faiz kalıcı olur; bu **altın için DÜŞÜŞ sebebidir**.
**Tunç Şatıroğlu (teknik/jeopolitik):** 102 test edildi ve dönüldü; ABD'nin Hürmüz çevresindeki mayın temizliği ve Hark adası vuruşu arz endişesini sınırlıyor, "yerleşemez".
**Atilla Yeşilada'nın 100-110 $ kötü senaryo eşiği aynı sayıyı veriyor ama ZIT yönde** (yukarı kırılım bekliyor) — o yüzden bu gruba **katılmadı**; bkz. `14_CELISKI_PANELI.md`.

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

**2026-09-04 — ağırlıklandırma ilk kez sıralamayı gerçekten değiştirdi.**
Barış Soydan 3. kapanmış iddiasına ulaşıp **%50 nötr'den %100'e** geçti. Soydan
5 kayıtta geçtiği için o beş kaydın skoru birden yükseldi ve **sıralamanın tepesi
değişti:**

| Kayıt | Eski skor | Yeni skor | Sonuç |
|---|---|---|---|
| Fed Eylül'de artırmaz | 3,0 (6 kaynak) | **4,0** (7 kaynak) | 2. → **1.** |
| Altın kısa vade taban bandı | 3,5 (7 kaynak) | 3,5 (değişmedi) | 1. → **2.** |
| TCMB gevşeme yönü | 2,5 | **3,0** | 3. sırada kaldı |
| Gümüş Ağustos bandı | 2,5 | **3,0** | 4. sırada kaldı |
| ABD kamu borcu 40 T$ | 2,0 | **2,5** | 6. → **5.** |
| BIST100 kritik eşik | 2,0 | **2,5** | 7. → **6.** |

Dikkat: 1. sıradaki kaydın yükselişinin **bir kısmı** kaynak sayısının 6'dan 7'ye
çıkmasından (Selçuk Geçer), **bir kısmı** Soydan'ın ağırlığından geliyor. İkisi
ayrıştırılırsa: 7 kaynak × nötr %50 = 3,50 olurdu; Soydan'ın %100'ü onu 4,00'a
taşıdı. **Yani ağırlıklandırmanın net katkısı +0,50.**

**Ama dürüst uyarı hâlâ geçerli:** bugün 24 kaynaktan **yalnızca 2'sinin**
(Şant Manukyan, Barış Soydan) değerlendirilebilir karnesi var ve **ikisi de %100**,
yani birbirlerinden ayrışmıyorlar. 21 kaydın 15'inde skor hâlâ basitçe
`kaynak_sayısı × 0,50`. Formül doğru çalışıyor, **girdi hâlâ yetersiz** — ama
artık tamamen ölü değil. `12_KAYNAK_PERFORMANS.md`'deki "kapatılmayı bekleyen
iddialar" listesi işlendikçe, özellikle **16 Eylül FOMC**'den sonra bu sıralama
gerçekten anlam kazanacak.

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
- **Brent 100 $ (Atilla Yeşilada).** Geçer ve Şatıroğlu ile **aynı sayı ama zıt
  yön**: Yeşilada 100-110 $'ı seçim sonrası kötü senaryonun *eşiği* sayıyor, yani
  aşılmasını bekliyor; diğer ikisi aşılmayacağını söylüyor. Aynı sayıyı zıt yönde
  kullanan kaynaklar konsensüs oluşturmaz (kayıt 6'daki BIST 14.000 dersi).
- **Altın 5.000 (kayıt 19 ile kayıt 7 arasında).** Aynı sayı iki kayıtta da geçiyor
  ama **vadeleri farklı** (kısa-orta vadeli tepki hedefi vs çok yıllık yapısal
  hedef). Birleştirilirse sahte bir 6 kaynaklı grup üretirdi; ayrı tutuldu.
- **S&P 7.600 (Paksoy) ile SPX 7.000-7.500 (yine Paksoy).** Aynı kaynağın iki farklı
  senaryosu — tek kaynak, konsensüs olmaz; ayrıca farklı seviyeler.
- **Eylül'ün "kırılma ayı" olması.** Beş kaynak Eylül'ü işaretliyor ama
  **yönleri zıt** (Şatıroğlu düşüş, Koç yukarı kırılım, Kripto Teknik golden cross).
  Ortak olan tarih, iddia değil — bu yüzden `16_ZAMANLAMA_KARNESI.md`'ye taşındı.


---

## 2026-09-06 OTURUMUNDA EKLENEN KAYITLAR

**Altın 4.800 - 5.000 tepki hedefi — artık 3 kaynak (ağırlıklı skor 1,0 → 1,5)**  
Berk Tavsan (5-6 Eyl) eklendi: **4.800-4.900 hedefi, stop 4.200, R/R ≈ 3**. Diğer
ikisinden farkı, hedefi tek başına değil **tam bir işlem planı** olarak vermesi —
yani yanlışlanabilirliği daha yüksek (stop seviyesi belli).

**Altın 4.200 stop/savunma bölgesi — 4.200 · ağırlıklı skor 1,0 (2 kaynak)** **YENİ**  
Paksoy (55 haftalık ortalama, ikinci savunma hattı) ve Tavsan (işlem planı stopu)
**aynı sayıyı aynı işlevle** kullanıyor: aşağı risk eşiği. Sayı örtüşmesinin yanında
**yön örtüşmesi de var** — 13_KONSENSUS'taki kayıtların çoğunda olmayan bir şey
(krş. kayıt "BIST100 kritik eşik bölgesi", orada aynı sayı zıt rolde).
Not: Tunç Şatıroğlu'nun 19 Ağustos'taki 4.200'ü **yukarı kırılım teyidi** olarak
kullandığı için (zıt işlev) bu kayda **dahil edilmedi** — bilerek atlandı.

**BTC 100.000 $ hedefi — ağırlıklı skor 1,0 (2 kaynak)** **YENİ**  
Paksoy haftalık ortalama senaryosundan, Tavsan 82.500 kırılımından aynı hedefe
varıyor. **Dikkat çeken ayrıntı:** Tavsan'ın tetiği **82.500**, Koç'un **84.000
"yılın pivotu"** eşiğine %1,8 uzaklıkta. İki bağımsız yöntem neredeyse aynı eşiği
işaretliyor; bu bir konsensüs kaydı değil ama **izlenmesi gereken bir kesişim**.

**ABD CPI (11 Eylül haftası) yönü belirleyecek — ağırlıklı skor 2,5 (4 kaynak)** **YENİ**  
Dosyadaki **ilk "olay penceresi" konsensüsü** — sayısal hedef değil, bir verinin
belirleyiciliği üzerine. Tavsan *"son kayıp parça"*, Geçer altın izleme listesinin
5. maddesi, Soydan *"beklentinin altında gelirse altın için olumlu"*, Şatıroğlu
CPI sonrası Fed fiyatlaması. Skoru yüksek çünkü **Barış Soydan'ın %100 isabet
oranı** ortalamayı yukarı çekiyor (4 × 0,625). Ölçümü `16_ZAMANLAMA_KARNESI.md`'de.

**Gümüş yapısal YUKARI yön — ağırlıklı skor 2,5 (5 kaynak)** **YENİ**  
Sayısal band **bilerek verilmedi**: hedefler birbirinden uzak (Lafçı & Perşembe
73-74, Tavsan 80-90, Dinçtürk 3 hane) ve ±%2 toleransı fazlasıyla aşıyor. Ortak
olan tek şey **yön**. Kaydın anlamı sayısal değil yapısal: Berk Tavsan'ın
eklenmesiyle Koç'un **54-62 negatif okumasına karşı kaynak sayısı 4'ten 5'e çıktı**.
Bkz. `14_CELISKI_PANELI.md` B1.


---

## 2026-09-07 OTURUMUNDA EKLENEN KAYITLAR

**ECB 10 Eylül'de faiz ARTIRIR — ağırlıklı skor 2,0 (3 kaynak)** **YENİ**
Selçuk Geçer (4 ve 7 Eylül, *"neredeyse kesin"*, dayanak Euro Bölgesi ÜFE aylık
+%1,6), Barış Soydan (7 Eylül, *"neredeyse kesin, yıl sonuna 2 artırım"*) ve
Integral FX TV / Murat Sağman (7 Eylül, *"ECB + BoE 2'şer artırım"*).
**Bu kaydın değeri, sayısında değil vadesinde:** üç kaynak da tek yönlü bağlandı ve
**10 Eylül'de tek günde ölçülecek**. Dosyadaki en yanlışlanabilir konsensüs kaydı bu.
Skoru 2,0'da kalıyor çünkü üç kaynağın ikisinin isabet oranı henüz ölçülemez (nötr %50);
Soydan'ın %100'ü ortalamayı 66,7'ye çekiyor.
➜ Yan iddia ayrı ölçülmeli: *"yıl sonuna kadar 2 artırım"* (Soydan + Sağman) —
10 Eylül'de değil **31 Aralık'ta** kapanır.

**Gram altın 10.000 TL hedefi — ağırlıklı skor 1,5 (3 kaynak)** **YENİ**
Turhan Bozkurt **17 Ağustos** (öncü, 21 gün önce), Cihat E. Çiçek 6 Eylül,
Selçuk Geçer 7 Eylül. ⚠️ **Vade ayrışması var:** Bozkurt *"yıl sonu"*, Geçer
*"çok yakında"* diyor — aynı sayı, farklı takvim. Bu bir tolerans sorunu değil,
**zamanlama ayrışması**; `16_ZAMANLAMA_KARNESI.md`'de ayrı satır açıldı.
⚠️ **İkinci uyarı — bileşik hedef:** gram altın = ons × kur. Hedef, ons tutmadan
kur tutarak da gerçekleşebilir. Yani bu kayıt **saf bir altın görüşü değil**;
tek başına "üç kaynak altında hemfikir" diye okunmamalı.

**TCMB yıl sonu politika faizi %35 — ağırlıklı skor 1,0 (2 kaynak)** **YENİ**
Murat Sağman **kendi tahmini** olarak veriyor (3 toplantıdan 2'sinde indirim);
Selçuk Geçer ise **Morgan Stanley'in aynı rakamını aktarıyor**.
⚠️ **Bilerek zayıf işaretlendi:** iki kaynak sayılsa da biri aktarım, gerçek
bağımsızlık ~1,5 kaynak düzeyinde. Yine de kaydedildi çünkü mevcut politika faizi
**%37** iken ikisi de **aşağı** yönü aynı sayıyla işaretliyor.

**BIST 14.000 = DESTEK (direnç değil) — ağırlıklı skor 1,5 (2 kaynak)** **YENİ**
Sağman (*"14.000 artık destek, yukarı gitmek isteyen borsa"*) ve Soydan (gün içi
dip tam **14.000**, kapanış 14.151). Kaydın açılma sebebi, ikisinin **hem sayıyı
hem ROLÜ** aynı vermesi — bu dosyanın aradığı çift örtüşme budur.
⚠️ Ama bu **bir konsensüs değil, üç yönlü ayrışmanın bir kanadı:** Atilla
Yeşilada'nın kaydında 14.000 **direnç**, Turhan Bozkurt aynı gün 14.100'ü *"endeks
mühendisliği"* sayıp **13.750 / 13.610 / 13.440** destekleri veriyor.
Bkz. `14_CELISKI_PANELI.md` **A6** ve **A14**.

**Altın 4.800 – 5.000 tepki hedefi — artık 4 kaynak (skor 1,5 → 2,0)**
Turhan Bozkurt eklendi (*"kurum hedefleri 5.000+ korunuyor, yıl sonu 4.700-5.000"*).
Bandının alt ucu diğerlerinden 100 $ aşağıda ama **±%2 toleransı içinde**, bölünmedi.

### Bu oturumda konsensüse ALINMAYANLAR (gerekçeli)

- **Fed Eylül'de sabit** — yeni kaynak gelmedi; Geçer sadece **kendi 4 Eylül
  görüşünü yineledi**. Tekrar, kaynak sayısını artırmaz. Buna karşılık **Sağman
  karşı tarafa yazıldı** (*"1 artırım fiyatlandı"*) — kayıt 1'in notuna düşüldü.
- **Petrol 40 $ (Bessent)** — Geçer **aktarıyor**, Ali Perşembe ise **kendi tezinin
  dayanağı** yapıyor. Aktarım + görüş karışımı olduğu için ayrı konsensüs kaydı
  açılmadı; `magicma/onemli_seviyeler.json`'a **2 kaynaklı** seviye olarak girdi
  ve `14_CELISKI_PANELI.md` **A12**'de çelişki olarak izleniyor.
- **Gümüş 71 $ (Bozkurt)** — 66-67 bandının **dışında** ve aynı gün Soydan **66**
  veriyor. Bu bir tez ayrışması değil **veri hatası**; bandı genişletmek sahte bir
  uzlaşma üretirdi. Kayıt 4 değişmedi, not düşüldü (A13).
- **USDTRY 56 (OVP 2027 ortalaması)** — resmi belge varsayımı, analist tahmini
  değil. Mevcut *"USDTRY yıl sonu bandı"* kaydına **katılmadı** (farklı yıl,
  farklı tür). Seviye kütüphanesine `aktarim_referans` olarak girdi.
- **Oracle bilançosu / AI-borç riski (Soydan)** — tek kaynak, konsensüs olmaz.
  `16_ZAMANLAMA_KARNESI.md`'ye **10 Eylül** penceresi olarak işlendi.
