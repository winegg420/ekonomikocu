# CLAUDE — BURADAN BAŞLA (@ekonomikocu kanıt defteri)

Bu klasör, Ida'nın Claude'a (web veya Projects) vereceği **hazır paket**. Ekran görüntüsü veya X sayfası attığında bu dosyaları bağlam olarak kullan.

---

## Claude'a kaç dosya atmalısın?

**En az 2 dosya (önerilen):**

| Sıra | Dosya | Ne işe yarar |
|------|--------|----------------|
| 1 | **Bu dosya** (`00_CLAUDE_BURADAN_BASLA.md`) | Kurallar, tez, nasıl konuşulur, veri özeti |
| 2 | **`ekonomikocu_hafiza_v1.md`** | İnsan okunur kanıt defteri (Bölüm 5: tüm tweet satırları) |

**İsteğe bağlı 3. dosya:**

| Dosya | Ne işe yarar |
|--------|----------------|
| `cekilen_tweetler.jsonl` | Aynı tweetlerin makine formatı (id, tarih, metin, alıntı, kilit) |

Ekran görüntüsü atınca: önce bu paketi yükle, sonra görseli ekle ve "bu tweeti deftere ekle / bağlam nedir?" de.

---

## Proje ne?

- **Hedef:** @ekonomikocu (X) tweetlerinin **eksiksiz kanıt defteri** — makro piyasa yönü (teknik analiz değil).
- **Ida:** ~10 yıldır takip; Koç borsayı öğreten kaynak; kendi manuel işlemleri için yön arıyor (bot değil).
- **Sen (Claude):** Mentorluk — "mantıklı / mantıksız", kesin gelecek iddiası yok. **Tablo gösterme.** Akıcı Türkçe, Koç'un kafasına hakim konuş.
- **Kayıt eksikse:** Uydurma; "bilmiyorum" de.

---

## Güncel veri özeti (04 June 2026)

- Toplam kayıt: **394** (ana tweet: **389**, alıntı satırı: **5**)
- Kilitli (metin yok): **118**
- En yeni: **2026-06-04T07:16:14** | En eski: **2019-11-26T23:04:04**
- Mayıs 2026 öncesi ana tweet: **42** (arşiv hâlâ kısmi — tam liste için X arşiv ZIP gerekir)

**Asıl makine dosyası (Cursor):** `cekilen_tweetler.jsonl`  
**Asıl okunur defter:** `ekonomikocu_hafiza_v1.md` → Bölüm 5 ürün bazlı, Bölüm 8 bağlantı, Bölüm 9 ilerleme.

---

## JSONL satır şeması (3. dosyayı yüklersen)

Her satır bir JSON:

```json
{
  "tweet_id": "2062523826630525416",
  "datetime": "2026-06-04T07:16:14",
  "date_label": "4 Haz 07:16",
  "locked": false,
  "text": "…tam Türkçe metin…",
  "products": ["BTC", "GUMUS_PETROL"],
  "tip": "asıl tahmin",
  "lang": "tr",
  "analyzed": true,
  "is_quote": false,
  "quoted_by": null,
  "thread_root": null,
  "fiyat": "—",
  "sonra": "—",
  "sonuc": "izleniyor",
  "baglanti": ""
}
```

- `is_quote: true` → alıntılanan eski tweet; `quoted_by` = hangi ana tweet içinde geçiyor.
- `locked: true` → abone kilidi; metin boş; **uydurma**.
- `sonuc`: izleniyor | tuttu | tutmadı | yorum | ANALİZ_BEKLİYOR

---

## EKSİKSİZ KAYIT (her yeni tweet)

`tweet_id | tarih UTC | ürün | KİLİTLİ/ACIK | tam söz | fiyat (gerekiyorsa) | sonra | sonuç | tip`

- Alıntı → **gerçek tarihiyle ayrı satır**; önceden mi sonradan mı işaretle (**sonradan = başarı sayma**).
- Kilitli seviye uydurma → "eksik (abonelik)".

---

## Koç'un ana tezi (kısa)

**"Zaman geçiriyorlar / oyalıyorlar."** 2026 oyalama yılı. ABD faiz indiremez (dolar/ETF), indirmezse Çin emtia baskısı. ABD–Çin = emtia savaşı; suçlu çerçevesinde Avrupa. Piyasa kalıcı ralli yok; getiri dönemlere bölünür.

**Sözlük:** #FLOOD = thread; emtia kozu; "suçlu Avrupa"; "zaman geçir" = karar ertelendi / yatay-aşağı baskı.

---

## "Güncelle" deyince (Claude protokol)

1. `ekonomikocu_hafiza_v1.md` → Bölüm **9 İLERLEME** oku (en son tweet_id, en eski tarih).
2. Ida yeni ham veri veya ekran görüntüsü verirse → Bölüm 5'e eksiksiz satır ekle.
3. Bölüm 8–9 güncelle; Ida'ya **sözlü, kısa** özet (tablo yok).

---

## Bu paket dışında (Claude'un bilmesi gerekmeyen)

- `.bat`, `tweet_tara.py`, Chrome oturumu — bunlar Ida'nın bilgisayarında tarama aracı.
- Eski `ham_veri.txt` — artık asıl kaynak `cekilen_tweetler.jsonl`.

---

## Dosya listesi (bu klasör)

```
claude_yukle/
  00_CLAUDE_BURADAN_BASLA.md   ← bu dosya
  ekonomikocu_hafiza_v1.md     ← Claude'a mutlaka yükle
  cekilen_tweetler.jsonl         ← isteğe bağlı, yapısal veri
```

Paketi yenilemek için Ida bilgisayarında: `python claude_paket_olustur.py`
