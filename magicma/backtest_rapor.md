# MagicMA Backtest Raporu

_Uretim: 2026-10-03 18:58 TSI · kod: `magicma/backtest.py` · saf simulasyon, gercek hesap/emir YOK._

**SONUC: test setinde, %0.1 gidis-donus maliyet sonrasi, rastgeleyi anlamli asan bir kombinasyon YOK.**

Olcut (hepsi birden): test ort. net getiri > 0 (tum temaslar VE yalniz ilk temaslar), gun-kumeli bootstrap %95 CI alt siniri > 0, rastgele (yon-permutasyon) baz cizgisine karsi p < 0.010 (5 kombo icin Bonferroni; ilk-temas alt kumesinde p < 0.05).

En iyi egitim kombinasyonu (stop %0.2 / TP %3) testte: n=1787, ort. net %-0.047, gun-kumeli %95 CI [-0.103; 0.024], rastgele baza gore p=0.382.

## 1. Veri kapsami

| kategori | karne olayi | simulasyona giren | oran |
|---|---|---|---|
| abd_hisse | 591 | 563 | 95.3% |
| bist | 1147 | 1071 | 93.4% |
| endeks_faiz | 232 | 194 | 83.6% |
| forex_emtia | 604 | 505 | 83.6% |
| gunun_hareketlileri | 2269 | 2148 | 94.7% |
| kripto | 2114 | 2000 | 94.6% |
| **toplam** | 6957 | 6481 | 93.2% |

Acik (durumu belirsiz) kayit: 19; bunlar simulasyona girer (yalniz karne karsilastirmasindan cikarilir).

Elenen olaylar (neden: adet, SESSIZCE ATLANMADI):

- **giris mumu yok**: 183 olay, 65 sembol
  - semboller: AEFES, AGESA, AGHOL, AGIUSDT, AKBNK, ALBRK, ANSGR, ASELS, AUDNZD, AVLUSDT, AXP, BIOEN, BLASTUSDT, BRETTUSDT, CADJPY, CCOLA, CHILLGUYUSDT, COST, CPOOLUSDT, DAPGM, DOHOL, DXY, EGEEN, ELSAUSDT, EREGL, ESCOM, EURCAD, EURCHF, EURGBP, EURJPY, EURUSD, GARAN, GBPCAD, GBPCHF, GBPJPY, GOATUSDT, INDES, LOGO, MAVIAUSDT, MBXUSDT, MERLUSDT, MGROS, MIATK, MOCAUSDT, NDX, NZDJPY, OYAKC, PETKM, SAFEUSDT, SAHOL, SDUSDT, SPX, TAIKOUSDT, TCKRC, UKOIL, US10Y, USDCAD, USDJPY, USDTRY, VESTL, XAUUSD, XPTUSD, XU100, ZEREBROUSDT, ZETAUSDT
- **pencere kesik (48 saat henuz dolmadi)**: 121 olay, 55 sembol
  - semboller: AAVEUSDT, ADP, AGHOL, ALBRK, AMZN, ANSGR, ATOMUSDT, AVAXUSDT, BICOUSDT, BKNG, BLK, BONKUSDT, BTC.D, BTCUSDT, CADJPY, CAT, COST, CRM, CSCO, DIS, DXY, ECILC, EREGL, ETHUSDT, EURCHF, GALAUSDT, GBPCHF, GRAMUSDT, HEMIUSDT, JPM, LINKUSDT, MCHP, MPARK, MSTR, NDX, PETKM, SBUX, SNPS, SPX, SPY, TCELL, TRENJ, TRXUSDT, TSKB, TTKOM, UKOIL, USOIL, VIX, XAGUSD, XAUTRY, XAUUSD, XLMUSDT, XPDUSD, XPTUSD, XRPUSDT
- **veri gelmedi**: 99 olay, 10 sembol
  - semboller: ALTIN, BADGERUSDT, BTC.D, HONEYUSDT, LMTSUSDT, MSTRXUSDT, OTHERS.D, TOTAL, TOTAL2, UFDUSDT
- **giris fiyati mumla uyusmuyor**: 67 olay, 53 sembol
  - semboller: AGHOL, AGIUSDT, API3USDT, APUUSDT, AVAUSDT, AVPGY, B3USDT, BFCUSDT, BIOEN, BJKAS, BLESSUSDT, BOBUSDT, CCOLA, CYSUSDT, DOGINMEUSDT, DYMUSDT, EGEEN, EUPWR, FLRUSDT, FLUIDUSDT, FZLGY, GCOINUSDT, GESAN, GUNDG, HARRYUSDT, HRKET, IHLGM, INFO, IOUSDT, KONYA, LPTUSDT, LSKUSDT, MIATK, ODAS, PATEK, PETKM, PHAUSDT, PROMUSDT, PSGYO, SISE, STARUSDT, SUSDT, TCELL, TORNUSDT, TREEUSDT, TRENJ, VESTL, VIX, VVSUSDT, XVGUSDT, XYMUSDT, ZKPUSDT, ZORAUSDT
- **sembol eslenemedi**: 6 olay, 1 sembol
  - semboller: XAUTRY

Veri kaynagi: kripto = Binance/MEXC/Bybit/Gate 5 dk (karnedeki borsa once denenir, giris fiyatiyla uyum dogrulanir); diger = Yahoo Finance 5 dk. Metaller (XAU/XAG/XPT/XPD) Yahoo'da spot olmadigi icin vadeli kontrat (GC=F, SI=F, PL=F, PA=F) **getiri vekili** olarak kullanildi ve olay basina giris fiyatina olceklendi; XAUTRY eslenmedi.

Giris mumu: giris anini iceren 5 dk mum. Mum baslangici ile giris ani arasi ortalama -13 sn (mum ici gecikme). Sezgisel not: ayni mumun high/low'u girisinden ONCE olan fiyatlari da icerir; bu stopu/TP'yi hafif fazla tetikler. Duyarlilik icin bir sonraki mumdan baslama asagida.

## 2. Varsayimlar ve sinirlar

- Stop/TP giristen yuzde; ayni mumda ikisi birden degerse STOP (muhafazakar). Stop/TP seviyesi gap ile atlanirsa cikis yine seviyeden varsayilir (iyimser). Trailing: mumun high'i stopu ceker, ayni mumun low'u vurabilir (kotumser).
- 48 saat duvar saati; kapali piyasalar (BIST/ABD/FX hafta sonu) icin 48 saat icindeki SON mumun kapanisindan cikilir.
- Getiriler esit buyuklukte (1 birim) islem varsayimiyla toplanir; DD = zamana gore sirali net getirilerin kumulatif toplaminin en buyuk tepeden-dibe dususu (yuzde puan). Islemler zaman bakimindan ust uste binebilir.
- Maliyet = gidis-donus yuzde, her islemden dusulur. Kayma (slippage) ve gap riski maliyete dahil DEGIL; BIST/ABD hisse/FX icin gercek maliyet farkli olabilir.
- Olaylar bagimsiz degil: ayni sembolde 48 saat icinde ardisik temaslar ve ayni gunde piyasa genelindeki hareketler korele. Bu yuzden ilk-temas alt kumesi ve gun-kumeli bootstrap ayrica verildi.

- Egitim: 28 Agu - 18 Eyl (n=4694); test: 19 Eyl - 3 Eki (n=1787). Test setinde ilk-temas alt kumesi n=440; tum setteki ilk-temas orani 24.1%.

## 3. Mevcut kuralin yeniden uretimi

Karnedeki durumlarla (basarili/basarisiz/zaman_asimi; acik kayitlar haric) simulatorun ayni olay icin verdigi sonuc karsilastirildi. Karne stopu girise degil **cizgiye** gore %0,3, taramasi ise ~10 dk'da bir ANLIK fiyatla yapildigi icin uc varyant denendi:

| varyant | olay | ayni durum | ortusme |
|---|---|---|---|
| A: giris-%0,3 stop (kullanici kurali) | 6480 | 5089 | 78.5% |
| B: cizgi-%0,3 stop, mum high/low | 6480 | 5314 | 82.0% |
| C: cizgi-%0,3 stop, 10 dk kapanis ornekleme | 6480 | 6116 | 94.4% |

**A: giris-%0,3 stop (kullanici kurali)**

|  | sim: basarili | sim: basarisiz | sim: zaman_asimi |
|---|---|---|---|
| karne: basarili | 2060 | 814 | 4 |
| karne: basarisiz | 481 | 2945 | 6 |
| karne: zaman_asimi | 21 | 65 | 84 |

**B: cizgi-%0,3 stop, mum high/low**

|  | sim: basarili | sim: basarisiz | sim: zaman_asimi |
|---|---|---|---|
| karne: basarili | 2204 | 669 | 5 |
| karne: basarisiz | 445 | 2981 | 6 |
| karne: zaman_asimi | 26 | 15 | 129 |

**C: cizgi-%0,3 stop, 10 dk kapanis ornekleme**

|  | sim: basarili | sim: basarisiz | sim: zaman_asimi |
|---|---|---|---|
| karne: basarili | 2717 | 153 | 8 |
| karne: basarisiz | 173 | 3252 | 7 |
| karne: zaman_asimi | 13 | 10 | 147 |

Neden %100 degil: (1) karne yalniz ~10 dk'da bir anlik fiyata bakar, simulator her 5 dk mumun high/low'unu gorur: mum ici igne (wick) girisleri/cikislari simulatorda tetikler, karne kacirir; (2) karne stopu cizgiye gore, kullanici kurali girise gore; (3) giris mumu girisin oncesini de icerir; (4) karnede ayni anda iki esik asilirsa hangisinin once sayildigi tarama sirasina bagli; (5) farkli borsa/veri saglayicisi fiyat farklari ve vekil (metal) verisi.

Motor dogrulamasi: vektorel simulator ile bagimsiz mum-mum (naif) simulator 4000 karsilastirmada 4000 kez birebir ayni sonucu verdi (400 rastgele olay x 5 kombo x 2 yon).

## 4. Referans: mevcut kural (stop %0,3 / TP %0,5, 48 saat) — tum kayitlar

| maliyet | kume | n | isabet | ort net % | PF | max DD (yp) |
|---|---|---|---|---|---|---|
| %0 | egitim | 4694 | 39.6% | 0.0152 | 1.08 | 24.8 |
| %0 | test | 1787 | 42.5% | 0.0384 | 1.22 | 7.3 |
| %0 | tum | 6481 | 40.4% | 0.0216 | 1.12 | 24.8 |
| %0 | tum - yalniz ilk temas | 1563 | 40.9% | 0.0237 | 1.14 | 17.3 |
| %0.05 | egitim | 4694 | 39.4% | -0.0348 | 0.83 | 168.9 |
| %0.05 | test | 1787 | 42.5% | -0.0116 | 0.94 | 34.1 |
| %0.05 | tum | 6481 | 40.2% | -0.0284 | 0.86 | 202.8 |
| %0.05 | tum - yalniz ilk temas | 1563 | 40.2% | -0.0263 | 0.87 | 51.5 |
| %0.1 | egitim | 4694 | 39.2% | -0.0848 | 0.65 | 401.3 |
| %0.1 | test | 1787 | 42.3% | -0.0616 | 0.73 | 110.9 |
| %0.1 | tum | 6481 | 40.1% | -0.0784 | 0.67 | 512.2 |
| %0.1 | tum - yalniz ilk temas | 1563 | 40.0% | -0.0763 | 0.67 | 122.3 |
| %0.2 | egitim | 4694 | 39.0% | -0.1848 | 0.39 | 867.5 |
| %0.2 | test | 1787 | 42.1% | -0.1616 | 0.44 | 288.7 |
| %0.2 | tum | 6481 | 39.8% | -0.1784 | 0.40 | 1156.3 |
| %0.2 | tum - yalniz ilk temas | 1563 | 39.6% | -0.1763 | 0.40 | 275.8 |

## 5. Tum izgara — egitim vs test (ort. net getiri %, maliyet %0.1, MagicMA yonu)

**EGITIM** (satir=stop, sutun=TP)

| stop \ TP | %0.3 | %0.5 | %0.75 | %1 | %1.5 | %2 | %3 |
|---|---|---|---|---|---|---|---|
| %0.2 | -0.097 | -0.076 | -0.062 | -0.058 | -0.052 | -0.057 | -0.044 |
| %0.3 | -0.107 | -0.085 | -0.074 | -0.070 | -0.069 | -0.073 | -0.059 |
| %0.5 | -0.121 | -0.101 | -0.089 | -0.087 | -0.085 | -0.094 | -0.076 |
| %0.75 | -0.128 | -0.110 | -0.102 | -0.099 | -0.090 | -0.093 | -0.074 |
| %1 | -0.126 | -0.110 | -0.104 | -0.099 | -0.098 | -0.106 | -0.096 |
| %1.5 | -0.130 | -0.120 | -0.108 | -0.102 | -0.103 | -0.123 | -0.117 |

| mod | ort net % |
|---|---|
| trailing %0.3 | -0.051 |
| trailing %0.5 | -0.093 |
| trailing %1 | -0.119 |

**TEST** (satir=stop, sutun=TP)

| stop \ TP | %0.3 | %0.5 | %0.75 | %1 | %1.5 | %2 | %3 |
|---|---|---|---|---|---|---|---|
| %0.2 | -0.086 | -0.059 | -0.051 | -0.052 | -0.044 | -0.056 | -0.047 |
| %0.3 | -0.093 | -0.062 | -0.054 | -0.060 | -0.056 | -0.061 | -0.060 |
| %0.5 | -0.107 | -0.079 | -0.073 | -0.069 | -0.070 | -0.077 | -0.065 |
| %0.75 | -0.119 | -0.089 | -0.088 | -0.083 | -0.106 | -0.129 | -0.122 |
| %1 | -0.124 | -0.099 | -0.104 | -0.097 | -0.108 | -0.121 | -0.098 |
| %1.5 | -0.120 | -0.105 | -0.118 | -0.104 | -0.113 | -0.119 | -0.104 |

| mod | ort net % |
|---|---|
| trailing %0.3 | -0.048 |
| trailing %0.5 | -0.083 |
| trailing %1 | -0.117 |

%0.1 maliyette ort. net getirisi pozitif olan kombinasyon sayisi: egitimde 0/45, testte 0/45. (Gurultuyle beklenen: yaklasik yarisi.)

## 6. Egitimde secilen en iyi 5 kombinasyon -> testte olcum (secim: egitim ort. net, maliyet %0.1)

| kombo | egitim ort % | test n | test isabet | test ort net % | test PF | test DD | %95 CI (bootstrap) | %95 CI (gun-kumeli) |
|---|---|---|---|---|---|---|---|---|
| stop %0.2 / TP %3 | -0.0437 | 1787 | 9.3% | -0.0468 | 0.83 | 110.4 | [-0.084; -0.008] | [-0.103; 0.024] |
| trailing %0.3 | -0.0509 | 1787 | 32.3% | -0.0483 | 0.71 | 92.8 | [-0.067; -0.029] | [-0.071; -0.023] |
| stop %0.2 / TP %1.5 | -0.0522 | 1787 | 15.8% | -0.0442 | 0.82 | 94.8 | [-0.072; -0.017] | [-0.085; 0.005] |
| stop %0.2 / TP %2 | -0.0567 | 1787 | 12.1% | -0.0560 | 0.79 | 123.9 | [-0.087; -0.024] | [-0.106; 0.006] |
| stop %0.2 / TP %1 | -0.0581 | 1787 | 21.1% | -0.0518 | 0.78 | 100.9 | [-0.074; -0.029] | [-0.084; -0.020] |

Maliyet duyarliligi (test, ort. net %):

| kombo | tum %0 | tum %0.05 | tum %0.1 | tum %0.2 | ilk-temas %0 | ilk-temas %0.05 | ilk-temas %0.1 | ilk-temas %0.2 |
|---|---|---|---|---|---|---|---|---|
| stop %0.2 / TP %3 | 0.0532 | 0.0032 | -0.0468 | -0.1468 | 0.0238 | -0.0262 | -0.0762 | -0.1762 |
| trailing %0.3 | 0.0517 | 0.0017 | -0.0483 | -0.1483 | 0.0961 | 0.0461 | -0.0039 | -0.1039 |
| stop %0.2 / TP %1.5 | 0.0558 | 0.0058 | -0.0442 | -0.1442 | 0.0756 | 0.0256 | -0.0244 | -0.1244 |
| stop %0.2 / TP %2 | 0.0440 | -0.0060 | -0.0560 | -0.1560 | 0.0429 | -0.0071 | -0.0571 | -0.1571 |
| stop %0.2 / TP %1 | 0.0482 | -0.0018 | -0.0518 | -0.1518 | 0.0511 | 0.0011 | -0.0489 | -0.1489 |

Ilk-temas alt kumesi (test): n=440.

## 7. Rastgele baz cizgisi (test, maliyet %0.1, 1000 tekrar)

Ayni giris anlari, ayni stop/TP; yalniz YON rastgele. (a) permutasyon: MagicMA'nin long/short orani korunarak yonler olaylar arasinda karistirilir; (b) yazi-tura: her olay %50 long/short. p = rastgele ortalamanin MagicMA ortalamasina esit/ustte olma orani.

| kombo | MagicMA ort % | perm. ort % | perm. p95 | perm. p | yazi-tura ort % | yazi-tura p | ilk-temas MagicMA % | ilk-temas perm. p |
|---|---|---|---|---|---|---|---|---|
| stop %0.2 / TP %3 | -0.0468 | -0.0515 | -0.0283 | 0.382 | -0.0500 | 0.398 | -0.0762 | 0.755 |
| trailing %0.3 | -0.0483 | -0.0646 | -0.0491 | 0.040 | -0.0640 | 0.049 | -0.0039 | 0.383 |
| stop %0.2 / TP %1.5 | -0.0442 | -0.0544 | -0.0373 | 0.165 | -0.0549 | 0.151 | -0.0244 | 0.095 |
| stop %0.2 / TP %2 | -0.0560 | -0.0625 | -0.0434 | 0.301 | -0.0639 | 0.264 | -0.0571 | 0.365 |
| stop %0.2 / TP %1 | -0.0518 | -0.0617 | -0.0482 | 0.117 | -0.0612 | 0.152 | -0.0489 | 0.204 |

Bonferroni esigi (5 kombo): p < 0.010.

## 8. Duyarlilik: bir sonraki mumdan baslama (giris mumunun gecmis wick'i etkisi)

| kombo | egitim ort net % (maliyet %0,1) | test ort net % (maliyet %0,1) | test n | test maliyet %0 | test maliyet %0.05 | test maliyet %0.1 | test maliyet %0.2 |
|---|---|---|---|---|---|---|---|
| stop %0.3 / TP %0.5 (mevcut kural) | -0.0724 | -0.0522 | 1784 | 0.0478 | -0.0022 | -0.0522 | -0.1522 |
| stop %0.2 / TP %3 | -0.0084 | -0.0004 | 1784 | 0.0996 | 0.0496 | -0.0004 | -0.1004 |
| trailing %0.3 | -0.0206 | -0.0198 | 1784 | 0.0802 | 0.0302 | -0.0198 | -0.1198 |
| stop %0.2 / TP %1.5 | -0.0207 | -0.0074 | 1784 | 0.0926 | 0.0426 | -0.0074 | -0.1074 |
| stop %0.2 / TP %2 | -0.0217 | -0.0108 | 1784 | 0.0892 | 0.0392 | -0.0108 | -0.1108 |
| stop %0.2 / TP %1 | -0.0276 | -0.0164 | 1784 | 0.0836 | 0.0336 | -0.0164 | -0.1164 |

Giris mumunun giristen ONCEki wick'i dahil (bolum 1-7) ile bir sonraki mumdan baslama (bu bolum) gercegin iki ucudur: ilki stop/TP'yi fazla tetikler, ikincisi giris mumunun giristen SONRAki kismini kacirir. Fark buyuk: sonuc varsayima duyarli. Bu bolumde maliyet %0,1'de hicbir kombo pozitif degil.

## 9. Kirilimlar (maliyet %0.1, tum kayitlar)

### Mevcut kural stop %0,3 / TP %0,5

**Kategori**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| gunun_hareketlileri | 2148 | 39.7% | -0.0827 | 0.66 | 679 | -0.0619 |
| kripto | 2000 | 38.2% | -0.0936 | 0.62 | 390 | -0.0779 |
| bist | 1071 | 46.1% | -0.0311 | 0.86 | 259 | -0.0082 |
| abd_hisse | 563 | 40.1% | -0.0798 | 0.67 | 240 | -0.0955 |
| forex_emtia | 505 | 36.6% | -0.0935 | 0.59 | 171 | -0.0716 |
| endeks_faiz | 194 | 38.7% | -0.0907 | 0.62 | 48 | -0.0069 |

**Cizgi**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| Gunluk Ust | 2533 | 40.4% | -0.0765 | 0.68 | 630 | -0.0670 |
| Gunluk Alt | 2323 | 41.1% | -0.0697 | 0.70 | 600 | -0.0512 |
| onemli_seviye/mega | 855 | 38.5% | -0.0889 | 0.63 | 288 | -0.0428 |
| Haftalik -1 | 431 | 35.7% | -0.1128 | 0.55 | 154 | -0.1199 |
| Haftalik -2 | 339 | 39.8% | -0.0810 | 0.66 | 115 | -0.0549 |

**Yon**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| short | 3323 | 40.3% | -0.0759 | 0.68 | 894 | -0.0475 |
| long | 3158 | 39.8% | -0.0810 | 0.66 | 893 | -0.0757 |

**Kaynak turu**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| teknik | 5604 | 40.3% | -0.0771 | 0.68 | 1499 | -0.0652 |
| onemli_seviye | 784 | 39.4% | -0.0837 | 0.65 | 279 | -0.0415 |
| mega_confluence | 71 | 28.2% | -0.1455 | 0.42 | 9 | -0.0856 |
| ? | 22 | 31.8% | 0.0141 | 1.12 | 0 | - |

### Egitim lideri stop %0.2 / TP %3

**Kategori**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| gunun_hareketlileri | 2148 | 6.7% | -0.0855 | 0.69 | 679 | -0.0879 |
| kripto | 2000 | 7.3% | -0.0678 | 0.76 | 390 | -0.1389 |
| bist | 1071 | 14.0% | 0.0859 | 1.33 | 259 | 0.1390 |
| abd_hisse | 563 | 10.5% | -0.0677 | 0.75 | 240 | -0.0897 |
| forex_emtia | 505 | 14.5% | -0.0520 | 0.79 | 171 | 0.0328 |
| endeks_faiz | 194 | 18.0% | 0.0154 | 1.06 | 48 | 0.2120 |

**Cizgi**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| Gunluk Ust | 2533 | 8.3% | -0.0616 | 0.78 | 630 | -0.0982 |
| Gunluk Alt | 2323 | 9.6% | -0.0178 | 0.93 | 600 | 0.0174 |
| onemli_seviye/mega | 855 | 11.9% | -0.0480 | 0.82 | 288 | -0.0115 |
| Haftalik -1 | 431 | 9.3% | -0.0770 | 0.71 | 154 | -0.0739 |
| Haftalik -2 | 339 | 9.4% | -0.0500 | 0.82 | 115 | -0.1518 |

**Yon**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| short | 3323 | 9.7% | -0.0360 | 0.87 | 894 | -0.0510 |
| long | 3158 | 9.0% | -0.0536 | 0.80 | 893 | -0.0426 |

**Kaynak turu**

| grup | n | isabet | ort net % | PF | test n | test ort net % |
|---|---|---|---|---|---|---|
| teknik | 5604 | 9.0% | -0.0440 | 0.84 | 1499 | -0.0536 |
| onemli_seviye | 784 | 11.6% | -0.0459 | 0.82 | 279 | -0.0047 |
| mega_confluence | 71 | 15.5% | -0.0711 | 0.70 | 9 | -0.2233 |
| ? | 22 | 4.5% | -0.0495 | 0.73 | 0 | - |

## 10. Rastgele 20 olayin elle dogrulamasi (mevcut kural: stop %0,3 / TP %0,5)

Her satir bagimsiz mum-mum simulatorle (`naif`) yeniden hesaplandi; getiri = (cikis seviyesi / giris - 1) (short icin ters). Sonuc, vektorel motor ciktisiyla da birebir karsilastirildi.

| sembol | yon | karne giris | giris fiyati | giris mumu | stop | TP | sonuc | tetik mumu | tetik mum H/L | getiri | motorla ayni |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BIOEN | long | 08-31 16:10 | 19.27 | 08-31 16:10 | 19.2122 | 19.3663 | stop | 08-31 16:20 | H=19.27 L=19.15 | -0.300% | evet |
| SISE | long | 09-10 11:00 | 44.48 | 09-10 11:00 | 44.3466 | 44.7024 | stop | 09-10 11:45 | H=44.44 L=44.2 | -0.300% | evet |
| SXTUSDT | short | 09-13 00:30 | 0.00853 | 09-13 00:30 | 0.00855559 | 0.00848735 | tp | 09-13 01:05 | H=0.00849 L=0.00848 | 0.500% | evet |
| ETHUSDT | long | 09-17 16:30 | 2452.86 | 09-17 16:30 | 2445.5 | 2465.12 | stop | 09-17 16:30 | H=2455.67 L=2445.12 | -0.300% | evet |
| SAHOL | long | 09-24 10:50 | 91.1 | 09-24 10:50 | 90.8267 | 91.5555 | stop | 09-24 10:55 | H=91 L=90.75 | -0.300% | evet |
| LAYERUSDT | short | 09-13 14:50 | 0.0702 | 09-13 14:50 | 0.0704106 | 0.069849 | tp | 09-13 16:00 | H=0.0702 L=0.0698 | 0.500% | evet |
| TORNUSDT | long | 09-11 13:20 | 5.986 | 09-11 13:20 | 5.96804 | 6.01593 | stop | 09-11 13:35 | H=5.993 L=5.964 | -0.300% | evet |
| CRM | short | 09-23 16:40 | 238.44 | 09-23 16:40 | 239.155 | 237.248 | tp | 09-23 16:40 | H=238.88 L=237.24 | 0.500% | evet |
| GRTHO | short | 09-11 15:20 | 228.1 | 09-11 15:20 | 228.784 | 226.959 | stop | 09-11 15:25 | H=229.9 L=227.3 | -0.300% | evet |
| FLUIDUSDT | short | 09-04 13:40 | 1.2502 | 09-04 13:40 | 1.25395 | 1.24395 | tp | 09-04 13:40 | H=1.24 L=1.24 | 0.500% | evet |
| UKOIL | long | 09-22 10:20 | 97.36 | 09-22 10:20 | 97.0679 | 97.8468 | tp | 09-22 10:30 | H=101.44 L=97.2 | 0.500% | evet |
| ASELS | short | 09-23 14:20 | 381 | 09-23 14:20 | 382.143 | 379.095 | stop | 09-23 14:35 | H=382.75 L=380.75 | -0.300% | evet |
| FLOKIUSDT | long | 09-03 20:20 | 2.583e-05 | 09-03 20:20 | 2.57525e-05 | 2.59591e-05 | stop | 09-03 20:20 | H=2.582e-05 L=2.573e-05 | -0.300% | evet |
| HBARUSDT | long | 09-15 18:10 | 0.07752 | 09-15 18:10 | 0.0772874 | 0.0779076 | stop | 09-15 18:15 | H=0.07751 L=0.07727 | -0.300% | evet |
| HBARUSDT | long | 09-09 23:30 | 0.07708 | 09-09 23:30 | 0.0768488 | 0.0774654 | stop | 09-10 00:40 | H=0.07692 L=0.07681 | -0.300% | evet |
| AVPGY | long | 09-11 09:40 | 55.6 | 09-11 09:55 | 55.4332 | 55.878 | stop | 09-11 10:00 | H=56.5 L=55.15 | -0.300% | evet |
| ZROUSDT | long | 09-13 22:30 | 1.024 | 09-13 22:30 | 1.02093 | 1.02912 | tp | 09-13 23:55 | H=1.03 L=1.028 | 0.500% | evet |
| XPTUSD | short | 09-21 14:50 | 1809 | 09-21 14:50 | 1814.43 | 1799.95 | stop | 09-21 15:10 | H=1816.29 L=1808.5 | -0.300% | evet |
| XRPUSDT | long | 09-14 11:50 | 1.3849 | 09-14 11:50 | 1.38075 | 1.39182 | tp | 09-14 12:40 | H=1.3936 L=1.388 | 0.500% | evet |
| LAYERUSDT | short | 09-18 19:20 | 0.0723 | 09-18 19:20 | 0.0725169 | 0.0719385 | tp | 09-18 20:00 | H=0.0721 L=0.0719 | 0.500% | evet |

Motorla ayni: 20/20.

## 11. Acik kalan isler / dikkat

- Maliyet ve kayma sembol sinifina gore farkli; tek yuzde ile modellendi.
- Ayni anda acik pozisyon/sermaye sinirlamasi modellenmedi (esit agirlik, ust uste binen islemler).
- 5 dk mumda mum ici sira (once high mi low mu) bilinmez; ayni mumda ikisi de degerse STOP sayildi, bu TP agirlikli kombinasyonlari sistematik olarak kotumser gosterir.
- ~5 haftalik tek rejim (Agu-Eki 2026); farkli piyasa rejimlerinde sonuc degisebilir.
- Karne olaylari bot'un 10 dk'lik taramasinda GORULEN temaslardir (gercek temas ani degil); canli uygulamada ek gecikme olur.
