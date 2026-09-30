import { useRef, useState } from 'react'

type Props = { file: File | null; onSelect: (file: File | null) => void; onAnalyze: () => void; busy: boolean; demoMode: boolean }

export default function ResumeUploader({ file, onSelect, onAnalyze, busy, demoMode }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [error, setError] = useState('')
  function choose(candidate?: File) {
    if (!candidate || busy) return
    if (!/\.(pdf|docx)$/i.test(candidate.name)) {
      setError('Please select a PDF or DOCX file.')
      onSelect(null)
      return
    }
    if (candidate.size > 10 * 1024 * 1024) { setError('Please choose a file smaller than 10 MB.'); onSelect(null); return }
    setError('')
    onSelect(candidate)
  }
  return <section className="panel upload" aria-labelledby="upload-heading">
    <div className="panel-top"><span>STEP 01</span><span className="badge">{demoMode ? 'INTERACTIVE DEMO' : 'PDF / DOCX'}</span></div>
    <h2 id="upload-heading">Start with your résumé</h2><p>{demoMode ? 'Choose a file to preview the results page. Your file stays in this browser.' : 'Choose a file to send to the parser service for analysis.'}</p>
    <input ref={input} className="sr-only" type="file" disabled={busy} accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" aria-label="Select a PDF or DOCX résumé" onChange={event => choose(event.target.files?.[0])} />
    <div className="drop" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); choose(event.dataTransfer.files[0]) }}><div className="upload-icon">↑</div><strong>{file?.name ?? 'Drag a file here, or browse'}</strong><small>PDF or DOCX · Up to 10 MB</small><button type="button" className="browse" disabled={busy} onClick={() => input.current?.click()}>{file ? 'Choose another file' : 'Browse files'}</button></div>
    {error && <p className="error" role="alert">{error}</p>}
    <button className="analyze" type="button" disabled={!file || busy} onClick={onAnalyze}>{busy ? 'Working…' : demoMode ? 'Show sample results' : 'Analyze résumé'} <span aria-hidden="true">→</span></button>
    <p className="fine-print">{demoMode ? 'This demo does not read or send your file. Results are sample data.' : 'Your file is sent to the parser for this request and is not saved by the app.'}</p>
  </section>
}
