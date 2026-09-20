import { useEffect, useState } from "react";

const STAGES = [
  "スライドを解析中…",
  "音声を文字起こし中…",
  "AIが審査中…（1分ほどかかる場合があります）",
];

export function LoadingState() {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, STAGES.length - 1));
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-state">
      <div className="spinner" aria-hidden="true" />
      <p>{STAGES[stageIndex]}</p>
    </div>
  );
}
