"""Editable blocks, a single-column DOCX, and a fresh parse of exported bytes."""
from collections import Counter
from io import BytesIO
import re
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from docx import Document
from .templates import TEMPLATES, style_document, style_paragraph
from .records import PERIOD, TENURE, _period, _role
from .structured import record_spec, valid_spec, normalize_record_text, repair_suggestions, FIELD_LABELS

SECTION_TITLES = {
    'contact': 'Contact', 'summary': 'Professional Summary', 'experience': 'Experience',
    'education': 'Education', 'skills': 'Skills', 'certifications': 'Certifications',
    'projects': 'Projects', 'leadership': 'Leadership', 'volunteer': 'Volunteer Work',
    'links': 'Links', 'awards': 'Awards and Activities', 'languages': 'Languages',
    'other': 'Additional Information',
}
Section = Literal['contact','summary','experience','education','skills','certifications',
                  'projects','leadership','volunteer','links','awards','languages','other']


class StructuredRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['contact', 'experience', 'education', 'certifications']
    fields: dict[Literal['fullName','organization','title','dates','location','parentOrganization',
                         'institution','qualification','program','credential'], str] = Field(min_length=1)
    sourceText: str = Field(max_length=40000)
    details: list[str] = Field(default_factory=list, max_length=1000)

    @model_validator(mode='after')
    def fields_match_record_kind(self):
        allowed = {'contact': {'fullName'}, 'experience': {'organization','title','dates','location','parentOrganization'},
                   'education': {'institution','qualification','program'}, 'certifications': {'credential'}}
        if not set(self.fields).issubset(allowed[self.kind]) or any(not value.strip() or len(value) > 40000 for value in self.fields.values()):
            raise ValueError('Use nonempty fields belonging to this record type.')
        return self


class Block(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=80)
    section: Section
    text: str = Field(max_length=40000)
    resolution: Literal['pending', 'include', 'exclude'] = 'include'
    record: StructuredRecord | None = None

    @model_validator(mode='after')
    def record_has_evidence(self):
        if self.record and not valid_spec(self.section, self.text, self.record.model_dump()):
            raise ValueError('Record fields no longer match the content. Refresh record detection after editing.')
        return self

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
    # A word hyphenated at an extracted line break is the same word after repair.
    text = re.sub(r'(?<=\w)-[ \t]*\n[ \t]*(?=\w)', '-', text)
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
    spec = block.record.model_dump() if block.record else record_spec(block.section, block.text)
    text = normalize_record_text(block.text, spec) if spec else block.text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            output.append({'kind': 'space', 'text': ''})
            continue
        bullet = re.match(r'^\s*[•●▪◦‣*–-]\s+', line)
        kind = 'body'
        if bullet:
            kind, line = 'bullet', line[bullet.end():]
        elif block.section == 'certifications' and spec and line.strip() == spec['fields'].get('credential'):
            kind = 'credential'
        elif block.section == 'links':
            kind = 'link'
        elif block.section == 'contact':
            kind = 'name' if (spec and line.strip() == spec['fields'].get('fullName')) or (not spec and i == 0 and len(line.split()) <= 6 and not re.search(r'[@\d]|https?://', line)) else 'contact'
        elif block.section in {'experience', 'education', 'projects', 'certifications'}:
            match = _period(line.strip())
            if match and match.start() == 0:
                kind = 'date'
            elif i == 0 or (_role(line.strip()) and i + 1 < len(lines) and _period(lines[i+1].strip())):
                kind = 'entry'
            elif TENURE.fullmatch(line.strip()):
                kind = 'tenure'
        if kind == 'body' and line.strip().endswith(':') and len(line.split()) <= 9:
            kind = 'subheading'
        # Join obvious wrapped prose only. No rewriting, fact filling or truncation.
        if (kind == 'body' and output and output[-1]['kind'] in {'body', 'bullet'}
                and not re.match(r'^(?:https?://|www\.)', line, re.I) and line[:1].islower() and output[-1]['text'] and
                not output[-1]['text'].endswith(('.', '!', '?', ';', ':'))):
            output[-1]['text'] += ('' if output[-1]['text'].endswith('-') else ' ') + line
        else:
            output.append({'kind': kind, 'text': line})
    return output


def build_document_model(blocks, section_order):
    sections = []
    for key in section_order:
        chosen = [b for b in blocks if b.section == key and b.resolution != 'exclude' and b.text.strip()]
        if chosen:
            sections.append({'key': key, 'title': SECTION_TITLES[key],
                             'blocks': [{'id': b.id, 'record': b.record.model_dump() if b.record else record_spec(b.section, b.text), 'paragraphs': paragraphs_for(b)} for b in chosen]})
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


def prepare_blocks(blocks, originals=()):
    prepared = []
    for block in blocks:
        item = block.model_dump()
        if not item['record']:
            old = next((b.record for b in originals if b.id == block.id and b.section == block.section and b.record), None)
            rebased = {**old.model_dump(), 'sourceText': block.text} if old else None
            item['record'] = rebased if valid_spec(block.section, block.text, rebased) else record_spec(block.section, block.text)
        item['suggestions'] = repair_suggestions(item)
        prepared.append(item)
    return prepared


def approved_baseline(blocks, section_order):
    from .parser import group_sections
    model = build_document_model(blocks, section_order)
    text = '\n'.join(('' if s['key'] == 'contact' else s['title'] + '\n') +
                     '\n'.join(p['text'] for b in s['blocks'] for p in b['paragraphs']) for s in model['sections'])
    return group_sections(text)


def check_records(blocks, parsed, actual):
    """Compare independent approved fields and per-record content, not counts alone."""
    checks = []
    pools = {'experience': list(parsed['workExperience']), 'education': list(parsed['educationRecords']),
             'certifications': list(parsed['certificationRecords'])}
    for block in blocks:
        spec = block.record.model_dump() if block.record else record_spec(block.section, block.text)
        if not spec:
            continue
        fields = spec['fields']
        issues = []
        label = next((fields[k] for k in ('fullName','credential','qualification','program','title','organization','institution') if fields.get(k)), block.id)
        observed = {}
        if block.section == 'contact':
            name = fields.get('fullName')
            if name:
                titles = [p.text.strip() for p in actual.paragraphs if p.style.name == 'Title']
                if name not in titles or name not in parsed['contact']:
                    issues.append('The full name did not survive as one consistently styled name heading.')
                observed['fullName'] = next((value for value in titles if value == name), None)
        else:
            candidates = pools[block.section]
            expected = tokens(block.text)
            item = max(candidates, key=lambda r: sum((expected & tokens('\n'.join(s['text'] for s in r['source']))).values()), default=None)
            if item:
                candidates.remove(item)
                observed = ({'credential': item['name']} if block.section == 'certifications' else
                            {**item, 'dates': (item.get('dates') or {}).get('raw')} if block.section == 'experience' else item)
                for key, value in fields.items():
                    found = observed.get(key)
                    if not found or tokens(value) != tokens(found):
                        issues.append(f"{FIELD_LABELS[key]} changed or could not be recovered from this entry.")
                recovered = tokens('\n'.join(s['text'] for s in item['source']))
                if recovered != expected:
                    issues.append('Supporting text was lost, split, merged or attached to a different record.')
            else:
                issues.append('This approved record could not be recovered from the generated file.')
        checks.append({'blockId': block.id, 'kind': block.section, 'label': label, 'passed': not issues,
                       'issues': issues, 'expectedFields': fields,
                       'actualFields': {key: observed.get(key) for key in fields}})
    # Detect extra records too, including certification descriptions mistaken for credentials.
    extras = {kind: len(items) for kind, items in pools.items() if items and any(c['kind'] == kind for c in checks)}
    return {'passed': all(c['passed'] for c in checks) and not extras, 'checks': checks,
            'assessedRecords': len(checks), 'extraRecords': extras,
            'note': 'Compares detected fields and supporting text with your approved entries. It cannot verify factual accuracy or another ATS.'}


def preview_export(request):
    from .parser import parse_resume
    import base64
    data = export_docx(request.blocks, request.templateId, request.sectionOrder)
    parsed = parse_resume(data, 'Peep-My-Resume.docx')
    approved = [b for b in request.blocks if b.resolution != 'exclude' and b.text.strip()]
    actual = Document(BytesIO(data))
    actual_tokens = tokens('\n'.join(p.text for p in actual.paragraphs if p.style.name != 'Heading 1'))
    expected = tokens('\n'.join(b.text for b in approved))
    preservation = check_records(approved, parsed, actual)
    baseline = approved_baseline(approved, request.sectionOrder)
    before, after = baseline['readability']['score'], parsed['readability']['score']
    new_findings = [r for r in parsed['parseCheck']['reasons'] if r not in baseline['parseCheck']['reasons']]
    score_ok = after is not None and (before is None or after >= before)
    formatting = inspect_section_spacing(actual)
    quality = {'passed': preservation['passed'] and score_ok and not new_findings and formatting['passed'] and actual_tokens == expected,
               'approvedScore': before, 'exportScore': after, 'scoreDidNotDecrease': score_ok, 'newFindings': new_findings,
               'note': 'The export is checked against your approved edits. A lower score or changed relationships are generation problems to review, not evidence that your original resume is worse.'}
    return {'result': parsed, 'coverage': coverage(request.original, approved),
            'exportPreservesApprovedWords': actual_tokens == expected,
            'recordCheck': preservation, 'exportQuality': quality, 'formattingCheck': formatting,
            'unresolvedBlocks': [b.id for b in request.blocks if b.resolution == 'pending' and b.text.strip()],
            'document': build_document_model(request.blocks, request.sectionOrder),
            'template': TEMPLATES[request.templateId],
            'docxBase64': base64.b64encode(data).decode('ascii')}
