import { useEffect, useState } from "react";
import type { SavedQuestionSetSummary } from "../../types/contest";
import { ContestApiError, listQuestionSets } from "../../api/contestApi";
import { LoadingState } from "../LoadingState";

const LOADING_STAGES = ["保存済みのQuestionsを読み込み中…"];

interface Props {
  onSelect: (id: string) => void;
  onBack: () => void;
}

export function SavedQuestionSetPicker({ onSelect, onBack }: Props) {
  const [summaries, setSummaries] = useState<SavedQuestionSetSummary[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listQuestionSets()
      .then((result) => {
        if (!cancelled) setSummaries(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setErrorMessage(err instanceof ContestApiError ? err.message : "一覧の取得中にエラーが発生しました。");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (summaries === null && !errorMessage) {
    return <LoadingState stages={LOADING_STAGES} />;
  }

  return (
    <div className="upload-form">
      <h1>保存済みのQuestionsを選ぶ</h1>
      <p className="lead">以前保存したQuestionセットを選ぶと、確認・編集画面から続けられます。</p>

      {errorMessage && <p className="error-text">{errorMessage}</p>}

      {summaries && summaries.length === 0 && <p className="note">保存済みのQuestionセットはまだありません。</p>}

      {summaries && summaries.length > 0 && (
        <ul className="saved-question-set-list">
          {summaries.map((s) => (
            <li key={s.id} className="saved-question-set-row">
              <div>
                <p className="saved-question-set-name">{s.name}</p>
                <p className="note">
                  {s.contest_name} ・ 観点{s.criteria_count}件 ・{" "}
                  {new Date(s.saved_at).toLocaleString("ja-JP")}
                </p>
              </div>
              <button type="button" onClick={() => onSelect(s.id)}>
                選ぶ
              </button>
            </li>
          ))}
        </ul>
      )}

      <button type="button" className="secondary-button" onClick={onBack}>
        戻る
      </button>
    </div>
  );
}
