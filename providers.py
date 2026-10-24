import re
from dataclasses import dataclass, field

import requests


class AIError(Exception):
    pass


@dataclass(frozen=True)
class AIConfig:
    provider: str = "Gemini"
    model: str = "gemini-3.5-flash-lite"
    api_key: str = field(default="", repr=False)


def request_json(method: str, url: str, **kwargs) -> dict:
    try:
        response = requests.request(method, url, allow_redirects=False, **kwargs)
    except requests.Timeout:
        raise AIError("Gemini timed out. Try again with shorter inputs.") from None
    except requests.RequestException:
        raise AIError("Could not reach Gemini. Check the server's network connection.") from None
    if response.status_code in {401, 403}:
        raise AIError("Gemini denied access. Check the server API key and project permissions.")
    if response.status_code == 404:
        raise AIError("Gemini model not found. Check GEMINI_MODEL on the server.")
    if response.status_code == 429:
        raise AIError("The Gemini project's usage limit was reached.")
    if not 200 <= response.status_code < 300:
        raise AIError(f"Gemini returned HTTP {response.status_code}.")
    try:
        data = response.json()
    except ValueError:
        raise AIError("Gemini returned an unreadable response.") from None
    if not isinstance(data, dict):
        raise AIError("Gemini returned an unexpected response format.")
    return data


def gemini_schema(value):
    if isinstance(value, dict):
        return {key: gemini_schema(item) for key, item in value.items()
                if key not in {"minLength", "maxLength"}}
    if isinstance(value, list):
        return [gemini_schema(item) for item in value]
    return value


def generate(config: AIConfig, messages: list[dict], schema: dict) -> str:
    if not config.api_key.strip():
        raise AIError("GEMINI_API_KEY is not configured on the server.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", config.model):
        raise AIError("GEMINI_MODEL must be a Gemini model ID.")
    contents = [
        {"role": "model" if message["role"] == "assistant" else "user",
         "parts": [{"text": message["content"]}]}
        for message in messages if message["role"] != "system"
    ]
    body = {
        "systemInstruction": {"parts": [{"text": "\n".join(
            message["content"] for message in messages if message["role"] == "system")}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
            "responseJsonSchema": gemini_schema(schema),
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model}:generateContent"
    data = request_json("POST", url, json=body,
                        headers={"x-goog-api-key": config.api_key.strip()}, timeout=(10, 120))
    candidates = data.get("candidates", [])
    if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
        raise AIError("Gemini returned no candidate.")
    candidate = candidates[0]
    if candidate.get("finishReason") not in {None, "STOP"}:
        raise AIError("Gemini did not finish a complete response. Try shorter inputs.")
    content = candidate.get("content", {})
    parts = content.get("parts", []) if isinstance(content, dict) else []
    if not isinstance(parts, list):
        raise AIError("Gemini returned an unexpected content format.")
    output = "".join(part["text"] for part in parts if isinstance(part, dict)
                     and not part.get("thought", False) and isinstance(part.get("text"), str))
    if not output.strip():
        raise AIError("Gemini returned no text.")
    return output
