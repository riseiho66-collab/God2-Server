"""Current EnyName identity coverage and bounded 1C level provenance.

No recovered base values are asserted. Diagnostic packets are synthetic; their
level bytes never enter the inventory. A caller may reuse its loaded actor.
The CLI emits JSON on stdout and does not write artifacts or integrate a DB.
"""
import hashlib
import json
from pathlib import Path
import struct

from .current_world_actor import MESSAGES, BASE, NativeWorldActor
from .current_monster_inventory import parse_enemy_catalog, pinned_catalog
from .current_indoor_resources import STACK, SP, SCRATCH, RETURN
from unicorn import (Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_WRITE,
                     UC_PROT_EXEC, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE)
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX,
                               UC_X86_REG_ECX, UC_X86_REG_ESI,
                               UC_X86_REG_ESP, UC_X86_REG_EIP)

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
GAME_FILE = 'Data2/Patch/Comm/gamedata.csvZ'
GAME_SHA256 = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
GAME_DECODED_SHA256 = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
FIELDS = ('level', 'hp', 'mp', 'constitution', 'strength', 'intelligence', 'speed')
BATTLE = 0x22000000
MANAGER = BATTLE + 0x144938
PACKET = SCRATCH + 0x8000
METADATA = SCRATCH + 0x9000
SPANS = {
    'logical_1c_length': (0x12a6, 0x12ac),
    'queue_1c_call': (0x114358, 0x114360),
    'participant_prefix': (0x115c90, 0x115df1),
    'normal_enemy_identity_join': (0x115df1, 0x115e0c),
    'original_enemy_lookup': (0x5a0a0, 0x5a11c),
    'participant_slot_lookup': (0x11e6e0, 0x11e76a),
    'level_display_prefix': (0x12d02a, 0x12d08d),
    'level_format_strings': (0x194310, 0x194328),
    'metadata_copy_to_actor': (0x121a30, 0x121a4c),
    'special_override_lookup_static_only': (0x5a120, 0x5a198),
    'special_override_call_static_only': (0x115e18, 0x115e4d),
    'alternate_bank_call_static_only': (0x115e4d, 0x115e77),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity_inventory(native=None, *, catalog=None):
    """Attach this lane's null fields to the shared, pinned identity inventory."""
    if native is not None:
        if sha(native.game_data) != GAME_DECODED_SHA256:
            raise ValueError('Current decoded gamedata changed')
        catalog = parse_enemy_catalog(native.game_data)
        if (catalog['loaded_groups'] != native.enemy_loaded_groups
                or catalog['group_offsets'] != native.enemy_group_offsets
                or catalog['groups'] != native.enemy_groups):
            raise AssertionError('Shared inventory/original loader mismatch')
    elif catalog is None:
        catalog = pinned_catalog()
    inventory = []
    for row in catalog['records']:
        index = row['source_record_index']
        inventory.append({
            'identity': {'bank': 'EnyName', 'source_record_index': index,
                         'area_generation': row['area_generation'], 'area': row['area'],
                         'scene': row['scene'], 'ordinal': row['ordinal'],
                         'special_override': None},
            'lookup_visible': row['lookup_visible'],
            'source': {'file': GAME_FILE, 'sha256': GAME_SHA256,
                       'decoded_sha256': GAME_DECODED_SHA256,
                       'decoded_offset': row['source_offset'], 'line': row['source_line'],
                       'record_sha256': row['record_sha256'],
                       'record_size': len(bytes.fromhex(row['raw_record_hex']))},
            'source_column_0_raw': bytes.fromhex(row['fields_hex'][0]).decode('ascii'),
            'name_hex': row['name_bytes_hex'],
            'native_record_hex': (bytes(native.vm.mem_read(
                native.u32(MESSAGES + 0xd2e24) + 26 * index, 26)).hex()
                if native is not None else None),
            'monster_category': None,
            'fields': dict.fromkeys(FIELDS), 'field_authority': dict.fromkeys(FIELDS),
            'runtime_eligible': False,
        })
    return inventory


class _LookupFixture:
    """Descriptor layout adapter only; the 26-byte record arena stays unmapped.

    The shared full-loader regression owns loader qualification. Here original
    code must compute source-backed identity pointers without reading payloads.
    """
    def __init__(self, image, catalog, *, vm=None):
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32) if vm is None else vm
        if vm is None:
            size = (len(image) + 4095) & ~4095
            self.vm.mem_map(BASE, size)
            self.vm.mem_write(BASE, image)
            self.vm.mem_protect(BASE, size, UC_PROT_READ | UC_PROT_EXEC)
        elif bytes(vm.mem_read(BASE, 0x170000)) != image[:0x170000]:
            raise ValueError('Existing native VM code differs from the pinned image')
        for address, size in ((STACK, 0x80000), (SCRATCH, 0x10000),
                              (MESSAGES, 0xe0000), (0x24000000, 0x10000)):
            self._map_rw(address, size)
        self.enemy_groups = catalog['groups']
        self.enemy_group_offsets = catalog['group_offsets']
        self.enemy_loaded_groups = catalog['loaded_groups']
        record_base, descriptor = 0x23000000, 0x24000000
        self.vm.mem_write(MESSAGES + 0xd2e24, struct.pack('<I', record_base))
        for area in range(17):
            groups = [(scene, rows) for (a, scene), rows in self.enemy_groups.items() if a == area]
            self.vm.mem_write(MESSAGES + 0xd2d9c + 8 * area,
                              struct.pack('<II', len(groups), descriptor))
            for scene, rows in groups:
                pointer = record_base + 26 * self.enemy_group_offsets[area, scene]
                self.vm.mem_write(descriptor, struct.pack('<III', scene, len(rows), pointer))
                descriptor += 12

    def _map_rw(self, address, size):
        NativeWorldActor._map_rw(self, address, size)

    def u32(self, address):
        return struct.unpack('<I', self.vm.mem_read(address, 4))[0]


class MonsterLevelProbe:
    """Execute the normal EnyName join and, separately, the Lv formatter prefix.

    No graphics, UI or formatter executes. The actor slot is deliberately empty.
    Default descriptors use the shared inventory and a deliberately unmapped
    record arena. Pass an existing NativeWorldActor to reuse its actual table.
    The transport record is always diagnostic.
    """
    def __init__(self, native=None):
        self.image = IMAGE.read_bytes()
        if sha(self.image) != IMAGE_SHA256:
            raise ValueError('Current native image changed')
        self.catalog = (parse_enemy_catalog(native.game_data) if native is not None
                        else pinned_catalog())
        self.inventory = identity_inventory(native, catalog=self.catalog)
        self.native = native if native is not None else _LookupFixture(self.image, self.catalog)
        self.descriptor_authority = ('existing_original_loader_output' if native is not None
                                     else 'shared_source_descriptor_fixture; record_arena_unmapped')
        n = self.native
        n._map_rw(BATTLE, 4096)
        n._map_rw(MANAGER & ~4095, 0x2000)
        n.vm.mem_write(BATTLE + 0x28, struct.pack('<I', MESSAGES))
        n.vm.mem_write(MANAGER + 0x38, bytes(28 * 24))
        self.record_base = n.u32(MESSAGES + 0xd2e24)

    def _run(self, start, stops, ranges, writable, *, budget=1500):
        n, visits, reads = self.native, [], []

        def code(vm, address, size, context):
            rva = address - BASE
            if rva in stops:
                vm.emu_stop()
                return
            if not any(lo <= rva and rva + size <= hi for lo, hi in ranges):
                raise AssertionError(f'Outside qualified instruction ranges: {rva:x}')
            visits.append(rva)

        def write(vm, access, address, size, value, context):
            if not any(lo <= address and address + size <= hi for lo, hi in writable):
                raise AssertionError(f'Unexpected native write: {address:x}')

        def read(vm, access, address, size, value, context):
            if self.record_base <= address < self.record_base + 26 * len(self.inventory):
                raise AssertionError('Prefix unexpectedly reads enemy payload')
            if PACKET <= address < PACKET + 4096:
                if address + size > PACKET + 45:
                    raise AssertionError('Read outside 45-byte diagnostic record')
                reads.append((vm.reg_read(UC_X86_REG_EIP) - BASE, address - PACKET, size))

        hooks = [n.vm.hook_add(UC_HOOK_CODE, code),
                 n.vm.hook_add(UC_HOOK_MEM_WRITE, write),
                 n.vm.hook_add(UC_HOOK_MEM_READ, read)]
        try:
            n.vm.emu_start(BASE + start, RETURN, count=budget)
            stop = n.vm.reg_read(UC_X86_REG_EIP) - BASE
            if stop not in stops:
                raise AssertionError('Native instruction budget exhausted')
        finally:
            for hook in hooks:
                n.vm.hook_del(hook)
        return {'stop_rva': stop, 'visits': visits, 'packet_reads': reads}

    def join(self, area, scene, ordinal, *, diagnostic_level, slot=14, poison=0xa5):
        if (any(type(v) is not int for v in (area, scene, ordinal, diagnostic_level, slot, poison))
                or not 0 <= area < 17 or not 0 <= scene <= 65535
                or not 0 <= ordinal <= 65535 or not 0 <= diagnostic_level <= 255
                or not 0 <= slot < 28 or not 0 <= poison <= 255):
            raise ValueError('Outside bounded normal enemy diagnostic inputs')
        n = self.native
        packet = bytearray(45)
        packet[0:3] = bytes((0x1c, slot, diagnostic_level))
        struct.pack_into('<HHH', packet, 3, 0x1234, 0x400, ordinal)
        packet[9] = area
        struct.pack_into('<H', packet, 11, scene)
        n.vm.mem_write(PACKET, bytes(packet))
        n.vm.mem_write(SP - 0x400, bytes((poison,)) * 0x500)
        n.vm.mem_write(SP, struct.pack('<II', RETURN, PACKET))
        n.vm.reg_write(UC_X86_REG_ESP, SP)
        n.vm.reg_write(UC_X86_REG_ECX, BATTLE)
        for register in (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ESI):
            n.vm.reg_write(register, poison * 0x01010101)
        trace = self._run(0x115c90, {0x115e0c},
                          ((0x115c90, 0x115e0c), SPANS['original_enemy_lookup'],
                           SPANS['participant_slot_lookup']), ((SP - 0x400, SP + 0x100),))
        stack = n.vm.reg_read(UC_X86_REG_ESP)
        if stack != SP - 0x1a8:
            raise AssertionError('Participant prefix stack mismatch')
        pointer = n.vm.reg_read(UC_X86_REG_EAX)
        trace.update({'metadata_hex': bytes(n.vm.mem_read(stack + 0x3c, 56)).hex(),
                      'record_pointer': pointer,
                      'input_authority': 'synthetic_diagnostic_only'})
        if bytes(n.vm.mem_read(PACKET, 45)) != packet:
            raise AssertionError('Prefix changed diagnostic packet')
        return trace

    def display_prefix(self, metadata):
        if type(metadata) is not bytes or len(metadata) != 56:
            raise ValueError('Expected exact prefix metadata')
        n = self.native
        n.vm.mem_write(METADATA, metadata)
        n.vm.reg_write(UC_X86_REG_ESI, METADATA)
        n.vm.reg_write(UC_X86_REG_ESP, SP)
        trace = self._run(0x12d02a, {0x12d045, 0x12d088},
                          (SPANS['level_display_prefix'],), ((SP - 0x40, SP + 0x80),))
        stack = n.vm.reg_read(UC_X86_REG_ESP)
        trace['format_va'] = n.u32(stack + 4)
        trace['argument'] = n.u32(stack + 8) if trace['stop_rva'] == 0x12d088 else None
        trace['formatter_executed'] = False
        return trace

    def evidence(self):
        visible = [r for r in self.inventory if r['lookup_visible']]
        for row in visible:
            key = row['identity']
            trace = self.join(key['area'], key['scene'], key['ordinal'], diagnostic_level=23)
            if trace['record_pointer'] != self.record_base + 26 * key['source_record_index']:
                raise AssertionError('Native battle join differs from loaded identity')
        authority = {}
        for field in FIELDS:
            authority[field] = {
                'value': None, 'source_sha256': None, 'source_offset': None,
                'verified_record_count': 0, 'unresolved_visible_record_count': len(visible),
                'status': 'unresolved_wild_monster_base_value',
                'consumer_evidence': ['participant_prefix', 'level_display_prefix']
                    if field == 'level' else [],
                'producer_frontier': ('Original sender of logical S2C1C byte +2, with '
                    'area +9, scene WORD +11, ordinal WORD +7, variant WORD +5; '
                    'prove base level versus encounter/display level.' if field == 'level' else
                    'No identity-bound base-value producer qualified in this bounded path.'),
            }
        return {
            'schema': 'current-monster-base-stats-v1',
            'domain': list(FIELDS),
            'descriptor_authority': self.descriptor_authority,
            'image': {'file': str(IMAGE), 'sha256': IMAGE_SHA256, 'base': BASE,
                      'rva_equals_file_offset': True},
            'native_spans': {name: {'source_sha256': IMAGE_SHA256, 'source_offset': lo,
                                   'end_offset_exclusive': hi, 'sha256': sha(self.image[lo:hi])}
                             for name, (lo, hi) in SPANS.items()},
            'coverage': {
                'scope': 'current EnyName bank; not a universal wild-monster denominator',
                'allocated_source_records': len(self.inventory),
                'lookup_visible_records': len(visible),
                'shadowed_source_records': len(self.inventory) - len(visible),
                'loaded_groups': len(self.native.enemy_loaded_groups),
                'lookup_visible_groups': len(self.native.enemy_groups),
                'native_battle_identity_joins_checked': len(visible),
                'verified_base_stat_records': 0,
                'true_wild_monster_denominator': None,
                'all_monster_systems_enumerated': False,
                'monster_categories': dict.fromkeys(('normal', 'boss', 'elite', 'quest',
                                                      'event', 'summoned')),
            },
            'join': {'bank': 'EnyName', 'lookup_rva': 0x5a0a0, 'call_rva': 0x115e07,
                     'packet': {'opcode': 0x1c, 'size': 45, 'area_byte_offset': 9,
                                'scene_word_offset': 11, 'ordinal_word_offset': 7,
                                'variant_word_offset': 5, 'level_byte_offset': 2},
                     'qualified_variant': 'WORD +5 = 0x0400: normal bank, no special override',
                     'metadata_level_byte_offset': 7,
                     'excluded_variant_frontiers': [0x115e25, 0x115e70],
                     'field_resource_or_battle_code_join': None,
                     'server_template_join': None},
            'field_authority': authority, 'records': self.inventory,
            'outside_inventory_frontiers': [
                {'bank': 'SpecialEnyInfo', 'status': 'not_executed_or_joined_here',
                 'source_file': GAME_FILE, 'source_sha256': GAME_SHA256,
                 'decoded_sha256': GAME_DECODED_SHA256,
                 'decoded_offset': 2781781, 'end_offset_exclusive': 2781824,
                 'section_sha256': 'c3d480f60ba45441c3dfc40fe2c61e420a9e79f32570a5b640f08b82652cc4ad',
                 'declared_source_rows': 1, 'boss_record_count': None,
                 'loader_rva': 0x5a560, 'lookup_rva': 0x5a120,
                 'call_rva': 0x115e25,
                 'selector': 'low byte of packet WORD +5, after nonnull normal lookup'},
                {'bank': 'EnyName alternate coordinates', 'status': 'not_executed_here',
                 'call_rva': 0x115e70,
                 'selector': 'WORD +5 bits 0x6000 select alternate path; WORD +7 '
                             'low14 is ordinal, 0x8000 selects scene3, else 0x4000 '
                             'selects scene13, else scene2; area0',
                 'monster_category': None},
            ],
            'runtime_eligible': False,
            'remaining': 'Qualify the original 1C sender and special/alternate identity banks; '
                         'obtain identity-bound base stat sources for every unresolved field. '
                         'No global absence conclusion follows from this bounded consumer proof.',
        }


def main():
    print(json.dumps(MonsterLevelProbe().evidence(), ensure_ascii=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
