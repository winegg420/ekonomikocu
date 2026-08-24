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

## IKINCI HESAP: @iriscibre ("iris cibre tara")
- "iris cibre tara" dendiginde taranacak profil **@iriscibre** (Iris Cibre).
- Tek giris yine ayni: `py -3 99_BOT_ARSIV/kod/tara_guvenli.py --hesap iriscibre --days 7`
  - `--hesap` TARANACAK profili secer; X'e giris yapan hesabi DEGISTIRMEZ
    (giris hala @420cryptofarmer olmali, cikis kodu 4 kurali aynen gecerli).
- Veri tamamen ayri klasorde: `iriscibre/` (cekilen_tweetler.jsonl, medya/,
  iriscibre_hafiza_v1.md, tara_bookmark.json, alinti_bekleyen.jsonl).
  ekonomikocu arsivi ile ASLA karismaz.
- Bu hesapta 00-10 yukleme paketi URETILMEZ (mentor paketine ozgu). Ham arsiv +
  medya toplanir ve push edilir.
- **Arama akisi bu hesapta kullanilmaz**: X aramasi yanitlari indekslemiyor,
  @iriscibre icerigi neredeyse tamamen yanit. Profil `with_replies` akisi sart.
- Yuksek hacimli oldugu icin `stop-before` kendiliginden tetiklenmez; `--days N`
  verildiginde scroll ust siniri otomatik `max(20, N*5)` olur.
