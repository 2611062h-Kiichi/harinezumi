"""Types for contest mode: the user's scoring criteria, the Jev Score questions
generated from them, and the scored result.

Limits come from docs/requirements.md (FR-1, FR-2, FR-7). Custom validation
messages are Japanese so the API layer can show them to users as-is.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

JEV_LEVEL_COUNT = 5  # levels per Jev Score question; Jev scores 0..JEV_LEVEL_COUNT-1
MAX_CRITERIA = 15
LOW_CONFIDENCE_THRESHOLD = 0.5

CriterionId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,40}$")]
RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ContestCriterion(BaseModel):
    """One scoring criterion as published by the contest organizer."""

    id: CriterionId
    name: Annotated[RequiredText, StringConstraints(max_length=100)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""
    # strict: reject "20", 20.0 and true so a typo in the UI cannot slip through.
    max_points: int = Field(ge=1, le=100, strict=True)


class ContestRubric(BaseModel):
    contest_name: Annotated[RequiredText, StringConstraints(max_length=100)]
    criteria: list[ContestCriterion] = Field(min_length=1, max_length=MAX_CRITERIA)

    @model_validator(mode="after")
    def _unique_criterion_ids(self):
        ids = [c.id for c in self.criteria]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"観点のIDが重複しています: {', '.join(duplicates)}")
        return self


class JevScoreQuestion(BaseModel):
    """A Jev `Score` question for one criterion. `levels` are ordered low to high,
    so level i corresponds to Jev score i."""

    criterion_id: CriterionId
    instructions: Annotated[RequiredText, StringConstraints(max_length=1000)]
    levels: list[Annotated[RequiredText, StringConstraints(max_length=500)]]

    @model_validator(mode="after")
    def _level_count(self):
        if len(self.levels) != JEV_LEVEL_COUNT:
            raise ValueError(
                f"観点 {self.criterion_id} の段階の数が{len(self.levels)}個です。"
                f"段階はちょうど{JEV_LEVEL_COUNT}個にしてください。"
            )
        return self


class QuestionSet(BaseModel):
    """A rubric together with exactly one Jev question per criterion."""

    rubric: ContestRubric
    questions: list[JevScoreQuestion]

    @model_validator(mode="after")
    def _one_question_per_criterion(self):
        criterion_ids = [c.id for c in self.rubric.criteria]
        question_ids = [q.criterion_id for q in self.questions]

        duplicated = sorted({i for i in question_ids if question_ids.count(i) > 1})
        missing = [i for i in criterion_ids if i not in question_ids]
        unknown = sorted(set(question_ids) - set(criterion_ids))

        problems = []
        if missing:
            problems.append(f"Questionが無い観点: {', '.join(missing)}")
        if unknown:
            problems.append(f"存在しない観点へのQuestion: {', '.join(unknown)}")
        if duplicated:
            problems.append(f"Questionが重複している観点: {', '.join(duplicated)}")
        if problems:
            raise ValueError("観点とQuestionが1対1になっていません。" + " / ".join(problems))
        return self


class ContestCriterionResult(BaseModel):
    criterion_id: CriterionId
    name: str
    max_points: int = Field(ge=1, le=100)
    jev_score: float = Field(ge=0, le=JEV_LEVEL_COUNT - 1)
    points: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    low_confidence: bool

    @model_validator(mode="after")
    def _points_within_max(self):
        if self.points > self.max_points:
            raise ValueError(f"観点 {self.criterion_id} の点数 {self.points} が配点 {self.max_points} を超えています。")
        return self


class ContestScoreResult(BaseModel):
    contest_name: str
    results: list[ContestCriterionResult] = Field(min_length=1, max_length=MAX_CRITERIA)
    total_points: float = Field(ge=0)
    max_total_points: int = Field(ge=1)
    transcript: str
    generated_at: datetime


class SavedQuestionSet(BaseModel):
    """A QuestionSet stored under a user-given name for reuse (FR-8)."""

    id: str
    name: Annotated[RequiredText, StringConstraints(max_length=100)]
    question_set: QuestionSet
    saved_at: datetime


class SavedQuestionSetSummary(BaseModel):
    """The lightweight shape used for listing saved Question sets."""

    id: str
    name: str
    contest_name: str
    criteria_count: int
    saved_at: datetime
