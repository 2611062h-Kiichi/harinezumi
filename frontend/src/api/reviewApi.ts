import type { PitchReviewResponse } from "../types/review";

const REQUEST_TIMEOUT_MS = 5 * 60 * 1000;

export class ReviewApiError extends Error {}

export async function submitPitchReview(
  slideFile: File,
  mediaFile?: File | null,
): Promise<PitchReviewResponse> {
  const formData = new FormData();
  formData.append("slide_file", slideFile);
  if (mediaFile) {
    formData.append("media_file", mediaFile);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch("/api/review", {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new ReviewApiError(body?.detail ?? `審査に失敗しました (HTTP ${response.status})`);
    }

    return (await response.json()) as PitchReviewResponse;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ReviewApiError("処理がタイムアウトしました。もう一度お試しください。");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}
