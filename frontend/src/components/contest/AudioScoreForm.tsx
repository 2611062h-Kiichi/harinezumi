import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import type { QuestionSet } from "../../types/contest";

// Same accepted extensions and per-file limits as the pitch-review upload form
// (backend/app/routers/review.py MEDIA_EXTS / SLIDE_EXTS, backend/app/config.py).
const MAX_MEDIA_MB = 25;
const MAX_SLIDE_MB = 20;
// Contest-mode only (backend/app/config.py max_contest_slide_*); checked by the server.
const MAX_SLIDE_PAGES = 60;
const MAX_SLIDE_CHARS = 30000;

interface Props {
  questionSet: QuestionSet;
  errorMessage: string | null;
  onSubmit: (mediaFile: File | null, slideFile: File | null) => void;
  onBack: () => void;
}

export function AudioScoreForm({ questionSet, errorMessage, onSubmit, onBack }: Props) {
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [slideFile, setSlideFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  function pick(e: ChangeEvent<HTMLInputElement>, maxMb: number, label: string, set: (f: File | null) => void) {
    const selected = e.target.files?.[0] ?? null;
    if (selected && selected.size > maxMb * 1024 * 1024) {
      setLocalError(`${label}が大きすぎます（上限 ${maxMb}MB）。`);
      set(null);
      return;
    }
    setLocalError(null);
    set(selected);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!mediaFile && !slideFile) {
      setLocalError("スライド資料、または発表の音声・動画のどちらかを選択してください。");
      return;
    }
    onSubmit(mediaFile, slideFile);
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h1>発表を採点する</h1>
      <p className="lead">
        {questionSet.rubric.contest_name} のQuestion（{questionSet.questions.length}件）で採点します。
        スライド資料と発表の音声・動画のどちらか一方だけでも、両方でも採点できます。
      </p>

      <label className="field">
        <span>スライド資料（PDF / PPTX、任意）</span>
        <input type="file" accept=".pdf,.pptx" onChange={(e) => pick(e, MAX_SLIDE_MB, "スライドファイル", setSlideFile)} />
      </label>

      <label className="field">
        <span>発表の音声・動画（任意）</span>
        <input
          type="file"
          accept=".mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm"
          onChange={(e) => pick(e, MAX_MEDIA_MB, "音声/動画ファイル", setMediaFile)}
        />
      </label>

      <p className="note">
        スライドは文字（スピーカーノート・表・グループ化した図形の中の文字を含む）だけを読み取ります。図や画像の中の文字は読み取れません。
        スライドは{MAX_SLIDE_PAGES}ページ・{MAX_SLIDE_CHARS.toLocaleString()}文字（ノートを含む）までです。
      </p>
      <p className="note">
        動画（mp4 / webm）を選ぶと、静止画数枚から表情・姿勢・身振り手振りもAIが読み取り、採点の材料にします。
      </p>

      {(localError || errorMessage) && <p className="error-text">{localError ?? errorMessage}</p>}

      <button type="submit" disabled={!mediaFile && !slideFile}>
        採点する
      </button>
      <button type="button" className="secondary-button" onClick={onBack}>
        Questionの編集に戻る
      </button>
    </form>
  );
}
