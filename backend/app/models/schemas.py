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


class PitchReviewLLMOutput(BaseModel):
    """Schema requested from Claude — generated_at/transcript_included are filled in by the server."""

    overall_summary: str
    criteria: list[CriterionScore]
    strengths: list[str]
    improvements: list[ImprovementSuggestion]
    one_line_verdict: str
