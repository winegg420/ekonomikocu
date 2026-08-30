# 12 — KAYNAK PERFORMANS SIRALAMASI

_Güncelleme: 2026-08-30_

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

Toplam **179 iddia**nın **165'i (%92) hâlâ İZLENİYOR** durumunda. Kapanmış
(TUTTU + TUTMADI) iddia sayısı yalnızca **13**, ve bunların **tamamı TUTTU** —
dosyada **kapanmış tek bir TUTMADI kaydı yok**.

Bu, kaynakların çok isabetli olduğu anlamına **gelmez**. Anlamı şu: karne sistemi
şu ana kadar iddiaları **kaydediyor ama kapatmıyor**. Kapanmış 13 kaydın çoğu da
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

**Tek satırlık bir sıralama istatistiksel olarak sıralama değildir.** Ayrıca
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
| Barış Soydan | 2 | 2 | 0 | 12 | 0 | 14 | Tüpraş kâr tezi + carry trade zirvesi (ikincisi anlık veri) |
| Erol Polat / Money Talks | 2 | 2 | 0 | 5 | 0 | 7 | TP2 önerisi + AK3/TP2/HVS/GHS'nin BIST100'ü yenmesi |
| Emrah Lafçı (solo) | 1 | 1 | 0 | 7 | 0 | 8 | CDS 219bp — Paksoy'un 217bp'siyle çapraz doğrulandı |
| Ferhat Yükseltürk & Uraz Çay | 1 | 1 | 0 | 4 | 0 | 5 | Tüpraş kâr büyümesi (Soydan verisiyle doğrulandı) |
| Cihat E. Çiçek | 1 | 1 | 0 | 3 | 0 | 4 | Gerçekleşmiş TEFAS getirileri (tahmin değil) |
| Integral FX TV / Erhan Aslanoğlu | 1 | 1 | 0 | 7 | 0 | 8 | TCMB 10 Eylül tahmini — 16 gün ERKEN gerçekleşti |
| Turhan Bozkurt | 0 | 0 | 0 | 4 | 1 | 5 | TCMB 80 ton altın iddiası **DOĞRULANMADI** (yanlışlanmadı da) |
| Tunç Şatıroğlu | 0 | 0 | 0 | 15 | 0 | 15 | Dosyadaki en çok iddialı ama hiç kapanmamış kaynak |
| Berk Dinçtürk | 0 | 0 | 0 | 14 | 0 | 14 | Hedefleri uzun vadeli (2028'e kadar), doğal olarak açık |
| Emrah Lafçı & Ali Perşembe | 0 | 0 | 0 | 14 | 0 | 14 | — |
| Atilla Yeşilada | 0 | 0 | 0 | 11 | 0 | 11 | 4.500 altın çağrısı gerçekleşmedi ama kapatılmadı (aşağıya bak) |
| Şant Manukyan | — | — | — | — | — | — | *(sıralamada)* |
| Cüneyt Paksoy | 0 | 0 | 0 | 9 | 0 | 9 | — |
| Bora Özkent | 0 | 0 | 0 | 6 | 0 | 6 | — |
| Emrah Altınocağı | 0 | 0 | 0 | 6 | 0 | 6 | — |
| Kripto Teknik | 0 | 0 | 0 | 5 | 0 | 5 | Tamamı 1 Eylül civarı vadeli — yakında kapanacak |
| Erkan Öz | 0 | 0 | 0 | 5 | 0 | 5 | Dosyaya en son giren kaynak (30 Ağu) |
| Baki Atılal | 0 | 0 | 0 | 4 | 0 | 4 | — |
| Fiba Bank | 0 | 0 | 0 | 4 | 0 | 4 | — |
| Onur Duygu | 0 | 0 | 0 | 4 | 0 | 4 | — |
| Doruk İşmen | 0 | 0 | 0 | 4 | 0 | 4 | Vadesi 5-10 yıl, ölçülemez |
| Kemal Hiçyılmaz | 0 | 0 | 0 | 3 | 0 | 3 | — |
| Prof. Daron Acemoğlu | — | — | — | — | — | 0 | Fiyat/seviye vermediği için karneye hiç alınmadı |

**Toplam: 23 kaynak · 179 iddia · 13 TUTTU · 0 TUTMADI · 165 İZLENİYOR · 1 SONUÇSUZ.**

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

