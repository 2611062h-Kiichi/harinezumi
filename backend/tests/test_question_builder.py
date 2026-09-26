import asyncio
import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from fastapi import HTTPException

from app.models.contest import ContestRubric, QuestionSet
from app.services import question_builder
from app.services.question_builder import GeneratedQuestion, GeneratedQuestions

LEVELS = ["全く触れていない", "触れているが曖昧", "一定の具体性がある", "具体的で根拠がある", "数値と実例で裏付けられている"]

RUBRIC = ContestRubric.model_validate(
    {
        "contest_name": "学生ビジコン2026",
        "criteria": [
            {"id": "problem", "name": "課題の明確さ", "description": "誰のどんな課題か", "max_points": 20},
            {"id": "market", "name": "市場性", "max_points": 30},
        ],
    }
)


def q(cid, levels=LEVELS):
    return GeneratedQuestion(criterion_id=cid, instructions=f"{cid} をどの程度満たしているか", levels=levels)


class FakeAnthropic:
    """Stands in for AsyncAnthropic and records what Claude would receive."""

    calls: list[dict] = []
    parsed_output = None
    error: Exception | None = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.messages = SimpleNamespace(parse=self._parse)

    async def _parse(self, **kwargs):
        FakeAnthropic.calls.append({"api_key": self.api_key, **kwargs})
        if FakeAnthropic.error is not None:
            raise FakeAnthropic.error
        return SimpleNamespace(parsed_output=FakeAnthropic.parsed_output)


@pytest.fixture
def fake_claude(monkeypatch):
    FakeAnthropic.calls = []
    FakeAnthropic.parsed_output = None
    FakeAnthropic.error = None
    monkeypatch.setattr(question_builder, "AsyncAnthropic", FakeAnthropic)
    return FakeAnthropic


def generate():
    return asyncio.run(question_builder.generate_questions(RUBRIC))


def test_returns_one_question_per_criterion(fake_claude):
    fake_claude.parsed_output = GeneratedQuestions(questions=[q("problem"), q("market")])

    result = generate()

    assert isinstance(result, QuestionSet)
    assert result.rubric == RUBRIC
    assert [x.criterion_id for x in result.questions] == ["problem", "market"]
    assert result.questions[0].levels == LEVELS


def test_sends_every_criterion_to_claude(fake_claude):
    fake_claude.parsed_output = GeneratedQuestions(questions=[q("problem"), q("market")])

    generate()

    assert len(fake_claude.calls) == 1
    call = fake_claude.calls[0]
    assert call["api_key"] == "test-anthropic-key"
    assert call["model"] == "claude-sonnet-5"
    assert call["output_format"] is GeneratedQuestions
    assert call["system"] == question_builder.SYSTEM_PROMPT

    prompt = call["messages"][0]["content"]
    assert "学生ビジコン2026" in prompt
    criteria_json = prompt[prompt.index("[") : prompt.rindex("]") + 1]
    assert json.loads(criteria_json) == [
        {"id": "problem", "name": "課題の明確さ", "description": "誰のどんな課題か", "max_points": 20},
        {"id": "market", "name": "市場性", "description": "（説明なし）", "max_points": 30},
    ]


def expect_502(fake_claude, questions) -> str:
    fake_claude.parsed_output = GeneratedQuestions(questions=questions)
    with pytest.raises(HTTPException) as excinfo:
        generate()
    assert excinfo.value.status_code == 502
    return excinfo.value.detail


def test_missing_question_is_rejected(fake_claude):
    detail = expect_502(fake_claude, [q("problem")])
    assert "Questionが無い観点: market" in detail


def test_extra_question_is_rejected(fake_claude):
    detail = expect_502(fake_claude, [q("problem"), q("market"), q("team")])
    assert "存在しない観点へのQuestion: team" in detail


def test_duplicate_question_is_rejected(fake_claude):
    detail = expect_502(fake_claude, [q("problem"), q("problem"), q("market")])
    assert "Questionが重複している観点: problem" in detail


@pytest.mark.parametrize("count", [4, 6])
def test_wrong_level_count_is_rejected(fake_claude, count):
    # Distinct sentences per level, not the same one repeated, so this
    # exercises a realistic wrong-count answer rather than a degenerate one.
    levels = [f"段階{i}の説明文" for i in range(count)]
    detail = expect_502(fake_claude, [q("problem", levels=levels), q("market")])
    assert "ちょうど5個" in detail


def test_blank_level_in_generated_question_gets_japanese_error(fake_claude):
    detail = expect_502(fake_claude, [q("problem", levels=LEVELS[:4] + ["  "]), q("market")])
    assert "入力してください" in detail
    assert "段階5" in detail
    # Not the raw Pydantic default ("String should have at least ...").
    assert "String" not in detail


def test_unparseable_claude_output_is_rejected(fake_claude):
    fake_claude.parsed_output = None

    with pytest.raises(HTTPException) as excinfo:
        generate()

    assert excinfo.value.status_code == 502
    assert excinfo.value.detail == question_builder.FAILURE_DETAIL


def test_claude_connection_error_becomes_502(fake_claude):
    # An SDK-level failure during the call itself (not just a malformed
    # response), e.g. a dropped connection mid-request. _call_claude has a
    # dedicated, more specific Japanese message for this SDK exception type.
    fake_claude.error = anthropic.APIConnectionError(
        request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    )

    with pytest.raises(HTTPException) as excinfo:
        generate()

    assert excinfo.value.status_code == 502
    assert "接続に失敗" in excinfo.value.detail


def test_claude_unexpected_exception_becomes_502_with_failure_detail(fake_claude):
    # Any other SDK-level exception not specifically handled falls through to
    # _call_claude's generic `except Exception`, using our failure_detail.
    fake_claude.error = RuntimeError("something the SDK doesn't type")

    with pytest.raises(HTTPException) as excinfo:
        generate()

    assert excinfo.value.status_code == 502
    assert excinfo.value.detail == question_builder.FAILURE_DETAIL


def test_missing_anthropic_key_is_a_clear_error(fake_claude, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    question_builder.get_settings.cache_clear()

    with pytest.raises(HTTPException) as excinfo:
        generate()

    assert excinfo.value.status_code == 400
    assert "ANTHROPIC_API_KEY" in excinfo.value.detail
    assert fake_claude.calls == []


def test_output_schema_uses_only_supported_json_schema_features():
    # Structured outputs reject e.g. length/range constraints; the real SDK
    # conversion must yield a plain schema with closed objects.
    import anthropic

    schema = anthropic.transform_schema(GeneratedQuestions)
    text = json.dumps(schema)
    for unsupported in ("minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum", "pattern"):
        assert unsupported not in text
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["GeneratedQuestion"]["additionalProperties"] is False
