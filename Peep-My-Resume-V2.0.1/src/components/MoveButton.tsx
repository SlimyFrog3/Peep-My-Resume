import { useId } from 'react'

export default function MoveButton({ direction, label, disabled, onClick }: {
  direction: 'up' | 'down'; label: string; disabled?: boolean; onClick: () => void
}) {
  const id = useId()
  return <span className="move-control">
    <button type="button" className="browse move-button" aria-label={label} aria-describedby={id}
      title={label} disabled={disabled} onClick={onClick}>
      <svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.3" strokeLinecap="round" strokeLinejoin="round">
        {direction === 'up' ? <path d="M12 20V4M5 11l7-7 7 7" /> : <path d="M12 4v16M5 13l7 7 7-7" />}
      </svg><span>{direction === 'up' ? 'Move up' : 'Move down'}</span>
    </button>
    <span id={id} role="tooltip" className="move-tooltip">{label}{disabled ? ' — already at the edge' : ''}</span>
  </span>
}
