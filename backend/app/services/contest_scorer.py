"""Scores a pitch transcript against a contest's QuestionSet with Jev.

Jev only rates each criterion on its 0-based level scale; conversion to the
contest's points and the total are computed here, deterministically.
"""

import logging
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from typesafe_sdk import Score

from app.models.contest import (
    LOW_CONFIDENCE_THRESHOLD,
    ContestCriterionResult,
    ContestScoreResult,
    QuestionSet,
)
from app.services.jev_scorer import run_system_one
from app.services.transcription import transcribe

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


async def score_transcript(question_set: QuestionSet, transcript: str) -> ContestScoreResult:
    if not transcript.strip():
        raise HTTPException(
            status_code=400,
            detail="発表の文字起こしが空です。音声に話し声が入っているか確認して、もう一度お試しください。",
        )

    questions = build_jev_questions(question_set)
    response = await run_system_one(transcript, questions)

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
        transcript=transcript,
        generated_at=datetime.now(timezone.utc),
    )


async def score_audio(question_set: QuestionSet, audio_path: str, filename: str) -> ContestScoreResult:
    """Transcribes the pitch with Whisper and scores the text as-is with Jev."""
    transcription = await transcribe(audio_path, filename)
    return await score_transcript(question_set, transcription.text)
