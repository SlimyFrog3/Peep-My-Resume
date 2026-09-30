import { useState } from 'react'
import ResumeUploader from './components/ResumeUploader'
import ParseResults from './components/ParseResults'
import type { ParseResult } from './types/ParseResult'
import { demoMode, parseResume } from './services/parserApi'
import './App.css'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<ParseResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  function selectFile(next: File | null) { setFile(next); setResult(null); setError('') }
  async function analyze() {
    if (!file || busy) return
    setBusy(true)
    setError('')
    setResult(null)
    try { setResult(await parseResume(file)) }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Something went wrong.') }
    finally { setBusy(false) }
  }

  return <div className="site-shell">
    <header><a href="#top" className="brand"><img className="brand-icon" src="/eye-logo.svg" alt="" /><span className="brand-name">Peep<span className="brand-hyphen">-</span><span className="brand-my">My</span><span className="brand-hyphen">-</span>Resume</span></a><small>See what the resume bot sees</small></header>
    <main id="top">
      <div className="intro"><div className="eyebrow">● &nbsp; RESUME X-RAY TOOL</div><h1 className="tagline">Is your <span className="tagline-resume">résumé</span> <em>being parsed correctly?</em></h1><p>See how résumé parsing software organizes your information. {demoMode ? 'Preview sample results while we connect the parsing service.' : 'Upload your résumé to see the information extracted by our parser.'}</p></div>
      <div className="workspace">
        <ResumeUploader file={file} onSelect={selectFile} onAnalyze={analyze} busy={busy} demoMode={demoMode} />
        {result && file ? <ParseResults result={result} fileName={file.name} demoMode={demoMode} /> : <section className="empty panel"><div className="magnify" aria-hidden="true">⌕</div><h2>Your X-Ray will appear here</h2><p>Choose a PDF or DOCX résumé, then {demoMode ? 'show sample results to preview the interface.' : 'analyze it to see extracted results.'}</p><span className="badge">{demoMode ? 'DEMO MODE · NO FILE UPLOADED' : 'READY TO ANALYZE'}</span></section>}
      </div>
      {busy && <p role="status" className="workflow-message">{demoMode ? 'Loading sample results…' : 'Analyzing your résumé…'}</p>}
      {error && <p role="alert" className="workflow-message error">{error}</p>}
      <section className="steps"><h2>How this works</h2><div className="step-grid"><div><b>01</b><h3>Upload</h3><p>Choose a résumé to examine.</p></div><div><b>02</b><h3>Parse</h3><p>Read document text and group it by section headings.</p></div><div><b>03</b><h3>Review</h3><p>Compare extracted information with your original.</p></div></div></section>
    </main><footer>Peep-My-Resume · The Résumé X-Ray</footer>
  </div>
}
