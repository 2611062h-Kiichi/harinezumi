import type { RubricCriterionPreview, RubricPreviewResponse } from "../types/review";

interface Props {
  preview: RubricPreviewResponse;
  editable?: boolean;
  onChange?: (criteria: RubricCriterionPreview[]) => void;
}

export function RubricPreviewPanel({ preview, editable = false, onChange }: Props) {
  function updateName(index: number, name: string) {
    if (!onChange) return;
    onChange(preview.criteria.map((c, i) => (i === index ? { ...c, name } : c)));
  }

  return (
    <div className="rubric-preview">
      <p className="rubric-preview-label">{preview.rubric_mode_label}</p>
      {editable && <p className="note">項目名を編集できます（審査時にその内容が使われます）。各点数の判定基準は変更できません。</p>}
      <ul className="rubric-preview-list">
        {preview.criteria.map((c, critIndex) => (
          <li key={c.id}>
            <details open={editable}>
              <summary>
                {editable ? (
                  <input
                    type="text"
                    value={c.name}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => updateName(critIndex, e.target.value)}
                  />
                ) : (
                  c.name
                )}
              </summary>
              <ol>
                {c.levels.map((level, levelIndex) => (
                  <li key={levelIndex}>
                    <span className="criterion-level-num">{levelIndex + 1}点</span> {level}
                  </li>
                ))}
              </ol>
            </details>
          </li>
        ))}
      </ul>
    </div>
  );
}
