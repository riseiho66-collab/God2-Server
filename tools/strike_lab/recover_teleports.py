"""Import retained portal evidence, never promote a legacy route into runtime.

The C# and SQL readers deliberately accept only the retained catalog grammar.
They do not execute migrations or treat CAN resource references as teleports.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct

from .world_scenes import parse_can

ROOT = Path(__file__).resolve().parents[2]
CLASSIC = Path('C:/God2Evidence/classic-20260820/files/'
               'God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource')
XJZ = ROOT / 'artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation'
ROUTES = 'src/God2.ClassicServer.Runtime/OfficialPortalClosedLoop.cs'
WIRE = 'src/God2.ClassicServer.Protocol/OfficialPortalWire.cs'
GATE = 'database/schema/127_pin_enabled_portal_evidence_hashes.sql'
CANDIDATES = 'db/imports/official/portals/portals.official.json'
GRID = 'src/God2.ClassicServer.Runtime/WorldContentRuntime.cs'
WIRE_TESTS = 'tests/God2.ClassicServer.Protocol.Tests/OfficialPortalWireTests.cs'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
MAX_SOURCE = 16 * 1024 * 1024
PINNED_CATALOGS = {
    ROUTES: '7ebdf790221d12de9873762da334e383b25e9301b1e09dc6b8f36c8ca605a681',
    WIRE: '46063ac459d048163db010e36acf8dcfb4e2cda7681286139a87f6ba02441e31',
    GATE: 'f2dc7c2dc9a6b450f4a48857d98eec8b182b77d0a0fa5f398461d9e57d3ef76e',
    GRID: '0a2beea3cd756fe37fd1f2432e468ed311c9b0a91e4234c5b1096b4a5f6636d5',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_SOURCE + 1)
    if len(raw) > MAX_SOURCE:
        raise ValueError('source exceeds length bound')
    return raw


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def json_read(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))


def integer(value, maximum, name):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('invalid ' + name)
    return value


def section(text, start, end):
    if text.count(start) != 1:
        raise ValueError('missing or duplicate catalog section: ' + start)
    return text.split(start, 1)[1].split(end, 1)[0]


def parse_routes(text):
    body = section(text, 'private static readonly IReadOnlyDictionary<(ushort MapId, byte AreaId), OfficialPortalRoute> Routes =', '};')
    body = body.split('{', 1)[1]
    pattern = re.compile(
        r'\[\((\d+),\s*(\d+)\)\]\s*=\s*new\((\d+),\s*(\d+),\s*'
        r'new WorldPosition3\((\d+),\s*(\d+)\),\s*(\d+),\s*(\d+),\s*(\d+),\s*'
        r'new WorldPosition3\((\d+),\s*(\d+)\),\s*"(ExplicitActivation|MovementRegion)",\s*"([^"\r\n]+)"\)')
    records, seen, end = [], set(), 0
    for match in pattern.finditer(body):
        if body[end:match.start()].strip(' \r\n\t,'):
            raise ValueError('unsupported route syntax')
        n = [int(v) for v in match.groups()[:11]]
        key_map, key_area, sm, sa, sx, sy, radius, dm, da, dx, dy = n
        if (key_map, key_area) != (sm, sa) or (sa, sm) in seen:
            raise ValueError('duplicate or inconsistent route key')
        seen.add((sa, sm))
        for v in (sm, dm):
            integer(v, 1023, 'scene')
        for v in (sa, da):
            integer(v, 63, 'area')
        for v in (sx, sy, dx, dy, radius):
            integer(v, 32767, 'coordinate')
        records.append({'source': {'area': sa, 'scene': sm, 'x': sx, 'y': sy},
                        'destination': {'area': da, 'scene': dm, 'x': dx, 'y': dy},
                        'trigger': {'kind': match[12], 'retained_radius': radius},
                        'observation_reference': match[13],
                        'catalog_excerpt': match[0],
                        'catalog_line': text[:text.index(match[0])].count('\n') + 1})
        end = match.end()
    if not records or body[end:].strip(' \r\n\t,'):
        raise ValueError('empty or unsupported route catalog')
    return records


def parse_gate(text):
    records = []
    for statement in text.split(';'):
        if 'SET `source_sha256`' not in statement:
            continue
        values = re.findall(r'`([a-z_0-9]+)`\s*=\s*(?:\x27([^\x27]*)\x27|([0-9]+))', statement)
        row = {}
        for key, string, number in values:
            if key in row:
                raise ValueError('duplicate gate field: ' + key)
            row[key] = int(number) if number else string
        required = {'portal_id', 'source_sha256', 'source_reference', 'source_map_id',
                    'destination_map_id', 'source_x', 'source_y', 'source_radius',
                    'destination_x', 'destination_y', 'client_build_id', 'enabled',
                    'identity_evidence_status', 'source_coordinate_evidence_status',
                    'destination_coordinate_evidence_status', 'trigger_evidence_status'}
        if set(row) != required or row['enabled'] != 1:
            raise ValueError('unsupported or incomplete portal gate')
        if not re.fullmatch('[0-9A-Fa-f]{64}', row['source_sha256']):
            raise ValueError('invalid gate hash')
        records.append(row)
    ids = [r['portal_id'] for r in records]
    if not records or len(ids) != len(set(ids)):
        raise ValueError('empty or duplicate portal gate')
    return records


def scene_index(atlas):
    """Check selector rows against their embedded original CAN bytes."""
    areas, result = {}, {}
    for area in atlas['areas']:
        key = integer(area['area'], 63, 'area')
        if key in areas:
            raise ValueError('duplicate atlas area')
        raw = bytes.fromhex(area['source']['raw_hex'])
        if sha(raw) != area['source']['sha256']:
            raise ValueError('atlas CAN hash mismatch')
        areas[key] = (area, raw, parse_can(raw))
    for row in atlas['scenes']:
        key = (integer(row['area'], 63, 'area'), integer(row['scene'], 255, 'scene'))
        if key in result:
            raise ValueError('duplicate atlas scene')
        area, raw, can = areas[key[0]]
        index = can['scene_file_indices'][key[1]]
        offset = 16 + can['file_count'] * 64 + key[1] * 2
        expected_path = str(Path(area['can_relative']).parent / can['files'][index]['asset_path']).replace('\\', '/')
        if (row['file_index'] != index or row['source_offset'] != offset
                or row['source_sha256'] != sha(raw)
                or row['source_file'] != area['can_relative']
                or row['asset_relative'] != expected_path
                or row['packed_selector'] != (key[1] << 6 | key[0])):
            raise ValueError('atlas scene disagrees with CAN')
        result[key] = row
    return result


def audit_xjz(root):
    path = (root / 'xjz_evidence.sqlite').resolve()
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        samples = connection.execute('SELECT COUNT(*) FROM teleport_flow_sample').fetchone()[0]
        bindings = connection.execute('SELECT COUNT(*) FROM transport_binding').fetchone()[0]
        groups = connection.execute('SELECT binding_kind, packet_evidence_boundary, COUNT(*) '
                                    'FROM transport_service_template GROUP BY binding_kind, '
                                    'packet_evidence_boundary ORDER BY binding_kind, packet_evidence_boundary').fetchall()
    with path.open('rb') as stream:
        database_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'file': 'xjz_evidence.sqlite', 'sha256': database_sha,
            'teleport_flow_sample_count': samples,
            'transport_binding_count': bindings,
            'service_templates': [{'kind': k, 'packet_evidence_boundary': b, 'count': n}
                                  for k, b, n in groups],
            'imported_edges': 0,
            'qualification': 'Different client corpus; static mount bindings are not map edges.'}


def build_teleports(classic, xjz, atlas_path):
    classic, xjz = Path(classic).resolve(), Path(xjz).resolve()
    sources, texts = {}, {}

    def source(relative):
        path = (classic / relative).resolve()
        if not path.is_relative_to(classic):
            raise ValueError('evidence reference escapes Classic root')
        if relative not in sources:
            raw = read(path)
            sources[relative] = {'corpus': 'classic', 'file': relative,
                                 'sha256': sha(raw), 'size': len(raw)}
            texts[relative] = raw.decode('utf-8-sig')
        return texts[relative]

    routes = parse_routes(source(ROUTES))
    gates = parse_gate(source(GATE))
    wire = source(WIRE)
    build = re.search(r'ClientBuildId = "([^"]+)"', wire)[1]
    exe_sha = re.search(r'ClientExeSha256 = "([0-9A-F]{64})"', wire)[1].lower()
    source(GRID)
    source(WIRE_TESTS)
    source('database/schema/109_add_portal_evidence_gate.sql')
    source('database/schema/115_publish_official_portal_resource_links.sql')
    source('database/schema/083_publish_latest_verified_map3_map19_portals.sql')
    atlas_raw = read(atlas_path)
    index = scene_index(json_read(atlas_raw))
    used, edges = set(), []
    for route in routes:
        src, dst = route['source'], route['destination']
        matches = [g for g in gates if (g['source_x'], g['source_y'], g['source_radius'],
                    g['destination_x'], g['destination_y']) ==
                   (src['x'], src['y'], route['trigger']['retained_radius'], dst['x'], dst['y'])]
        if len(matches) != 1 or matches[0]['portal_id'] in used:
            raise ValueError('route has missing, ambiguous or duplicate migration gate')
        gate = matches[0]
        used.add(gate['portal_id'])
        reference = gate['source_reference']
        source(reference)
        if sources[reference]['sha256'] != gate['source_sha256'].lower():
            raise ValueError('migration evidence hash mismatch: ' + reference)
        if gate['client_build_id'] != build:
            raise ValueError('gate build mismatch')
        # A destination must also exist in the retained wire catalog, with the
        # same coordinates. The runtime map ID is intentionally not a selector.
        destination = re.search(
            r'\[\(' + str(dst['scene']) + r',\s*' + str(dst['area']) +
            r'\)\]\s*=\s*new\(\d+,\s*' + str(dst['area']) + r',\s*' +
            str(dst['scene']) + r',\s*' + str(dst['x']) + r',\s*' + str(dst['y']) +
            r',\s*(\d+),\s*(0x[0-9A-Fa-f]+),\s*(0x[0-9A-Fa-f]+|PreservedOpaqueWord),', wire)
        if destination is None:
            raise ValueError('route destination absent from wire evidence')
        mode, prelude, opaque = destination.groups()
        dst['position_mode'] = int(mode)
        dst['prelude_state'] = int(prelude, 16)
        dst['opaque_word'] = 0x0404 if opaque == 'PreservedOpaqueWord' else int(opaque, 16)
        retained_frames = set(re.findall(r'"(0C0061[0-9A-F]{18})"', source(WIRE_TESTS)))
        matching_frames = []
        for hex_frame in retained_frames:
            frame = bytes.fromhex(hex_frame)
            selector, opaque_word, packed = struct.unpack_from('<HHI', frame, 3)
            if (selector, opaque_word, packed & 3, (packed >> 2) & 32767, packed >> 17) == (
                    dst['scene'] << 6 | dst['area'], dst['opaque_word'], dst['position_mode'], dst['x'], dst['y']):
                if sum(v + 60 for v in frame[:-1]) & 255 != frame[-1]:
                    raise ValueError('retained transition checksum mismatch')
                matching_frames.append(hex_frame)
        if len(matching_frames) != 1:
            raise ValueError('missing or ambiguous retained transition bytes')
        route['retained_transition'] = {'decoded_frame_hex': matching_frames[0],
            'source': WIRE_TESTS,
            'source_line': source(WIRE_TESTS)[:source(WIRE_TESTS).index(matching_frames[0])].count('\n') + 1,
            'qualification': 'Retained Classic codec test vector, not a new live capture'}
        for endpoint, field in ((src, 'source'), (dst, 'destination')):
            endpoint['legacy_database_map_id'] = gate[field + '_map_id']
            row = index.get((endpoint['area'], endpoint['scene']))
            endpoint['current_selector_match'] = None if row is None else {
                k: row[k] for k in ('asset_relative', 'asset_variants', 'packed_selector',
                                   'file_index', 'source_file', 'source_offset', 'source_sha256')}
        route['id'] = gate['portal_id']
        route['coordinate_unit'] = 'unscaled unsigned 15-bit wire X/Y'
        route['current_coordinate_transform'] = None
        route['trigger']['evidence_status'] = gate['trigger_evidence_status']
        route['legacy_evidence_status'] = {k: v for k, v in gate.items() if k.endswith('_status')}
        route['provenance'] = {'catalog': ROUTES, 'migration': reference,
                               'migration_sha256': gate['source_sha256'].lower(), 'gate': GATE,
                               'wire': WIRE, 'client_build_id': build, 'client_exe_sha256': exe_sha}
        route['runtime_eligible'] = False
        route['unresolved'] = ['Current-build route and coordinate compatibility unproven',
                               'Current-build activation and complete transition unproven']
        if gate['trigger_evidence_status'] != 'Verified':
            route['unresolved'].append('Retained trigger radius is derived, not original evidence')
        if not all(e['current_selector_match'] for e in (src, dst)):
            route['unresolved'].append('Current selector missing from atlas')
        edges.append(route)
    if len(used) != len(gates):
        raise ValueError('migration gate has routes absent from runtime catalog')
    candidate_doc = json_read(source(CANDIDATES))
    candidates = candidate_doc['records']
    if candidate_doc['recordCount'] != len(candidates):
        raise ValueError('candidate count mismatch')
    ids = [c['id'] for c in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate candidate id')
    # Pin the retained relationship between runtime selectors and DB gates;
    # coordinate coincidence alone must not admit edits to either catalog.
    for name, expected_sha in PINNED_CATALOGS.items():
        if sources[name]['sha256'] != expected_sha:
            raise ValueError('retained catalog hash mismatch: ' + name)
    unresolved = [{'id': c['id'], 'retained_record': c, 'runtime_eligible': False,
                   'source': CANDIDATES, 'source_record_index': i,
                   'reason': 'Resource association or visual candidate; exact edge not proven'}
                  for i, c in enumerate(candidates)]
    audit = audit_xjz(xjz)
    for name in ('evidence-transport-binding-v0.md', 'evidence-transport-service-template-v0.md'):
        raw = read(xjz / name)
        sources['xjz/' + name] = {'corpus': 'xjz', 'file': name, 'sha256': sha(raw), 'size': len(raw)}
    edges.sort(key=lambda r: r['id'])
    return {'schema_version': 1, 'edges': edges,
            'unresolved_candidates': sorted(unresolved, key=lambda r: r['id']),
            'runtime_edges': [], 'sources': [sources[k] for k in sorted(sources)],
            'current_atlas': {'sha256': sha(atlas_raw), 'schema_version': json_read(atlas_raw).get('schema_version'),
                              'qualification': 'Exact selector lookup in retained CAN atlas; not cross-build map equivalence'},
            'xjz_audit': audit,
            'native_test_boundary': {'image_sha256': IMAGE_SHA,
                'selector_slice_rva': ['0x6bcdc', '0x6bd4a'],
                'position_slice_rva': ['0x6bf6c', '0x6bf9e'],
                'qualification': 'Scalar slices only; tests enter blocks directly and stop before resource calls'},
            'legacy_coordinate_note': {'units_per_resource_cell': 21, 'source': GRID,
                'qualification': 'Classic claim only; no grid conversion or current transform applied'},
            'counts': {'retained_coordinate_edges': len(edges),
                       'legacy_trigger_verified': sum(r['trigger']['evidence_status'] == 'Verified' for r in edges),
                       'legacy_trigger_derived': sum(r['trigger']['evidence_status'] == 'Derived' for r in edges),
                       'current_selector_pairs_present': sum(all(r[e]['current_selector_match'] for e in ('source', 'destination')) for r in edges),
                       'unresolved_candidates': len(unresolved), 'runtime_eligible_edges': 0}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classic', type=Path, default=CLASSIC)
    parser.add_argument('--xjz', type=Path, default=XJZ)
    parser.add_argument('--scenes', type=Path, default=ROOT / 'artifacts/world-atlas/current-scenes.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        if (output == args.scenes.resolve() or output.is_relative_to(args.classic.resolve())
                or output.is_relative_to(args.xjz.resolve())):
            raise ValueError('output would overwrite evidence inputs')
        result = build_teleports(args.classic, args.xjz, args.scenes)
        data = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + '\n'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(data, encoding='utf-8', newline='\n')
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, sqlite3.Error) as error:
        parser.error(str(error))
    print(json.dumps(result['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
