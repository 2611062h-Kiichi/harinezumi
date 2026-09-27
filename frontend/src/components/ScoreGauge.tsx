import type { CSSProperties } from "react";

interface Props {
  value: number;
  max: number;
  // Shown in the middle; defaults to the value itself.
  display?: string | number;
}

// Ring gauge for an overall score; the arc is drawn in CSS from --pct.
export function ScoreGauge({ value, max, display }: Props) {
  const pct = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
  return (
    <div
      className="score-gauge"
      style={{ "--pct": pct } as CSSProperties}
      role="img"
      aria-label={`${display ?? value} / ${max}`}
    >
      <div className="score-gauge-inner">
        <span className="score-gauge-value">{display ?? value}</span>
        <span className="score-gauge-max">/ {max}</span>
      </div>
    </div>
  );
}
