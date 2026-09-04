from dataclasses import dataclass

import pytest

from app.services import gemini_service


@dataclass
class FakeSettings:
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"


@dataclass
class FakeResponse:
    text: str | None


class FakeModel:
    def __init__(self, response_text: str | None = None, raise_exc: Exception | None = None, delay: float = 0):
        self._response_text = response_text
        self._raise_exc = raise_exc
        self._delay = delay

    async def generate_content_async(self, prompt: str):
        import asyncio

        if self._delay:
            await asyncio.sleep(self._delay)
        if self._raise_exc:
            raise self._raise_exc
        return FakeResponse(text=self._response_text)


@pytest.mark.asyncio
async def test_missing_api_key_returns_none(monkeypatch):
    monkeypatch.setattr(gemini_service, "get_settings", lambda: FakeSettings(gemini_api_key=""))
    result = await gemini_service.generate_explanation("some prompt")
    assert result is None


@pytest.mark.asyncio
async def test_valid_response_returned(monkeypatch):
    monkeypatch.setattr(gemini_service, "get_settings", lambda: FakeSettings(gemini_api_key="fake-key"))
    monkeypatch.setattr("google.generativeai.configure", lambda **kw: None)
    monkeypatch.setattr(
        "google.generativeai.GenerativeModel",
        lambda model_name: FakeModel(response_text="RELIANCE moved unusually today."),
    )
    result = await gemini_service.generate_explanation("some prompt")
    assert result == "RELIANCE moved unusually today."


@pytest.mark.asyncio
async def test_malformed_empty_response_falls_back(monkeypatch):
    monkeypatch.setattr(gemini_service, "get_settings", lambda: FakeSettings(gemini_api_key="fake-key"))
    monkeypatch.setattr("google.generativeai.configure", lambda **kw: None)
    monkeypatch.setattr("google.generativeai.GenerativeModel", lambda model_name: FakeModel(response_text=""))
    result = await gemini_service.generate_explanation("some prompt")
    assert result is None


@pytest.mark.asyncio
async def test_none_response_falls_back(monkeypatch):
    monkeypatch.setattr(gemini_service, "get_settings", lambda: FakeSettings(gemini_api_key="fake-key"))
    monkeypatch.setattr("google.generativeai.configure", lambda **kw: None)
    monkeypatch.setattr("google.generativeai.GenerativeModel", lambda model_name: FakeModel(response_text=None))
    result = await gemini_service.generate_explanation("some prompt")
    assert result is None


@pytest.mark.asyncio
async def test_sdk_exception_falls_back_without_leaking_key(monkeypatch, caplog):
    secret_key = "super-secret-key-value"
    monkeypatch.setattr(gemini_service, "get_settings", lambda: FakeSettings(gemini_api_key=secret_key))
    monkeypatch.setattr("google.generativeai.configure", lambda **kw: None)
    monkeypatch.setattr(
        "google.generativeai.GenerativeModel",
        lambda model_name: FakeModel(raise_exc=RuntimeError(f"invalid request, key={secret_key}")),
    )
    with caplog.at_level("WARNING"):
        result = await gemini_service.generate_explanation("some prompt")
    assert result is None
    assert secret_key not in caplog.text


@pytest.mark.asyncio
async def test_timeout_falls_back(monkeypatch):
    monkeypatch.setattr(gemini_service, "get_settings", lambda: FakeSettings(gemini_api_key="fake-key"))
    monkeypatch.setattr(gemini_service, "REQUEST_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr("google.generativeai.configure", lambda **kw: None)
    monkeypatch.setattr(
        "google.generativeai.GenerativeModel",
        lambda model_name: FakeModel(response_text="too slow", delay=0.05),
    )
    result = await gemini_service.generate_explanation("some prompt")
    assert result is None
