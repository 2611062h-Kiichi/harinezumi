import { useState } from "react";
import { UploadForm } from "./components/UploadForm";
import { LoadingState } from "./components/LoadingState";
import { ReviewResult } from "./components/ReviewResult";
import { submitPitchReview, ReviewApiError } from "./api/reviewApi";
import type { PitchReviewResponse, RubricMode } from "./types/review";

type Status = "idle" | "submitting" | "success" | "error";

export default function App() {
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
  ) {
    setStatus("submitting");
    setErrorMessage(null);
    try {
      const result = await submitPitchReview(slideFile, mediaFile, mediaUrl, mode, eventContext, criteriaNames);
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
      {status === "idle" && <UploadForm onSubmit={handleSubmit} />}
      {status === "submitting" && <LoadingState />}
      {status === "error" && (
        <div className="error-panel">
          <p className="error-text">{errorMessage}</p>
          <button onClick={handleReset}>やり直す</button>
        </div>
      )}
      {status === "success" && review && <ReviewResult review={review} onReset={handleReset} />}
    </main>
  );
}
