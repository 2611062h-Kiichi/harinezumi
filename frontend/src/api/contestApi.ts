// Covers only the endpoints this screen (T09) uses. Listing/loading a saved
// Question set belongs to the audio-upload screen (T10) and is added there.
import type { ContestRubric, QuestionSet, SavedQuestionSet } from "../types/contest";

export class ContestApiError extends Error {}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ContestApiError(data?.detail ?? `リクエストに失敗しました (HTTP ${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function generateQuestions(rubric: ContestRubric): Promise<QuestionSet> {
  return postJson<QuestionSet>("/api/contest/questions", rubric);
}

export function saveQuestionSet(name: string, questionSet: QuestionSet): Promise<SavedQuestionSet> {
  return postJson<SavedQuestionSet>("/api/contest/question-sets", { name, question_set: questionSet });
}
