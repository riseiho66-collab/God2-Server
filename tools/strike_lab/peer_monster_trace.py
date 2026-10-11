"""Read-only peer ZIP to pinned current native identity provenance join.

Archive content is evidence, never executable instructions. External guide
numbers remain unverified; matching identity cannot verify numeric stats.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

from .current_monster_inventory import pinned_catalog, SOURCE_SHA

ARCHIVE_SHA = '6a3cd33fd33f99f001768bdc0898d34d6c8d0095e9d0f4625213b05a8275cabb'


def read_json(z, basename):
    entries = [i for i in z.infolist() if i.filename.rsplit('/', 1)[-1] == basename]
    if len(entries) != 1 or entries[0].file_size > 8 * 1024 * 1024:
        raise ValueError('Ambiguous or oversized archive member')
    raw = z.read(entries[0])
    return json.loads(raw.decode('utf-8-sig'))


def compare_entries(peer_entries, native_records):
    local = defaultdict(list)
    undecodable = 0
    for row in native_records:
        key = (row['area'], row['scene'], row['ordinal'])
        fields = []
        for value in row['fields_hex']:
            try:
                fields.append(bytes.fromhex(value).decode('cp950'))
            except UnicodeDecodeError:
                fields.append(None)
        undecodable += int(None in fields)
        local[key].append((fields, row))
    counts, exceptions = Counter(), []
    counts['native_rows_with_undecodable_fields'] = undecodable
    for peer in peer_entries:
        key = (peer['area'], peer['map'], peer['entryIndex'])
        candidates = local.get(key, [])
        equal = [row for fields, row in candidates if None not in fields and fields == peer['rawFields']]
        if equal:
            counts['exact_fields'] += 1
            counts['exact_fields_visible'] += int(any(r['lookup_visible'] for r in equal))
            counts['same_source_line'] += int(any(r['source_line'] == peer['sourceLine'] for r in equal))
        else:
            reason = ('native_decode_unresolved' if any(None in f for f, _ in candidates)
                      else 'different_fields' if candidates else 'missing_key')
            counts[reason] += 1
            exceptions.append({'key': list(key), 'name': peer['name'], 'reason': reason,
                               'peer_fields': peer['rawFields'],
                               'current_fields': [f for f, _ in candidates]})
    return dict(counts), exceptions, local


def trace(path):
    path = Path(path)
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Archive size exceeds audit bound')
    if hashlib.sha256(path.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError('Archive changed; inspect before accepting a new identity')
    with zipfile.ZipFile(path, metadata_encoding='cp950') as z:
        monsters = read_json(z, 'monsters.json')
        guide = read_json(z, 'bahamut_monster_stats.json')
    catalog = pinned_catalog()
    counts, exceptions, local = compare_entries(monsters['entries'], catalog['records'])
    guide_counts, guide_issues = Counter(), []
    for row in guide['records']:
        matches = row['nativeMatches']
        if row['bindingStatus'] != '\u540c\u540d\u540c\u5730\u5716\u552f\u4e00\u5c0d\u61c9' or len(matches) != 1:
            guide_counts['not_uniquely_bound_by_peer'] += 1
            continue
        m = matches[0]
        candidates = local.get((m['area'], m['map'], m['entryIndex']), [])
        matching = [r for f, r in candidates if f[1] == row['name'] and
                    f[2:] == m['rawAppearanceFields']]
        if matching:
            guide_counts['identity_matches_current'] += 1
            guide_counts['identity_visible_current'] += int(any(r['lookup_visible'] for r in matching))
        else:
            guide_counts['identity_not_confirmed_current'] += 1
            guide_issues.append({'name': row['name'], 'reference': m})
    return {
        'authority': 'IDENTITY_PROVENANCE_ONLY_EXTERNAL_STATS_NOT_VERIFIED',
        'archive_sha256': ARCHIVE_SHA, 'current_gamedata_sha256': SOURCE_SHA,
        'peer_gamedata_sha256': next(s['sha256'] for s in monsters['report']['sources']
                                   if s['file'].endswith('gamedata.csvZ')),
        'peer_entries': len(monsters['entries']), 'current_occurrences': len(catalog['records']),
        'comparison': counts, 'exceptions': exceptions,
        'guide_comparison': dict(guide_counts), 'guide_issues': guide_issues,
        'guide_sources': sorted({r['sourceUrl'] for r in guide['records']}),
        'numeric_stat_authority': 'PLAYER_GUIDE_CLAIMS_ONLY',
        'production_database_writes': 0,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive')
    args = parser.parse_args()
    print(json.dumps(trace(args.archive), ensure_ascii=False, indent=2))
