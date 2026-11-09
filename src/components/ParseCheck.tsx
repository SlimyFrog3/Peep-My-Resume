import type { ParseCheckResult } from '../types/ParseResult'

const labels = {
  looks_good: 'Looks good',
  needs_review: 'Needs review',
  could_not_assess: 'Couldn’t assess',
} as const

export default function ParseCheck({ check }: { check: ParseCheckResult }) {
  const { status, reasons } = check
  return <div className={`parse-check parse-check--${status}`}>
    <div className="parse-check-title"><span>Parse Check</span><strong>{labels[status]}</strong></div>
    {reasons.length > 0
      ? <ul>{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>
      : <p>No issues flagged in the fields this parser detected. Compare them with the original.</p>}
    <small>Checks this parse only. It doesn’t predict ATS acceptance.</small>
  </div>
}
