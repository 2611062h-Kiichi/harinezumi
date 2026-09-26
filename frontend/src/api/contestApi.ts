import type { ContestRubric, ContestScoreResult, QuestionSet, SavedQuestionSet, SavedQuestionSetSummary } from "../types/contest";

export class ContestApiError extends Error {}

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ContestApiError(data?.detail ?? `リクエストに失敗しました (HTTP ${response.status})`);
  }
  return response.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  return readResponse<T>(await fetch(path));
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  return readResponse<T>(
    await fetch(path, {
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
  return readResponse<ContestScoreResult>(await fetch("/api/contest/score", { method: "POST", body: formData }));
}
