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
