import { useState } from "react";
import { UploadForm } from "./components/UploadForm";
import { LoadingState } from "./components/LoadingState";
import { ReviewResult } from "./components/ReviewResult";
import { ContestQuestionsPage } from "./components/contest/ContestQuestionsPage";
import { submitPitchReview, ReviewApiError } from "./api/reviewApi";
import type { FeedbackTone, PitchReviewResponse, RubricMode } from "./types/review";

type Status = "idle" | "submitting" | "success" | "error";
type AppMode = "review" | "contest";

export default function App() {
  const [appMode, setAppMode] = useState<AppMode>("review");
  const [status, setStatus] = useState<Status>("idle");
  const [review, setReview] = useState<PitchReviewResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(
    slideFile: File | null,
    mediaFile: File | null,
    mediaUrl: string | null,
    mode: RubricMode,
    tone: FeedbackTone,
  ) {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      const result = await submitPitchReview(slideFile, mediaFile, mediaUrl, mode, tone);
      setReview(result);
      setStatus("success");
    } catch (err) {
      setErrorMessage(err instanceof ReviewApiError ? err.message : "審査中にエラーが発生しました。");
      setStatus("error");
    }
  }

  function handleReset() {
    setReview(null);
    setErrorMessage(null);
    setStatus("idle");
  }

  return (
    <main className="app">
      <nav className="app-mode-tabs">
        <button
          type="button"
          className={appMode === "review" ? "app-mode-tab active" : "app-mode-tab"}
          onClick={() => setAppMode("review")}
        >
          ピッチ審査
        </button>
        <button
          type="button"
          className={appMode === "contest" ? "app-mode-tab active" : "app-mode-tab"}
          onClick={() => setAppMode("contest")}
        >
          コンテスト観点モード
        </button>
      </nav>

      {appMode === "contest" ? (
        <ContestQuestionsPage />
      ) : (
        <>
          {status === "idle" && <UploadForm onSubmit={handleSubmit} />}
          {status === "submitting" && <LoadingState />}
          {status === "error" && (
            <div className="error-panel">
              <p className="error-text">{errorMessage}</p>
              <button onClick={handleReset}>やり直す</button>
            </div>
          )}
          {status === "success" && review && <ReviewResult review={review} onReset={handleReset} />}
        </>
      )}
    </main>
  );
}
