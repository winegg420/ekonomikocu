# 12 — KAYNAK PERFORMANS SIRALAMASI

_Güncelleme: 2026-09-04_ (4 Eylül NFP günü girişleri işlendi: Paksoy, Soydan, Selçuk Geçer **yeni kaynak**, Tunç Şatıroğlu ×2)

> **Kaynak:** Bu dosya tamamen `11_DIS_KAYNAKLAR.md` içindeki **KARNE** tablolarından
> türetilmiştir. Yeni veri toplanmaz, hiçbir iddia yeniden derecelendirilmez —
> sadece mevcut `TUTTU / TUTMADI / İZLENİYOR / SONUÇSUZ` etiketleri sayılır.
>
> **BU DOSYA NASIL GÜNCELLENİR:**
> 1. `11_DIS_KAYNAKLAR.md`'ye yeni bir KARNE satırı eklendiğinde veya mevcut bir
>    satırın sonucu değiştiğinde bu dosya **yeniden sayılır**.
> 2. Sayım değişirse **`13_KONSENSUS.md` ve `magicma/kaynak_konsensus.json`'daki
>    `agirlikli_skor` alanları da yeniden hesaplanmalıdır** (İş 6 formülü aşağıda).
> 3. Yeni bir kaynak eklendiğinde ayrıca `14_CELISKI_PANELI.md` (çelişki var mı?)
>    ve `16_ZAMANLAMA_KARNESI.md` (tarih penceresi verdi mi?) kontrol edilmeli.

---

## ⚠️ ÖNCE OKU — BU TABLONUN EN ÖNEMLİ BULGUSU

Toplam **206 iddia**nın **189'u (%92) hâlâ İZLENİYOR** durumunda. Kapanmış
(TUTTU + TUTMADI) iddia sayısı yalnızca **16**, ve bunların **tamamı TUTTU** —
dosyada **kapanmış tek bir TUTMADI kaydı yok**.

**2026-09-04 değişimi:** 4 Eylül NFP günü **3 iddia kapandı ve üçü de TUTTU** —
Barış Soydan'ın "bu cuma NFP altın/gümüş için kritik" uyarısı (NFP beklentinin
~4 katı geldi, altın 4.500→4.370), Tunç Şatıroğlu'nun "BTC 79 K tutunamazsa
76.840" eşiği (79 K tuttu, 79,6 K kapanış) ve yine Şatıroğlu'nun 1,057'lik XRP
uzun vade alım çağrısı (fiyat 1,40). Bununla **Barış Soydan 3 kapanmış iddiaya
ulaşıp sıralama tablosuna girdi** — tabloda artık iki satır var.

Bu, kaynakların çok isabetli olduğu anlamına **gelmez**. Anlamı şu: karne sistemi
şu ana kadar iddiaları **kaydediyor ama kapatmıyor**. Kapanmış 16 kaydın çoğu da
tahmin değil **olgu aktarımı** (bir raporun yayınlanması, gerçekleşmiş bir getiri
verisi, bir fiyat farkının gözlenmesi). Yani bugünkü hâliyle bu tablo bir
**güvenilirlik sıralaması değil, sıralamanın neden henüz yapılamadığının kanıtıdır.**

➜ Gerçek sıralama, `11_DIS_KAYNAKLAR.md`'deki İZLENİYOR satırları düzenli olarak
kapatılmaya başlanınca anlam kazanacak. Aşağıda "Kapatılmayı bekleyen iddialar"
bölümünde bunun için somut bir çalışma listesi var.

---

## SIRALAMA (en az 3 kapanmış iddiası olanlar)

İsabet oranı = TUTTU / (TUTTU + TUTMADI). İZLENİYOR ve SONUÇSUZ paydaya girmez.

| Sıra | Kaynak | İsabet Oranı | Tuttu | Tutmadı | İzleniyor | Sonuçsuz | Toplam |
|---|---|---|---|---|---|---|---|
| 1 | Şant Manukyan | %100 | 3 | 0 | 9 | 0 | 12 |
| 1 | Barış Soydan | %100 | 3 | 0 | 15 | 0 | 18 |

**İki satırlık bir sıralama da istatistiksel olarak sıralama değildir** — ikisi de
%100, yani hâlâ hiçbir ayrım üretmiyor. Soydan'ın üç kapanmış kaydının **ikisi
olgu aktarımı** (Tüpraş kâr verisi, carry-trade zirvesi), yalnızca biri
(**NFP sürprizi uyarısı, 1 Eylül'de verildi, 4 Eylül'de gerçekleşti**) gerçek bir
önden tahmindir. Manukyan için de aynı uyarı geçerli:
Manukyan'ın 3 kapanmış kaydının üçü de dosyada açıkça **"olgu aktarımı, tahmin
değil"** diye işaretlenmiş (Beyaz Saray transshipping raporu, Çin–Batı gümüş fiyat
farkı, Basel/Warsh bağlantısı). Yani %100'lük oran **öngörü isabeti değil, doğru
haber aktarımı** ölçüyor. Bu satır, eşiği geçtiği için tabloda; ağırlık verilirken
bu uyarı unutulmamalı.

---

## HENÜZ DEĞERLENDİRİLEMEZ (3'ten az kapanmış iddia)

İstatistiksel olarak anlamsız oldukları için sıralamaya karıştırılmadılar.
"Kapanmış" sütunu = TUTTU + TUTMADI.

| Kaynak | Kapanmış | Tuttu | Tutmadı | İzleniyor | Sonuçsuz | Toplam | Not |
|---|---|---|---|---|---|---|---|
| Sellcoin | 2 | 2 | 0 | 10 | 0 | 12 | Her ikisi de 27 Tem çağrıları (altın 4.000 dibi, gümüş 55$ dibi) |
| Barış Soydan | — | — | — | — | — | — | *(sıralamada)* |
| Erol Polat / Money Talks | 2 | 2 | 0 | 5 | 0 | 7 | TP2 önerisi + AK3/TP2/HVS/GHS'nin BIST100'ü yenmesi |
| Emrah Lafçı (solo) | 1 | 1 | 0 | 7 | 0 | 8 | CDS 219bp — Paksoy'un 217bp'siyle çapraz doğrulandı |
| Ferhat Yükseltürk & Uraz Çay | 1 | 1 | 0 | 4 | 0 | 5 | Tüpraş kâr büyümesi (Soydan verisiyle doğrulandı) |
| Cihat E. Çiçek | 1 | 1 | 0 | 3 | 0 | 4 | Gerçekleşmiş TEFAS getirileri (tahmin değil) |
| Integral FX TV / Erhan Aslanoğlu | 1 | 1 | 0 | 7 | 0 | 8 | TCMB 10 Eylül tahmini — 16 gün ERKEN gerçekleşti |
| Turhan Bozkurt | 0 | 0 | 0 | 4 | 1 | 5 | TCMB 80 ton altın iddiası **DOĞRULANMADI** (yanlışlanmadı da) |
| Tunç Şatıroğlu | 2 | 2 | 0 | 21 | 0 | 23 | 4 Eyl'de ilk iki kaydı kapandı (BTC 79 K + XRP 1,057), ikisi de TUTTU. **Dosyadaki en çok iddialı kaynak** — 1 kapanmış daha gelince sıralamaya girer |
| Berk Dinçtürk | 0 | 0 | 0 | 14 | 0 | 14 | Hedefleri uzun vadeli (2028'e kadar), doğal olarak açık |
| Emrah Lafçı & Ali Perşembe | 0 | 0 | 0 | 14 | 0 | 14 | — |
| Atilla Yeşilada | 0 | 0 | 0 | 11 | 0 | 11 | 4.500 altın çağrısı gerçekleşmedi ama kapatılmadı (aşağıya bak) |
| Şant Manukyan | — | — | — | — | — | — | *(sıralamada)* |
| Cüneyt Paksoy | 0 | 0 | 0 | 18 | 0 | 18 | 4 Eyl'de 9 yeni iddia; hâlâ hiç kapanmamış. Sayı bazında ikinci en iddialı kaynak |
| Bora Özkent | 0 | 0 | 0 | 6 | 0 | 6 | — |
| Emrah Altınocağı | 0 | 0 | 0 | 6 | 0 | 6 | — |
| Kripto Teknik | 0 | 0 | 0 | 5 | 0 | 5 | Tamamı 1 Eylül civarı vadeli — yakında kapanacak |
| Erkan Öz | 0 | 0 | 0 | 5 | 0 | 5 | Dosyaya en son giren kaynak (30 Ağu) |
| Baki Atılal | 0 | 0 | 0 | 4 | 0 | 4 | — |
| Fiba Bank | 0 | 0 | 0 | 4 | 0 | 4 | — |
| Onur Duygu | 0 | 0 | 0 | 4 | 0 | 4 | — |
| Doruk İşmen | 0 | 0 | 0 | 4 | 0 | 4 | Vadesi 5-10 yıl, ölçülemez |
| Kemal Hiçyılmaz | 0 | 0 | 0 | 3 | 0 | 3 | — |
| **Selçuk Geçer** | 0 | 0 | 0 | 6 | 0 | 6 | **YENİ KAYNAK (4 Eyl 2026).** 6 iddianın 5'i Eylül içinde ölçülebilir (ECB 10 Eyl, Fed 16 Eyl, altın 4.500, Brent 100, DXY) — dosyaya en hızlı kapanacak karneyle girdi |
| Prof. Daron Acemoğlu | — | — | — | — | — | 0 | Fiyat/seviye vermediği için karneye hiç alınmadı |

**Toplam: 24 kaynak · 206 iddia · 16 TUTTU · 0 TUTMADI · 189 İZLENİYOR · 1 SONUÇSUZ.**

> _Önceki sayım (2026-08-30): 23 kaynak · 179 iddia · 13 TUTTU · 165 İZLENİYOR._
> 4 Eylül'de eklenen 27 yeni iddia: Paksoy 9 · Tunç Şatıroğlu 8 · Selçuk Geçer 6 · Barış Soydan 4.

---

## KAPATILMAYI BEKLEYEN İDDİALAR (sonraki oturum için iş listesi)

Aşağıdaki İZLENİYOR satırlarının sonucu bugünkü veriyle **ölçülebilir** durumda.
Bilerek kapatılmadılar — bu dosyanın işi saymak, derecelendirmek değil. Bir sonraki
oturumda `11_DIS_KAYNAKLAR.md` üzerinde tek tek karara bağlanmalı:

- **Sellcoin (10 Ağu):** "BTC 67.300 kırılırsa hedef 72.600" — BTC 27 Ağu'da ~80 K.
- **Kemal Hiçyılmaz (20 Ağu):** "BTC 67.000 kırıldı, 80 K hedef" — 80 K görüldü.
- **Atilla Yeşilada (13 Ağu):** "Altın kısa vade $4.500 üstü, sonra $4.000'e çekilme" —
  dosyanın kendi notu 4.500'ün görülmediğini, sonra 4.700'e çıkıldığını söylüyor.
- **Cihat E. Çiçek (15 Ağu):** "Altın 4.400 Ağustos'ta kırılmazsa Ekim'de 4.660" —
  pencere **bugün (31 Ağu) kapanıyor**, 4.400 çoktan aşıldı, koşul düştü.
- **Barış Soydan (22 Ağu):** "Nvidia bilançosu AI rallisinin sağlaması" — bilanço
  geldi, +%7,5.
- **Berk Dinçtürk (20 Ağu):** "Jackson Hole sonrası 1-2 hafta oynaklık, çöküş yok" —
  pencere kapandı.
- **Fiba Bank:** "Petrol 80$'a gelmeden TCMB politika faizi 37'ye inmez" — petrol
  90$ üstündeyken faiz **25 Ağu'da 37'ye indi** (Aslanoğlu kaydı). Bu bir
  **TUTMADI adayı** ve dosyadaki ilk TUTMADI olabilir.
- **Emrah Lafçı (21 Ağu):** "Politika faizi 37'nin ALTINA inmez" — 37'ye indi,
  altına inmedi; hâlâ açık ama izlenmeli.

### 4 Eylül sonrası eklenen iş listesi

- **Selçuk Geçer (4 Eyl):** "ECB 10 Eylül'de artırım neredeyse kesin" — **10 Eylül'de
  kendiliğinden kapanacak**, dosyadaki en yakın vadeli yeni iddia.
- **Barış Soydan (4 Eyl):** "TCMB 10 Eylül ya da Ekim'de indirir" — 10 Eylül'de
  kısmen ölçülebilir hale gelir (indirmezse Ekim'e sarkar, kapanmaz).
- **Fed 16 Eylül:** Selçuk Geçer "sabit", Tunç Şatıroğlu "artırmaz", Paksoy dolaylı.
  Bu tarihte **hem A5 çelişkisi hem üç kaynağın karnesi aynı anda kapanıyor** —
  dosyanın ilk toplu kapanış günü olacak.


---

# EK A — HEDEF BÜYÜKLÜĞÜ AĞIRLIKLI KARNE (İş 9)

_Eklendi: 2026-08-30_

## Ayarlanabilir sabit

```
HEDEF_BUYUKLUGU_ESIK = 5     # yüzde. Bu değerden UZAK hedefler "cesur",
                             # altındakiler "trivial" sayılır.
```

Bu sabiti değiştirmek istersen sadece bu satırı değiştir; aşağıdaki tüm
sınıflandırma ona göre yeniden yapılmalı.

## Yöntem

```
cesaret_skoru        = |hedef - iddia_anındaki_fiyat| / iddia_anındaki_fiyat × 100
ağırlıklı_isabet     = Σ(TUTTU olanların cesaret skoru) / Σ(tüm kapanmışların cesaret skoru)
```

Ham isabet oranının **yerine geçmez**, yanına yazılır.

## ⚠️ SONUÇ: BU METRİK BUGÜN HESAPLANAMIYOR — nedeni ve çözümü

13 kapanmış iddianın **yalnızca 2'sinde** hem hedef hem de iddia anındaki fiyat
repoda mevcut. Kalan 11'i **sayısal hedef içermeyen** iddialar (olgu aktarımı,
gerçekleşmiş getiri verisi, tez doğrulaması).

| # | Kaynak | Kapanmış iddia | Hedef var mı? | O anki fiyat var mı? | Cesaret skoru |
|---|---|---|---|---|---|
| 1 | Sellcoin | Altın 4.000 dibi tamamlandı, **hedef 4.300** | ✅ 4.300 | ✅ ~4.000 (kendi ifadesi) | **%7,5 → CESUR** |
| 2 | Integral FX TV | TCMB haftalık repoya geçer (**politika faizi 40 → 37**) | ✅ 37 | ✅ 40 | **%7,5 → CESUR** *(fiyat değil faiz oranı — ayrı kategori, dikkat)* |
| 3 | Sellcoin | Gümüş **55 $** potansiyel dip, zayıf | ✅ 55 | ❌ 27 Tem gümüş fiyatı repoda yok | ölçülemez |
| 4 | Ferhat Yükseltürk & Uraz Çay | Tüpraş kâr büyümesi güçlü kalır | ❌ sayısal hedef yok | — | ölçülemez |
| 5 | Barış Soydan | Tüpraş kâr büyümesi güçlü | ❌ | — | ölçülemez |
| 6 | Cihat E. Çiçek | 1 yıllık gerçekleşmiş getiri (gümüş %90, altın %77) | ❌ tahmin değil, olmuş veri | — | ölçülemez |
| 7 | Erol Polat | AK3/TP2/HVS/GHS 3 yılda BIST100'ü yendi | ❌ olmuş veri | — | ölçülemez |
| 8 | Erol Polat | TP2 önerisi | ❌ | — | ölçülemez |
| 9 | Emrah Lafçı (solo) | CDS 219 bp | ❌ ölçüm aktarımı | — | ölçülemez |
| 10 | Barış Soydan | Carry trade zirvesi ($65,3 mia) | ❌ olgu | — | ölçülemez |
| 11 | Şant Manukyan | Transshipping raporu Türkiye'yi hedef aldı | ❌ olgu | — | ölçülemez |
| 12 | Şant Manukyan | Çin-Batı gümüş farkı kapanmıyor | ❌ olgu | — | ölçülemez |
| 13 | Şant Manukyan | Basel yumuşaması ↔ Warsh bağlantısı | ❌ olgu | — | ölçülemez |

**Ölçülebilen 2 iddianın ikisi de TUTTU ve ikisi de CESUR:**

```
ağırlıklı_isabet = (7,5 + 7,5) / (7,5 + 7,5) = %100
ham_isabet       = 2 / 2                     = %100
```

| Kaynak | Ham İsabet | Ağırlıklı İsabet (cesaret) |
|---|---|---|
| Sellcoin | %100 (2/2 kapanmış) | %100 — ölçülebilen tek hedefi **cesur** (%7,5) |
| Integral FX TV | %100 (1/1) | %100 — ölçülebilen tek hedefi **cesur** (%7,5) |
| Diğer 21 kaynak | — | **yetersiz veri** (hiçbirinin ölçülebilir hedefi yok) |

**İki oran da %100 çıktığı için metrik bugün hiçbir ayrım üretmiyor.** Bu bir
hesaplama hatası değil, **veri eksikliğidir** ve düzeltmesi somut:

### Bunu ölçülebilir hale getirmenin tek yolu

`04_TWEETLER.jsonl` / `07_ABONE_TWEETLER.jsonl` kayıtlarındaki **`fiyat` alanı
pratikte boş**: 7.314 kaydın 6.678'i `—`, 636'sı `DOĞRULANACAK (web)`, yalnızca
**4 kayıtta** gerçek bir değer var. Aynı boşluk `11_DIS_KAYNAKLAR.md` için de
geçerli — kaynak girişlerine "iddia anındaki fiyat" yazılmıyor.

➜ **Kural önerisi:** `11_DIS_KAYNAKLAR.md`'ye bir hedef içeren giriş eklerken
hedefin yanına **o anki fiyatı da** yaz (çoğu videoda zaten söyleniyor —
Berk Dinçtürk'ün "program anı fiyatları" bloğu bunun iyi örneği). Bu tek alışkanlık,
cesaret ağırlıklı karneyi birkaç hafta içinde hesaplanabilir hale getirir.

---

# EK B — PİYASA REJİMİNE GÖRE PERFORMANS (İş 10)

_Eklendi: 2026-08-30_

## Ayarlanabilir sabitler

```
REJIM_ESIK_YUZDE  = 10     # BTC 30 günde bu yüzdeden fazla net hareket ettiyse "trend"
REJIM_PENCERE_GUN = 30     # bakılan geriye dönük pencere
```

Referans enstrüman **BTCUSDT**. Fiyat kaynağı `99_BOT_ARSIV/kod/magicma_ham.jsonl`
(kayıtlı seri: **17 Haziran – 30 Ağustos 2026, 22 gün**). Her kapanmış iddia,
**verildiği tarihteki** rejime göre etiketlendi.

> Not: seri günlük değil, tarama günlerinden oluşuyor. Bu yüzden "30 gün önce"
> için **en yakın önceki tarama günü** kullanıldı; her satırda hangi iki gün
> karşılaştırıldığı açıkça yazıyor.

## Rejim etiketleri (gerçek hesap)

| Kaynak | Tarih | Kapanmış iddia | Sonuç | Rejim | BTC 30g hareketi |
|---|---|---|---|---|---|
| Sellcoin | 27 Tem | Altın 4.000 dibi → hedef 4.300 | TUTTU | **YATAY** | %+4,8 (23 Haz 62.273 → 27 Tem 65.252) |
| Sellcoin | 27 Tem | Gümüş 55 $ dip, zayıf | TUTTU | **YATAY** | %+4,8 |
| Ferhat Yükseltürk & Uraz Çay | 13 Ağu | Tüpraş kâr büyümesi güçlü | TUTTU | **YATAY** | %+4,8 (13 Tem 62.239 → 10 Ağu 65.247) |
| Cihat E. Çiçek | 14 Ağu | 1 yıllık gerçekleşmiş getiri | TUTTU | **YATAY** | %+4,8 |
| Barış Soydan | 15 Ağu | Tüpraş kâr büyümesi güçlü | TUTTU | **YATAY** | %+4,8 |
| Erol Polat | 16 Ağu | Fonlar 3 yılda BIST100'ü yendi | TUTTU | **YATAY** | %+4,8 |
| Integral FX TV | 19 Ağu | TCMB 10 Eylül'de haftalık repoya geçer | TUTTU | **YATAY** | %−1,5 (20 Tem 64.361 → 17 Ağu 63.379) |
| Şant Manukyan | 20 Ağu | Transshipping raporu | TUTTU | **TREND** | %+12,2 (20 Tem 64.361 → 20 Ağu 72.204) |
| Şant Manukyan | 20 Ağu | Çin-Batı gümüş farkı | TUTTU | **TREND** | %+12,2 |
| Şant Manukyan | 20 Ağu | Basel ↔ Warsh bağlantısı | TUTTU | **TREND** | %+12,2 |
| Emrah Lafçı (solo) | ~27 Ağu | CDS 219 bp | TUTTU | **TREND** | %+19,6 (27 Tem 65.252 → 26 Ağu 78.042) |
| Barış Soydan | 27 Ağu | Carry trade zirvesi | TUTTU | **TREND** | %+19,6 |
| Erol Polat | tarihsiz | TP2 önerisi | TUTTU | **TARİHSİZ** | ölçülemez |

**Dağılım: 7 YATAY · 5 TREND · 1 tarihsiz.**

## Kaynak bazında iki ayrı isabet oranı

| Kaynak | Trend Dönemi İsabet | Yatay Dönem İsabet |
|---|---|---|
| Sellcoin | yetersiz veri (0 kapanmış) | %100 (2/2) |
| Şant Manukyan | %100 (3/3) | yetersiz veri (0 kapanmış) |
| Barış Soydan | %100 (1/1) | %100 (1/1) |
| Erol Polat / Money Talks | yetersiz veri | %100 (1/1) · +1 tarihsiz |
| Emrah Lafçı (solo) | %100 (1/1) | yetersiz veri |
| Integral FX TV | yetersiz veri | %100 (1/1) |
| Ferhat Yükseltürk & Uraz Çay | yetersiz veri | %100 (1/1) |
| Cihat E. Çiçek | yetersiz veri | %100 (1/1) |
| Diğer 15 kaynak | yetersiz veri | yetersiz veri |

**Genel: TREND %100 (5/5) · YATAY %100 (7/7).**

## ⚠️ Bu tablo neden hiçbir şey söylemiyor

Rejim sınıflandırması **çalışıyor** — BTC serisi mevcut, eşik uygulanıyor,
20 Ağustos'ta rejimin YATAY'dan TREND'e geçtiği net görülüyor (%+9,6'dan
%+12,2'ye). Sorun sınıflandırmada değil, **ölçülen şeyde**:

Veri setinde **hiç TUTMADI yok** (bkz. bu dosyanın başındaki uyarı). Payda ne
olursa olsun pay ona eşit; her rejimde isabet %100 çıkıyor. **Rejim ayrımı ancak
ilk TUTMADI kayıtları girdiğinde anlam kazanacak.**

Ayrıca iki yapısal sınırlama:

1. **Fiyat serisi 17 Haziran'da başlıyor.** Daha eski iddialar (Sellcoin'in
   "önceki oturum" kayıtları, Baki Atılal, Tunç Şatıroğlu'nun tarihsiz girişleri)
   rejim etiketi alamıyor.
2. **BTC tek referans.** BIST hissesi (Tüpraş) ya da TCMB faizi hakkındaki bir
   iddiayı BTC'nin rejimiyle etiketlemek kabaca doğru olabilir (küresel risk
   iştahı vekili olarak) ama **doğrudan ilgili değil**. Daha doğrusu, varlık
   sınıfına göre ayrı referans kullanmaktır (BIST için XU100, altın için XAUUSD) —
   `magicma_ham.jsonl` bu serileri zaten tutuyor, ileride yapılabilir.

### Yan bulgu — tarihlenebilir bir gerçek

Rejim hesabı, `16_ZAMANLAMA_KARNESI.md`'deki "Ağustos 3. hafta" bulgusunu
**bağımsız olarak doğruluyor:** BTC'nin 30 günlük net hareketi 19 Ağustos'ta
%−1,5 iken **20 Ağustos'ta %+12,2'ye** sıçrıyor. Yani rejim değişiminin tarihi,
Koç'un aylar önceden verdiği pencerenin tam ortasına düşüyor.
