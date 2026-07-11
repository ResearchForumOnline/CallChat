#!/usr/bin/env python3
"""Owner-managed AI and IonQ provider control for CallChat.

Keys are kept server-side in an owner-only state file. Provider calls never
receive ZMath passphrases, pattern images, Matrix keys, protected-message or
file plaintext, or ZME1 payloads from this module's assurance and receipt paths.
"""

from __future__ import annotations

import copy
import json
import os
import re
import secrets
import stat
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROVIDER_STORE = Path(
    os.getenv(
        "CALLCHAT_PROVIDER_STORE",
        "/var/lib/callchat-openzero-bridge/provider-secrets.json",
    )
)
PROVIDER_TIMEOUT = float(os.getenv("CALLCHAT_PROVIDER_TIMEOUT", "20"))
PROVIDER_LOCK = threading.RLock()

AI_PROVIDER_IDS = {"local", "openai", "groq"}
IONQ_BACKENDS = {
    "simulator",
    "qpu.aria-1",
    "qpu.aria-2",
    "qpu.forte-1",
    "qpu.forte-enterprise-1",
    "qpu.forte-enterprise-2",
    "qpu.forte-enterprise-3",
}
MODEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")
PROVIDER_ENDPOINTS = {
    "openai": {
        "chat": "https://api.openai.com/v1/chat/completions",
        "models": "https://api.openai.com/v1/models",
    },
    "groq": {
        "chat": "https://api.groq.com/openai/v1/chat/completions",
        "models": "https://api.groq.com/openai/v1/models",
    },
    "ionq": {
        "jobs": "https://api.ionq.co/v0.4/jobs",
        "whoami": "https://api.ionq.co/v0.4/whoami",
        "backends": "https://api.ionq.co/v0.4/backends",
    },
}
PROVIDER_ENV_KEYS = {
    "openai": ("CALLCHAT_OPENAI_API_KEY", "OPENAI_API_KEY"),
    "groq": ("CALLCHAT_GROQ_API_KEY", "GROQ_API_KEY"),
    "ionq": ("CALLCHAT_IONQ_API_KEY", "IONQ_API_KEY"),
}


class ProviderConfigError(ValueError):
    """Raised when an owner provider update is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_provider_state() -> dict[str, Any]:
    return {
        "version": 1,
        "active_ai_provider": "local",
        "updated_at": "",
        "providers": {
            "openai": {
                "api_key": "",
                "enabled": False,
                "model": "gpt-5.5",
                "updated_at": "",
            },
            "groq": {
                "api_key": "",
                "enabled": False,
                "model": "qwen/qwen3-32b",
                "updated_at": "",
            },
            "ionq": {
                "api_key": "",
                "enabled": False,
                "backend": "simulator",
                "allow_paid_qpu": False,
                "updated_at": "",
            },
        },
    }


def valid_model(value: Any) -> str:
    model = str(value or "").strip()
    if not MODEL_PATTERN.fullmatch(model):
        raise ProviderConfigError("Choose a valid provider model identifier.")
    return model


def valid_api_key(value: Any) -> str:
    key = str(value or "").strip()
    if not 16 <= len(key) <= 512:
        raise ProviderConfigError("API keys must be between 16 and 512 characters.")
    if any(ord(char) < 33 or ord(char) > 126 for char in key):
        raise ProviderConfigError("API keys must contain printable non-space characters only.")
    return key


def environment_key(provider: str) -> str:
    for name in PROVIDER_ENV_KEYS.get(provider, ()):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def load_provider_state(path: Path | None = None) -> dict[str, Any]:
    store = path or PROVIDER_STORE
    state = default_provider_state()
    with PROVIDER_LOCK:
        try:
            raw = json.loads(store.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return state
        except (OSError, json.JSONDecodeError):
            return state

    if not isinstance(raw, dict) or raw.get("version") != 1:
        return state
    active = str(raw.get("active_ai_provider") or "local")
    if active in AI_PROVIDER_IDS:
        state["active_ai_provider"] = active
    state["updated_at"] = str(raw.get("updated_at") or "")[:40]
    raw_providers = raw.get("providers")
    if not isinstance(raw_providers, dict):
        return state

    for provider in ("openai", "groq", "ionq"):
        incoming = raw_providers.get(provider)
        if not isinstance(incoming, dict):
            continue
        target = state["providers"][provider]
        key = str(incoming.get("api_key") or "").strip()
        if key:
            try:
                target["api_key"] = valid_api_key(key)
            except ProviderConfigError:
                target["api_key"] = ""
        target["enabled"] = bool(incoming.get("enabled"))
        target["updated_at"] = str(incoming.get("updated_at") or "")[:40]
        if provider in {"openai", "groq"}:
            try:
                target["model"] = valid_model(incoming.get("model") or target["model"])
            except ProviderConfigError:
                pass
        else:
            backend = str(incoming.get("backend") or "simulator")
            target["backend"] = backend if backend in IONQ_BACKENDS else "simulator"
            target["allow_paid_qpu"] = bool(incoming.get("allow_paid_qpu"))
    return state


def provider_key(provider: str, state: dict[str, Any] | None = None) -> str:
    current = state or load_provider_state()
    stored = str(current.get("providers", {}).get(provider, {}).get("api_key") or "")
    return stored or environment_key(provider)


def public_provider_status(state: dict[str, Any] | None = None) -> dict[str, Any]:
    current = state or load_provider_state()
    providers: dict[str, Any] = {}
    for provider in ("openai", "groq", "ionq"):
        details = current["providers"][provider]
        key = provider_key(provider, current)
        status = {
            "configured": bool(key),
            "enabled": bool(details.get("enabled")),
            "updated_at": details.get("updated_at") or "",
        }
        if provider in {"openai", "groq"}:
            status["model"] = details["model"]
        else:
            status["backend"] = details["backend"]
            status["allow_paid_qpu"] = bool(details.get("allow_paid_qpu"))
        providers[provider] = status
    return {
        "version": 1,
        "active_ai_provider": current["active_ai_provider"],
        "updated_at": current.get("updated_at") or "",
        "providers": providers,
        "security_boundary": {
            "provider_protected_plaintext": False,
            "provider_zmath_factors": False,
            "provider_matrix_keys": False,
            "provider_zme1_payloads": False,
        },
    }


def write_provider_state(state: dict[str, Any], path: Path | None = None) -> None:
    store = path or PROVIDER_STORE
    parent = store.parent
    with PROVIDER_LOCK:
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            parent.chmod(0o700)
        except OSError:
            pass
        if store.is_symlink():
            raise ProviderConfigError("Provider store cannot be a symbolic link.")
        temp = parent / f".{store.name}.{secrets.token_hex(8)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(temp, flags, 0o600)
        try:
            payload = json.dumps(state, indent=2, sort_keys=True).encode("utf-8")
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.chmod(temp, 0o600)
        os.replace(temp, store)
        os.chmod(store, 0o600)


def update_provider_state(update: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    current = load_provider_state(path)
    next_state = copy.deepcopy(current)
    active = update.get("active_ai_provider")
    if active is not None:
        active = str(active)
        if active not in AI_PROVIDER_IDS:
            raise ProviderConfigError("Choose local, OpenAI, or Groq for AI routing.")
        next_state["active_ai_provider"] = active

    providers = update.get("providers")
    if providers is not None and not isinstance(providers, dict):
        raise ProviderConfigError("Provider settings must be an object.")
    for provider, incoming in (providers or {}).items():
        if provider not in {"openai", "groq", "ionq"} or not isinstance(incoming, dict):
            raise ProviderConfigError("Unknown provider settings were supplied.")
        target = next_state["providers"][provider]
        if incoming.get("clear_api_key") is True:
            target["api_key"] = ""
            target["enabled"] = False
        elif "api_key" in incoming and str(incoming.get("api_key") or "").strip():
            target["api_key"] = valid_api_key(incoming["api_key"])
        if "enabled" in incoming:
            target["enabled"] = bool(incoming["enabled"])
        if provider in {"openai", "groq"} and "model" in incoming:
            target["model"] = valid_model(incoming["model"])
        if provider == "ionq":
            if "backend" in incoming:
                backend = str(incoming["backend"])
                if backend not in IONQ_BACKENDS:
                    raise ProviderConfigError("Choose a supported IonQ backend.")
                target["backend"] = backend
            if "allow_paid_qpu" in incoming:
                target["allow_paid_qpu"] = bool(incoming["allow_paid_qpu"])
            if target["backend"] != "simulator" and not target["allow_paid_qpu"]:
                raise ProviderConfigError("Confirm paid QPU use before selecting IonQ hardware.")
        target["updated_at"] = utc_now()

    selected = next_state["active_ai_provider"]
    if selected != "local" and not provider_key(selected, next_state):
        raise ProviderConfigError(f"Configure the {selected} API key before activating it.")
    if selected != "local" and not next_state["providers"][selected].get("enabled"):
        raise ProviderConfigError(f"Enable the {selected} provider before activating it.")
    next_state["updated_at"] = utc_now()
    write_provider_state(next_state, path)
    return next_state


def request_json(
    url: str,
    *,
    api_key: str,
    auth_scheme: str = "Bearer",
    payload: dict[str, Any] | None = None,
    timeout: float | None = None,
    max_bytes: int = 2_000_000,
) -> Any:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"{auth_scheme} {api_key}"
    data = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout or PROVIDER_TIMEOUT) as response:
        return json.loads(response.read(max_bytes).decode("utf-8"))


def test_provider_key(provider: str, api_key: str) -> dict[str, Any]:
    key = valid_api_key(api_key)
    if provider in {"openai", "groq"}:
        try:
            result = request_json(PROVIDER_ENDPOINTS[provider]["models"], api_key=key)
        except urllib.error.HTTPError as error:
            raise ProviderConfigError(f"{provider.title()} rejected the API key ({error.code}).") from error
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            raise ProviderConfigError(f"{provider.title()} could not be reached.") from error
        models = result.get("data") if isinstance(result, dict) else None
        ids = sorted(
            {
                str(item.get("id"))
                for item in (models or [])
                if isinstance(item, dict) and MODEL_PATTERN.fullmatch(str(item.get("id") or ""))
            }
        )
        if provider == "openai":
            preferred = [model for model in ids if model.startswith(("gpt-5.6", "gpt-5.5", "gpt-5.4"))]
            ids = preferred or ids
        return {"provider": provider, "valid": True, "models": ids[:100]}
    if provider == "ionq":
        try:
            result = request_json(
                PROVIDER_ENDPOINTS["ionq"]["whoami"],
                api_key=key,
                auth_scheme="apiKey",
                max_bytes=32_768,
            )
        except urllib.error.HTTPError as error:
            raise ProviderConfigError(f"IonQ rejected the API key ({error.code}).") from error
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            raise ProviderConfigError("IonQ could not be reached.") from error
        valid = isinstance(result, dict) and bool(result.get("key_id"))
        if not valid:
            raise ProviderConfigError("IonQ returned an incomplete key response.")
        return {"provider": "ionq", "valid": True}
    raise ProviderConfigError("Choose OpenAI, Groq, or IonQ for the key test.")


def cloud_chat_completion(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 260,
    temperature: float = 0.35,
    state: dict[str, Any] | None = None,
    provider_override: str | None = None,
    timeout: float | None = None,
) -> tuple[str | None, dict[str, str]]:
    current = state or load_provider_state()
    provider = provider_override or str(current.get("active_ai_provider") or "local")
    if provider not in {"openai", "groq"}:
        return None, {"provider": "local", "model": ""}
    details = current["providers"][provider]
    key = provider_key(provider, current)
    if not key or not details.get("enabled"):
        return None, {"provider": provider, "model": str(details.get("model") or "")}
    model = valid_model(details.get("model"))
    bounded_messages = []
    for item in messages[-8:]:
        role = str(item.get("role") or "user")
        content = str(item.get("content") or "")[:8_000]
        if role in {"system", "user", "assistant"} and content:
            bounded_messages.append({"role": role, "content": content})
    body: dict[str, Any] = {
        "model": model,
        "messages": bounded_messages,
        "stream": False,
    }
    if provider == "openai":
        body["max_completion_tokens"] = max(32, min(int(max_tokens), 2_000))
    else:
        body["max_tokens"] = max(32, min(int(max_tokens), 2_000))
        body["temperature"] = max(0.0, min(float(temperature), 1.0))
    try:
        result = request_json(
            PROVIDER_ENDPOINTS[provider]["chat"],
            api_key=key,
            payload=body,
            timeout=timeout,
        )
        text = result["choices"][0]["message"]["content"]
    except (
        OSError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
    ):
        return None, {"provider": provider, "model": model}
    return str(text).strip() or None, {"provider": provider, "model": model}


def ionq_receipt(
    commitment: str,
    *,
    purpose: str = "zshield-assurance",
    name: str = "CallChat ZShield assurance receipt",
    state: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    current = state or load_provider_state()
    details = current["providers"]["ionq"]
    key = provider_key("ionq", current)
    if not key or not details.get("enabled"):
        return None, "IonQ is not configured for this CallChat server."
    if not re.fullmatch(r"[a-f0-9]{64}", commitment):
        return None, "A valid commitment is required."
    backend = str(details.get("backend") or "simulator")
    if backend not in IONQ_BACKENDS:
        return None, "The configured IonQ backend is not supported."
    if backend != "simulator" and not details.get("allow_paid_qpu"):
        return None, "Paid IonQ QPU use is not approved by the server owner."
    payload = {
        "type": "ionq.circuit.v1",
        "name": name[:120],
        "backend": backend,
        "shots": 100,
        "metadata": {
            "purpose": re.sub(r"[^a-z0-9._-]", "-", purpose.lower())[:80],
            "commitment": commitment,
            "security_boundary": "provider-isolated",
        },
        "input": {
            "qubits": 4,
            "gateset": "qis",
            "circuit": [
                {"gate": "h", "target": 0},
                {"gate": "h", "target": 1},
                {"gate": "cnot", "control": 0, "target": 2},
                {"gate": "cnot", "control": 1, "target": 3},
            ],
        },
    }
    try:
        result = request_json(
            PROVIDER_ENDPOINTS["ionq"]["jobs"],
            api_key=key,
            auth_scheme="apiKey",
            payload=payload,
            timeout=PROVIDER_TIMEOUT,
            max_bytes=32_768,
        )
    except urllib.error.HTTPError as error:
        return None, f"IonQ rejected the job ({error.code})."
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None, "IonQ is temporarily unavailable."
    job_id = str(result.get("id") or "") if isinstance(result, dict) else ""
    if not re.fullmatch(r"[A-Za-z0-9-]{8,80}", job_id):
        return None, "IonQ returned an invalid job receipt."
    return {
        "provider": "IonQ",
        "api": "v0.4",
        "backend": backend,
        "job_id": job_id,
        "status": str(result.get("status") or "submitted")[:40],
        "receipt": f"ionq:v0.4:{backend}:{job_id}",
        "commitment": commitment,
        "key_material": False,
    }, None


def provider_store_permissions(path: Path | None = None) -> dict[str, Any]:
    store = path or PROVIDER_STORE
    if not store.exists():
        return {"exists": False, "mode": "", "secure": True}
    is_symlink = store.is_symlink()
    mode = stat.S_IMODE(store.lstat().st_mode)
    return {
        "exists": True,
        "mode": f"{mode:04o}",
        "secure": not is_symlink and mode == 0o600,
    }
