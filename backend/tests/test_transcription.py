import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import transcription


class FakeOpenAI:
    """Stands in for AsyncOpenAI and records what Whisper would receive."""

    calls: list[dict] = []

    def __init__(self, api_key):
        self.api_key = api_key
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._create))

    async def _create(self, model, file):
        FakeOpenAI.calls.append({"api_key": self.api_key, "model": model, "content": file.read()})
        return SimpleNamespace(text="こんにちは、私たちのピッチを始めます。")


@pytest.fixture
def fake_openai(monkeypatch):
    FakeOpenAI.calls = []
    monkeypatch.setattr(transcription, "AsyncOpenAI", FakeOpenAI)
    return FakeOpenAI


def test_returns_whisper_text(tmp_path, fake_openai):
    audio = tmp_path / "pitch.mp3"
    audio.write_bytes(b"fake-audio-bytes")

    result = asyncio.run(transcription.transcribe(str(audio), "pitch.mp3"))

    assert result.filename == "pitch.mp3"
    assert result.text == "こんにちは、私たちのピッチを始めます。"
    assert fake_openai.calls == [
        {"api_key": "test-openai-key", "model": "whisper-1", "content": b"fake-audio-bytes"}
    ]


def test_missing_openai_key_is_a_clear_error(tmp_path, fake_openai, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    transcription.get_settings.cache_clear()
    audio = tmp_path / "pitch.mp3"
    audio.write_bytes(b"x")

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(transcription.transcribe(str(audio), "pitch.mp3"))

    assert excinfo.value.status_code == 400
    assert "OPENAI_API_KEY" in excinfo.value.detail
    assert fake_openai.calls == []


def test_file_over_whisper_limit_is_rejected(tmp_path, fake_openai):
    audio = tmp_path / "long.mp3"
    with open(audio, "wb") as f:
        f.truncate(transcription.WHISPER_MAX_BYTES + 1)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(transcription.transcribe(str(audio), "long.mp3"))

    assert excinfo.value.status_code == 400
    assert fake_openai.calls == []
