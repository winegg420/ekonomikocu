# 15 — KOÇ'UN KENDİ TUTARLILIK TAKİBİ

_Güncelleme: 2026-08-30_

> **Kapsam:** Bu dosya Koç'u dış kaynaklarla DEĞİL, **kendi geçmiş tweetleriyle**
> karşılaştırır. Kaynak: `04_TWEETLER.jsonl` + `07_ABONE_TWEETLER.jsonl` üzerinde
> aynı ürün/seviye etrafında tarama; sonuçlar `06_ANALIZ.md`'deki mevcut
> değerlendirmelerle karşılaştırılarak doğrulandı.
>
> **ÖLÇÜT — abartmama kuralı:** Buraya yalnızca **aynı sayısal seviye etrafında**
> ve **net** olan durumlar girer. Her ton nüansı çelişki sayılmaz. Bu yüzden
> dosyanın sonunda ayrı bir **"kontrol edildi, tutarlı çıktı"** bölümü var —
> aranıp da çelişki bulunamayan seviyeler orada, çünkü "aradık, yok" bulgusu da
> bulgudur.
>
> **BU DOSYA NASIL GÜNCELLENİR:**
> 1. Yeni tarama sonrası `06_ANALIZ.md`'ye yeni bir Koç seviyesi eklenirken,
>    o seviyenin arşivdeki ESKİ geçişleri taranır; ton değişimi varsa buraya kayıt açılır.
> 2. Bir kayıt "açık geri adım" olarak kapanırsa `06_ANALIZ.md`'deki ilgili karne
>    satırı da güncellenmelidir (iki dosya birbirine referans verir).
> 3. Koç ↔ **dış kaynak** çelişkileri buraya değil `14_CELISKI_PANELI.md`'ye yazılır.

---

## 1. ALTIN 4.000 $ — "baskıladılar" iddiası kendi arşiviyle çelişiyor

- **24 Ağustos 2026, 15:14:** *"Ağustos 3. haftaya kadar #ALTIN tarafını, zorla
  **4000 #dolar altında** baskılıyorlar. #ETH 2000 dolar altında baskılıyorlar,
  #BTC 60 k da baskılıyorlar."*
- **Arşivin gösterdiği:** Altın 4.000'i **3 Ağustos'tan önce** aşmıştı —
  **6 Ağustos 4.265**, **17 Ağustos 4.396**. Yani Ağustos 3. haftaya gelindiğinde
  altın 4.000'in yaklaşık **%10 üstündeydi**.
- **Değerlendirme: AÇIK GERİ ADIM DEĞİL, GERİYE DÖNÜK HATA.** Aynı cümledeki
  ETH (1.732-1.966 bandı) ve BTC (62-65 K) tespitleri arşivle **birebir doğru**;
  yalnızca altın ayağı yanlış. `06_ANALIZ.md` bunu zaten **"KISMEN YANLIŞ"**
  olarak işaretlemiş.
- **Neden önemli:** Koç'un "hepsini aynı anda baskılıyorlar" çerçevesi burada
  çatlıyor — üç varlıktan ikisi baskıdaydı, biri değildi. Çerçeve doğru, kapsam
  fazla geniş kurulmuş.

---

## 2. "AĞUSTOS 3. HAFTA" PENCERESİ — 48 saatte iki farklı okuma

- **17 Ağustos 2026, 14:37:** *"**ZAMAN geçirmeye devam yani.**"*
  → Pencere sonuçsuz/oyalama okuması.
- **19 Ağustos 2026, 16:55:** *"**Panik yok.. Ağustos 3. hafta geldi.** ABD
  #borsalarında vadelerin dolmasına az kaldı."*
  → Pencereyi **kendisi açık ilan ediyor**, henüz bitmedi diyor.
- **19 Ağustos 2026, 23:49:** *"Bu sene kripto iki kere tepki verdi. Birisi
  NİSAN 7'dir. Birisi **Ağustos 3. haftadır**."*
  → Aynı gün içinde pencereyi **gerçekleşmiş** sayıyor.
- **Değerlendirme: SESSİZ TON DEĞİŞİMİ.** İki gün içinde "zaman geçiriyorlar
  (sonuç yok)" → "pencere geldi (henüz açık)" → "tepki verdi (gerçekleşti)".
  Üç ayrı duruş, hiçbirinde önceki söze atıf yok.
- **Nüans — Koç'un lehine olan taraf:** `06_ANALIZ.md` bunu bir çelişki değil
  **kendi düzeltmesi** olarak kaydetti (17 Ağustos'taki söz o an pencerenin
  kapandığı anlamına gelmiyordu; ABD aylık opsiyon vadesi ayın 3. Cuma'sı =
  21 Ağustos, yani 17'sinde pencere gerçekten açıktı). **Sonuç itibarıyla
  çağrı TUTTU** (17→25 Ağu: BTC +%27,1 · ETH +%32,1 · ALTIN +%5,5 · NASDAQ −%3,4).
- **Kayıt gerekçesi:** Çağrının kendisi tuttu, ama **aynı pencere hakkında 48 saat
  içinde üç farklı ton** kullanılması, gerçek zamanlı okumada Koç'un ne dediğinin
  belirsizleştiği anlamına geliyor. Bu, mentor oturumunda "Koç şu an ne diyor?"
  sorusuna cevap verirken **hangi saatteki tweeti aldığın önemli** demektir.

---

## 3. GÜMÜŞ 68 $ — tez kurulup kapatıldı, geri dönüşte yeniden kurulmadı

- **24 Mayıs 2026:** *"#GÜMÜŞ 68 #dolar altı kalmadan ABD'nin eli net
  rahatlayamıyor. Kısır döngüden kurtulamıyor."*
- **31 Mayıs / 3-5 Haziran (defalarca tekrar):** *"ABD'nin gümüşü 68 dolar altına
  almadan da eli rahatlayamıyor... Yukarıda kaldıkça RİSK içeriyor."*
- **8 Haziran 2026:** *"#gümüş **68 dolar altında kaldı. ABD'nin eli rahatladı.**
  64 dolar kırılmadan bu durulur."* → **Tez kapandı, tuttu.**
- **17 Temmuz 2026:** Gümüş **54 $**; trend çizgisi 57 $ ("5.7 öğretisi ve altına
  aldılar"). Aşağı tez devam ediyor.
- **25 Ağustos 2026:** *"**#GÜMÜŞ 68** #GOLDGR 150 DOLAR gördü. Normalde gümüş
  goldgr'nin yarısıdır. **altın fazla götürüyorlar.**"*
- **Değerlendirme: SESSİZ TON DEĞİŞİMİ / KAPATILMAMIŞ TEZ.** Gümüş, üç ay boyunca
  "ABD'nin eli rahatlaması için altına inmesi gereken" seviyeye **geri döndü** —
  ama Koç bunu *"ABD'nin eli yeniden sıkıştı"* diye okumuyor, konuyu **altın/gümüş
  oranına** kaydırıyor. Kendi kurduğu eşik geri alındığında tez yeniden
  değerlendirilmedi.
- **Ölçülecek:** Gümüş 68'in üstünde kalıcı olursa "ABD'nin eli sıkıştı" sonucunun
  Koç tarafından telaffuz edilip edilmediğine bakılmalı. Edilmezse bu, bir
  **asimetrik tez** işaretidir (aşağı kırılım sayılıyor, yukarı kırılım sayılmıyor).

---

## KONTROL EDİLDİ — TUTARLI ÇIKANLAR

Aşağıdaki seviyeler aynı yöntemle tarandı ve **gerçek bir çelişki bulunamadı.**
Bunlar burada, ileride yanlışlıkla yeniden "çelişki" diye açılmasınlar diye duruyor.

### BTC 60 K — 2 yıl 4 ay boyunca kelimesi kelimesine aynı
- **21 Mart 2024, 22:47** ve **11 Temmuz 2026, 21:16** — *aynı metin*:
  *"60 K #BTC yarımcısını zenginle, fakir edecek en büyük resmin pivotudur...
  altında fakirleşirsin, üstünde zengin olursun... Yıllar geçse de değişmeyecektir.
  İsterse 10 yıl geçsin."*
- **8 Ağustos 2026:** *"2026 Ocak ayında #BİTCOİN 60 K bandındaydı, aradan 8 ay
  geçti, hâlâ 60 K... Koskoca 8 ay ne demek? Geçen zamana yazık."*
- **Değerlendirme: TUTARLI.** İkincisi seviyeyi değil **zamanı** eleştiriyor.
  Pivot tezi ile "zaman kaybı" tezi aynı çerçevenin iki yüzü — çelişmiyorlar.

### BTC 84 K ile 60 K'nın ikisine de "pivot" denmesi
- **20 Mayıs 2026:** *"#bitcoin de 84 K kesinlikle ve kesinlikle **yılın pivotudur**.
  Tüm dönemlerin zamanların pivotudur."*
- **11 Temmuz 2026:** 60 K = *"**en büyük resmin** pivotu"*.
- **Değerlendirme: TUTARLI — hiyerarşi farkı.** 84 K "bu yılın", 60 K "en büyük
  resmin" pivotu. Ayrıca `06_ANALIZ.md`, 84 K'nın kaynağını buldu: 22 Kasım 2024'teki
  *"altında 84 USD pivot olduğuna göre BTC'de 84 K'yı önemser"* — yani 84 K,
  gram/ons altındaki 84 USD pivotunun kriptoya kopyalanmış hali. İki farklı ölçek,
  iki farklı türetme.

### ETH 2.570
- Nisan 2025'ten Mayıs 2026'ya kadar taranan tüm geçişlerde aynı: *"2570 aşılmadan
  yürümez"*. **Değerlendirme: TUTARLI**, 13 ay boyunca sabit.

### DOW / XAUUSD 4376
- 30 Mart 2026 (*"#ALTIN kanadını da 4376 dan gazlamışlardı"*) ile 18 Mayıs 2026
  (*"#DOW 43760 dan #XAUUSD yi ise 4376 dan gazladılar"*) aynı ifade.
  **Değerlendirme: TUTARLI.**

---

## ÖZET

| | Sayı |
|---|---|
| Taranan seviye | 8 (60 K · 84 K · 73.500 · 57 K · 4376 · 2570 · 1746 · gümüş 54/57/62/68) |
| Gerçek tutarsızlık | **3** (altın 4.000 · Ağustos 3. hafta tonu · gümüş 68) |
| Bunlardan "açık geri adım" | **0** |
| "Sessiz ton değişimi" | 2 (Ağustos 3. hafta · gümüş 68) |
| "Geriye dönük olgu hatası" | 1 (altın 4.000) |
| Tutarlı çıkan | 5 |

**Genel değerlendirme:** Koç'un sayısal seviyeleri **çok tutarlı** — 60 K tezi
2,5 yıl boyunca kelimesi kelimesine aynı kalmış. Tutarsızlıklar seviyelerde değil,
**geriye dönük anlatımda** (ne zaman neyin baskılandığı) ve **kendi eşiği geri
alındığında tezi güncellememekte** ortaya çıkıyor.
