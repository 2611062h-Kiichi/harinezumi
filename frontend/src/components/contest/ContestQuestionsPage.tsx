import { useState } from "react";
import type { ContestRubric, QuestionSet } from "../../types/contest";
import { ContestApiError, generateQuestions } from "../../api/contestApi";
import { CriteriaForm } from "./CriteriaForm";
import { LoadingState } from "../LoadingState";
import { QuestionSetReview } from "./QuestionSetReview";

type Status = "form" | "generating" | "review";

export function ContestQuestionsPage() {
  const [status, setStatus] = useState<Status>("form");
  const [questionSet, setQuestionSet] = useState<QuestionSet | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(rubric: ContestRubric) {
    setStatus("generating");
    setErrorMessage(null);
    try {
      const result = await generateQuestions(rubric);
      setQuestionSet(result);
      setStatus("review");
    } catch (err) {
      setErrorMessage(err instanceof ContestApiError ? err.message : "Questionの生成中にエラーが発生しました。");
      setStatus("form");
    }
  }

  function handleReset() {
    setQuestionSet(null);
    setErrorMessage(null);
    setStatus("form");
  }

  if (status === "generating") {
    return <LoadingState />;
  }
  if (status === "review" && questionSet) {
    return (
      <QuestionSetReview questionSet={questionSet} onQuestionSetChange={setQuestionSet} onReset={handleReset} />
    );
  }
  return <CriteriaForm onSubmit={handleSubmit} errorMessage={errorMessage} />;
}
