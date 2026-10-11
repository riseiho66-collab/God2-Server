"""Bounded S2C83/action7 resource-selector exclusion, not monster stat recovery.

No server/client process, renderer, database or source mutation. Native execution
is restricted to the pure original 52DCC0 helper; its callers/CSV loader are static.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
RAW_SHA = '9c8a1977355e096f72924a36ccf61dfea9940af75b4816d0d56727e63a7acf27'
PLAIN_SHA = '479861b2034da6f27d5bf9e0f7f38facf19ee6b71cee7eaf01d7a0fd4e8fec97'
SPANS = {
    'selector': (0x12dcc0, 0x12dd30),
    'resource_loader': (0x4fc50, 0x4fda5),
    'resource_lookup': (0x4fdd0, 0x4fdfd),
    'loader_callers': (0x110ce9, 0x110d53),
    'action7': (0x116ecd, 0x1170ce),
    'subtype2': (0x117500, 0x117539),
    'subtype2_hide': (0x126060, 0x12611d),
    'subtype2_reset': (0x1202d0, 0x1202ff),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit():
    import pefile
    image = IMAGE.read_bytes()
    require(sha(image) == IMAGE_SHA, 'Pinned native image identity mismatch')
    raw_pe = (CLIENT / 'God2.exe').read_bytes()
    pe = pefile.PE(data=raw_pe)
    spans = {}
    for name, (lo, hi) in SPANS.items():
        require(pe.get_data(lo, hi - lo) == image[lo:hi], 'Current PE code mismatch: ' + name)
        spans[name] = {'rva_start': hex(lo), 'rva_end_exclusive': hex(hi),
                       'sha256': sha(image[lo:hi]), 'pe_match': True}
    raw = (CLIENT / 'Data2/Patch/GodEft.csvZ').read_bytes()
    require(sha(raw) == RAW_SHA, 'GodEft source identity mismatch')
    plain = decode_csvz(raw, limit=4096)
    require(sha(plain) == PLAIN_SHA, 'GodEft decoded identity mismatch')
    require(image[0x19c5a8:0x19c5b3] == b'GodEft.csv\0', 'Native filename identity mismatch')
    rows = []
    offset = 0
    for number, line in enumerate(plain.splitlines(keepends=True), 1):
        if number >= 27:
            cells = line.rstrip(b'\r\n').split(b',')
            require(len(cells) == 4, 'Unexpected GodEft row shape')
            rows.append({'line': number, 'offset': offset, 'sha256_with_line_ending': sha(line),
                         'key': int(cells[0]), 'resource_id': int(cells[1]),
                         'resource_path': cells[2].decode('ascii'), 'raw_hex': line.hex()})
        offset += len(line)
    require(len(rows) == 34 and [r['key'] for r in rows] == list(range(1, 35)), 'GodEft row domain mismatch')
    require([r['resource_id'] for r in rows] == list(range(5601, 5635)), 'GodEft ROM ID domain mismatch')
    return image, {'image_sha256': IMAGE_SHA, 'current_exe_sha256': sha(raw_pe), 'code_spans': spans,
                   'source': {'path': 'Data2/Patch/GodEft.csvZ', 'raw_sha256': RAW_SHA,
                              'decoded_sha256': PLAIN_SHA, 'rows': rows},
                   'wild_attack_defense_values_recovered': 0, 'runtime_eligible': False}


def native_selector(image):
    sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP
    base, stack, output, stop = 0x400000, 0x3000000, 0x3001000, 0x3002000
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(base, (len(image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
    vm.mem_write(base, image)
    vm.mem_map(stack, 0x3000)
    destinations = tuple(output + 8 * i for i in range(4))
    visits = set()

    def code(machine, address, size, data):
        require(base + 0x12dcc0 <= address and address + size <= base + 0x12dd30,
                'Unqualified native selector instruction')
        visits.add(address - base)

    def write(machine, access, address, size, value, data):
        require(stack <= address and address + size <= stack + 0x1000 or
                (address in destinations and size == 1), 'Unexpected selector write')

    vm.hook_add(UC_HOOK_CODE, code)
    vm.hook_add(UC_HOOK_MEM_WRITE, write)
    digest = hashlib.sha256()
    count = 0
    # All low10 selectors, both signs of the 16-bit packet WORD and three
    # distinct unconsumed upper halves. These inputs are synthetic probes.
    for high_word in (0, 0x12340000, 0xffff0000):
        for sign in (0, 0x8000):
            for low in range(1024):
                word = sign | low
                argument = high_word | word
                first, second = (word >> 9) & 1, (word >> 7) & 3
                if first:
                    third, fourth = (word & 15) + 16, (word >> 4) & 7
                elif word > 100:
                    first, third, fourth = 1, word & 127, 1
                else:
                    third, fourth = word & 127, 0
                expected = bytes((first, second, third, fourth))
                vm.mem_write(output, b'\xa5' * 32)
                vm.mem_write(stack + 0x800, struct.pack('<6I', stop, argument, *destinations))
                vm.reg_write(UC_X86_REG_ESP, stack + 0x800)
                vm.emu_start(base + 0x12dcc0, stop, timeout=1000000, count=128)
                require(vm.reg_read(UC_X86_REG_EIP) == stop and
                        vm.reg_read(UC_X86_REG_ESP) == stack + 0x818, 'Native selector budget/return mismatch')
                actual = bytes(vm.mem_read(address, 1)[0] for address in destinations)
                require(actual == expected, 'Native selector output mismatch')
                complete = bytearray(b'\xa5' * 32)
                for index, value in enumerate(expected):
                    complete[index * 8] = value
                require(bytes(vm.mem_read(output, 32)) == complete, 'Selector output guard changed')
                digest.update(struct.pack('<I', argument) + actual)
                count += 1
    require(bytes(vm.mem_read(base, len(image))) == image, 'Native image mutated')
    return {'synthetic_vectors': count, 'result_sha256': digest.hexdigest(),
            'visited_rvas': [hex(rva) for rva in sorted(visits)],
            'instructions_per_case_cap': 128, 'timeout_microseconds': 1000000,
            'native_entry': '0x12dcc0', 'native_end_exclusive': '0x12dd30'}


if __name__ == '__main__':
    image, report = audit()
    report['native_selector'] = native_selector(image)
    print(json.dumps(report, ensure_ascii=True, indent=2))
