import os
import sys

import requests

TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
SECRET = os.environ.get("WEBHOOK_SECRET", "")

if not TOKEN:
    print("BOT_TOKEN tidak diatur. Set environment variable BOT_TOKEN.")
    sys.exit(1)

if not WEBHOOK_URL:
    print("WEBHOOK_URL tidak diatur. Contoh: https://telegram-bot-omega-sand.vercel.app")
    sys.exit(1)

url = WEBHOOK_URL.rstrip("/") + "/api/webhook"

payload = {"url": url, "drop_pending_updates": False}
if SECRET:
    payload["secret_token"] = SECRET
else:
    print("PERINGATAN: WEBHOOK_SECRET kosong — webhook tidak tergembok!")

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/setWebhook",
    json=payload,
    timeout=15,
)

print(f"Target webhook: {url}")
if resp.ok:
    print(resp.json())
else:
    print(f"Gagal: {resp.status_code}")
    print(resp.text)
