import type { CriterionScore } from "../types/review";

export function CriterionCard({ criterion }: { criterion: CriterionScore }) {
  return (
    <div className="criterion-card">
      <div className="criterion-header">
        <span className="criterion-name">{criterion.name}</span>
        <span className="criterion-score">
          {criterion.score} / {criterion.max_score}
        </span>
      </div>
      <div className="criterion-bar">
        <div
          className="criterion-bar-fill"
          style={{ width: `${(criterion.score / criterion.max_score) * 100}%` }}
        />
      </div>
      <p className="criterion-comment">{criterion.comment}</p>
      <p className="criterion-confidence">AI確信度: {Math.round(criterion.confidence * 100)}%</p>
    </div>
  );
}
