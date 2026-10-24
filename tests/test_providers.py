import json

import pytest
import requests

from models import Review
from providers import AIConfig, AIError, generate, gemini_schema


class Response:
    def __init__(self, data=None, status=200):
        self.data = data
        self.status_code = status

    def json(self):
        return self.data


def test_key_is_in_header_and_not_url_or_repr(monkeypatch):
    seen = {}
    def request(method, url, **kwargs):
        seen.update(url=url, **kwargs)
        return Response({"candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": "hidden thought", "thought": True}, {"text": '{"ok":true}'}]}}]})
    monkeypatch.setattr(requests, "request", request)
    config = AIConfig(api_key="private-test-key")
    output = generate(config, [{"role": "system", "content": "rules"},
                               {"role": "user", "content": "data"}], {"type": "object"})
    assert "private-test-key" not in seen["url"]
    assert "private-test-key" not in repr(config)
    assert seen["headers"]["x-goog-api-key"] == "private-test-key"
    assert seen["json"]["systemInstruction"]["parts"][0]["text"] == "rules"
    assert seen["allow_redirects"] is False
    assert output == '{"ok":true}'


@pytest.mark.parametrize("status,message", [(401,"denied"),(403,"denied"),(404,"not found"),
                                          (429,"usage limit"),(500,"HTTP 500"),(302,"HTTP 302")])
def test_provider_errors_do_not_expose_body(monkeypatch, status, message):
    monkeypatch.setattr(requests, "request", lambda *args, **kwargs: Response({"secret":"private"}, status))
    with pytest.raises(AIError, match=message) as error:
        generate(AIConfig(api_key="test"), [], {})
    assert "private" not in str(error.value)


def test_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(requests, "request", timeout)
    with pytest.raises(AIError, match="timed out"):
        generate(AIConfig(api_key="test"), [], {})


@pytest.mark.parametrize("data", [{"candidates":[]}, {"candidates":[None]},
                                {"candidates":[{"finishReason":"MAX_TOKENS"}]},
                                {"candidates":[{"content":{"parts":[]}}]}])
def test_incomplete_response_rejected(monkeypatch, data):
    monkeypatch.setattr(requests, "request", lambda *args, **kwargs: Response(data))
    with pytest.raises(AIError):
        generate(AIConfig(api_key="test"), [], {})


def test_schema_keeps_structure_without_unsupported_string_constraints():
    original = Review.model_json_schema()
    cleaned = gemini_schema(original)
    assert "maxLength" in json.dumps(original)
    assert "maxLength" not in json.dumps(cleaned)
    assert cleaned["required"] == original["required"]


def test_missing_key_stops_before_request(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("No request should be sent without a key")
    monkeypatch.setattr(requests, "request", forbidden)
    with pytest.raises(AIError, match="not configured"):
        generate(AIConfig(), [], {})


def test_model_id_cannot_change_the_api_destination():
    with pytest.raises(AIError, match="model ID"):
        generate(AIConfig(api_key="test", model="../other/path"), [], {})
