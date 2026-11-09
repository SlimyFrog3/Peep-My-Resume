"""Read document regions, classify sections, then build reviewable records."""
from dataclasses import replace
from io import BytesIO
import re
from zipfile import ZipFile, BadZipFile
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.psparser import PSEOF
from lxml.etree import XMLSyntaxError
import pdfplumber
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from .layout import Line, PageReading, read_pdf_page
from .links import recover_links
from .records import certification_records, education_records, experience_records, job_start, reflow

MAX_BYTES = 10 * 1024 * 1024
MAX_TEXT = 200_000
# Add an alias here to support another heading; values become result card keys.
HEADINGS = {
    'contact': ['contact', 'contact information', 'personal information', 'contact details'],
    'experience': ['experience', 'work experience', 'professional experience', 'employment', 'employment history', 'work history', 'professional background', 'relevant experience'],
    'education': ['education', 'academic background', 'educational background', 'academic qualifications', 'education and training'],
    'skills': ['skills', 'tools', 'tools and technologies', 'ai skill', 'ai skills', 'technical skills', 'computer languages', 'programming languages', 'core competencies', 'skills and abilities', 'skills and activities', 'technologies', 'technical proficiencies'],
    'summary': ['summary', 'personal profile', 'professional summary', 'profile', 'professional profile', 'objective', 'career objective', 'about me'],
    'certifications': ['certifications', 'certification', 'certificates', 'licenses', 'licenses and certifications', 'certifications and licenses', 'credentials', 'training'],
    'projects': ['projects', 'personal projects', 'academic projects', 'selected projects'],
    'leadership': ['leadership', 'leadership experience', 'leadership roles'],
    'volunteer': ['volunteer', 'volunteer work', 'volunteer experience', 'volunteering', 'community service', 'community involvement'],
    'links': ['links', 'websites', 'website', 'online profiles', 'portfolio', 'social links'],
    'awards': ['awards', 'honors', 'honours', 'awards and honors', 'activities', 'awards and activities', 'extracurricular activities', 'interests', 'ooo activities'],
    'languages': ['languages', 'spoken languages', 'language proficiency'],
    'other': ['references', 'publications', 'additional information'],
}
ALIASES = {heading: section for section, headings in HEADINGS.items() for heading in headings}
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")
COLUMN_BREAK = '[Column boundary]'
COMPACT_HEADINGS = {heading.replace(' ', ''): heading for heading in ALIASES}
TECH = re.compile(r'^(?:java(?:script)?|typescript|python|ruby|kotlin|swift|scala|rust|go|golang|c(?:\+\+|#)?|objective[- ]c|r(?: programming)?|sql(?:\s*/\s*pl/sql)?|pl/sql|oracle(?: database)?|html5?|css|matlab|bash|php|perl|dart|julia|lua|haskell|ocaml|shell|powershell|vba|assembly)(?:\b|$)', re.I)
SPOKEN = re.compile(r'^(?:english|spanish|french|german|italian|portuguese|arabic|hindi|urdu|bengali|mandarin|cantonese|chinese|japanese|korean|russian|ukrainian|vietnamese|tagalog|farsi|persian|dutch|polish|punjabi|gujarati|turkish|hebrew|greek|swahili|tamil|telugu|indonesian|thai|malay|romanian|norwegian|danish|swedish|finnish|czech|asl|american sign language)\b', re.I)


class ParseError(ValueError):
    pass


def heading_key(line):
    key = re.sub(r'\s+', ' ', line.strip().strip(':').strip()).casefold().replace('&', 'and')
    # Some PDFs encode titles such as W O R K E X P E R I E N C E.
    if re.fullmatch(r'[a-z](?: [a-z]){4,}', key):
        return COMPACT_HEADINGS.get(key.replace(' ', ''), key)
    return key


def _plain_lines(text, page=None, region='main'):
    return [Line(s, page, region, i) for i, s in enumerate(text.splitlines(), 1) if s.strip()]


def _read_document(data: bytes, filename: str):
    main, sidebar, embedded, notes, issues = [], [], [], [], []
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
                column_pages = []
                for page in pdf.pages:
                    try:
                        reading = read_pdf_page(page)
                    except ValueError:
                        reading = PageReading(_plain_lines(page.extract_text() or '', page.page_number), [],
                                              f'Page {page.page_number}: layout analysis was unavailable; standard text reading was used. Check the reading order.')
                    main.extend(reading.main)
                    sidebar.extend(reading.sidebar)
                    if reading.sidebar:
                        column_pages.append(str(page.page_number))
                    if reading.warning:
                        issues.append(reading.warning)
                    if not reading.main and not reading.sidebar:
                        issues.append(f'Page {page.page_number}: no readable text was found.')
                    try:
                        for link in page.hyperlinks:
                            uri = link.get('uri')
                            if isinstance(uri, str):
                                box = tuple(link[k] for k in ('x0', 'top', 'x1', 'bottom'))
                                embedded.append((uri, Line(uri, page.page_number, 'annotation', box=box)))
                    except (ValueError, TypeError, KeyError):
                        issues.append(f'Page {page.page_number}: embedded links could not be checked.')
                if column_pages:
                    notes.append(f'A likely two-column layout was read as separate regions on page(s) {", ".join(column_pages)}. Check the reading order against the original.')
        elif extension == 'docx':
            with ZipFile(BytesIO(data)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 40 * 1024 * 1024:
                    raise ParseError('The Word file expands beyond the supported size.')
                if 'word/document.xml' not in archive.namelist():
                    raise ParseError('This file is not a valid DOCX document.')
            document = Document(BytesIO(data))
            def add_paragraph(paragraph):
                for text in paragraph.text.splitlines():
                    if text.strip():
                        main.append(Line(text, number=len(main)+1))
                for link in paragraph.hyperlinks:
                    if link.url:
                        embedded.append((link.url, Line(link.text, region='annotation', number=len(main))))

            # Read paragraphs and table cells in document order. Keep table rows
            # intact instead of flattening their contents across unrelated rows.
            for element in document.element.body:
                if element.tag.endswith('}p'):
                    add_paragraph(Paragraph(element, document))
                elif element.tag.endswith('}tbl'):
                    table = Table(element, document)
                    seen = set()
                    for row in table.rows:
                        for cell in row.cells:
                            if cell._tc in seen:
                                continue
                            seen.add(cell._tc)
                            for paragraph in cell.paragraphs:
                                add_paragraph(paragraph)
        else:
            raise ParseError('Only PDF and DOCX files are supported.')
    except ParseError:
        raise
    except PDFPasswordIncorrect as error:
        raise ParseError('This PDF requires a password to open. Upload an unlocked copy.') from error
    except (PDFSyntaxError, PSEOF) as error:
        raise ParseError('The PDF structure could not be read. Try exporting a new PDF from the original document.') from error
    except (BadZipFile, XMLSyntaxError) as error:
        raise ParseError('The DOCX contents could not be read. Open the original document and save a new DOCX copy.') from error
    if not main and not sidebar:
        raise ParseError('No readable text was extracted. If this is a scan or image, export a text-based document or use OCR before uploading.')
    if sum(len(line.text) + 1 for line in main + sidebar) > MAX_TEXT:
        raise ParseError('The document contains too much text for this resume demo.')
    return main, sidebar, embedded, notes, issues


def _classify(main, sidebar, embedded=(), notes=(), issues=()):
    groups = {key: [] for key in HEADINGS}
    notes, issues = list(notes), list(issues)
    links, skipped, incomplete = recover_links((main, sidebar), embedded)
    for host in sorted(incomplete):
        issues.append(f'An incomplete {host} profile link was found. Check the original URL.')

    jobs, ungrouped_jobs = [], []
    for flow in (main, sidebar):
        start_experience = len(groups['experience'])
        current = None
        opening = True
        preamble_count = 0
        for i, source in enumerate(flow):
            if source in skipped:
                continue
            line = source.text.strip()
            prefix, separator, remainder = line.partition(':')
            section = ALIASES.get(heading_key(prefix if separator else line))
            if section:
                opening = False
                if not (separator and remainder.strip()):
                    current = section
                    continue
                source = replace(source, text=remainder.strip())
                destination = section
            else:
                if flow is main and current in (None, 'summary', 'other') and job_start(flow, i):
                    current, opening = 'experience', False
                destination = current or 'other'
                if source.region == 'header' and re.fullmatch(r'[A-Za-z](?: [A-Za-z]){3,}', line):
                    destination = 'contact'
                    source = replace(source, text=line.replace(' ', ''))
                elif opening and preamble_count < 12:
                    destination = 'contact'
                    preamble_count += 1
            if destination == 'languages':
                # Keep unrecognized entries reviewable rather than assuming a language.
                items = [x.strip() for x in re.split(r'[,;]', source.text) if x.strip()]
                for value in items:
                    target = 'skills' if TECH.match(value) else 'languages' if SPOKEN.match(value) else 'other'
                    groups[target].append(replace(source, text=value))
                continue
            if destination == 'links':
                # Only validated links are shown as URLs; preserve other lines for review.
                destination = 'other'
            groups[destination].append(source)
        records, unassigned = experience_records(groups['experience'][start_experience:])
        jobs.extend(records)
        ungrouped_jobs.extend(unassigned)

    raw = '\n'.join(line.text for line in main)
    if sidebar:
        raw += '\n' + COLUMN_BREAK + '\n' + '\n'.join(line.text for line in sidebar)
    sections = {key: [line.text for line in lines] for key, lines in groups.items()}
    sections['contact'] = list(dict.fromkeys(sections['contact']))
    for pattern in (EMAIL, PHONE):
        for match in pattern.findall(raw):
            if not any(match in item for item in sections['contact']):
                sections['contact'].append(match)
    sections['links'] = [link['url'] for link in links]
    sections['summary'] = reflow(groups['summary'])
    sections['certifications'] = reflow(groups['certifications'], title_lines=True)
    education = education_records(groups['education'])

    if groups['experience'] and (ungrouped_jobs or any(not job['title'] or not job['organization'] or not job['dates'] for job in jobs)):
        issues.append('Experience contains text that could not be fully assigned to roles. Check the original job titles, employers, and dates.')
    if education and any(not record['institution'] or not record['qualification'] for record in education):
        issues.append('Some education records are missing an institution or qualification.')
    if groups['other']:
        issues.append('Some text could not be classified. Review Other / Unclassified.')
    if not EMAIL.search(raw) and not PHONE.search(raw):
        issues.append('No email or phone number was detected. Check the Contact section.')
    has_fields = bool(jobs or education or any(sections[k] for k in ('skills', 'summary', 'certifications', 'experience', 'projects')))
    if not has_fields:
        status = 'could_not_assess'
        issues.insert(0, 'Text was read, but there was not enough recognizable resume information to assess the result.')
    elif issues:
        status = 'needs_review'
    else:
        status = 'looks_good'
    return {**sections, 'extractedText': raw, 'warnings': notes + issues,
            'workExperience': jobs, 'unassignedExperience': ungrouped_jobs,
            'educationRecords': education, 'certificationRecords': certification_records(groups['certifications']), 'linkRecords': links,
            'parseCheck': {'status': status, 'reasons': list(dict.fromkeys(issues))}}


def group_sections(text: str):
    """Classify an already ordered plain-text document."""
    main, separator, sidebar = text.partition(COLUMN_BREAK)
    return _classify(_plain_lines(main), _plain_lines(sidebar, region='sidebar') if separator else [])


def parse_resume(data: bytes, filename: str):
    return _classify(*_read_document(data, filename))
