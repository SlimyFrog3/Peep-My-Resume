"""Read full embedded targets and repair conservative within-column URL wraps."""
import re
from urllib.parse import urlsplit
from .layout import adjacent

LINK = re.compile(r'(?:https?://|www\.)[^\s<>]+|(?:linkedin\.com|github\.com)/[^\s<>]*', re.I)
PROFILES = {'linkedin.com', 'github.com'}


def url_value(value):
    value = value.strip().rstrip('.,;)]')
    if not value or any(c.isspace() or ord(c)<32 for c in value):
        return None
    if '://' not in value:
        if not re.match(r'^(?:www\.|linkedin\.com/|github\.com/)', value, re.I):
            return None
        value = 'https://' + value
    try:
        u = urlsplit(value)
        if u.scheme in {'http','https'} and not u.username and not u.password and re.fullmatch(r'(?:[a-z0-9-]+\.)+[a-z]{2,}', u.hostname or ''):
            return value
    except ValueError:
        pass
    return None


def recover_links(flows, embedded):
    records, skipped, partial = {}, set(), set()

    def add(url, source, method):
        u = urlsplit(url)
        host, path = u.hostname.removeprefix('www.'), u.path.strip('/')
        if host in PROFILES and (not path or host == 'linkedin.com' and path in {'in','pub','company'}):
            partial.add(host)
            return False
        records.setdefault((host, path, u.query), {'url':url,'source':[l.evidence() for l in source],'method':method})
        return True

    for target, line in embedded:
        if value := url_value(target):
            add(value,[line],'embedded')
    for lines in flows:
        for i,line in enumerate(lines):
            for m in LINK.finditer(line.text):
                value = url_value(m[0])
                if not value:
                    continue
                u = urlsplit(value)
                host = u.hostname.removeprefix('www.')
                source = [line]
                if host in PROFILES and u.path in ('','/','/in/','/pub/') and i+1<len(lines):
                    following = lines[i+1]
                    segment = following.text.strip()
                    pattern = (r'[A-Za-z0-9][A-Za-z0-9-]{0,38}' if host=='github.com'
                               else r'[A-Za-z0-9-]+/?' if u.path in ('/in/','/pub/')
                               else r'/?(?:in|pub|company)/[A-Za-z0-9%_/-]+')
                    if adjacent(line,following) and re.fullmatch(pattern,segment):
                        if joined := url_value(value.rstrip('/')+'/'+segment.lstrip('/')):
                            value = joined
                            source.append(following)
                            skipped.add(following)
                if add(value,source,'wrapped text' if len(source)==2 else 'visible text'):
                    if not line.text[:m.start()].strip() and not line.text[m.end():].strip(' .,;)'):
                        skipped.add(line)
    return list(records.values()), skipped, partial-{key[0] for key in records}
