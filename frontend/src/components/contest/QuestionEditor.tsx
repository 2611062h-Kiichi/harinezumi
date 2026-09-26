import type { ContestCriterion, JevScoreQuestion } from "../../types/contest";

interface Props {
  index: number;
  criterion: ContestCriterion;
  question: JevScoreQuestion;
  onChange: (updated: JevScoreQuestion) => void;
}

export function QuestionEditor({ index, criterion, question, onChange }: Props) {
  function updateLevel(levelIndex: number, value: string) {
    const levels = question.levels.map((l, i) => (i === levelIndex ? value : l));
    onChange({ ...question, levels });
  }

  return (
    <div className="question-editor-card">
      <div className="question-editor-header">
        <span className="question-editor-index">観点{index + 1}</span>
        <span className="question-editor-name">{criterion.name}</span>
        <span className="question-editor-points">配点 {criterion.max_points}</span>
      </div>

      {criterion.description && (
        <p className="question-editor-original">
          主催者の説明: {criterion.description}
        </p>
      )}

      <label className="field">
        <span>Jevへの質問文</span>
        <textarea
          rows={2}
          value={question.instructions}
          onChange={(e) => onChange({ ...question, instructions: e.target.value })}
        />
      </label>

      <p className="note">
        AIが観点の説明を元に作った段階評価です。主催者の説明と見比べて、意図と違う場合は文言を直してください。
      </p>

      <div className="level-list">
        {question.levels.map((level, i) => (
          <label className="field level-field" key={i}>
            <span>段階{i + 1}（{i === 0 ? "最も低い" : i === question.levels.length - 1 ? "最も高い" : `${i + 1}番目`}）</span>
            <textarea rows={2} value={level} onChange={(e) => updateLevel(i, e.target.value)} />
          </label>
        ))}
      </div>
    </div>
  );
}
