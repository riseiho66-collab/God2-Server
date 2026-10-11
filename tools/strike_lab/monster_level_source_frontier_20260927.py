"""Read current local tables and historical reference pages; never promote levels.

This is a discovery tool. Name matches are explicitly non-authoritative, and the
output has no production import path. It never opens a client or modifies saves.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .omega_assets import decode_csvz
from .current_monster_inventory import pinned_catalog, SOURCE_SHA

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.text = []
        self.cells = []
        self.cell = None
        self.href = None
        self.label = []
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignore += 1
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.label = []
        if tag in ('td', 'th'):
            if self.cell is not None:
                self.cells.append(' '.join(self.cell).strip())
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignore = max(0, self.ignore - 1)
        if tag == 'a':
            if self.href:
                self.links.append((self.href, ''.join(self.label).strip()))
            self.href = None
        if tag in ('td', 'th') and self.cell is not None:
            self.cells.append(' '.join(self.cell).strip())
            self.cell = None

    def handle_data(self, data):
        if self.ignore:
            return
        data = data.strip()
        if data:
            self.text.append(data)
            if self.href:
                self.label.append(data)
            if self.cell is not None:
                self.cell.append(data)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def level_observation(literal):
    """Owner clarification 2026-09-27: 1 star starts30, 2 stars40, etc.

    The resulting range is not an exact original encounter level and must not
    be encoded as a guessed packet78 or1C level. This annotation does not alter
    the separately verified current client's numeric-versus-star formatter.
    """
    value = unicodedata.normalize('NFKC', literal).strip()
    if re.fullmatch(r'[0-9]{1,3}', value):
        return dict(historical_exact_level=int(value),
            observation_kind='exact_number', star_count=None,
            historical_level_range=None, range_authority=None)
    if re.fullmatch(r'[0-9]{0,3}\*', value):
        stars = int(value[:-1]) if value[:-1] else 1
        if not 1 <= stars <= 999:
            raise ValueError('Star count outside positive reference bounds')
        low = 20 + 10 * stars
        return dict(historical_exact_level=None,
            observation_kind='star_label_only', star_count=stars,
            historical_level_range=dict(minimum=low, maximum=low + 9),
            range_authority='OWNER_CLARIFICATION_20260927; not an exact native level')
    raise ValueError('Unknown level notation')


def local_tables():
    """Extend the previous Data2-only lexical frontier to current Data/Data3."""
    rows = []
    for bank in ('Data', 'Data3'):
        for path in sorted((CLIENT / bank).rglob('*.csvZ')):
            raw = path.read_bytes()
            if len(raw) > 8 << 20:
                raise ValueError('Source byte bound')
            plain = decode_csvz(raw, limit=32 << 20)
            hits = []
            offset = 0
            for number, line in enumerate(plain.splitlines(keepends=True), 1):
                text = line.decode('cp950', errors='replace')
                if re.search(r'等級|敵人|怪物|\blevel\b|\bLv\b', text, re.I):
                    hits.append(dict(line=number, offset=offset,
                        sha256=sha(line), raw_hex=line.hex(), text=text.rstrip()))
                offset += len(line)
            rows.append(dict(path=path.relative_to(CLIENT).as_posix(),
                sha256=sha(raw), decoded_sha256=sha(plain), size=len(plain),
                lexical_hits=hits, numeric_authority=False,
                scope='Current table lexical discovery; loader and identity join required'))
    return rows


def historical_page(url, output):
    """Fetch only the owner-supplied historical monster reference namespace."""
    import requests
    parsed = urlparse(url)
    if (parsed.scheme != 'https' or parsed.netloc != 'xjz.17173.com'
            or not parsed.path.startswith('/monster/') or parsed.query):
        raise ValueError('Reference URL outside qualified discovery namespace')
    response = requests.get(url, timeout=(5, 12), allow_redirects=False)
    response.raise_for_status()
    if len(response.content) > 2 << 20:
        raise ValueError('Reference byte bound')
    raw = response.content
    # This historical site declares GB2312; GB18030 provides strict supersets.
    text = raw.decode('gb18030', errors='strict')
    parser = Page()
    parser.feed(text)
    links = []
    for href, label in parser.links:
        absolute = urljoin(url, href)
        target = urlparse(absolute)
        if target.netloc == parsed.netloc and target.path.startswith('/monster/'):
            links.append(dict(url=absolute, label=label))
    levels = []
    for index, cell in enumerate(parser.cells[:-1]):
        if cell.strip() == '等级':
            value = parser.cells[index + 1].strip()
            if re.fullmatch(r'[0-9]{1,3}', value):
                levels.append(dict(level=int(value), cell_index=index + 1,
                    authority='Historical regional reference; build and variant unqualified'))
    name = None
    # Qualified reference-only title: final nonempty heading before 分类.
    for index, text in enumerate(parser.text):
        if text == '分类' and index:
            name = parser.text[index - 1]
            break
    record = dict(url=url, sha256=sha(raw), encoding='gb18030',
        title_candidate=name, level_candidates=levels, links=links,
        native_runtime_eligible=False, current_identity=None,
        missing=['Regional/version compatibility', 'Current identity and variant join'])
    key = sha(url.encode())[:16]
    (output / (key + '.html')).write_bytes(raw)
    (output / (key + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return record


def indexed_candidates(folder, catalog):
    """Retain literal level observations, separate exact numbers from stars.

    Excerpts are incomplete. A matching name only generates review candidates,
    even if there is exactly one current name. It never qualifies a native join.
    """
    names = {}
    for row in catalog['records']:
        if not row['lookup_visible']:
            continue
        try:
            name = bytes.fromhex(row['name_bytes_hex']).decode('cp950', errors='strict')
        except UnicodeDecodeError:
            continue
        names.setdefault(name, []).append(dict(area=row['area'], scene=row['scene'],
            ordinal=row['ordinal'], record_sha256=row['record_sha256']))
    observations = {}
    sources = []
    # Table names may wrap over several short lines. Longer paragraphs and
    # unrelated fields cannot be mistaken for the monster-name cell.
    name_cell = r'[0-9A-Za-z\u3400-\u9fff\uff10-\uff5a　 \t]{1,14}'
    pattern = re.compile(r'^(' + name_cell + r'(?:\n' + name_cell + r'){0,3})'
        r'\s*〖[^〗\n]*〗\s*\|\s*(?:Image\s*\|\s*)?'
        r'([0-9０-９]{1,3}(?:[＊*])?|[＊*])\s*\|', re.M)
    for path in sorted(Path(folder).glob('web-search*.json')):
        raw = path.read_bytes()
        record = json.loads(raw)
        text = record['result']
        for block in text.split('--------------------------------------------------------------------------------'):
            head = re.search(r'^([^\n]+) \((https://wiki2\.gamer\.com\.tw/[^\s)]+)\)', block, re.M)
            if not head:
                continue
            url = head[2]
            sources.append(dict(url=url, excerpt_sha256=sha(block.encode()),
                cache_path=str(path), cache_sha256=sha(raw), complete=False))
            for match in pattern.finditer(block):
                name = re.sub(r'\s+', '', match[1])
                literal = match[2]
                headings = list(re.finditer(r'^(#{1,6}) ([^\n]+)$', block[:match.start()], re.M))
                hierarchy = []
                for heading in headings:
                    depth = len(heading[1])
                    hierarchy = [(d, label) for d, label in hierarchy if d < depth]
                    hierarchy.append((depth, heading[2]))
                map_path = [label for _, label in hierarchy]
                area_label = map_path[-1] if map_path else None
                floors = list(re.finditer(r'^([^\n|]*[一二三四五六七八九十0-9][樓F][^\n|]*)$',
                    block[:match.start()], re.M))
                floor_label = floors[-1][1].strip() if floors else None
                notation = level_observation(literal)
                key = (url, tuple(map_path), floor_label, name, literal)
                observations[key] = dict(source_url=url, source_excerpt_sha256=sha(block.encode()),
                    source_character_offset=match.start(), source_row=match[0],
                    map_label=area_label, map_path=map_path, floor_label=floor_label,
                    name=name, level_literal=literal,
                    **notation,
                    current_name_candidates=names.get(name, []),
                    current_native_level=None, runtime_eligible=False,
                    unresolved=['Historical version compatibility',
                        'Map/variant/instance identity binding',
                        'Original sender value corroboration'])
    rows = list(observations.values())
    return dict(sources=sources, observations=rows,
        summary=dict(observed_rows=len(rows), exact_historical_rows=sum(
            r['observation_kind']=='exact_number' for r in rows),
            star_only_rows=sum(r['observation_kind']=='star_label_only' for r in rows),
            rows_with_current_name_candidates=sum(bool(r['current_name_candidates']) for r in rows),
            verified_original_current_levels=0, production_rows_written=0),
        policy='Search excerpts are reference leads only; name and star labels never authorize import')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', action='append', default=[])
    parser.add_argument('--indexed-dir', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    catalog = pinned_catalog()
    local = local_tables()
    pages, failures = [], []
    for url in args.url:
        try:
            pages.append(historical_page(url, args.output))
        except Exception as error:
            failures.append(dict(url=url, error=str(error)))
    result = dict(schema='god2-monster-level-source-frontier-v1',
        current_catalog_sha256=SOURCE_SHA,
        visible_lookup_records=sum(r['lookup_visible'] for r in catalog['records']),
        local_tables=local, historical_pages=pages, fetch_failures=failures,
        native_level_rows_recovered=0, production_rows_written=0,
        native_level_recovery_percent=0,
        policy='No inferred levels; own-server memory is not original balance authority')
    if args.indexed_dir:
        result['indexed_reference_crosscheck'] = indexed_candidates(args.indexed_dir, catalog)
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(local_tables=len(local), lexical_hits=sum(len(r['lexical_hits']) for r in local),
        historical_pages=len(pages), failures=failures,
        links=pages[0]['links'] if pages else [], recovered_original_levels=0,
        indexed_summary=result.get('indexed_reference_crosscheck', {}).get('summary')), ensure_ascii=False))


if __name__ == '__main__':
    main()
