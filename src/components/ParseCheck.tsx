import { reviewSections, type ParseCheckResult } from '../types/ParseResult'

const labels = {
  looks_good: 'Looks good',
  needs_review: 'Needs review',
  could_not_assess: 'Couldn’t assess',
} as const

export default function ParseCheck({ check }: { check: ParseCheckResult }) {
  const { status, reasons, findings } = check
  return <div className={`parse-check parse-check--${status}`}>
    <div className="parse-check-title"><span>Parse Check</span><strong>{labels[status]}</strong></div>
    {findings?.length ? <ul className="parse-findings">{findings.map(({ message, nextStep, section }, index) =>
      <li key={index}>
        <p>{message}</p>
        <p><strong>What to do:</strong> {nextStep}</p>
        <a href={`#review-${section}`} onClick={() => {
          if (section === 'extractedText') {
            const details = document.getElementById('review-extractedText')
            if (details instanceof HTMLDetailsElement) details.open = true
          }
        }}>View {reviewSections[section]}</a>
      </li>
    )}</ul> : reasons.length > 0
      ? <ul>{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>
      : <p>No issues flagged in the fields this parser detected. Compare them with the original.</p>}
    {check.observations?.length ? <div><strong>Recognized structure</strong><ul>{check.observations.map(note => <li key={note.message}><p>{note.message}</p><p>{note.nextStep}</p></li>)}</ul></div> : null}
    <small>Checks this parse only. It doesn’t predict ATS acceptance.</small>
  </div>
}
