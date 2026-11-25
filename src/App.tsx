import { useRef, useState } from 'react'
import ResumeUploader from './components/ResumeUploader'
import ParseResults from './components/ParseResults'
import ParseCheck from './components/ParseCheck'
import ReadabilityScore from './components/ReadabilityScore'
import type { ParseResult } from './types/ParseResult'
import { demoMode, parseResume, UnreadableResumeError } from './services/parserApi'
import './App.css'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<ParseResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [unreadable, setUnreadable] = useState(false)
  // A request number prevents an older upload from replacing newer results.
  const requestNumber = useRef(0)
  const activeRequest = useRef<AbortController | null>(null)
  function selectFile(next: File | null) {
    activeRequest.current?.abort()
    requestNumber.current += 1
    setFile(next)
    setResult(null)
    setError('')
    setUnreadable(false)
    setBusy(false)
    if (next) void analyze(next)
  }
  async function analyze(selected: File) {
    activeRequest.current?.abort()
    const request = ++requestNumber.current
    const controller = new AbortController()
    activeRequest.current = controller
    setBusy(true)
    setError('')
    setUnreadable(false)
    setResult(null)
    try {
      const parsed = await parseResume(selected, controller.signal)
      if (request === requestNumber.current) setResult(parsed)
    } catch (failure) {
      if (request === requestNumber.current) {
        setError(failure instanceof Error ? failure.message : 'Something went wrong.')
        setUnreadable(failure instanceof UnreadableResumeError)
      }
    } finally {
      if (request === requestNumber.current) setBusy(false)
    }
  }

  return <div className="site-shell">
    <header><a href="#top" className="brand"><img className="brand-icon" src="/eye-logo.svg" alt="" /><span className="brand-name">Peep<span className="brand-hyphen">-</span><span className="brand-my">My</span><span className="brand-hyphen">-</span>Resume</span></a><small>See what the resume bot sees</small></header>
    <main id="top">
      <div className="intro"><div className="eyebrow">● &nbsp; RESUME X-RAY TOOL · BETA 4.0.2</div><h1 className="tagline">Is your <span className="tagline-resume">resume</span> <em>being parsed correctly?</em></h1><p>See how resume parsing software organizes your information. {demoMode ? 'Preview sample results while we connect the parsing service.' : 'Upload your resume to see the information extracted by our parser.'}</p></div>
      <div className="workspace">
        <ResumeUploader file={file} onSelect={selectFile} busy={busy} demoMode={demoMode} />
        {result && file ? <ParseResults key={requestNumber.current} result={result} fileName={file.name} demoMode={demoMode} /> : error ? <section className="panel results" aria-labelledby="results-heading" role="alert"><h2 id="results-heading">Your Resume X-Ray</h2>{unreadable ? <ReadabilityScore value={{ score: 0, status: 'could_not_assess', rubricVersion: '1.1', categories: [], note: '0 means no readable text could be extracted. A scan may need OCR, or a fresh text-based export.' }} /> : <p>No score is available because analysis did not finish.</p>}<ParseCheck check={{ status: 'could_not_assess', reasons: [error] }} />{file && <button className="browse" onClick={() => void analyze(file)}>Retry analysis</button>}</section> : <section className="empty panel"><div className="magnify" aria-hidden="true">⌕</div><h2>Your X-Ray will appear here</h2><p>{busy ? 'Reading your document and organizing its sections…' : 'Choose a PDF or DOCX resume. Analysis starts automatically.'}</p><span className="badge">{demoMode ? 'DEMO MODE · NO FILE UPLOADED' : busy ? 'PROCESSING' : 'READY TO UPLOAD'}</span></section>}
      </div>
      {busy && <p role="status" className="workflow-message">{demoMode ? 'Loading sample results…' : 'Analyzing your resume…'}</p>}
      <section className="steps"><h2>How this works</h2><div className="step-grid"><div><b>01</b><h3>Upload</h3><p>Choose a resume to examine.</p></div><div><b>02</b><h3>Parse</h3><p>Check readability and organize your information.</p></div><div><b>03</b><h3>Review</h3><p>Review, edit, and export a cleaner DOCX. Compare the measured scores.</p></div></div></section>
    </main><footer>Peep-My-Resume · The Resume X-Ray</footer>
  </div>
}
