"""Bounded MDL model/entry/attachment graph; never grants monster placements.

All 142 current MDLs must match the earlier zero-Pass qualification receipt.
Runs complete original 441560/441DF0/441EB0/449BB0 and the complete
43F1C0 -> 433AF0 -> 442990 preallocated-block lookup path. No callee adapters.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct

import capstone
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as x
from .current_monster_binary_producer import parse_mdl
from .omega_assets import decode_csvz
from .world_atlas import parse_catalog
from .world_scenes import parse_can

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
PIN = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
IMAGE_PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE, STACK, DATA, TABLE, NODES, STOP = 0x400000, 0x2000000, 0x3000000, 0x3100000, 0x3200000, 0x2100000
SP = STACK + 0x8000
SPANS = ((0x41560, 0x415db), (0x41df0, 0x41e73), (0x41eb0, 0x41eb7),
         (0x49bb0, 0x49bdc), (0x3f1c0, 0x3f212), (0x33af0, 0x33b9b),
         (0x42990, 0x429b5), (0x48980, 0x48dc0), (0x48dc0, 0x48ffb),
         (0x4c420, 0x4c6c4), (0x47440, 0x47750), (0x41ec0, 0x41f10),
         (0x496b0, 0x49737), (0x34210, 0x3425d), (0x49000, 0x49328),
         (0x67063, 0x67099), (0x83530, 0x83563))


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def half(n):
    return n // 2 if n >= 0 else -((-n) // 2)


def relative_target(source, reference):
    path = (CLIENT / source).parent / reference.replace('\\', '/')
    require(path.resolve().is_relative_to((CLIENT / 'Data2/map').resolve()), 'Attachment escapes map subtree')
    return path.resolve().relative_to(CLIENT.resolve()).as_posix().lower()


class Native:
    def __init__(self, image):
        self.vm = v = Uc(UC_ARCH_X86, UC_MODE_32)
        for at, size in ((0, 0x1000), (BASE, (len(image)+4095)&~4095),
                         (STACK, 0x10000), (STOP, 0x1000), (DATA, 0x10000),
                         (TABLE, 0x10000), (NODES, 0x100000)):
            v.mem_map(at, size)
        v.mem_write(BASE, image)
        self.allowed = []
        self.steps = 0
        v.hook_add(UC_HOOK_CODE, self.code)

    def code(self, vm, at, size, _):
        self.steps += 1
        require(any(a <= at < b for a, b in self.allowed), 'Unexpected native boundary ' + hex(at))

    def put(self, at, *values):
        self.vm.mem_write(at, struct.pack('<'+'I'*len(values), *(v & 0xffffffff for v in values)))

    def call(self, address, obj, args, spans, cleanup):
        v = self.vm
        self.allowed = [(BASE+a, BASE+b) for a, b in spans]
        self.steps = 0
        self.put(SP, STOP, *args)
        v.reg_write(x.UC_X86_REG_ESP, SP)
        v.reg_write(x.UC_X86_REG_ECX, obj)
        v.emu_start(address, STOP, count=50000)
        require(v.reg_read(x.UC_X86_REG_EIP) == STOP, 'Native instruction budget / return')
        require(v.reg_read(x.UC_X86_REG_ESP) == SP+4+cleanup, 'Native return stack')
        return v.reg_read(x.UC_X86_REG_EAX)

    def entries(self, values):
        self.call(0x441560, DATA, [], [SPANS[0]], 0)
        expected = [-1]*8
        returns = []
        for i in range(4):
            px, py = values[2*i:2*i+2]
            accept = px == -1 or [px, py] not in [expected[k:k+2] for k in range(0, 8, 2)]
            ret = self.call(0x441df0, DATA, [i, px, py], [SPANS[1]], 12)
            require(ret == int(accept), 'Native entry uniqueness predicate')
            if accept:
                expected[2*i:2*i+2] = [px, py]
            returns.append(ret)
        actual = list(struct.unpack('<8i', self.vm.mem_read(DATA+0x2c, 32)))
        require(actual == expected, 'Native entry model state')
        return {'source_pairs': values, 'setter_returns': returns, 'native_pairs': actual}

    def transform(self, px, py):
        self.call(0x449bb0, 0, [px, py, DATA+0x800, DATA+0x804], [SPANS[3]], 0)
        actual = list(struct.unpack('<2i', self.vm.mem_read(DATA+0x800, 8)))
        require(actual == [px-half(py), px+half(py+1)], 'Native point projection')
        return actual

    def tile_type(self, kind):
        self.put(DATA+8, DATA+0x400)
        self.put(DATA+0x414, kind)
        return self.call(0x441eb0, DATA, [], [SPANS[2]], 0)

    def lookup(self, placements, query):
        # Construct explicit source-ordered linked-list fixtures. Native list
        # insertion order is not claimed; duplicate matches remain ambiguous.
        require(len(placements) < 250000, 'Placement fixture bound')
        grouped = defaultdict(list)
        for i, p in enumerate(placements):
            grouped[tuple(p['block'])].append((i, p))
        empty = DATA+0x3000
        self.put(empty+0xc, 0)
        self.vm.mem_write(TABLE, struct.pack('<I', empty)*16384)
        self.put(DATA+0x1464, TABLE, 128, 128)
        bucket = DATA+0x4000
        bx, by = query[0]//21, query[1]//21
        candidates = grouped.get((bx, by), [])
        require(len(candidates) < 16000, 'Native node arena bound')
        require(0 <= bx < 128 and 0 <= by < 128, 'Source lookup block bounds')
        self.put(TABLE+(by*128+bx)*4, bucket)
        self.put(bucket+0xc, NODES if candidates else 0)
        matches = []
        for j, (i, p) in enumerate(candidates):
            at = NODES+j*0x40
            self.put(at+8, at+0x40 if j+1 < len(candidates) else 0)
            self.put(at+0x14, *p['fields'][3:5])
            if p['fields'][3:5] == list(query):
                matches.append((at, i))
        result = self.call(0x43f1c0, DATA, list(query), SPANS[4:7], 8)
        require(result == (matches[0][0] if matches else 0), 'Native coordinate lookup output')
        return {'query_xy': list(query), 'candidate_count': len(candidates),
                'matching_source_indices': [i for at, i in matches],
                'fixture_first_result_index': matches[0][1] if matches else None,
                'steps': self.steps}


def run():
    raw = (CLIENT/'God2.exe').read_bytes()
    require(sha(raw) == PIN, 'Current PE identity')
    image = pefile.PE(data=raw).get_memory_mapped_image()
    saved = (ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(sha(saved) == IMAGE_PIN, 'Mapped native identity')
    spans = []
    for a, b in SPANS:
        require(image[a:b] == saved[a:b], 'Current/native code mismatch '+hex(a))
        spans.append({'start_rva': hex(a), 'end_rva': hex(b), 'sha256': sha(image[a:b])})
    require(image[0x187634:0x187639] == b'.hmd\0' and image[0x1885e0:0x1885e5] == b'.mdt\0', 'Attachment literals')
    native = Native(image)
    prior_raw = (ROOT/'artifacts/research/mdl-zero-pass-20260927/evidence.json').read_bytes()
    require(sha(prior_raw) == '79e3c1da56eef4db78b8b72b17865bb39fd9d739d02a4b7586cd14013f61f0f7', 'Prior source receipt identity')
    prior = json.loads(prior_raw)
    pins = prior['sources']['parsed']
    require(prior['status'] == 'PASS' and len(pins) == 142, 'Prior complete-source qualification')
    observed = {p.relative_to(CLIENT).as_posix().lower() for p in (CLIENT/'Data2/map').rglob('*')
                if p.is_file() and p.suffix.lower() in ('.mdl', '.mdlz')}
    require(observed == {p['file'].lower() for p in pins}, 'MDL source set changed')
    models = {}
    type_counts, placement_types, extras6, extras7, extras9, attachments, passvalues = [Counter() for _ in range(7)]
    source_rows, edges, unique_entries, unique_points, special_models = [], [], {}, set(), []
    for pin in pins:
        path = CLIENT/pin['file']; raw = path.read_bytes()
        require(sha(raw) == pin['source_sha256'], 'MDL compressed identity')
        plain = decode_csvz(raw) if path.suffix.lower() == '.mdlz' else raw
        require(sha(plain) == pin['decoded_sha256'], 'MDL decoded identity')
        m = parse_mdl(plain, allow_parent_rom=True)
        require(m['unaccounted_bytes'] == 0, 'Unconsumed MDL bytes')
        key = pin['file'].lower().removesuffix('z')
        models[key] = m
        source_rows.append({k: pin[k] for k in ('file', 'source_sha256', 'decoded_sha256', 'models', 'placements')})
        for t in m['tiles']:
            type_counts[t['fields'][0]] += 1
        for i, model in enumerate(m['models']):
            values = model['extra_8_ints']; tup = tuple(values)
            if tup not in unique_entries:
                unique_entries[tup] = native.entries(values)
            pairs = unique_entries[tup]['native_pairs']
            for j in range(0, 8, 2):
                if pairs[j] >= 0:
                    unique_points.add(tuple(pairs[j:j+2]))
            if any(pairs[j] >= 0 for j in range(0, 8, 2)):
                special_models.append({'file': pin['file'], 'model': i, 'offset': model['offset'], 'raw_pairs': values,
                                       'native_pairs': pairs})
            for grid in model['grids']:
                passvalues.update(int(v) for v in plain[grid['start']:grid['end_exclusive']].split())
        for i, p in enumerate(m['placements']):
            f = p['fields']; model = m['models'][f[0]]; body = model['layers'][0][0]
            kind = None if body == -1 else m['tiles'][body]['fields'][0] & 15
            placement_types[str(kind)] += 1
            extras6[f[6]] += 1; extras7[f[7]] += 1; extras9[f[9]] += 1
            ref = p['attached_reference']
            if ref:
                attachments[Path(ref).suffix.lower()] += 1
            if ref or f[6] >= 0:
                pairs = unique_entries[tuple(model['extra_8_ints'])]['native_pairs']
                targets = []
                for j in range(0, 8, 2):
                    if pairs[j] >= 0:
                        dx, dy = native.transform(*pairs[j:j+2])
                        targets.append({'entry_index': j//2, 'xy': [f[3]+dx, f[4]+dy]})
                edges.append({'source': pin['file'], 'placement': i, 'offset': p['offset'],
                              'end_exclusive': p['end_exclusive'], 'record_sha256': p['sha256'],
                              'block': p['block'], 'fields': f, 'body_tile_type': kind,
                              'attachment': ref, 'target_asset': relative_target(pin['file'], ref) if ref else None,
                              'entry_points': targets, 'monster_identity': None, 'encounter_conditions': None})
    require(sum(p['models'] for p in source_rows) == 12140 and sum(p['placements'] for p in source_rows) == 169522, 'Source count pin')
    type_native = []
    for kind in sorted({k & 15 for k in type_counts}):
        require(native.tile_type(kind) == kind, 'Native tile getter')
        type_native.append(kind)
    point_results = [{'source_pair': list(p), 'native_offset': native.transform(*p)} for p in sorted(unique_points)]
    raw = (CLIENT/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    require(sha(raw) == '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731', 'Map catalog source pin')
    catalog = parse_catalog(decode_csvz(raw))
    can_rows, asset_scenes = [], defaultdict(list)
    for row in catalog:
        if row['scene'] != 0:
            continue
        path = (CLIENT/row['mdt_relative']).with_suffix('.can')
        if not path.is_file():
            continue
        raw = path.read_bytes(); can = parse_can(raw)
        can_rows.append({'area': row['area'], 'file': path.relative_to(CLIENT).as_posix(), 'sha256': sha(raw),
                         'files': can['files'], 'scene_file_indices': can['scene_file_indices']})
        for scene, index in enumerate(can['scene_file_indices']):
            r = can['files'][index]
            target = (path.parent/r['asset_path']).resolve().relative_to(CLIENT.resolve()).as_posix().lower()
            asset_scenes[target].append({'area': row['area'], 'scene': scene, 'can_record': index,
                                         'record_sha256': r['source_record_sha256']})
    can_pin = sha(json.dumps(sorted((r['file'].lower(), r['sha256']) for r in can_rows), separators=(',', ':')).encode())
    require(can_pin == 'c01d4a963563a19822f4a9d52de31e630f960d15f879d99ccc04dd49ad7e9dbe', 'Current CAN source aggregate identity')
    queries = {}
    for edge in edges:
        target = edge['target_asset']
        edge['can_candidates'] = asset_scenes.get(target, []) if target else []
        # .hmd is a different placement grammar; do not pretend it is MDL.
        destination = target.removesuffix('.mdt')+'.mdl' if target and target.endswith('.mdt') else None
        if target is None:
            destination = edge['source'].lower().removesuffix('z')
        edge['destination_mdl_source'] = destination if destination in models else None
        if destination in models and edge['fields'][6] >= 0 and edge['fields'][7] >= 0:
            query = tuple(edge['fields'][6:8]); key = (destination, *query)
            if key not in queries:
                queries[key] = dict(native.lookup(models[destination]['placements'], query), destination=destination)
                details = []
                for index in queries[key]['matching_source_indices']:
                    p = models[destination]['placements'][index]
                    model = models[destination]['models'][p['fields'][0]]
                    details.append({'placement': index, 'offset': p['offset'], 'record_sha256': p['sha256'],
                                    'raw_fields': p['fields'], 'attachment': p['attached_reference'],
                                    'raw_model_entry_pairs': model['extra_8_ints']})
                queries[key]['source_matches'] = details
            edge['coordinate_lookup'] = queries[key]
        else:
            edge['coordinate_lookup'] = None
        edge['runtime_route_verified'] = False
    # Focused invalid/absent queries through the actual complete native lookup.
    negative = native.lookup([], (21, 21))
    require(negative['fixture_first_result_index'] is None, 'Empty native lookup')
    # Direct references are machine-code checked; no decompiler name assumptions.
    calls = []
    for a, dest in ((0x48ef8, 0x48980), (0x48f64, 0x48980), (0x48cf7, 0x3f1c0),
                    (0x3f1f4, 0x33af0), (0x3f201, 0x42990), (0x4cc1b, 0x41df0),
                    (0x41f08, 0x4a0f0), (0x6707c, 0x34210), (0x3424c, 0x49000),
                    (0x49034, 0x49040), (0x4901d, 0x49250), (0x6708f, 0x83530)):
        require(image[a] == 0xe8 and a+5+struct.unpack_from('<i', image, a+1)[0] == dest, 'Native call pin')
        calls.append({'call_va': hex(BASE+a), 'target_va': hex(BASE+dest)})
    caller_targets = {0x448dc0: [], 0x448980: [], 0x43f1c0: [], 0x434210: [], 0x449000: []}
    for off in range(0x1000, min(len(image)-5, 0x180000)):
        if image[off] in (0xe8, 0xe9):
            dest = BASE+off+5+struct.unpack_from('<i', image, off+1)[0]
            if dest in caller_targets:
                caller_targets[dest].append(hex(BASE+off))
    pointer_refs = {}
    for target in caller_targets:
        found = []; off = 0; token = struct.pack('<I', target)
        while True:
            off = image.find(token, off)
            if off == -1:
                break
            found.append(hex(BASE+off)); off += 4
        pointer_refs[hex(target)] = found
    require(len(queries) == 1261 and len(edges) == 1626, 'Graph count pin')
    query_results = Counter('missing' if not q['matching_source_indices'] else
                            'unique' if len(q['matching_source_indices']) == 1 else 'multiple' for q in queries.values())
    require(query_results == {'unique': 1248, 'missing': 9, 'multiple': 4}, 'Native query result distribution')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    disassembly = {hex(BASE+a): ['%08X %s %s' % (i.address, i.mnemonic, i.op_str)
                               for i in md.disasm(image[a:b], BASE+a)] for a,b in SPANS}
    return {'status': 'PASS', 'scope': 'SOURCE_GRAPH_AND_BOUNDED_NATIVE_CONSUMERS_NOT_MONSTER_SPAWNS',
            'current_pe_sha256': PIN, 'mapped_sha256': IMAGE_PIN, 'source_mdl_pins': source_rows,
            'counts': {'mdl_files': len(models), 'model_definitions': 12140, 'placements': 169522,
                       'entry_pair_sets': len(unique_entries), 'active_entry_models': len(special_models),
                       'unique_point_projections': len(point_results), 'attachment_or_destination_edges': len(edges),
                       'native_destination_queries': len(queries), 'can_sources': len(can_rows),
                       'qualified_monster_spawns': 0, 'qualified_encounter_regions': 0},
            'tile_source_raw_types': dict(sorted(type_counts.items())), 'placement_body_native_types': dict(placement_types),
            'placement_field6': dict(sorted(extras6.items())), 'placement_field7': dict(sorted(extras7.items())),
            'placement_field9': dict(sorted(extras9.items())), 'attachment_extensions': dict(attachments),
            'pass_byte_counts': dict(sorted(passvalues.items())), 'entry_sets_native': list(unique_entries.values()),
            'special_models': special_models, 'point_projection_native': point_results,
            'tile_getter_native': type_native, 'source_graph': edges, 'can_sources': can_rows,
            'native_queries': list(queries.values()), 'native_empty_lookup': negative,
            'native_query_distribution': dict(query_results), 'can_source_aggregate_sha256': can_pin,
            'source_receipt_sha256': sha(prior_raw),
            'native_scope': 'Complete named functions on source-derived data; map containers/list order are explicit fixtures. No file loader, interaction dispatch, encounter trigger, renderer, or live game run.',
            'code_spans': spans, 'machine_calls': calls,
            'bounded_relative_call_scan': {hex(k):v for k,v in caller_targets.items()},
            'mapped_absolute_pointer_scan': pointer_refs,
            'disassembly': disassembly}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.output.resolve().is_relative_to((ROOT/'artifacts/research/monster-map-placement-join-20260927').resolve()), 'Output scope')
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pending = args.output.with_suffix('.pending')
    pending.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    pending.replace(args.output)
    print(json.dumps(result['counts']))
