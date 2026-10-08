# CANLI DURUM (otomatik üretilir — elle düzenleme; kaynak: CANLI_DURUM.json)
- last_updated: 2026-10-08T22:00:39+03:00
- source_commit: 1f35590
- Son taranan tweet: 2026-10-08T21:25:34 [2108262544712344038]
- Analiz bekleyen tweet sayısı: 0
- Son işlenen tweet: 2026-10-07T00:55:31 (tur 28)
- Kapsam: koc_cagrilari son 16 gün (23 Eyl - 8 Eki 2026, son işlenen tweet'e göre). Durum alanı 06_ANALIZ TUR 29 karnesine (8 Eki ~21:55 TSİ fiyatları) dayanır; canlı piyasa verisini webden çek ve seviyelerle kendin karşılaştır. Bu dosyada fiyat YOKTUR.
- Okuma sırası: CANLI_DURUM.md → Canlı piyasa verisini webden çek, seviyelerle karşılaştır → Gerekirse 06_ANALIZ.md (Koç çerçevesi) ve 11_DIS_KAYNAKLAR.md (dış kaynaklar, ayrı) → Kanıt için ham 03_HAFIZA.md / 04_TWEETLER.jsonl / 07_ABONE_TWEETLER.jsonl (tweet_id ile ara)

## KOÇ (yalnız @ekonomikocu'nun kendi sözü)
Durumlar: GEÇERLİ = seviye/koşul hâlâ izleniyor, bozulmadı; TETİKLENDİ = Koç'un söylediği tepki/seviye gerçekleşti; BOZULDU = iddia tutmadı (şimdilik olanlar notta belirtilir); BELİRSİZ = net okunamadı, ölçülemedi veya sınanmadı

### Çağrılar (son 14 gün, yeniden eskiye)
- 2026-10-08 CIN-ABD: "ABD ile Çin asla uzun vadeli anlaşamazlar"; "anlaşsalar grafikler onaylamaz" → GEÇERLİ (metin) [2108197546162057377] — Anlaşma doğrulaması YOK (cin_abd_anlasma false kalır); "Trump İran ile verimli görüşme" haberi 8 Eki [2108231333797630145]
- 2026-10-08 FAIZ: Koç: faizler düşmeli (dilek); petrol düşmeli, emtia kaprisi bitmeli, faizler düşmeli → BELİRSİZ (metin) [2107960386763051505] — FED indirimi beklentisi DEĞİL; "petrolü ve faizi düşürmezsen shorta devam" [2108247877600653334]; 5-6 yıldır faizler düşer yönlü oyun [2108245853542735936]
- 2026-10-08 ZAMAN: ABD vadesi 15 Eyl-15 Ara; son çeyrek 13-14 Ekim'den sonra; "Ekim ortasına kadar izleme"; "ayın 18'ine kadar vakti var"; "2027 Nisan'a kadar zamanın var" → GEÇERLİ (görsel okundu) [2108200811041882321] — Koç takvim yönetimi [2108202957774700856][2108229340823691562][2108235754392731948]; 30 Eyl yanıtı [2108200811041882321]
- 2026-10-08 BTCUSD: 106.309,69 (Koç'un yuvarlak içine aldığı çizgi kesişimi); "buraya gitse bile kılımı kımıldatmam" → BELİRSİZ (görsel okundu) [2107955273293848614] — Çağrı değil, çizim sorusu; BTC 83K civarındayken. Takipçilerden çizgi temasını çizmelerini istedi
- 2026-10-08 EURUSD: 1,1180'de robot: altında kalırsa DXY bir tur ciddi yukarı; üstündeyse DXY gevşer → GEÇERLİ (görsel okundu) [2108121720267932155] — 8 Eki EURUSD 1,1188 → 1,1215; DXY 102,16; kanıt: 15 Nis 2026 [2108122060383735815]
- 2026-10-08 ETH: 2776,25 yatay red (23 Eyl, 2 Eki); 2570+2620 üstü anca pozitif; ETH.D 13-14 üstü kalmalı → TETİKLENDİ (görsel okundu) [2108217860573008252] — 2776 reddi H1'de teyitli; ETH 2.448 [2108217860573008252][2107963414987579602]
- 2026-10-08 BTCTRY: 4.257,118 (4257 = 5.7) yatay + yükselen trend; "bozmasalar teknik alım" → GEÇERLİ (görsel okundu) [2107951664485277989] — BTCTRY 4.109.959, trend çizgisi teması [2107950994202259656]; "ALTIN GÜMÜŞ bunları baskılıyorlar"
- 2026-10-07 BTC: 80.600 son kale; 84.700 kırıldı; 12. gün / 18. güne kadar süre; 85K üstü 18'ine kadar → GEÇERLİ (görsel okundu) [2107858986611446216] — 80.600 H1 8 Eki'de 80.667 dip ile test edildi [2108233147695710382]; BTC 81.500. "Aşağıya robot koyup satışları tetikletiyorlar" [2107867384048398762]
- 2026-10-08 DOW: 52.800 aşılmadan geri geliyor; 50.600 tutuyor (H4 50.607,67); H1 üst 51.570,76 → GEÇERLİ (görsel okundu) [2108190560141881795] — "50600 kırılmadan düşmez, 52800'ü aşacak dinamiği de bulamıyor; haber lazım" [2108190560141881795][2108189895235641427]; 8 Eki "kıramıyorlar, zorlanıyorlar"
- 2026-10-07 NASDAQ: 31.400 kesişimi: değdi, şelale (7-8 Eki) → TETİKLENDİ (görsel okundu) [2107854861207236791] — H1 yatay 31.404,88 reddi, NDX 30.697; XAUUSD/NASDAQ oranı 0,132 [2107839726577193046]
- 2026-10-08 NASDAQ: 31.060 altında kalışlar SAT, üstü anca diri (8 Eki: yarına kadar vakti var) → TETİKLENDİ (metin) [2108195060751728699] — NDX 30.697 < 31.060; 9 Eki kritik. Koç 31400'den shortladığını söyledi (ölçülemez)
- 2026-10-07 GUMUS: 50 doların altında kalmadan ABD bırakmaz; 58 gördü; ~68 kesişim aşmasın → GEÇERLİ (görsel okundu) [2107907337709400356] — Gümüş 59,24; 7 Eki 58'e temas [2107813527675085045]; 8 Eki günlük ~68 kesişim [2108197180708438066]; "ederi 50 altı" temel görüş [2107820480040161504]
- 2026-10-07 ALTIN: 4060 = 6 öğretisi destek: 4060 gördü, +50$ sekti; 4060 altı kalma = ekstra baskı; 4300-4500'de short kovalanmaz → TETİKLENDİ (görsel okundu) [2107863579844055142] — 7 Eki: 4060'a değdi, sekti; altın 4.128,6. "4376 altı zaten satış" [2107863579844055142]; "4060 altı kalma anca ekstra baskı" [2107865241711464734]
- 2026-10-06 EURJPY: Ocak çağrısı: 175'e düzeltme lazım; 'gelmesi 6 ay sürüyor' → GEÇERLİ (metin) [2107564806257668186] — Süre beyanı; JPY çaprazlarını short geçer, kriz bekler [2107567356541112553]
- 2026-10-06 SP500: 7816 altında kalırsa sendeler → TETİKLENDİ (metin) [2107523489137615037] — SPX 7.757 < 7.816 (8 Eki)
- 2026-10-06 NASDAQ: 31.400 direnç: değdi, satış yedi (H1) → TETİKLENDİ (görsel okundu) [2107522128362844307] — Koç işleme girip kâr elde ettiğini söyledi (ölçülemez)
- 2026-10-06 ALTIN: 4235 üstü kalış = ekstra prim (4376 direnç etiketli) → GEÇERLİ (görsel okundu) [2107444098252820703] — Altın 4.128,6; 4235 geçilmedi (8 Eki)
- 2026-10-06 ALTIN: 4192 yatay direnç + düşen trend kesişimi önemini koruyor → GEÇERLİ (görsel okundu) [2107442847645655353] — Altın 4.128,6; 4192 geçilmedi (8 Eki)
- 2026-10-06 BIST100: 12.800 üstü kapanış gelirse rahatlar; altı stres → BELİRSİZ (görsel okundu) [2107238461920956571] — BIST100 12.214; üstü kapanış yok, stres tarafında
- 2026-10-06 EURUSD: 1,1280 altı negatif, üstü toparlar → TETİKLENDİ (metin) [2107361032196767960] — EURUSD 1,1215 < 1,1280 (8 Eki); 1,1180 yeni "robot" seviyesi
- 2026-10-06 EURUSD: 1,1460 trend bozuldu; gerçek toparlama için 1,1460 üstü kalış → GEÇERLİ (metin) [2107358777003716617] — EURUSD 1,1215, 1,1460'tan ~%2,2 uzakta; toparlama yok
- 2026-10-06 BRENT: 97 altı haftalık kapanış gelirse piyasa toparlar; "tek umut burası" → GEÇERLİ (görsel okundu) [2107221007077384602] — Brent 104,4 (8 Eki Trump-İran haberiyle -3$ sonrası); 97 altı kapanış yok
- 2026-10-06 BTC: 84.700 üstü pozitif, altı kenara çekilin (12 Ekim'e kadar) → TETİKLENDİ (metin) [2107251852722962850] — 84.700 altına inildi (H1 kesişim kırıldı); BTC 81.500, 12 Eki'ye kadar geri dönüş yok [2107860033589616802]
- 2026-10-06 BTC: 84K altı trend bozulur → TETİKLENDİ (metin) [2107251492574900466] — 8 Eki H1 dip 80.667; BTC 81.500
- 2026-10-06 BTC: Petrol 97 altında + BTC 87K üstü -> 18 Ekim'e kadar piyasalar neşelenir → GEÇERLİ (metin) [2107251004466995621] — 87K aşılmadı (BTC 81.500), Brent 104,4; 18 Eki'ye kadar süre
- 2026-10-06 NASDAQ: 30.600 yatay direnç üstü; 30.600 altı satışa iter → GEÇERLİ (görsel okundu) [2107218087518867745] — NDX 30.697 (8 Eki ~21:55), 30.600'e ~100 puan; sınırda
- 2026-10-06 DOW: 50.600 üstünde kaldıkça sorun yok; aşağısı direkt düşüş (haftalık) → TETİKLENDİ (görsel okundu) [2107219240977879450] — 8 Eki H4/H1 dibi 50.607,67 yatayda tepki; DJI 51.168 [2108190560141881795]
- 2026-10-06 DOW: 8. güne kadar 51.570 takip edilecek → BOZULDU (metin) [2107405675873829113] — Süre 8 Eki doldu; DJI 51.168, 51.570'e gelmedi. Koç: "kıramıyorlar, zorlanıyorlar" [2108196270485434829]
- 2026-10-06 GUMUS: Haftalık yükselen trend çizgisi bozulmadı → BELİRSİZ (metin) [2107504607354118190] — Haftalık 58,752 çizgiye temas (8 Eki), kırılım teyidi yok; gümüş 59,24 [2108224068327555249]
- 2026-10-03 BTC: 81.998 yatay: eski direnç banda alındı -> destek → BOZULDU (görsel okundu) [2106457547699839083] — BTC 81.500 < 81.998; banda dönüş yok (8 Eki)
- 2026-10-03 ALTIN: 4376,38 üç kez red (Eki 2025, Haz 2026, Eyl 2026) → GEÇERLİ (görsel okundu) [2106458126220431475] — Altın 4.128,6; 7 Eki "4376 altı zaten satış" [2107863579844055142]
- 2026-10-03 ALTIN: 4257'den şelale (4257,44 yatay + kısa trend kesişimi) → TETİKLENDİ (görsel okundu) [2106395823319990772] — 25 Eyl 4257 çağrısının teyidi
- 2026-10-03 EURGBP: EUR 1,12'ye, EURGBP 0,84'e düşüyor → GEÇERLİ (metin) [2106450083273466229] — EURUSD 1,1215 (1,12 civarı doldu); EURGBP 0,8476, 0,84'e inmedi
- 2026-10-03 GBPJPY: 219,2 -> 206 düşüş; 206,857 yatay destek → GEÇERLİ (görsel okundu) [2106448997128732738] — GBPJPY 208,73; 206,857 denenmedi
- 2026-10-03 DOW: 50.600 -> 51.570 atak: 50.600 = 6 öğretisi, 51.570 = 5.7 öğretisi → BOZULDU (görsel okundu) [2106389498523426927] — 50.600 tuttu ama 51.570'e ulaşılmadı (8 Eki)
- 2026-10-03 NASDAQ: 31.060 fitil yeri = 6 öğretisi → GEÇERLİ (görsel okundu) [2106388491169124412] — 8 Eki: "31060 altında kalışlar SAT, üstü diri" [2108195060751728699]; NDX 30.697 altında
- 2026-10-02 ALTIN: 4235 geçilmeden sorun yok, üstü dikkat → GEÇERLİ (metin) [2106018280268075350] — Altın 4.128,6 < 4235
- 2026-10-02 EURJPY: Haftalık 170,60 ve 150,60 → BELİRSİZ (görsel okundu) [2105968739002765523] — Yön/koşul net okunmadı
- 2026-10-02 DXY: İdeal bant 90-95; 100 üstü dünyaya yaramıyor → GEÇERLİ (metin) [2105963036242477548] — DXY 102,16 (8 Eki)
- 2026-10-01 EURGBP: H4 0,8600-0,8610 reddi (Haziran'da açtığı short) → GEÇERLİ (görsel okundu) [2105671816182403524] — Pozisyon kârı beyanı ölçülemez
- 2026-10-01 NASDAQ: 25.700 = 5.7 öğretisi destek → BELİRSİZ (görsel okundu) [2105644176033345581] — Ürün/ölçek metinde NASDAQ; kesinlik düşük
- 2026-10-01 DOW: Ayın 8'ine kadar zamanı var, 51.570 üstüne aldılar → BOZULDU (metin) [2105637723323166935] — Süre doldu; 51.570 gelmedi (8 Eki)
- 2026-10-01 OTHERS.D: 10,60 aşılmadan iştah yok → GEÇERLİ (görsel okundu) [2105629874681454890]
- 2026-10-01 ALTIN: 4217'de robot var → GEÇERLİ (metin) [2105626569230414119] — Altın 4.128,6 altında; 4217 geçilmedi
- 2026-09-30 SEMBOLSUZ (muhtemelen DJI): 52.800 altı short; 50.600 kırılırsa satış derinleşir; 49.200/49.400 önemli → BELİRSİZ (metin) [2105328731678294326] — Sembol yazılmamış; DJI doğrulanmadı
- 2026-09-30 DAX: 25.700 (5.7 öğretisi) kırılan trendin altında yatay direnç → GEÇERLİ (görsel okundu) [2105320390008742289] — DAX sembol listesinde yok
- 2026-09-30 BRENT: 95,7 üstü long / altı short; 106 yanaşınca short denenir → GEÇERLİ (görsel okundu) [2105261131308708306] — 95.7 = 5.7 öğretisi
- 2026-09-30 BTC: 80.600 üstü long; 79.200 stop; 84K alım tetiği; 87.600 aşılırsa yeni zirve → GEÇERLİ (görsel okundu) [2105258824127160667] — 8 Eki H1 dip 80.667 çizgide tepki; "80.600 son kale" [2108233147695710382]; kalıcı altı yok
- 2026-09-30 ETH: 2620 üstü long; 2570 kritik; 2776 aşılırsa alım; 2840 asıl bakılacak; 2557 stop → BOZULDU (görsel okundu) [2105251223397888209] — ETH 2.448 < 2.570 (8 Eki); 2776 yine red yedi
- 2026-09-30 NASDAQ: 26K VE 22.600 birlikte taciz edilirse küresel satış işareti → GEÇERLİ (metin) [2105062684488015890] — Eski tepe kuralının fiyat versiyonu
- 2026-09-29 BTC: 107.800 eski destek kırıldı, direnç → GEÇERLİ (görsel okundu) [2105030629679042681]
- 2026-09-29 ETH: Seviye zinciri: 1379 (aylık kapanış altı = biter); 1746-1846; 2060-2157; 2570 (hacim ister); 2776; 3060; 3300 üstü net kapanış → GEÇERLİ (metin) [2105012338743239121] — 1379 aylık savunma izleniyor
- 2026-09-29 BTCTRY: 4,2-4,3 milyon trend direnci → GEÇERLİ (metin) [2104961619482771848] — Tek veri noktası; zaman sinyalleri 2027 ilk çeyrek + Ağustos 2027
- 2026-09-28 BRENT: 100 ve üstü 'beni kurtarıyor'; 103-106'da altın-gümüş daha çok düşer → GEÇERLİ (metin) [2104615352856625404] — Koç'un kendi short pozisyonu bağlamı
- 2026-09-28 US10Y: Trend hedefi %5,5-6,2 → GEÇERLİ (görsel okundu) [2104610222585299309]
- 2026-09-28 BRENT: 96,30 üstü ayın 2'sine kadar diri → TETİKLENDİ (metin) [2104503978599784609] — 28 Eyl; süre içinde tuttu
- 2026-09-27 BTC: Log 1H üst trend çizgisi ~130-135K (yaklaşık okuma) → BELİRSİZ (görsel okundu) [2104307976668667948] — Okuma yaklaşık; kesin seviye değil
- 2026-09-26 BTC/GBP: 60.600 kesişimi (6 öğretisi) → BELİRSİZ (görsel okundu) [2103935574260547895] — Tek görsel okuma; karnesi yok
- 2026-09-26 BTC: Haftalık 67.000,53: 67K altında bekletip üstüne alıyorlar → GEÇERLİ (görsel okundu) [2103860230379483624] — 67K üstünde kalış sürüyor
- 2026-09-26 ETH: M30 2620,88 yatay destek → BOZULDU (görsel okundu) [2103621589103509874] — ETH 2.448 < 2.620 (8 Eki)
- 2026-09-25 ALTIN: Gelecek hafta 4257 altı satış, üstü diri → TETİKLENDİ (metin) [2103529014010708354] — 28 Eyl 4257'ye değdi, sonra aşağı
- 2026-09-25 NASDAQ: 30.300 altı ayın 4'üne kadar satış baskısı → BOZULDU (görsel okundu) [2103526020188180688] — 4 Ekim süresi doldu, 30.300 altına inilmedi; Koç hatayı kabul etti (hafta sonunu hesaplamamış) [2106393285610680566]
- 2026-09-25 NASDAQ: Yeni aylık mum eski zirve üstünde açılmazsa varlıklar düşer → BELİRSİZ (metin) [2103523340371497407] — Ekim aylık açılış mumu doğrulanmadı; sınanmadı
- 2026-09-24 NASDAQ: 29.700 önemini kimse unutmasın; 30.600 üstünde tutma → GEÇERLİ (metin) [2103143907231981773] — NDX 30.697; 29.700 denenmedi
- 2026-09-24 ETH/BRENT: 28,4 direnç; 16,2 destek; 73,6 zirve → BELİRSİZ (görsel okundu) [2103128399594074541] — Metin-görsel eşlemesi kesin değil (06 TUR 27)
- 2026-09-24 FED FAIZI: 5,75 aşılmadan ilk etap bir şey olmaz → GEÇERLİ (metin) [2103081364723790243]
- 2026-09-23 DOW: 50.600 üstü zaman geçirir; 50.570 altı süreç bitiyor → GEÇERLİ (metin) [2102845245977231455] — 50.600 8 Eki'de test edildi, tuttu
- 2026-09-23 ETH: 2776 'güçlü direnç değil, aşılırsa bir çırpıda geçer' → BOZULDU (metin) [2102744076613308671] — 2776 iğnesi tekrarlandı, kapanış üstü yok; şimdilik tutmadı
- 2026-09-23 GUMUS: 68 üstü ABD stres; 68 altında kalacak, 65-70 bandı; aylık 66'da biterse 75-80-90 senaryosu → TETİKLENDİ (metin) [2102716298329227753] — 68 tavanı tuttu (TUR 27 karnesi); 75-90 senaryosu gerçekleşmedi
- 2026-09-23 GRAM ALTIN: 6800 TL önemli → BELİRSİZ (görsel okundu) [2102528291043233962] — Karnesi yok
- 2026-09-23 ALTIN: 4376 pivot: üstüne çok taşarsa sat, altına kayarsa sebebine bak → TETİKLENDİ (metin) [2102525897572229178] — 23 Eyl 4376,91'den döndü (TUR 27 karnesi)

### Muhtemel varlık (kesin değil)
- 2840 → ETH (ETHUSD), kesinlik: orta [2106101544798326934]
  - Gerekçe: 22 Eyl 15:32 [2102375411128602831] ve 30 Eyl 13:59 [2105251223397888209] tweet'leri 2840'ı ETH ile anıyor; 2 Ekim tweet'i ürün yazmıyor.
  - KESİN DEĞİL. 8.4 öğretisi aynı etiketle NASDAQ 28400 için de kullanılmış. Seviyeyi kesin ETH diye sunma.

### Öğreti sayıları
- 5.7 (orta): Seviyenin son iki hanesi 57/…70 (ölçekten bağımsız); 'her varlıkta büyük pivot'. Örnekler: 75.700, 65.700, 0,857, 57, 65,7, 25,7 [2105041065086468585] — 30 Eyl: Brent 95.7; DAX 25.700 [2105320390008742289]
- 6 / 60.60 (orta): …60 hanesi: 57 — 60.60 — 84 — 92 — 106 merdiveni (Koç'un 30 Eyl 18:17 tweet'i) [2105316177572503590] — Brent 106 = 6 öğretisi; BTC 60K ve XAGUSD/BRENT 0,60 aynı ölçek
- 8.4 (belirsiz): 84 / 8.4 / 28.4 / 2840 / 8400 için etiket [2106101544798326934] — Ürün atfı belirsiz (muhtemel_varlik'a bak); kapsamı kesin tanımlı değil
- 9.2 (belirsiz): Koç 'görürsem öne çıkartırım' dedi [tweet_id yok] — Kuralın dışında kaldı; tanımı net değil (06_ANALIZ TUR 25 D)

### Eski tepe kuralı
- Boğaya gitse bile varlık zamanla ESKİ TEPEYE düzeltir. Aylık kapanışlar önceki tepeyi aşamıyorsa o malın işi bitmiştir; yeni hikâye ister. (2026-09-30) [2105044389407912055]
  - BTC: 19.292,53 (2017 tepesi) (orta)
  - ETH: 1.379,43 (2017 tepesi); aylık kapanış altında kalırsa ETH biter (orta) [2105012338743239121]
  - NASDAQ100: 16.365 · 22.683 · 26.269; 26K VE 22.600 birlikte taciz = küresel satış (orta) [2105062684488015890]
  - GUMUS: 50 $ (2011 tepesi) (orta)
- Koç aynı gün 'BTC 126K'da satan adamı zarar ettiremezsin, 170-200 dese de oraya döner' dedi [2105050425347240220]; ETH için 4800'e düzeltme beklentisi sordu [2105047851764273374]. Test: Eylül aylık NASDAQ kapanışı, Ekim ortası ETH/1.379 davranışı.
- Zaman tezi: 12 gün boyunca tek çatı: 'zaman geçiriyorlar' — ölçüt fiyat değil tarih (Ekim ortası, 13-14 Ekim, vade 15 Eyl-15 Ara). Seviye 'geldi/gelmedi' bu rejimde yanlış okunur.

### Takvim
- 2026-10-08: DOW 51.570 hedefi için Koç'un süresi ("8. güne kadar") DOLDU — 51.570'e gelmedi; Koç: "kıramıyorlar, zorlanıyorlar" [2108196270485434829] [2105637723323166935]
- 2026-10-09: Koç: NASDAQ 31.060 altı SAT / üstü diri, "yarına kadar vakti var" [2108195060751728699]
- 2026-10-12: Koç: BTC 84.700 üstü pozitif, altı kenara çekilin ('bu ayın 12. gününe kadar vakti var') [2107251852722962850]
- 2026-10-13/14: Koç: '13-14 Ekim önemli'; 6 Eki: 'artık 10-14-15 Ekim önemli' [2105636945002910171]
- 2026-10-15: Koç: 'Ekim ortasına kadar izlemek lazım' [2103143481979904474]
- 2026-10-18: Koç: petrol 97 altı + BTC 87K üstü ise 'ayın 18. gününe kadar vakti var' [2107251004466995621]
- 2026-10-ay sonu: Koç: 'Ay sonu FED var' (6 Eki) [2107218551983489364]
- 2026-12-15: Vade: 15 Eyl - 15 Ara 90 günlük döngü bitişi [2102349810338873574]
- 2027-01: Koç: 'Ocak 2027'ye kadar anlaşma tarihi' [2104496858538324393]
- 2026-10-19: Koç 60 günlük blok sonraki durak (bot hesabı, Koç tweet'i değil) [tweet_id yok]
- 2027-04: Koç: "Zaman geçir, 2027 Nisan'a kadar zamanın var" (ABD için) [2108235754392731948]
- 2026-09-15/2026-12-15: Koç: ABD vadesi 15 Eylül'de başlar, 15 Aralık'ta biter; son çeyrek 13-14 Ekim'den sonra [2108202957774700856]

## KULLANICI DURUŞU (Ida — analist görüşü DEĞİL)
- Bu bölüm Ida'nın kendi duruşudur; Koç'un veya herhangi bir analistin görüşü DEĞİLDİR. Analist görüşleriyle karıştırma.
- ETH uzun vade hedef ~10.000$; ETH satmaz, BTC'ye çevirmez.
- Yeni nakit kademeli olarak BTC'ye gider.
- Ana odak: spot (BIST) + PrimeXBT'de kaldıraçlı forex / ABD hissesi.
- Kripto (altcoin dahil, stablecoin hariç) takip kapsamındadır.

## MAGICMA
- MagicMA tek başına işlem sistemi değildir; yardımcı seviye/sinyal katmanıdır.
- Backtest: magicma/backtest_rapor.md (3 Ekim 2026): eğitim 28 Ağu-18 Eyl, test 19 Eyl-3 Eki; %0,1 gidiş-dönüş maliyet sonrası test setinde rastgeleyi anlamlı aşan kârlı kombinasyon YOK. En iyi eğitim kombinasyonu (stop %0,2 / TP %3) testte n=1787, ort. net %-0,047, p=0,382.
- Alarm/karne verisi bilgi amaçlıdır; tek başına al-sat gerekçesi yapma.

## DIŞ KAYNAKLAR (Koç'a atfedilmez)
- Bu kaynaklar Koç'a ASLA atfedilmez. Koç'un çerçevesi yalnız koc_cagrilari ve 06_ANALIZ.md'dedir.
- Dosya: 11_DIS_KAYNAKLAR.md — kaynaklar: Sellcoin, Berk Dinçtürk, Atilla Yeşilada, Tunç Şatıroğlu, Emrah Lafçı, Baki Atılal, Emrah Altınocağı, Erol Polat, Cüneyt Paksoy, Yükseltürk & Çay, Cihat Çiçek, Barış Soydan, Selçuk Geçer, Berk Tavsan, Integral FX TV, Şant Manukyan, Turhan Bozkurt, Bora Özkent, Fiba Bank, Kemal Hiçyılmaz, Kripto Teknik, Erkan Öz, Erdal Sağlam, Iris Cibre
- Abone/imza kuralı: Koç thread'lerindeki abone tweetleri Koç'a yazılmaz. 07'de imza/hesap alanı yok; atıf için jev_abone_etiketler.jsonl (yazar=abone/koc + güven) ve elle kontrol kullanılır.
  - MANUELAGBADOU (@Alizber65), abone: BTCTRY 80.600 / 84.000 / 85.700 / 86.000 / 92.000 (21 Eyl) [2104961306952368261] — Koç yalnız 'dolar bazlı izleyin' dedi
  - ThePenguinBTC: Japonya/yen haberi görseli [2103939368071332290] — Koç yalnız yorumladı
  - uzmancoin: 'Kripto Haftası' görseli (15 Tem) [2103132971947753862] — Koç'un değil
  - isimsiz Fransa/ECB analisti: Fransa bütçe analizi [2104171811017544047] — Koç aktardı; kendi görüşü değil
  - dış söylem: Altın 5600 / Petrol 100 retoriği [2105727709821157734] — Koç'un seviyesi değil
- Çin-ABD anlaşması: Doğrulayan içerik yok (magicma/koc_tetigi_durum.json: false).
