import type { ResumeTemplate, TemplateId } from '../types/ParseResult'
export default function TemplateChooser({ templates, selected, onSelect }: {
  templates: ResumeTemplate[]; selected: TemplateId; onSelect: (id: TemplateId) => void
}) {
  return <section className="style-chooser" aria-labelledby="style-heading">
    <h3 id="style-heading">Choose your style!</h3><p>Same content and section order. Three different finishes.</p>
    <div className="template-grid">{templates.map(t => <button type="button" key={t.id}
      className={`template-card template-${t.id}`} aria-pressed={selected === t.id} onClick={() => onSelect(t.id)}>
      <img className="template-thumbnail" src={`/templates/${t.id}.png`} alt="" loading="lazy" />
      <strong>{t.name}</strong><span>{t.caption}</span><span className="selection-tag">{selected === t.id ? '✓ Selected' : 'Select style'}</span>
    </button>)}</div>
  </section>
}
