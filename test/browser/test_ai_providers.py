"""Provider selection / configuration tests (no corpus, no API key)."""

import pytest

from tf.browser import ai_query


class FakeResponse:
    def __init__(self, text):
        self.text = text
        self.candidates = [type("C", (), {"finish_reason": 1})()]


@pytest.fixture
def spy(monkeypatch):
    """Capture which provider path was taken and with what settings."""
    calls = {}

    def fake_gemini(prompt, api_key, model="", base_url=""):
        calls.update(
            provider="gemini", api_key=api_key, model=model, base_url=base_url
        )
        return "word sp=verb"

    def fake_anthropic(prompt, api_key, model="", base_url=""):
        calls.update(
            provider="claude", api_key=api_key, model=model, base_url=base_url
        )
        return "word sp=verb"

    monkeypatch.setattr(ai_query, "_call_gemini", fake_gemini)
    monkeypatch.setattr(ai_query, "_call_anthropic", fake_anthropic)
    return calls


def test_detects_anthropic_key():
    assert ai_query.detect_provider("sk-ant-abc123") == "claude"


def test_detects_gemini_key():
    assert ai_query.detect_provider("AIzaSyABC") == "gemini"


def test_explicit_provider_overrides_key_shape(spy):
    ai_query.call_llm("p", "AIzaSyABC", provider="claude")
    assert spy["provider"] == "claude"


def test_auto_dispatch_by_key(spy):
    ai_query.call_llm("p", "sk-ant-xyz")
    assert spy["provider"] == "claude"
    ai_query.call_llm("p", "AIzaSyABC")
    assert spy["provider"] == "gemini"


def test_model_and_base_url_passed_through(spy):
    ai_query.call_llm(
        "p",
        "sk-ant-xyz",
        model="claude-opus-5",
        base_url="https://proxy.example/v1",
    )
    assert spy["model"] == "claude-opus-5"
    assert spy["base_url"] == "https://proxy.example/v1"


def test_unknown_provider_rejected():
    with pytest.raises(ValueError, match="Unknown provider"):
        ai_query.call_llm("p", "AIzaSyABC", provider="gpt")


def test_generate_query_reports_provider(spy):
    result = ai_query.generate_query(
        "find verbs", "AIzaSyABC", provider="claude", model="claude-sonnet-5"
    )
    assert result["provider"] == "claude"
    assert not result["error"]
    assert result["query"] == "word sp=verb"
    assert spy["model"] == "claude-sonnet-5"


def test_generate_query_rejects_bad_provider():
    result = ai_query.generate_query("find verbs", "AIzaSyABC", provider="gpt")
    assert "Unknown provider" in result["error"]


def test_generate_query_infers_provider_for_response():
    result = ai_query.generate_query("find verbs", "", provider="")
    assert result["error"] == "API key is required"


def test_gemini_model_resolution_prefers_newest_pro():
    class M:
        def __init__(self, name):
            self.name = f"models/{name}"
            self.supported_generation_methods = ["generateContent"]

    class FakeGenai:
        @staticmethod
        def list_models():
            return [
                M("gemini-2.5-pro"),
                M("gemini-3.6-flash"),
                M("gemini-3.5-flash-lite"),
                M("gemini-3.1-flash-image"),
            ]

    ai_query._GEMINI_RESOLVED = None
    try:
        assert ai_query._resolve_gemini_model(FakeGenai) == "gemini-3.6-flash"
    finally:
        ai_query._GEMINI_RESOLVED = None


def test_gemini_model_resolution_falls_back_on_error():
    class Boom:
        @staticmethod
        def list_models():
            raise RuntimeError("no network")

    ai_query._GEMINI_RESOLVED = None
    try:
        assert (
            ai_query._resolve_gemini_model(Boom) == ai_query.GEMINI_FALLBACK_MODEL
        )
    finally:
        ai_query._GEMINI_RESOLVED = None
