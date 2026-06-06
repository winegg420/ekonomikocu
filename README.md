# ekonomikocu

@ekonomikocu X tweet arşivi, mentor paketi ve tarama botları.

**GitHub:** https://github.com/winegg420/ekonomikocu

## Claude / Gemini — dosyaları nereden alır?

Yerel klasör yerine **bu repoyu** kaynak kullan.

### Claude Project

1. Project → **Settings** → **Integrations** → **GitHub** bağla
2. Repo: `winegg420/ekonomikocu` seç (veya Project knowledge’a repo ekle)
3. Yükleme sırası: `00_OKU_YUKLEME_SIRASI.txt` ve `01_BURADAN_BASLA.md`
4. **Grafikler:** Project zip vision vermez — seviye sorusunda ilgili jpg’yi sohbete ekle (`09_GRAFIKLER_GEMINI/` veya `05_GRAFIKLER.zip`)

### Gemini

1. Repo’yu clone et veya GitHub’dan `08`, `09`, `10` dosyalarını indir
2. Sıra: `01`–`06`, sonra `08` → `09/` → `10`

## Yerel güncelleme

```bash
# Paket üret (00–10)
python 99_BOT_ARSIV/kod/claude_paket_olustur.py

# GitHub’a gönder
python 99_BOT_ARSIV/kod/github_guncelle.py
```

## Kök dosyalar (yükleme seti)

| Dosya | Açıklama |
|-------|----------|
| `01_BURADAN_BASLA.md` | Giriş |
| `02_MENTOR_REHBERI.md` | Mentor kuralları |
| `03_HAFIZA.md` | Kanıt defteri |
| `04_TWEETLER.jsonl` | Public tweetler |
| `05_GRAFIKLER.zip` | Grafikler (Claude) |
| `06_ANALIZ.md` | Analiz beyni |
| `07`–`10` | Abone + Gemini |

Ham veri: `cekilen_tweetler.jsonl`, `ekonomikocu_hafiza_v1.md`, `medya/`
