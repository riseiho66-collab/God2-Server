"""Full current Mission_data parser qualification, not quest progression rules."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import pefile
from .omega_assets import decode_csvz
from .recover_quests import parse_table
from .recover_companion_growth import _NativeRows

ROOT = Path(__file__).resolve().parents[2]
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
SOURCE = 'Data2/Patch/Comm/Mission_data.csvZ'
SOURCE_SHA = '659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716'
DECODED_SHA = 'f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class MissionNative(_NativeRows):
    HEAP, HEAP_SIZE, FILE = 0x3500000, 0x200000, 0x12340000

    def __init__(self, image, lines):
        super().__init__(image)
        self.lines, self.consumed = list(lines), 0
        self.next_allocation = self.HEAP
        self.allocations, self.accessors = [], Counter()
        self.vm.mem_map(self.HEAP, self.HEAP_SIZE)
        self.vm.mem_write(self.TABLE+4, struct.pack('<I', self.FILE))
        self.vm.mem_write(self.TABLE+8, struct.pack('<H', 4))
        for address in (0x547e23, 0x547973, 0x547a95):
            self.vm.hook_add(self.uc.UC_HOOK_CODE, self.crt, begin=address, end=address)
        for address in (0x451ae0, 0x451b50):
            self.vm.hook_add(self.uc.UC_HOOK_CODE, self.observe, begin=address, end=address)

    def observe(self, vm, address, size, context):
        sp = vm.reg_read(self.x86.UC_X86_REG_ESP)
        column = struct.unpack('<I', vm.mem_read(sp+4, 4))[0]
        kind = 'definition' if self.lines[self.consumed-1].split(b',', 1)[0] else 'description'
        self.accessors[f'{kind}:{address:08x}:column{column}'] += 1

    def crt(self, vm, address, size, context):
        sp = vm.reg_read(self.x86.UC_X86_REG_ESP)
        ret, a, b, c = struct.unpack('<4I', vm.mem_read(sp, 16))
        if address in (0x547e23, 0x547973):
            require(ret in (0x4584c0, 0x458587, 0x4585e2), 'Unqualified allocator caller')
            amount = a*b if address == 0x547e23 else a
            require(0 < amount <= self.HEAP_SIZE and self.next_allocation+amount <= self.HEAP+self.HEAP_SIZE,
                    'Native allocation exceeds bounded heap')
            result = self.next_allocation
            self.next_allocation += (amount+15) & ~15
            vm.mem_write(result, bytes(amount) if address == 0x547e23 else b'\xa5'*amount)
            self.allocations.append({'caller': hex(ret), 'address': result, 'size': amount,
                                     'kind': 'calloc' if address == 0x547e23 else 'malloc'})
        else:
            require(ret == 0x451ab0 and b == 4096 and c == self.FILE, 'Unqualified fgets caller')
            require(self.STACK <= a and a+b <= self.STACK+0x10000, 'fgets outside stack')
            result = 0
            if self.consumed < len(self.lines):
                raw = self.lines[self.consumed].replace(b'\r\n', b'\n')
                require(raw.endswith(b'\n') and len(raw)<b and b'\0' not in raw, 'Source text bounds')
                vm.mem_write(a, raw+b'\0')
                self.consumed += 1
                result = a
        vm.reg_write(self.x86.UC_X86_REG_EAX, result)
        vm.reg_write(self.x86.UC_X86_REG_ESP, sp+4)
        vm.reg_write(self.x86.UC_X86_REG_EIP, ret)

    def parse(self, count):
        self.reg('ECX', self.TABLE)
        self.reg('ESP', self.SP)
        self.vm.mem_write(self.SP, struct.pack('<II', self.RETURN, count))
        self.vm.emu_start(0x4584a0, self.RETURN, count=20000000, timeout=20000000)
        require(self.vm.reg_read(self.x86.UC_X86_REG_EIP) == self.RETURN, 'Full parser did not return')
        require(self.vm.reg_read(self.x86.UC_X86_REG_ESP) == self.SP+8, 'Parser stack imbalance')
        require(self.vm.reg_read(self.x86.UC_X86_REG_EAX) == 1, 'Parser rejected source')
        require(self.consumed == len(self.lines), 'Parser left unread rows')
        highwater, table = struct.unpack('<II', self.vm.mem_read(self.TABLE+0xd2ac0, 8))
        require(highwater == count and table == self.HEAP, 'Parser table/count mismatch')
        result = []
        for index in range(count):
            raw = bytes(self.vm.mem_read(table+40*index, 40))
            n = struct.unpack_from('<h', raw)[0]
            pointer = struct.unpack_from('<I', raw, 36)[0]
            texts = []
            for j in range(n):
                address = struct.unpack('<I', self.vm.mem_read(pointer+j*4, 4))[0]
                if not address:
                    texts.append(None)
                    continue
                allocation = next(r for r in self.allocations if r['address'] == address)
                content = bytes(self.vm.mem_read(address, allocation['size']))
                require(content[-1:] == b'\0', 'Unterminated source string')
                texts.append(content[:-1].hex())
            result.append({'mission_id': index+1, 'description_count': n,
                           'name_hex': raw[2:36].split(b'\0', 1)[0].hex(),
                           'native_record40_hex': raw.hex(), 'description_hex': texts})
        return result


def audit(client):
    executable = (client/'God2.exe').read_bytes()
    require(sha(executable) == CLIENT_SHA, 'Current client changed')
    image = pefile.PE(data=executable).get_memory_mapped_image()
    packed = (client/SOURCE).read_bytes()
    require(sha(packed) == SOURCE_SHA, 'Mission_data source changed')
    plain = decode_csvz(packed)
    require(sha(plain) == DECODED_SHA, 'Mission_data decoded source changed')
    source = parse_table('missions', plain)
    lines = plain.splitlines(keepends=True)[3:]
    native = MissionNative(image, lines)
    rows = native.parse(418)
    cursor = 0
    truncated = []
    for row in rows:
        header = lines[cursor].rstrip(b'\r\n').split(b',')
        require(int(header[0]) == row['mission_id'] and int(header[2]) == row['description_count'], 'Header mismatch')
        require(row['name_hex'] == header[1][:33].hex(), 'Name mismatch')
        row['source_line'] = cursor+4
        row['raw_definition_hex'] = lines[cursor].hex()
        raw40 = bytes.fromhex(row['native_record40_hex'])
        expected = struct.pack('<H', int(header[2])) + (header[1][:33]+b'\0').ljust(34, b'\0')
        require(raw40[:36] == expected, 'Unaccounted native record scalar/name bytes')
        cursor += 1
        for description_index, text in enumerate(row['description_hex']):
            fields = lines[cursor].rstrip(b'\r\n').split(b',')
            require(text == fields[3][:379].hex(), 'Full parser text differs from native token cap/read order')
            if len(fields[3]) > 379:
                parsed = bytes.fromhex(text)
                try:
                    parsed.decode('cp950')
                    cp950_complete = True
                except UnicodeDecodeError:
                    cp950_complete = False
                truncated.append({'mission_id': row['mission_id'], 'description_index': description_index,
                                  'source_line': cursor+4, 'source_bytes': len(fields[3]), 'native_bytes': len(parsed),
                                  'raw_source_hex': fields[3].hex(), 'raw_source_sha256': sha(fields[3]),
                                  'native_hex': text, 'native_sha256': sha(parsed),
                                  'native_cp950_decodable': cp950_complete})
            cursor += 1
    require(cursor == len(lines), 'Source accounting mismatch')
    # Diagnostics mutate only isolated text inputs from the first actual mission.
    # Native validates the STEP range but stores by physical read order.
    altered = list(lines[:3])
    altered[1] = altered[1].replace(b',,1,', b',,2,', 1)
    altered[2] = altered[2].replace(b',,2,', b',,1,', 1)
    reordered = MissionNative(image, altered).parse(1)[0]
    require(reordered['description_hex'] == rows[0]['description_hex'], 'STEP changed physical text order')
    invalid = list(lines[:3])
    invalid[1] = invalid[1].replace(b',,1,', b',,0,', 1)
    skipped = MissionNative(image, invalid).parse(1)[0]
    require(skipped['description_hex'] == [None, rows[0]['description_hex'][1]], 'Invalid STEP did not leave zero pointer hole')
    spans = {'mission_loader': (0x584a0, 0x58680), 'row_reader_tokenizer': (0x51a90, 0x51cd2),
             'journal_click': (0xc9260, 0xc9390), 'journal_display': (0xc9550, 0xc9610),
             'journal_writer': (0xc9670, 0xc9770)}
    return {'schema': 'god2-current-quest-rule-frontier-v1', 'client_sha256': CLIENT_SHA,
            'source_sha256': SOURCE_SHA, 'decoded_sha256': DECODED_SHA,
            'source_header_hex': plain.splitlines()[1].hex(), 'definitions': rows,
            'definition_count': len(rows), 'description_count': sum(r['description_count'] for r in rows),
            'source_rows_consumed': native.consumed, 'accessor_calls': dict(native.accessors),
            'native_description_truncations': truncated,
            'allocations': native.allocations, 'native_heap_bytes': native.next_allocation-native.HEAP,
            'spans': {k: {'rva_start': hex(a), 'rva_end_exclusive': hex(b), 'sha256': sha(image[a:b])}
                      for k,(a,b) in spans.items()},
            'diagnostics': {'swapped_step_labels_preserve_read_order': reordered,
                            'step_zero_leaves_pointer_hole': skipped, 'authority': 'isolated synthetic input mutations'},
            'execution_scope': 'Full original 4584A0,451A90,451BE0,field accessors and inline copies. CRT allocation/fgets/decimal adapters only. No journal UI/progression/reward execution.',
            'new_executable_quest_rules': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=ROOT.parent/'God2')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.resolve().is_relative_to(args.client.resolve()), 'Output cannot modify client')
    result = audit(args.client)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'definitions': result['definition_count'],
                      'descriptions': result['description_count'], 'output_sha256': sha(args.output.read_bytes())}))


if __name__ == '__main__':
    main()
