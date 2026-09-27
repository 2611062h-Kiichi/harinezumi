import { useEffect, useState } from "react";

const DEFAULT_STAGES = [
  "スライドを解析中…",
  "音声を文字起こし中…",
  "AIが審査中…（1分ほどかかる場合があります）",
];

interface Props {
  // Defaults to the pitch-review stages above; pass a screen-specific list
  // (e.g. contest mode's "Questionを生成中…") so the message stays accurate.
  stages?: string[];
}

// The server does not report progress, so stages advance on a timer as an
// estimate; the last stage stays active until the response arrives.
export function LoadingState({ stages = DEFAULT_STAGES }: Props) {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    setStageIndex(0);
    const interval = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, stages.length - 1));
    }, 8000);
    return () => clearInterval(interval);
  }, [stages]);

  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p className="loading-current">{stages[stageIndex]}</p>
      {stages.length > 1 && (
        <ol className="loading-steps">
          {stages.map((stage, i) => (
            <li key={stage} className={i < stageIndex ? "done" : i === stageIndex ? "current" : undefined}>
              {stage.replace(/….*$/, "")}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
