import type { RubricPreviewResponse } from "../types/review";

interface Props {
  preview: RubricPreviewResponse;
}

export function RubricPreviewPanel({ preview }: Props) {
  return (
    <div className="rubric-preview">
      <p className="rubric-preview-label">{preview.rubric_mode_label}</p>
      <ul className="rubric-preview-list">
        {preview.criteria.map((c) => (
          <li key={c.id}>
            <details>
              <summary>{c.name}</summary>
              <ol>
                {c.levels.map((level, i) => (
                  <li key={i}>
                    <span className="criterion-level-num">{i + 1}点</span> {level}
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
