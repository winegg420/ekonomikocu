# BIST MagicMA Fiyat Kontrolü — 2026-08-28 (10:17 TSİ, seans açık)

> Seviye kaynağı: `99_BOT_ARSIV/kod/magicma_ham.jsonl`, en yeni tarama **2026-08-26**.
> Canlı fiyat: Yahoo Finance `.IS`, 744/747 sembol çekildi (26 sn).
> Taranan BIST sembolü: **183**. %1 içinde 18 satır, **%0,25 içinde 7 satır**.
> Eşik kuralı: ≤ %0,25 = çizgiye yapışık = işlem adayı. %0,3 ve üzeri "uzak".
> Fiyat çizginin ALTINDA = direnç = short adayı · ÜSTÜNDE = destek = long adayı.

## İşlem adayları (≤ %0,25 — en yakın en üstte)

| # | SEMBOL | Fiyat | Çizgi | Çizgi değeri | Mesafe | Yön |
|---|---|---|---|---|---|---|
| 1 | AKSEN | 83,55 | G-Üst | 83,5264 | %+0,03 | **long adayı** (destek) |
| 2 | GARAN | 132,90 | G-Üst | 132,94 | %-0,03 | **short adayı** (direnç) |
| 3 | YKBNK | 36,84 | G-Alt | 36,8173 | %+0,06 | **long adayı** (destek) |
| 4 | MPARK | 436,75 | G-Üst | 437,054 | %-0,07 | **short adayı** (direnç) |
| 5 | TAVHL | 284,50 | G-Üst | 284,825 | %-0,11 | **short adayı** (direnç) |
| 6 | DOFRB | 138,40 | G-Üst | 138,212 | %+0,14 | **long adayı** (destek) |
| 7 | TSPOR | 1,18 | H-2 | 1,18217 | %-0,18 | **short adayı** (direnç) |

## Uzak (%0,26–%1,00 — işlem adayı değil, izleme listesi)

| SEMBOL | Fiyat | Çizgi | Çizgi değeri | Mesafe | Yön |
|---|---|---|---|---|---|
| SAHOL | 93,65 | G-Üst | 93,3599 | %+0,31 | long tarafı |
| OBASE | 38,60 | G-Alt | 38,4306 | %+0,44 | long tarafı |
| OBASE | 38,60 | G-Üst | 38,4089 | %+0,50 | long tarafı |
| GUBRF | 496,00 | G-Alt | 493,017 | %+0,61 | long tarafı |
| CLEBI | 1.484,00 | H-2 | 1.474,90 | %+0,62 | long tarafı |
| BIOEN | 19,10 | H-1 | 19,2249 | %-0,65 | short tarafı |
| VAKBN | 32,46 | G-Üst | 32,2388 | %+0,69 | long tarafı |
| MPARK | 436,75 | G-Alt | 439,953 | %-0,73 | short tarafı |
| EKGYO | 20,48 | G-Alt | 20,6619 | %-0,88 | short tarafı |
| THYAO | 306,50 | G-Üst | 309,264 | %-0,89 | short tarafı |
| AKBNK | 72,70 | G-Üst | 72,0446 | %+0,91 | long tarafı |

## Sıkışma / iki çizgi arası

- **MPARK 436,75** → G-Üst 437,054 (%-0,07) ile G-Alt 439,953 (%-0,73) **arasında değil,
  ikisinin de altında**. Üst çizgiye yapışık; 437,05 üstü kapanış olmadıkça short tarafı.
  (Not: MPARK, fiyat_kontrol.py'nin Yahoo `.IS` doğrulama referansı — veri güvenilir.)
- **OBASE 38,60** → G-Alt 38,4306 ve G-Üst 38,4089'un **ikisinin de üstünde**; iki desteğin
  üzerinde duruş, ama %0,44'ten uzak — henüz aday değil.

## Seans açılışında ne değişti (09:42 kapalı → 10:17 canlı)

| SEMBOL | 09:42 (dün kapanış) | 10:17 (canlı) | Değişim | Durum |
|---|---|---|---|---|
| AKSEN | 83,40 (%-0,15 short) | 83,55 (%+0,03 long) | +0,15 | **yön değiştirdi** — çizginin altından üstüne geçti |
| GARAN | 133,00 (%+0,04 long) | 132,90 (%-0,03 short) | -0,10 | **yön değiştirdi** — çizginin üstünden altına indi |
| VAKBN | 32,20 (%-0,12 short) | 32,46 (%+0,69 long) | +0,26 | çizgiyi yukarı geçti ama artık uzak |
| GUBRF | 488,00 (%-0,26) | 496,00 (%+0,61) | +8,00 | G-Alt'ı yukarı geçti, uzaklaştı |
| YKBNK | 36,86 | 36,84 | -0,02 | aday olarak kaldı |
| DOFRB | 138,30 | 138,40 | +0,10 | aday olarak kaldı |
| MPARK, TAVHL, TSPOR | — | — | — | **seans açılışıyla listeye yeni girdi** |

## Uyarılar

- Seviyeler **26 Ağustos** taramasından; MagicMA çizgileri sık değişmez ama 2 günlük gecikme var.
- AKSEN ve GARAN çizginin tam üstünde salınıyor — gün içi birkaç kuruşluk hareket yönü
  çeviriyor. Bu ikisinde **kapanış teyidi** beklenmeli, gün içi sinyal güvenilir değil.
- 3 sembolde (tüm evrende) canlı fiyat çekilemedi (744/747).
