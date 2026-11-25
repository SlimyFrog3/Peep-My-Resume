"""Explain what the parse check observed and what the reader can do next."""


def finding(message, next_step, section='extractedText'):
    return {'message': message, 'nextStep': next_step, 'section': section}


def record_findings(jobs, unassigned, education, other):
    findings = []
    if unassigned:
        findings.append(finding(
            'Some experience text could not be assigned to a specific role.',
            'Open “Unassigned experience text” and compare it with the original. If it belongs to a job, place it directly under that job’s title, employer, and dates.',
            'experience',
        ))

    overviews, incomplete = [], []
    for job in jobs:
        if job['isEmployerOverview']:
            overviews.append(job)
        elif not all(job[field] for field in ('title', 'organization', 'dates')):
            incomplete.append(job)
    if overviews:
        example = overviews[0]['organization']
        message = (f'The parser read {example} as an employer overview. It detected roles beneath it, but no single job title for the overview.'
                   if len(overviews) == 1 else
                   f'The parser found {len(overviews)} employer overviews with roles beneath them but no single title for each overview (for example, {example}).')
        related = [job for job in jobs if job.get('parentOrganization') in {overview['organization'] for overview in overviews}]
        complete = bool(related) and all(all(job.get(field) for field in ('title', 'organization', 'dates')) for job in related)
        note = finding(
            message,
            'If the overview is intentional and the roles below it look right, you can leave it as is. For a flatter layout, list each actual title with its employer and dates, and put shared achievements under the relevant role.',
            'experience',
        )
        if complete:
            note['severity'] = 'info'
        findings.append(note)
    if incomplete:
        missing = [label for key, label in [('title', 'job title'), ('organization', 'employer'), ('dates', 'date range')]
                   if any(not job[key] for job in incomplete)]
        fields = ', '.join(missing)
        message = (f'The parser could not identify every job field in {len(incomplete)} '
                   f'{"entry" if len(incomplete) == 1 else "entries"}. Check: {fields}.')
        findings.append(finding(
            message,
            'Compare the flagged entries with “View source.” If the details are separated, try putting the job title, employer, and date range together above that role’s bullets.',
            'experience',
        ))

    if any(not record['institution'] or not (record['qualification'] or record.get('program')) for record in education):
        findings.append(finding(
            'The parser could not identify a school or qualification/program in one or more Education entries.',
            'Open “View source” on the affected entry. If the school or qualification/program is abbreviated or split across the page, try listing the full school name and degree, diploma, or program together.',
            'education',
        ))
    if other:
        findings.append(finding(
            'Some text was placed in Other / Unclassified.',
            'Check whether the text belongs under a clearer heading, such as Projects or Certifications. If it belongs in a separate section and reads correctly, you can leave it there.',
            'other',
        ))
    return findings
