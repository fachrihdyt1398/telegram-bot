import os

import requests

REQUEST_TIMEOUT = 12


def _text_from_result(data: dict, *paths: str) -> str | None:
    for path in paths:
        try:
            parts = path.split(".")
            val = data
            for key in parts:
                if key.isdigit():
                    val = val[int(key)]
                else:
                    val = val[key]
            if val and isinstance(val, str) and val.strip():
                return val.strip()
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return None


class GeminiProvider:
    name = "Gemini"

    def __init__(self) -> None:
        self.key = os.environ.get("GEMINI_API_KEY", "")
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    def ask(self, prompt: str) -> str | None:
        if not self.key:
            return None
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                params={"key": self.key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                return None
            if not resp.ok:
                return None
            return _text_from_result(
                resp.json(),
                "candidates.0.content.parts.0.text",
            )
        except requests.RequestException:
            return None


class GroqProvider:
    name = "Groq"

    def __init__(self) -> None:
        self.key = os.environ.get("GROQ_API_KEY", "")
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    def ask(self, prompt: str) -> str | None:
        if not self.key:
            return None
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                return None
            if not resp.ok:
                return None
            return _text_from_result(
                resp.json(), "choices.0.message.content"
            )
        except requests.RequestException:
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

    def ask(self, prompt: str) -> str | None:
        if not self.token or not self.account_id:
            return None
        try:
            resp = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"messages": [{"role": "user", "content": prompt}]},
                timeout=REQUEST_TIMEOUT,
            )
            if not resp.ok:
                return None
            return _text_from_result(resp.json(), "result.response")
        except requests.RequestException:
            return None


class OpenRouterProvider:
    name = "OpenRouter"

    def __init__(self) -> None:
        self.key = os.environ.get("OPENROUTER_API_KEY", "")
        self.model = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    def ask(self, prompt: str) -> str | None:
        if not self.key:
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
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                return None
            if not resp.ok:
                return None
            return _text_from_result(
                resp.json(), "choices.0.message.content"
            )
        except requests.RequestException:
            return None


ALL_PROVIDERS: list = [GeminiProvider(), GroqProvider(), CloudflareProvider(), OpenRouterProvider()]


def ask_ai(prompt: str) -> tuple[str | None, str | None]:
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
            text = provider.ask(prompt)
        except Exception:
            text = None
        if text and text.strip():
            return text.strip(), provider.name
    return None, None


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