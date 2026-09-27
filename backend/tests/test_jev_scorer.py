import asyncio
from types import SimpleNamespace

import httpx2
import pytest
import typesafe_sdk
from fastapi import HTTPException
from typesafe_sdk import Score

from app.rubric import DEFAULT_MODE, SCALE_MIN, get_rubric_criteria
from app.services import jev_scorer


class FakeTypeSafeClient:
    """Stands in for AsyncTypeSafeClient and records what Jev would receive."""

    calls: list[dict] = []
    error: Exception | None = None

    def __init__(self, api_key):
        self.api_key = api_key

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def system_one(self, state, questions):
        FakeTypeSafeClient.calls.append({"api_key": self.api_key, "state": state, "questions": questions})
        if FakeTypeSafeClient.error is not None:
            raise FakeTypeSafeClient.error
        # Jev scores are 0-based; answer level 2 (i.e. the middle) with 0.8 confidence.
        return SimpleNamespace(
            scores={name: SimpleNamespace(score=2.0, confidence=0.8) for name in questions}
        )


@pytest.fixture
def fake_jev(monkeypatch):
    FakeTypeSafeClient.calls = []
    FakeTypeSafeClient.error = None
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)
    return FakeTypeSafeClient


def test_sends_pitch_text_and_score_questions_to_jev(fake_jev):
    result = asyncio.run(jev_scorer.score_with_jev("発表の書き起こしテキスト", get_rubric_criteria(DEFAULT_MODE)))

    assert len(fake_jev.calls) == 1
    call = fake_jev.calls[0]
    assert call["api_key"] == "test-typesafe-key"
    assert call["state"] == "発表の書き起こしテキスト"

    criteria = get_rubric_criteria(DEFAULT_MODE)
    assert set(call["questions"]) == {c["id"] for c in criteria}
    for c in criteria:
        question = call["questions"][c["id"]]
        assert isinstance(question, Score)
        assert list(question.criteria) == c["levels"]

    for c in criteria:
        # 0-based Jev score 2.0 -> 1-5 scale 3.0
        assert result[c["id"]].score_1_5 == 2.0 + SCALE_MIN
        assert result[c["id"]].confidence == 0.8


def test_missing_typesafe_key_is_a_clear_error(fake_jev, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "")
    jev_scorer.get_settings.cache_clear()

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(jev_scorer.score_with_jev("text", get_rubric_criteria(DEFAULT_MODE)))

    assert excinfo.value.status_code == 400
    assert "TYPESAFE_API_KEY" in excinfo.value.detail
    assert fake_jev.calls == []


def test_authentication_error_becomes_japanese_400(fake_jev):
    fake_jev.error = typesafe_sdk.TypeSafeAuthenticationError(
        status=401, body=None, headers=httpx2.Headers(), message="bad key"
    )

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(jev_scorer.score_with_jev("text", get_rubric_criteria(DEFAULT_MODE)))

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "TYPESAFE_API_KEYが正しくありません。"
