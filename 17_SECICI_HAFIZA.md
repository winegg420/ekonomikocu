# 17 — SEÇİCİ HAFIZA / KENDİNİ HAKLI ÇIKARMA TESPİTİ

_Güncelleme: 2026-08-30_

> **Soru:** Bir kaynak kendi geçmiş çağrılarını alıntılarken **sadece tutanları** mı
> öne çıkarıyor? Tutmayanları hiç anıyor mu?
>
> **Yöntem:** `04_TWEETLER.jsonl` + `07_ABONE_TWEETLER.jsonl` üzerinde kendi-atıf
> kalıpları tarandı (*"demiştim", "yazmıştım", "anlatmıştım", "hatırlayın",
> "unutmayın", "twitim", "analizime bakalım", "önceden", "Oku..."* + alıntı/SS
> paylaşımları). Bulunan her atıf, `06_ANALIZ.md`'deki Koç karnesiyle eşleştirildi.
>
> **Kritik ölçüt — ikinci tarama:** Ayrıca **itiraf kalıpları** tarandı
> (*"yanıldım", "tutmadı", "bilemedim", "kaçırdım", "hata yaptım", "şaşırdım",
> "düzeltiyorum", "geri alıyorum", "beklemiyordum"*). Bu ikinci taramanın sonucu
> bu dosyanın ana bulgusu.
>
> **BU DOSYA NASIL GÜNCELLENİR:** Her yeni taramadan sonra iki kalıp taraması
> tekrarlanır ve sayılar güncellenir. `06_ANALIZ.md`'ye yeni bir TUTMADI kaydı
> eklendiğinde, Koç'un o çağrıya sonradan atıf yapıp yapmadığı **özellikle**
> kontrol edilmelidir — aşağıdaki "hiç anılmayan TUTMADI'lar" listesi oraya bakar.

---

## KOÇ

### Sayılar

| Ölçüm | Değer |
|---|---|
| Toplam kendi-atıf sayısı | **140** (`04`: 76 · `07`: 64) |
| Bunlardan **kendi bir çağrısının tutmadığını kabul eden** | **0** |
| İtiraf kalıbı eşleşmesi (ham) | 13 |
| — bunlardan gerçekten kendi hatasını kabul eden | **0** |
| Koç'un genel karne TUTTU oranı (`06_ANALIZ.md`) | **%90,6** (58 TUTTU / 64 kapanmış) |
| Alıntılanan çağrıların TUTTU oranı (eşleştirilebilen 14 örnek) | **%100** (8 TUTTU + 6 açık/çerçeve, 0 TUTMADI) |

### 13 "itiraf kalıbı" eşleşmesinin tamamı yanlış pozitif

Tarama 13 eşleşme buldu ama **hiçbiri Koç'un kendi çağrısıyla ilgili değil.**
Hepsi başkalarının hatası hakkında:

- *"Biden şurada **hata yaptı**. BTC'ye ETF verip..."* (4 Haz)
- *"FED çok büyük **hata yaptı**. 2025 Temmuz'a kadar şakır şakır faiz indirmeliydi"* (29 Tem)
- *"Bence ABD de **hata yaptı**, yönetemediler"* (14 Haz)
- *"Çin... **Stratejik hata yaptılar**"* (15 Haz)
- *"Ortak para birimi **tutmadı**"* (Avrupa hakkında, 30 Mar)
- *"Ben hallederim kafası **tutmuyor**"* (Trump hakkında, 3 Haz)
- *"Evire çevire iyi silkeliyorlar ya da silkiyorlar **bilemedim**"* (retorik, 4 Haz)
- *"NASDAQ 29700 üstünde tutmadılar mı? **Ben mi yanlış görüyorum?**"* (retorik soru, 5 Haz)
- *"Bir de adamları **düzeltiyorum**. Trump bozdu."* (başkalarını düzeltiyor, 22 Haz)

➜ **Arşivde Koç'un kendi bir çağrısı için "tutmadı / yanıldım" dediği tek bir kayıt yok.**

### Eşleştirilebilen kendi-atıflar (14 örnek)

Atfın işaret ettiği çağrının sonucu `06_ANALIZ.md` karnesinden bulunabilenler:

| Tarih | Atıf | İşaret edilen çağrının sonucu |
|---|---|---|
| 12 Tem | *"ETHTRY... 120.6 bin lira aşılmadan atak gelmez **demiştim**"* | TUTTU |
| 7 Haz (abone) | *"#BTCUSD 60 k **twitim**. O dönem abonelik yoktu"* | TUTTU |
| 19 Ağu | *"11 Haziran **analizime bakalım**... Ağustos 3. haftaya kadar karışıklık"* | TUTTU |
| 19 Ağu | *"Ben aylar önceden Nisan 7. günün önemini de **yazmıştım**"* | TUTTU |
| 20 Ağu | *"16 Şubat... Nisan 7. gün... Kaç ay **önceden** görebiliyorum"* | TUTTU |
| 20 Ağu | *"7 Nisan çıktı... Ağustos 3. hafta tepki geldi"* | TUTTU |
| 22 Ağu | *"ETHTRY... OBO vardı ama bozdular **demiştim**... 120.600'e ulaştı"* | TUTTU |
| 26 Ağu | *"#CAD **hatırlayın**. 1.38 altı kaldığı an dünya pozitif olur **demiştim**. 1.38 altında kaldı"* | TUTTU |
| 25 Ağu | *"ALTIN 4700-4800'e yanaşmak zorunda... **daha önceden sohbetini yaptık**"* | TUTTU (27 Ağu 4.700) |
| 21 Ağu | *"Ben bunu da **anlatmıştım**. NASDAQ tepede OBO yapıyor"* | İZLENİYOR |
| 24 Ağu | *"merdiven usulü yükseltirsin. **Daha önceden** BTC üzerinden **anlatmıştım**"* | çerçeve (ölçülemez) |
| 17 Tem (abone) | *"4026'ya robot koydular... **geçen seneki robotları unutmayın**"* | İZLENİYOR |
| 19 Ağu | *"#GBPJPY üzerinden süreci **anlatmıştım**"* | çerçeve (ölçülemez) |
| 19 Ağu | *"Geçen sene Temmuz'da... **faiz indirmeliler demiştim**"* | çerçeve (ölçülemez) |

**8 TUTTU · 2 İZLENİYOR · 4 çerçeve · 0 TUTMADI.**

### Hiç anılmayan TUTMADI'lar

`06_ANALIZ.md` Koç için **6 TUTMADI + 3 KISMEN** kaydediyor. Arşivde bunların
hiçbirine sonradan yapılmış bir atıf yok:

| Çağrı | Karne sonucu | Sonradan anıldı mı? |
|---|---|---|
| BTC 80.600 yukarı hedef ("10-12 May'a vakti var") — 27 Nis | TUTMADI (gitmedi, düştü) | **Hayır** — 80.600 sonradan geçiyor ama hep *başka* bir bağlamda (kesişim/negatiflik eşiği), hedefin tutmadığına değinilmiyor |
| Gümüş 68 $ kritik taban — Haziran | TUTMADI (taban kırıldı) | **Hayır** — gümüş 25 Ağustos'ta 68'e geri döndü, tez yeniden kurulmadı (bkz. `15_KOC_TUTARLILIK.md` §3) |
| Gümüş 64 $ kırılmadan durulur — 8 Haz | TUTMADI (54 $ görüldü) | **Hayır** — 9 Haziran'da 64'e *"ÇİN değeri, 64'ten gazladılar"* diye farklı çerçeveden dönülüyor |
| XAUUSD 4336 altı kapanış görmeli — 7 Ağu | TUTMADI (gelmedi) | **Hayır** |
| BTC 52K → 40K; ETH 850; SOL 25 — 21 May | Fiilen ıskalandı (`06_ANALIZ` notu: *"Koç resmen 'tutmadı' demedi"*) | **Hayır** |
| ALTIN 4.000 altında baskılandı (24 Ağu, geriye dönük) | KISMEN YANLIŞ | **Hayır** |

### Yorum

**Seçicilik var, ama tek başına bu sayılarla ölçülemeyecek kadar iç içe geçmiş.**

Alıntılananların TUTTU oranı (%100) ile genel karne oranı (%90,6) arasındaki fark
tek başına küçük görünüyor. **Asıl bulgu bu fark değil, farkın hesaplandığı
tabanın kendisi:**

Koç'un %90,6'lık karne oranı, büyük ölçüde **Koç'un kendi öne çıkardığı çağrılardan**
üretildi — çünkü arşiv taraması onun paylaştıklarını kaydediyor ve analiz oturumları
onun işaret ettiği tarihleri karneye geçiriyor. Yani **seçicilik hem alıntılarda hem
de karnenin kendisinde var.** Karne oranını "bağımsız referans" sayıp alıntı oranını
ona kıyaslamak, bu yüzden dairesel bir ölçüm.

**Sağlam olan tek ölçüm şudur:** 140 kendi-atıfta, 9 kayıtlı TUTMADI/KISMEN'e
**sıfır** geri dönüş var. Bu, oranlardan bağımsız, doğrudan sayılabilir bir sonuç —
ve seçici hafızanın en net göstergesi.

---

## DİĞER KAYNAKLAR

**Veri yetersiz — istatistik üretilmedi.** `11_DIS_KAYNAKLAR.md` video özetlerinden
oluşuyor; kaynakların kendi eski çağrılarına yaptıkları atıflar ancak özete
girdiği kadar görünüyor. Tespit edilen tüm kendi-atıflar:

| Kaynak | Atıf | Yön |
|---|---|---|
| Sellcoin (20 Ağu) | *"[altın] kırılımı geçen hafta **önceden çağırmış**"* | Kendini haklı çıkarma |
| Berk Dinçtürk | *"MTA süper döngüsü tezini **2024'ten beri savunuyor**"* | Kendini haklı çıkarma |
| Cüneyt Paksoy (JH haftası) | *"Yuan, yılbaşında **öngördükleri gibi** güçlendi... tezi doğrulandı (**kendi karnelerine göre**)"* | Kendini haklı çıkarma |

**n = 3.** Üçü de olumlu yöndeki bir geçmiş çağrıya atıf; hiçbiri tutmayan bir
çağrıya değinmiyor. **Yön Koç'la aynı ama örneklem istatistik için çok küçük** —
oran hesaplanmadı.

**Tek istisna, ve kayda değer:** Sellcoin'in gümüşteki görüş değişimi
(27 Tem *"55 $ dip, zayıf"* → 10 Ağu *"62 $ yeni destek, trend başladı"*)
kaynağın kendisi tarafından değil, **`11_DIS_KAYNAKLAR.md`'yi yazan analiz
tarafından** tespit edilip kaydedilmiş. Yani dış kaynaklarda görüş değişiminin
kaydını kaynak değil, bu depo tutuyor.

---

## SINIRLAMA

- **Kalıp taraması metin tabanlı.** Koç'un eski tweetini **ekran görüntüsü olarak**
  paylaştığı, ama metinde hiçbir atıf kalıbı kullanmadığı durumlar bu sayıma
  girmiyor. Bu, 140 sayısının **alt sınır** olduğu anlamına gelir.
- **`is_quote` alanı güvenilir bir kendi-atıf göstergesi değil** — alıntılanan
  içerik başkasına ait olabiliyor. Bu yüzden sınıflandırma metin kalıbına dayandırıldı.
- Karne eşleştirmesi **elle** yapıldı (14 örnek); 140 atfın tamamı için otomatik
  eşleştirme mümkün değil, çünkü atıfların çoğu hangi çağrıya işaret ettiğini
  açıkça söylemiyor.
