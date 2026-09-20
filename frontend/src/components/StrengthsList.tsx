export function StrengthsList({ strengths }: { strengths: string[] }) {
  if (strengths.length === 0) return null;
  return (
    <section className="list-section">
      <h2>良かった点</h2>
      <ul>
        {strengths.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>
    </section>
  );
}
