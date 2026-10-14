"""Extract document text, then conservatively group lines by explicit headings."""
from io import BytesIO
import re
from zipfile import ZipFile, BadZipFile
import pdfplumber
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

MAX_BYTES = 10 * 1024 * 1024
MAX_TEXT = 200_000
# Add an alias here to support another heading; values become result card keys.
HEADINGS = {
    'contact': ['contact', 'contact information', 'personal information', 'contact details'],
    'experience': ['experience', 'work experience', 'professional experience', 'employment', 'employment history', 'work history', 'professional background', 'relevant experience'],
    'education': ['education', 'academic background', 'educational background', 'academic qualifications', 'education and training'],
    'skills': ['skills', 'technical skills', 'computer languages', 'programming languages', 'core competencies', 'skills and abilities', 'skills and activities', 'technologies', 'technical proficiencies'],
    'summary': ['summary', 'professional summary', 'profile', 'professional profile', 'objective', 'career objective', 'about me'],
    'certifications': ['certifications', 'certificates', 'licenses', 'licenses and certifications', 'certifications and licenses', 'credentials', 'training'],
    'projects': ['projects', 'personal projects', 'academic projects', 'selected projects'],
    'leadership': ['leadership', 'leadership experience', 'leadership roles'],
    'volunteer': ['volunteer', 'volunteer work', 'volunteer experience', 'volunteering', 'community service', 'community involvement'],
    'links': ['links', 'websites', 'website', 'online profiles', 'portfolio', 'social links'],
    'awards': ['awards', 'honors', 'honours', 'awards and honors', 'activities', 'awards and activities', 'extracurricular activities', 'interests'],
    'languages': ['languages', 'spoken languages', 'language proficiency'],
    'other': ['references', 'publications', 'additional information'],
}
ALIASES = {heading: section for section, headings in HEADINGS.items() for heading in headings}
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")
LINK = re.compile(r"(?:https?://|www\.)[^\s<>]+|(?:linkedin\.com|github\.com)/[^\s<>]+", re.I)
COLUMN_BREAK = '[Column boundary]'

class ParseError(ValueError):
    pass

def heading_key(line):
    return re.sub(r'\s+', ' ', line.strip().strip(':').strip()).lower().replace('&', 'and')

def read_pdf_page(page):
    """Only split pages with a clear gutter and section headings on both sides.

    A right-aligned date is not sufficient evidence of a second column.
    Full-width opening text stays before both columns.
    """
    words = page.extract_words()
    for fraction in (0.5, 0.6, 0.65, 0.7, 0.4, 0.35):
        split = page.width * fraction
        left = page.crop((0, 0, split, page.height)).extract_text() or ''
        right = page.crop((split, 0, page.width, page.height)).extract_text() or ''
        if not any(heading_key(line) in ALIASES for line in left.splitlines()):
            continue
        if not any(heading_key(line) in ALIASES for line in right.splitlines()):
            continue
        # A real gutter has very few words crossing it, below the header.
        rows = {}
        for word in words:
            rows.setdefault(round(word['top'] / 3) * 3, []).append(word)
        starts = []
        for top, row in rows.items():
            for side in (True, False):
                line = ' '.join(w['text'] for w in sorted(row, key=lambda w: w['x0'])
                                if (w['x0'] < split) == side)
                if heading_key(line) in ALIASES:
                    starts.append(top)
        if not starts:
            continue
        start = max(0, min(starts) - 3)
        body = [w for w in words if w['top'] >= start]
        crossings = [w for w in body if w['x0'] < split < w['x1']]
        if not body or len(crossings) > max(1, len(body) * .015):
            continue
        # Require an actual blank strip, rather than cutting at a word edge.
        if sum(w['x0'] < split + 5 and w['x1'] > split - 5 for w in body) > max(2, len(body) * .03):
            continue
        header = page.crop((0, 0, page.width, start)).extract_text() if start > 0 else ''
        left = page.crop((0, start, split, page.height)).extract_text() or ''
        right = page.crop((split, start, page.width, page.height)).extract_text() or ''
        return '\n'.join(filter(None, [header, left])), right
    return page.extract_text() or '', None

def extract_text(data: bytes, filename: str):
    if not data:
        raise ParseError('The file is empty. Choose a PDF or DOCX resume.')
    if len(data) > MAX_BYTES:
        raise ParseError('The file exceeds the 10 MB limit.')
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    try:
        if extension == 'pdf':
            if b'%PDF-' not in data[:1024]:
                raise ParseError('This file is not a valid PDF.')
            with pdfplumber.open(BytesIO(data)) as pdf:
                if len(pdf.pages) > 20:
                    raise ParseError('Please choose a resume with 20 pages or fewer.')
                main, sidebar = [], []
                for page in pdf.pages:
                    left, right = read_pdf_page(page)
                    main.append(left)
                    if right is not None:
                        sidebar.append(right)
                text = '\n\n'.join(main)
                if sidebar:
                    text += '\n' + COLUMN_BREAK + '\n' + '\n\n'.join(sidebar)
        elif extension == 'docx':
            with ZipFile(BytesIO(data)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 40 * 1024 * 1024:
                    raise ParseError('The Word file expands beyond the supported size.')
                if 'word/document.xml' not in archive.namelist():
                    raise ParseError('This file is not a valid DOCX document.')
            document = Document(BytesIO(data))
            lines = []
            # Walk body elements in document order, including tables.
            for element in document.element.body:
                if element.tag.endswith('}p'):
                    lines.append(Paragraph(element, document).text)
                elif element.tag.endswith('}tbl'):
                    table = Table(element, document)
                    for row in table.rows:
                        seen = set()
                        for cell in row.cells:
                            # Merged cells may appear more than once in a row.
                            if cell._tc in seen: continue
                            seen.add(cell._tc)
                            lines.append(cell.text)
            text = '\n'.join(lines)
        else:
            raise ParseError('Only PDF and DOCX files are supported.')
    except ParseError:
        raise
    except Exception as error:
        raise ParseError('The document could not be read. It may be corrupted or password protected.') from error
    if not text.strip():
        raise ParseError('No readable text found. Scanned or image-only PDFs need OCR, which version 2 does not support.')
    if len(text) > MAX_TEXT:
        raise ParseError('The document contains too much text for this resume demo.')
    return text

def group_sections(text: str):
    groups = {key: [] for key in HEADINGS}
    warnings = []
    current = None
    # Inline subheadings return to their parent section on the next line.
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == COLUMN_BREAK:
            current = None
            continue
        prefix, separator, remainder = line.partition(':')
        section = ALIASES.get(heading_key(prefix if separator else line))
        if section:
            if separator and remainder.strip():
                groups[section].append(remainder.strip())
            else:
                current = section
        else:
            groups[current or 'other'].append(line)

    # Preserve opening text, but only treat a short initial block as contact.
    opening = []
    for line in text.splitlines():
        if ALIASES.get(heading_key(line.partition(':')[0])) or line == COLUMN_BREAK:
            break
        if line.strip():
            opening.append(line.strip())
    for line in opening[:12]:
        if line in groups['other']:
            groups['other'].remove(line)
        if line not in groups['contact']:
            groups['contact'].append(line)
    if len(opening) > 12:
        warnings.append('Some opening text remains in Other / Unclassified; verify the Contact card.')

    # Find explicit contact details and URLs even outside an opening block.
    for pattern, destination in ((EMAIL, 'contact'), (PHONE, 'contact'), (LINK, 'links')):
        for match in pattern.findall(text):
            value = match.rstrip('.,;)')
            if not any(value in item for item in groups[destination]):
                groups[destination].append(value)
    if not EMAIL.search(text):
        warnings.append('No email address detected. Check the original and extracted text.')
    if COLUMN_BREAK in text:
        warnings.append('A likely two-column layout was read as separate columns. Verify reading order against the original.')
    if groups['other']:
        warnings.append('Some text could not be classified. Review Other / Unclassified.')
    warnings.append('Sections are detected using headings and explicit labels. Unusual layouts or missing headings can still be misread; no missing information is invented.')
    return {**groups, 'extractedText': text, 'warnings': warnings}

def parse_resume(data: bytes, filename: str):
    return group_sections(extract_text(data, filename))
