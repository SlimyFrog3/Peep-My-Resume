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
HEADINGS = {
    'contact': ['contact', 'contact information', 'personal information', 'contact details'],
    'experience': ['experience', 'work experience', 'professional experience', 'employment', 'employment history', 'work history', 'professional background', 'relevant experience'],
    'education': ['education', 'academic background', 'educational background', 'academic qualifications'],
    'skills': ['skills', 'technical skills', 'core competencies', 'skills and abilities', 'technologies', 'technical proficiencies'],
    'other': ['summary', 'professional summary', 'profile', 'objective', 'career objective', 'projects', 'personal projects', 'academic projects', 'certifications', 'certificates', 'awards', 'interests', 'languages', 'references', 'volunteer experience', 'leadership', 'publications', 'activities'],
}
ALIASES = {heading: section for section, headings in HEADINGS.items() for heading in headings}

class ParseError(ValueError):
    pass

def heading_key(line):
    return re.sub(r'\s+', ' ', line.strip().strip(':').strip()).lower()

def extract_text(data: bytes, filename: str):
    if not data:
        raise ParseError('The file is empty. Choose a PDF or DOCX résumé.')
    if len(data) > MAX_BYTES:
        raise ParseError('The file exceeds the 10 MB limit.')
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    try:
        if extension == 'pdf':
            if b'%PDF-' not in data[:1024]:
                raise ParseError('This file is not a valid PDF.')
            with pdfplumber.open(BytesIO(data)) as pdf:
                if len(pdf.pages) > 20:
                    raise ParseError('Please choose a résumé with 20 pages or fewer.')
                text = '\n\n'.join(page.extract_text() or '' for page in pdf.pages)
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
        raise ParseError('No readable text found. Scanned or image-only PDFs need OCR, which version 1 does not support.')
    if len(text) > MAX_TEXT:
        raise ParseError('The document contains too much text for this résumé demo.')
    return text

def group_sections(text: str):
    groups = {key: [] for key in ['contact', 'experience', 'education', 'skills']}
    warnings = []
    found = set()
    current = None
    preamble = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line: continue
        # Support headings on their own line, or "Skills: Python, SQL".
        prefix, separator, remainder = line.partition(':')
        key = heading_key(prefix if separator else line)
        section = ALIASES.get(key)
        if section:
            current = section
            found.add(section)
            if separator and remainder.strip() and section in groups:
                groups[section].append(remainder.strip())
        elif current in groups:
            groups[current].append(line)
        elif current is None:
            preamble.append(line)
    # Keep the opening block as a candidate contact block; don't guess a name.
    if not groups['contact']:
        groups['contact'] = preamble[:12]
        if len(preamble) > 12:
            warnings.append('The opening block was truncated in Contact; all text is available below.')
    for section in ['experience', 'education', 'skills']:
        if section not in found:
            warnings.append(f'No recognized {section} heading. Check the extracted text for content that was not grouped.')
    warnings.append('Version 1 groups text by headings. Columns, text boxes, headers, footers, and unusual headings may be missed or read out of order.')
    return {**groups, 'extractedText': text, 'warnings': warnings}

def parse_resume(data: bytes, filename: str):
    return group_sections(extract_text(data, filename))
