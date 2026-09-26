import type { ContestScoreResult } from "../../types/contest";

interface Props {
  result: ContestScoreResult;
  onScoreAgain: () => void;
  onReset: () => void;
}

export function ContestScoreResultView({ result, onScoreAgain, onReset }: Props) {
  return (
    <div className="contest-score-result">
      <h1>{result.contest_name} の採点結果</h1>

      <div className="overall-card">
        <div className="overall-score">
          {result.total_points}
          <span className="overall-score-max"> / {result.max_total_points}</span>
        </div>
      </div>

      <section className="list-section">
        <h2>観点別の点数</h2>
        <div className="criteria-grid">
          {result.results.map((r) => (
            <div className="criterion-card" key={r.criterion_id}>
              <div className="criterion-header">
                <span className="criterion-name">{r.name}</span>
                <span className="criterion-score">
                  {r.points} / {r.max_points}
                </span>
              </div>
              <div className="criterion-bar">
                <div className="criterion-bar-fill" style={{ width: `${(r.points / r.max_points) * 100}%` }} />
              </div>
              {r.low_confidence && (
                <p className="note criterion-confidence">
                  発表の中に判断材料が少ないため、この点数は参考値です。
                </p>
              )}
            </div>
          ))}
        </div>
      </section>

      <button onClick={onScoreAgain}>別の音声でもう一度採点する</button>
      <button className="secondary-button" onClick={onReset}>
        最初からやり直す
      </button>
    </div>
  );
}
