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
      {criterion.confidence != null && (
        <p className="criterion-confidence">AI確信度: {Math.round(criterion.confidence * 100)}%</p>
      )}
      {criterion.levels.length > 0 && (
        <details className="criterion-levels">
          <summary>審査基準を見る</summary>
          <ol>
            {criterion.levels.map((level, i) => (
              <li key={i} className={i + 1 === criterion.score ? "criterion-level-achieved" : undefined}>
                <span className="criterion-level-num">{i + 1}点</span> {level}
              </li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
