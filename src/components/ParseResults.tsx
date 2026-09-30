import type { ParseResult } from '../types/ParseResult'

type Props = { result: ParseResult; fileName: string; demoMode: boolean }
export default function ParseResults({ result, fileName, demoMode }: Props) {
  return <section className="panel results" aria-labelledby="results-heading">
    <div className="panel-top"><span>STEP 02</span><span className="badge">{demoMode ? 'SAMPLE DATA' : 'PARSER RESULTS'}</span></div>
    <h2 id="results-heading">X-Ray Results</h2><p><strong>{fileName}</strong>. {demoMode ? 'These details are examples, not content extracted from your file.' : 'Review the extracted information below against your original résumé.'}</p>
    <div className="result-grid"><Group title="Contact" items={result.contact}/><Group title="Experience" items={result.experience}/><Group title="Education" items={result.education}/><Group title="Skills" items={result.skills}/></div>
    {result.warnings && result.warnings.length > 0 && <div className="parser-notes"><h3>Reading notes</h3><ul>{result.warnings.map(note => <li key={note}>{note}</li>)}</ul></div>}
    <details><summary>View {demoMode ? 'sample ' : ''}extracted text</summary><pre>{result.extractedText}</pre></details>
  </section>
}
function Group({ title, items }: { title: string; items: string[] }) {
  return <div className="group"><h3><span aria-hidden="true">●</span> {title}</h3>{items.length === 0 && <p>No information extracted.</p>}<ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul></div>
}
