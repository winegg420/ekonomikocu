# MagicMA Backtest — Stop %2 / TP %2

_Uretim: 2026-10-09 15:00 · kod: `magicma/backtest_2x2.py`(backtest.py'yi import eder, ona dokunmaz) · saf simulasyon, gercek hesap yok._

**Varsayimlar (backtest.py ile ayni):** olay = karnedeki temas (giris fiyati/zamani, yon etiketi: fiyat cizgi ustunde=long, altinda=short); giris, giris anini iceren 5 dk mumdan baslar; stop/TP girisin %2'si; ayni mumda ikisi de degerse STOP once; sonuclanmayan olay pencere sonu kapanisinda kapatilir; maliyet %0,1 gidis-donus; 1R = %2. 7 gunluk pencere ve temas-oncesi sert hareket kirilimi bu turda KAPSAM DISI (veri yok). Metaller (XAU/XAG/XPT/XPD) vadeli kontrat getiri vekili ile simule edildi. Karne temaslari ayni sembolde ust uste binebilir (bagimsiz olay sayisi gorunenden dusuktur). Giris mumunun giristen ONCEKI wick'i simulasyona dahildir (stop/TP'yi hafif fazla tetikler; backtest_rapor.md bir sonraki mumdan baslamanin sonucu cok degistirdigini gosteriyor) — bu raporda duyarlilik testi yok.

## Ozet

- 48 saat: n=6598, vurma 49.4%, net -0.122%/islem, sonuclanan 5655.

## Pencere: 48 saat

Karne temasi 7509; simulasyona giren **6598**. Elenenler: giris mumu yok=429, pencere kesik=290, veri gelmedi=111, giris fiyati mumla uyusmuyor=69, sembol eslenemedi=12.

- Sonuclanan (TP veya stop vurmus): **5655** (85.7%); sonuclanmayan: **943** (14.3%) — pencere sonu kapanisinda cikildi varsayildi.
- TP 2796 (42.4%) + stop 2859 (43.3%) + sonuc yok 943 (14.3%) = 100.0%.
- Vurma orani (TP / sonuclanan): **49.4%** (basabas %50). Ort. R (hepsi, sonuclanmayan kapanisla): **-0.011**; yalniz sonuclananlarda -0.011.
- Beklenen deger: brut -0.022% / islem; maliyet sonrasi (-%0,1) **-0.122%** / islem.
- Ayni mumda hem TP hem stop vuran: **11** olay (hepsi STOP sayildi, muhafazakar); sonuclananlarin 0.2%'i.

**Rastgele yon tabani** (2000 tekrar, ayni girisler, yon yazi-tura): vurma 49.9% (SS 0.7%), ort. net -0.103%. MagicMA: vurma 49.4% / net -0.122% → p(rastgele >= MagicMA): vurma=0.768, net=0.795.

### Yon / urun turu / cizgi turu

| grup | temas | sonuclanan | vurma (TP/sonuclanan) | stop % | sonuc yok % | ort. R | ort. brut % | ort. net % (-0,1) |
|---|---|---|---|---|---|---|---|---|
| yon: long | 3220 | 2747 (85%) | 54.0% | 39.3% | 14.7% | +0.066 | +0.132 | +0.032 |
| yon: short | 3378 | 2908 (86%) | 45.2% | 47.2% | 13.9% | -0.084 | -0.169 | -0.269 |
| urun: abd_hisse | 589 | 367 (62%) | 54.2% | 28.5% | 37.7% | +0.050 | +0.099 | -0.001 |
| urun: bist | 1086 | 848 (78%) | 47.5% | 41.0% | 21.9% | -0.041 | -0.083 | -0.183 |
| urun: endeks_faiz | 199 | 65 (33%) | 50.8% ⚠ | 16.1% | 67.3% | -0.012 | -0.023 | -0.123 |
| urun: forex_emtia | 532 | 264 (50%) | 53.8% | 22.9% | 50.4% | +0.029 | +0.059 | -0.041 |
| urun: kripto | 4192 | 4111 (98%) | 49.1% | 49.9% | 1.9% | -0.017 | -0.034 | -0.134 |
| cizgi: Gunluk Alt | 2348 | 2150 (92%) | 53.4% | 42.6% | 8.4% | +0.064 | +0.129 | +0.029 |
| cizgi: Gunluk Ust | 2556 | 2353 (92%) | 45.9% | 49.8% | 7.9% | -0.074 | -0.147 | -0.247 |
| cizgi: Haftalik -1 | 451 | 312 (69%) | 41.3% | 40.6% | 30.8% | -0.149 | -0.298 | -0.398 |
| cizgi: Haftalik -2 | 352 | 296 (84%) | 49.3% | 42.6% | 15.9% | -0.018 | -0.037 | -0.137 |
| cizgi: onemli_seviye/mega | 891 | 544 (61%) | 53.9% | 28.2% | 38.9% | +0.042 | +0.084 | -0.016 |

(⚠ = sonuclanan < 100: orneklem yetersiz)

### Train / test

| grup | temas | sonuclanan | vurma (TP/sonuclanan) | stop % | sonuc yok % | ort. R | ort. brut % | ort. net % (-0,1) |
|---|---|---|---|---|---|---|---|---|
| train 28 Agu-18 Eyl | 4694 | 4096 (87%) | 48.7% | 44.8% | 12.7% | -0.021 | -0.041 | -0.141 |
| ↳ rastgele yon tabani | 4694 | | 49.9% | | | | | -0.104 |
| test 19 Eyl-bugun | 1904 | 1559 (82%) | 51.4% | 39.8% | 18.1% | +0.013 | +0.025 | -0.075 |
| ↳ rastgele yon tabani | 1904 | | 49.9% | | | | | -0.105 |

### Temastan once 24-72 saatte sert hareket

**Veri yok** — yerel onbellek her temasin yalniz girisinden sonrasini kapsar (ust uste binen pencereler disinda); onceki 72 saat indirilmedi, bu turda kapsam disi.
