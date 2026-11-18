"""Versioned, deterministic readability checks, not a hiring prediction."""
import re

RUBRIC_VERSION = '1.0'


def score_result(result):
    text = result['extractedText']
    words = text.split()
    long = sum(len(w) > 35 and not any(c in w for c in ('/', '@')) for w in words)
    bad = text.count('\ufffd') + sum(ord(c) < 32 and c not in '\n\t\r' for c in text)
    noise = min(1, (long / max(1, len(words))) * 8 + bad / max(1, len(text)) * 30)
    extraction_issues = [r for r in result['parseCheck']['reasons']
                         if any(x in r for x in ('no readable text', 'layout analysis', 'overlapping columns'))]
    extraction = round(30 * max(0, 1 - noise - min(.75, len(extraction_issues) * .25)))
    content = sum(len(t) for b in result['reviewBlocks'] for t in [b['text']])
    unknown = sum(len(s) for s in result['other'])
    leaked = sum(len(s) for s in result['contact'] if len(s.split()) > 22)
    classification = round(25 * max(0, 1 - min(1, (unknown + leaked) / max(1, content))))
    fields = []
    for job in result['workExperience']:
        if not job.get('isEmployerOverview'):
            fields.extend(bool(job[k]) for k in ('title', 'organization', 'dates'))
    for edu in result['educationRecords']:
        fields.extend(bool(edu[k]) for k in ('institution', 'qualification'))
    associations = sum(fields) / len(fields) if fields else 1
    if result['experience']:
        unassigned = sum(len(x) for x in result['unassignedExperience'])
        associations *= max(0, 1 - unassigned / max(1, sum(len(x) for x in result['experience'])))
    organization = round(25 * associations)
    contact_ok = bool(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '\n'.join(result['contact']))
                      or re.search(r'\d[\d ()+.-]{7,}\d', '\n'.join(result['contact'])))
    link_problem = any('incomplete' in r.lower() and 'link' in r.lower()
                       for r in result['parseCheck']['reasons'])
    contact = (10 if contact_ok else 0) + (0 if link_problem else 10)
    categories = [
        {'key': 'text', 'label': 'Readable text', 'earned': extraction, 'possible': 30,
         'detail': 'Checks unusually long joined words, unreadable characters, blank pages and layout fallbacks.'},
        {'key': 'sections', 'label': 'Section separation', 'earned': classification, 'possible': 25,
         'detail': 'Checks the proportion left unclassified or likely prose inside Contact.'},
        {'key': 'records', 'label': 'Record associations', 'earned': organization, 'possible': 25,
         'detail': 'Checks detected job titles, employers and dates, school and qualification pairs, and unassigned experience. Absent optional sections are not deducted.'},
        {'key': 'contact', 'label': 'Contact and links', 'earned': contact, 'possible': 20,
         'detail': '10 points for a detected email or phone; 10 for no detected incomplete profile links. Links are optional.'},
    ]
    total = sum(c['earned'] for c in categories)
    assessable = result['parseCheck']['status'] != 'could_not_assess'
    return {'score': total if assessable else None, 'rubricVersion': RUBRIC_VERSION,
            'status': ('could_not_assess' if not assessable else
                       'looks_good' if total >= 90 and not result['parseCheck']['reasons'] else 'needs_review'),
            'categories': categories,
            'note': '100 means all implemented readability checks passed. It does not prove complete extraction, factual accuracy, or ATS acceptance.'}
