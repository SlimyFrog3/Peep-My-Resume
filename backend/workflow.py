"""Editable blocks, a single-column DOCX, and a fresh parse of exported bytes."""
from collections import Counter
from io import BytesIO
import re
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from docx import Document
from .templates import TEMPLATES, style_document, style_paragraph
from .records import PERIOD, TENURE, _period, _role

SECTION_TITLES = {
    'contact': 'Contact', 'summary': 'Professional Summary', 'experience': 'Experience',
    'education': 'Education', 'skills': 'Skills', 'certifications': 'Certifications',
    'projects': 'Projects', 'leadership': 'Leadership', 'volunteer': 'Volunteer Work',
    'links': 'Links', 'awards': 'Awards and Activities', 'languages': 'Languages',
    'other': 'Additional Information',
}
Section = Literal['contact','summary','experience','education','skills','certifications',
                  'projects','leadership','volunteer','links','awards','languages','other']


class Block(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=80)
    section: Section
    text: str = Field(max_length=40000)
    resolution: Literal['pending', 'include', 'exclude'] = 'include'

    @field_validator('text')
    @classmethod
    def valid_document_text(cls, value):
        if any(ord(c) < 32 and c not in '\n\t\r' for c in value):
            raise ValueError('Text contains unsupported control characters.')
        return value


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    templateId: Literal['classic', 'modern', 'compact'] = 'classic'
    sectionOrder: list[Section] = Field(default_factory=lambda: list(SECTION_TITLES))
    original: list[Block] = Field(min_length=1, max_length=100)
    blocks: list[Block] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def bounds(self):
        if len(self.sectionOrder) != len(SECTION_TITLES) or set(self.sectionOrder) != set(SECTION_TITLES):
            raise ValueError('Section order must contain each known section exactly once.')
        for blocks in (self.original, self.blocks):
            if sum(len(b.text) for b in blocks) > 200000:
                raise ValueError('Too much text in the review.')
            if len({b.id for b in blocks}) != len(blocks):
                raise ValueError('Block IDs must be unique.')
        if not any(b.text.strip() and b.resolution != 'exclude' for b in self.blocks):
            raise ValueError('The reviewed resume is empty.')
        return self


def tokens(text):
    return Counter(re.findall(r"\w+(?:['’-]\w+)*", text.casefold()))


def coverage(original, reviewed):
    before = tokens('\n'.join(b.text for b in original))
    after = tokens('\n'.join(b.text for b in reviewed))
    removed, added = before - after, after - before
    return {'retainedPercent': round(100 * sum((before & after).values()) / max(1, sum(before.values()))),
            'removedTokenCount': sum(removed.values()), 'addedTokenCount': sum(added.values()),
            'removedExamples': list(removed)[:20], 'addedExamples': list(added)[:20],
            'note': 'Word-count comparison flags additions and omissions; it cannot verify that facts or associations stayed correct.'}


def paragraphs_for(block):
    """Formatting roles only: the user's words stay untouched."""
    output = []
    for i, line in enumerate(block.text.splitlines()):
        if not line.strip():
            output.append({'kind': 'space', 'text': ''})
            continue
        bullet = re.match(r'^\s*[•●▪◦‣*–-]\s+', line)
        kind = 'body'
        if bullet:
            kind, line = 'bullet', line[bullet.end():]
        elif block.section == 'links':
            kind = 'link'
        elif block.section == 'contact':
            kind = 'name' if i == 0 and len(line.split()) <= 6 and not re.search(r'[@\d]|https?://', line) else 'contact'
        elif block.section in {'experience', 'education', 'projects', 'certifications'}:
            match = _period(line.strip())
            if match and match.start() == 0:
                kind = 'date'
            elif i == 0 or (_role(line.strip()) and i + 1 < len(block.text.splitlines()) and _period(block.text.splitlines()[i+1].strip())):
                kind = 'entry'
            elif TENURE.fullmatch(line.strip()):
                kind = 'tenure'
        if kind == 'body' and line.strip().endswith(':') and len(line.split()) <= 9:
            kind = 'subheading'
        # Join obvious wrapped prose only. No rewriting, fact filling or truncation.
        if (kind == 'body' and output and output[-1]['kind'] in {'body', 'bullet'}
                and not re.match(r'^(?:https?://|www\.)', line, re.I) and line[:1].islower() and output[-1]['text'] and
                not output[-1]['text'].endswith(('.', '!', '?', ';', ':'))):
            output[-1]['text'] += ' ' + line
        else:
            output.append({'kind': kind, 'text': line})
    return output


def build_document_model(blocks, section_order):
    sections = []
    for key in section_order:
        chosen = [b for b in blocks if b.section == key and b.resolution != 'exclude' and b.text.strip()]
        if chosen:
            sections.append({'key': key, 'title': SECTION_TITLES[key],
                             'blocks': [{'id': b.id, 'paragraphs': paragraphs_for(b)} for b in chosen]})
    return {'sections': sections}


def export_docx(blocks, template_id='classic', section_order=None):
    doc = Document()
    doc.core_properties.author = ''
    doc.core_properties.title = 'Resume'
    style_document(doc, template_id)
    model = build_document_model(blocks, section_order or list(SECTION_TITLES))
    for section in model['sections']:
        if section['key'] != 'contact':
            heading = doc.add_heading(section['title'], level=1)
            if template_id == 'compact':
                # Visual uppercase is formatting, not a content change.
                for run in heading.runs:
                    run.font.all_caps = True
        for block in section['blocks']:
            for item in block['paragraphs']:
                para = doc.add_paragraph(item['text'])
                style_paragraph(para, item['kind'], template_id)
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def inspect_section_spacing(doc):
    headings = [p for p in doc.paragraphs if p.style.name == 'Heading 1']
    checks = []
    for p in headings:
        before = p.paragraph_format.space_before
        if before is None:
            before = p.style.paragraph_format.space_before
        after = p.paragraph_format.space_after
        if after is None:
            after = p.style.paragraph_format.space_after
        checks.append({'heading': p.text, 'beforePt': before.pt if before is not None else 0,
                       'afterPt': after.pt if after is not None else 0,
                       'keptWithNext': p.paragraph_format.keep_with_next if p.paragraph_format.keep_with_next is not None else p.style.paragraph_format.keep_with_next})
    return {'passed': all(c['beforePt'] >= 18 and c['afterPt'] >= 8 and c['keptWithNext'] for c in checks),
            'headingCount': len(checks), 'checks': checks,
            'note': 'Checks actual DOCX heading tags, minimum spacing and keep-with-next. It does not certify correct field associations.'}


def preview_export(request):
    from .parser import parse_resume
    import base64
    data = export_docx(request.blocks, request.templateId, request.sectionOrder)
    parsed = parse_resume(data, 'Peep-My-Resume.docx')
    approved = [b for b in request.blocks if b.resolution != 'exclude']
    actual = Document(BytesIO(data))
    actual_tokens = tokens('\n'.join(p.text for p in actual.paragraphs if p.style.name != 'Heading 1'))
    expected = tokens('\n'.join(b.text for b in approved))
    return {'result': parsed, 'coverage': coverage(request.original, approved),
            'exportPreservesApprovedWords': actual_tokens == expected,
            'formattingCheck': inspect_section_spacing(actual),
            'unresolvedBlocks': [b.id for b in request.blocks if b.resolution == 'pending' and b.text.strip()],
            'document': build_document_model(request.blocks, request.sectionOrder),
            'template': TEMPLATES[request.templateId],
            'docxBase64': base64.b64encode(data).decode('ascii')}
