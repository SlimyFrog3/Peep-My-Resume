"""Extract evidence-backed roles, qualifications, and credentials."""
import re
from .layout import adjacent, reflow

MONTHS = 'jan feb mar apr may jun jul aug sep oct nov dec'.split()
MONTH = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?'
DATE = rf'(?:(?:{MONTH})\s+|\d{{1,2}}/)?(?:19|20)\d{{2}}(?:-(?:0[1-9]|1[0-2]))?'
PERIOD = re.compile(rf'(?<!\w)(?P<start>{DATE})\s*(?:[-–—]|\bto\b)\s*(?P<end>{DATE}|present|current|now)\b', re.I)
ROLE = re.compile(r'\b(?:engineer|developer|manager|director|lead|analyst|specialist|designer|instructor|consultant|coordinator|assistant|intern|architect|associate|administrator|scientist|technician|teacher|officer|founder|president|quality assurance|recruiter|accountant|nurse|operator|supervisor|representative)\b', re.I)
ACTION = re.compile(r'^(?:managed|led|built|developed|worked|provided|performed|trained|used|designed|tested|implemented|created|coordinated|oversaw|supported|signed|participated|maintained|assisted|as the|responsible)\b', re.I)
DEGREE = re.compile(r'\b(?:bachelor|master|doctorate|associate|diploma|b\.?s|b\.?a|m\.?s|m\.?a|mba|ph\.?d)\b', re.I)
SCHOOL = re.compile(r'\b(?:university|college|institute|school|polytechnic|academy)\b', re.I)
BULLET = re.compile(r'^\s*[•●▪◦‣*–-]\s+')


def date_value(s):
    if s.lower() in {'present','current','now'}:
        return {'value':'present','precision':'present'}
    m = re.search(r'(?:19|20)\d{2}',s)
    if not m:
        return None
    prefix, suffix = s[:m.start()].strip(), s[m.end():].strip()
    mon = MONTHS.index(prefix.lower()[:3])+1 if prefix.lower()[:3] in MONTHS else None
    if prefix.rstrip('/').isdigit() and 1 <= int(prefix.rstrip('/')) <= 12:
        mon = int(prefix.rstrip('/'))
    if re.fullmatch(r'-(?:0[1-9]|1[0-2])',suffix):
        mon = int(suffix[1:])
    return {'value':f'{m[0]}-{mon:02}' if mon else m[0],'precision':'month' if mon else 'year'}


def _range(m):
    return {'raw':m[0],'start':date_value(m['start']),'end':date_value(m['end'])}


def _period(text):
    m = PERIOD.search(text)
    return m if m and len(text)<=150 and not text[m.end():].strip(' )|·,') else None


def _name(s):
    return bool(3<=len(s)<=95 and len(s.split())<=12 and not ACTION.search(s)
                and not any(c in s for c in '@<>:?!') and not s.startswith(('http','www.')))


def _role(s):
    return bool(_name(s) and ROLE.search(s) and not s.endswith('.') and not PERIOD.search(s))


def job_start(lines,i,explicit=False):
    """Return a record header and consumed line count only on strong cues."""
    window = []
    for line in lines[i:i+4]:
        if line.page != lines[i].page or line.region != lines[i].region:
            break
        window.append(BULLET.sub('',line.text).strip())
    a,b,c = (window+['','',''])[:3]
    ma,mb,mc = map(_period,(a,b,c))
    def record(count,org,title,dates,location=None):
        return count, {'organization':org,'title':title,'dates':dates,'location':location}
    def prefix(text,m):
        return text[:m.start()].strip(' ,|·–-')
    if ma and any(sep in a for sep in (' | ',' · ')):
        pieces = [p.strip() for p in re.split(r'\s+[|·]\s+', prefix(a,ma)) if p.strip()]
        if len(pieces)==2 and _role(pieces[0]) and _name(pieces[1]):
            return record(1,pieces[1],pieces[0],_range(ma))
        if len(pieces)==2 and _role(pieces[1]) and _name(pieces[0]):
            return record(1,pieces[0],pieces[1],_range(ma))
    if ma and _name(org:=prefix(a,ma)):
        if _role(b):
            dates, count, loc = _range(ma), 2, None
            if mc:
                more = _range(mc)
                if all(dates[k]['value'][:4]==more[k]['value'][:4] for k in ('start','end')):
                    dates, count, loc = more, 3, prefix(c,mc) or None
            elif re.fullmatch(r'[\w .,-]{2,50}\s+\([^)]{2,35}\)',c):
                count,loc=3,c
            return record(count,org,b,dates,loc)
        if explicit and org.isupper() and not _role(org):
            return record(1,org,None,_range(ma))
    if _role(a):
        if mb and _name(org:=prefix(b,mb)):
            org, _, loc = org.partition(',')
            return record(2,org,a,_range(mb),loc.strip() or None)
        if _name(b) and mc and mc.start()==0:
            return record(3,b,a,_range(mc))
        if explicit and mb and mb.start()==0:
            return record(2,None,a,_range(mb))
    if (_name(a) and _role(b) and mc and mc.start()==0 and not BULLET.match(lines[i].text)
        and (not lines[i].box or not lines[i+1].box or abs(lines[i].box[0]-lines[i+1].box[0])<=7)):
        return record(3,a,b,_range(mc))
    return None


def experience_records(lines):
    result, leftover, current, parent, i = [], [], None, None, 0
    while i<len(lines):
        header = job_start(lines,i,explicit=True)
        if header:
            n,item = header
            title_first = _role(lines[i].text)
            if not item['title']:
                parent=item['organization']
            elif not title_first:
                parent=None
            item['parentOrganization'] = parent if title_first and parent!=item['organization'] else None
            current = {**item,'source':lines[i:i+n],'body':[]}
            result.append(current)
            i+=n
            continue
        if current:
            current['body'].append(lines[i])
        else:
            leftover.append(lines[i].text)
        i+=1
    for item in result:
        body = item.pop('body')
        item['description']=reflow(body)
        item['source']=[l.evidence() for l in item['source']+body]
    return result,leftover


def education_records(lines):
    result, current = [], None
    for line in lines:
        text = BULLET.sub('',line.text).strip()
        is_degree,is_school = bool(DEGREE.search(text)),bool(SCHOOL.search(text))
        if current is None or (is_degree and current['qualification']) or (is_school and current['institution'] and not is_degree):
            current={'institution':None,'qualification':None,'date':None,'notes':[],'source':[]}
            result.append(current)
        prev = current['source'][-1] if current['source'] else None
        current['source'].append(line)
        if is_degree and not current['qualification']:
            chunks = re.split(r'\s+[|·]\s+',text)
            current['qualification'] = chunks[0]
            for chunk in chunks[1:]:
                if SCHOOL.search(chunk) and not current['institution']:
                    current['institution']=chunk
                elif re.fullmatch(DATE,chunk,re.I):
                    current['date']=date_value(chunk)
                else:
                    current['notes'].append(chunk)
        elif is_school and not current['institution']:
            suffix = re.search(rf'\s+((?:expected\s+)?{DATE})$', text, re.I)
            current['institution']=text[:suffix.start()].rstrip(' ,|·–-') if suffix else text
            if suffix:
                current['date']=date_value(re.sub(r'^expected\s+', '', suffix[1], flags=re.I))
        elif re.fullmatch(rf'(?:expected\s+)?{DATE}',text,re.I):
            current['date']=date_value(re.sub(r'^expected\s+', '', text, flags=re.I))
        elif current['qualification'] and not current['institution'] and adjacent(prev,line,max_dx=5,max_dy=18):
            current['qualification']+=' '+text
        else:
            current['notes'].append(text)
    for item in result:
        if item['qualification'] and not item['institution']:
            match = re.fullmatch(r'(.+?)\s+\(([^()]+)\)',item['qualification'])
            if match and (SCHOOL.search(match[2]) or re.match(r'^[A-Z]{2,}(?:,|$)',match[2])):
                item['qualification'],item['institution']=match[1],match[2]
        item['source']=[l.evidence() for l in item['source']]
    return result


def certification_records(lines):
    records=[]
    for line in lines:
        marker=line.text.strip().casefold() in {'certificate','certification'}
        if records:
            first,prev=records[-1][0],records[-1][-1]
            indented=(first.box and line.box and first.page==line.page and first.region==line.region
                      and line.box[0]>first.box[0]+7)
            wrap=(adjacent(prev,line,max_dx=5,max_dy=15)
                  and prev.text.strip().casefold() not in {'certificate','certification'}
                  and (prev.text.endswith('-') or line.text.startswith('(')
                       or line.text[0].islower() or prev.box[2]-prev.box[0]>=85))
            if marker or indented or wrap:
                records[-1].append(line)
                continue
        records.append([line])
    output=[]
    for block in records:
        title,details=[],[]
        for l in block:
            if l.text.strip().casefold() in {'certificate','certification'} and len(block)>1:
                continue
            (details if l.box and block[0].box and l.box[0]>block[0].box[0]+7 else title).append(l)
        name=' '.join(reflow(title,True))
        output.append({'name':name,'status':'In progress' if re.search(r'\bin progress\b',name,re.I) else None,
                       'description':reflow(details),'source':[l.evidence() for l in block]})
    return output
