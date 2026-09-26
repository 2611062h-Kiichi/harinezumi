import { useState } from "react";
import type { FormEvent } from "react";
import type { ContestCriterion, ContestRubric } from "../../types/contest";
import { MAX_CRITERIA } from "../../types/contest";

const MIN_POINTS = 1;
const MAX_POINTS = 100;

interface CriterionInput {
  name: string;
  description: string;
  maxPoints: string; // kept as text while editing so the field can be empty
}

function emptyCriterion(): CriterionInput {
  return { name: "", description: "", maxPoints: "" };
}

interface Props {
  onSubmit: (rubric: ContestRubric) => void;
  errorMessage: string | null;
}

export function CriteriaForm({ onSubmit, errorMessage }: Props) {
  const [contestName, setContestName] = useState("");
  const [criteria, setCriteria] = useState<CriterionInput[]>([emptyCriterion()]);
  const [localError, setLocalError] = useState<string | null>(null);

  function updateCriterion(index: number, patch: Partial<CriterionInput>) {
    setCriteria((prev) => prev.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  }

  function addCriterion() {
    setCriteria((prev) => (prev.length >= MAX_CRITERIA ? prev : [...prev, emptyCriterion()]));
  }

  function removeCriterion(index: number) {
    setCriteria((prev) => (prev.length <= 1 ? prev : prev.filter((_, i) => i !== index)));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLocalError(null);

    if (!contestName.trim()) {
      setLocalError("コンテスト名を入力してください。");
      return;
    }
    for (const [i, c] of criteria.entries()) {
      if (!c.name.trim()) {
        setLocalError(`観点${i + 1}の名前を入力してください。`);
        return;
      }
      const points = Number(c.maxPoints);
      if (!Number.isInteger(points) || points < MIN_POINTS || points > MAX_POINTS) {
        setLocalError(`観点${i + 1}の配点は${MIN_POINTS}〜${MAX_POINTS}の整数で入力してください。`);
        return;
      }
    }

    const rubricCriteria: ContestCriterion[] = criteria.map((c, i) => ({
      // The id is an internal join key between the criterion and its
      // generated Question; the user never needs to see or type it.
      id: `c${i + 1}`,
      name: c.name.trim(),
      description: c.description.trim(),
      max_points: Number(c.maxPoints),
    }));

    onSubmit({ contest_name: contestName.trim(), criteria: rubricCriteria });
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h1>コンテスト観点モード</h1>
      <p className="lead">
        出場するピッチコンテストの採点観点を入力すると、AIがJev（採点AI）用の質問（Question）を作成します。
        生成後に文言を確認・編集してから、発表の採点に使えます。
      </p>

      <label className="field">
        <span>コンテスト名</span>
        <input
          type="text"
          value={contestName}
          onChange={(e) => setContestName(e.target.value)}
          placeholder="例: 学生ビジネスプランコンテスト2026"
        />
      </label>

      <div className="criterion-list">
        {criteria.map((c, i) => (
          <div className="criterion-input-card" key={i}>
            <div className="criterion-input-header">
              <span>観点{i + 1}</span>
              {criteria.length > 1 && (
                <button type="button" className="link-button" onClick={() => removeCriterion(i)}>
                  削除
                </button>
              )}
            </div>

            <label className="field">
              <span>名前</span>
              <input
                type="text"
                value={c.name}
                onChange={(e) => updateCriterion(i, { name: e.target.value })}
                placeholder="例: 課題の明確さ"
              />
            </label>

            <label className="field">
              <span>説明（任意）</span>
              <textarea
                rows={2}
                value={c.description}
                onChange={(e) => updateCriterion(i, { description: e.target.value })}
                placeholder="主催者の採点基準の説明があれば、そのまま貼り付けてください。"
              />
            </label>

            <label className="field">
              <span>配点（{MIN_POINTS}〜{MAX_POINTS}）</span>
              <input
                type="number"
                min={MIN_POINTS}
                max={MAX_POINTS}
                value={c.maxPoints}
                onChange={(e) => updateCriterion(i, { maxPoints: e.target.value })}
              />
            </label>
          </div>
        ))}
      </div>

      <button type="button" className="secondary-button" onClick={addCriterion} disabled={criteria.length >= MAX_CRITERIA}>
        観点を追加する（{criteria.length}/{MAX_CRITERIA}）
      </button>

      {(localError || errorMessage) && <p className="error-text">{localError ?? errorMessage}</p>}

      <button type="submit">Questionを生成する</button>
    </form>
  );
}
