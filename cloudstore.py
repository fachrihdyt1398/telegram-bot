import json
import os

import requests

CF_TOKEN = os.environ.get("CLOUDFLARE_KV_TOKEN", "")
CF_ACCOUNT = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
CF_NAMESPACE = os.environ.get("CLOUDFLARE_KV_NAMESPACE_ID", "")

_cache: dict = {}


def enabled() -> bool:
    return bool(CF_TOKEN and CF_ACCOUNT and CF_NAMESPACE)


def _base_url() -> str:
    return (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{CF_ACCOUNT}/storage/kv/namespaces/{CF_NAMESPACE}/values"
    )


def _headers() -> dict:
    return {"Authorization": f"Bearer {CF_TOKEN}"}


def get_json(key: str, default=None):
    if not enabled():
        return default
    if key in _cache:
        return _cache[key]
    try:
        resp = requests.get(f"{_base_url()}/{key}", headers=_headers(), timeout=8)
        if resp.status_code == 404:
            return default
        if not resp.ok:
            return default
        data = resp.json()
        _cache[key] = data
        return data
    except (requests.RequestException, ValueError):
        return default


def put_json(key: str, value) -> bool:
    if not enabled():
        return False
    _cache[key] = value
    try:
        resp = requests.put(
            f"{_base_url()}/{key}",
            headers=_headers(),
            data=json.dumps(value),
            timeout=8,
        )
        return resp.ok
    except requests.RequestException:
        return False
