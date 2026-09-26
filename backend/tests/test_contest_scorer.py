import asyncio
from types import SimpleNamespace

import httpx2
import pytest
import typesafe_sdk
from fastapi import HTTPException
from typesafe_sdk import Score

from app.models.contest import ContestScoreResult, QuestionSet
from app.services import contest_scorer, jev_scorer

LEVELS = ["全く触れていない", "触れているが曖昧", "一定の具体性がある", "具体的で根拠がある", "数値と実例で裏付けられている"]
TRANSCRIPT = "私たちは、大学生の8割が困っている就活情報の偏りを解決します。"

QUESTION_SET = QuestionSet.model_validate(
    {
        "rubric": {
            "contest_name": "学生ビジコン2026",
            "criteria": [
                {"id": "problem", "name": "課題の明確さ", "max_points": 20},
                {"id": "market", "name": "市場性", "max_points": 30},
            ],
        },
        "questions": [
            # Deliberately in a different order from the rubric.
            {"criterion_id": "market", "instructions": "市場性をどの程度満たしているか", "levels": LEVELS},
            {"criterion_id": "problem", "instructions": "課題の明確さをどの程度満たしているか", "levels": LEVELS},
        ],
    }
)


class FakeTypeSafeClient:
    """Stands in for AsyncTypeSafeClient; answers with the configured scores."""

    calls: list[dict] = []
    answers: dict[str, tuple[float, float]] = {}
    error: Exception | None = None

    def __init__(self, api_key):
        self.api_key = api_key

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def system_one(self, state, questions):
        FakeTypeSafeClient.calls.append({"state": state, "questions": questions})
        if FakeTypeSafeClient.error is not None:
            raise FakeTypeSafeClient.error
        return SimpleNamespace(
            scores={
                name: SimpleNamespace(score=score, confidence=confidence)
                for name, (score, confidence) in FakeTypeSafeClient.answers.items()
            }
        )


@pytest.fixture
def fake_jev(monkeypatch):
    FakeTypeSafeClient.calls = []
    FakeTypeSafeClient.answers = {"problem": (3.0, 0.8), "market": (2.0, 0.9)}
    FakeTypeSafeClient.error = None
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)
    return FakeTypeSafeClient


def score() -> ContestScoreResult:
    return asyncio.run(contest_scorer.score_transcript(QUESTION_SET, TRANSCRIPT))


def test_sends_transcript_and_score_questions_to_jev(fake_jev):
    score()

    assert len(fake_jev.calls) == 1
    call = fake_jev.calls[0]
    assert call["state"] == TRANSCRIPT
    assert set(call["questions"]) == {"problem", "market"}
    for cid, name in [("problem", "課題の明確さ"), ("market", "市場性")]:
        question = call["questions"][cid]
        assert isinstance(question, Score)
        assert list(question.criteria) == LEVELS
        assert question.instructions.startswith(f"【観点】{name}\n")


def test_converts_jev_score_to_contest_points(fake_jev):
    result = score()

    by_id = {r.criterion_id: r for r in result.results}
    # AC-07 example: score 3.0 on 5 levels with 20 points -> 15.0
    assert by_id["problem"].jev_score == 3.0
    assert by_id["problem"].points == 15.0
    # 2.0 / 4 * 30 = 15.0
    assert by_id["market"].points == 15.0
    assert result.total_points == 30.0
    assert result.max_total_points == 50
    assert result.contest_name == "学生ビジコン2026"
    assert result.transcript == TRANSCRIPT


def test_fractional_points_are_rounded_to_one_decimal(fake_jev):
    fake_jev.answers = {"problem": (1.7, 0.8), "market": (2.35, 0.8)}

    result = score()

    by_id = {r.criterion_id: r for r in result.results}
    assert by_id["problem"].points == 8.5  # 1.7 / 4 * 20
    assert by_id["market"].points == 17.6  # 2.35 / 4 * 30 = 17.625
    assert result.total_points == 26.1


def test_results_follow_rubric_order(fake_jev):
    assert [r.criterion_id for r in score().results] == ["problem", "market"]


@pytest.mark.parametrize("confidence, expected", [(0.49, True), (0.5, False), (0.9, False)])
def test_low_confidence_flag_uses_threshold(fake_jev, confidence, expected):
    fake_jev.answers = {"problem": (3.0, confidence), "market": (2.0, 0.9)}

    result = score()

    assert result.results[0].low_confidence is expected


def test_slightly_out_of_range_jev_scores_are_clamped(fake_jev):
    fake_jev.answers = {"problem": (4.0000001, 0.9), "market": (-0.0000001, 0.9)}

    result = score()

    by_id = {r.criterion_id: r for r in result.results}
    assert by_id["problem"].jev_score == 4.0
    assert by_id["problem"].points == 20.0
    assert by_id["market"].jev_score == 0.0
    assert by_id["market"].points == 0.0


@pytest.mark.parametrize("bad_score", [5.0, -1.0, 4.5, -0.5])
def test_significantly_out_of_range_jev_score_is_rejected(fake_jev, bad_score):
    fake_jev.answers = {"problem": (bad_score, 0.9), "market": (2.0, 0.9)}

    with pytest.raises(HTTPException) as excinfo:
        score()

    assert excinfo.value.status_code == 502
    assert "課題の明確さ" in excinfo.value.detail


def test_missing_jev_answer_is_rejected(fake_jev):
    fake_jev.answers = {"problem": (3.0, 0.8)}

    with pytest.raises(HTTPException) as excinfo:
        score()

    assert excinfo.value.status_code == 502
    assert "市場性" in excinfo.value.detail


def test_missing_typesafe_key_is_a_clear_error(fake_jev, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "")
    jev_scorer.get_settings.cache_clear()

    with pytest.raises(HTTPException) as excinfo:
        score()

    assert excinfo.value.status_code == 400
    assert "TYPESAFE_API_KEY" in excinfo.value.detail
    assert fake_jev.calls == []


def test_authentication_error_becomes_japanese_400(fake_jev):
    fake_jev.error = typesafe_sdk.TypeSafeAuthenticationError(
        status=401, body=None, headers=httpx2.Headers(), message="bad key"
    )

    with pytest.raises(HTTPException) as excinfo:
        score()

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "TYPESAFE_API_KEYが正しくありません。"


@pytest.mark.parametrize(
    "jev_score, level_count, max_points, expected",
    [
        (3.0, 5, 20, 15.0),
        (0.05, 5, 20, 0.3),  # exactly 0.25 -> 四捨五入 gives 0.3 (Python's round() would give 0.2)
        (0.3, 5, 30, 2.3),  # exactly 2.25 (float math would give 2.2499999...) -> 2.3
        (0.15, 5, 30, 1.1),  # 1.125 is not a half at one decimal -> 1.1
        (4.0, 5, 7, 7.0),
    ],
)
def test_points_use_round_half_up(jev_score, level_count, max_points, expected):
    assert contest_scorer.to_points(jev_score, level_count, max_points) == expected
