"""Three original layouts guided by the supplied references."""
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

TEMPLATES = {
    'classic': {'id': 'classic', 'name': 'Classic Professional', 'caption': 'Open spacing and a clear, traditional hierarchy.',
                'font': 'Cambria', 'bodyPt': 11, 'namePt': 29, 'headingPt': 12,
                'accent': '#343946', 'margin': .8, 'paragraphAfter': 7, 'headingBefore': 20, 'lineSpacing': 1.15},
    'modern': {'id': 'modern', 'name': 'Modern Accent', 'caption': 'A clean layout with a muted green accent.',
               'font': 'Calibri', 'bodyPt': 11, 'namePt': 30, 'headingPt': 12,
               'accent': '#527766', 'margin': .75, 'paragraphAfter': 7, 'headingBefore': 20, 'lineSpacing': 1.15},
    'compact': {'id': 'compact', 'name': 'Compact Professional', 'caption': 'A centered header and efficient spacing for longer resumes.',
                'font': 'Arial', 'bodyPt': 10.5, 'namePt': 20, 'headingPt': 11,
                'accent': '#252525', 'margin': .6, 'paragraphAfter': 5, 'headingBefore': 18, 'lineSpacing': 1.12},
}


def style_document(doc, template_id):
    style = TEMPLATES[template_id]
    # Word's default Title can carry a blue border. Clear inherited decoration.
    for border in list(doc.styles.element.xpath('.//w:pBdr')):
        border.getparent().remove(border)
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(style['margin'])
    section.left_margin = section.right_margin = Inches(style['margin'])
    normal = doc.styles['Normal']
    normal.font.name, normal.font.size = style['font'], Pt(style['bodyPt'])
    normal.font.color.rgb = RGBColor.from_string('252525')
    normal.paragraph_format.space_after = Pt(style['paragraphAfter'])
    normal.paragraph_format.line_spacing = style['lineSpacing']
    normal.paragraph_format.widow_control = True
    for name in ('Title', 'Heading 1', 'Heading 2'):
        doc.styles[name].font.name = style['font']
        doc.styles[name].font.color.rgb = RGBColor.from_string(style['accent'][1:])
    title = doc.styles['Title']
    title.font.size = Pt(style['namePt'])
    title.font.bold = template_id in {'modern', 'compact'}
    title.paragraph_format.space_after = Pt(5)
    title.paragraph_format.keep_with_next = True
    heading = doc.styles['Heading 1']
    heading.font.size, heading.font.bold = Pt(style['headingPt']), True
    heading.paragraph_format.space_before = Pt(style['headingBefore'])
    heading.paragraph_format.space_after = Pt(8)
    heading.paragraph_format.keep_with_next = True
    bullet = doc.styles['List Bullet']
    bullet.font.name, bullet.font.size = style['font'], Pt(style['bodyPt'])
    bullet.paragraph_format.space_after = Pt(style['paragraphAfter'])
    bullet.paragraph_format.line_spacing = style['lineSpacing']
    bullet.paragraph_format.left_indent = Inches(.18)
    bullet.paragraph_format.first_line_indent = Inches(-.12)
    return style


def style_paragraph(para, kind, template_id):
    style = TEMPLATES[template_id]
    if kind == 'name':
        para.style = 'Title'
    elif kind == 'heading':
        para.style = 'Heading 1'
    elif kind == 'bullet':
        para.style = 'List Bullet'
    if kind == 'entry':
        para.paragraph_format.space_before = Pt(12 if template_id != 'compact' else 10)
        para.paragraph_format.keep_with_next = True
        for run in para.runs:
            run.bold = True
    if kind == 'subheading':
        para.paragraph_format.space_before = Pt(9)
        para.paragraph_format.keep_with_next = True
        for run in para.runs:
            run.bold = True
    if kind in {'date', 'tenure'}:
        for run in para.runs:
            run.font.size = Pt(max(10, style['bodyPt'] - .5))
            run.font.color.rgb = RGBColor.from_string('606060')
        para.paragraph_format.keep_with_next = True
    if template_id == 'compact' and kind in {'name', 'contact'}:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
