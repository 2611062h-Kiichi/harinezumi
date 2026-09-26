const POWERED_BY = ["Claude (Anthropic)", "Whisper (OpenAI)", "Jev (TypeSafe AI)"];

export function PoweredBy() {
  return (
    <p className="powered-by">
      Powered by {POWERED_BY.map((name, i) => (
        <span key={name}>
          <span className="powered-by-name">{name}</span>
          {i < POWERED_BY.length - 1 && <span className="powered-by-sep"> · </span>}
        </span>
      ))}
    </p>
  );
}
