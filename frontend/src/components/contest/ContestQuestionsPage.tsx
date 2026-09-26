import { useState } from "react";
import type { ContestRubric, ContestScoreResult, QuestionSet } from "../../types/contest";
import { ContestApiError, generateQuestions, loadQuestionSet, scoreAudio } from "../../api/contestApi";
import { CriteriaForm } from "./CriteriaForm";
import { LoadingState } from "../LoadingState";
import { QuestionSetReview } from "./QuestionSetReview";
import { SavedQuestionSetPicker } from "./SavedQuestionSetPicker";
import { AudioScoreForm } from "./AudioScoreForm";
import { ContestScoreResultView } from "./ContestScoreResultView";

type Status =
  | "form"
  | "generating"
  | "review"
  | "saved-list"
  | "loading-saved"
  | "audio-upload"
  | "scoring"
  | "score-result";

const GENERATING_STAGES = ["Questionを生成中…"];
const SCORING_STAGES = ["音声を文字起こし中…", "Jevが採点中…"];

export function ContestQuestionsPage() {
  const [status, setStatus] = useState<Status>("form");
  const [questionSet, setQuestionSet] = useState<QuestionSet | null>(null);
  const [scoreResult, setScoreResult] = useState<ContestScoreResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleGenerate(rubric: ContestRubric) {
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

  async function handleSelectSaved(id: string) {
    setStatus("loading-saved");
    setErrorMessage(null);
    try {
      const saved = await loadQuestionSet(id);
      setQuestionSet(saved.question_set);
      setStatus("review");
    } catch (err) {
      setErrorMessage(err instanceof ContestApiError ? err.message : "読み込み中にエラーが発生しました。");
      setStatus("saved-list");
    }
  }

  async function handleScoreAudio(file: File) {
    if (!questionSet) return;
    setStatus("scoring");
    setErrorMessage(null);
    try {
      const result = await scoreAudio(questionSet, file);
      setScoreResult(result);
      setStatus("score-result");
    } catch (err) {
      setErrorMessage(err instanceof ContestApiError ? err.message : "採点中にエラーが発生しました。");
      setStatus("audio-upload");
    }
  }

  function handleReset() {
    setQuestionSet(null);
    setScoreResult(null);
    setErrorMessage(null);
    setStatus("form");
  }

  switch (status) {
    case "generating":
      return <LoadingState stages={GENERATING_STAGES} />;
    case "loading-saved":
      return <LoadingState stages={["保存済みのQuestionsを読み込み中…"]} />;
    case "scoring":
      return <LoadingState stages={SCORING_STAGES} />;
    case "saved-list":
      return (
        <SavedQuestionSetPicker onSelect={handleSelectSaved} onBack={() => setStatus("form")} />
      );
    case "review":
      if (!questionSet) break;
      return (
        <QuestionSetReview
          questionSet={questionSet}
          onQuestionSetChange={setQuestionSet}
          onProceedToScoring={() => {
            setErrorMessage(null);
            setStatus("audio-upload");
          }}
          onReset={handleReset}
        />
      );
    case "audio-upload":
      if (!questionSet) break;
      return (
        <AudioScoreForm
          questionSet={questionSet}
          errorMessage={errorMessage}
          onSubmit={handleScoreAudio}
          onBack={() => setStatus("review")}
        />
      );
    case "score-result":
      if (!scoreResult) break;
      return (
        <ContestScoreResultView
          result={scoreResult}
          onScoreAgain={() => {
            setScoreResult(null);
            setStatus("audio-upload");
          }}
          onReset={handleReset}
        />
      );
  }

  return <CriteriaForm onSubmit={handleGenerate} onUseSaved={() => setStatus("saved-list")} errorMessage={errorMessage} />;
}
