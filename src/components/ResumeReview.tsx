import { useEffect, useRef, useState } from 'react'
import { sections, type AISuggestion, type ExportPreview, type ParseResult, type ReviewBlock } from '../types/ParseResult'
import { aiSuggestions, capabilities, exportResume, previewResume } from '../services/reviewApi'
import ReadabilityScore from './ReadabilityScore'

export default function ResumeReview({ result, demoMode }: { result: ParseResult; demoMode: boolean }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [blocks, setBlocks] = useState<ReviewBlock[]>(() => structuredClone(result.reviewBlocks))
  const [preview, setPreview] = useState<ExportPreview | null>(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [aiEnabled, setAiEnabled] = useState(false)
  const [consent, setConsent] = useState(false)
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([])
  const [aiMessage, setAiMessage] = useState('')
  const [approved, setApproved] = useState(false)
  const [changesAccepted, setChangesAccepted] = useState(false)
  const [tab, setTab] = useState<'edit' | 'preview'>('edit')
  useEffect(() => { void capabilities().then(c => setAiEnabled(c.aiEnabled)).catch(() => {}) }, [])
  function edit(next: ReviewBlock[]) {
    setBlocks(next); setPreview(null); setApproved(false); setChangesAccepted(false); setError('')
    setSuggestions([]); setAiMessage('')
  }
  function update(id: string, patch: Partial<ReviewBlock>) {
    edit(blocks.map(block => block.id === id ? { ...block, ...patch } : block))
  }
  function move(index: number, delta: number) {
    const next = [...blocks]
    ;[next[index], next[index + delta]] = [next[index + delta], next[index]]
    edit(next)
  }
  async function check() {
    setBusy('Checking the actual DOCX…'); setError('')
    try { setPreview(await previewResume(result.reviewBlocks, blocks)); setTab('preview') }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not preview the file.') }
    finally { setBusy('') }
  }
  async function download() {
    setBusy('Preparing your download…'); setError('')
    try {
      const blob = await exportResume(result.reviewBlocks, blocks)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = 'Peep-My-Resume.docx'; a.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not export the file.') }
    finally { setBusy('') }
  }
  async function askAI() {
    setBusy('Requesting organization suggestions…'); setError(''); setSuggestions([])
    try {
      const next = await aiSuggestions(blocks)
      setSuggestions(next); setAiMessage(next.length ? 'Review each suggestion below. Nothing has changed yet.' : 'No section moves suggested. You can still make corrections manually.')
    } catch (e) { setError(e instanceof Error ? e.message : 'AI review is unavailable.') }
    finally { setBusy('') }
  }
  const changed = preview && (preview.coverage.removedTokenCount > 0 || preview.coverage.addedTokenCount > 0)
  const canDownload = preview?.exportPreservesApprovedWords && approved && (!changed || changesAccepted)
  return <div className="review-launch">
    <h3>Make a cleaner copy</h3><p>Review every section, correct associations, and export an editable single-column DOCX. Your wording stays yours.</p>
    <button className="primary" disabled={demoMode} onClick={() => dialog.current?.showModal()}>Review &amp; create DOCX</button>
    {demoMode && <p>Upload a real resume to use export.</p>}
    <dialog className="review-dialog" ref={dialog} aria-labelledby="editor-heading">
      <div className="review-top"><div><span className="eyebrow">REVIEW BEFORE EXPORT</span><h2 id="editor-heading">Your resume, under your control</h2></div>
        <button className="browse" onClick={() => dialog.current?.close()}>Close review</button></div>
      <p>Compare with your original file. Edit wording, change sections, add missing content, or split a block by adding blank lines. The template groups standard sections and keeps your block order within each section.</p>
      <div className="review-tabs">
        <button className="browse" aria-pressed={tab === 'edit'} onClick={() => setTab('edit')}>1. Edit content</button>
        <button className="browse" aria-pressed={tab === 'preview'} onClick={() => setTab('preview')}>2. Preview &amp; compare</button>
      </div>
      <fieldset disabled={!!busy} className="review-fieldset">
      {tab === 'edit' ? <>
        <details className="ai-panel"><summary>Optional AI organization suggestions</summary>
          <p>Send the current non-contact blocks to OpenAI to suggest section moves. Names or personal details in other sections may still be included. Contact blocks, detected emails and phone numbers are omitted. Provider retention policies apply. AI cannot rewrite your text or apply changes automatically.</p>
          {!aiEnabled && <p>AI is not configured on this service. Manual review and export work normally.</p>}
          <label className="check-label"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} />I agree to send this text for AI review.</label>
          <button className="browse" disabled={!consent || !aiEnabled} onClick={() => void askAI()}>Suggest section moves</button>
          {aiMessage && <p role="status">{aiMessage}</p>}
          {suggestions.map(s => <div className="suggestion" key={s.id}>
            <strong>Move to {sections.find(([key]) => key === s.section)?.[1]}</strong>
            <blockquote>{blocks.find(b => b.id === s.id)?.text.slice(0, 230)}</blockquote><p>{s.reason}</p>
            <button className="browse" onClick={() => {
              const remaining = suggestions.filter(x => x.id !== s.id)
              update(s.id, { section: s.section }); setSuggestions(remaining)
            }}>Accept move</button>
            <button className="browse" onClick={() => setSuggestions(suggestions.filter(x => x.id !== s.id))}>Reject</button>
          </div>)}
        </details>
        {blocks.map((block, i) => <article className="edit-block" key={block.id}>
          <div className="block-toolbar"><label>Block {i + 1} section
            <select value={block.section} onChange={e => update(block.id, { section: e.target.value as ReviewBlock['section'] })}>
              {sections.map(([key, title]) => <option key={key} value={key}>{title}</option>)}
            </select></label>
            <button className="browse" disabled={i === 0} aria-label={`Move block ${i+1} up`} onClick={() => move(i, -1)}>↑</button>
            <button className="browse" disabled={i === blocks.length-1} aria-label={`Move block ${i+1} down`} onClick={() => move(i, 1)}>↓</button>
            <button className="browse" onClick={() => edit(blocks.filter(b => b.id !== block.id))}>Remove</button>
          </div>
          <label className="text-label">Content<textarea value={block.text} onChange={e => update(block.id, { text: e.target.value })} rows={Math.min(15, Math.max(4, block.text.split('\n').length))} /></label>
          <button className="browse" disabled={!/\n\s*\n/.test(block.text)} onClick={() => {
            const pieces = block.text.split(/\n\s*\n/).filter(s => s.trim())
            edit(blocks.flatMap(b => b.id === block.id ? pieces.map(text => ({ ...block, id: crypto.randomUUID(), text })) : [b]))
          }}>Split at blank lines</button>
          {block.source?.length ? <details><summary>Original extracted source</summary><pre>{block.source.map(s => s.text).join('\n')}</pre></details> : null}
        </article>)}
        <button className="browse" disabled={blocks.length >= 100} onClick={() => edit([...blocks, { id: crypto.randomUUID(), section: 'other', text: '' }])}>Add a block</button>
        {result.excludedFurniture.length > 0 && <details><summary>Excluded repeated headers and page numbers — review or restore</summary>
          {result.excludedFurniture.map((text, i) => <div key={i}><pre>{text}</pre><button className="browse" onClick={() => edit([...blocks, { id: crypto.randomUUID(), section: 'other', text }])}>Restore to review</button></div>)}
        </details>}
        <details><summary>Compare original extracted text</summary><pre>{result.extractedText}</pre></details>
        <button className="primary" disabled={!blocks.some(b => b.text.trim()) || blocks.length > 100} onClick={() => void check()}>Build preview &amp; reparse DOCX</button>
      </> : <>
        {!preview ? <p>Build the preview to check the actual generated file before downloading.</p> : <>
          <div className="score-comparison"><ReadabilityScore title="Original" value={result.readability} /><ReadabilityScore title="Reformatted DOCX" value={preview.result.readability} /></div>
          <p><strong>{result.readability.score !== null && preview.result.readability.score !== null ? `Measured change: ${preview.result.readability.score - result.readability.score > 0 ? '+' : ''}${preview.result.readability.score - result.readability.score} points.` : 'A numerical comparison is unavailable.'}</strong> The same rubric was used for both files. Improvement is not guaranteed.</p>
          <div className="content-check"><strong>{preview.coverage.retainedPercent}% of original extracted words retained</strong>
            <p>{preview.coverage.removedTokenCount} removed · {preview.coverage.addedTokenCount} added. {preview.coverage.note}</p>
            {changed && <details><summary>Review changed words</summary><p>Removed examples: {preview.coverage.removedExamples.join(', ') || 'None'}</p><p>Added examples: {preview.coverage.addedExamples.join(', ') || 'None'}</p></details>}
            {!preview.exportPreservesApprovedWords && <p className="error">The export did not preserve the approved words. Download is blocked; return to editing and report the issue.</p>}
          </div>
        </>}
        <div className="resume-paper" aria-label="Single-column resume content preview">
          {sections.map(([key, title]) => {
            const chosen = blocks.filter(b => b.section === key && b.text.trim())
            return chosen.length > 0 && <section key={key}>{key !== 'contact' && <h3>{title === 'Other / Unclassified' ? 'Additional Information' : title}</h3>}{chosen.map(b => <div className="preview-block" key={b.id}>{b.text}</div>)}</section>
          })}
        </div><p>This is the content preview. Word controls the final page breaks.</p>
        {preview && <>
          <details><summary>Readability findings for the exported file</summary><ul>{preview.result.parseCheck.reasons.map(r => <li key={r}>{r}</li>)}</ul></details>
          {changed && <label className="check-label"><input type="checkbox" checked={changesAccepted} onChange={e => setChangesAccepted(e.target.checked)} />I reviewed the additions and omissions shown above.</label>}
          <label className="check-label"><input type="checkbox" checked={approved} onChange={e => setApproved(e.target.checked)} />I reviewed the content, job associations and dates, and approve this copy for export.</label>
          <button className="primary" disabled={!canDownload} onClick={() => void download()}>Download editable DOCX</button>
        </>}
        <button className="browse" disabled={!blocks.some(b => b.text.trim())} onClick={() => void check()}>Build / refresh preview</button>
      </>}
      </fieldset>
      {busy && <p role="status">{busy}</p>}{error && <p className="error" role="alert">{error}</p>}
    </dialog>
  </div>
}
