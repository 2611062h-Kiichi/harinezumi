import type { ContestScoreResult } from "../../types/contest";

interface Props {
  result: ContestScoreResult;
  onScoreAgain: () => void;
  onReset: () => void;
}

function sourceLabel(result: ContestScoreResult): string {
  const used: string[] = [];
  if (result.slides_included) used.push("スライド資料");
  if (result.transcript_included) used.push("発表の音声");
  if (result.visual_included) used.push("映像（身振り・表情）");
  if (used.length === 1 && result.slides_included) return "スライド資料だけで採点しました（発表の音声なし）。";
  if (used.length === 1) return "発表の音声で採点しました（スライド資料なし）。";
  return `${used.join(used.length > 2 ? "・" : "と")}で採点しました。`;
}

export function ContestScoreResultView({ result, onScoreAgain, onReset }: Props) {
  return (
    <div className="contest-score-result">
      <h1>{result.contest_name} の採点結果</h1>
      <p className="note">{sourceLabel(result)}</p>

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

      {result.visual_description && (
        <section className="list-section">
          <h2>映像から読み取った様子</h2>
          <p className="visual-description">{result.visual_description}</p>
          <p className="note">動画から取り出した数枚の静止画だけをもとにしたAIの説明です。採点の材料の一つとして使いました。</p>
        </section>
      )}

      <button onClick={onScoreAgain}>もう一度採点する</button>
      <button className="secondary-button" onClick={onReset}>
        最初からやり直す
      </button>
    </div>
  );
}
