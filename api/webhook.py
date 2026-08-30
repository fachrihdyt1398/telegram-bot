import os

import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{TOKEN}"


def handle_message(text: str) -> str | None:
    if text == "/start":
        return (
            "Halo! Saya bot Telegram sederhana. Kirim /help untuk melihat perintah."
        )
    if text == "/help":
        return (
            "Perintah yang tersedia:\n"
            "/start - mulai percakapan\n"
            "/help - bantuan\n"
            "\nKamu juga bisa mengirim pesan teks apa pun dan aku akan membalasnya."
        )
    if text.startswith("/"):
        return None
    return f"Kamu bilang: {text}"


@app.route("/", methods=["POST"])
@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=True) or {}
    message = update.get("message") or {}
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if chat_id:
        reply = handle_message(text)
        if reply:
            try:
                requests.post(
                    f"{API_BASE}/sendMessage",
                    json={"chat_id": chat_id, "text": reply},
                    timeout=5,
                )
            except Exception:
                pass

    return "ok", 200