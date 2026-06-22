# OTOMASYON PLANI — Portföy-Farkındalı Uyarı Sistemi

> **Durum: TASLAK (mimari notu).** Bu dosya yalnızca ileride kurulacak otomasyonun
> planıdır; içinde çalışan kod/cron tanımı YOKTUR. Kod yazımı ayrı bir faza bırakılmıştır.

## 1. Amaç
Birkaç saatte bir otomatik olarak: en güncel veriyi topla → MagicMA seviyelerini güncelle →
portföye göre uyarı/rapor üret → çıktıyı erişilebilir bir yere (panel/bildirim) akıt.
Hedef: bir Koç seviyesine / MagicMA çizgisine yaklaşınca veya kâr/zarar eşiği geçilince
kullanıcının **elle bakmadan** haberdar olması.

## 2. Zincir (sıra önemli)
Her tur şu sırayla çalışır (önceki adım veriyi tazeler, sonraki onu kullanır):

1. **Tarama** — `python 99_BOT_ARSIV/kod/tara_guvenli.py`
   - Yeni tweet/alıntı/flood + abone_ozel etiketleri güncellenir.
   - Çıkış kodu 4 = yanlış/eksik hesap → tur durur, bildirim "giriş gerekli".
2. **MagicMA tarama** — TradingView tabanlı seviye çekimi (`magicma_yakinlik.py` akışı).
   - `99_BOT_ARSIV/kod/magicma_ham.jsonl` sembol başına en güncel ts ile tazelenir.
   - Önkoşul: 9222'li Chrome + TradingView sekmesi (indikatör yüklü, giriş yapılı).
3. **Portföy raporu** — `python 99_BOT_ARSIV/kod/portfoy_rapor.py --out rapor_son.md`
   - Canlı fiyat + kâr/zarar + en yakın Koç seviyesi + en yakın MagicMA çizgisi + uyarılar.
   - `portfoy_ozel.json` boşsa "veri yok" der, tur hatasız tamamlanır.

## 3. Zamanlama (cron)
- Önerilen: **2–4 saatte bir** (piyasa saatlerinde sık, gece seyrek).
- Linux cron örneği (KAVRAMSAL, kurulunca yazılacak):
  - `0 */3 * * *` → bir kabuk scripti (`otomasyon_tur.sh`) zinciri sırayla çağırır.
- Windows tarafında alternatif: Görev Zamanlayıcı (Task Scheduler) ile aynı kabuk/PowerShell sarmalayıcı.
- Her adım **bağımsız try-catch / exit-code kontrolü**; bir adım düşse tur loglar ve devam/iptal kararı verir.

## 4. Çıktının akışı (panel / bildirim)
Seçenekler (ileride biri seçilecek):
- **Bildirim (push):** Telegram bot veya e-posta — yalnızca **UYARILAR** bölümü tetiklenince gönder
  (gürültüyü azaltmak için: uyarı yoksa mesaj atma).
- **Statik panel:** `rapor_son.md` → HTML'e çevrilip basit bir sayfada yayınlanır
  (yerel sunucu veya GitHub Pages — ama **portföy verisi gizli**, public panele konmaz).
- **Hibrit:** Tam rapor gizli/yerel panelde; sadece uyarı özeti push bildirimde.

## 5. Gizlilik (kritik)
- `portfoy_ozel.json` **asla** commit/push edilmez (zaten `.gitignore`'da) ve **public panele konmaz**.
- Sunucuda secret/izinli dizinde tutulur; rapor çıktısı da kişiseldir → kimliği doğrulanmış erişim.
- `portfoy_ornek.json` yalnızca demo/test içindir (sahte veri).

## 6. Bağımlılıklar / dayanıklılık
- Tarama ve MagicMA adımları **çalışan Chrome (port 9222)** ister; otomasyon önce CDP'yi kontrol etmeli,
  kapalıysa Chrome'u headless/off-screen başlatmalı (bkz. mevcut CHROME_X akışı).
- Fiyat kaynağı: kripto canlı (Binance REST), diğerleri MagicMA son tarama fiyatı (fallback).
  Canlı kaynak eklemek istenirse (BIST/emtia) sağlayıcı + API anahtarı gerekir.
- Tüm ağ çağrıları timeout + try-catch; bir veri kaynağı düşse rapor yine üretilmeli ("alınamadı" notu).

## 7. Sonraki adım (kod fazı — henüz YAPILMADI)
- `otomasyon_tur.sh` / PowerShell sarmalayıcı (zincir + log + exit-code).
- Bildirim entegrasyonu (Telegram/e-posta) — token'lar secret olarak.
- Opsiyonel HTML panel üreteci.
- Cron/Task Scheduler kurulumu + sağlık izleme (tur düşerse haber ver).
