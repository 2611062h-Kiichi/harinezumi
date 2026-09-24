import { useEffect, useRef } from "react";
import confetti from "canvas-confetti";
import type { PitchReviewResponse } from "../types/review";
import { CriterionCard } from "./CriterionCard";
import { StrengthsList } from "./StrengthsList";
import { ImprovementsList } from "./ImprovementsList";
import { useCountUp } from "../hooks/useCountUp";

const CONFETTI_SCORE_THRESHOLD = 80;

interface Props {
  review: PitchReviewResponse;
  onReset: () => void;
}

export function ReviewResult({ review, onReset }: Props) {
  const animatedScore = useCountUp(review.overall_score);
  const hasFiredConfetti = useRef(false);

  useEffect(() => {
    if (hasFiredConfetti.current || review.overall_score < CONFETTI_SCORE_THRESHOLD) {
      return;
    }
    hasFiredConfetti.current = true;
    const timer = setTimeout(() => {
      confetti({
        particleCount: 140,
        spread: 80,
        origin: { y: 0.6 },
      });
    }, 900);
    return () => clearTimeout(timer);
  }, [review.overall_score]);

  return (
    <div className="review-result">
      <p className="rubric-mode-badge">
        {review.rubric_mode_label} ・ {review.feedback_tone_label}
      </p>
      <div className="overall-card">
        <div className="overall-score">{animatedScore}</div>
        <div>
          <p className="one-line-verdict">{review.one_line_verdict}</p>
          <p className="overall-summary">{review.overall_summary}</p>
          {!review.transcript_included && (
            <p className="note">※ 音声書き起こしなし。スライドのみでの審査です。</p>
          )}
        </div>
      </div>

      <section className="list-section">
        <h2>評価項目別スコア</h2>
        <div className="criteria-grid">
          {review.criteria.map((c) => (
            <CriterionCard key={c.id} criterion={c} />
          ))}
        </div>
      </section>

      <StrengthsList strengths={review.strengths} />
      <ImprovementsList improvements={review.improvements} />

      <button className="reset-button" onClick={onReset}>
        別のピッチを審査する
      </button>
    </div>
  );
}
