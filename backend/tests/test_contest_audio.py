"""Audio -> Whisper transcript -> Jev state, end to end with both APIs faked."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import contest_scorer, jev_scorer, transcription
from tests.test_contest_scorer import QUESTION_SET, FakeTypeSafeClient

TRANSCRIPT = "えー、私たちは、就活情報の偏りという課題を解決します。"


class FakeOpenAI:
    """Stands in for AsyncOpenAI; returns the configured transcript text."""

    calls: list[dict] = []
    text = TRANSCRIPT

    def __init__(self, api_key):
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._create))

    async def _create(self, model, file):
        FakeOpenAI.calls.append({"model": model, "content": file.read()})
        return SimpleNamespace(text=FakeOpenAI.text)


@pytest.fixture
def fakes(monkeypatch):
    FakeOpenAI.calls = []
    FakeOpenAI.text = TRANSCRIPT
    FakeTypeSafeClient.calls = []
    FakeTypeSafeClient.answers = {"problem": (3.0, 0.8), "market": (2.0, 0.9)}
    FakeTypeSafeClient.error = None
    monkeypatch.setattr(transcription, "AsyncOpenAI", FakeOpenAI)
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)
    return SimpleNamespace(whisper=FakeOpenAI, jev=FakeTypeSafeClient)


@pytest.fixture
def audio_file(tmp_path):
    path = tmp_path / "pitch.mp3"
    path.write_bytes(b"fake-audio-bytes")
    return path


def score_audio(path):
    return asyncio.run(contest_scorer.score_audio(QUESTION_SET, str(path), "pitch.mp3"))


def test_whisper_text_becomes_jev_state_unchanged(fakes, audio_file):
    result = score_audio(audio_file)

    assert fakes.whisper.calls == [{"model": "whisper-1", "content": b"fake-audio-bytes"}]
    assert len(fakes.jev.calls) == 1
    assert fakes.jev.calls[0]["state"] == TRANSCRIPT
    assert result.transcript == TRANSCRIPT
    assert result.total_points == 30.0


def test_surrounding_whitespace_is_passed_through_as_is(fakes, audio_file):
    fakes.whisper.text = "  " + TRANSCRIPT + "\n"

    score_audio(audio_file)

    assert fakes.jev.calls[0]["state"] == "  " + TRANSCRIPT + "\n"


@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_empty_transcript_is_rejected_before_jev(fakes, audio_file, text):
    fakes.whisper.text = text

    with pytest.raises(HTTPException) as excinfo:
        score_audio(audio_file)

    assert excinfo.value.status_code == 400
    assert "文字起こしが空" in excinfo.value.detail
    assert fakes.jev.calls == []


def test_empty_text_input_is_rejected_too(fakes):
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(contest_scorer.score_transcript(QUESTION_SET, "  "))

    assert excinfo.value.status_code == 400
    assert fakes.jev.calls == []


def test_missing_openai_key_stops_before_any_api_call(fakes, audio_file, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    transcription.get_settings.cache_clear()

    with pytest.raises(HTTPException) as excinfo:
        score_audio(audio_file)

    assert excinfo.value.status_code == 400
    assert "OPENAI_API_KEY" in excinfo.value.detail
    assert fakes.whisper.calls == []
    assert fakes.jev.calls == []
