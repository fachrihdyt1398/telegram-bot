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


def _record_error(key: str, detail: str) -> None:
    LAST_ERRORS[key] = detail


class GeminiProvider:
    name = "Gemini"
    default_model = "gemini-3.6-flash"

    def __init__(self) -> None:
        self.key = os.environ.get("GEMINI_API_KEY", "")
        self.model = os.environ.get("GEMINI_MODEL", self.default_model)

    def ask(self, messages: list[dict], model: str | None = None) -> str | None:
        model = model or self.model
        if not self.key:
            _record_error(f"{self.name}:{model}", "API key kosong")
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
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": self.key},
                json={
                    "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                    "contents": contents,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                _record_error(f"{self.name}:{model}", "HTTP 429 (rate limit)")
                return None
            if not resp.ok:
                _record_error(f"{self.name}:{model}", f"HTTP {resp.status_code}: {resp.text[:200]}")
                return None
            text = _text_from_result(resp.json(), "candidates.0.content.parts.0.text")
            if not text:
                _record_error(f"{self.name}:{model}", "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(f"{self.name}:{model}", f"Request gagal: {exc}")
            return None


class GroqProvider:
    name = "Groq"
    default_model = "llama-3.3-70b-versatile"

    def __init__(self) -> None:
        self.key = os.environ.get("GROQ_API_KEY", "")
        self.model = os.environ.get("GROQ_MODEL", self.default_model)

    def ask(self, messages: list[dict], model: str | None = None) -> str | None:
        model = model or self.model
        if not self.key:
            _record_error(f"{self.name}:{model}", "API key kosong")
            return None
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.key}"},
                json={"model": model, "messages": _openai_messages(messages)},
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                _record_error(f"{self.name}:{model}", "HTTP 429 (rate limit)")
                return None
            if not resp.ok:
                _record_error(f"{self.name}:{model}", f"HTTP {resp.status_code}: {resp.text[:200]}")
                return None
            text = _text_from_result(resp.json(), "choices.0.message.content")
            if not text:
                _record_error(f"{self.name}:{model}", "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(f"{self.name}:{model}", f"Request gagal: {exc}")
            return None


class CloudflareProvider:
    name = "Cloudflare"
    default_model = "@cf/meta/llama-3.1-8b-instruct"

    def __init__(self) -> None:
        self.token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        self.model = os.environ.get("CLOUDFLARE_MODEL", self.default_model)

    def ask(self, messages: list[dict], model: str | None = None) -> str | None:
        model = model or self.model
        if not self.token or not self.account_id:
            _record_error(f"{self.name}:{model}", "Token/Account ID kosong")
            return None
        try:
            resp = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{model}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"messages": _openai_messages(messages)},
                timeout=REQUEST_TIMEOUT,
            )
            if not resp.ok:
                _record_error(f"{self.name}:{model}", f"HTTP {resp.status_code}: {resp.text[:200]}")
                return None
            text = _text_from_result(resp.json(), "result.response")
            if not text:
                _record_error(f"{self.name}:{model}", "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(f"{self.name}:{model}", f"Request gagal: {exc}")
            return None


class OpenRouterProvider:
    name = "OpenRouter"
    default_model = "google/gemma-4-31b-it:free"

    def __init__(self) -> None:
        self.key = os.environ.get("OPENROUTER_API_KEY", "")
        self.model = os.environ.get("OPENROUTER_MODEL", self.default_model)

    def ask(self, messages: list[dict], model: str | None = None) -> str | None:
        model = model or self.model
        if not self.key:
            _record_error(f"{self.name}:{model}", "API key kosong")
            return None
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "messages": _openai_messages(messages)},
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                _record_error(f"{self.name}:{model}", "HTTP 429 (rate limit)")
                return None
            if not resp.ok:
                _record_error(f"{self.name}:{model}", f"HTTP {resp.status_code}: {resp.text[:200]}")
                return None
            text = _text_from_result(resp.json(), "choices.0.message.content")
            if not text:
                _record_error(f"{self.name}:{model}", "Respons tanpa teks")
            return text
        except requests.RequestException as exc:
            _record_error(f"{self.name}:{model}", f"Request gagal: {exc}")
            return None


ALL_PROVIDERS: list = [
    GeminiProvider(),
    GroqProvider(),
    CloudflareProvider(),
    OpenRouterProvider(),
]

PROVIDER_BY_NAME: dict[str, object] = {p.name: p for p in ALL_PROVIDERS}


def _is_configured(p: object) -> bool:
    if p.name == "Gemini":
        return bool(p.key)
    if p.name == "Groq":
        return bool(p.key)
    if p.name == "Cloudflare":
        return bool(p.token and p.account_id)
    if p.name == "OpenRouter":
        return bool(p.key)
    return False


def _normalize_model_key(provider: str, model: str) -> str:
    return f"{provider}:{model}"


def get_model_list() -> list[tuple[object, str | None]]:
    env = os.environ.get("AI_MODELS", "").strip()
    if env:
        entries = []
        for item in env.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                prov, _, mdl = item.partition(":")
                prov = prov.strip()
                mdl = mdl.strip() or None
                if prov in PROVIDER_BY_NAME:
                    entries.append((PROVIDER_BY_NAME[prov], mdl))
                else:
                    _record_error("konfigurasi", f"Provider '{prov}' tidak dikenal (di AI_MODELS)")
            else:
                if item in PROVIDER_BY_NAME:
                    entries.append((PROVIDER_BY_NAME[item], None))
                else:
                    _record_error("konfigurasi", f"Provider '{item}' tidak dikenal (di AI_MODELS)")
        if entries:
            return entries

    order_env = os.environ.get("AI_PROVIDERS", "")
    if order_env:
        names = [n.strip() for n in order_env.split(",") if n.strip()]
        used = set()
        entries = []
        for n in names:
            if n in PROVIDER_BY_NAME and n not in used:
                entries.append((PROVIDER_BY_NAME[n], None))
                used.add(n)
        for p in ALL_PROVIDERS:
            if p.name not in used:
                entries.append((p, None))
        return entries

    return [(p, None) for p in ALL_PROVIDERS]


def available_models() -> list[dict]:
    result = []
    for idx, (p, model) in enumerate(get_model_list()):
        m = model or p.model
        result.append({
            "id": idx,
            "key": _normalize_model_key(p.name, m),
            "provider": p.name,
            "model": m,
            "configured": _is_configured(p),
        })
    return result


def ask_ai(
    messages: list[dict],
    preferred_key: str | None = None,
    order: list[str] | None = None,
) -> tuple[str | None, str | None, str | None]:
    LAST_ERRORS.clear()
    entries = get_model_list()

    if order:
        by_key = {}
        remaining = []
        for p, model in entries:
            m = model or p.model
            key = _normalize_model_key(p.name, m)
            if key in order:
                by_key[key] = (p, model)
            else:
                remaining.append((p, model))
        ordered = [by_key[k] for k in order if k in by_key]
        entries = ordered + remaining

    if preferred_key:
        front = []
        rest = []
        for p, model in entries:
            m = model or p.model
            if _normalize_model_key(p.name, m) == preferred_key:
                front.append((p, model))
            else:
                rest.append((p, model))
        entries = front + rest

    for p, model in entries:
        m = model or p.model
        key = _normalize_model_key(p.name, m)
        try:
            text = p.ask(messages, model=model)
        except Exception as exc:
            text = None
            _record_error(key, f"Eksepsi: {exc}")
        if text and text.strip():
            return text.strip(), p.name, key
        if key not in LAST_ERRORS:
            _record_error(key, "Tidak ada respons")
    return None, None, None


def get_last_errors() -> dict[str, str]:
    return dict(LAST_ERRORS)


def clear_last_errors() -> None:
    LAST_ERRORS.clear()


def configured_providers() -> list[dict]:
    result = []
    for p in ALL_PROVIDERS:
        result.append({"name": p.name, "configured": _is_configured(p)})
    return result