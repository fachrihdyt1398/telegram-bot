import html
import os
import re

import requests
from flask import Flask, request

from ai import ask_ai, configured_providers, get_last_errors

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{TOKEN}"

MAX_HISTORY = 20

CONVERSATIONS: dict[int, list[dict]] = {}

MAIN_MENU = {
    "inline_keyboard": [
        [{"text": "💬 Mulai Chat", "callback_data": "menu_chat"}],
        [{"text": "🧠 Info Provider", "callback_data": "menu_providers"}],
        [{"text": "🔄 Reset Percakapan", "callback_data": "menu_reset"}],
        [{"text": "ℹ️ Bantuan", "callback_data": "menu_help"}],
    ]
}

CHAT_BUTTONS = {
    "inline_keyboard": [
        [
            {"text": "🔄 Tanya Lagi", "callback_data": "again"},
            {"text": "🗑 Reset", "callback_data": "menu_reset"},
        ]
    ]
}


def tg(method: str, **kwargs) -> dict:
    try:
        resp = requests.post(f"{API_BASE}/{method}", json=kwargs, timeout=10)
        return resp.json()
    except requests.RequestException:
        return {}


def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> int | None:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    result = tg("sendMessage", **payload)
    msg = result.get("result") or {}
    return msg.get("message_id")


def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict | None = None) -> None:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    tg("editMessageText", **payload)


def answer_callback(callback_id: str, text: str = "", alert: bool = False) -> None:
    tg("answerCallbackQuery", callback_query_id=callback_id, text=text, show_alert=alert)


def escape_html(text: str) -> str:
    return html.escape(text, quote=False)


def format_answer(text: str) -> str:
    code_blocks: list[str] = []

    def _save_code(code: str) -> str:
        code_blocks.append(f"<pre>{escape_html(code)}</pre>")
        return f"@@CODE{len(code_blocks) - 1}@@"

    text = re.sub(
        r"```([\w+.-]*)\n?([\s\S]*?)```",
        lambda m: _save_code(m.group(2)),
        text,
    )
    text = re.sub(
        r"`([^`\n]+)`",
        lambda m: _save_code(m.group(1)),
        text,
    )

    text = escape_html(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", text)

    for i, block in enumerate(code_blocks):
        text = text.replace(f"@@CODE{i}@@", block)
    return text


def get_history(chat_id: int) -> list[dict]:
    return CONVERSATIONS.get(chat_id, [])


def add_message(chat_id: int, role: str, content: str) -> None:
    history = CONVERSATIONS.setdefault(chat_id, [])
    history.append({"role": role, "content": content})
    CONVERSATIONS[chat_id] = history[-MAX_HISTORY:]


def reset_chat(chat_id: int) -> None:
    CONVERSATIONS.pop(chat_id, None)


def build_ai_reply(chat_id: int, prompt: str) -> str:
    add_message(chat_id, "user", prompt)
    answer, provider = ask_ai(get_history(chat_id))
    if answer:
        add_message(chat_id, "assistant", answer)
        return f"🤖 <b>{provider}</b>\n\n{format_answer(answer)}"
    return "😔 Maaf, semua provider AI sedang tidak tersedia atau kehabisan kuota. Coba lagi nanti."


def providers_text() -> str:
    lines = ["🧠 <b>Status Provider AI:</b>"]
    for p in configured_providers():
        status = "🟢 aktif" if p["configured"] else "🔴 belum diset"
        lines.append(f"• {p['name']}: {status}")
    return "\n".join(lines)


def help_text() -> str:
    return (
        "🤖 <b>fachri_AI</b> — asisten AI pintar\n\n"
        "💬 <b>Cara pakai:</b>\n"
        "• Langsung ketik pesan apa pun, aku akan menjawab dengan AI\n"
        "• /ai &lt;pertanyaan&gt; — tanya AI secara eksplisit\n"
        "• /providers — cek status provider\n"
        "• /reset — mulai percakapan baru\n\n"
        "✨ Aku punya <b>memori percakapan</b>, jadi kamu bisa lanjut diskusi "
        "tanpa mengulang konteks.\n"
        "🎨 Jawaban mendukung <b>bold</b>, <i>italic</i>, dan blok kode."
    )


def handle_message(msg: dict) -> None:
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if not text:
        send_message(chat_id, "Maaf, saya hanya bisa membaca pesan teks. ✍️")
        return

    if text == "/start":
        send_message(
            chat_id,
            "👋 Halo! Saya <b>fachri_AI</b>, asisten AI pintar kamu.\n\n"
            "Ketik pesan apa pun untuk memulai, atau pilih menu di bawah:",
            MAIN_MENU,
        )
        return

    if text == "/help":
        send_message(chat_id, help_text(), MAIN_MENU)
        return

    if text == "/providers":
        send_message(chat_id, providers_text())
        return

    if text == "/debug":
        errors = get_last_errors()
        if not errors:
            send_message(chat_id, "🔍 Belum ada percobaan AI. Kirim pesan dulu untuk test.")
            return
        lines = ["🐞 <b>Diagnostik AI (percobaan terakhir):</b>"]
        for name, err in errors.items():
            lines.append(f"• <b>{name}</b>: {escape_html(err)}")
        send_message(chat_id, "\n".join(lines))
        return

    if text in ("/reset", "/new"):
        reset_chat(chat_id)
        send_message(chat_id, "🧹 Percakapan sudah direset. Mulai dari awal yuk!")
        return

    if text.startswith("/ai "):
        prompt = text[4:].strip()
        if not prompt:
            send_message(chat_id, "Format: <code>/ai &lt;pertanyaan&gt;</code>")
            return
        tg("sendChatAction", chat_id=chat_id, action="typing")
        placeholder = send_message(chat_id, "⏳ <i>Sedang berpikir...</i>")
        reply = build_ai_reply(chat_id, prompt)
        if placeholder:
            edit_message(chat_id, placeholder, reply, CHAT_BUTTONS)
        return

    if text.startswith("/"):
        send_message(chat_id, "Perintah tidak dikenal. Ketik /help untuk bantuan.")
        return

    tg("sendChatAction", chat_id=chat_id, action="typing")
    placeholder = send_message(chat_id, "⏳ <i>Sedang berpikir...</i>")
    reply = build_ai_reply(chat_id, text)
    if placeholder:
        edit_message(chat_id, placeholder, reply, CHAT_BUTTONS)


def handle_callback(cq: dict) -> None:
    callback_id = cq["id"]
    chat_id = cq["message"]["chat"]["id"]
    message_id = cq["message"]["message_id"]
    data = cq.get("data", "")

    if data == "menu_chat":
        answer_callback(callback_id, "Ketik pesan apa pun untuk chat dengan AI! ✨")
        return

    if data == "menu_help":
        answer_callback(callback_id)
        edit_message(chat_id, message_id, help_text(), MAIN_MENU)
        return

    if data == "menu_providers":
        answer_callback(callback_id)
        edit_message(chat_id, message_id, providers_text(), MAIN_MENU)
        return

    if data == "menu_reset":
        reset_chat(chat_id)
        answer_callback(callback_id, "Percakapan direset ✅")
        edit_message(
            chat_id,
            message_id,
            "🧹 Percakapan sudah direset. Mulai dari awal yuk!",
            MAIN_MENU,
        )
        return

    if data == "again":
        history = get_history(chat_id)
        user_msgs = [m for m in history if m["role"] == "user"]
        if not user_msgs:
            answer_callback(callback_id, "Belum ada pertanyaan untuk diulang")
            return
        last = user_msgs[-1]["content"]
        answer_callback(callback_id, "Mengulang pertanyaan terakhir...")
        tg("sendChatAction", chat_id=chat_id, action="typing")
        placeholder = send_message(chat_id, "⏳ <i>Sedang berpikir...</i>")
        reply = build_ai_reply(chat_id, last)
        if placeholder:
            edit_message(chat_id, placeholder, reply, CHAT_BUTTONS)
        return


@app.route("/", methods=["POST"])
@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=True) or {}

    if "message" in update:
        handle_message(update["message"])
    elif "callback_query" in update:
        handle_callback(update["callback_query"])

    return "ok", 200