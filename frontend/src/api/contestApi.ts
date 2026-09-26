import type { ContestRubric, ContestScoreResult, QuestionSet, SavedQuestionSet, SavedQuestionSetSummary } from "../types/contest";

const REQUEST_TIMEOUT_MS = 5 * 60 * 1000;

// Same convention as reviewApi.ts: unset locally (Vite proxies relative
// /api/... to localhost:8000); set to the deployed backend's URL in
// production when the frontend and backend are separate origins.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ContestApiError extends Error {}

async function fetchWithTimeout(path: string, init?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ContestApiError("処理がタイムアウトしました。もう一度お試しください。");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ContestApiError(data?.detail ?? `リクエストに失敗しました (HTTP ${response.status})`);
  }
  return response.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  return readResponse<T>(await fetchWithTimeout(path));
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  return readResponse<T>(
    await fetchWithTimeout(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
}

export function generateQuestions(rubric: ContestRubric): Promise<QuestionSet> {
  return postJson<QuestionSet>("/api/contest/questions", rubric);
}

export function saveQuestionSet(name: string, questionSet: QuestionSet): Promise<SavedQuestionSet> {
  return postJson<SavedQuestionSet>("/api/contest/question-sets", { name, question_set: questionSet });
}

export function listQuestionSets(): Promise<SavedQuestionSetSummary[]> {
  return getJson<SavedQuestionSetSummary[]>("/api/contest/question-sets");
}

export function loadQuestionSet(id: string): Promise<SavedQuestionSet> {
  return getJson<SavedQuestionSet>(`/api/contest/question-sets/${encodeURIComponent(id)}`);
}

export async function scoreAudio(questionSet: QuestionSet, mediaFile: File): Promise<ContestScoreResult> {
  const formData = new FormData();
  formData.append("media_file", mediaFile);
  formData.append("question_set", JSON.stringify(questionSet));
  // No Content-Type header: the browser sets the multipart boundary itself.
  return readResponse<ContestScoreResult>(await fetchWithTimeout("/api/contest/score", { method: "POST", body: formData }));
}
