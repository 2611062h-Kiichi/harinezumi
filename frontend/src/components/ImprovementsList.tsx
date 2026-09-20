import type { ImprovementSuggestion } from "../types/review";

export function ImprovementsList({ improvements }: { improvements: ImprovementSuggestion[] }) {
  if (improvements.length === 0) return null;
  return (
    <section className="list-section">
      <h2>改善提案</h2>
      <ul className="improvements">
        {improvements.map((imp, i) => (
          <li key={i}>
            <strong>{imp.point}</strong>
            <p>{imp.suggestion}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
