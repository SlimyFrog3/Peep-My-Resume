import type { Readability } from '../types/ParseResult'

export default function ReadabilityScore({ value, title = 'Parsing Readiness' }: { value: Readability; title?: string }) {
  const label = value.score === null ? 'Couldn’t assess' : value.status === 'looks_good' ? 'Looks good' : 'Needs review'
  return <div className={`parse-check parse-check--${value.status}`}>
    <div className="score-heading"><div><span>{title}</span><h3>{label}</h3></div>
      <div className="score-number">{value.score ?? '—'}<span>/100</span></div></div>
    {value.score !== null && <meter min={0} max={100} value={value.score} aria-label={`${title}: ${value.score} out of 100`} />}
    <p>{value.score === null ? 'There is not enough recognizable information to give a reliable number. Unreadable uploads cannot be scored.' : value.note}</p>
    <details><summary>How this score works</summary><p>Rubric {value.rubricVersion}. Same rules for the original and exported file. This is a check of our parser’s output.</p>
      <ul>{value.categories.map(c => <li key={c.key}><strong>{c.label}: {c.earned}/{c.possible}</strong><p>{c.detail}</p></li>)}</ul>
      <p>90–100 with no review findings: Looks good. Other assessable results: Needs review. Missing optional sections do not cost points.</p>
    </details>
  </div>
}
