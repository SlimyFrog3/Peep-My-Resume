import type { CSSProperties } from 'react'
import type { ResumeDocument, ResumeTemplate } from '../types/ParseResult'

export default function ResumeDocumentPreview({ document, template }: { document: ResumeDocument; template: ResumeTemplate }) {
  const style = {
    '--resume-accent': template.accent, '--resume-font': template.font,
    '--resume-body': `${template.bodyPt}pt`, '--resume-name': `${template.namePt}pt`,
    '--resume-heading': `${template.headingPt}pt`, '--resume-line': template.lineSpacing,
    '--resume-after': `${template.paragraphAfter}pt`, '--resume-before': `${template.headingBefore}pt`,
    '--resume-margin': `${template.margin}in`,
  } as CSSProperties
  return <div className={`resume-paper resume-style-${template.id}`} style={style} aria-label={`${template.name} content preview`}>
    {document.sections.map(section => <section key={section.key} data-resume-section={section.key}>
      {section.key !== 'contact' && <h3>{section.title}</h3>}
      {section.blocks.map(block => <div key={block.id} data-resume-block={block.id}>{block.paragraphs.map((p, i) =>
        <p key={i} className={`resume-${p.kind}`}>{p.kind === 'bullet' && <span aria-hidden="true">• </span>}{p.text || '\u00a0'}</p>)}</div>)}
    </section>)}
  </div>
}
