import os

import requests

REQUEST_TIMEOUT = 12

SYSTEM_PROMPT = (
    "Kamu adalah asisten AI yang profesional, ramah, dan membantu. "
    "Jawab dalam bahasa Indonesia, gunakan format Markdown untuk kode "
    "(blok kode dengan tiga backtick beserta nama bahasa jika relevan) "
    "dan bold untuk menekankan poin penting. Jawaban harus jelas, "
    "ringkas, dan rapi."
)

LAST_ERRORS: dict[str, str] = {}


def _text_from_result(data: dict, *paths: str) -> str | None:
    for path in paths:
        try:
            val = data
            for key in path.split("."):
                if key.isdigit():
                    val = val[int(key)]
                else:
                    val = val[key]
            if val and isinstance(val, str) and val.strip():
                return val.strip()
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return None


def _openai_messages(messages: list[dict]) -> list[dict]:
    return [{"role": "system", "content": SYSTEM_PROMPT}] + messages


def _record_error(name: str, detail: str) -> None:
    LAST_ERRORS[name] = detail


class GeminiProvider:
    name = "Gemini"

    def __init__(self) -> None:
        self.key = os.environ.get("GEMINI_API_KEY", "")
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    def ask(self, messages: list[dict]) -> str | None:
        if not self.key:
            _record_error(self.name, "API key kosong")
            return None
        try:
            contents = [
                {
                    "role": "model" if m["role"] == "assistant" else "user",
                    "parts": [{"text": m["content"]}],
                }
                for m in messages
            ]
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                params={"key": self.key},
                json={
                    "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                    "contents": contents,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                _record_error(self.name, "HTTP 429 (rate limit)")
                return None
            if not resp.ok:
                body = resp.text[:300]
                _record_error(self.name, f"HTTP {resp.status_code}: {body}")
                return None
            text = _text_from_result(
                resp.json(),
                "candidates.0.content.parts.0.text",
            )
            if not text:
                _record_error(self.name, "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(self.name, f"Request gagal: {exc}")
            return None


class GroqProvider:
    name = "Groq"

    def __init__(self) -> None:
        self.key = os.environ.get("GROQ_API_KEY", "")
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    def ask(self, messages: list[dict]) -> str | None:
        if not self.key:
            _record_error(self.name, "API key kosong")
            return None
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.key}"},
                json={
                    "model": self.model,
                    "messages": _openai_messages(messages),
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                _record_error(self.name, "HTTP 429 (rate limit)")
                return None
            if not resp.ok:
                body = resp.text[:300]
                _record_error(self.name, f"HTTP {resp.status_code}: {body}")
                return None
            text = _text_from_result(resp.json(), "choices.0.message.content")
            if not text:
                _record_error(self.name, "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(self.name, f"Request gagal: {exc}")
            return None


class CloudflareProvider:
    name = "Cloudflare"

    def __init__(self) -> None:
        self.token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        self.model = os.environ.get(
            "CLOUDFLARE_MODEL",
            "@cf/meta/llama-3.1-8b-instruct",
        )

    def ask(self, messages: list[dict]) -> str | None:
        if not self.token or not self.account_id:
            _record_error(self.name, "Token/Account ID kosong")
            return None
        try:
            resp = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"messages": _openai_messages(messages)},
                timeout=REQUEST_TIMEOUT,
            )
            if not resp.ok:
                body = resp.text[:300]
                _record_error(self.name, f"HTTP {resp.status_code}: {body}")
                return None
            text = _text_from_result(resp.json(), "result.response")
            if not text:
                _record_error(self.name, "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(self.name, f"Request gagal: {exc}")
            return None


class OpenRouterProvider:
    name = "OpenRouter"

    def __init__(self) -> None:
        self.key = os.environ.get("OPENROUTER_API_KEY", "")
        self.model = os.environ.get(
            "OPENROUTER_MODEL",
            "meta-llama/llama-3.1-8b-instruct:free",
        )

    def ask(self, messages: list[dict]) -> str | None:
        if not self.key:
            _record_error(self.name, "API key kosong")
            return None
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": _openai_messages(messages),
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                _record_error(self.name, "HTTP 429 (rate limit)")
                return None
            if not resp.ok:
                body = resp.text[:300]
                _record_error(self.name, f"HTTP {resp.status_code}: {body}")
                return None
            text = _text_from_result(resp.json(), "choices.0.message.content")
            if not text:
                _record_error(self.name, "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(self.name, f"Request gagal: {exc}")
            return None


ALL_PROVIDERS: list = [
    GeminiProvider(),
    GroqProvider(),
    CloudflareProvider(),
    OpenRouterProvider(),
]


def ask_ai(messages: list[dict]) -> tuple[str | None, str | None]:
    LAST_ERRORS.clear()
    order = os.environ.get("AI_PROVIDERS", "")
    if order:
        names = [n.strip() for n in order.split(",") if n.strip()]
        ordered = []
        for name in names:
            for p in ALL_PROVIDERS:
                if p.name.lower() == name.lower():
                    ordered.append(p)
                    break
        remaining = [p for p in ALL_PROVIDERS if p not in ordered]
        ordered = ordered + remaining
    else:
        ordered = ALL_PROVIDERS

    for provider in ordered:
        try:
            text = provider.ask(messages)
        except Exception as exc:
            text = None
            _record_error(provider.name, f"Eksepsi: {exc}")
        if text and text.strip():
            return text.strip(), provider.name
    return None, None


def get_last_errors() -> dict[str, str]:
    return dict(LAST_ERRORS)


def configured_providers() -> list[dict]:
    result = []
    for p in ALL_PROVIDERS:
        if p.name == "Gemini":
            ok = bool(p.key)
        elif p.name == "Groq":
            ok = bool(p.key)
        elif p.name == "Cloudflare":
            ok = bool(p.token and p.account_id)
        elif p.name == "OpenRouter":
            ok = bool(p.key)
        else:
            ok = False
        result.append({"name": p.name, "configured": ok})
    return result