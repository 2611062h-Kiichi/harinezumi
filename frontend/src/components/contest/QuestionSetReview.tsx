import { useState } from "react";
import type { FormEvent } from "react";
import type { JevScoreQuestion, QuestionSet } from "../../types/contest";
import { ContestApiError, saveQuestionSet } from "../../api/contestApi";
import { QuestionEditor } from "./QuestionEditor";

interface Props {
  questionSet: QuestionSet;
  onQuestionSetChange: (updated: QuestionSet) => void;
  onProceedToScoring: () => void;
  onReset: () => void;
}

type SaveStatus = "idle" | "saving" | "saved" | "error";

export function QuestionSetReview({ questionSet, onQuestionSetChange, onProceedToScoring, onReset }: Props) {
  const [saveName, setSaveName] = useState(questionSet.rubric.contest_name);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  const criteriaById = new Map(questionSet.rubric.criteria.map((c) => [c.id, c]));

  function updateQuestion(criterionId: string, updated: JevScoreQuestion) {
    onQuestionSetChange({
      ...questionSet,
      questions: questionSet.questions.map((q) => (q.criterion_id === criterionId ? updated : q)),
    });
    // Editing after a save invalidates the saved copy; ask the user to save again.
    if (saveStatus === "saved") {
      setSaveStatus("idle");
    }
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!saveName.trim()) {
      setSaveStatus("error");
      setSaveError("保存する名前を入力してください。");
      return;
    }
    setSaveStatus("saving");
    setSaveError(null);
    try {
      await saveQuestionSet(saveName.trim(), questionSet);
      setSaveStatus("saved");
    } catch (err) {
      setSaveStatus("error");
      setSaveError(err instanceof ContestApiError ? err.message : "保存中にエラーが発生しました。");
    }
  }

  return (
    <div className="question-set-review">
      <h1>Questionの確認・編集</h1>
      <p className="lead">
        {questionSet.rubric.contest_name} の採点観点から、{questionSet.questions.length}件のQuestionを作成しました。
        内容を確認し、必要なら文言を直してから保存してください。
      </p>

      <div className="question-editor-list">
        {/* Questions already come back in the organizer's criterion order (sorted server-side). */}
        {questionSet.questions.map((q, i) => {
          const criterion = criteriaById.get(q.criterion_id);
          if (!criterion) return null;
          return (
            <QuestionEditor
              key={q.criterion_id}
              index={i}
              criterion={criterion}
              question={q}
              onChange={(updated) => updateQuestion(q.criterion_id, updated)}
            />
          );
        })}
      </div>

      <form className="save-question-set-form" onSubmit={handleSave}>
        <label className="field">
          <span>保存する名前</span>
          <input type="text" value={saveName} onChange={(e) => setSaveName(e.target.value)} />
        </label>
        <button type="submit" disabled={saveStatus === "saving"}>
          {saveStatus === "saving" ? "保存中..." : "この内容を保存する"}
        </button>
        {saveStatus === "saved" && <p className="note save-success">保存しました。次回から一覧で選んで再利用できます。</p>}
        {saveStatus === "error" && saveError && <p className="error-text">{saveError}</p>}
      </form>

      <button onClick={onProceedToScoring}>この内容で音声を採点する</button>
      <button className="secondary-button" onClick={onReset}>
        別のコンテストの観点を入力する
      </button>
    </div>
  );
}
