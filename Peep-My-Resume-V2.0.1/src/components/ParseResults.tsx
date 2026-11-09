import { sections, type ParseResult } from '../types/ParseResult'

type Props = { result: ParseResult; fileName: string; demoMode: boolean }
export default function ParseResults({ result, fileName, demoMode }: Props) {
  const detected = sections.filter(([key]) => result[key].length > 0)
  const missing = sections.filter(([key]) => key !== 'other' && result[key].length === 0)
  return <section className="panel results" aria-labelledby="results-heading">
    <div className="panel-top"><span>RESULTS</span><span className="badge">{demoMode ? 'SAMPLE DATA' : 'PARSER RESULTS'}</span></div>
    <h2 id="results-heading">Your Resume X-Ray</h2>
    <p><strong>{fileName}</strong>. {demoMode ? 'These are sample details.' : 'Compare these extracted sections with your original resume.'}</p>
    <div className="result-grid">{detected.map(([key, title]) => <Group key={key} title={title} items={result[key]} />)}</div>
    {missing.length > 0 && <details><summary>Sections not detected ({missing.length})</summary><p className="missing-sections">{missing.map(([, title]) => title).join(' · ')}</p><p>Not detected does not necessarily mean absent. Check the extracted text.</p></details>}
    {result.warnings.length > 0 && <div className="parser-notes"><h3>Parsing warnings</h3><ul>{result.warnings.map(note => <li key={note}>{note}</li>)}</ul></div>}
    <details><summary>View {demoMode ? 'sample ' : ''}extracted text</summary><pre>{result.extractedText}</pre></details>
  </section>
}
function Group({ title, items }: { title: string; items: string[] }) {
  return <div className="group"><h3><span aria-hidden="true">●</span> {title}</h3><ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul></div>
}
