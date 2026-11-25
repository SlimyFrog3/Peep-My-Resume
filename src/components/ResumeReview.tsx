import { useEffect, useRef, useState } from 'react'
import { sections, type ExportPreview, type ParseResult, type ReviewBlock, type ResumeTemplate, type SectionKey, type TemplateId } from '../types/ParseResult'
import { downloadPreview, getTemplates, previewResume } from '../services/reviewApi'
import ReadabilityScore from './ReadabilityScore'
import TemplateChooser from './TemplateChooser'
import ResumeDocumentPreview from './ResumeDocumentPreview'
import MoveButton from './MoveButton'

export default function ResumeReview({ result, demoMode }: { result: ParseResult; demoMode: boolean }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [blocks, setBlocks] = useState<ReviewBlock[]>(() => structuredClone(result.reviewBlocks).map(b => ({
    ...b, resolution: b.resolution ?? (b.section === 'other' ? 'pending' : 'include'),
  })))
  const [order, setOrder] = useState<SectionKey[]>(sections.map(([key]) => key))
  const [templates, setTemplates] = useState<ResumeTemplate[]>([])
  const [templateId, setTemplateId] = useState<TemplateId>('classic')
  const [templateError, setTemplateError] = useState('')
  const [preview, setPreview] = useState<ExportPreview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [approved, setApproved] = useState(false)
  const [changesAccepted, setChangesAccepted] = useState(false)
  const [tab, setTab] = useState<'edit' | 'preview'>('edit')
  useEffect(() => {
    let current = true
    void getTemplates().then(t => { if (current) setTemplates(t) }).catch(() => { if (current) setTemplateError('Could not load styles. Check your connection and retry; your edits are still here.') })
    return () => { current = false }
  }, [])
  async function retryStyles() {
    setTemplateError('')
    try { setTemplates(await getTemplates()) }
    catch { setTemplateError('Could not load styles. Check your connection and retry; your edits are still here.') }
  }
  function invalidate() {
    setPreview(null); setApproved(false); setChangesAccepted(false); setError('')
  }
  function edit(next: ReviewBlock[]) { setBlocks(next); invalidate() }
  function update(id: string, patch: Partial<ReviewBlock>) {
    edit(blocks.map(b => b.id === id ? { ...b, ...patch } : b))
  }
  const activeSections = order.filter(key => blocks.some(b => b.section === key))
  function moveSection(key: SectionKey, delta: number) {
    const position = activeSections.indexOf(key)
    const next = [...order], a = next.indexOf(key), b = next.indexOf(activeSections[position + delta])
    ;[next[a], next[b]] = [next[b], next[a]]
    setOrder(next); invalidate()
  }
  function moveBlock(block: ReviewBlock, delta: number) {
    const sameSection = blocks.filter(b => b.section === block.section)
    const position = sameSection.findIndex(b => b.id === block.id)
    const next = [...blocks], a = next.findIndex(b => b.id === block.id), b = next.findIndex(b => b.id === sameSection[position + delta].id)
    ;[next[a], next[b]] = [next[b], next[a]]
    edit(next)
  }
  async function check() {
    setBusy(true); setError('')
    try { setPreview(await previewResume(result.reviewBlocks, blocks, templateId, order)); setTab('preview') }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not preview the file.') }
    finally { setBusy(false) }
  }
  const changed = preview && (preview.coverage.removedTokenCount > 0 || preview.coverage.addedTokenCount > 0)
  const pending = blocks.filter(b => b.resolution === 'pending' && b.text.trim())
  const canDownload = preview?.exportPreservesApprovedWords && preview.formattingCheck.passed && !preview.unresolvedBlocks.length && approved && (!changed || changesAccepted)
  return <div className="review-launch">
    <h3>Make a cleaner copy</h3><p>Choose a style, arrange your sections, and review every word before exporting an editable DOCX.</p>
    <button className="primary" disabled={demoMode} onClick={() => dialog.current?.showModal()}>Review &amp; create DOCX</button>
    {demoMode && <p>Upload a real resume to use export.</p>}
    <dialog className="review-dialog" ref={dialog} aria-labelledby="editor-heading">
      <div className="review-top"><div><span className="eyebrow">REVIEW BEFORE EXPORT</span><h2 id="editor-heading">Your resume, under your control</h2></div>
        <button className="browse" onClick={() => dialog.current?.close()}>Close review</button></div>
      <p>Your section order and entry order carry through to the document. Keep dates, names and achievements accurate; no text is rewritten automatically.</p>
      <div className="review-tabs">
        <button className="browse" aria-pressed={tab === 'edit'} onClick={() => setTab('edit')}>1. Edit &amp; choose style</button>
        <button className="browse" aria-pressed={tab === 'preview'} onClick={() => setTab('preview')}>2. Preview &amp; compare</button>
      </div>
      <fieldset disabled={busy} className="review-fieldset">
        {tab === 'edit' ? <>
          {templates.length > 0 && <TemplateChooser templates={templates} selected={templateId} onSelect={id => { if (id !== templateId) { setTemplateId(id); invalidate() } }} />}
          {templateError && <div><p className="error" role="alert">{templateError}</p><button className="browse" onClick={() => void retryStyles()}>Retry styles</button></div>}
          {!templates.length && !templateError && <p>Loading your styles…</p>}
          {pending.length > 0 && <div className="placement-notice" role="status"><strong>{pending.length} {pending.length === 1 ? 'block needs' : 'blocks need'} placement</strong>
            <p>We couldn’t confidently place this text. Choose a section, keep it as Additional Information, or explicitly exclude it. You can also check the original formatting and upload again. This can be a parser limitation.</p></div>}
          {activeSections.map((key, sectionIndex) => {
            const label = sections.find(([k]) => k === key)![1]
            const entries = blocks.filter(b => b.section === key)
            return <section className="edit-section" key={key} data-edit-section={key}>
              <div className="section-toolbar"><h3>{key === 'other' ? 'Needs placement / Additional Information' : label}</h3><div>
                <MoveButton direction="up" label={`Move ${label} section up`} disabled={sectionIndex === 0} onClick={() => moveSection(key, -1)} />
                <MoveButton direction="down" label={`Move ${label} section down`} disabled={sectionIndex === activeSections.length - 1} onClick={() => moveSection(key, 1)} />
              </div></div>
              {entries.map((block, i) => <article className={`edit-block ${block.resolution === 'pending' ? 'pending-block' : ''} ${block.resolution === 'exclude' ? 'excluded-block' : ''}`} key={block.id} data-edit-block={block.id}>
                <div className="block-toolbar"><label>Entry {i + 1} section
                  <select value={block.section} onChange={e => {
                    const section = e.target.value as SectionKey
                    update(block.id, { section, resolution: section === 'other' ? 'pending' : 'include' })
                  }}>{sections.map(([k, title]) => <option key={k} value={k}>{title}</option>)}</select>
                </label>
                  <MoveButton direction="up" label={`Move entry ${i+1} up within ${label}`} disabled={i === 0} onClick={() => moveBlock(block, -1)} />
                  <MoveButton direction="down" label={`Move entry ${i+1} down within ${label}`} disabled={i === entries.length - 1} onClick={() => moveBlock(block, 1)} />
                </div>
                {block.resolution === 'pending' && <p className="placement-status"><strong>Needs placement.</strong> Use the section dropdown or choose an option below.</p>}
                <label className="text-label">Content<textarea value={block.text} onChange={e => update(block.id, { text: e.target.value })} rows={Math.min(15, Math.max(4, block.text.split('\n').length))} /></label>
                <div className="entry-actions">
                  <button className="browse" disabled={!/\n\s*\n/.test(block.text) || blocks.length >= 100} onClick={() => {
                    const pieces = block.text.split(/\n\s*\n/).filter(s => s.trim())
                    if (blocks.length - 1 + pieces.length > 100) { setError('Split would exceed 100 blocks. Use fewer blank-line groups.'); return }
                    edit(blocks.flatMap(b => b.id === block.id ? pieces.map(text => ({ ...block, id: crypto.randomUUID(), text })) : [b]))
                  }}>Split at blank lines</button>
                  {block.section === 'other' && block.resolution !== 'include' && <button className="browse" onClick={() => update(block.id, { resolution: 'include' })}>Keep as Additional Information</button>}
                  {block.resolution === 'exclude' ? <button className="browse" onClick={() => update(block.id, { resolution: block.section === 'other' ? 'pending' : 'include' })}>Restore entry</button>
                    : <button className="browse" onClick={() => update(block.id, { resolution: 'exclude' })}>Exclude from export</button>}
                </div>
                {block.resolution === 'exclude' && <p>Excluded from export. The content remains here so you can restore it.</p>}
                {block.source?.length ? <details><summary>Original extracted source</summary><pre>{block.source.map(s => s.text).join('\n')}</pre></details> : null}
              </article>)}
            </section>
          })}
          <button className="browse" disabled={blocks.length >= 100} onClick={() => edit([...blocks, { id: crypto.randomUUID(), section: 'other', text: '', resolution: 'pending' }])}>Add a block</button>
          {result.excludedFurniture.length > 0 && <details><summary>Excluded repeated headers and page numbers — review or restore</summary>
            {result.excludedFurniture.map((text, i) => <div key={i}><pre>{text}</pre><button className="browse" disabled={blocks.length >= 100} onClick={() => edit([...blocks, { id: crypto.randomUUID(), section: 'other', text, resolution: 'pending' }])}>Restore to review</button></div>)}
          </details>}
          <details><summary>Compare original extracted text</summary><pre>{result.extractedText}</pre></details>
          <button className="primary" disabled={!templates.length || !blocks.some(b => b.text.trim() && b.resolution !== 'exclude')} onClick={() => void check()}>Build preview &amp; reparse DOCX</button>
        </> : <>
          {!preview ? <p>Build a preview of the selected style. Changing content, section order or style clears the previous approval.</p> : <>
            <div className="score-comparison"><ReadabilityScore title="Original" value={result.readability} /><ReadabilityScore title="Reformatted DOCX" value={preview.result.readability} /></div>
            <p><strong>{result.readability.score !== null && preview.result.readability.score !== null ? `Measured change: ${preview.result.readability.score - result.readability.score > 0 ? '+' : ''}${preview.result.readability.score - result.readability.score} points.` : 'A numerical comparison is unavailable.'}</strong> The same rubric was used for both files. Improvement is not guaranteed.</p>
            <div className="content-check"><strong>{preview.coverage.retainedPercent}% of original extracted words retained</strong>
              <p>{preview.coverage.removedTokenCount} removed · {preview.coverage.addedTokenCount} added. {preview.coverage.note}</p>
              {changed && <details><summary>Review changed words</summary><p>Removed examples: {preview.coverage.removedExamples.join(', ') || 'None'}</p><p>Added examples: {preview.coverage.addedExamples.join(', ') || 'None'}</p></details>}
              {!preview.exportPreservesApprovedWords && <p className="error">The export did not preserve the approved words. Download is blocked; return to editing and report the issue.</p>}
            </div>
            {preview.unresolvedBlocks.length > 0 && <p className="placement-notice">This preview includes unplaced text under Additional Information. Resolve its placement in the editor before downloading.</p>}
            <div className="content-check"><strong>{preview.formattingCheck.passed ? 'Section spacing verified' : 'Section spacing needs attention'}</strong>
              <p>{preview.formattingCheck.headingCount} section headings checked in the actual DOCX for clear spacing above and below. Each heading stays with its following paragraph.</p>
              <p>{preview.formattingCheck.note}</p>
              {!preview.formattingCheck.passed && <p className="error">Download is blocked because the generated file failed its section-spacing check. Rebuild the preview; if it persists, report the issue.</p>}
            </div>
            <h3>{preview.template.name}</h3>
            <ResumeDocumentPreview document={preview.document} template={preview.template} />
            <p>Content, section order and styling match this DOCX. Word controls exact pagination and font substitution.</p>
            <details><summary>Readability findings for the exported file</summary>{preview.result.parseCheck.reasons.length ? <ul>{preview.result.parseCheck.reasons.map(r => <li key={r}>{r}</li>)}</ul> : <p>No findings flagged.</p>}</details>
            {changed && <label className="check-label"><input type="checkbox" checked={changesAccepted} onChange={e => setChangesAccepted(e.target.checked)} />I reviewed the additions and omissions shown above.</label>}
            <label className="check-label"><input type="checkbox" checked={approved} onChange={e => setApproved(e.target.checked)} />I reviewed the content, job associations and dates, and approve this copy for export.</label>
            <button className="primary" disabled={!canDownload} onClick={() => {
              try { downloadPreview(preview) } catch (e) { setError(e instanceof Error ? e.message : 'Download failed. Please rebuild the preview.') }
            }}>Download editable DOCX</button>
          </>}
          <button className="browse" disabled={!templates.length || !blocks.some(b => b.text.trim() && b.resolution !== 'exclude')} onClick={() => void check()}>Build / refresh preview</button>
        </>}
      </fieldset>
      {busy && <p role="status">Building and checking your selected style…</p>}{error && <p className="error" role="alert">{error}</p>}
    </dialog>
  </div>
}
