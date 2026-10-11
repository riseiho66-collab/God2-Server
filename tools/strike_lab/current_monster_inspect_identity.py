"""Current pet inspect identity/packet consumers; stdout-only research.

No wild identity join, server values, capture transition or live acceptance is
inferred. All incoming records below are explicit diagnostic operands.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_item_metadata import NativeItemMetadata
from . import recover_companion_growth as growth
from .omega_assets import decode_csvz


ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
SPANS = {
    'fb_world_case': (0x691b0, 0x691c2),
    'router_entry': (0x858b0, 0x858c9),
    'router_fb': (0x85c34, 0x85c77),
    'pet2_receive': (0xa52a0, 0xa52f5),
    'pet2_guards': (0xa5070, 0xa50ee),
    'metadata_getter': (0x59a60, 0x59a7e),
    'pet2_selection': (0xa40c0, 0xa4151),
    'type_selector': (0xb6414, 0xb6447),
    'tooltip_wrapper': (0x87690, 0x876c9),
}
# (start, stop-before-call, body offset, bit shift, mask, UI field index)
PANEL_FIELDS = (
    (0xa41d7, 0xa41fc, 4, 0, 0x3fff, 1),
    (0xa4201, 0xa4229, 4, 14, 0x7ff, 2),
    (0xa422e, 0xa4253, 12, 0, 0x3fff, 3),
    (0xa4258, 0xa4283, 12, 14, 0x7ff, 4),
    (0xa4288, 0xa42a9, 3, 0, 0xff, 5),
    (0xa4321, 0xa4343, 0x10, 0, 0xffff, 8),
    (0xa4348, 0xa436d, 0x12, 0, 0xffff, 9),
    (0xa4372, 0xa4394, 0x14, 0, 0xffff, 10),
    (0xa4399, 0xa43bb, 0x16, 0, 0xffff, 11),
    (0xa43c0, 0xa43e2, 0x24, 0, 0xffff, 13),
    (0xa43e7, 0xa440c, 0x26, 0, 0xffff, 12),
    (0xa4411, 0xa4433, 0x28, 0, 0xffff, 14),
    (0xa4438, 0xa445a, 0x2a, 0, 0xffff, 15),
    (0xa445f, 0xa4481, 0x18, 0, 0xffff, 20),
    (0xa4486, 0xa44ab, 0x1a, 0, 0xffff, 21),
    (0xa44b0, 0xa44d2, 0x1c, 0, 0xffff, 22),
    (0xa44d7, 0xa44f9, 0x1e, 0, 0xffff, 23),
    (0xa44fe, 0xa4520, 0x20, 0, 0xffff, 24),
    (0xa45c7, 0xa45e9, 8, 28, 0xf, 17),
    (0xa45ee, 0xa4613, 8, 24, 0xf, 18),
)
# ProgramMsg ID, instance WORD offset, executed interval, native DWORD read PC.
TOOLTIP_FIELDS = (
    (73, 6, 0xb787e, 0xb78ad, 0xb7898),
    (74, 4, 0xb78ee, 0xb7920, 0xb7908),
    (72, 8, 0xb7961, 0xb7993, 0xb797b),
    (75, 10, 0xb79d4, 0xb7a03, 0xb79ee),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pinned(path, expected):
    data = Path(path).read_bytes()
    if digest(data) != expected:
        raise ValueError('Current source hash mismatch: ' + str(path))
    return data


def static_evidence(image):
    if digest(image) != IMAGE_SHA:
        raise ValueError('Current native image hash mismatch')
    spans = dict(SPANS)
    spans.update({f'panel_{field:x}': (start, stop)
                  for start, stop, _, _, _, field in PANEL_FIELDS})
    spans.update({f'tooltip_{label}': (start, stop)
                  for label, _, start, stop, _ in TOOLTIP_FIELDS})
    spans.update(tooltip_level_life=(0xb77dc, 0xb783d),
                 tooltip_jump_table=(0xbc188, 0xbc1f3),
                 native_tag_array=(0x1897ec, 0x18987c),
                 ncp_category_column=(0x59816, 0x5982f),
                 ncp_category_consumer=(0xb7a41, 0xb7a9b))
    calls = ((0x691bd, 0x858b0), (0x85c72, 0xa52a0),
             (0xa52cd, 0xa5090), (0xa50bf, 0x59a60),
             (0xa413e, 0x59a60), (0x876ac, 0x59a60),
             (0x876c9, 0xb5be0))
    for pc, target in calls:
        if image[pc] != 0xe8 or pc + 5 + struct.unpack_from('<i', image, pc + 1)[0] != target:
            raise AssertionError('Native call mismatch')
    packets = {}
    for opcode, handler, length_rva, length in (
            (0xfb, 0x691b0, 0x1312, 73), (0xe3, 0x6919e, 0x12e2, 53),
            (0x3b, 0x6a029, 0x1258, 25)):
        if struct.unpack_from('<I', image, 0x6b5d4 + 4 * opcode)[0] != BASE + handler:
            raise AssertionError('World dispatch mismatch')
        if struct.unpack_from('<I', image, 0x1324 + 4 * opcode)[0] != BASE + length_rva:
            raise AssertionError('Length table mismatch')
        if image[length_rva:length_rva + 6] != b'\xb8' + struct.pack('<I', length) + b'\xc3':
            raise AssertionError('Length function mismatch')
        packets[f'{opcode:02X}'] = dict(handler_rva=handler, length=length,
                                      length_function_rva=length_rva)
    return dict(packets=packets, calls=[dict(call_rva=p, target_rva=t) for p, t in calls],
                spans={name: dict(start_rva=a, end_rva_exclusive=z,
                                 sha256=digest(image[a:z]), bytes_hex=image[a:z].hex())
                       for name, (a, z) in spans.items()})


class NativeInspect(NativeItemMetadata):
    PET_UI = 0x3800000
    MESSAGE = 0x3900000
    LABELS = 0x3a00000
    INSTANCE = 0x3b00000

    def __init__(self):
        super().__init__()
        self.evidence = static_evidence(self.image)
        self.flow_active = False
        self.vm.hook_add(self.uc.UC_HOOK_CODE, self._flow_code)
        self.vm.hook_add(self.uc.UC_HOOK_MEM_READ, self._flow_read)
        for address, size in ((self.PET_UI, 0x4000), (self.MESSAGE, 0x1000),
                              (self.LABELS, 0x2000), (self.INSTANCE, 0x1000),
                              (self.OWNER + 0x232000, 0x1000)):
            self.vm.mem_map(address, size, self.uc.UC_PROT_READ | self.uc.UC_PROT_WRITE)
        self.put32(self.OWNER + 0x232ebc, self.PET_UI)
        self.put32(self.PET_UI + 0xdc, self.OWNER)
        self.vm.mem_write(self.OWNER + 0x232e6a, b'\x01\x00')
        self.vm.mem_write(self.MESSAGE, bytes(0x1000))
        self.vm.mem_protect(self.MESSAGE, 0x1000, self.uc.UC_PROT_READ)
        self.vm.mem_protect(self.INSTANCE, 0x1000, self.uc.UC_PROT_READ)
        self.metadata = self._ncp_rows()
        self.labels = self._labels()
        self.vm.mem_protect(self.RECORD, 0x1000, self.uc.UC_PROT_READ)

    def put32(self, address, value):
        self.vm.mem_write(address, struct.pack('<I', value))

    def value(self, name):
        return self.vm.reg_read(getattr(self.x86, 'UC_X86_REG_' + name))

    def _ncp_rows(self):
        if digest(self.decoded) != growth.SOURCE_HASHES['gamedata'][1]:
            raise ValueError('Decoded gamedata changed')
        tags = []
        for index in range(36):
            at = struct.unpack_from('<I', self.image, 0x1897ec + index * 4)[0] - BASE
            tags.append(self.image[at:self.image.index(0, at)])
        selector = next(i for i, tag in enumerate(tags) if tag[:3] == b'NCP')
        if selector != 34:
            raise AssertionError('NCP native tag selector changed')
        rows = growth.parse_sections(self.decoded, ('NCP',))['NCP']['records'][:2]
        result = {}
        for ordinal, row in enumerate(rows):
            values = growth.fields(row)
            key = int(values[0])
            address = self.RECORD + 16 + ordinal * 0x200
            self.vm.mem_write(address - 16, b'\xa5' * 16 + bytes(0x18c) + b'\xa5' * 16)
            self.tokenize(row, len(values))
            self.call(0x59420, key, address, 0, selector,
                      allowed=((address, address + 0x18c),))
            if bytes(self.vm.mem_read(address - 16, 16)) != b'\xa5' * 16 or bytes(
                    self.vm.mem_read(address + 0x18c, 16)) != b'\xa5' * 16:
                raise AssertionError('Metadata canary changed')
            parsed = bytes(self.vm.mem_read(address, 0x18c))
            self.reg('ESI', self.TABLE)
            self.reg('EAX', key)
            self.reg('EDX', address)
            slot = self.TABLE + 0xb2d40 + key * 4
            self.allowed = ((slot, slot + 4),)
            try:
                self.run(0x59a20, 0x59a27)
            finally:
                self.allowed = None
            result[key] = dict(source=row, address=address, selector=selector,
                               native_record_hex=parsed.hex(), columns=list(self.columns))
        return result

    def _labels(self):
        raw = pinned(CLIENT / 'Data2/Patch/Comm/message.csvZ', growth.SOURCE_HASHES['message'][0])
        plain = decode_csvz(raw)
        if digest(plain) != growth.SOURCE_HASHES['message'][1]:
            raise ValueError('Decoded message source changed')
        rows = growth.parse_sections(plain, ('ProgramMsg',))['ProgramMsg']['records']
        labels = {}
        self.put32(self.TABLE + 0xb2c68, self.LABELS)
        self.vm.mem_write(self.TABLE + 0xb2c6c, struct.pack('<H', 575))
        for row in rows:
            fields = growth.fields(row)
            key = int(fields[0])
            if key in (72, 73, 74, 75, 84, 575):
                address = self.LABELS + 0x1000 + len(labels) * 64
                self.vm.mem_write(address, fields[1] + b'\0')
                self.put32(self.LABELS + 4 * (key - 1), address)
                labels[key] = dict(source=row, address=address)
        if len(labels) != 6:
            raise AssertionError('Missing current ProgramMsg labels')
        self.vm.mem_protect(self.LABELS, 0x2000, self.uc.UC_PROT_READ)
        return labels

    def _flow_code(self, vm, address, size, _):
        if not self.flow_active:
            return
        pc = address - BASE
        if pc in self.flow_stops:
            vm.emu_stop()
            return
        if not any(a <= pc and pc + size <= z for a, z in self.flow_ranges):
            raise AssertionError(f'Unqualified inspect instruction {pc:X}')
        self.flow_pcs.append(pc)

    def _flow_read(self, vm, access, address, size, value, _):
        if self.flow_active and not self.STACK <= address < self.STACK + 0x10000:
            self.flow_reads.append([self.value('EIP') - BASE, address, size])

    def prepare(self):
        self.vm.mem_write(self.SP - 0x1000, b'\xa5' * 0x3000)
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'EBP', 'ESI', 'EDI'):
            self.reg(name, 0xa5a5a5a5)
        self.reg('ESP', self.SP)
        self.reg('EFLAGS', 2)

    def slice(self, start, stops, ranges, writes=()):
        self.flow_ranges = ranges
        self.flow_stops = set(stops)
        self.flow_pcs, self.flow_reads = [], []
        self.allowed = writes
        self.writes.clear()
        self.flow_active = True
        try:
            self.vm.emu_start(BASE + start, 0, count=5000, timeout=1000000)
        finally:
            self.flow_active = False
            self.allowed = None
        stop = self.value('EIP') - BASE
        if stop not in self.flow_stops:
            raise AssertionError('Inspect slice did not reach declared stop')
        return dict(stop_rva=stop, pcs=list(self.flow_pcs), reads=list(self.flow_reads),
                    writes=list(self.writes), instruction_count=len(self.flow_pcs))

    def receive_fb(self, body):
        if type(body) is not bytes or len(body) != 72 or body[2] not in (42, 43, 44):
            raise ValueError('Expected 72-byte diagnostic body and slot 42..44')
        self.prepare()
        self.vm.mem_write(self.MESSAGE, b'\xfb' + body)
        self.vm.mem_write(self.PET_UI, b'\xa5' * 0xd8)
        dest = self.PET_UI + (body[2] - 42) * 72
        self.reg('EBX', self.MESSAGE)
        self.reg('EBP', (self.OWNER - 0xa7f2f6c) & 0xffffffff)
        names = ('fb_world_case', 'router_entry', 'router_fb', 'pet2_receive',
                 'pet2_guards', 'metadata_getter')
        trace = self.slice(0x691b0, (0xa52f5, 0xa5390, 0xa50d7),
                           [SPANS[n] for n in names], ((dest, dest + 72),))
        expected = bytearray(b'\xa5' * 0xd8)
        if trace['stop_rva'] == 0xa52f5:
            offset = dest - self.PET_UI
            expected[offset:offset + 72] = body
        if bytes(self.vm.mem_read(self.PET_UI, 0xd8)) != expected:
            raise AssertionError('Pet2 row/canary mismatch')
        return dict(body_hex=body.hex(), record_address=dest, trace=trace)

    def select_fb(self, slot):
        self.prepare()
        self.vm.mem_write(self.PET_UI + 0xd8, bytes((slot,)))
        self.reg('ECX', self.PET_UI)
        trace = self.slice(0xa40c0, (0xa4151, 0xa4db9, 0xa50d7),
                           [SPANS[n] for n in ('pet2_selection', 'pet2_guards', 'metadata_getter')])
        return dict(record_address=self.value('EBX'), metadata_address=self.value('ESI'), trace=trace)

    def receive_fb_inactive(self, body):
        """Execute the entire receiver with all three dependent UI handles inactive.

        Preserve existing rows across calls; do not substitute for live/open UI.
        """
        if type(body) is not bytes or len(body) != 72 or body[2] not in (42, 43, 44):
            raise ValueError('Expected 72-byte diagnostic body and slot 42..44')
        self.prepare()
        self.vm.mem_write(self.MESSAGE, body)
        handles = (0x232dc8, 0x232e50, 0x232e6a)
        saved = [bytes(self.vm.mem_read(self.OWNER + offset, 2)) for offset in handles]
        before = bytes(self.vm.mem_read(self.PET_UI, 0xe0))
        # Code hook stops before this RX address; never execute a stack sentinel.
        return_rva = 0x1000
        self.vm.mem_write(self.SP, struct.pack('<2I', BASE + return_rva, self.MESSAGE))
        self.reg('ECX', self.PET_UI)
        dest = self.PET_UI + (body[2] - 42) * 72
        try:
            for offset in handles:
                self.vm.mem_write(self.OWNER + offset, b'\xff\xff')
            trace = self.slice(
                0xa52a0, (return_rva,),
                ((0xa52a0, 0xa5395), SPANS['pet2_guards'],
                 SPANS['metadata_getter'], (0xad080, 0xad09b), (0xad547, 0xad54f)),
                ((dest, dest + 72),))
        finally:
            for offset, value in zip(handles, saved):
                self.vm.mem_write(self.OWNER + offset, value)
        if self.value('ESP') != self.SP + 8:
            raise AssertionError('Full FB receiver stack imbalance')
        for register in ('EBX', 'ESI', 'EDI', 'EBP'):
            if self.value(register) != 0xa5a5a5a5:
                raise AssertionError('Full FB receiver clobbered callee-saved register')
        expected = bytearray(before)
        if 0xa52f3 in trace['pcs']:
            offset = dest - self.PET_UI
            expected[offset:offset + 72] = body
        if bytes(self.vm.mem_read(self.PET_UI, 0xe0)) != expected:
            raise AssertionError('Full FB receiver altered unrelated storage')
        return dict(record_address=dest, trace=trace)

    def panel_fields(self, record):
        results = []
        for start, stop, offset, shift, mask, field in PANEL_FIELDS:
            self.prepare()
            self.reg('EBP', self.PET_UI)
            self.reg('EBX', record)
            trace = self.slice(start, (stop,), ((start, stop),))
            args = list(struct.unpack('<5I', self.vm.mem_read(self.value('ESP'), 20)))
            results.append(dict(body_offset=offset, shift=shift, mask=mask,
                                ui_field=field, arguments=args, trace=trace))
        return results

    def tooltip(self, record):
        if type(record) is not bytes or len(record) != 20:
            raise ValueError('Expected exact 20-byte diagnostic instance')
        self.vm.mem_write(self.INSTANCE, record)
        self.prepare()
        self.vm.mem_write(self.SP + 4, struct.pack('<4I', 0x1a6, 0x1b5, self.INSTANCE, 0))
        self.reg('ECX', self.PET_UI)
        wrapper = self.slice(0x87690, (0x876c9,),
                             (SPANS['tooltip_wrapper'], SPANS['metadata_getter']))
        args = list(struct.unpack('<6I', self.vm.mem_read(self.value('ESP'), 24)))
        self.prepare()
        self.put32(self.SP + 0x11ac, self.INSTANCE)
        self.reg('EDX', 0)  # Explicit zero remainder for preceding string copy.
        branch = self.slice(0xb6414, (0xb77dc, 0xb6f0e, 0xba850), (SPANS['type_selector'],))
        results = []
        if branch['stop_rva'] == 0xb77dc:
            self.prepare()
            self.reg('EBP', self.OWNER)
            self.put32(self.SP + 0x11ac, self.INSTANCE)
            level = self.slice(0xb77dc, (0xb783d,), ((0xb77dc, 0xb783d),))
            level_args = list(struct.unpack('<6I', self.vm.mem_read(self.value('ESP'), 24)))
            results.append(dict(labels=[84, 575], arguments=level_args, trace=level))
            for label, offset, start, stop, read_pc in TOOLTIP_FIELDS:
                self.prepare()
                self.reg('EAX', self.TABLE)
                self.reg('EBX', self.INSTANCE)
                trace = self.slice(start, (stop,), ((start, stop),))
                arguments = list(struct.unpack('<4I', self.vm.mem_read(self.value('ESP'), 16)))
                results.append(dict(label=label, instance_word_offset=offset,
                                    opcode_3b_word_offset=5 + offset,
                                    native_read_pc=read_pc, arguments=arguments, trace=trace))
        return dict(record_hex=record.hex(), wrapper_arguments=args, wrapper_trace=wrapper,
                    branch_trace=branch, fields=results)


def diagnostic_body(key=28001, slot=42, seed=1):
    body = bytearray((i * 17 + seed) & 255 for i in range(72))
    struct.pack_into('<H', body, 0, key)
    body[2] = slot
    return bytes(body)


def report():
    native = NativeInspect()
    body = diagnostic_body()
    received = native.receive_fb(body)
    selected = native.select_fb(42)
    instance = struct.pack('<I4HII', 28001 | (34 << 16), 0x1234, 0x8000,
                           0xffff, 7, 0x05123456, 0xc5817fff)
    return dict(
        image_sha256=IMAGE_SHA, base=BASE, rva_equals_file_offset=True,
        source_hashes={name: dict(raw_sha256=growth.SOURCE_HASHES[name][0],
                                 decoded_sha256=growth.SOURCE_HASHES[name][1])
                       for name in ('gamedata', 'message')},
        native_evidence=native.evidence, metadata=native.metadata, labels=native.labels,
        fb_receive=received, fb_selection=selected,
        fb_numeric_consumers=native.panel_fields(selected['record_address']),
        tooltip=native.tooltip(instance),
        operands='Synthetic packets; actual native source-row parsing and consumer execution.',
        adapters=['Existing CRT decimal adapter for source tokenization only.',
                  'Allocated metadata/RomMaps storage and original index-store slice.',
                  'Six source-backed ProgramMsg pointers; no full message loader.',
                  'Independent display slices; no renderer or formatter executed.'],
        wildmonsterjoin_proven=False, original_wild_numeric_values_recovered=0,
        wild_identity_join=None, runtime_eligible=False,
        missing=['Native mapping from wild composite identity+variant+version to received pet instance.',
                 'Original server FB/3B sender and capture/recruit transaction continuity.',
                 'Proof whether captured attributes preserve, regenerate or transform wild values.',
                 'Active-UI refresh paths and remaining packed/skill semantics; '
                 'control labels are separately proven by current_pet2_stat_labels.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.summary:
        result = dict(image_sha256=result['image_sha256'], opcode='FB', logical_length=73,
                      native_metadata_keys=list(result['metadata']),
                      native_receive_stop=result['fb_receive']['trace']['stop_rva'],
                      numeric_consumer_fields=len(result['fb_numeric_consumers']),
                      tooltip_labelled_fields=6, wildmonsterjoin_proven=False,
                      original_wild_numeric_values_recovered=0, runtime_eligible=False)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))


if __name__ == '__main__':
    main()
