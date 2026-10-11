"""Execute a newly audited selected-skill reader to its original renderer boundary.

The native tables select animation actions. No game, DB or combat formula runs.
"""
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import struct
import sys

from .current_skill_identity import decode_definitions, SOURCE, SOURCE_SHA256, IMAGE_SHA256
from .omega_assets import decode_csvz
from .recover_combat_skills import parse_skills

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def run():
    import pefile
    raw = (CLIENT / SOURCE).read_bytes()
    require(sha(raw) == SOURCE_SHA256, 'Skill source identity mismatch')
    definitions = decode_definitions(raw)
    require(len(definitions) == 448, 'Skill definition domain mismatch')
    game_source = (CLIENT / 'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    require(sha(game_source) == '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731',
            'Skill-book text identity mismatch')
    # Existing current-only parser; no retired archive/catalog entry points run.
    books = parse_skills(decode_csvz(game_source))['definitions']
    literals = []
    for book in books:
        for column in range(7, 13):
            value = book['fields'][column]
            if re.search('[倍%％]|百分|固定', value):
                literals.append({'item_id': book['item_id'], 'name': book['name'],
                    'source_line': book['source_line'], 'decoded_offset': book['decoded_offset'],
                    'source_record_sha256': book['source_record_sha256'], 'column': column,
                    'literal': value, 'authority': 'NATIVE_CLIENT_TEXT_NOT_EXECUTABLE_SERVER_FORMULA'})
    require(len(books) == 381 and len(literals) == 24, 'Skill description literal coverage changed')
    native = IMAGE.read_bytes()
    require(sha(native) == IMAGE_SHA256, 'Native image identity mismatch')
    executable = (CLIENT / 'God2.exe').read_bytes()
    pe = pefile.PE(data=executable)
    spans = {}
    for name, lo, hi in [('caller', 0x1259c2, 0x1259f4), ('reader', 0x1297d0, 0x129861),
                         ('side_tables', 0x19ced0, 0x19cf80)]:
        require(pe.get_data(lo, hi-lo) == native[lo:hi], 'Current PE span mismatch: ' + name)
        spans[name] = {'rva_start': hex(lo), 'rva_end_exclusive': hex(hi), 'sha256': sha(native[lo:hi])}
    sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EIP
    base, context, actor, definition, stack = 0x400000, 0x4000000, 0x5000000, 0x6000000, 0x7000000
    stop, render_owner = stack + 0xf00, 0x8000000
    selector = context + 0xa7fbc6c
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(base, (len(native)+4095)&~4095, UC_PROT_READ | UC_PROT_EXEC)
    vm.mem_write(base, native)
    for page in (context, actor, definition, stack, selector & ~4095):
        vm.mem_map(page, 4096)
    vm.mem_write(context + 12, struct.pack('<I', render_owner))
    vm.mem_write(selector, struct.pack('<h', -7))
    vm.mem_write(actor, b'\xa5' * 4096)
    vm.mem_write(actor + 0xec4, struct.pack('<I', definition))
    vm.mem_write(actor + 0x10, struct.pack('<H', 1))
    reads = []

    def code(machine, address, size, data):
        if address == base + 0x1bf30:
            machine.emu_stop()
            return
        require(base + 0x1297d0 <= address and address+size <= base + 0x129861,
                'Unexpected selected-skill instruction')

    def write(machine, access, address, size, value, data):
        require(stack <= address and address+size <= stack+4096, 'Selected-skill reader changed nonstack memory')

    def read(machine, access, address, size, value, data):
        if definition <= address < definition + 110:
            reads.append((machine.reg_read(UC_X86_REG_EIP)-base, address-definition, size))

    vm.hook_add(UC_HOOK_CODE, code)
    vm.hook_add(UC_HOOK_MEM_WRITE, write)
    vm.hook_add(UC_HOOK_MEM_READ, read)
    entries, cases = [], 0
    for (kind, identity), record in definitions.items():
        for side in (0, 1):
            # A second run mutates every nonidentity definition byte, including
            # MP42, unknown46, and effect-presence4C..64. These are counterfactuals.
            for mutation in (False, True):
                source = record.raw if not mutation else record.raw[:2] + b'\xff' * 108
                vm.mem_write(definition, source)
                vm.mem_write(actor + 0x234, bytes((side << 7,)))
                before = bytes(vm.mem_read(actor, 4096))
                vm.mem_write(stack + 0x800, struct.pack('<II', stop, actor))
                vm.reg_write(UC_X86_REG_ESP, stack + 0x800)
                vm.reg_write(UC_X86_REG_ECX, context)
                reads.clear()
                vm.emu_start(base+0x1297d0, stop, count=128)
                end = vm.reg_read(UC_X86_REG_EIP)
                if kind == 2:
                    require(end == base+0x1bf30, 'Skill renderer boundary not reached')
                    args = struct.unpack('<5I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 20))
                    action = native[(0x19ced0 if side == 0 else 0x19cf28) + identity - 1]
                    require(args == (base+0x12985c, render_owner+0x2a0, 0xfffffff9, action, 0),
                            'Native renderer argument mismatch')
                    require(reads == [(0x1297e0, 1, 1), (0x1297e6, 0, 1)], 'Unexpected skill numeric field read')
                    if not mutation:
                        entries.append({'kind': kind, 'id': identity, 'side': side, 'action': action,
                                        'source_offset': record.source_offset, 'record_sha256': sha(record.raw)})
                else:
                    require(end == stop and vm.reg_read(UC_X86_REG_ESP) == stack+0x808,
                            'Non-kind2 did not return unchanged')
                    require(reads == [(0x1297e0, 1, 1)], 'Non-kind2 read unqualified fields')
                require(bytes(vm.mem_read(actor, 4096)) == before, 'Actor state changed')
                require(bytes(vm.mem_read(definition, 110)) == source, 'Skill definition changed')
                cases += 1
    require(bytes(vm.mem_read(base, len(native))) == native, 'Native image changed')
    return {'image_sha256': IMAGE_SHA256, 'current_exe_sha256': sha(executable),
            'source_sha256': SOURCE_SHA256, 'code_spans': spans,
            'native_cases': cases, 'kind2_side_mappings': entries,
            'skill_book_source_sha256': sha(game_source), 'description_literal_claims': literals,
            'word46_unclassified_distribution': dict(sorted(Counter(
                int.from_bytes(value.raw[0x46:0x48], 'little') for value in definitions.values()).items())),
            'server_formula_recovered': False,
            'scope': '1297D0 native reader and static1259EF caller; stop before1BF30 renderer'}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, ensure_ascii=True))
