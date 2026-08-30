# Telegram Bot Sederhana

Bot Telegram AI pintar menggunakan Python, dengan **multi-provider AI + fallback otomatis**. Siap di-deploy ke [Vercel](https://vercel.com) (gratis, tanpa kartu kredit) atau [Render](https://render.com).

Fitur:
- Chat langsung dengan AI (pesan biasa otomatis dijawab AI)
- `/ai <pertanyaan>` — tanya AI secara eksplisit
- `/model` — pilih model AI secara manual (tombol)
- `/providers` — cek status provider AI
- `/debug` — diagnostik jika AI error
- `/start`, `/help`
- Multi-provider: Gemini, Groq, Cloudflare Workers AI, OpenRouter — fallback otomatis **per model** sesuai urutan yang bisa diatur

## Mengatur Urutan Fallback (Per-Model)

Set env var `AI_MODELS` (format: `Provider:model`, dipisah koma). Model pertama = prioritas tertinggi. Jika kena limit, otomatis pindah ke model berikutnya.

```bash
AI_MODELS=OpenRouter:google/gemma-4-31b-it:free,Gemini:gemini-3.6-flash,Groq:llama-3.3-70b-versatile
```

- Tanpa `AI_MODELS`, urutan default: Gemini → Groq → Cloudflare → OpenRouter (hanya yang key-nya terisi).
- Model bisa diulang untuk provider yang sama, contoh: `OpenRouter:model-a:free,OpenRouter:model-b:free`.
- Di bot, perintah `/model` menampilkan semua model dengan tombol untuk memilih manual. Jika model yang dipilih kena limit, tetap fallback ke urutan di bawahnya.

## Daftar API Key (semua gratis)

| Provider | Cara dapat | Env var |
|---|---|---|
| Google Gemini | https://aistudio.google.com/apikey | `GEMINI_API_KEY` |
| Groq | https://console.groq.com/keys | `GROQ_API_KEY` |
| Cloudflare Workers AI | https://dash.cloudflare.com/profile/api-tokens | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` |
| OpenRouter | https://openrouter.ai/keys | `OPENROUTER_API_KEY` |

Cukup set minimal **satu** API key. Urutan fallback bisa diatur via env var `AI_PROVIDERS`, contoh: `Gemini,Groq,OpenRouter,Cloudflare`.

## Cara Menjalankan Lokal

1. Buat bot di Telegram lewat [@BotFather](https://t.me/BotFather) dan salin token-nya.
2. Install dependency:

   ```bash
   pip install -r requirements.txt
   ```

3. Set token:

   ```bash
   # Windows PowerShell
   $env:BOT_TOKEN="123456:ABC-DEF..."

   # Linux / macOS
   export BOT_TOKEN="123456:ABC-DEF..."
   ```

4. Jalankan (mode polling):

   ```bash
   python bot.py
   ```

5. Buka bot di Telegram dan kirim `/start`.

## Deploy ke Vercel (Gratis, Tanpa Kartu Kredit)

1. Pastikan repo ini sudah push ke GitHub.
2. Buka [Vercel](https://vercel.com) → **Add New Project** → import repo `telegram-bot`.
3. Di **Environment Variables**, tambahkan:
   - `BOT_TOKEN` — token dari @BotFather
4. Klik **Deploy**.
5. Setelah selesai, set webhook Telegram:

   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://nama-proyek.vercel.app/api/webhook"
   ```

   Atau jalankan script `set_webhook.py`:

   ```bash
   pip install -r requirements.txt
   $env:WEBHOOK_URL="https://nama-proyek.vercel.app"
   python set_webhook.py
   ```

6. Coba kirim `/start` ke bot di Telegram.

## Deploy ke Render

### Opsi 1: Blueprint (otomatis, via `render.yaml`)

1. Buat repo di GitHub dan push kode ini ke sana.
2. Masuk ke [Render Dashboard](https://dashboard.render.com).
3. Klik **New** → **Blueprint** → pilih repo `telegram-bot`.
4. Render akan mendeteksi `render.yaml` dan membuat service secara otomatis.
5. Set environment variable berikut di service:
   - `BOT_TOKEN` — token dari @BotFather
   - `WEBHOOK_URL` — URL service Render Anda, contoh `https://telegram-bot.onrender.com`

### Opsi 2: Manual (Web Service)

1. Masuk ke [Render Dashboard](https://dashboard.render.com).
2. Klik **New** → **Web Service** → connect repo GitHub Anda.
3. Isi:
   - **Name**: `telegram-bot`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
4. Pada **Environment**, tambahkan:
   - `BOT_TOKEN` — token dari @BotFather
   - `WEBHOOK_URL` — URL service Render Anda, contoh `https://telegram-bot.onrender.com`
5. Klik **Create Web Service** dan tunggu sampai status `Live`.

Setelah live, bot siap digunakan.
