from datetime import datetime

from pydantic import BaseModel, Field


class SlideContent(BaseModel):
    index: int
    text: str
    notes: str = ""


class SlideExtractionResult(BaseModel):
    filename: str
    slides: list[SlideContent]


class TranscriptionResult(BaseModel):
    filename: str
    text: str


class CriterionScore(BaseModel):
    id: str
    name: str
    score: int = Field(ge=1, le=5)
    max_score: int = 5
    comment: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    levels: list[str]


class ImprovementSuggestion(BaseModel):
    point: str
    suggestion: str


class PitchReviewResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    overall_summary: str
    criteria: list[CriterionScore]
    strengths: list[str]
    improvements: list[ImprovementSuggestion]
    one_line_verdict: str
    generated_at: datetime
    transcript_included: bool
    rubric_mode: str
    rubric_mode_label: str
    feedback_tone: str
    feedback_tone_label: str


class CriterionComment(BaseModel):
    id: str
    comment: str


class PitchReviewLLMOutput(BaseModel):
    """Schema requested from Claude when Jev is available. Scores are decided
    by Jev beforehand and given to Claude as context — Claude only writes the
    qualitative comment justifying each already-decided score, plus the
    overall narrative fields."""

    overall_summary: str
    criterion_comments: list[CriterionComment]
    strengths: list[str]
    improvements: list[ImprovementSuggestion]
    one_line_verdict: str


class CriterionScoreAndComment(BaseModel):
    id: str
    score: int = Field(ge=1, le=5)
    comment: str


class PitchReviewLLMOutputFallback(BaseModel):
    """Schema requested from Claude when no TYPESAFE_API_KEY is configured —
    Claude scores every criterion itself instead of using Jev."""

    overall_summary: str
    criterion_scores: list[CriterionScoreAndComment]
    strengths: list[str]
    improvements: list[ImprovementSuggestion]
    one_line_verdict: str


class GeneratedCriterion(BaseModel):
    name: str
    levels: list[str] = Field(min_length=5, max_length=5)


class CustomRubricLLMOutput(BaseModel):
    """Schema requested from Claude to design a rubric tailored to a
    user-described event, used for the general mode's optional event_context."""

    criteria: list[GeneratedCriterion] = Field(min_length=5, max_length=9)


class RubricCriterionPreview(BaseModel):
    id: str
    name: str
    levels: list[str]


class RubricPreviewResponse(BaseModel):
    rubric_mode_label: str
    criteria: list[RubricCriterionPreview]
