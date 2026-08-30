import os

import requests
from flask import Flask, request

from ai import ask_ai, configured_providers

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{TOKEN}"


def handle_message(text: str) -> str | None:
    if text == "/start":
        return (
            "Halo! Saya bot AI pintar. Kirim /help untuk melihat perintah.\n"
            "\nKamu bisa langsung chat denganku, atau pakai /ai <pertanyaan>."
        )
    if text == "/help":
        return (
            "Perintah yang tersedia:\n"
            "/start - mulai percakapan\n"
            "/help - bantuan\n"
            "/ai <pertanyaan> - tanya AI secara eksplisit\n"
            "/providers - cek status provider AI\n"
            "\nKamu juga bisa langsung kirim pesan dan aku akan menjawabnya dengan AI."
        )
    if text == "/providers":
        lines = ["Status provider AI:"]
        for p in configured_providers():
            status = "aktif" if p["configured"] else "belum diset"
            lines.append(f"- {p['name']}: {status}")
        return "\n".join(lines)
    if text.startswith("/ai "):
        prompt = text[4:].strip()
        if not prompt:
            return "Gunakan format: /ai <pertanyaan>"
        answer, provider = ask_ai(prompt)
        if answer:
            return f"🤖 ({provider})\n\n{answer}"
        return "Maaf, semua provider AI sedang tidak tersedia atau kehabisan kuota. Coba lagi nanti."
    if text.startswith("/"):
        return None
    answer, provider = ask_ai(text)
    if answer:
        return f"🤖 ({provider})\n\n{answer}"
    return "Maaf, AI sedang tidak tersedia saat ini. Coba lagi nanti."


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