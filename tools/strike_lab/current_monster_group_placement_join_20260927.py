"""Current EnyName namespace/map join and native S2C71 identity prefix oracle.

Descriptors are source-backed fixtures, not a new full EnyName loader run.
No monster placement, actor construction or server integration is performed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

import pefile
from .current_monster_inventory import pinned_catalog, SOURCE, SOURCE_SHA, PLAIN_SHA
from .omega_assets import decode_csvz
from .world_atlas import parse_catalog
from .current_monster_base_stats import _LookupFixture, IMAGE, IMAGE_SHA256, MESSAGES
from .current_monster_variant_identity import VariantIdentityProbe, SPANS as SPECIAL_SPANS
from .current_indoor_resources import BASE, SP, SCRATCH
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP,
                               UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EFLAGS)

ROOT = Path(__file__).resolve().parents[2]
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(client):
    executable = (client / 'God2.exe').read_bytes()
    if sha(executable) != CLIENT_SHA:
        raise ValueError('Current executable identity changed')
    image = pefile.PE(data=executable).get_memory_mapped_image()
    reference = IMAGE.read_bytes()
    if sha(reference) != IMAGE_SHA256:
        raise ValueError('Mapped reference identity changed')
    spans = {**SPECIAL_SPANS, 'world71_identity_prefix': (0x6a3b4, 0x6a3d9),
             'scene_group_lookup': (0x5a000, 0x5a095),
             'full_name_loader': (0x5a1a0, 0x5a560),
             'world71_dispatch_and_actor_calls': (0x6a3b4, 0x6a62b),
             'monster_actor_packet_coordinate_prefix': (0xcb120, 0xcb2a0)}
    proofs = []
    for name, (lo, hi) in spans.items():
        if image[lo:hi] != reference[lo:hi]:
            raise ValueError('Native span changed: ' + name)
        proofs.append({'name': name, 'rva_start': hex(lo), 'rva_end_exclusive': hex(hi),
                       'sha256': sha(image[lo:hi])})
    catalog = pinned_catalog(client)
    plain = decode_csvz((client / SOURCE).read_bytes())
    if sha(plain) != PLAIN_SHA:
        raise ValueError('Decoded source changed')
    maps = {(r['area'], r['scene']): r for r in parse_catalog(plain)}
    fixture = _LookupFixture(image, catalog)
    world = 0x10000000
    fixture._map_rw(world + 0xaa36480, 4)
    fixture.vm.mem_write(world + 0xaa36480, struct.pack('<I', MESSAGES))
    packet_address = SCRATCH + 0x8000

    def identity_prefix(area, scene, ordinal, noise):
        packet = bytearray([noise] * 21)
        packet[0] = 0x71
        struct.pack_into('<H', packet, 5, area | scene << 6)
        struct.pack_into('<H', packet, 19, ordinal << 3 | (noise & 7))
        vm = fixture.vm
        vm.mem_write(packet_address, bytes(packet))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBX, packet_address)
        vm.reg_write(UC_X86_REG_EBP, world)
        vm.reg_write(UC_X86_REG_EFLAGS, 2)
        vm.emu_start(BASE + 0x6a3b4, BASE + 0x6a3d9, count=5000)
        if vm.reg_read(UC_X86_REG_EIP) != BASE + 0x6a3d9 or vm.reg_read(UC_X86_REG_ESP) != SP:
            raise RuntimeError('S2C71 prefix did not return with balanced native stack')
        if bytes(vm.mem_read(packet_address, 21)) != packet:
            raise RuntimeError('Identity-only prefix unexpectedly mutated packet')
        return {'area': area, 'scene': scene, 'ordinal': ordinal, 'noise': noise,
                'synthetic_packet_hex': packet.hex(), 'returned_pointer': vm.reg_read(UC_X86_REG_EAX)}

    groups, cases = [], []
    for (area, scene), entries in sorted(catalog['groups'].items()):
        first = catalog['group_offsets'][area, scene]
        source_row = catalog['records'][first]
        native_map = maps.get((area, scene))
        assets = []
        if native_map:
            stem = Path(native_map['mdt_relative']).with_suffix('')
            for ext in ('.mdl', '.mbd'):
                for suffix in ('', 'Z'):
                    relative = str(stem) + ext + suffix
                    path = client / relative
                    if path.is_file():
                        raw = path.read_bytes()
                        assets.append({'path': path.relative_to(client).as_posix(),
                                       'sha256': sha(raw), 'size': len(raw)})
        group = {'display_area': area, 'display_scene': scene, 'count': len(entries),
                 'source_first_record_index': first, 'source_first_record_line': source_row['source_line'],
                 'source_first_record_hex': source_row['raw_record_hex'],
                 'map_catalog': native_map, 'map_companion_files': assets,
                 'authority': 'LOOKUP_NAMESPACE_JOIN_NOT_SPAWN_AUTHORITY'}
        groups.append(group)
        for ordinal, noise in ((1, 0), (len(entries), 0), (1, 0xff), (0, 0), (len(entries)+1, 0)):
            case = identity_prefix(area, scene, ordinal, noise)
            expected = 0 if ordinal in (0, len(entries)+1) else 0x23000000 + 26 * (first + ordinal - 1)
            if case['returned_pointer'] != expected:
                raise RuntimeError('Original S2C71 lookup differs from pinned source descriptor')
            cases.append(case)
    for key in ((2, 15, 1), (17, 0, 1), (63, 1023, 8191)):
        case = identity_prefix(*key, 0)
        if case['returned_pointer']:
            raise RuntimeError('Invalid/absent display namespace returned a record')
        cases.append(case)

    special = VariantIdentityProbe(allocation_poison=0xa5)
    special_lookup = special.lookup(1)
    if special.loaded_record != bytes.fromhex('029500000000' + 'a5' * 20):
        raise RuntimeError('Special original loader byte boundary changed')
    if bytes.fromhex(special_lookup['result_hex'])[18:] != b'\xa5' * 8:
        raise RuntimeError('Special native component tail unexpectedly initialized')
    rows = catalog['records']
    stats = {'source_records': len(rows), 'visible_records': sum(r['lookup_visible'] for r in rows),
             'source_groups': len(catalog['loaded_groups']), 'visible_groups': len(groups),
             'groups_matching_map_catalog': sum(g['map_catalog'] is not None for g in groups),
             'visible_rows_matching_map_catalog': sum(g['count'] for g in groups if g['map_catalog']),
             'nonmap_namespace_rows': sum(g['count'] for g in groups if not g['map_catalog']),
             'source_label_differs_from_ordinal': sum(r['source_label'] != r['ordinal'] for r in rows),
             'source_field_widths': dict(Counter(len(r['fields_hex']) for r in rows)),
             'native_prefix_cases': len(cases), 'qualified_spawn_records': 0}
    return {'schema': 'god2-monster-group-placement-join-v1', 'client_sha256': CLIENT_SHA,
            'source_sha256': SOURCE_SHA, 'decoded_sha256': PLAIN_SHA, 'native_spans': proofs,
            'counts': stats, 'groups': groups, 'native_world71_identity_cases': cases,
            'native_scope': 'Original 46A3B4..46A3D9 including full 45A0A0 return; staged source descriptors, unmapped record payloads. No actor allocation/render/placement.',
            'special': {'source_row_hex': b'1,IGS_SPECIAL,0,0,149,1\r\n'.hex(),
                        'loader': 'Original 45A560 full return with bounded CRT adapters',
                        'loaded_hex': special.loaded_record.hex(), 'loader_trace': special.loader_trace,
                        'lookup_synthetic_base': special_lookup,
                        'uninitialized_offsets': list(range(6, 26))},
            'missing': ['server choice of display key for encounter/spawn', 'world scene versus appearance namespace binding',
                        'world coordinates or region and direction', 'weights/counts/respawn and encounter triggers']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'God2')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.client)
    if args.output.resolve().is_relative_to(args.client.resolve()):
        raise ValueError('Output must be outside current client')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sha256': sha(args.output.read_bytes()), **result['counts']}))


if __name__ == '__main__':
    main()
