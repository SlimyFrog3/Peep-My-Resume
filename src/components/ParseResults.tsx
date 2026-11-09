import { sections, type ParseResult, type SourceLine } from '../types/ParseResult'
import ParseCheck from './ParseCheck'

type Props = { result: ParseResult; fileName: string; demoMode: boolean }
export default function ParseResults({ result, fileName, demoMode }: Props) {
  const detected = sections.filter(([key]) => result[key].length > 0)
  const missing = sections.filter(([key]) => key !== 'other' && result[key].length === 0)
  return <section className="panel results" aria-labelledby="results-heading">
    <div className="panel-top"><span>RESULTS</span><span className="badge">{demoMode ? 'SAMPLE DATA' : 'PARSER RESULTS'}</span></div>
    <h2 id="results-heading">Your Resume X-Ray</h2>
    <ParseCheck check={result.parseCheck} />
    <p><strong>{fileName}</strong>. {demoMode ? 'These are sample details.' : 'Compare these extracted sections with your original resume.'}</p>
    <div className="result-grid">{detected.map(([key, title]) => {
      if (key === 'experience' && result.workExperience.length) return <Group key={key} title={title} wide>
        {result.workExperience.map((job, i) => <article className="record" key={i}>
          <h4>{job.title || 'Role title not identified'}</h4>
          <p>{[job.organization, job.location, job.dates?.raw].filter(Boolean).join(' · ')}</p>
          {job.parentOrganization && <p>Listed under {job.parentOrganization} in the resume.</p>}
          <Items items={job.description} />
          <Source lines={job.source} />
        </article>)}
        {result.unassignedExperience.length > 0 && <details><summary>Unassigned experience text</summary><Items items={result.unassignedExperience} /></details>}
      </Group>
      if (key === 'education' && result.educationRecords.length) return <Group key={key} title={title}>
        {result.educationRecords.map((record, i) => <article className="record" key={i}>
          <h4>{record.qualification || 'Qualification not identified'}</h4>
          <p>{[record.institution, record.date?.value].filter(Boolean).join(' · ')}</p>
          <Items items={record.notes} />
          <Source lines={record.source} />
        </article>)}
      </Group>
      if (key === 'certifications' && result.certificationRecords.length) return <Group key={key} title={title}>
        {result.certificationRecords.map((record, i) => <article className="record" key={i}>
          <h4>{record.name}</h4>
          {record.status && <p>{record.status}</p>}
          <Items items={record.description} />
          <Source lines={record.source} />
        </article>)}
      </Group>
      if (key === 'links') return <Group key={key} title={title}>
        {result.linkRecords.map(link => <article className="record" key={link.url}>
          <p>{link.url}</p><small>{link.method}</small><Source lines={link.source} />
        </article>)}
      </Group>
      return <Group key={key} title={title}><Items items={result[key]} /></Group>
    })}</div>
    {missing.length > 0 && <details><summary>Sections not detected ({missing.length})</summary><p className="missing-sections">{missing.map(([, title]) => title).join(' · ')}</p><p>Check the original to see whether the parser missed anything.</p></details>}
    {result.warnings.length > 0 && <details className="parser-notes"><summary>Parsing notes ({result.warnings.length})</summary><Items items={result.warnings} /></details>}
    <details><summary>View {demoMode ? 'sample ' : ''}extracted text</summary><pre>{result.extractedText}</pre></details>
  </section>
}
function Group({ title, wide, children }: { title: string; wide?: boolean; children: React.ReactNode }) {
  return <div className={`group${wide ? ' group--wide' : ''}`}><h3><span aria-hidden="true">●</span> {title}</h3>{children}</div>
}
function Items({ items }: { items: string[] }) {
  return items.length > 0 && <ul>{items.map((item, i) => <li key={i}>{item}</li>)}</ul>
}
function Source({ lines }: { lines: SourceLine[] }) {
  if (!lines.length) return null
  const pages = [...new Set(lines.flatMap(line => line.page == null ? [] : [line.page]))]
  return <details className="record-source"><summary>View source{pages.length ? ` · ${pages.length === 1 ? 'page' : 'pages'} ${pages.join(', ')}` : ''}</summary>
    <pre>{lines.map(line => line.text).join('\n')}</pre>
  </details>
}
