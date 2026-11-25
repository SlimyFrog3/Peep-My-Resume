import { useState } from 'react'
import type { ReviewBlock, StructuredRecord } from '../types/ParseResult'

const labels: Record<string, string> = {
  fullName: 'Full name', organization: 'Employer / organization', title: 'Job title', dates: 'Date range',
  location: 'Location', institution: 'Institution', qualification: 'Qualification', program: 'Program / area of study',
  credential: 'Certification title',
}
const keys: Record<string, string[]> = {
  contact: ['fullName'], experience: ['organization', 'title', 'dates', 'location'],
  education: ['institution', 'qualification', 'program'], certifications: ['credential'],
}
function evidenceMatch(text: string, value: string) {
  const escaped = value.trim().split(/\s+/).map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replaceAll('-', '-\\s*')).join('\\s+')
  return new RegExp(escaped, 'i').test(text)
}
export default function RecordEditor({ block, onAssign }: { block: ReviewBlock; onAssign: (record: StructuredRecord) => void }) {
  const [fields, setFields] = useState<Record<string, string>>(block.record?.fields ?? {})
  const [error, setError] = useState('')
  if (!keys[block.section]) return null
  return <details className="record-editor">
    <summary>{block.record ? 'Detected fields and relationships — review or correct' : 'Assign fields from this entry’s content'}</summary>
    <p>Use wording already in the content below. To change wording, edit the content first. These assignments tell the template which details belong together.</p>
    <div className="record-fields">{keys[block.section].map(key => <label key={key}>{labels[key]}
      <input value={fields[key] ?? ''} onChange={e => { setFields({ ...fields, [key]: e.target.value }); setError('') }} />
    </label>)}</div>
    {block.record?.fields.parentOrganization && <p><strong>Employer group:</strong> {block.record.fields.parentOrganization}. Keep the overview above its related roles; confirm the employer/client relationship against the original.</p>}
    <button className="browse" onClick={() => {
      const chosen: Record<string, string> = Object.fromEntries(Object.entries(fields).map(([k, v]) => [k, v.trim()]).filter(([, v]) => v))
      if (!Object.keys(chosen).length) { setError('Assign at least one field from the content, or edit the content and refresh detection.'); return }
      const invalid = Object.entries(chosen).find(([key, value]) => key !== 'parentOrganization' && !evidenceMatch(block.text, value))
      if (invalid) { setError(`${labels[invalid[0]]}: use the wording found in this entry, or edit its content first.`); return }
      onAssign({ kind: block.section as StructuredRecord['kind'], fields: chosen, details: block.record?.details ?? [], sourceText: block.text })
    }}>Use these field assignments</button>
    {error && <p className="error" role="alert">{error}</p>}
  </details>
}
