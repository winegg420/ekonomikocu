# 16 — ZAMANLAMA KARNESİ

_Güncelleme: 2026-09-04_ (4 Eylül NFP günü girişlerinden 7 yeni pencere eklendi)

> **Bu karne fiyat karnesi DEĞİLDİR.** Ölçtüğü şey seviyenin tutup tutmadığı değil,
> **verilen zaman penceresinin** kendisinin isabeti: pencere kapandığında gerçekten
> bir şey oldu mu, yoksa öteleme mi geldi.
>
> **Sonuç etiketleri:**
> - **TUTTU** — pencerede gerçekten belirtilen şey oldu.
> - **TUTMADI** — pencere kapandı, hiçbir şey olmadı, öteleme de yapılmadı.
> - **SONUÇSUZ** — öteleme yapıldı / koşul düştü / yeni pencereye ertelendi.
> - **İZLENİYOR** — pencere henüz kapanmadı.
>
> **Kaynak:** `06_ANALIZ.md` (Koç) + `11_DIS_KAYNAKLAR.md` (tüm dış kaynaklar).
> Yeni veri toplanmadı; tarihler ve sonuçlar bu iki dosyadaki mevcut kayıtlardan.
>
> **BU DOSYA NASIL GÜNCELLENİR:**
> 1. Bir pencerenin kapanış tarihi geçtiğinde satır **İZLENİYOR'dan çıkarılır** ve
>    sonuç yazılır. Bu, tarih geçtiği için otomatik yapılabilecek tek karne işidir.
> 2. Öteleme yapılırsa **eski satır SONUÇSUZ olarak kalır**, yeni pencere için
>    **yeni satır** açılır — üzerine yazılmaz. Ötelemelerin zinciri bu karnenin
>    en değerli verisidir.
> 3. Yeni kaynak eklenirken tarih içeren her iddia buraya da işlenmeli;
>    `12_KAYNAK_PERFORMANS.md`'deki fiyat karnesiyle **karıştırılmaz**, ayrı sayılır.

---

## KAPANMIŞ PENCERELER

| Kaynak | Verilen pencere | Pencere kapanış tarihi | Sonuç |
|---|---|---|---|
| Koç | 22 Haziran – 3 Temmuz "stres penceresi" | 3 Tem 2026 | **TUTTU** — o pencerede BTC dibi ~57-58 K, kendi grafiğiyle işaretli |
| Koç | Temmuz 9-11 karar penceresi (22 May / 3 Haz'da verildi) | 11 Tem 2026 | **SONUÇSUZ** — ötelendi; 10 Tem: *"Neyse Ağustos 3. haftaya kadar gelsinler bakalım..."* |
| Koç | **Ağustos 3. hafta** karar penceresi (Haziran'dan beri, 60 gün hesabı) | ~21-23 Ağu 2026 | **TUTTU** — 17→25 Ağu: BTC +%27,1 · ETH +%32,1 · ALTIN +%5,5 · NASDAQ −%3,4. Kendi teyidi (19 Ağu 23:49): *"Bu sene kripto iki kere tepki verdi. Birisi NİSAN 7'dir. Birisi Ağustos 3. haftadır."* Sadece yön değil **kompozisyon** da tuttu |
| Koç | *"Ağustos 3. haftaya kadar BTC 60 K üstü kalış pozitif"* (7-8 Haz, 2,5 ay önceden) | ~23 Ağu 2026 | **TUTTU** — BTC 80.526 |
| Koç | ALTIN **"27. gün"** penceresi + **4640 robot** (25 Ağu abone tweetinde önceden verildi) | 27 Ağu 2026 | **TUTTU** — 27. gün 4640'tan 70 dolar düştü, dip **4570** (5.7 öğretisi). Ertesi gece 4570 tekrar test edilip sektirildi. Hem tarih hem seviye tuttu |
| Koç | **XAUUSD 4570 "büyük pivot"** (13 Tem 2026 abone tweeti, 1,5 ay önceden) | 27-28 Ağu 2026 | **TUTTU** — üç dokunuş (21, 27, 28 Ağu), her seferinde sektirildi |
| Koç | **SP500 7570 + 200-300 puan robot** (10 Tem 2026 abone tweeti) | Ağu 2026 | **TUTTU** — 7.800'ler görüldü |
| Koç | *"BTC 126 K görse bile bu boğa olmaz, enflasyon farkı olur"* (**2 Haz 2025**, 15 ay önceden) | 29 Ağu 2026 | **TUTTU** — BTC 126 K gördü, Koç: *"boğa geldi mi? Gelmedi…"* |
| Koç | *"Hikayenin **Avrupa'da doğması lazım**, dip gören rakip üzerine pozitif hikaye yazılır"* (4 Mar 2022) | 2026 | **TUTMADI** — Koç'un kendi kabulü (27 Ağu 2026): *"Avrupa bölgesine hikaye yazamadılar"* |
| Integral FX TV (panel) | TCMB **10 Eylül'de** haftalık repoya geçer | 10 Eyl 2026 | **TUTTU** — ama **16 gün ERKEN** gerçekleşti (25 Ağu). Tarih ıskalandı, yön ve olay tuttu |
| Ferhat Yükseltürk | TCMB "Eylül'e doğru" haftalık repoya geçiş | Eyl 2026 | **TUTTU** — 25 Ağu (erken) |
| Barış Soydan | 23-28 Ağu penceresi: Nvidia bilançosu + Jackson Hole belirleyici olacak | 28 Ağu 2026 | **TUTTU** — Nvidia +%7,5 ($225), Jackson Hole konuşması yapıldı |
| Emrah Altınocağı | **19 Ağustos** operasyonu (Beyaz Saray kripto zirvesi + Hazine geri alımı + BTC sıçraması aynı gün) | 19 Ağu 2026 | **TUTTU** — üçü de aynı gün oldu (olgu aktarımı, tahmin değil) |
| Cihat E. Çiçek | *"Altın 4.400 **Ağustos sonuna kadar** kırılmazsa Ekim'de 4.660"* | 31 Ağu 2026 | **SONUÇSUZ — koşul düştü.** Altın 4.400'ü Ağustos içinde yukarı aştı (27 Ağu 4.600-4.700), yani öngörünün ön koşulu ortadan kalktı; Ekim hedefi ölçülemez |

---
| Koç | *"2022 ilk çeyrek ile 2022 haziran dönemi çok stratejik geçecektir"* (**22 Eki 2021**, 5 ay önceden) | 2022 Q1 + Haz 2026 | **TUTTU (ikisi de)** — savaş 2022 ilk çeyrekte çıktı, DXY tam Haziran 2022'de 114,7 ile tepe yaptı |
| Üçüncü taraf (ozdmr_trading) | *"BTC 4 senelik döngünün sonuna yaklaştık, kabaca **7 haftamız kaldı**"* (27 Ağu 2025) | ~15 Eki 2025 | **TUTTU** — BTC zirvesi 8 Ekim 2025'te 126 K |
| Koç | *"Bir sonraki ETH rallisi **4700**'den önce dönmez"* (**19 Mar 2024**, 25,7 B görüntüleme) | 2025 | **TUTTU** — ETH rallisi 4.700 üstünü gördükten sonra döndü |
| Koç | Gümüş gram *"tam baskıda **80 liraya** kadar altı boş"* (12 Mar 2026, fiyat 120,60) | Mar-Ağu 2026 | **KISMEN** — dip 86,81'de durdu; Koç kendisi *"Ben 80 yazdım ama…"* diyor |

## AÇIK PENCERELER (yakından uzağa)

| Kaynak | Verilen pencere | Pencere kapanış tarihi | Sonuç |
|---|---|---|---|
| **Selçuk Geçer** | **ECB 10 Eylül'de faiz artırır** ("neredeyse kesin"); Euro Bölgesi ÜFE aylık +%1,6 dayanağı | **10 Eyl 2026** | İZLENİYOR — **dosyadaki en yakın pencere** |
| **Barış Soydan** | **TCMB 10 Eylül ya da Ekim'de faiz indirir** → mevduat cazibesi azalır | 10 Eyl 2026 → 31 Eki 2026 | İZLENİYOR — 10 Eylül'de kısmen ölçülür; indirmezse Ekim'e sarkar, kapanmaz |
| **Tunç Şatıroğlu + Selçuk Geçer** | **Fed 16 Eylül'de artırmaz** (Geçer: "sabit — ne artırım ne indirim"; Tunç: "CME %59,4 fiyatlıyor, ben beklemiyorum") | **16 Eyl 2026** | İZLENİYOR — piyasa fiyatlamasına **karşı** pozisyon |
| **Barış Soydan** | **Önümüzdeki hafta ABD CPI son noktayı koyar** — beklenti altı gelirse Fed artırım ihtimali düşer, altın için olumlu | ~11 Eyl 2026 | İZLENİYOR |
| **Tunç Şatıroğlu** | **XRP: "önümüzdeki hafta karar haftası"** (günlük AL, haftalıkta 4 pozitif uyumsuzluk) | ~11 Eyl 2026 | İZLENİYOR |
| **Cüneyt Paksoy** | **Eylül'ün ilk 1-2 haftası S&P'nin yönünü belirler** (7.670-7.600 altına inilmedikçe stres yok) | ~14 Eyl 2026 | İZLENİYOR |
| **Tunç Şatıroğlu** | Alternatif senaryo: **Eylül boyu yükseliş, Ekim'de düşüş** (ana senaryo: son bir yukarı → yeni zirve → düşüş) | 31 Eki 2026 | İZLENİYOR — 1 Eyl – 9 Eki penceresiyle **kısmen çelişiyor**, kaynak iki senaryo veriyor |
| **Cüneyt Paksoy** | **TCMB indirimi Kasım/Aralık'ta, 1-2 puan** (Eylül toplantısı bekle-gör) | 31 Ara 2026 | İZLENİYOR — Soydan'ın 10 Eyl/Ekim penceresiyle **çelişiyor**, bkz. `14_CELISKI_PANELI.md` A10 |
| Onur Duygu | Ağustos = "pivot ay" | 31 Ağu 2026 | İZLENİYOR — **yarın kapanıyor** |
| Kripto Teknik | ETH Golden Cross ~29-30 Ağustos | 30 Ağu 2026 | İZLENİYOR — **bugün kapanıyor** |
| Kripto Teknik | BTC Golden Cross **1 Eylül 2026** (200 GO $69.000) | 1 Eyl 2026 | İZLENİYOR |
| Tunç Şatıroğlu | Nasdaq 1 Eylül'e kadar yükselir, **1 Eylül – 9 Ekim düşer**, sonra ara seçime kadar ralli | 9 Eki 2026 | İZLENİYOR |
| Tunç Şatıroğlu | Eylül'de **5-6 haftalık** ciddi düşüş (yeni zirveler sonrası) | ~15 Eki 2026 | İZLENİYOR |
| Berk Dinçtürk | Jackson Hole sonrası **1-2 hafta oynaklık**, çöküş yok | ~11 Eyl 2026 | İZLENİYOR |
| Güvercin kamp (Sellcoin, Soydan, Onur Duygu, Berk, Şatıroğlu, Lafçı&Perşembe) | Fed **Eylül** toplantısında faiz artırmaz | Eylül FOMC | İZLENİYOR |
| Şahin kamp (Aslanoğlu, Erkan Öz, Lafçı&Perşembe) | Eylül'de/seçim sonrası faiz **artırımı** | Eylül FOMC → Kasım 2026 | İZLENİYOR |
| Kemal Hiçyılmaz | **CLARITY Act 15 Eylül** oylaması (Senatör Lummis) | 15 Eyl 2026 | İZLENİYOR |
| Koç | **15 Haziran – 15 Eylül** 90 günlük vade ("dünyadan zaman çalınıyor") | 15 Eyl 2026 | İZLENİYOR |
| Koç | Gümüş gram **Eylül kesişimi = 86 lira** (13 Tem 2026); üst kesişim 106 lira | Eyl 2026 | İZLENİYOR |
| Koç | **Ekim 13-14** — *"ABD'de net TREND haftasıdır. Dünya orada ABD'den artık bir beklenti içine girer"* (28 Ağu 2026) | 13-14 Eki 2026 | İZLENİYOR |
| Berk Dinçtürk | CLARITY Act **Eylül'de** çıkar | 30 Eyl 2026 | İZLENİYOR |
| Berk Dinçtürk | **Trump-Şi zirvesi 24 Eylül**, kademeli mutabakat | 24 Eyl 2026 | İZLENİYOR |
| Koç | **Eylül** = vadeler sıfırlanır, gerçek yön belli olur | 30 Eyl 2026 | İZLENİYOR |
| Turhan Bozkurt | Ons altın **5.161 $** ("1-2 ay içi") | ~17 Eki 2026 | İZLENİYOR |
| Koç (türetme) | Ağustos 3. hafta **+ 60 gün** = Ekim 3. haftası — sonraki iç blok durağı **19 Ekim 2026** | ~19-23 Eki 2026 | İZLENİYOR — `magicma/gunluk_ozet.py` bu tarihi otomatik hesaplıyor |
| Erkan Öz | **ABD ara seçimi 3 Kasım 2026**; seçim sonrası yılbaşına kadar S&P tarihsel olarak pozitif (14 dönemin 12'si) | 31 Ara 2026 | İZLENİYOR |
| Erkan Öz | Seçim **SONRASI** İran'a sert askeri müdahale riski | Kasım 2026 sonrası | İZLENİYOR |
| Integral FX TV / Aslanoğlu | Eylül'de yarım puan indirim ihtimali %50'den az; süreç **Ekim/Aralık'a** sarkabilir | 31 Ara 2026 | İZLENİYOR |
| Integral FX TV / Aslanoğlu | Yıl sonu USDTRY 50-55, BIST 16-17.000 | 31 Ara 2026 | İZLENİYOR |
| Turhan Bozkurt | Yıl sonu ons **5.300-5.750 $**, gram **10.000 TL** | 31 Ara 2026 | İZLENİYOR |
| Baki Atılal | Yıl sonu **4.700 $** potansiyeli (temkinli) | 31 Ara 2026 | İZLENİYOR |
| Onur Duygu | Altın yıl sonuna kadar en fazla ~4.800 (%10-20) | 31 Ara 2026 | İZLENİYOR |
| Uraz Çay | Çip sektörü endeks-üstü performansı 2026 H2, belki 2027'ye kadar | 31 Ara 2026 | İZLENİYOR |
| Koç | Vade takvimi: **15 Eylül → 15 Aralık** (bir sonraki 90 günlük blok) | 15 Ara 2026 | İZLENİYOR |
| Koç | *"84 K ve **8 ay** uyarısı"* (19 May 2026) — altında kalınırsa zaman kaybı | ~19 Oca 2027 | İZLENİYOR |
| Berk Dinçtürk | Freeport-McMoRan **6 ay vadede** $85-90 | ~13 Şub 2027 | İZLENİYOR |
| Emrah Lafçı & Ali Perşembe | Altın **6 ay içinde** $6.500 potansiyeli | ~19 Şub 2027 | İZLENİYOR |
| Cüneyt Paksoy | BIST **yıl sonu + Q1** hedefi 17.000-17.500 | 31 Mar 2027 | İZLENİYOR |
| **Cüneyt Paksoy** | **BIST 17.000 yıl sonu / 2027 1. çeyrek** — 4 Eyl'de yinelendi: *"teknik olarak hâlâ var"* | 31 Mar 2027 | İZLENİYOR — yukarıdaki satırın **4 Eylül'de teyit edilmiş hâli**; kaynak hedefini düşürmedi |
| Barış Soydan (aktarım) | UBS: altın $5.000, **2027 ilk yarısı** | 30 Haz 2027 | İZLENİYOR |
| Atilla Yeşilada | **2027'de iyileşme yok** | 31 Ara 2027 | İZLENİYOR |
| Bora Özkent | ABD tahvil programı **seçimden hemen sonra** bitiyor | Kasım-Aralık 2026 | İZLENİYOR |
| Berk Dinçtürk | Fed bilanço küçültme teması **2027 H2'ye** kayar | 31 Ara 2027 | İZLENİYOR |
| Atilla Yeşilada | Seçim **2028 baharından önce yok** | Nis 2028 | İZLENİYOR |
| Emrah Lafçı | **2028 Nisan'dan önce** seçim yok | Nis 2028 | İZLENİYOR |
| Berk Dinçtürk | Altın **$10.000** — Trump dönemi sonuna kadar / **2028** | 2028 | İZLENİYOR |
| Doruk İşmen | ETH **5-10 yılda** $62.500-125.000 | 2031-2036 | İZLENİYOR |

---

## PENCERESİZ İDDİALAR (bu karneye giremeyenler)

Bunlar tarih vermedikleri için zamanlama karnesine **alınamaz**; fiyat karnesinde
(`12_KAYNAK_PERFORMANS.md`) kalırlar. Kayıt amacı: ileride "bu neden yok?" diye
tekrar aranmasın.

- **Atilla Yeşilada** — *"Altın kısa vade $4.500 üstü, sonra $4.000'e çekilme"*:
  "kısa vade" ölçülebilir bir pencere değil. Dosya notu 4.500'ün görülmediğini
  söylüyor ama **kapanış tarihi tanımsız** olduğu için TUTMADI yazılamaz.
- **Şant Manukyan** — *"35 ülkeye AI ultimatomu gönderilecek **gibi görünüyor**"*:
  ne tarih ne kesinlik var.
- **Şant Manukyan** — *"Gerçek altın rallisi henüz başlamadı, tetik sistemik güven
  çöküşü"*: koşullu, tarihsiz.
- **Cihat E. Çiçek** — altın aylık sezonsallık tablosu (Aralık %89, Haziran en zayıf):
  tekrarlayan istatistik, tekil pencere değil.
- **Berk Dinçtürk** — "Gümüş 3 haneli / altın 5 haneli, Trump dönemi sonuna kadar":
  vadesi $10.000 satırıyla aynı, ayrı satır açılmadı.

---

## İSTATİSTİK

| | Sayı |
|---|---|
| Toplam tarih penceresi | **55** |
| Kapanmış | **9** |
| — TUTTU | **7** |
| — TUTMADI | **0** |
| — SONUÇSUZ | **2** (Koç Temmuz 9-11 ötelendi · Cihat E. Çiçek koşul düştü) |
| Açık (İZLENİYOR) | **46** |
| Penceresiz, ölçülemez | 5 |

> _Önceki sayım (2026-08-30): 46 pencere · 9 kapanmış · 37 açık._
> 4 Eylül'de eklenen 9 pencere: Selçuk Geçer 1 (+1 ortak) · Barış Soydan 2 ·
> Tunç Şatıroğlu 3 (+1 ortak) · Cüneyt Paksoy 3.

### Ne öğreniyoruz

1. **Zamanlama karnesi fiyat karnesinden ÇOK daha hızlı kapanıyor.** Fiyat
   karnesinde 179 iddiadan 13'ü (%7) kapandı; burada 46 pencereden 9'u (%20)
   kapandı — çünkü tarih kendiliğinden geçiyor, fiyat ise eşik bekliyor.
   ➜ **Bir kaynağı erken değerlendirmek istiyorsan tarih verdiği iddialara bak.**

2. **Koç'un tarih sistemi ölçülebilir ve şu ana kadar 3/4 tutmuş.** Tek SONUÇSUZ'u
   (Temmuz 9-11) **kendisi öteledi** ve ötelediği hedef (Ağustos 3. hafta) tuttu.
   Bu, "öteleme = başarısızlık" saymamak gerektiğini gösteriyor — ama zincir
   kırılırsa (Ekim 3. haftası da ötelenirse) sistem sorgulanmalı.

3. **Tarih veren 20 dış kaynak var ama çoğu tek bir uzak tarih veriyor.**
   Sayı bazında en çok pencere açan: **Koç (7)**, Berk Dinçtürk (6),
   Tunç Şatıroğlu (2), Kripto Teknik (2), Turhan Bozkurt (2), Erkan Öz (2).
   Geri kalanların çoğunda tek satır var ve o da "yıl sonu" gibi uzak bir tarih.
   **Bu karnede hiç görünmeyenler:** Fiba Bank, Erol Polat / Money Talks,
   Sellcoin (Fed-Eylül kampı dışında), Emrah Altınocağı (19 Ağustos dışında),
   Şant Manukyan — hiç ölçülebilir tarih vermemişler.

4. **Eylül 2026 bir tıkanma noktası — 4 Eylül'den sonra daha da yoğunlaştı.**
   Yeni eklenen 9 pencerenin **6'sı Eylül içinde** kapanıyor, üstelik ikisi tek
   güne yığılıyor: **10 Eylül'de ECB (Geçer) + TCMB (Soydan/Paksoy çelişkisi)**
   aynı anda ölçülecek, **16 Eylül FOMC** ise hem A5 çelişkisini hem üç kaynağın
   karnesini birden kapatacak. Aşağıdaki eski sayım hâlâ geçerli, üstüne bunlar
   ekleniyor:
   46 pencerenin **10'u** Eylül içinde kapanıyor
   (1 Eyl BTC golden cross · 2 Eyl Koç altın penceresi · 11 Eyl Jackson Hole+2 hafta ·
   Eylül FOMC × 2 kamp · 15 Eyl Clarity Act · 15 Eyl Koç 90 günlük vade ·
   24 Eyl Trump-Şi · 30 Eyl Clarity son tarih · 30 Eyl Koç "gerçek yön").
   ➜ **Eylül sonunda bu dosya tek seferde büyük ölçüde kapanacak.** O tarihte
   `12_KAYNAK_PERFORMANS.md` sıralaması ilk kez gerçekten anlamlı hale gelecek.
