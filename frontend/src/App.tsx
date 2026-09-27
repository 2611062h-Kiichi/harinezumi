import { useState } from "react";
import { UploadForm } from "./components/UploadForm";
import { LoadingState } from "./components/LoadingState";
import { ReviewResult } from "./components/ReviewResult";
import { BrandMark } from "./components/BrandMark";
import { ContestQuestionsPage } from "./components/contest/ContestQuestionsPage";
import { submitPitchReview, ReviewApiError } from "./api/reviewApi";
import type { CustomRubricCriterion, PitchReviewResponse, RubricMode } from "./types/review";

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
    eventContext: string | null,
    criteriaNames: string[] | null,
    customRubric: CustomRubricCriterion[] | null,
  ) {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      const result = await submitPitchReview(
        slideFile,
        mediaFile,
        mediaUrl,
        mode,
        eventContext,
        criteriaNames,
        customRubric,
      );
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
      <a href="#main-content" className="skip-link">
        メインコンテンツへスキップ
      </a>

      <header className="site-header">
        <div className="brand">
          <BrandMark />
          <div>
            <p className="brand-name">harinezumi</p>
            <p className="brand-tagline">ピッチを、本番の審査基準で採点する</p>
          </div>
        </div>
        <nav className="app-mode-tabs" aria-label="モード切り替え" data-active={appMode}>
          <button
            type="button"
            className={appMode === "review" ? "app-mode-tab active" : "app-mode-tab"}
            aria-current={appMode === "review" ? "page" : undefined}
            onClick={() => setAppMode("review")}
          >
            ピッチ審査
          </button>
          <button
            type="button"
            className={appMode === "contest" ? "app-mode-tab active" : "app-mode-tab"}
            aria-current={appMode === "contest" ? "page" : undefined}
            onClick={() => setAppMode("contest")}
          >
            コンテスト観点モード
          </button>
        </nav>
      </header>

      <div id="main-content">
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
      </div>
    </main>
  );
}
