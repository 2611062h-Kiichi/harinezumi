import { useState } from "react";
import type { FormEvent } from "react";
import type { QuestionSet } from "../../types/contest";

// Same accepted extensions and per-file limit as the pitch-review upload form
// (backend/app/routers/review.py MEDIA_EXTS, backend/app/config.py max_media_mb).
const MAX_MEDIA_MB = 25;

interface Props {
  questionSet: QuestionSet;
  errorMessage: string | null;
  onSubmit: (file: File) => void;
  onBack: () => void;
}

export function AudioScoreForm({ questionSet, errorMessage, onSubmit, onBack }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    if (selected && selected.size > MAX_MEDIA_MB * 1024 * 1024) {
      setLocalError(`音声/動画ファイルが大きすぎます（上限 ${MAX_MEDIA_MB}MB）。`);
      setFile(null);
      return;
    }
    setLocalError(null);
    setFile(selected);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) {
      setLocalError("発表の音声・動画ファイルを選択してください。");
      return;
    }
    onSubmit(file);
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h1>発表を採点する</h1>
      <p className="lead">
        {questionSet.rubric.contest_name} のQuestion（{questionSet.questions.length}件）で、発表の音声・動画を採点します。
      </p>

      <label className="field">
        <span>発表の音声・動画</span>
        <input type="file" accept=".mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm" onChange={handleFileChange} />
      </label>

      {(localError || errorMessage) && <p className="error-text">{localError ?? errorMessage}</p>}

      <button type="submit" disabled={!file}>
        採点する
      </button>
      <button type="button" className="secondary-button" onClick={onBack}>
        Questionの編集に戻る
      </button>
    </form>
  );
}
