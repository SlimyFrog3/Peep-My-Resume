import type { Readability } from '../types/ParseResult'

export default function ReadabilityScore({ value, title = 'Parsing Readiness' }: { value: Readability; title?: string }) {
  const label = value.status === 'could_not_assess' ? 'Couldn’t assess' : value.status === 'looks_good' ? 'Looks good' : value.status === 'needs_attention' ? 'Needs attention' : 'Needs review'
  const strengths = value.categories.filter(c => c.assessed && c.strength)
  return <div className={`parse-check parse-check--${value.status}`}>
    <div className="score-heading"><div><span>{title}</span><h3>{label}</h3></div>
      <div className="score-number">{value.score ?? '—'}<span>/100</span></div></div>
    {value.score !== null && <div className="score-track" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value.score} aria-label={`${title}: ${value.score} out of 100`}><span style={{ width: `${value.score}%` }} /></div>}
    {value.greenChecklist && <div className="green-checklist"><strong>{value.status === 'looks_good' ? 'Why this is green' : 'What it takes to get green'}</strong>
      <ul>{value.greenChecklist.map((item, i) => <li key={i}><span aria-hidden="true">{item.met ? '✓' : '○'}</span> <strong>{item.met ? 'Passed: ' : 'To check: '}</strong>{item.label}
        {!item.met && <p>{item.action}</p>}
      </li>)}</ul>
    </div>}
    <p>{value.score === null ? 'There is not enough recognizable information to give a reliable number.' : value.note}</p>
    {strengths.length > 0 && <div className="strengths"><strong>What’s working well</strong><ul>{strengths.map(c => <li key={c.key}><strong>{c.label}: {c.earned}/{c.possible}</strong><p>{c.strength}</p></li>)}</ul></div>}
    <details><summary>How this score works</summary><p>Rubric {value.rubricVersion}. Same rules for the original and exported file.</p>
      <ul className="rubric-list">{value.categories.map(c => <li key={c.key} className={`rubric-${c.status ?? 'review'}`}><strong>{c.label}: {c.earned}/{c.possible}</strong>
        <span className="rubric-badge">{c.assessed === false ? 'Not assessed · no deduction' : c.status === 'strong' ? 'Strong result' : c.status === 'attention' ? 'Needs attention' : 'Check this area'}</span><p>{c.detail}</p></li>)}</ul>
      <p>Green: at least 90 with no unresolved findings. Yellow: 55 or above with work to review. Red: below 55 or unable to assess. Absent optional sections do not cost points.</p>
    </details>
  </div>
}
