"""Positioned source lines and geometry-first reading for sidebar PDFs."""
from dataclasses import dataclass
from statistics import median
import re


@dataclass(frozen=True)
class Line:
    text: str
    page: int | None = None
    region: str = 'main'
    number: int = 0
    box: tuple | None = None

    def evidence(self):
        return {'text': self.text, 'page': self.page, 'region': self.region,
                'line': self.number, 'bbox': [round(x, 1) for x in self.box] if self.box else None}


@dataclass
class PageReading:
    main: list[Line]
    sidebar: list[Line]
    warning: str | None = None


def _lines(page, region):
    return [Line(r['text'], page.page_number, region, i,
                 (r['x0'], r['top'], r['x1'], r['bottom']))
            for i, r in enumerate(page.extract_text_lines(return_chars=False), 1) if r['text'].strip()]


def _rows(words):
    rows = []
    for word in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if not rows or word['top'] - rows[-1][0]['top'] > 4:
            rows.append([])
        rows[-1].append(word)
    return rows


def _content(words):
    # Date-only margins are common in single-column resumes.
    dates = {'jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec',
             'present','current','to','now','expected'}
    return any(sum(c.isalpha() for c in w['text']) >= 2 and
               w['text'].lower().strip('.,') not in dates and
               w['text'].lower()[:3] not in dates for w in words)


def _gutter(words, bounds):
    left, top, right, bottom = bounds
    width, height = right-left, bottom-top
    rows = _rows(words)
    candidates, ambiguous = [], False
    if len(rows) < 5:
        return None, top, False
    for i in range(18, 83):
        x = left + width*i/100
        parallel, leading, crossing = [], [], 0
        for row in rows:
            y = row[0]['top']
            a = [w for w in row if w['x1'] <= x-2]
            b = [w for w in row if w['x0'] >= x+2]
            if len(a)+len(b) != len(row):
                if not parallel and y < top + height*.12:
                    leading.append(max(w['bottom'] for w in row))
                else:
                    crossing += 1
            elif _content(a) and _content(b):
                parallel.append(y)
        if len(parallel) < 3 or parallel[-1]-parallel[0] < 18:
            continue
        if crossing:
            ambiguous |= len(parallel) >= 5 and crossing <= len(parallel)//4
        else:
            candidates.append((len(parallel), x, max(leading, default=top)))
    if not candidates:
        return None, top, ambiguous
    best = max(c[0] for c in candidates)
    runs = []
    for c in (c for c in candidates if c[0] == best):
        if not runs or c[1]-runs[-1][-1][1] > width*.011:
            runs.append([])
        runs[-1].append(c)
    run = max(runs, key=len)
    return median(c[1] for c in run), max(c[2] for c in run), False


def read_pdf_page(page):
    left, top, right, bottom = page.bbox
    x, body_top, uncertain = _gutter(page.extract_words(), page.bbox)
    if x is None:
        note = f'Page {page.page_number}: possible overlapping columns; check reading order.' if uncertain else None
        return PageReading(_lines(page, 'main'), [], note)
    header = _lines(page.crop((left,top,right,body_top)), 'header') if body_top > top else []
    a = [l for l in _lines(page.crop((left,top,x,bottom)), 'left') if l.box[1] >= body_top-.01]
    b = [l for l in _lines(page.crop((x,top,right,bottom)), 'right') if l.box[1] >= body_top-.01]
    main, side = (b,a) if x < left+(right-left)*.43 else (a,b)
    return PageReading(header+main, side)


def reflow(lines, title_lines=False):
    output, prev = [], None
    for line in lines:
        text = re.sub(r'^\s*[•●▪◦‣*–-]\s+', '', line.text).strip()
        if not text:
            continue
        near = adjacent(prev, line, max_dx=5, max_dy=18)
        if (near and output and not output[-1].endswith(('.', '!', '?', ';')) and
                not re.match(r'^\s*[•●▪◦‣*–-]\s+', line.text) and
                (title_lines or output[-1].endswith('-') or text[0].islower())):
            output[-1] += ('' if output[-1].endswith('-') else ' ') + text
        else:
            output.append(text)
        prev = line
    return output


def adjacent(a, b, max_dx=16, max_dy=24):
    return bool(a and a.box and b.box and a.page == b.page and a.region == b.region
                and abs(a.box[0]-b.box[0]) <= max_dx and 0 < b.box[1]-a.box[1] <= max_dy)
