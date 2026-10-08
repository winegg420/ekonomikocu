# CANLI DURUM (otomatik üretilir — elle düzenleme; kaynak: CANLI_DURUM.json)
- last_updated: 2026-10-08T21:40:43+03:00
- source_commit: b4a7647
- Son taranan tweet: 2026-10-08T21:25:34 [2108262544712344038]
- Analiz bekleyen tweet sayısı: 260
- ⚠ UYARI: 260 yeni tweet taranmış, analiz bekliyor; yeni çağrılar henüz işlenmedi
- Son işlenen tweet: 2026-10-07T00:55:31 (tur 28)
- Kapsam: koc_cagrilari son 14 gün (23 Eyl - 7 Eki 2026, son işlenen tweet'e göre). 7 Ekim 00:55'ten sonraki tweet'ler henüz analiz edilmedi. Durum alanı 06_ANALIZ TUR 28 karnesine (7 Ekim) dayanır; canlı piyasa verisini webden çek ve seviyelerle kendin karşılaştır. Bu dosyada fiyat YOKTUR.
- Okuma sırası: CANLI_DURUM.md → Canlı piyasa verisini webden çek, seviyelerle karşılaştır → Gerekirse 06_ANALIZ.md (Koç çerçevesi) ve 11_DIS_KAYNAKLAR.md (dış kaynaklar, ayrı) → Kanıt için ham 03_HAFIZA.md / 04_TWEETLER.jsonl / 07_ABONE_TWEETLER.jsonl (tweet_id ile ara)

## KOÇ (yalnız @ekonomikocu'nun kendi sözü)
Durumlar: GEÇERLİ = seviye/koşul hâlâ izleniyor, bozulmadı; TETİKLENDİ = Koç'un söylediği tepki/seviye gerçekleşti; BOZULDU = iddia tutmadı (şimdilik olanlar notta belirtilir); BELİRSİZ = net okunamadı, ölçülemedi veya sınanmadı

### Çağrılar (son 14 gün, yeniden eskiye)
- 2026-10-06 EURJPY: Ocak çağrısı: 175'e düzeltme lazım; 'gelmesi 6 ay sürüyor' → GEÇERLİ (metin) [2107564806257668186] — Süre beyanı; JPY çaprazlarını short geçer, kriz bekler [2107567356541112553]
- 2026-10-06 SP500: 7816 altında kalırsa sendeler → GEÇERLİ (metin) [2107523489137615037] — Teyit/kırılım yok
- 2026-10-06 NASDAQ: 31.400 direnç: değdi, satış yedi (H1) → TETİKLENDİ (görsel okundu) [2107522128362844307] — Koç işleme girip kâr elde ettiğini söyledi (ölçülemez)
- 2026-10-06 ALTIN: 4235 üstü kalış = ekstra prim (4376 direnç etiketli) → GEÇERLİ (görsel okundu) [2107444098252820703] — Alt yatay ~3930 yaklaşık okuma
- 2026-10-06 ALTIN: 4192 yatay direnç + düşen trend kesişimi önemini koruyor → GEÇERLİ (görsel okundu) [2107442847645655353] — Alt kanal ~3970 yaklaşık okuma
- 2026-10-06 BIST100: 12.800 üstü kapanış gelirse rahatlar; altı stres → BELİRSİZ (görsel okundu) [2107238461920956571] — Koşul gerçekleşmedi; Koç'un stres tarafı sürüyor
- 2026-10-06 EURUSD: 1,1280 altı negatif, üstü toparlar → BELİRSİZ (metin) [2107361032196767960] — Koşul gerçekleşmedi (negatif taraf)
- 2026-10-06 EURUSD: 1,1460 trend bozuldu; gerçek toparlama için 1,1460 üstü kalış → GEÇERLİ (metin) [2107358777003716617] — Aylık trend çizgisinin değeri 1,1460 (görsel 2107365069281808839)
- 2026-10-06 BRENT: 97 altı haftalık kapanış gelirse piyasa toparlar; "tek umut burası" → GEÇERLİ (görsel okundu) [2107221007077384602] — Haftalık kapanış Cuma; 6 Eki 97 görüldü, geri döndü
- 2026-10-06 BTC: 84.700 üstü pozitif, altı kenara çekilin (12 Ekim'e kadar) → GEÇERLİ (metin) [2107251852722962850] — Süre 12 Ekim
- 2026-10-06 BTC: 84K altı trend bozulur → GEÇERLİ (metin) [2107251492574900466]
- 2026-10-06 BTC: Petrol 97 altında + BTC 87K üstü -> 18 Ekim'e kadar piyasalar neşelenir → GEÇERLİ (metin) [2107251004466995621] — Süre 18 Ekim; iki koşul birlikte
- 2026-10-06 NASDAQ: 30.600 yatay direnç üstü; 30.600 altı satışa iter → GEÇERLİ (görsel okundu) [2107218087518867745] — Direnç -> destek rolüne geçti
- 2026-10-06 DOW: 50.600 üstünde kaldıkça sorun yok; aşağısı direkt düşüş (haftalık) → GEÇERLİ (görsel okundu) [2107219240977879450]
- 2026-10-06 DOW: 8. güne kadar 51.570 takip edilecek → GEÇERLİ (metin) [2107405675873829113] — Süre 8 Ekim; 10-14-15 Ekim önemli [2107218551983489364]
- 2026-10-06 GUMUS: Haftalık yükselen trend çizgisi bozulmadı → GEÇERLİ (metin) [2107504607354118190] — Çizginin sayısal değeri yazılmadı
- 2026-10-03 BTC: 81.998 yatay: eski direnç banda alındı -> destek → GEÇERLİ (görsel okundu) [2106457547699839083] — 3 kez direnç olan bant üstüne alındı
- 2026-10-03 ALTIN: 4376,38 üç kez red (Eki 2025, Haz 2026, Eyl 2026) → GEÇERLİ (görsel okundu) [2106458126220431475]
- 2026-10-03 ALTIN: 4257'den şelale (4257,44 yatay + kısa trend kesişimi) → TETİKLENDİ (görsel okundu) [2106395823319990772] — 25 Eyl 4257 çağrısının teyidi
- 2026-10-03 EURGBP: EUR 1,12'ye, EURGBP 0,84'e düşüyor → GEÇERLİ (metin) [2106450083273466229] — 0,84 bölgesi H4 görselde ok [2106451512545210746]; 0,84e inilmedi
- 2026-10-03 GBPJPY: 219,2 -> 206 düşüş; 206,857 yatay destek → GEÇERLİ (görsel okundu) [2106448997128732738] — Destek denenmedi
- 2026-10-03 DOW: 50.600 -> 51.570 atak: 50.600 = 6 öğretisi, 51.570 = 5.7 öğretisi → GEÇERLİ (görsel okundu) [2106389498523426927] — H4: üst direnç 51.570, alt destek 50.600
- 2026-10-03 NASDAQ: 31.060 fitil yeri = 6 öğretisi → GEÇERLİ (görsel okundu) [2106388491169124412] — H1; 2 Eki tepe 31.060, dip 30.300 [2106392130986111191]
- 2026-10-02 ALTIN: 4235 geçilmeden sorun yok, üstü dikkat → GEÇERLİ (metin) [2106018280268075350] — 2 Eki; TUR 28: 6 Eki Koç tekrarladı (4192 önemli, 4235 üstü kalış lazım); 4235 geçilmedi
- 2026-10-02 EURJPY: Haftalık 170,60 ve 150,60 → BELİRSİZ (görsel okundu) [2105968739002765523] — Yön/koşul net okunmadı
- 2026-10-02 DXY: İdeal bant 90-95; 100 üstü dünyaya yaramıyor → GEÇERLİ (metin) [2105963036242477548] — DXY 110→95 tetiği ile ilişkili
- 2026-10-01 EURGBP: H4 0,8600-0,8610 reddi (Haziran'da açtığı short) → GEÇERLİ (görsel okundu) [2105671816182403524] — Pozisyon kârı beyanı ölçülemez
- 2026-10-01 NASDAQ: 25.700 = 5.7 öğretisi destek → BELİRSİZ (görsel okundu) [2105644176033345581] — Ürün/ölçek metinde NASDAQ; kesinlik düşük
- 2026-10-01 DOW: Ayın 8'ine kadar zamanı var, 51.570 üstüne aldılar → GEÇERLİ (metin) [2105637723323166935] — Süre 8 Ekim; TUR 28: 6 Eki "8. güne kadar 51570" tekrarı; hedef henüz gelmedi
- 2026-10-01 OTHERS.D: 10,60 aşılmadan iştah yok → GEÇERLİ (görsel okundu) [2105629874681454890]
- 2026-10-01 ALTIN: 4217'de robot var → GEÇERLİ (metin) [2105626569230414119] — 1 Eki
- 2026-09-30 SEMBOLSUZ (muhtemelen DJI): 52.800 altı short; 50.600 kırılırsa satış derinleşir; 49.200/49.400 önemli → BELİRSİZ (metin) [2105328731678294326] — Sembol yazılmamış; DJI doğrulanmadı
- 2026-09-30 DAX: 25.700 (5.7 öğretisi) kırılan trendin altında yatay direnç → GEÇERLİ (görsel okundu) [2105320390008742289] — DAX sembol listesinde yok
- 2026-09-30 BRENT: 95,7 üstü long / altı short; 106 yanaşınca short denenir → GEÇERLİ (görsel okundu) [2105261131308708306] — 95.7 = 5.7 öğretisi
- 2026-09-30 BTC: 80.600 üstü long; 79.200 stop; 84K alım tetiği; 87.600 aşılırsa yeni zirve → GEÇERLİ (görsel okundu) [2105258824127160667] — TUR 28: 87K aşılıp kalınmadı; 84K altına kısa dokunuş oldu; 84.700 üstü pozitif / 12 Ekim; 87.600 aşılmadı
- 2026-09-30 ETH: 2620 üstü long; 2570 kritik; 2776 aşılırsa alım; 2840 asıl bakılacak; 2557 stop → GEÇERLİ (görsel okundu) [2105251223397888209] — 2840 ürünü: muhtemel_varlik alanına bak
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
- 2026-09-26 ETH: M30 2620,88 yatay destek → GEÇERLİ (görsel okundu) [2103621589103509874] — 26 Eyl; 2620/2570 tutuyor
- 2026-09-25 ALTIN: Gelecek hafta 4257 altı satış, üstü diri → TETİKLENDİ (metin) [2103529014010708354] — 28 Eyl 4257'ye değdi, sonra aşağı
- 2026-09-25 NASDAQ: 30.300 altı ayın 4'üne kadar satış baskısı → BOZULDU (görsel okundu) [2103526020188180688] — 4 Ekim süresi doldu, 30.300 altına inilmedi; Koç hatayı kabul etti (hafta sonunu hesaplamamış) [2106393285610680566]
- 2026-09-25 NASDAQ: Yeni aylık mum eski zirve üstünde açılmazsa varlıklar düşer → BELİRSİZ (metin) [2103523340371497407] — Ekim aylık açılış mumu doğrulanmadı; sınanmadı
- 2026-09-24 NASDAQ: 29.700 önemini kimse unutmasın; 30.600 üstünde tutma → GEÇERLİ (metin) [2103143907231981773] — Destek denenmedi
- 2026-09-24 ETH/BRENT: 28,4 direnç; 16,2 destek; 73,6 zirve → BELİRSİZ (görsel okundu) [2103128399594074541] — Metin-görsel eşlemesi kesin değil (06 TUR 27)
- 2026-09-24 FED FAIZI: 5,75 aşılmadan ilk etap bir şey olmaz → GEÇERLİ (metin) [2103081364723790243]
- 2026-09-23 DOW: 50.600 üstü zaman geçirir; 50.570 altı süreç bitiyor → GEÇERLİ (metin) [2102845245977231455]
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
- 2026-10-08: DOW 51.570 hedefi için Koç'un süresi ('8. güne kadar'); 6 Eki tekrarı [2107405675873829113]; 'Ayın 8. günü önemli' [2107517377084612611] [2105637723323166935]
- 2026-10-12: Koç: BTC 84.700 üstü pozitif, altı kenara çekilin ('bu ayın 12. gününe kadar vakti var') [2107251852722962850]
- 2026-10-13/14: Koç: '13-14 Ekim önemli'; 6 Eki: 'artık 10-14-15 Ekim önemli' [2105636945002910171]
- 2026-10-15: Koç: 'Ekim ortasına kadar izlemek lazım' [2103143481979904474]
- 2026-10-18: Koç: petrol 97 altı + BTC 87K üstü ise 'ayın 18. gününe kadar vakti var' [2107251004466995621]
- 2026-10-ay sonu: Koç: 'Ay sonu FED var' (6 Eki) [2107218551983489364]
- 2026-12-15: Vade: 15 Eyl - 15 Ara 90 günlük döngü bitişi [2102349810338873574]
- 2027-01: Koç: 'Ocak 2027'ye kadar anlaşma tarihi' [2104496858538324393]
- 2026-10-19: Koç 60 günlük blok sonraki durak (bot hesabı, Koç tweet'i değil) [tweet_id yok]

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
