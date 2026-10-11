"""Current-only reward/capture coverage and bounded capture-result producer.

JSON goes to stdout. No gameplay value is inferred from the synthetic oracle.
The shared inventory supplies identities; no full EnyName loader is rerun here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_monster_inventory import pinned_catalog, SOURCE, SOURCE_SHA, PLAIN_SHA
from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
MESSAGE = 'Data2/Patch/Comm/message.csvZ'
MESSAGE_SHA256 = '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
MESSAGE_PLAIN_SHA256 = '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'
BASE = 0x400000
FIELDS = ('base_experience', 'capturable')
CATEGORIES = ('normal', 'boss', 'elite', 'quest', 'event', 'summoned')
MESSAGE_IDS = (884, 655, 882, 883, 1151, 1390, 41, 1391, 1392)
SPANS = {
    'output_context_argument': (0x1140c9, 0x1140e7),
    'forward_output_context': (0x1291e4, 0x1291f1),
    'selected_actor_action_load': (0x128d9c, 0x128db0),
    'result_relay': (0x128dd4, 0x128dec),
    'message_selector': (0x11411b, 0x1141c4),
    'message_jump_table': (0x114610, 0x114634),
    'argument_to_actor_word': (0x12b3c2, 0x12b3db),
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_pinned(path, expected, limit):
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit or sha256(raw) != expected:
        raise ValueError('Current source size/hash mismatch: ' + str(path))
    return raw


def load_image(path=IMAGE):
    return read_pinned(path, IMAGE_SHA256, 16 * 1024 * 1024)


def message_evidence(client):
    root = Path(client).resolve()
    path = (root / MESSAGE).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Message source escapes current client')
    raw = read_pinned(path, MESSAGE_SHA256, 1024 * 1024)
    plain = decode_csvz(raw, limit=1024 * 1024)
    if sha256(plain) != MESSAGE_PLAIN_SHA256:
        raise ValueError('Current decoded message hash mismatch')
    rows, offset, remaining = {}, 0, 0
    for line_number, line in enumerate(plain.splitlines(keepends=True), 1):
        columns = line.rstrip(b'\r\n').split(b',')
        if columns[0] == b'SystemMessage':
            remaining = int(columns[1])
        elif remaining:
            remaining -= 1
            identity = int(columns[0])
            if identity in MESSAGE_IDS:
                if identity in rows:
                    raise ValueError('Duplicate result message')
                rows[identity] = {
                    'id': identity, 'source': MESSAGE,
                    'source_sha256': MESSAGE_SHA256,
                    'decoded_sha256': MESSAGE_PLAIN_SHA256,
                    'decoded_offset': offset, 'line': line_number,
                    'length': len(line), 'sha256': sha256(line),
                    'raw_hex': line.hex(), 'text_cp950': columns[2].decode('cp950'),
                    'authority': 'result_label_only',
                }
        offset += len(line)
    if set(rows) != set(MESSAGE_IDS):
        raise ValueError('Missing result message')
    return [dict(rows[mid], selector=index) for index, mid in enumerate(MESSAGE_IDS, 1)]


def native_evidence(image):
    if sha256(image) != IMAGE_SHA256:
        raise ValueError('Pinned native image mismatch')
    return {
        'status': 'verified_bounded_result_relay_not_capture_eligibility',
        'image_sha256': IMAGE_SHA256, 'base': BASE, 'rva_equals_file_offset': True,
        'spans': {name: {
            'rva_start': lo, 'file_offset': lo, 'end_exclusive': hi,
            'sha256': sha256(image[lo:hi]), 'raw_hex': image[lo:hi].hex(),
        } for name, (lo, hi) in SPANS.items()},
        'condition': {'action_byte_equals': 0x96, 'output_pointer_nonnull': True},
        'read': {'actor_offset': 0x286, 'width': 1, 'rva': 0x128de1},
        'write': {'output_offset': 0xb, 'battle_context_offset': 0x53,
                  'width': 1, 'rva': 0x128de7},
        'action_byte_source': {'other_actor_offset': 0x232, 'rva': 0x128da0},
        'message_branch_targets': [v - BASE for v in struct.unpack_from('<9I', image, 0x114610)],
        'execution_boundary': 'Independent original instruction islands; intervening '
            'animation/UI calls and the complete caller path are not executed.',
        'identity_join': None,
        'client_capture_target_selection_gate': None,
        'server_capturability': None, 'capture_probability': None,
    }


class CaptureResultOracle:
    """Execute untouched x86 islands with explicit synthetic operands only."""

    ACTOR, CONTEXT = 0x3400000, 0x3500000

    def __init__(self, image=None):
        # This existing VM adapter loads only the pinned image and bundled Unicorn.
        from .current_battle_entry import NativeRun
        self.native = NativeRun(load_image() if image is None else image)

    def relay(self, status_word, *, action=0x96, output_present=True):
        from .current_battle_entry import SP
        from unicorn import UC_HOOK_MEM_READ
        from unicorn.x86_const import UC_X86_REG_EIP
        if (type(status_word) is not int or not 0 <= status_word <= 0xffff
                or type(action) is not int or not 0 <= action <= 255
                or type(output_present) is not bool):
            raise ValueError('Expected synthetic WORD, action byte, and pointer-presence bool')
        n = self.native
        n.visits.clear()
        n.writes.clear()
        n.put(self.ACTOR, b'\x5a' * 0x300)
        n.put(self.ACTOR + 0x286, struct.pack('<H', status_word))
        n.put(self.CONTEXT, b'\xa5' * 0x80)
        n.put32(SP + 0x1c, self.CONTEXT + 0x48 if output_present else 0)
        n.registers(esp=SP, edi=self.ACTOR, ebx=action)
        reads = []

        def read(vm, access, address, size, value, _):
            reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address, size))

        hook = n.vm.hook_add(UC_HOOK_MEM_READ, read)
        try:
            n.run(0x128dd4, [(0x128dd4, 0x128dec)], {0x128dec, 0x128e60}, budget=16)
        finally:
            n.vm.hook_del(hook)
        return {'stop_rva': n.stop, 'context_hex': bytes(n.vm.mem_read(self.CONTEXT, 0x80)).hex(),
                'result_byte': n.vm.mem_read(self.CONTEXT + 0x53, 1)[0],
                'reads': reads, 'writes': list(n.writes), 'visits': list(n.visits)}

    def select_message(self, selector):
        from .current_battle_entry import SP
        if type(selector) is not int or not 0 <= selector <= 255:
            raise ValueError('Expected synthetic byte selector')
        n = self.native
        n.visits.clear()
        n.writes.clear()
        n.put(self.CONTEXT, b'\xa5' * 0x80)
        n.put(self.CONTEXT + 0x53, bytes([selector]))
        n.registers(esp=SP, esi=self.CONTEXT)
        n.run(0x11411b, [(0x11411b, 0x1141bc)], {0x1141bc, 0x1141c4}, budget=24)
        return {'stop_rva': n.stop, 'message_id': n.get32(SP - 16) if n.stop == 0x1141bc else None,
                'visits': list(n.visits)}


def build_evidence(client=ROOT.parent / 'God2', image_path=IMAGE):
    catalog = pinned_catalog(client)
    native = native_evidence(load_image(image_path))
    records = []
    for row in catalog['records']:
        # Exact source occurrence join preserves names, component/bank/variant inputs.
        identity = {key: row[key] for key in (
            'source_record_index', 'source_line', 'source_offset', 'record_sha256',
            'area_generation', 'area', 'scene', 'ordinal', 'lookup_visible',
            'source_label', 'name_bytes_hex', 'fields_hex', 'raw_record_hex')}
        identity['source_sha256'] = SOURCE_SHA
        records.append({
            'identity': identity, 'category': None,
            'fields': {field: {
                'status': 'unresolved_no_identity_bound_original_producer', 'value': None,
                'value_source_sha256': None, 'value_source_offset': None,
                'producer_rva': None, 'identity_join': None,
            } for field in FIELDS},
        })
    visible = sum(r['identity']['lookup_visible'] for r in records)
    return {
        'schema': 'god2-current-monster-rewards-capture-v1',
        'field_domain': list(FIELDS),
        'sources': {'identity': {'path': SOURCE, 'sha256': SOURCE_SHA, 'decoded_sha256': PLAIN_SHA},
                    'image': {'path': str(Path(image_path).resolve()), 'sha256': IMAGE_SHA256}},
        'identity_join_key': ['source_sha256', 'source_record_index', 'area_generation',
                              'area', 'scene', 'ordinal'],
        'coverage': {'source_occurrences': len(records),
                     'source_groups': len(catalog['loaded_groups']),
                     'lookup_visible_records': visible, 'lookup_visible_groups': len(catalog['groups']),
                     'superseded_occurrences': len(records) - visible,
                     'true_wild_monster_denominator': None,
                     'all_monster_systems_enumerated': False,
                     'categories': {category: {'denominator': None, 'verified_records': 0}
                                    for category in CATEGORIES},
                     'fields': {field: {'verified_records': 0, 'unresolved_source_occurrences': len(records),
                                        'unresolved_lookup_records': visible} for field in FIELDS}},
        'native_proof': native, 'result_messages': message_evidence(client),
        'producer_frontiers': {
            'capture_result': {'actor_offset': 0x286, 'candidate_argument_writer_rva': 0x12b3c2,
                               'candidate_argument_offset_at_slice_entry': 0x60,
                               'capture_path_binding_verified': False,
                               'next': 'Qualify the 12B060 call path that supplies this WORD for '
                                       'action 0x96, then its original upstream producer and identity.'},
            'capturable': {'producer_rva': None, 'client_target_gate_rva': None,
                           'next': 'Recover pre-command capture target filtering and a distinct '
                                   'original server eligibility producer, each bound to monster identity.'},
            'base_experience': {'producer_rva': None, 'source_offset': None,
                                'identity_input_loader_rva': 0x5a1a0,
                                'identity_input_lookup_rva': 0x5a0a0,
                                'next': 'Find an original monster-definition or reward-calculation '
                                        'producer with an identity-preserving input join. EnyName '
                                        'occurrences and awarded/display XP do not establish it.'},
        },
        'records': records, 'runtime_eligible': False,
        'limitations': ['The result relay condition is not capture eligibility.',
                        'No monster base EXP, target gate, capturability or probability recovered.',
                        'EnyName coverage does not exhaust normal/boss/elite/quest/event/summoned systems.',
                        'No names, visual IDs, pets, descriptions or transformation-card stats are joined.',
                        'Bounded unresolved evidence is not proof of global absence.'],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'God2')
    parser.add_argument('--image', type=Path, default=IMAGE)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args(argv)
    report = build_evidence(args.client, args.image)
    if args.summary:
        report = {key: value for key, value in report.items() if key != 'records'}
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
