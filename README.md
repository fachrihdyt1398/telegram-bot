# Telegram Bot Sederhana

Bot Telegram sederhana menggunakan Python (`python-telegram-bot`), siap di-deploy ke [Render](https://render.com).

Fitur:
- `/start` — memulai percakapan
- `/help` — daftar perintah
- Echo — membalas pesan teks apa pun

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
