# ekonomikocu

@ekonomikocu X (Twitter) hesabinin tweet arsivi, mentor analiz paketi ve
tarama botlari. Playwright ile acik Chrome oturumundan tweet/grafik/abone
verisi ceker; ham veriyi Claude/Gemini icin yukleme paketlerine (00–10)
donusturur ve GitHub'a gonderir. MagicMA seviyelerinden islem adayi raporu
uretir. Ayrintili genel bakis icin `README.md` ve `SEMA.md`.

- Kod: `99_BOT_ARSIV/kod/` — tek tarama girisi `tara_guvenli.py`
- Ham veri: `cekilen_tweetler.jsonl`, `ekonomikocu_hafiza_v1.md`, `medya/`
- Yukleme seti: `00`–`10` kok dosyalari

## KURULUM

Gereken: Python 3.10+ ve Google Chrome. (Bu makinede `python` PATH'te yoksa
`py -3` kullan.)

```bash
# 1) Sanal ortam (opsiyonel ama onerilir)
python -m venv .venv && .venv\Scripts\activate

# 2) Bagimliliklar
pip install -r 99_BOT_ARSIV/requirements.txt

# 3) Playwright tarayici surucusu
python -m playwright install chromium

# 4) Ortam degiskenleri
copy .env.example .env   # sonra .env icini doldur (OPENAI_API_KEY opsiyonel)
```

Sik kullanilan komutlar:

```bash
# Guncel/artimli tarama (once @420cryptofarmer ile Chrome'da giris yapili olmali)
python 99_BOT_ARSIV/kod/tara_guvenli.py

# Abone tweet metinlerini doldur
python 99_BOT_ARSIV/kod/tara_guvenli.py --abone

# Claude/Gemini yukleme paketi uret (00–10)
python 99_BOT_ARSIV/kod/claude_paket_olustur.py

# GitHub'a gonder
python 99_BOT_ARSIV/kod/github_guncelle.py
```

## TARAMA KURALI
- Tarama için ASLA tara_*.py / guncelle_*.py dosyalarını doğrudan çağırma.
- Her zaman tek giriş: python 99_BOT_ARSIV/kod/tara_guvenli.py
  - Güncel/artımlı tarama:  python 99_BOT_ARSIV/kod/tara_guvenli.py
  - Abone tweet doldurma:    python 99_BOT_ARSIV/kod/tara_guvenli.py --abone
- Çıkış kodu 4 = yanlış/eksik hesap. Bu durumda TARAMA YAPMA, kullanıcıya
  "@420cryptofarmer ile giriş yap" de. Kendi başına hesap değiştirme.
- abone_etiketle.py'yi ASLA çalıştırma (boşlukları maskeler).

## MENTOR ANALIZ KAYIT KURALI
- Mentor oturumlarında çıkan önemli analiz sentezleri 06_ANALIZ.md sonuna tarihli bölüm olarak eklenir ve github_guncelle.py ile push edilir. 06_ANALIZ.md'nin üstteki içeriği asla silinmez/üzerine yazılmaz.

## MAGICMA RAPOR FORMAT KURALI
- MagicMA raporu oluştururken SADECE çizgiye gerçekten yapışık ürünleri listele: ≤ %0,25 mesafe.
- %0,3 ve üzeri uzaklıktakiler "uzak" sayılır, işlem adayı olarak listelenmez.
- Liste yakınlığa göre sıralı (en yakın en üstte).
- Her satırda yön etiketi olacak:
  - Fiyat çizginin ALTINDA = DİRENÇ = "short adayı"
  - Fiyat çizginin ÜSTÜNDE = DESTEK = "long adayı"
- Satır formatı: SEMBOL | fiyat | çizgi adı (G-Alt/G-Üst/H-1/H-2) | çizgi değeri | mesafe % | short adayı / long adayı
- Seviyeler en son taramadan alınır (magicma_ham.jsonl içinde her sembol için en yüksek ts).

## COK HESAPLI TARAMA — HESAPLAR BIRBIRINE KARISMAZ

Bu depo birden fazla X hesabini tarar. **Hicbir hesabin verisi digerine karismaz**;
bu bir konvansiyon degil, kodla zorlanan bir kural.

- Tek giris ayni: `py -3 99_BOT_ARSIV/kod/tara_guvenli.py --hesap <handle> --days N`
- `--hesap` yalnizca TARANACAK profili secer; X'e giris yapan hesabi DEGISTIRMEZ
  (giris hala @420cryptofarmer olmali, cikis kodu 4 kurali aynen gecerli).
- Veri koku kurali tek yerde: `99_BOT_ARSIV/kod/hesap_kok.py`
  - `ekonomikocu` -> depo koku (eski davranis, hic degismedi)
  - baska her hesap -> `<depo>/<handle>/` (jsonl, medya/, `<handle>_hafiza_v1.md`,
    tara_bookmark.json, alinti_bekleyen.jsonl, tara_deneme.json)
- **Karisma engelleri (RuntimeError ile durdurur):**
  1. Ikincil hesap depo kokune (ekonomikocu arsivine) YAZAMAZ.
  2. Her ikincil klasorde `_HESAP.txt` isaret dosyasi var; baska hesap o klasore
     yazmaya kalkarsa durur.
  3. Veri koku DAIMA handle'dan turetilir — ayarlanacak ikinci bir degisken yok,
     dolayisiyla "handle verildi ama kok unutuldu" hatasi imkansiz.
- **Denetim:** `py -3 99_BOT_ARSIV/kod/hesap_denetle.py` — tum hesaplarda tweet_id
  ve medya cakismasini kontrol eder. Cikis 0 = temiz. Yeni hesap ekledikten sonra
  bir kez calistir.
- Yeni hesap eklemek icin kod degisikligi GEREKMEZ: `--hesap <yeni>` yeter.

### @iriscibre ("iris cibre tara")
- "iris cibre tara" dendiginde taranacak profil **@iriscibre** (Iris Cibre).
- Komut: `py -3 99_BOT_ARSIV/kod/tara_guvenli.py --hesap iriscibre --days 7`
- Bu hesapta 00-10 yukleme paketi URETILMEZ (mentor paketine ozgu). Ham arsiv +
  medya toplanir ve push edilir.
- Yuksek hacimli oldugu icin profil kaydirmasinda `stop-before` tetiklenmez
  (her scroll'da yeni kayit gelir, "yeni yok" kosulu olusmaz) ve tarama aylarca
  geriye sarkar. Bu yuzden `--days N` verildiginde otomatik **tarih sinirli arama
  moduna** gecer: `from:iriscibre since:.. until:..`.
- Arama akisi yanitlari DA dondurur (ekonomikocu'daki abone-ozel kisitlamasi
  burada yok, hesap herkese acik). Ancak sonuc akisi gec dolar: ilk 2-3 scroll
  "ekranda 3-4" gorunur, **erken durdurma**.

## HIZLI FİYAT KONTROLÜ (MagicMA çizgilerini yeniden taramadan)

MagicMA seviyeleri (4H/haftalık indikatör çizgileri) sık değişmez. Mentor oturumlarında "işlem fırsatı var mı" sorulduğunda çizgileri yeniden taramaya (TradingView/Chrome CDP 9222 üzerinden `magicma_yakinlik.py --tara`) gerek YOK — sadece `magicma/magicma_islem_adaylari_TARIH.md` dosyasındaki son çizgi listesi + o anki güncel fiyat karşılaştırılır.

**Önemli kısıt:** Mentor oturumları (claude.ai Project/Cowork) ayrı bir bulut sandbox'ta çalışır; bu sandbox'ın ağ erişimi kısıtlıdır (api.binance.com, query1.finance.yahoo.com gibi ham API'lere doğrudan curl/requests ile erişemiyor — proxy 403 döndürüyor) ve bu depoya git push yetkisi yoktur. O yüzden mentor oturumu güncel fiyatları sadece web arama/fetch araçlarıyla (tarayıcı benzeri) çekebiliyor, ham API ile değil.

Bu nedenle mentor oturumunun hızlı ve güvenilir çalışabilmesi için doğrulanmış kaynak kalıpları:
- **BIST hisseleri:** `https://infoyatirim.com/borsa/{kod-küçük-harf}-hisse` (örn. OYAKC → `https://infoyatirim.com/borsa/oyakc-hisse`) — hızlı, net tarihli, güvenilir.
- **Kripto:** `https://www.coingecko.com/en/coins/{slug}` (örn. ARKMUSDT → arkham, SUIUSDT → sui, KASUSDT → kaspa) — hızlı, güvenilir.
- **ABD hisseleri:** Yahoo Finance (`https://finance.yahoo.com/quote/{TICKER}/`) kullanılabilir ama bazen tutarsız/gecikmeli veri dönebiliyor; piyasa kapalıyken (NY saatiyle 09:30-16:00 dışı) canlı teyit anlamsız.
- **Forex çaprazları (USDCAD, CADJPY, USDJPY, EURGBP, GBPCHF, EURCHF vb.):** Henüz hem hızlı hem <%0,3 hassasiyette güvenilir bir kaynak bulunamadı (XE ve TradingEconomics'te bayat/cache'li zaman damgaları görüldü). Eğer ileride bu depoda/local makinede (sandbox kısıtı olmadan) çalışacak bir script yazılırsa, ücretsiz/anahtar gerektirmeyen bir forex API'si (örn. Frankfurter, exchangerate.host) düşünülebilir — ama bunu sandbox'tan çalıştıramayız, sadece local makineden (Claude Code / Ida'nın kendi bilgisayarı) çalıştırılabilir.

**Kripto için not (opsiyonel, ileride faydalı olabilir):** MagicMA taramasındaki kripto sembolleri zaten Binance ticker formatında (ARKMUSDT, SUIUSDT, KASUSDT vb.). Local makineden (mentor sandbox'ından değil) `https://api.binance.com/api/v3/ticker/price?symbol=ARKMUSDT` gibi bir çağrıyla anlık/kesin fiyat alınabilir — CoinGecko'dan bile daha kesin. İstersen bunun için basit bir yardımcı script (`magicma/fiyat_kontrol.py`) yazılabilir; mentor oturumu bunu çalıştıramaz ama sen (Ida) local'de saniyeler içinde çalıştırıp çıktısını mentor'a yapıştırabilirsin.

**GÜNCELLEME:** Artık `magicma/fiyat_kontrol.py` scripti var — local'den (Claude Code'dan) çalıştırıldığında Binance (kripto, tek toplu istek), Frankfurter (forex, tek toplu istek, ECB tabanlı) ve infoyatirim.com (BIST, paralel/threaded) kaynaklarından SANİYELER içinde yüzlerce sembolün güncel fiyatını çekip en son MagicMA taramasındaki çizgilerle karşılaştırır. Kullanım: `py -3 magicma/fiyat_kontrol.py` (varsayılan eşik %0,3, `--esik` ile değiştirilebilir). Çıktı hem konsola hem `magicma/fiyat_kontrol_son.md`'ye yazılır — bu dosyanın içeriği doğrudan mentor oturumuna yapıştırılabilir, mentor tekrar tek tek WebFetch yapmak zorunda kalmaz.

Ayrıca forex için tekil doğrulama gerekirse (mentor oturumundan) XE yerine `https://www.investing.com/currencies/{baz}-{karsi}` (örn. aud-nzd, eur-chf) kullanılsın — XE'de bayat/cache'li zaman damgaları görüldü, investing.com "Real-time Data" etiketli çalıştı.

**Yazıldıktan sonra düzeltilen kaynak notu (2026-08-27, script gerçekte ne kullanıyor):**
- **BIST: infoyatirim.com DEĞİL, Yahoo Finance `.IS`.** infoyatirim.com python-requests bağlantısını TLS el sıkışmasında resetliyor (WinError 10054), script içinden çekilemedi; `THYAO.IS`, `MPARK.IS` gibi Yahoo kodlarına geçildi (MPARK.IS = 437,25 ile tarama fiyatı birebir doğrulandı). infoyatirim.com mentor oturumu için (tarayıcı/WebFetch ile) hâlâ geçerli.
- **Forex: önce Yahoo `=X` (anlık), Frankfurter/ECB yalnızca yedek.** Frankfurter günlük ECB referans kuru döndürüyor, %0,3 eşiği için gün içi yeterince taze değil.
- **Kripto: sadece Binance değil** — Binance + MEXC + Gate.io + Bybit + OKX + KuCoin toplu ticker uçları (her biri tek istek); sembolün kendi borsası önce denenir. "Günün hareketlileri" listesindeki MEXC/Gate coinleri böyle kapsanıyor.
- **Değerli metal (XAUUSD/XAGUSD/XPTUSD/XPDUSD/XAUTRY):** api.gold-api.com (ücretsiz, anahtarsız, anlık spot) — Yahoo'da bu spot semboller yok.
- **Seviyeler markdown rapordan DEĞİL, `99_BOT_ARSIV/kod/magicma_ham.jsonl`'den** (her sembol için en yüksek ts) okunuyor; markdown rapor 2 ondalığa yuvarladığı için forexte %0,3 eşiği anlamsızlaşıyordu (AUDNZD 1,1946 → "1,19"). Rapordan okumak için `--rapordan` bayrağı var.
- Ölçülen kapsama: 747 sembolün 744'ü, ~30 saniyede.

## TELEGRAM MAGICMA ALARMI

`magicma/telegram_alarm.py` — `fiyat_kontrol.adaylari_hesapla()`'yi kullanarak
MagicMA cizgisine YENI temas eden sembolleri Telegram'a bildirir. Windows Task
Scheduler gorevi **"MagicMA Telegram Alarm"** her gun 09:00'dan itibaren 15
saat boyunca 15 dakikada bir calistirir (pyw.exe ile penceresiz).

- Gizli bilgi: repo kokundeki `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
  **.gitignore'da — asla commit edilmez.**
- Durum: `magicma/alarm_son_durum.json` (anahtar `SEMBOL|CIZGI_ADI`), log:
  `magicma/telegram_alarm_log.txt`. Ikisi de gitignore'da.
- **Histerezis:** giris esigi %0,25, cikis esigi %0,50 (`--cikis-esik`). Bir
  kayit %0,25'e girince bildirilir; listeden ancak %0,50'yi asinca duser.
  Boylece esik sinirinda salinan sembol her turda yeniden bildirilmez.
- Ilk calistirmada (durum dosyasi yoksa) bildirim GONDERILMEZ. Yeni temas
  yoksa mesaj gonderilmez.
- **Tarama araligi 10 dk** (Task Scheduler, 7/24).
- **Mesajlar arasi EN AZ 10 dk** (`--mesaj-araligi`, varsayilan 10). Bu sure
  dolmadan bulunan adaylar durum dosyasindaki KUYRUGA alinir, sonraki mesajda
  hepsi TEK seferde gider; kuyrukta bekleyenin yaninda gorulme saati yazar.
  Elle calistirma + zamanlanmis calistirma ust uste gelse bile arka arkaya iki
  bildirim dusmez. Kuyruk yalnizca mesaj BASARIYLA gidince bosaltilir.
- **Mesaj asla parcalanmaz:** bir turun tum adaylari tek mesajda; sinira
  sigmazsa kesilir ve "+N aday daha" yazilir.
- Elle deneme: `py -3 magicma/telegram_alarm.py --kuru` (gondermeden ekrana yazar).
  Bekletmeyi kapatmak icin `--mesaj-araligi 0`.
- **`fiyat_kontrol.py`'yi degistirirken `adaylari_hesapla()` imzasini bozma** —
  alarm scripti bunu import ediyor.

## MAGICMA BAND YON KURALI (2026-08-28 — eski geometrik kurali gecersiz kilar)

MagicMA cizgileri bagimsiz seviye DEGIL, **bandin iki siniri**:
- `Magicma Günlük Alt Çizgi` + `Magicma Günlük Üst Çizgi` -> **Günlük band**
- `Magicma Haftalık -1` + `Magicma Haftalık -2` -> **Haftalık band**

**Cizgi ADLARI guvenilir degil:** olculdu, 744 sembolun yalnizca 289'unda (%39)
"Alt Çizgi" gercekten "Üst Çizgi"den kucuk. Band sinirlari ADA gore degil
**DEGERE gore (min/max)** kurulur. Bu yuzden mesajlarda cizgi adi gosterilmez,
bandin sayisal araligi gosterilir.

**Yon kurali** (`magicma/bant_yon.py`):
- Fiyat bandin **USTUNDE** -> band destek -> **LONG adayi**
- Fiyat bandin **ALTINDA** -> band direnc -> **SHORT adayi**
- Fiyat bandin **ICINDE** -> banda hangi taraftan girildigi belirler:
  yukaridan indiyse LONG, asagidan ciktiysa SHORT.

Band ici gelis yonu **gercek saatlik kapanis serisiyle** bulunur: seri sondan
basa taranir, fiyatin bandi en son hangi taraftan terk ettigine bakilir.
Kaynak, fiyati veren borsanin kendi kline ucu (Binance `1h`, **MEXC `60m`** —
MEXC'te `1h` 400 doner —, Gate/Bybit/OKX/KuCoin adaptorleri) veya Yahoo
`range=1mo&interval=1h`. Seri alinamazsa TradingView toplu high/low
(bugun -> bu hafta -> bu ay) yedegi; o da net degilse band ici konum tahmini
kullanilir ve gerekce metnine **TAHMİN** yazilir.

**Eski kural neden birakildi:** cizgileri tek tek "fiyat altinda = direnc"
diye etiketlemek, fiyat bandin icindeyken ayni sembol icin bir cizgiye gore
SHORT digerine gore LONG uretiyordu (kendi icinde celiskili).

> **ACIK KALAN:** `99_BOT_ARSIV/kod/magicma_islem_adaylari.py` (satir 86-87, 99)
> HALA eski cizgi-bazli geometrik kurali kullaniyor ve
> `magicma_islem_adaylari_TARIH.md` raporlarini ona gore uretiyor. Tarama aninin
> fiyatiyla calistigi icin band-ici yon tespiti ayri bir tasarim gerektiriyor;
> bilerek degistirilmedi.

## PIYASA SAATI FILTRESI (2026-08-28)

`magicma/piyasa_saati.py` — her varlik sinifi yalnizca KENDI acik oldugu saatte
taranir. Filtre **script icinde**, Task Scheduler seviyesinde DEGIL; gorev artik
**7/24, her 15 dakikada bir** calisir.

- `bist.txt` -> hafta ici **09:40-18:10 TSI**, hafta sonu kapali.
- `abd_hisse.txt` -> hafta ici **09:30-16:00 New York saati**. TSI karsiligi DST
  ile kayar (yaz 16:30-23:00, kis 17:30-00:00). **Tarih hardcode EDILMEZ**,
  `zoneinfo` ile New York yerel saatine cevrilip karsilastirilir.
- `kripto.txt`, `forex_emtia.txt`, `endeks_faiz.txt`, `gunun_hareketlileri.txt`
  -> **filtre yok, 7/24**. (Forex gercekte hafta sonu kapali ama bu surumde
  bilerek filtrelenmiyor. Resmi tatil takvimi de yok — bilinen sinirlamalar.)
- Bir sembol hem filtreli hem serbest listede varsa **serbest kazanir**
  (orn. XU100 `endeks_faiz.txt`'te -> filtrelenmez).

Kapali sembollerin fiyati **hic cekilmez** (gereksiz API cagrisi yok).
Piyasa kapandigi icin listeden dusen sembol "LISTEDEN CIKTI" diye
**bildirilmez**, sessizce durum dosyasindan duser — gercek bir sinyal degil.

**`tzdata` bagimliligi:** Windows'ta sistem saat dilimi veritabani yoktur,
`zoneinfo` icin `tzdata` paketi gerekir (requirements.txt'e eklendi). Paket
yoksa modul cokmez: Turkiye sabit UTC+3, ABD icin 2007'den beri gecerli DST
KURALI (Mart'in 2. Pazari - Kasim'in 1. Pazari) uygulanir. Iki yol da ayni
sonucu veriyor (22/22 senaryoda dogrulandi).

Filtreyi kapatmak icin: `telegram_alarm.py --piyasa-saatini-yoksay`.
`fiyat_kontrol.py`'de filtre **varsayilan KAPALI** (mentor icin kapali
piyasanin son kapanis fiyati hala ise yariyor); acmak icin `--piyasa-saati`.

## MAGICMA OKUNAMAYAN KARA LISTESI (2026-08-28)

`99_BOT_ARSIV/kod/magicma_kara_liste.py` + `magicma/okunamayan_kara_liste.json`

TradingView'de MagicMA gostergesi cizilmeyen "olu" semboller sembol basina
~20 sn (MAX_DENEME x timeout) harciyordu. Artik kendi kendini guncelleyen bir
kara liste var:

- Sembol okunamazsa -> kara listeye eklenir, `deneme_sayisi` artar.
- **Sembol okunursa -> kara listeden CIKARILIR** (gecici arizalar kalici
  engellenmez; MEXC:CTRUSDT ornegi).
- `deneme_sayisi >= KARA_LISTE_ESIK` (3) -> sonraki taramalarda TradingView'e
  **hic gidilmez**, dogrudan "okunamayanlar"a yazilir.
- Atlanan sembol `YENIDEN_DENE_GUN` (7) gun sonra **bir kez daha denenir**
  (yeni coin sonradan MagicMA verisi kazanabilir). Yine basarisizsa sayac
  sifirdan baslar.
- Esikler tek yerde: `magicma_kara_liste.py` basi.

**Iki katmanli koruma:**
1. `magicma_tara_dayanikli.py` — tarama sirasinda atlar.
2. `gunun_hareketlileri_guncelle.py` — kara listedeki sembolu
   `gunun_hareketlileri.txt`'e **hic yazmaz**. Bu sart, cunku o dosya her
   calistirmada bastan uretiliyor; elle "yorum satirina alma" kalici degil.

**Tohumlama:** `py -3 99_BOT_ARSIV/kod/magicma_kara_liste.py --tohumla`
En son `magicma_rapor_*.md`'nin "Okunamayanlar" bolumu ILE `magicma_ham.jsonl`de
hic kaydi olmayanlarin KESISIMINI kara listeye ekler. Iki sart birden arandigi
icin "bugun eklenmis, henuz denenmemis" sembol yanlislikla girmez.

**Durum gormek icin:** `py -3 99_BOT_ARSIV/kod/magicma_kara_liste.py`
`magicma/taranamayan_semboller.md` icindeki `KARA-LISTE-OTOMATIK` isaretcileri
arasindaki blok her taramada yeniden yazilir; disindaki elle notlara DOKUNULMAZ.
