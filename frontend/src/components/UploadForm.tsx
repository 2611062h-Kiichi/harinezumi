import { useState } from "react";
import type { FormEvent } from "react";
import type { RubricMode } from "../types/review";
import { PoweredBy } from "./PoweredBy";

const MAX_SLIDE_MB = 20;
const MAX_MEDIA_MB = 25; // Whisper's hard per-file limit

const RUBRIC_MODE_OPTIONS: { id: RubricMode; label: string }[] = [
  { id: "business", label: "ビジネスコンテスト向け（起業の科学ベース）" },
  { id: "general", label: "汎用ピッチ審査" },
];

const MAX_EVENT_CONTEXT_LENGTH = 300;

type MediaInputType = "file" | "url";

interface Props {
  onSubmit: (
    slideFile: File | null,
    mediaFile: File | null,
    mediaUrl: string | null,
    mode: RubricMode,
    eventContext: string | null,
  ) => void;
}

export function UploadForm({ onSubmit }: Props) {
  const [slideFile, setSlideFile] = useState<File | null>(null);
  const [mediaInputType, setMediaInputType] = useState<MediaInputType>("file");
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [mediaUrl, setMediaUrl] = useState("");
  const [mode, setMode] = useState<RubricMode>("business");
  const [eventContext, setEventContext] = useState("");
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

  function handleMediaInputTypeChange(type: MediaInputType) {
    setMediaInputType(type);
    setMediaFile(null);
    setMediaUrl("");
    setError(null);
  }

  const hasMedia = mediaInputType === "file" ? !!mediaFile : !!mediaUrl;
  const canSubmit = !!slideFile || hasMedia;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!slideFile && !hasMedia) {
      setError("スライド資料、または発表の音声・動画のいずれかを指定してください。");
      return;
    }
    if (mediaInputType === "url" && mediaUrl && !/^https?:\/\//i.test(mediaUrl)) {
      setError("音声/動画のURLは http:// または https:// から始まる必要があります。");
      return;
    }
    onSubmit(
      slideFile,
      mediaInputType === "file" ? mediaFile : null,
      mediaInputType === "url" && mediaUrl ? mediaUrl : null,
      mode,
      mode === "general" && eventContext.trim() ? eventContext.trim() : null,
    );
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h1>ピッチ審査を添削するAI</h1>
      <PoweredBy />
      <p className="lead">
        ピッチ資料（スライド）と発表の音声・動画をアップロードすると、AIが審査員として添削します。
        どちらか一方だけでも審査できます。
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

      {mode === "general" && (
        <label className="field">
          <span>イベント内容（任意）</span>
          <textarea
            rows={2}
            maxLength={MAX_EVENT_CONTEXT_LENGTH}
            placeholder="例: 学生団体主催のアプリ開発ハッカソン、社会人向け新規事業ピッチコンテストなど"
            value={eventContext}
            onChange={(e) => setEventContext(e.target.value)}
          />
          <p className="note">
            イベントの内容を入力すると、その内容に合わせてAIが専用の審査基準を作成します。空欄の場合は汎用の審査基準を使用します。
          </p>
        </label>
      )}

      <label className="field">
        <span>スライド資料（PDF / PPTX、任意）</span>
        <input type="file" accept=".pdf,.pptx" onChange={handleSlideChange} />
      </label>

      <div className="field">
        <span>発表の音声・動画（任意）</span>
        <div className="media-input-toggle">
          <label>
            <input
              type="radio"
              name="media-input-type"
              checked={mediaInputType === "file"}
              onChange={() => handleMediaInputTypeChange("file")}
            />
            ファイルをアップロード
          </label>
          <label>
            <input
              type="radio"
              name="media-input-type"
              checked={mediaInputType === "url"}
              onChange={() => handleMediaInputTypeChange("url")}
            />
            URLを指定
          </label>
        </div>

        {mediaInputType === "file" ? (
          <input type="file" accept=".mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm" onChange={handleMediaChange} />
        ) : (
          <>
            <input
              type="url"
              placeholder="https://example.com/pitch.mp4 または YouTubeなどのURL"
              value={mediaUrl}
              onChange={(e) => setMediaUrl(e.target.value)}
            />
            <p className="note">
              直接リンクされた音声/動画ファイル、またはYouTubeなど対応プラットフォームのURLに対応しています。
              著作権・利用規約上、自分に権利のあるコンテンツのみ指定してください。
            </p>
          </>
        )}
      </div>

      {error && <p className="error-text">{error}</p>}

      <button type="submit" disabled={!canSubmit}>
        審査を開始する
      </button>
    </form>
  );
}
