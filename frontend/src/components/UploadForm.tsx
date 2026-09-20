import { useState } from "react";
import type { FormEvent } from "react";
import type { RubricMode } from "../types/review";

const MAX_SLIDE_MB = 20;
const MAX_MEDIA_MB = 300;

const RUBRIC_MODE_OPTIONS: { id: RubricMode; label: string }[] = [
  { id: "business", label: "ビジネスコンテスト向け（起業の科学ベース）" },
  { id: "general", label: "汎用ピッチ審査" },
];

interface Props {
  onSubmit: (slideFile: File, mediaFile: File | null, mode: RubricMode) => void;
}

export function UploadForm({ onSubmit }: Props) {
  const [slideFile, setSlideFile] = useState<File | null>(null);
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [mode, setMode] = useState<RubricMode>("business");
  const [error, setError] = useState<string | null>(null);

  function handleSlideChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    if (file && file.size > MAX_SLIDE_MB * 1024 * 1024) {
      setError(`スライドファイルが大きすぎます（上限 ${MAX_SLIDE_MB}MB）。`);
      setSlideFile(null);
      return;
    }
    setError(null);
    setSlideFile(file);
  }

  function handleMediaChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    if (file && file.size > MAX_MEDIA_MB * 1024 * 1024) {
      setError(`音声/動画ファイルが大きすぎます（上限 ${MAX_MEDIA_MB}MB）。`);
      setMediaFile(null);
      return;
    }
    setError(null);
    setMediaFile(file);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!slideFile) {
      setError("スライド資料（PDF または PPTX）を選択してください。");
      return;
    }
    onSubmit(slideFile, mediaFile, mode);
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h1>ピッチ審査を添削するAI</h1>
      <p className="lead">
        ピッチ資料と、任意で発表の音声・動画をアップロードすると、AIが審査員として添削します。
      </p>

      <label className="field">
        <span>審査モード</span>
        <select value={mode} onChange={(e) => setMode(e.target.value as RubricMode)}>
          {RUBRIC_MODE_OPTIONS.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>スライド資料（PDF / PPTX）*</span>
        <input type="file" accept=".pdf,.pptx" onChange={handleSlideChange} />
      </label>

      <label className="field">
        <span>発表の音声・動画（任意）</span>
        <input type="file" accept="audio/*,video/*" onChange={handleMediaChange} />
      </label>

      {error && <p className="error-text">{error}</p>}

      <button type="submit" disabled={!slideFile}>
        審査を開始する
      </button>
    </form>
  );
}
