import type { PitchReviewResponse, RubricMode } from "../types/review";

const REQUEST_TIMEOUT_MS = 5 * 60 * 1000;

// Local dev: unset, so requests go to relative /api/... and Vite's dev-server
// proxy forwards them to localhost:8000. Production: set to the deployed
// backend's URL (e.g. https://harinezumi-backend.vercel.app) since the
// frontend and backend are separate Vercel projects/origins there.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ReviewApiError extends Error {}

export async function submitPitchReview(
  slideFile: File | null | undefined,
  mediaFile: File | null | undefined,
  mediaUrl: string | null | undefined,
  mode: RubricMode,
): Promise<PitchReviewResponse> {
  const formData = new FormData();
  if (slideFile) {
    formData.append("slide_file", slideFile);
  }
  formData.append("mode", mode);
  if (mediaFile) {
    formData.append("media_file", mediaFile);
  } else if (mediaUrl) {
    formData.append("media_url", mediaUrl);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}/api/review`, {
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
