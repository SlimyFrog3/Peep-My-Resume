"""Small, evidence-backed record descriptions shared by review and export."""
import re
from .layout import Line
from .records import education_records, experience_records, _role

FIELD_LABELS = {
    'fullName': 'Full name', 'organization': 'Employer / organization', 'title': 'Job title',
    'dates': 'Date range', 'location': 'Location', 'parentOrganization': 'Employer group',
    'institution': 'Institution', 'qualification': 'Qualification', 'program': 'Program / area of study',
    'credential': 'Certification title',
}


def field_match(text, value):
    """Literal evidence, allowing extraction whitespace and wrapped hyphens only."""
    pattern = re.escape(value.strip())
    pattern = re.sub(r'(?:\\\s)+', r'\\s+', pattern)
    pattern = pattern.replace(r'\-', r'-\s*')
    return re.search(pattern, text, re.I) if value.strip() else None


def name_candidate(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    first = lines[0]
    if re.search(r'[@\d:/|]', first) or _role(first) or len(first.split()) > 6:
        return None
    if len(lines) > 1 and len(first.split()) == 1:
        second = lines[1]
        word = r"[^\W\d_][^\W\d_’'-]{0,39}"
        if re.fullmatch(word, first) and re.fullmatch(word, second) and not _role(second):
            return first + ' ' + second
    return first


def record_spec(section, text, parsed=None):
    """Source geometry can seed a record; no unseen qualifications are filled in."""
    fields = {}
    details = []
    if section == 'contact':
        name = name_candidate(text)
        if name:
            fields['fullName'] = name
    elif section == 'experience':
        if parsed is None:
            jobs, _ = experience_records([Line(line, number=i) for i, line in enumerate(text.splitlines(), 1) if line.strip()])
            parsed = jobs[0] if len(jobs) == 1 else None
        if parsed:
            fields = {key: parsed.get(key) for key in ('organization', 'title', 'location', 'parentOrganization')}
            fields['dates'] = (parsed.get('dates') or {}).get('raw')
            details = parsed.get('description', [])
    elif section == 'education':
        if parsed is None:
            records = education_records([Line(line, number=i) for i, line in enumerate(text.splitlines(), 1) if line.strip()])
            if len(records) == 1:
                parsed = records[0]
        if parsed and not parsed.get('institution'):
            joined = education_records([Line(' '.join(text.splitlines()))])
            if len(joined) == 1 and joined[0]['institution']:
                parsed = joined[0]
        if parsed:
            fields = {key: parsed.get(key) for key in ('institution', 'qualification', 'program')}
    elif section == 'certifications':
        title = parsed.get('name') if parsed else next((line.strip() for line in text.splitlines() if line.strip()), '')
        fields['credential'] = title
        details = parsed.get('description', []) if parsed else []
    fields = {key: value for key, value in fields.items() if value and (key == 'parentOrganization' or field_match(text, value))}
    return {'kind': section, 'fields': fields, 'details': [value for value in details if value and field_match(text, value)], 'sourceText': text} if fields else None


def valid_spec(section, text, spec):
    if not spec or spec['kind'] != section or spec['sourceText'] != text:
        return False
    return (all(key == 'parentOrganization' or field_match(text, value) for key, value in spec['fields'].items())
            and all(field_match(text, value) for value in spec.get('details', [])))


def normalize_record_text(text, spec):
    """Reconnect only named fields already supported by the approved source."""
    fields = spec['fields']
    keys = {'contact': ['fullName'], 'education': ['qualification', 'program'],
            'certifications': ['credential']}.get(spec['kind'], [])
    for key in keys:
        value = fields.get(key)
        if value and (match := field_match(text, value)) and match[0] != value:
            text = text[:match.start()] + value + text[match.end():]
    for value in sorted(spec.get('details', []), key=len, reverse=True):
        if (match := field_match(text, value)) and '\n' in match[0]:
            text = text[:match.start()] + value + text[match.end():]
    # Render adjacent approved education fields as one unambiguous unit.
    if spec['kind'] == 'education' and fields.get('institution'):
        study = fields.get('qualification') or fields.get('program')
        institution = field_match(text, fields['institution'])
        award = field_match(text, study) if study else None
        if award and institution and not (award.start() < institution.end() and institution.start() < award.end()):
            first, second = sorted((award, institution), key=lambda match: match.start())
            if not text[first.end():second.start()].strip(' ()|·,\n\t'):
                suffix = second.end()
                if suffix < len(text) and text[suffix] == ')' and '(' in text[first.end():second.start()]:
                    suffix += 1
                text = text[:first.start()] + study + ' (' + fields['institution'] + ')' + text[suffix:]
    # Keep a parenthesized school with its qualification instead of orphaning it.
    if spec['kind'] == 'education' and fields.get('institution'):
        text = re.sub(r'\n\s*(\([^\n]+\))\s*$', r' \1', text)
    return text


def repair_suggestions(block):
    spec = block.get('record')
    suggestions = []
    if spec:
        after = normalize_record_text(block['text'], spec)
        if after != block['text']:
            label = {'contact': 'Keep the full name together', 'education': 'Reconnect the degree and school',
                     'certifications': 'Keep the certification title together', 'experience': 'Reconnect wrapped role descriptions'}[spec['kind']]
            suggestions.append({'id': 'join-fields', 'title': label, 'before': block['text'], 'after': after,
                                'explanation': 'Connect related fields and repair extraction line breaks while preserving your wording. Compare the proposed formatting before applying it.'})
    if block['section'] == 'experience' and (not spec or not all(spec['fields'].get(k) for k in ('organization', 'title', 'dates'))):
        overview = spec and spec['fields'].get('organization') and not spec['fields'].get('title')
        suggestions.append({'id': 'review-job', 'title': 'Review employer-group relationships' if overview else 'Check the job header',
                            'explanation': 'Keep the employer overview above its actual roles and client assignments; confirm who employed you. Do not invent a title for the overview.' if overview else
                            'Keep the actual job title, employer and dates together above this role’s achievements. Edit the content if a field is missing; the service will not fill it in.',
                            'before': None, 'after': None})
    if block['section'] == 'education' and (not spec or not spec['fields'].get('institution') or not (spec['fields'].get('qualification') or spec['fields'].get('program'))):
        suggestions.append({'id': 'review-school', 'title': 'Check the education entry', 'explanation': 'Put the institution and actual qualification or program together. Preserve abbreviations unless you choose to expand them; do not add an unearned degree.', 'before': None, 'after': None})
    if block['section'] == 'other':
        suggestions.append({'id': 'place-text', 'title': 'Choose where this text belongs', 'explanation': 'Use the section dropdown, keep this as Additional Information, or explicitly exclude it. Compare with the original first.', 'before': None, 'after': None})
    return suggestions
