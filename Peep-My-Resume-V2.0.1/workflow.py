"""Editable blocks, a single-column DOCX, and a fresh parse of exported bytes."""
from collections import Counter
from io import BytesIO
import re
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from docx import Document
from docx.shared import Inches, Pt, RGBColor

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

    @field_validator('text')
    @classmethod
    def valid_document_text(cls, value):
        if any(ord(c) < 32 and c not in '\n\t\r' for c in value):
            raise ValueError('Text contains unsupported control characters.')
        return value


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    original: list[Block] = Field(min_length=1, max_length=100)
    blocks: list[Block] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def bounds(self):
        for blocks in (self.original, self.blocks):
            if sum(len(b.text) for b in blocks) > 200000:
                raise ValueError('Too much text in the review.')
            if len({b.id for b in blocks}) != len(blocks):
                raise ValueError('Block IDs must be unique.')
        if not any(b.text.strip() for b in self.blocks):
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


def export_docx(blocks):
    doc = Document()
    doc.core_properties.author = ''
    doc.core_properties.title = 'Resume'
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Inches(.65)
    section.left_margin = section.right_margin = Inches(.75)
    normal = doc.styles['Normal']
    normal.font.name, normal.font.size = 'Calibri', Pt(11)
    normal.paragraph_format.space_after = Pt(5)
    for name in ('Title', 'Heading 1'):
        doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    doc.styles['Heading 1'].font.size = Pt(13)
    doc.styles['Heading 1'].paragraph_format.keep_with_next = True
    # Group blocks by a stable standard section order, retaining order within a section.
    for key, title in SECTION_TITLES.items():
        chosen = [b for b in blocks if b.section == key and b.text.strip()]
        if not chosen:
            continue
        if key != 'contact':
            doc.add_heading(title, level=1)
        for block in chosen:
            for i, line in enumerate(block.text.splitlines()):
                if not line.strip():
                    doc.add_paragraph()
                    continue
                bullet = re.match(r'^\s*[•●▪◦‣*–-]\s+', line)
                para = doc.add_paragraph(re.sub(r'^\s*[•●▪◦‣*–-]\s+', '', line) if bullet else line,
                                         style='List Bullet' if bullet else 'Normal')
                if key == 'experience' and i == 0 and not bullet:
                    para.runs[0].bold = True
                    para.paragraph_format.space_before = Pt(9)
                if key == 'experience' and i < 3 and not bullet:
                    para.paragraph_format.keep_with_next = True
                if key == 'contact' and i == 0 and len(line.split()) <= 6 and '@' not in line:
                    para.runs[0].bold = True
                    para.runs[0].font.size = Pt(17)
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def preview_export(request):
    from .parser import parse_resume
    data = export_docx(request.blocks)
    parsed = parse_resume(data, 'Peep-My-Resume.docx')
    # Compare approved content with what the file actually contains, separately from parser categorization.
    actual = Document(BytesIO(data))
    actual_tokens = tokens('\n'.join(p.text for p in actual.paragraphs if p.style.name != 'Heading 1'))
    expected = tokens('\n'.join(b.text for b in request.blocks))
    return {'result': parsed, 'coverage': coverage(request.original, request.blocks),
            'exportPreservesApprovedWords': actual_tokens == expected}
