"""Scores a pitch (transcript and/or slides) against a contest's QuestionSet with Jev.

Jev only rates each criterion on its 0-based level scale; conversion to the
contest's points and the total are computed here, deterministically.
"""

import logging
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from anthropic import AsyncAnthropic
from fastapi import HTTPException
from typesafe_sdk import Score

from app.config import get_settings
from app.models.contest import (
    LOW_CONFIDENCE_THRESHOLD,
    ContestCriterionResult,
    ContestScoreResult,
    QuestionSet,
)
from app.models.schemas import SlideExtractionResult
from app.services.jev_scorer import run_system_one
from app.services.review_generator import build_user_prompt, describe_presentation_visuals
from app.services.transcription import transcribe
from app.services.video_frames import extract_frames_base64, is_video_file

logger = logging.getLogger(__name__)

# Jev's score should land in [0, top_level]; this only absorbs float rounding
# drift (e.g. 4.0000001). Anything further off is treated as a bad answer
# rather than silently clamped, since it likely means Jev and the sent
# criteria disagree on the level count.
JEV_SCORE_DRIFT_TOLERANCE = 0.001


def build_jev_questions(question_set: QuestionSet) -> dict[str, Score]:
    names = {c.id: c.name for c in question_set.rubric.criteria}
    return {
        q.criterion_id: Score(
            # Lead with the criterion name so Jev knows which criterion it rates.
            instructions=f"【観点】{names[q.criterion_id]}\n{q.instructions}",
            criteria=q.levels,
        )
        for q in question_set.questions
    }


def round_half_up(value: Decimal) -> float:
    # FR-6 asks for 四捨五入; Python's round() rounds halves to even instead.
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def to_points(jev_score: float, level_count: int, max_points: int) -> float:
    # Decimal(str(...)) keeps e.g. 0.3 exact, so 0.3 / 4 * 30 is 2.25, not 2.2499999...
    return round_half_up(Decimal(str(jev_score)) / (level_count - 1) * max_points)


def build_jev_state(
    slides: SlideExtractionResult | None,
    transcript: str | None,
    visual_description: str | None = None,
) -> str:
    # Transcript only: pass it through unchanged, exactly as before slides were
    # supported. With slides or video: the same layout the pitch-review mode
    # already sends to Jev.
    if slides is None and visual_description is None:
        return transcript or ""
    return build_user_prompt(slides, transcript, visual_description)


def _has_slide_text(slides: SlideExtractionResult) -> bool:
    return any(s.text.strip() or s.notes.strip() for s in slides.slides)


def check_slide_limits(slides: SlideExtractionResult) -> None:
    """Rejects decks too large to be a pitch, before any paid API is called."""
    settings = get_settings()
    pages = len(slides.slides)
    if pages > settings.max_contest_slide_pages:
        raise HTTPException(
            status_code=400,
            detail=(
                f"スライド資料のページ数が多すぎます（{pages}ページ、上限{settings.max_contest_slide_pages}ページ）。"
                "発表で使うページだけにしてから、もう一度お試しください。"
            ),
        )
    chars = sum(len(s.text) + len(s.notes) for s in slides.slides)
    if chars > settings.max_contest_slide_chars:
        raise HTTPException(
            status_code=400,
            detail=(
                f"スライド資料の文字数が多すぎます（{chars:,}文字、上限{settings.max_contest_slide_chars:,}文字。"
                "スピーカーノートを含みます）。発表で使うページだけにするか、ノートを短くしてから、もう一度お試しください。"
            ),
        )


async def score_materials(
    question_set: QuestionSet,
    slides: SlideExtractionResult | None = None,
    transcript: str | None = None,
    visual_description: str | None = None,
) -> ContestScoreResult:
    """Scores a pitch from its slides, its transcript, or both (plus, for a
    video, a description of the speaker's non-verbal delivery)."""
    if slides is None and transcript is None:
        raise HTTPException(status_code=400, detail="スライド資料、または発表の音声・動画を指定してください。")
    if slides is not None:
        check_slide_limits(slides)
    if transcript is not None and not transcript.strip():
        detail = "発表の文字起こしが空です。音声に話し声が入っているか確認して、もう一度お試しください。"
        if slides is not None and _has_slide_text(slides):
            detail += "スライド資料だけを選び直して採点すれば、スライドだけで採点することもできます。"
        raise HTTPException(status_code=400, detail=detail)
    if transcript is None and not _has_slide_text(slides):
        raise HTTPException(
            status_code=400,
            detail=(
                "スライド資料から文字を読み取れませんでした。画像だけのスライドやスキャンしたPDFは読み取れません。"
                "文字を含む資料を使うか、発表の音声・動画と一緒に送ってください。"
            ),
        )

    questions = build_jev_questions(question_set)
    response = await run_system_one(build_jev_state(slides, transcript, visual_description), questions)

    levels_by_id = {q.criterion_id: q.levels for q in question_set.questions}
    results = []
    for criterion in question_set.rubric.criteria:
        answer = response.scores.get(criterion.id)
        if answer is None:
            logger.error("Jev returned no score for criterion %s", criterion.id)
            raise HTTPException(
                status_code=502,
                detail=f"Jevから観点「{criterion.name}」の採点結果が返ってきませんでした。もう一度お試しください。",
            )

        top_level = len(levels_by_id[criterion.id]) - 1
        if answer.score < -JEV_SCORE_DRIFT_TOLERANCE or answer.score > top_level + JEV_SCORE_DRIFT_TOLERANCE:
            logger.error(
                "Jev returned an out-of-range score for criterion %s: %r (expected 0..%d)",
                criterion.id,
                answer.score,
                top_level,
            )
            raise HTTPException(
                status_code=502,
                detail=f"Jevから観点「{criterion.name}」の異常な採点結果が返ってきました。もう一度お試しください。",
            )
        # Jev's score is a probability-weighted average of levels; clamp only float drift.
        jev_score = min(max(answer.score, 0.0), float(top_level))
        results.append(
            ContestCriterionResult(
                criterion_id=criterion.id,
                name=criterion.name,
                max_points=criterion.max_points,
                jev_score=jev_score,
                points=to_points(jev_score, top_level + 1, criterion.max_points),
                confidence=answer.confidence,
                low_confidence=answer.confidence < LOW_CONFIDENCE_THRESHOLD,
            )
        )

    return ContestScoreResult(
        contest_name=question_set.rubric.contest_name,
        results=results,
        total_points=round_half_up(sum(Decimal(str(r.points)) for r in results)),
        max_total_points=sum(c.max_points for c in question_set.rubric.criteria),
        transcript=transcript or "",
        generated_at=datetime.now(timezone.utc),
        slides_included=slides is not None,
        transcript_included=transcript is not None,
        visual_included=visual_description is not None,
        visual_description=visual_description,
    )


async def score_transcript(question_set: QuestionSet, transcript: str) -> ContestScoreResult:
    return await score_materials(question_set, transcript=transcript)


async def score_audio(
    question_set: QuestionSet,
    audio_path: str,
    filename: str,
    slides: SlideExtractionResult | None = None,
) -> ContestScoreResult:
    """Transcribes the pitch with Whisper and scores it (with slides, if any) with Jev."""
    if slides is not None:
        # Before transcription, so an oversized deck doesn't cost a Whisper call.
        check_slide_limits(slides)
    transcription = await transcribe(audio_path, filename)
    visual_description = None
    if transcription.text.strip() and is_video_file(filename):
        # Only once scoring can go ahead: describing frames is a paid Claude call.
        visual_description = await describe_video(audio_path)
    return await score_materials(
        question_set, slides=slides, transcript=transcription.text, visual_description=visual_description
    )


async def describe_video(video_path: str) -> str | None:
    """Best-effort description of the speaker's non-verbal delivery, as in the
    pitch-review mode. None (score without it) if there's no Claude key, no
    usable frames, or the Claude call fails."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set; scoring the video without visual analysis")
        return None
    frames = extract_frames_base64(video_path)
    if not frames:
        return None
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    description = await describe_presentation_visuals(client, settings.claude_model, frames)
    # A blank answer carries no visual signal; don't report the video as used.
    return description.strip() if description and description.strip() else None
