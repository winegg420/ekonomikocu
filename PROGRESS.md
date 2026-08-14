# PROGRESS — ekonomikocu

Proje hafizasi. Her oturumda ekleme yapilir, uzerine yazilmaz.

## 2026-07-06 — Guncel tarama + push (rate-limit ile kesildi)

**Yapilan:**
- Debug Chrome (CHROME_X.bat, port 9222, @420cryptofarmer) baslatildi, hesap dogrulandi.
- `tara_guvenli.py` ile artimli tarama yapildi. Arsiv 6550 -> 6566 tweet.
- 1 Temmuz 21:41 sonrasi 10 yeni gunluk kayit alindi (2-4 Temmuz). En yeni tweet: 2026-07-04T20:29:44. 4 Temmuz sonrasi tweet yok.
- Yeni medya/grafikler indi (6 klasor).
- GitHub'a pushlandi: commit db51971.

**Kesinti:**
- Tarama 26 Haziran'a inince "Bir sorun olustu / yeniden yukle" (agir rate-limit) sayfasi cikti; kullanici durdurdu.
- Sirec agaci (tara_guvenli -> tara_guncel_yeni -> tweet_tara) taskkill /T /F ile durduruldu. Veri diske incremental yazildigindan kayip yok (JSONL 0 bozuk).
- 26 Haziran ve oncesi zaten arsivde mevcut, bosluk YOK. Guncel aralik tam.

**Not / karar:**
- "Bir sorun olustu" sayfasi = agir rate-limit; tekrar taramadan once ~15 dk tam soguma gerekir.
- Tarama tek giris kurali: sadece `tara_guvenli.py`. python PATH'te yok -> `py -3`.

## 2026-07-08 — MagicMA taramasi + dayaniklilik altyapisi

**Sorun:** `magicma_yakinlik.py --tara` calisirken ~45. sembolde CDP baglantisi
kopunca (socket.send / Connection closed) Playwright ASILI KALIYOR, kendini
oldurmuyor; kullanici PC'ye bakmazsa fark edilmiyordu.

**Cozum (uretime hazir):**
- `magicma_yakinlik.py`: calistirma blogu `if __name__ == "__main__":` altina
  alindi (davranis birebir korunur) -> artik import edilebilir. Yedek: `.bak`.
- Yeni `magicma_tara_dayanikli.py`: kopunca CDP'ye yeniden baglanip ayni
  sembolden devam eder; her cagri zaman asimli (asili kalmaz); bugun taranmis
  sembolleri atlar (resume, ham 'kaynak' alanindan). Bitince rapor .md uretir.
- Scratchpad'de `magicma_supervisor.sh`: koşucu 6 dk ilerleme yazmazsa oldurup
  resume ile yeniden baslatir; rapor uretilene kadar surdurur (maks 25 tur).

**Karar:** Bundan sonra MagicMA taramasi supervisor + dayanikli kosucu ile
yapilir; ham/rapor cikti formati ve kurallar magicma_yakinlik.py'den degismedi.

**Tarama sonucu:** 422 sembol -> 403 basarili. 19 taranamayan analiz edildi:
hicbiri YANLIS KOD DEGIL (hepsi gecerli TV sembolu). Basarisizlik sebebi:
"Dogu Block" MagicMA seviye plotlari (Haftalik/Gunluk) ∅ (bos) donuyor ->
yeterli haftalik/gunluk gecmis yok (yeni token / askidaki BIST / kisa gecmisli).

**Alternatif borsa testi (ampirik, magicma_altkod.py):** 4 sembol icin ayni
varligin uzun gecmisli borsasi MagicMA seviyesi uretiyor -> DUZELTILDI:
- BINANCE:MEGAUSDT -> MEXC:MEGAUSDT
- BINANCE:XAUTUSDT -> BYBIT:XAUTUSDT
- BINANCE:LRCUSDT  -> BYBIT:LRCUSDT
- NYSE:WMT         -> NASDAQ:WMT
kripto.txt otomatik uretildigi icin `kripto_liste_guncelle.py`'ye REMAP tablosu
eklendi (regenerate'te fix korunur). abd_hisse.txt elle guncellendi. 4'u de
tarandi, ham+rapora girdi (bugun toplam 407 sembol, 272 rapora girdi).
- REUSDT->RENDER onerisi REDDEDILDI (farkli varlik, RENDER zaten listede).

**Gercekten veri olmayan 15 (kod dogru, hicbir borsada MagicMA seviyesi yok):**
REUSDT, TONUSDT, UTKUSDT, OPGUSDT, MUBUSDT, CHIPUSDT (yeni/kisa gecmis token);
KOZAA, KOZAL, IPEKE (askidaki BIST-TMSF); GENKM, ATATR, EKDMR, NETCD, BESTE,
SVGYO (yeni/az islemli BIST). Veri olgunlasinca sonraki taramalarda okunacak.

**15 veri-yok sembol listeden CIKARILDI** (kullanici istegi, sonraki taramada
denenmesin): kripto.txt'ten 6 (kripto_liste_guncelle.py'ye MAGICMA_YOK={RE,TON,
UTK,OPG,MUB,CHIP} hariç seti eklendi -> regenerate'te geri gelmez), bist.txt'ten
9. Liste artik 407 sembol (kripto 96, bist 183). GitHub push: commit 7ee4c56.

## 2026-07-08 — Tweet tarama (rate-limit) + botun rate-limit'i kendi farketmesi

**Yapilan:**
- `tara_guvenli.py` artimli tarama: hesap @420cryptofarmer dogrulandi, 6568 -> 6577
  tweet (+9). Yeni: 2 tweet 7 Temmuz (en yeni 2026-07-07T20:09:32) + 7 gecmis bosluk.
- Tarama 24-29 Haziran civarinda "yeniden yukle" (agir rate-limit) sayfasina takildi;
  kullanici ekranda gordu, bot fark etmiyordu -> durduruldu (taskkill, veri kayipsiz).
- Siniflandirma: analiz_devam.py (6577 tweet), paket 00-10 yeniden uretildi, push: ae01683.

**Kok sorun + kalici cozum:**
- Ana scroll dongusu (tweet_tara.py ~3140) rate-limit'i KONTROL ETMIYORDU; sadece
  page_has_x_error ile sessizce kurtarma deneyip donup duruyordu. rate_limit_var()
  zaten "bir sorun olustu / yeniden yukle"yi taniyordu ama dongude kullanilmiyordu.
- Eklendi: `rate_limit_streak` — ilerleme yokken (new_in_batch==0) rate_limit_var True
  ust uste 3 scroll sürerse ">>> RATE-LIMIT DURDU" yazip diske yazarak DURUYOR.
  Artik bot rate-limit'i kendi farkediyor, sessizce churn etmiyor.

**Karar:** Rate-limit'ten sonra ~15 dk soguma gerek.

## 2026-07-10 — Artimli tarama (+21 tweet), rate-limit'te elle durduruldu

**Yapilan:**
- Chrome CDP (port 9222) kapaliydi -> `99_BOT_ARSIV/calistir/CHROME_X.bat` baslatildi,
  hesap @420cryptofarmer dogrulandi (cikis kodu 4 alinmadi).
- `tara_guvenli.py` artimli tarama: 6577 -> 6598 tweet (+21). Bot 19 scroll'da
  2026-07-10T01:47:29'a (bugunun tweetleri dahil) kadar cekti, sonra 20 Haziran
  civarinda rate-limit sayfasina girdi (ekranda 0 tweet, "rate-limit izi 1/3").
- Kullanici istegiyle streak 3'e ulasmadan durduruldu. Son "DISKE YAZILDI: 6600"
  sonrasi yeni kayit gelmedigi icin veri kaybi yok.
- Siniflandirma: analiz_devam.py -> 6598 analiz, 851 izleniyor, 6559 public.
- Paket 00-10 yeniden uretildi (637 grafik, 96.9 MB zip).

**Gozlem:** Bot 3 kez "Takilma -> profil yenileniyor" (01 Tem, 22 Haz, 20 Haz) ve
"Kurtarma (durak #4)" yapti; her seferinde birkac yeni tweet daha yakaladi. Yani
self-heal calisiyor, ama X akisi eskiye inildikce rate-limit'e giriyor.

**Not:** Tarama sirasinda 07-05, 07-06, 07-08 gunleri bos kaldi; 07-02/07-03 tek
tweet. Bunlar gercekten bos olabilir ya da gap olabilir — soguma sonrasi
kontrol edilmeli.

## 2026-07-11 — Guncel tarama + rate-limit kesintisi (bot durmama sorunu)

- Chrome kapaliydi; CHROME_X.bat baslatilarak CDP 9222 acildi, tarama yeniden kosuldu.
- `tara_guvenli.py` artimli tarama: jsonl 6598 -> 6603 satir (+5; log sayaci 6605 tekil goruyor).
  En yeni tweet 2026-07-10T15:36:16 — profil ustunden tarandigi icin bugune ait
  tweet olsaydi yakalanirdi; bugunden son taramaya kadar arsiv TAM.
- Bot scroll 2'de tum yeni tweetleri almisti ama durmayip 120 scroll dongusune
  devam etti, scroll 13'te rate-limit sayfasina ("Bir sorun olustu") girdi.
  Kullanici fark etti, TaskStop ile durduruldu; veri kaybi yok.
- Siniflandirma: analiz_devam.py -> 6603 analiz, 851 izleniyor, 6564 public.
- Paket 00-10 yeniden uretildi (637 grafik, 96.9 MB zip), GitHub'a push edildi
  (commit ed0d80b).

**Kok neden (bot neden kendiliginden durmadi):** tweet_tara.py'daki stop-before
kontrolu `session_oldest`i sadece BATCH'e giren (yani arsivde olmayan YENI)
tweetlerden hesapliyor. Artimli taramada yeni tweetler hep guncel tarihli
oldugundan session_oldest stop-before'un (7 Tem) altina hic inmiyor; eski
tweetler zaten arsivde oldugu icin batch'e girmiyor. Sonuc: bot yakalayacak
yeni tweet kalmayinca durmak yerine 120 scroll'u tuketiyor / rate-limit'e giriyor.
**Onerilen duzeltme:** profil modunda "art arda N scroll 0 yeni tweet + ekrandaki
gorunur en eski tarih <= stop-before" kosulunda temiz cikis eklemek.

## 2026-07-11 — Stop-before bug duzeltmesi (bot artik kendiliginden duruyor)

- **Asil kok neden bulundu:** tweet_tara.py `--stop-before "7 Tem"` degerine
  " 12:00 2026" ekleyip parse ediyordu; try_parse_date "12"yi YIL saniyor ve
  stop_before = MS 12 (0012-07-07) oluyordu. Hicbir tweet bundan eski
  olamayacagi icin durma kosulu hic tetiklenmiyordu.
- Duzeltme 1 (tweet_tara.py): stop-before once ISO (YYYY-MM-DD) denenir,
  olmazsa guncel yil eklenerek parse edilir; yil < 2000 cikarsa guncel yila
  cekilir (sacma-yil korumasi).
- Duzeltme 2 (tweet_tara.py): durma kosulu guclendirildi — ekranda hedeften
  eski tweet gorulse bile yeni tweet gelmeye devam ediyorsa durmaz (usttteki
  eski tarihli abone/karisik tweetler erken durdurmasin); art arda 2 scroll
  0 yeni + hedef gecildi = temiz cikis. Hedefin 7+ gun gerisine inildiyse
  aninda durur (derin tarama guvenligi).
- Duzeltme 3 (tara_guncel_yeni.py): stop-before artik ISO (YYYY-MM-DD) formatinda
  gecirilir; ekran cikti etiketi TR kalir.
- Test: ISO, "7 Tem", "11 Haz", "7 Tem 12:00", "1 Ara 2025" girdilerinin tumu
  dogru yila parse ediliyor; py_compile temiz. Diger eski cagiranlar
  (tara_tam, devam_gecmis, tamamla_* vb.) yeni parse ile uyumlu.

## 2026-07-13 — Guncel tarama + pinned tweet stall duzeltmesi

### Yapilan
- 10 Tem 15:36'dan bugune guncel tarama. Arsiv 6603 -> 6636 tweet.
- Yeni tweetler: 11 Tem (17 adet) + 12 Tem (16 adet).

### Bulunan hata (kritik): pinned tweet taramayi erken durduruyordu
- `tweet_tara.py` stop-before mantiginda `batch_oldest`, ekrandaki EN ESKI
  tweeti baz aliyordu. Profilin en ustundeki sabitlenmis (pinned) 2019 tarihli
  tweet ilk viewport'a dustugu icin `hard_past` (hedeften 7+ gun geride)
  aninda tetikleniyor ve tarama 1. scroll'da, 5 yeni tweet alip 21 tweeti
  ATLAYARAK duruyordu. Sessiz veri kaybi — log "BITTI" diyordu.
- Duzeltme: bir batch icindeki tweetler kronolojik olarak birbirine yakin
  oldugu icin, batch'in en yenisinden 90 GUNDEN fazla eski olan aykiri
  kayitlar (pinned) durma hesabinin disinda birakildi. Ayrica `hard_past`
  yalnizca `new_in_batch == 0` iken gecerli — yeni tweet akiyorsa durma.

### Cikarim / dikkat
- **Ayni anda iki tarama calistirma.** Duzeltmeyi test ederken onceki tarama
  hala calisiyordu; iki surec ayni Chrome sekmesini ve ayni JSONL'i kullanip
  birbirini bozdu ("ekranda 0 tweet", sayfa surekli reset, rate-limit gorunumu).
  Tek surec kalinca scroll normale dondu ve +18 tweet geldi.
- Scroll sirasinda birkac tweet yine atlanabiliyor (X sanallastirmasi).
  Bu 9 tweet `gap_ekle.py` ile ID vererek status sayfasindan tek tek cekildi.
- Tarama sonrasi bosluk dogrulamasi sart: profili ayrica gezip ID'leri arsivle
  karsilastirmadan "bitti" deme. Log "+N yeni" dese bile atlama olabilir.

### Sonuc
- Bosluk dogrulamasi: 9 Tem sonrasi profildeki 32 tweetin tamami arsivde (EKSIK 0).
- Paket 00-10 uretildi, GitHub'a push edildi (6d833c6).

## 2026-07-13 — MagicMA taramasi (407/407 tam)

**Yapilan:**
- CDP 9222 kapaliydi -> CHROME_X.bat ile debug Chrome acildi; TradingView grafik
  sekmesi CDP /json/new ile acildi (kayitli duzen + "Dogu Block" indikatoru
  yuklendi), tek sembol --json okumasiyla dogrulandi.
- magicma_tara_dayanikli.py arka planda kosuldu: 407 sembol okundu, 0 okunamadi
  (baglanti kopmasi olmadi). Rapor: magicma/magicma_rapor_2026-07-13.md
  (290 sembol rapora girdi, |mesafe| <= %15).
- Cizgiye yapisik (<= %0,25) 22 satir / 18 sembol; en yakinlar BIOEN (%0,00),
  TURSG (%0,02), AUDNZD (%0,02), UUSDT (%0,02).

**Not:** Ham jsonl'de listeden cikarilan 5 eski sembol (ETHBTC, IMXUSDT, ENSUSDT,
CAKEUSDT, TONUSDT — Haziran kayitlari) duruyor; yapisik listeye girmediler. Aday
listesi yalnizca bugunku (en yuksek ts) kayitlardan uretildi.

## 2026-07-15 - Guncel tarama + full paket + push

**Yapilan:**
- CHROME_X.bat kapaliydi (exit 4); Claude baslatip CDP dogruladi, tarama tekrar basladi.
- tara_guvenli.py: +14 yeni tweet (toplam 6650). En yeni kayit: 2026-07-15T00:24:53. Analiz bekleyen: 0.
- 10 inatci alinti "metin kesik" kaldi (birbirini alintilayan eski tweetler, 2'sinin ana tweeti yok); 6 tur denendi, eksik isaretlendi. Gerekirse ALINTI_TAMAMLA.bat.
- claude_paket_olustur.py + kapsam_durum.py: paket 00-10 guncel, 2026 kapsami %100.
- github_guncelle.py: commit cd0e41a pushlandi.

**Not:** Ana tarama ~3 dk surdu; uzun gorunmesinin sebebi alinti tamamlama turlariydi (5-6 tur, sinirli dongu, mudahale gerekmedi).

## 2026-07-17 — Guncel tarama + paket + push (tam akis, sorunsuz)

**Yapilan:**
- Debug Chrome kapaliydi (exit 4); CHROME_X.bat baslatildi, port 9222 dogrulandi, tarama tekrarlandi.
- `tara_guvenli.py` tam akis: arsiv 6650 -> 6678 tweet (+28), +1 alinti (121), en yeni kayit 2026-07-16T20:12:30.
- Siniflandirma otomatik tamamlandi (analyzed olmayan: 0). Paket (00-10) uretildi, medya indi (8 yeni grafik).
- GitHub push: commit 5791c61 (35 dosya).

**Not:**
- 10 alinti metni hala kesik/eksik (bazilari birbirini alintiliyor, max tur doldu). Gerekirse ALINTI_TAMAMLA.bat ile tekrar denenebilir; veri kaybi yok, sadece alinti metinleri kisaltilmis.
- GitHub uyarisi: 05_GRAFIKLER.zip 98.85 MB (>50 MB onerilen). Simdilik push kabul ediliyor; buyumeye devam ederse LFS dusunulmeli.

## 2026-07-17 — Rate-limit koken duzeltmesi (JSON on-cikarim + rastgele bekleme + navigasyon tavani)

**Kok neden:** Alinti/flood asamasi (crawl_quote/crawl_thread) X rate-limit duvarina carpiyordu.
1. `tara_api.parse_tweet()` alintinin TAM icerigini (metin+medya+tarih) JSON'dan zaten alabilirken sadece quoted_id kaydedip birakiyor; sonra crawl_quote ayni bilgi icin AYRI sayfa aciyor (gereksiz cift is).
2. finish_quotes_loop/flush_quotes onlarca navigasyonu sabit 2.5-3.5sn araliklarla art arda yapiyor (rastgelesiz, bot pateni) -> bot tespiti/rate-limit.

**Yapilan degisiklikler:**
- **ADIM 1 — tara_api.py:** `parse_tweet()` artik liste donuyor; `quoted_status_result` bulununca nested result uzerinde kendini rekursif cagirip alintiyi TAM ikinci kayit olarak uretiyor (isQuote=True, quotedBy=parent, json_full). `main()` bu alinti kayitlarini (parent Koc tweet kaydedildiyse) jsonl'e yaziyor. Cogu alinti crawl_quote hic calismadan tamamlaniyor.
- **ADIM 2 — alinti_common.py:** `row_quote_needs_visit()` jsonFull+tam metin varsa sayfa ziyaretini atliyor. tweet_tara.py `finish_threads_loop`: flood parcalari JSON'dan toplanmissa (kok + >=2 parca, metin dolu) crawl_thread navigasyonunu atliyor.
- **ADIM 3 — tweet_tara.py:** crawl_quote/crawl_thread sabit `wait_for_timeout(2500/3500/800)` -> `_insan_bekle()` ile 3-8sn rastgele. `finish_quotes_loop` yeni `nav_cap=20` parametresi: oturum basina alinti navigasyon tavani; tavana ulasilinca kalanlar erken "erisilemedi" isaretlenmeden sonraki oturuma birakiliyor (ziyaret edilmeyen alintiyi yanlis isaretleme korumasi eklendi).
- **Yayginlik kontrolu:** alinti_flood_tara.py'deki navigasyon-sonrasi sabit beklemeler de `_insan_bekle()` ile rastgeleye cevrildi. abone_tamamla.py incelendi — crawl navigasyon dongusu yok (sadece profil timeline'da kilitli metin dolduruyor), sabit beklemeleri kurtarma/idle backoff'u; degisiklik gerekmedi.

**Dogrulama:** 4 dosya py_compile OK. parse_tweet birim testi: alinti icin 2 kayit (main + quoted, tam metin, quoted_by dolu) uretiyor. row_quote_needs_visit: jsonFull tam satir -> False (ziyaret yok), bos stub -> True.

**Test edilmesi gereken:** Sonraki `tara_guvenli.py` tam akisinda alinti asamasi cok daha az sayfa aciyor mu (log'da "JSON'dan on-cikan alinti: N" ve "navigasyon k/20"); veri kaybi olmadan alinti metinleri doluyor mu.

## 2026-07-17 — Rate-limit duzeltmesi sonrasi ilk tam tarama (dogrulama)

**Yapilan:** `tara_guvenli.py` tam akis (Chrome debug 9222 acildi, hesap @420cryptofarmer dogrulandi).
- Arsiv 6678 -> 6697 tweet (+19), en yeni kayit 2026-07-17T20:22:19. Siniflandirma tamam (analiz bekleyen 0). Paket 00-10 uretildi, 12 yeni grafik indi.
- Otomatik commit + push: `9da6954` (32 dosya).

**Duzeltme dogrulamasi (KANIT):**
- Yeni tarama alintilari kaydirma sirasinda JSON'dan on-cikti (alinti 121->122) — **hic Asama 2 sayfa navigasyonu YAPILMADAN**. JSON on-cikarim calisiyor.
- Tarama boyunca rate-limit / "Bir sorun olustu" duvarina carpilmadi.
- Asama 2'de yalnizca onceden bilinen 10 inatci alinti kaldi (birbirini alintiliyor / ana tweeti eksik / X UI kisaltmasi). Her turda 10 ziyaret (nav_cap 20 altinda), ilerleme yok — beklenen davranis, regresyon degil.

**Gozlem (ileride iyilestirilebilir):** tara_guvenli bu 10 kalici-kesik alintiyi 6 ayri ALINTI_TAMAMLA turunda tekrar deniyor (6x10=60 navigasyon). nav_cap tek finish_quotes_loop cagrisini sinirliyor ama 6 dis turu sinirlamiyor. Bu 10 alinti asla tamamlanamayacagi icin (allow_foreign kapali + X UI kisaltmasi), dis tur sayisi veya kalici-erisilemedi isaretlemesi ile bu 60 navigasyon tamamen elenebilir.

## 2026-07-20 — Guncel tarama + paket + push (05_GRAFIKLER.zip Git LFS'e tasindi)

**Yapilan:** `tara_guvenli.py` tam akis (Chrome debug 9222 acildi, hesap @420cryptofarmer dogrulandi).
- Arsiv 6697 -> 6718 tweet (+21), alinti 122 -> 126, en yeni kayit 2026-07-17T20:22:19 -> bugunku tweetler. Kaydirma hedefe (2026-07-14) ulasip durdu.
- Alinti on-cikarim JSON'dan calisti (rate-limit yok). Aşama 2'de yalnizca bilinen 10 inatci alinti kaldi (birbirini alintiliyor / X UI kisaltmasi) — 6 dis tur denedi, cozulemedi (beklenen, regresyon degil).
- Siniflandirma tamam (analiz bekleyen 0). Paket 00-10 uretildi; 05_GRAFIKLER.zip 101.09 MB / 664 grafik.

**SORUN + COZUM (Git LFS):** Zip 101.09 MB olunca GitHub 100 MB HARD dosya sinirini asti, ilk push `pre-receive hook declined` ile reddedildi (commit 243a362 local kaldi). PROGRESS'te ongorulen esik gerceklesti.
- Kullanici onayiyla **Git LFS'e gecildi** (git-lfs 3.7.1 zaten kurulu).
- `git lfs install --local` + `git lfs track "05_GRAFIKLER.zip"` -> .gitattributes olustu. Zip `git rm --cached` + `git add` ile 134 byte LFS pointer'a cevrildi. Commit **gecmis yeniden yazilmadan** amend edildi (243a362 -> 2fe578a, henuz push edilmemisti, guvenli).
- Push basarili: LFS 106 MB yuklendi, `27c64eb..2fe578a main -> main`. main...origin/main senkron.

**Onemli not (ileri):** Bundan sonra her tarama ~106 MB'lik yeni bir zip surumunu LFS deposuna ekler. GitHub ucretsiz LFS 1 GB depo + 1 GB/ay bant genisligi; ~9-10 tarama sonra kota dolabilir (ucretli olabilir). Alternatif: her tarama oncesi eski LFS surumlerini temizleme veya zip'i git'ten tamamen cikarip medya/ ile yetinme. Simdilik LFS ile devam.

## 2026-07-20 — MagicMA taramasi (dayanikli kosucu + gozetmen, kopmasiz)

**Yapilan:** Kullanici TradingView chart layout'unu (chart/zOsq3cIW, MagicMA gostergeli) port 9222 debug Chrome'da acti. Gozetmen scratchpad'de yeniden olusturuldu (magicma_supervisor.sh: 6 dk ilerleme yoksa oldur + resume, maks 25 tur) ve arka planda kosucu (magicma_tara_dayanikli.py) ile calistirildi.
- **407/407 sembol okundu, 0 okunamadi, HIC KOPMA olmadan** (gecmiste ~45. sembolde asili kaliyordu). 284 sembol rapora girdi (<=%15).
- Rapor: magicma/magicma_rapor_2026-07-20.md
- Isleme adayi (<=%0,25 cizgiye yapisik, CLAUDE.md kurali): **25 aday**. En yakinlar: UUSDT/CDNS/TSKB (%0,03), CHFJPY/XOM (%0,04), TOTAL/NZDUSD (%0,06). Cogunluk short adayi (fiyat cizgi altinda = direnc).

**Not:** Gozetmen bu oturumun scratchpad'inde yeniden olusturuldu (oturuma ozel, onceki oturumdan tasinmadi). Onkosul: 9222'de MagicMA gostergeli TradingView chart sekmesi acik olmali (ana sayfa yetmez).

## 2026-07-22 — Ekonomikocu güncel tarama + MagicMA tarama (tek oturum)

### Ekonomikocu tarama
- CHROME_X.bat ile 9222 debug Chrome açıldı (@420cryptofarmer giriş doğrulandı).
- Güncel/artımlı tarama: 6718 → **6736 tweet** (+18). En yeni tweet 2026-07-20 21:35 (hesap o tarihten beri atmamış → "şu ana kadar" kapsandı).
- tara_guvenli.py tüm akışı yürüttü: sınıflandırma + full paket (00–10) + commit `b1c01ec` + GitHub push (LFS 107 MB). Depo %21 (213 MB).
- Yanlışlıkla repo köküne düşen scratch logları (scratch_tara_log/out) temizlendi + .gitignore'a eklendi.

### MagicMA tarama
- Aynı 9222 Chrome'da TradingView chart sekmesi (giriş yapılı, indikatör yüklü layout zOsq3cIW) CDP ile açıldı.
- magicma_tara_dayanikli.py: **407 sembol, 406 okundu, 1 okunamadı**, kopma yok.
- Okunamayan: **NASDAQ:WMT** → Walmart NYSE'de. Sembol listesi düzeltildi: `magicma/sembol_listesi/abd_hisse.txt` NASDAQ:WMT → **NYSE:WMT**. (Not: 07-08'de yanlışlıkla NASDAQ'a çevrilmiş; asıl doğru NYSE.)
- Otomatik rapor: magicma/magicma_rapor_2026-07-22.md (≤%15, 280 giren).
- İşlem adayı raporu (CLAUDE.md ≤%0,25 kuralı): magicma/magicma_islem_adaylari_2026-07-22.md — **15 aday**. En yakın: UUSDT/CIMSA (%0,01). Çoğunluk short (fiyat çizgi altında = direnç).

## 2026-07-24 — Ekonomikocu guncel tarama (bugunden son taramaya)

- 9222 debug Chrome CHROME_X.bat ile acildi; hesap dogrulandi (@420cryptofarmer).
- `tara_guvenli.py` tam akis: **6736 -> 6746 tweet (+10)**. Kaydirma 2026-07-13'e kadar indi (hedef 17 Tem asildi), en yeni kayit **2026-07-23T21:43:52** — hesap 24 Tem'de tweet atmamis, "bugune kadar" kapsandi.
- Alinti: +0 (toplam 127). Bilinen **10 inatci alinti** yine cozulemedi — 6 dis turun hepsi calisti, her turda "Ilerleme yok — kalanlar isaretleniyor". Beklenen davranis, regresyon degil.
- Siniflandirma tamam (analiz bekleyen 0). Paket 00-10 uretildi: 05_GRAFIKLER.zip **101.9 MB / 668 grafik**. 7 yeni medya dosyasi indi.
- Commit `cbda56b` + push basarili (LFS 107 MB yuklendi). main...origin/main senkron.
- **LFS kotasi: 320 MB / 1024 MB (%31) — tahminen 6 tarama daha siginiyor.** Kota dolmadan zip'i git'ten cikarma / eski LFS surumlerini temizleme karari verilmeli.

**Gozlem (tekrar):** 6 dis alinti turu hala calisiyor (6x10=60 gereksiz navigasyon, ~10 dk). 5a2b0b2'deki "kalici erisilemedi" isaretlemesi tur ici dongui kapatiyor ama dis tur sayisini sinirlamiyor. Dis turu 1'e dusurmek tarama suresini belirgin kisaltir.

## 2026-07-26 — Ekonomikocu guncel tarama (tam akis)

- 9222 debug Chrome baslatildi (onceki oturum kapaliydi); hesap dogrulandi (@420cryptofarmer).
- `tara_guvenli.py` tam akis: **6746 -> 6756 tweet (+10)**. Stop-before 20 Tem, en yeni kayit **2026-07-26T01:23:07** — 24-26 Tem araligi kapsandi.
- Alinti: **+1** (127 -> 128). Bilinen **10 inatci alinti** yine cozulemedi (6 dis turun hepsi calisti). Beklenen davranis.
- Flood: +0 (1856). Siniflandirma tamam: analiz 6756 | izleniyor 872 | alinti-onceden 49 | alinti-sonradan 1.
- 5 yeni medya/grafik dosyasi indi. Paket 00-10 uretildi.
- Commit `468c551` (25 dosya, +1214/-957) + push basarili. LFS 107 MB yuklendi. main...origin/main senkron.
- **LFS kotasi: 427 MB / 1024 MB (%42) — tahminen 5 tarama daha siginiyor.** (07-24'te %31 idi; tarama basina ~106 MB.) Kota karari giderek aciliyor: 05_GRAFIKLER.zip'i git'ten cikarmak veya eski LFS surumlerini temizlemek gerekecek.

**Gozlem (3. kez tekrar):** 6 dis alinti turu hala calisiyor, taramanin ~10 dk'sini yiyor. Dis tur sayisini 1'e dusurmek hala bekleyen iyilestirme.

## 2026-07-27 — MagicMA taramasi (407/407 tam, WMT borsa kodu duzeltildi)

**Yapilan:** Port 9222 Chrome kapaliydi; MagicMA gostergeli chart layout
(`tradingview.com/chart/zOsq3cIW/`) ile ayni user-data-dir uzerinden yeniden
acildi. Gozetmen (scratchpad `magicma_supervisor.sh`, 6 dk stall -> resume) +
`magicma_tara_dayanikli.py` arka planda kosuldu.

- Tarama tek turda bitti (~29 dk, 11:25–11:54), **kopma yok**: 406 okundu,
  1 okunamadi (NYSE:WMT).
- Otomatik rapor: `magicma/magicma_rapor_2026-07-27.md` (407 sembol, 286 giren).
- Islem adayi raporu: `magicma/magicma_islem_adaylari_2026-07-27.md` — **14 aday**.
  En yakin: TRXUSDT %-0,01 (short), EURCAD %-0,01 (short). Cogunluk long
  (fiyat cizgi ustunde = destek) — 07-22'nin tersi.

**WMT teshisi ve karar:** `NYSE:WMT` MagicMA plotlarini **∅ (bos)** donduruyor;
ayni layout'ta `NASDAQ:WMT` degerleri okuyor (109,47). Yani bu hesap/layout icin
calisan kod NASDAQ. 07-22'de "asil dogru NYSE" diye yapilan degisiklik taramayi
bozmus -> `magicma/sembol_listesi/abd_hisse.txt` **NYSE:WMT -> NASDAQ:WMT** geri
alindi, tekrar tarandi, ham + raporlar 407'ye guncellendi. (Bir daha NYSE'ye
cevirme; borsa "dogrulugu" degil, TV'nin veri verdigi kod belirleyici.)

**Yeni arac:** `99_BOT_ARSIV/kod/magicma_islem_adaylari.py` — islem adayi raporu
artik elle degil scriptle uretiliyor (CLAUDE.md ≤%0,25 kurali, yakinliga sirali,
yon etiketli). Kullanim: `py -3 99_BOT_ARSIV/kod/magicma_islem_adaylari.py [TARIH]`.

## 2026-07-27 — Guncel tweet taramasi (+20 tweet)

- `tara_guvenli.py` tam akis: hesap dogrulama OK (@420cryptofarmer) -> tarama ->
  siniflandirma -> paket (00–10) -> GitHub push. Tek kosumda, mudahalesiz bitti.
- **Yeni tweet: +20 (toplam 6776)** · yeni alinti +0 (128) · yeni flood +0 (1856).
  En yeni kayit: 2026-07-27T01:56:55. Durma sebebi: 2 scroll yeni tweet yok.
- 7 yeni medya + 4 Gemini grafigi indi. Paket: 05_GRAFIKLER.zip 102,9 MB / 674 grafik.
- Commit `6d1fb5b` (31 dosya, +1602/-988), push OK, LFS 108 MB yuklendi.
- **LFS kotasi: 535 MB / 1024 MB (%52) — ~4 tarama daha sigar.** (07-26'da %42 idi.)
  Kota karari artik erteleneMEZ: 05_GRAFIKLER.zip'i git'ten cikarmak ya da eski
  LFS surumlerini temizlemek onumuzdeki 1-2 taramada gerekecek.

**Cozulmeyen (tekrar eden):** 10 alinti hala "metin kesik" — 6 dis alinti turu
calisip hicbirini tamamlayamiyor (ayni 10 ID: 2076065170099417470,
2071744148168684011, 2065017533371936987, 2064023815873585325,
2064023475178598410, 2046329630873747618, 2045587086695391351,
2038986156075872628, 1875571495164113292, 1875548019430658062). Ucu ana tweeti
None; dordu karsilikli birbirini gosteriyor (dongu). Tur sayisini 1'e dusurmek
~10 dk kazandirir — hala bekleyen iyilestirme.

## 2026-07-28 — Guncel tweet taramasi (+13 tweet)

- Baslangicta CDP 9222 kapaliydi -> `tara_guvenli.py` cikis kodu 4 verdi ("HESAP
  OKUNAMADI, Chrome kapali"). `CHROME_X.bat` calistirilarak debug Chrome acildi;
  kalici oturum profili sayesinde yeniden giris gerekmedi, hesap dogrulama OK
  (@420cryptofarmer). **Cikaram:** kod 4 her zaman "yanlis hesap" demek degil;
  Chrome kapali oldugunda da ayni kod donuyor — once CDP portunu kontrol et.
- Tam akis tek kosumda bitti: tarama -> siniflandirma -> paket (00–10) -> push.
- **Yeni tweet: +13 (toplam 6789)** · yeni alinti +0 (128) · yeni flood +0 (1856).
  5 scroll, 2026-07-13'e kadar inildi, "1 scroll'dur yeni tweet yok" ile durdu.
  En yeni kayit: 2026-07-28T02:48:08.
- 3 yeni medya klasoru + Gemini grafikleri indi. Paket: 05_GRAFIKLER.zip
  102,9 MB / 674 grafik. Kapsam 2026: ana metin/alinti/#FLOOD %100.
- Commit `2fad20e` (23 dosya, +1212/-953), push OK, LFS 108 MB yuklendi.
- **LFS kotasi: 643 MB / 1024 MB (%63) — tahmini 3 tarama daha sigar.**
  (07-27'de %52 idi, tarama basina ~106 MB.) Kota karari artik acil: bir sonraki
  taramadan once 05_GRAFIKLER.zip'i git'ten cikarmak ya da eski LFS surumlerini
  temizlemek gerekiyor.

**Cozulmeyen (tekrar eden):** Ayni 10 alinti hala "metin kesik" — bu turda da 6
tur donup hicbiri tamamlanamadi ("Ilerleme yok, kalanlar isaretleniyor").
Dordu karsilikli birbirini gosteriyor (dongu), ucunun ana tweeti None. Tur
sayisini 1'e dusurmek ~10 dk kazandirir — hala bekleyen iyilestirme.

## 2026-08-02 — Guncel tweet taramasi (+41 tweet)

- CDP 9222 yine kapaliydi -> `CHROME_X.bat` ile debug Chrome acildi (Chrome 150),
  kalici oturum profili sayesinde yeniden giris gerekmedi. Kod 4 refleksi dogru
  calisti (once CDP kontrolu, sonra Chrome ac).
- Tam akis tek kosumda bitti: tarama -> siniflandirma -> paket (00–10) -> push.
- **Yeni tweet: +41 (toplam 6830)** · yeni alinti +1 (129) · yeni flood +7 (1863).
  13 scroll, 2026-07-11'e kadar inildi, "1 scroll'dur yeni tweet yok" ile durdu.
  En yeni kayit: 2026-08-02T14:03:44.
- Siniflandirma paketlemeden once tamam: 6830/6830 `analyzed`, bekleyen 0
  (tarama icinde otomatik calisti, ayrica `analiz_devam.py` cagirmaya gerek olmadi).
- Paket: 05_GRAFIKLER.zip 104,1 MB / 682 grafik (+8 yeni Gemini grafigi).
  Reklam/kirli 13 satir pakete alinmadi.
- Commit `59d11ea` (tarama otomatik commit'i, ana paket burada) + `76255af`
  (github_guncelle.py). Push OK.

**YENI CIKARIM — cift zip israfi:** Tarama scripti bitiste kendi paketini uretip
otomatik commit atiyor (`59d11ea`). Sonrasinda `claude_paket_olustur.py`'yi elle
tekrar calistirinca 05_GRAFIKLER.zip yeniden uretildi ve **ikinci bir 104 MB LFS
objesi** dogdu. Bu turda LFS'e 218 MB yuklendi (2 obje) — normalde ~106 MB olacakti.
Bundan sonra: tarama bittiginde once `git log`'a bak, otomatik commit paketi zaten
urettiyse `claude_paket_olustur.py`'yi TEKRAR CALISTIRMA, dogrudan
`github_guncelle.py` ile kalanlari gonder.

**LFS KOTASI KRITIK:** 07-28'de 643 MB / 1024 MB (%63) idi; bu turda +218 MB ile
tahmini **~861 MB / 1024 MB (%84)**. Bir tarama daha (~106 MB) sigar, sonrasi kota
asimi. Karar artik erteleneMEZ: bir sonraki taramadan ONCE ya 05_GRAFIKLER.zip
git'ten cikarilmali (.gitignore + `git lfs untrack`) ya da eski LFS surumleri
temizlenmeli (`git lfs prune --verify-remote` yeterli degil; GitHub tarafinda
purge gerek).

**Cozulmeyen (tekrar eden, 3. tur):** Ayni 10 alinti hala "metin kesik". Asama 2'de
6 tur donuldu, hicbiri tamamlanamadi — hepsinde "Baska hesap sayfasi acilmadi
(Koc sayfasindaki metin kullanildi)". Dordu karsilikli birbirini gosteriyor
(1875571495164113292 <-> 1875548019430658062 dongusu), ucunun ana tweeti None.
Tur sayisini 1'e dusurmek ~10 dk kazandirir — hala bekleyen iyilestirme.

## 2026-08-02 (2) — LFS kotasi cozumu + alinti turu kisaltmasi

**Yapilanlar (tek commit `4516daf`):**

1. **05_GRAFIKLER.zip git takibinden cikarildi.**
   - `git rm --cached 05_GRAFIKLER.zip` — dosya **diskte duruyor** (105 MB), silinmedi.
   - `.gitignore`'a `05_GRAFIKLER.zip` eklendi.
   - `git lfs untrack "05_GRAFIKLER.zip"` — `.gitattributes` bosaldi; icine
     "TEKRAR git lfs track ETME" notu birakildi.
   - `claude_paket_olustur.py` **degistirilmedi** — zip'i uretmeye devam ediyor,
     sadece commit'e girmiyor. Claude/Gemini'ye yuklerken kok klasorden elle alinir.
   - Dogrulama: `git lfs ls-files` (HEAD) **bos**; `git status` temiz (zip ignore'da).

2. **Yerel LFS cache temizlendi.** `git lfs prune --verify-remote` →
   8 obje silindi, 1 tutuldu. `.git/lfs` **821 MB → 5 KB** (~821 MB disk kazanci).

3. **Alinti tur sayisi 6 → 1.** `tara_guncel_yeni.py:65` `--alinti-rounds`
   varsayilani 1 oldu (gerekirse `--alinti-rounds N` ile artirilabilir).
   Beklenen kazanc: her taramada ~10 dk.

**GITHUB TARAFINDA KOTA DUSMEDI — bilerek yapilmadi:**
Uzak LFS deposu hala **861 MB / 1024 MB (%84)**. `git rm --cached` + push yalnizca
HEAD'i temizler; **gecmis commit'lerdeki 8 ayri zip surumu remote'ta duruyor**
(`git lfs ls-files --all -s` → 106–109 MB x 8). `git lfs prune` sadece YEREL
cache'i temizler, GitHub depolamasina dokunmaz. GitHub'in git uzerinden LFS objesi
silme yolu **yok**.

Kalan gercek secenekler (hepsi geri donusu zor, kullanici karari bekliyor):
- **a)** GitHub Support'a LFS objelerinin silinmesi talebi (en guvenli).
- **b)** Repo'yu silip yeniden olusturmak — LFS depolamasi sifirlanir; issue/star/
  fork gecmisi kaybolur.
- **c)** `git filter-repo` ile zip'i gecmisten cikarip force-push — pointer'lar
  gider ama GitHub referanssiz LFS objelerini otomatik GC ETMEZ, kota yine dusmez.
  Tek basina ise yaramaz; (a) ile birlikte anlamli.

**Onemli olan:** kota artik **BUYUMUYOR**. Bundan sonraki taramalar LFS'e hicbir
sey eklemeyecek, %84'te sabit kalacak. Acil mudahale gerekmiyor; (a)/(b) karari
sakin sakin verilebilir.

## 2026-08-03 — Tarama + yerel .git kaybi kurtarma

**Tarama sonucu (tek giris `tara_guvenli.py`, exit 0):**
- Chrome kapaliydi (CDP 9222 yok) → `CHROME_X.bat` ile acildi, yeniden giris gerekmedi.
- Hesap dogrulama: @420cryptofarmer OK.
- 8 scroll, hedef 2026-07-30'a inildi, **+15 yeni tweet** → toplam **6845**.
- Yeni alinti +0 (129), yeni flood +0 (1863). En yeni kayit: **2026-08-03T01:23:35**.
- Siniflandirma tamam (Analiz: 6845, izleniyor 887). Paket 00–10 uretildi,
  reklam/kirli 13 satir pakete alinmadi.

**SORUN: yerel `.git` klasoru yoktu.** Oturum basinda repo git deposu degildi
(`.gitattributes`/`.gitignore` duruyor, `.git` yok). Uzak depo saglamdi
(`origin/main` = 062825a). Sebep bilinmiyor — onceki oturumda LFS temizligi
yapilmisti ama repo silinmemisti.

Sonucu: `tara_guvenli.py` bitiste `github_guncelle.py` cagirdi, o da `.git`
olmayinca **`git init` ile sifirdan repo kurup** her seyi tek root-commit
(`51a3240`) olarak commit etti → push **rejected (fetch first)**, cunku uzak
gecmisle akrabaligi yok.

**Kurtarma (dosyalara dokunulmadan):**
1. `git fetch --no-tags --filter=blob:none origin main` — blobsuz (partial clone)
   fetch. Tam fetch 5 dk'da bitmedi; blobsuz ~2 dk. Eski surumlerin 100+ MB'lik
   zip/gorsel bloblari indirilmedi.
2. `git reset --soft origin/main` — HEAD uzak gecmise tasindi, index (calisma
   agacinin tamami) korundu. Calisma agacina **hic dokunulmadi**.
3. Silinen dosya var mi diye `git diff --cached --name-status --diff-filter=D`
   kontrol edildi → **bos**. Sadece 7 ekleme (6 medya + 1 gemini grafik), 19
   degisiklik.
4. Commit `31641e8` + push → `062825a..31641e8 main -> main` **basarili**.

**LFS:** `git lfs ls-files` bos, bu turda LFS'e **0 MB** yuklendi. Kota %84'te
sabit kaldi — 08-02'deki untrack karari calisiyor.

**Cikarimlar:**
- `github_guncelle.py:30` `.git` yoksa sessizce `git init` yapiyor. Bu, gecmisi
  olan bir repoda **yanlis davranis** — push'u kesin patlatir. Ileride
  iyilestirme: `.git` yoksa `git init` yerine `git clone`/`fetch + reset --soft`
  yolu, ya da en azindan uyarip durmak.
- Repo artik **partial clone** (promisor remote, blob:none filtreli). Gunluk
  tarama/commit/push icin sorunsuz; ancak eski commit'lere `checkout` yapilirsa
  o an ag'dan blob cekilir. Tam gecmis istenirse:
  `git fetch --refetch --no-filter origin main` (yuz MB'larca indirir).
- Log yolu: taramanin stdout'u ayri bir dosyaya yonlendirilirse arka plan gorev
  ciktisi bos gorunur; ilerleme icin dogrudan o log dosyasina bakilmali.

## 2026-08-03 (2) — .git korumasi + public veri aynasi

**1. `github_guncelle.py` artik `git init` YAPMIYOR.**
`.git` yoksa `HATA: .git bulunamadi - repo bozuk olabilir, elle kontrol et`
yazip **exit 5** ile cikiyor (eski davranis: sessizce `git init` → root-commit →
push rejected; bkz. 08-03 (1) kaydi). Test edildi: gitsiz klasorde exit 5.

**2. Yeni public ayna repo: `winegg420/ekonomikocu-veri`.**
Sadece 3 ham veri dosyasi, **LFS YOK** (duz blob, toplam ~7,7 MB):
`04_TWEETLER.jsonl`, `07_ABONE_TWEETLER.jsonl`, `magicma_ham.jsonl`
(sonuncusu ana repoda `99_BOT_ARSIV/kod/` altinda, aynada kokte duz isimle).

**3. `veri_ayna_push.py` (yeni).** Ayna calisma klasoru ana repo DISINDA:
`%LOCALAPPDATA%\ekonomikocu_veri_ayna` — boylece ana repoya hicbir sey sizmiyor.
Her calistirmada 3 dosyayi kopyalar, degisiklik varsa commit+push, yoksa
"Degisiklik yok" deyip cikar. Uzakta gecmis varsa `fetch + reset --soft` ile
onun ustune oturur (ayna klasoru silinse bile yeniden kurulur).

**4. `tara_guvenli.py` akisina eklendi** — tarama bittikten sonra, LFS kota
kontrolunden once `veri_ayna_push.py` calisir. `check=False` + try/except ile
sarili: ayna push'u patlasa bile **ana tarama akisi bozulmaz**.

**Dogrulama (token'siz/anonim):** repo `private: false`, `visibility: public`,
repo sayfasi HTTP 200, `raw.githubusercontent.com/.../magicma_ham.jsonl` HTTP 200,
API contents 3 dosyayi gercek boyutlariyla listeliyor (LFS pointer degil).
Ikinci calistirma "Degisiklik yok - push atlandi" verdi (idempotent).

**Not:** ana repo ozel, ayna repo **public** — icinde tweet metinleri ve MagicMA
seviyeleri var, ikisi de zaten aleni veri. Ayna repoya baska dosya eklenmemeli.

## 2026-08-03 (3) — MagicMA taramasi (407/407) + ayna push

**Tarama:** Onceki tarama 27 Temmuz'du (7 gun bayat). Chrome 9222 aciken
MagicMA gostergeli layout (`tr.tradingview.com/chart/zOsq3cIW/`) ayni
user-data-dir'e yeni sekme olarak acildi. Gozetmen (scratchpad
`magicma_supervisor.sh`, 6 dk stall -> resume) + `magicma_tara_dayanikli.py`.

- **407/407 okundu, 0 okunamadi**, tek turda bitti, hic kopma yok
  (10:46:44 -> 11:13:05, **~26 dk**).
- Rapor: `magicma/magicma_rapor_2026-08-03.md` (407 sembol, **287 rapora girdi**).
- Ham dosya: 4121 satir; 2026-08-03 icin 407 kayit. En yeni ts: **2026-08-03T11:13:05**.
- 07-27'de duzeltilen `NASDAQ:WMT` bu turda da sorunsuz okundu (okunamayan yok).

**Ayna push:** `veri_ayna_push.py` calistirildi -> `8ed9a42..fedba7a`.
Ayna repodaki `magicma_ham.jsonl` **kokte** duruyor (ana repodaki
`99_BOT_ARSIV/kod/` yolu korunmuyor, bilerek — DOSYALAR eslesmesi bunu yapiyor).
Dogrulama: raw.githubusercontent'ten anonim indirildi, yerel dosyayla **birebir**
ayni (4121 satir, en yeni ts 2026-08-03T11:13:05, bugun 407 kayit).

**Kapsam dogrulamasi:** `veri_ayna_push.py:25-29` DOSYALAR listesi 3 dosyayi da
iceriyor (`04_TWEETLER.jsonl`, `07_ABONE_TWEETLER.jsonl`, `magicma_ham.jsonl`);
`tara_guvenli.py:39` her taramadan sonra bu scripti cagiriyor. Yani tweet
taramasi da MagicMA taramasi da ayni ayna push'unu tetikliyor, 3 dosya birlikte
guncelleniyor. Ek degisiklik gerekmedi.

**Not:** Islem adayi raporu bu turda uretilmedi (istenmedi). Gerekirse:
`py -3 99_BOT_ARSIV/kod/magicma_islem_adaylari.py 2026-08-03`.

**Islem adayi raporu (2026-08-03):** `magicma/magicma_islem_adaylari_2026-08-03.md`
— 407 sembolden **11 aday** (<= %0,25). En yakinlar: UUSDT %+0,01 (G-Ust ve G-Alt
ikisi de, cizgiler ust uste), EURAUD %+0,01, CVKMD %+0,02 — hepsi long.
Short adaylari: PETKM %-0,04 (H-2), SKBNK %-0,06 (H-1), ALARK %-0,10 (G-Alt).
Dagilim **8 long / 3 short** — 07-27'deki (14 aday) cogunluk-long egilimi suruyor.

---

## 2026-08-06 — MagicMA taramasi + ekonomikocu taramasi (tam akis)

**Baslangic durumu:** Chrome kapaliydi (CDP 9222 baglanamiyordu). Once
`99_BOT_ARSIV/calistir/CHROME_X.bat` calistirildi; ardindan MagicMA layout
sekmesi CDP `/json/new` PUT ile acildi (`https://tr.tradingview.com/chart/zOsq3cIW/`).
Kalici profil sayesinde yeniden giris gerekmedi.

**MagicMA:** supervisor (`magicma_supervisor.sh`) + `magicma_tara_dayanikli.py`
ile **tur 1'de tek seferde bitti**: 407/407 sembol okundu, **0 okunamadi**,
kopma/yeniden baglanma olmadi. Sure ~16 dk.
- Rapor: `magicma/magicma_rapor_2026-08-06.md` (407 sembol, **290 rapora girdi**).
- Islem adaylari: `magicma/magicma_islem_adaylari_2026-08-06.md` —
  **23 aday** (<= %0,25), 08-03'teki 11 adayin iki katindan fazla.
  En yakinlar: UUSDT %-0,02 (G-Alt + G-Ust ikisi de), IBM %-0,04, AAVEUSDT %-0,04,
  JTOUSDT %+0,05, TABGD %+0,06, SISE %+0,06.
  Dagilim **11 long / 12 short** — onceki turlardaki cogunluk-long egilimi
  bu turda dengeye dondu (08-03: 8 long / 3 short).

**ekonomikocu taramasi:** `tara_guvenli.py` tek girisiyle, tam akis sorunsuz:
- Yeni tweet **+21** (toplam 6866), yeni alinti +0 (129), yeni flood +0 (1863).
- Scroll 13/120'de durdu (bu oturumda en eski 2026-07-20, hedef 2026-07-31,
  1 scroll boyunca yeni tweet yok) — normal artimli davranis.
- Siniflandirma otomatik kosuldu: analiz 6866, izleniyor 890.
- 2026 kapsam: alinti %100. Abone metinli: 3425.
- 9 yeni grafik medyasi indirildi (`medya/` + `09_GRAFIKLER_GEMINI/`).
- Push: ana repo `2db95cf..f20212a` (38 dosya), veri aynasi `fedba7a..0aeca25`.

**Gozlem:** Commit mesajindaki `(2026-08-03T23:23:48)` damgasi commit zamani degil,
`tara_guncel_yeni.py:172`'deki `newest2` — yani **en yeni tweetin** zamani.
Hesabin son tweeti 08-03; 08-04..08-06 arasi yeni paylasim yok. Karistirmamak icin
not edildi (hata degil).

---

## 2026-08-07 — ekonomikocu taramasi + MagicMA taramasi (tam akis)

**Baslangic durumu:** Chrome yine kapaliydi (CDP 9222 yanit vermiyordu).
`99_BOT_ARSIV/calistir/CHROME_X.bat` ile acildi, kalici profil sayesinde yeniden
giris gerekmedi. Hesap dogrulamasi OK: aktif hesap @420cryptofarmer.

**ekonomikocu taramasi:** `tara_guvenli.py` tek girisiyle, tam akis sorunsuz:
- Yeni tweet **+37** (toplam **6903**). En yeni kayit girisi 2026-08-03T23:23:48.
- Scroll, bu oturumda gorulen en eski 2026-07-13'te durdu (hedef 2026-07-31,
  2 scroll boyunca yeni tweet yok) — normal artimli davranis.
- Ara kurtarma turu (durak #4) devreye girdi, sayfa basina donmeden devam etti.
- Siniflandirma: analiz **6903**, izleniyor **891**, alinti-onceden 50,
  alinti-sonradan 1. 2026 alinti kapsami **%100** (126/126).
- 4 yeni grafik medyasi indirildi (`medya/` + `09_GRAFIKLER_GEMINI/`).
- Push: ana repo `737d348..d4d7749` (24 dosya), veri aynasi `0aeca25..2d0926f`.

**MagicMA:** `magicma_tara_dayanikli.py` ile **tek turda bitti**: 407/407 sembol
okundu, **0 okunamadi**, kopma/yeniden baglanma yok (~35 dk).
Not: PROGRESS'te 08-06'da gecen `magicma_supervisor.sh` repoda yok (o oturumda
gecici uretilmis); dayanikli script tek basina yeterli oldu.
- Rapor: `magicma/magicma_rapor_2026-08-07.md` (407 sembol, **286 rapora girdi**).
- Islem adaylari: `magicma/magicma_islem_adaylari_2026-08-07.md` —
  **17 aday** (<= %0,25). En yakinlar: TSPOR %+0,00 (G-Ust, tam yapisik),
  NXPI %-0,00 (H-1), XAUTRY %+0,02, UUSDT %-0,03 (G-Alt + G-Ust ikisi de).
  Dagilim **5 long / 12 short** — 08-06'daki dengeden (11/12) belirgin sekilde
  **short tarafina** kaydi.

**Gozlem:** UUSDT ucuncu turdur ust uste iki cizgide birden aday cikiyor
(G-Alt ve G-Ust cakisik) — stablecoin oldugu icin cizgiler surekli yapisik,
gercek bir sinyal degil, filtrelenebilir bir yapisal gurultu.
Bu turda FX cifti agirligi dikkat cekici: 17 adaydan 6'si forex (EURAUD, GBPUSD,
EURGBP, NZDJPY x2, AUDUSD x2) ve hepsi ayni yonde toplanmiyor.

---

## 2026-08-10 — MagicMA taramasi

**Baslangic durumu:** Chrome kapaliydi (CDP 9222 yanit vermiyordu).
`99_BOT_ARSIV/calistir/CHROME_X.bat` ile acildi. Ilk tarama denemesi
"TradingView sekmesi bulunamadi" ile dustu — CHROME_X.bat sadece x.com aciyor,
MagicMA layout sekmesini acmiyor. Layout CDP `/json/new` PUT ile acildi
(`https://tr.tradingview.com/chart/zOsq3cIW/`), kalici profil sayesinde
yeniden giris gerekmedi.

**MagicMA:** `magicma_tara_dayanikli.py` ile **tek turda bitti**: 407/407 sembol
okundu, **0 okunamadi**, kopma/yeniden baglanma yok (~15 dk, ~55 sembol/2dk
sabit tempo).
- Rapor: `magicma/magicma_rapor_2026-08-10.md` (407 sembol, **299 rapora girdi**).
- Islem adaylari: `magicma/magicma_islem_adaylari_2026-08-10.md` —
  **21 aday** (<= %0,25). En yakinlar: GBPJPY %-0,01 (G-Ust), UUSDT %-0,02
  (G-Alt + G-Ust ikisi de), DXY %+0,11, COP %-0,12, TRGYO %+0,12.
  Dagilim **10 long / 11 short** — 08-07'deki belirgin short agirligindan
  (5/12) dengeye dondu.

**Gozlem:** FX yogunlugu bu turda daha da arti: 21 adayin 8'i forex cifti
(GBPJPY x2, AUDUSD x2, EURUSD, AUDJPY, EURGBP, NZDJPY x2) — 08-07'de 17'de 6'ydi.
Makro cift tarafinda hem G-Alt hem G-Ust ayni anda aday cikan semboller
(GBPJPY, AUDUSD, NZDJPY, BTC.D, UUSDT) bantlarin daralmasina isaret ediyor.
UUSDT dorduncu turdur cift-cizgi adayi — stablecoin yapisal gurultusu, filtrelenebilir.

**Push:** Ana repo `f434d4b..8441457` (4 dosya: 2 rapor + magicma_ham.jsonl + PROGRESS).
Veri aynasi push'u **BASARISIZ**: `winegg420/ekonomikocu-veri` icin
`Repository not found`; anonim HTTP istegi de 404 dondu — repo silinmis/yeniden
adlandirilmis. Ana repo ayni kimlikle sorunsuz push edildigi icin sorun yetki
degil, repo yoklugu. Yeniden kurma karari kullaniciya birakildi.

---

## 2026-08-10 — ekonomikocu taramasi (tam akis)

**ekonomikocu taramasi:** `tara_guvenli.py` tek girisiyle, tam akis sorunsuz:
- Yeni tweet **+38** (toplam **6941**). En yeni kayit girisi 2026-08-09T23:59:32
  (commit damgasi da bu — commit zamani degil, en yeni tweetin zamani).
- Scroll 15/120'de durdu (2 scroll boyunca yeni tweet yok) — normal artimli davranis.
  Ara kurtarma turu (durak #4) scroll 11'de devreye girdi, +7 tweet daha getirdi.
- Siniflandirma: analiz **6940**, izleniyor **897**, alinti-onceden 50,
  alinti-sonradan 1. 2026 alinti kapsami **%100** (126/126), #FLOOD kok %100 (8/8).
  Abone (metinli): **3435**.
- **15 yeni grafik medyasi** indirildi (`medya/` + `09_GRAFIKLER_GEMINI/`), toplam 699 grafik.
- Push: ana repo `1670e26..9e3b000` (43 dosya).

**Veri aynasi yine BASARISIZ:** `ekonomikocu-veri` reposu hala yok (404).
Bu oturumda ikinci kez ayni hata — repo yeniden kurulana kadar her taramada tekrarlayacak.

**LFS uyarisi (YANLIS ALARM):** Script "861 MB / 1024 MB (%84), ~1 tarama daha
sigar (~106 MB/tarama)" dedi — ama bu tahmin **eski**. Dogrulandi:
`git lfs ls-files` bos, `05_GRAFIKLER.zip` `.gitignore:33`'te ve son commit'te yok.
Yani 2026-08-02'deki untrack'ten beri **her tarama LFS'e 106 MB eklemiyor**;
861 MB gecmis commit'lerde donmus duruyor ve **buyumuyor**. Uyari metnindeki
"~1 tarama daha sigar" satiri `lfs_kota_kontrol.py`'nin guncellenmemis
tahmin formulunden geliyor, gercek risk degil. Acil aksiyon gerekmez.

**Gozlem:** Bu turda "en eski" damgasi tum scroll'larda sabit **2019-11-28 20:04:04**
gorundu (onceki turlarda 2026-07-13 gibi guncel tarihlerdi). Sabit kalmasi
zaman tunelinin tepesindeki **sabitlenmis (pinned) tweet** oldugunu gosteriyor —
tarama derinligiyle ilgili bir sorun degil, artimli durma kurali yine
"2 scroll boyunca yeni yok" ile calisti.

---

## 2026-08-11 — ekonomikocu taramasi (tam akis)

**Chrome kapali baslangic:** Ilk `tara_guvenli.py` denemesi CDP'ye baglanamadi
(`ECONNREFUSED 127.0.0.1:9222`) — Chrome hic acik degildi. `CHROME_X.bat`
calistirildi, port 9222 dogrulandi (Chrome/151.0.7922.77).

**Ikinci deneme cikis 4 (soguk acilis):** Chrome acildiktan ~12 sn sonra
`hesap_dogrula.py` handle okuyamadi ("HESAP OKUNAMADI"). Yanlis hesap degil —
`hesap_dogrula.py:34-35` x.com/home'u acip yalnizca **2500 ms** bekliyor;
soguk baslatilan Chrome'da sol menu (`AppTabBar_Profile_Link`) o surede
render olmamis. **Cikarim:** CHROME_X.bat'tan sonra taramaya gecmeden once
Chrome'un isinmasini bekle; ucuncu denemede ayni kod degismeden
"OK — aktif hesap @420cryptofarmer" verdi. Cikis kodu 4'un ucuncu nedeni bu
(digerleri: yanlis hesap, Chrome kapali).

**Tarama sonucu:** Yeni tweet **+6** (toplam **6946**). Yeni alinti +0 (130),
yeni flood +0 (1863). Scroll 8/120'de durdu — "bu oturumda gorulen en eski
2026-07-29, hedef 2026-08-06, 1 scroll'dur yeni tweet yok".
Ingilizce(kirli) 0, reklam/kirli atlanan 13 satir (pakette yok).
Yeni medya: `2086088516832842152/graf_01.jpg` (+ Gemini kopyasi).

**Bos scroll serisi yaniltici:** Scroll 3-6 boyunca **+0 yeni** geldi, ama
scroll 7'de tekrar +3 tweet cikti. Durma kurali salt "2 bos scroll" degil;
hedef tarihe ulasilmasi da sarta dahil. Bos seri gorunce taramayi erken
oldurme — kendi durma mantigina birak.

**Push:** Ana repo `52f2b55..1d8a646` (20 dosya, +1176/-980).

**Veri aynasi yine BASARISIZ (ucuncu kez):** `ekonomikocu-veri` reposu 404
(GitHub API ile dogrulandi; ana repo 200). Repo yeniden kurulana kadar her
taramanin sonunda ayni hata tekrarlayacak — tarama sonucunu etkilemiyor.

**Bilinen eksik:** 130 alintinin **10'u** hala metinsiz
("EKSIK: 10 alinti — tekrar: ALINTI_TAMAMLA.bat"). Onceki turdan devreden
kalinti, bu turda +0 alinti geldigi icin degismedi.

**LFS:** Yine "%84 (861/1024 MB)" uyarisi — 2026-08-10 kaydindaki gibi
**yanlis alarm**; rakam gecmis commit'lerde donmus, tarama basina buyumuyor.


---

## 2026-08-14 — 11_DIS_KAYNAKLAR.md (Koç dışı analistler) + pakete entegrasyon

**Ne yapıldı:** Yeni kök dosya `11_DIS_KAYNAKLAR.md` oluşturuldu. İçerik:
Ida'nın izlediği Koç DIŞI analistlerin (Sellcoin, Atilla Yeşilada, Berk
Dinçtürk & Ferhat Yükseltürk, Tunç Şatıroğlu, Emrah Lafçı, Baki Atılal,
Emrah Altınocağı, Foneria) tarih + seviye/hedef + Koç ile örtüşme/çelişki
notu. Sonda kaynaklar arası yakınsama/çelişki tablosu.

**Karar — neden ayrı dosya:** Bu görüşler `06_ANALIZ.md`'ye KARIŞTIRILMAZ.
06 sadece Koç'un kendi çerçevesi. Yanlış atıf riski (bir önceki oturumda
Tesla/Meta yorumu Berk Dinçtürk'e atfedilmişti, aslında Lafçı'ya aitti)
bu ayrımı zorunlu kıldı.

**Paket entegrasyonu (`claude_paket_olustur.py`):**
- `F11_DIS` sabiti eklendi. 06 gibi **asla üzerine yazılmaz / silinmez** —
  LEGACY listesinde değil, hiçbir write yolu yok.
- `write_upload_readme()` 00 dosyasını her pakette sıfırdan ürettiği için
  elle eklenen 11. satır ilk pakette silinecekti; fonksiyona `F11_DIS.is_file()`
  koşullu satır eklendi. Başlık "00-10" → "00-11".
- `basla_md()` (01) ve `build_mentor_md()` (02): 11'in tanıtımı + "hiçbir
  görüş Koç'a atfedilmez, her alıntıda kaynak ismi söylenir" mentor kuralı.
  İkisi de F11 yoksa hiçbir şey yazmıyor (geriye dönük güvenli).
- `github_guncelle.py` `git add -A` kullanıyor → değişiklik gerekmedi.

**Not:** Paket scripti ÇALIŞTIRILMADI (104 MB zip + LFS israfı). Sadece
py_compile + `basla_md`/`build_mentor_md` render testi yapıldı, çıktı doğru.
İlk gerçek doğrulama bir sonraki taramada olacak.
