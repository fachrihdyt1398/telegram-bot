import os
import sys

import requests

TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

if not TOKEN:
    print("BOT_TOKEN tidak diatur. Set environment variable BOT_TOKEN.")
    sys.exit(1)

if not WEBHOOK_URL:
    print("WEBHOOK_URL tidak diatur. Contoh: https://nama-proyek.vercel.app")
    sys.exit(1)

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/setWebhook",
    data={"url": WEBHOOK_URL},
    timeout=10,
)

if resp.ok:
    print(f"Webhook berhasil diatur ke: {WEBHOOK_URL}")
    print(resp.json())
else:
    print(f"Gagal: {resp.status_code}")
    print(resp.text)