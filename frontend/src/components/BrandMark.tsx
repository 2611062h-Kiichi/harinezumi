// Hedgehog ("harinezumi") mark; same drawing as public/favicon.svg.
export function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="16" fill="currentColor" />
      <path d="M14 42c0-11 8-20 19-20 8 0 14 4 17 11l4 1-3 3c-1 3-4 5-8 5H14z" fill="#f6f1ea" />
      <path
        d="M18 34l-5-4 7 0-3-6 7 3 0-7 5 6 3-7 3 7 4-5 1 7 5-3"
        fill="none"
        stroke="#f6f1ea"
        strokeWidth="3"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle cx="44" cy="35" r="2" fill="#2b1d17" />
    </svg>
  );
}
