import type { PitchReviewResponse } from "../types/review";
import { CriterionCard } from "./CriterionCard";
import { StrengthsList } from "./StrengthsList";
import { ImprovementsList } from "./ImprovementsList";

interface Props {
  review: PitchReviewResponse;
  onReset: () => void;
}

export function ReviewResult({ review, onReset }: Props) {
  return (
    <div className="review-result">
      <div className="overall-card">
        <div className="overall-score">{review.overall_score}</div>
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
