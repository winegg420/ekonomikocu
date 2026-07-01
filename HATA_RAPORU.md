# HATA RAPORU — @ekonomikocu Tarama Botu Dayanıklılık İncelemesi

**Tarih:** 2026-07-02
**Kapsam:** tweet_tara.py, alinti_flood_tara.py, abone_tamamla.py, tara_guncel_yeni.py, alinti_common.py, tara_nav.py + geçmiş loglar

---

## 1. Bulgular (log kanıtlarıyla)

### T1 — Tarayıcı/sayfa kopması kurtarması YOK → yüzlerce ID boşa "atlandı" ✅ DOĞRULANDI (en büyük kayıp)

| Log | "has been closed" | "Connection closed (driver)" dahil Timeout izi | Toplam "atlandi/Hata" |
|---|---|---|---|
| alinti_flood_tara_tum.log | 360 | 363 | 450 |
| alinti_flood_tara_log.txt | 97 | 97 | (97, "Hata (id)" olarak) |
| **Toplam** | **457** | **~462** | — |

Mentörün "462 timeout izi" tespiti birebir doğrulandı: izlerin tamamı iki tip
anlık ölü-bağlantı hatası — `Target page, context or browser has been closed`
ve `Connection closed while reading from the driver`. Loglarda **aynı saniye
içinde** onlarca ID art arda düşüyor (ör. `alinti_flood_tara_tum.log`
satır 242-616, hepsi `22:58:01`): bağlantı bir kez ölüyor, döngü ise her
kalan ID için anında hata alıp "atlandı" yazıyor.

**Kök neden (dosya/satır):**
- `tweet_tara.py:1998` — `refill_locked_since` except bloğu TÜM hataları yutup
  `continue` ediyor; bağlantı ölünce kalan yüzlerce abone ID'si boşa geziliyor
  ("400/400 | +0" tablosu buradan).
- `tweet_tara.py:2081` — `crawl_thread` except: hata yutulur, 0 döner;
  `finish_threads_loop` (2252) sonraki ID'ye geçer. Üstelik `note_thread_result`
  ölü bağlantı denemesini de deneme sayar → thread'ler YANLIŞLIKLA
  "erişilemedi" işaretlenebilir (veri kaybı riski).
- `tweet_tara.py:2189` — `crawl_quote` except: aynı desen; `flush_quotes` devam eder.
- `alinti_flood_tara.py:364` (keşif) ve `:502` (ana kuyruk) — "closed" görünce
  artık **duruyor** (7 Haziran düzeltmesi), fakat yeniden bağlanma yok: kalan
  kuyruk sonraki manuel çalıştırmaya kalıyor.
- Hiçbir yerde `connect_over_cdp`'ye **yeniden bağlanma** yok; CDP kurulumu tek
  seferlik (`tweet_tara.py:2542, 2681`; `alinti_flood_tara.py:467`;
  `abone_tamamla.py:133`).

### T2 — Rate-limit backoff YOK ✅ DOĞRULANDI (kısmen mevcut, yetersiz)

- Loglarda "rate limit"/"Too Many Requests" metni geçmiyor (X bunu UI'da
  "Something went wrong / Try again" olarak gösteriyor; `x_clear_error`
  körlemesine Retry'a tıklayıp devam ediyor → sınıra daha çok çarpma).
- Mevcut tek mekanizma `recover_backoff_ms` (`tweet_tara.py:2869`):
  3 sn → 15 sn tavan. Gerçek rate-limit için çok kısa; ayrıca sayfa
  metninde rate-limit tespiti hiç yok.
- scratch_tara_out.log: 21 "Kurtarma", 16 "splash" — kurtarmalar kısa
  aralıklarla üst üste geliyor, aradaki bekleme yetersiz.

### T3 — Boşa-tur early-exit sınırı sabit ve yüksek ✅ DOĞRULANDI

- `tweet_tara.py:3183` — `stale >= 35` (fast_period'da 12) sabit gömülü.
  120 scroll'luk güncel taramada yeni kayıt gelmese bile tur 35 boş scroll
  (~35 × 5 sn pause + kurtarmalar ≈ 4-6 dk) sürüyor. Ayarlanabilir değil.

### T4 — Sabit uzun wait_for_timeout ✅ DOĞRULANDI

- tweet_tara.py'de 69 adet `wait_for_timeout`. En maliyetlileri navigasyon
  sonrası kör 4000-8000 ms uykular (ör. 321, 354, 382, 1702, 2784, 2811,
  3111, 3135, 3156, 3163, 3180): içerik 1 sn'de gelse bile tam süre bekleniyor.

---

## 2. Yapılan düzeltmeler (Faz 1)

**Yeni modül: `99_BOT_ARSIV/kod/tarayici_saglik.py`** — tüm ortak dayanıklılık
yardımcıları tek yerde (kopyala-yapıştır yok):

- `baglanti_hatasi(err)` — "closed / not connected / disconnected / driver"
  izlerinden ölü bağlantı tespiti.
- `sayfa_canli(page)` — hızlı sağlık kontrolü (`is_closed` + `evaluate("1")`).
- `iyilestir(page, home_url=..., etiket=...)` — sayfa canlıysa aynen döndürür;
  değilse (1) mevcut context'ten sağlam sekme, (2) 127.0.0.1:9222'ye yeniden
  `connect_over_cdp` + `contexts[0]` (driver da öldüyse taze Playwright
  sürücüsüyle). Yeni sayfa `bind_safe_page` ile korunur. Başarısızsa `None`.
- `RateLimitBackoff` — 30→60→120→240 sn üstel, 300 sn tavan; `sifirla()` ile reset.
- `rate_limit_var(page)` — gövde metninde rate-limit izi arar
  ("rate limit", "too many requests", "çok fazla istek", "daha sonra tekrar dene").
- `icerik_bekle(page, max_ms, selector)` — kör uyku yerine koşullu bekleme:
  tweet makalesi görünür görünmez erken döner, üst sınır eski süreyle AYNI
  (davranış bozulmaz, sadece hızlanır).

**Entegrasyonlar (minimal dokunuş):**

| Dosya | Değişiklik |
|---|---|
| `tweet_tara.py` | `refill_locked_since`: kopma → `iyilestir` + kaldığı ID'den devam (state korunur); iyileşmezse turu kes. Boş metin turlarında `rate_limit_var` → backoff. |
| `tweet_tara.py` | Ana scroll döngüsü except'i: "closed" → önce `iyilestir`, olmazsa eski davranış (kaydet + çık). |
| `tweet_tara.py` | `finish_threads_loop` / `finish_quotes_loop`: her iş öncesi `sayfa_canli` kontrolü, kopmuşsa yeniden bağlan; iyileşmezse döngüyü kes (yanlış "erişilemedi" işaretleme durur). |
| `tweet_tara.py` | `feed_recover` içinde `rate_limit_var` → `RateLimitBackoff` (mevcut `recover_backoff_ms` korunndu, silinmedi). |
| `tweet_tara.py` | `--bos-tur-limit` (varsayılan 25): `stale >= 35` sabiti parametreye bağlandı. |
| `tweet_tara.py` | ~12 kör `wait_for_timeout(4000-6000)` → `icerik_bekle` (yalnızca navigasyon-sonrası güvenli yerler). |
| `alinti_flood_tara.py` | Ana kuyruk + keşif: kopma → `iyilestir`, iş kuyruğa geri konur, KALDIĞI ID'den devam; iyileşmezse eski davranış (durdur). "Boş sayfa" tekrarlarında rate-limit backoff. |
| `abone_tamamla.py` | Tur arası `sayfa_canli` kontrolü + `iyilestir`. |

**Korunanlar:** `fix_x_crash`, `RETRY_JS`, `wait_for_cdp_port`, `StallWatchdog`,
tara_guvenli.py giriş sözleşmesi (exit 4/5), abone_etiketle.py'ye dokunulmadı.

---

## 3. Bilerek DOKUNULMAYANLAR + açık sorular

1. **Scroll arası `--pause 5000`** (tara_guncel_yeni.py çağrısı): insan-hızı
   taklidi ve rate-limit'ten kaçınma amaçlı görünüyor — kısaltılmadı.
   *Soru: 5000 → 3500 denemek ister misin? Rate-limit riski artabilir.*
2. **`goto_status` içindeki 1800-2200 ms pause** (tweet_tara.py:1784): SPA
   yerleşme beklemesi; selector-tabanlı bekleme burada alıntı kartlarının geç
   render'ında eksik veri riski taşır — dokunulmadı.
3. **`page.wait_for_timeout(15_000)`** (2828, CDP'siz + girişsiz yol): nadiren
   çalışan eski yol — dokunulmadı.
4. **Eski `iyilestir` sonrası sync_playwright çıkışı:** driver öldüğünde taze
   sürücüyle devam ediliyor; ana `with sync_playwright()` bloğu kapanırken ölü
   sürücü nadiren uyarı verebilir (veri kaybı yok — tüm kayıtlar finally
   bloklarında diske yazıldıktan sonra). İzlenmeli.
5. `alinti_flood_tara.py` "429" log eşleşmeleri tweet ID'lerindeki rakam
   dizileri çıktı (gerçek HTTP 429 izi yok) — rate-limit tespiti bu yüzden
   sayfa metninden yapılıyor, HTTP kodundan değil.
