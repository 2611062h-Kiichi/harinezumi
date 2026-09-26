from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.contest import (
    JEV_LEVEL_COUNT,
    MAX_CRITERIA,
    ContestCriterion,
    ContestCriterionResult,
    ContestRubric,
    ContestScoreResult,
    JevScoreQuestion,
    QuestionSet,
)

LEVELS = ["全く触れていない", "触れているが曖昧", "一定の具体性がある", "具体的で根拠がある", "数値と実例で裏付けられている"]


def criterion(cid="problem", name="課題の明確さ", max_points=20, **extra):
    return {"id": cid, "name": name, "max_points": max_points, **extra}


def rubric(*criteria):
    return {"contest_name": "学生ビジコン2026", "criteria": list(criteria) or [criterion()]}


def question(cid="problem", levels=None):
    return {"criterion_id": cid, "instructions": "課題の明確さをどの程度満たしているか", "levels": LEVELS if levels is None else levels}


def error_text(excinfo) -> str:
    return str(excinfo.value)


# --- valid input ---------------------------------------------------------------


def test_valid_rubric_and_question_set():
    qs = QuestionSet.model_validate(
        {
            "rubric": rubric(criterion("problem"), criterion("market", "市場性", 30, description="市場規模の根拠")),
            "questions": [question("problem"), question("market")],
        }
    )
    assert [c.id for c in qs.rubric.criteria] == ["problem", "market"]
    assert qs.rubric.criteria[0].description == ""
    assert qs.rubric.criteria[1].description == "市場規模の根拠"
    assert qs.questions[1].levels == LEVELS


def test_names_are_trimmed():
    c = ContestCriterion.model_validate(criterion(name="  課題の明確さ  "))
    assert c.name == "課題の明確さ"


def test_fifteen_criteria_is_the_upper_limit():
    criteria = [criterion(f"c{i}") for i in range(MAX_CRITERIA)]
    assert len(ContestRubric.model_validate(rubric(*criteria)).criteria) == MAX_CRITERIA


# --- AC-05: rejected input -----------------------------------------------------


@pytest.mark.parametrize("points", [0, -5, 101])
def test_points_out_of_range_are_rejected(points):
    with pytest.raises(ValidationError):
        ContestCriterion.model_validate(criterion(max_points=points))


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_name_is_rejected(name):
    with pytest.raises(ValidationError):
        ContestCriterion.model_validate(criterion(name=name))


def test_sixteen_criteria_are_rejected():
    criteria = [criterion(f"c{i}") for i in range(MAX_CRITERIA + 1)]
    with pytest.raises(ValidationError):
        ContestRubric.model_validate(rubric(*criteria))


def test_zero_criteria_are_rejected():
    with pytest.raises(ValidationError):
        ContestRubric.model_validate({"contest_name": "x", "criteria": []})


@pytest.mark.parametrize("count", [0, 1, JEV_LEVEL_COUNT - 1, JEV_LEVEL_COUNT + 1])
def test_level_count_other_than_five_is_rejected(count):
    with pytest.raises(ValidationError) as excinfo:
        JevScoreQuestion.model_validate(question(levels=[f"段階{i}" for i in range(count)]))
    if count:
        assert "ちょうど5個" in error_text(excinfo)


def test_blank_level_is_rejected():
    with pytest.raises(ValidationError):
        JevScoreQuestion.model_validate(question(levels=LEVELS[:4] + ["  "]))


def test_duplicate_criterion_ids_are_rejected():
    with pytest.raises(ValidationError) as excinfo:
        ContestRubric.model_validate(rubric(criterion("problem"), criterion("problem", "別名")))
    assert "重複" in error_text(excinfo)


@pytest.mark.parametrize("cid", ["", "課題", "has space", "x" * 41])
def test_invalid_criterion_id_is_rejected(cid):
    with pytest.raises(ValidationError):
        ContestCriterion.model_validate(criterion(cid=cid))


# --- QuestionSet: exactly one question per criterion ---------------------------


def test_missing_question_is_rejected():
    with pytest.raises(ValidationError) as excinfo:
        QuestionSet.model_validate(
            {"rubric": rubric(criterion("problem"), criterion("market")), "questions": [question("problem")]}
        )
    assert "Questionが無い観点: market" in error_text(excinfo)


def test_question_for_unknown_criterion_is_rejected():
    with pytest.raises(ValidationError) as excinfo:
        QuestionSet.model_validate(
            {"rubric": rubric(criterion("problem")), "questions": [question("problem"), question("team")]}
        )
    assert "存在しない観点へのQuestion: team" in error_text(excinfo)


def test_duplicate_question_is_rejected():
    with pytest.raises(ValidationError) as excinfo:
        QuestionSet.model_validate(
            {"rubric": rubric(criterion("problem")), "questions": [question("problem"), question("problem")]}
        )
    assert "Questionが重複している観点: problem" in error_text(excinfo)


# --- results ---------------------------------------------------------------------


def result(**overrides):
    base = {
        "criterion_id": "problem",
        "name": "課題の明確さ",
        "max_points": 20,
        "jev_score": 3.0,
        "points": 15.0,
        "confidence": 0.8,
        "low_confidence": False,
    }
    return {**base, **overrides}


def test_valid_score_result():
    r = ContestScoreResult.model_validate(
        {
            "contest_name": "学生ビジコン2026",
            "results": [result()],
            "total_points": 15.0,
            "max_total_points": 20,
            "transcript": "書き起こし",
            "generated_at": datetime.now(timezone.utc),
        }
    )
    assert r.results[0].points == 15.0


@pytest.mark.parametrize(
    "overrides",
    [
        {"points": 20.5},  # above max_points
        {"points": -1},
        {"jev_score": JEV_LEVEL_COUNT},  # Jev scores are 0..4
        {"jev_score": -0.1},
        {"confidence": 1.1},
    ],
)
def test_out_of_range_result_is_rejected(overrides):
    with pytest.raises(ValidationError):
        ContestCriterionResult.model_validate(result(**overrides))
