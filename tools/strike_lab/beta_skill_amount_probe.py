"""Beta native action-prefix execution, stopping before presentation work."""
import hashlib
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as reg

from .beta_client_compare import skill_rows
from .beta_packet_probe import ROOT, IMAGE, SHA

BASE, MANAGER, SOURCE, TARGET = 0x400000, 0x3000000, 0x9000000, 0x9002000
PACKET, STACK = 0xa000000, 0xb000000
SP, RETURN = STACK + 0x8000, STACK + 0xff00
SKILL = Path('C:/Users/risei/Desktop/god2-test/Data2/Fight/Spg/cbspec2.bin')


class AmountProbe:
    def __init__(self):
        image = IMAGE.read_bytes()
        if hashlib.sha256(image).hexdigest() != SHA:
            raise ValueError('Unexpected beta image')
        self.source = SKILL.read_bytes()
        if hashlib.sha256(self.source).hexdigest() != 'df6c7ab8ad6a83011a4055e7d9572240e0a366792a09158dd0d9cc56726c45f8':
            raise ValueError('Unexpected beta skill source')
        self.rows = skill_rows(self.source, 108)
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(image) + 4095) & ~4095)
        self.vm.mem_write(BASE, image)
        for address, size in ((MANAGER, 0x5500000), (SOURCE, 0x4000),
                              (PACKET, 4096), (STACK, 65536)):
            self.vm.mem_map(address, size)
        self.vm.mem_write(MANAGER + 0x53e63a8, self.source[4:])
        self.vm.hook_add(UC_HOOK_CODE, self.hook)
        self.reached = False
        self.format_calls = None
        self.mp_mode = False

    def hook(self, vm, address, size, unused):
        if self.mp_mode:
            if BASE + 0x84500 <= address and address + size <= BASE + 0x845a0:
                return
            raise AssertionError(f'Unexpected MP predicate branch {address:x}')
        if self.format_calls is not None:
            if address == BASE + 0x102b12:
                sp = vm.reg_read(reg.UC_X86_REG_ESP)
                ret, dest, fmt, previous, amount = struct.unpack('<5I', vm.mem_read(sp, 20))
                if dest != PACKET + 512 or previous != dest:
                    raise AssertionError('Unexpected original format ABI')
                label = bytearray()
                for index in range(80):
                    value = bytes(vm.mem_read(fmt + index, 1))
                    if value == b'\0':
                        break
                    label.extend(value)
                else:
                    raise AssertionError('Unbounded format string')
                self.format_calls.append({'format_rva': hex(fmt - BASE),
                                          'format_hex': label.hex(),
                                          'amount': struct.unpack('<i', struct.pack('<I', amount))[0]})
                vm.reg_write(reg.UC_X86_REG_ESP, sp + 4)
                vm.reg_write(reg.UC_X86_REG_EAX, 0)
                vm.reg_write(reg.UC_X86_REG_EIP, ret)
                return
            if BASE + 0xd6be0 <= address and address + size <= BASE + 0xd6d25:
                return
            raise AssertionError(f'Unexpected formatter branch {address:x}')
        if address == BASE + 0xdba61:
            self.reached = True
            vm.emu_stop()
            return
        ranges = ((0xdcd30, 0xdd07c), (0xcf200, 0xcf28a), (0xdccc0, 0xdccf8),
                  (0xdb200, 0xdb480), (0xdb940, 0xdba61), (0xd2f80, 0xd2f96))
        if not any(BASE + lo <= address and address + size <= BASE + hi for lo, hi in ranges):
            raise AssertionError(f'Unexpected native prefix instruction: {address - BASE:x}')

    def evaluate(self, key, amount, side=0, slot=0):
        if key not in self.rows or not 0 <= amount <= 65535 or side not in (0, 1) or not 0 <= slot < 14:
            raise ValueError('Diagnostic input bounds')
        vm = self.vm
        vm.mem_write(SOURCE, bytes(0x4000))
        vm.mem_write(MANAGER + 0x38, bytes(2 * 14 * 6 * 4))
        target_side = 1 - side
        vm.mem_write(MANAGER + 0x38 + (side * 14 + slot) * 24, struct.pack('<I', SOURCE))
        vm.mem_write(MANAGER + 0x38 + (target_side * 14 + slot) * 24, struct.pack('<I', TARGET))
        offset, raw = self.rows[key]
        definition = MANAGER + 0x53e63a8 + offset - 4
        vm.mem_write(SOURCE + 0xdcc, struct.pack('<I', definition))
        body = bytearray(16)
        body[0], body[1] = side * 14 + slot, target_side * 14 + slot
        body[6], body[8], body[9] = 3, key[1], key[0]
        struct.pack_into('<H', body, 14, amount)
        vm.mem_write(PACKET, b'\x80' + bytes(body))
        vm.mem_write(SP, struct.pack('<6I', RETURN, PACKET + 1, side, slot, target_side, slot))
        vm.reg_write(reg.UC_X86_REG_ESP, SP)
        vm.reg_write(reg.UC_X86_REG_ECX, MANAGER)
        vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
        self.reached = False
        vm.emu_start(BASE + 0xdcd30, RETURN, count=10000)
        if not self.reached:
            raise AssertionError('Did not reach the original amount store')
        actual = struct.unpack('<H', vm.mem_read(SOURCE + 0x26c, 2))[0]
        pointer = struct.unpack('<I', vm.mem_read(SOURCE + 0xe98, 4))[0]
        if actual != amount or pointer != definition:
            raise AssertionError('Native amount or skill binding differed')
        if bytes(vm.mem_read(definition, 108)) != raw:
            raise AssertionError('Native skill definition was modified')
        return {'bank': key[0], 'id': key[1], 'side': side, 'slot': slot,
                'logical_marker_word': amount, 'stored_word': actual,
                'signed_interpretation': struct.unpack('<h', struct.pack('<H', actual))[0]}

    def format_gate(self, field, gate, amount):
        if field not in (0x5e, 0x60, 0x62, 0x64) or not 0 <= gate <= 65535 or not -32768 <= amount <= 32767:
            raise ValueError('Formatter diagnostic bounds')
        raw = bytearray(108)
        struct.pack_into('<H', raw, field, gate)
        vm = self.vm
        vm.mem_write(PACKET + 128, bytes(raw))
        vm.mem_write(SP, struct.pack('<4I', RETURN, PACKET + 512, PACKET + 128, amount & 0xffffffff))
        vm.reg_write(reg.UC_X86_REG_ESP, SP)
        vm.reg_write(reg.UC_X86_REG_ECX, MANAGER)
        self.format_calls = []
        try:
            vm.emu_start(BASE + 0xd6be0, RETURN, count=1000)
            calls = self.format_calls[:]
            if vm.reg_read(reg.UC_X86_REG_EIP) != RETURN or len(calls) != int(gate != 0):
                raise AssertionError('Unexpected native format gate result')
            if calls and calls[0]['amount'] != amount:
                raise AssertionError('Native formatter changed the supplied amount')
            return {'field': hex(field), 'gate': gate, 'input_amount': amount, 'calls': calls}
        finally:
            self.format_calls = None

    def mp_gate(self, key, mp, mode):
        if key not in self.rows or not 0 <= mp <= 0xffffffff or mode not in ('selected', 'indexed'):
            raise ValueError('MP diagnostic bounds')
        raw = self.rows[key][1]
        vm = self.vm
        role, menu = bytearray(4096), bytearray(4096)
        struct.pack_into('<I', role, 0xc8, TARGET)
        struct.pack_into('<I', role, 0x64, mp)
        struct.pack_into('<I', menu, 0x150, PACKET + 128)
        vm.mem_write(SOURCE, bytes(role))
        vm.mem_write(TARGET, bytes(menu))
        vm.mem_write(MANAGER + 0x76bd0, struct.pack('<I', SOURCE))
        vm.mem_write(PACKET + 128, raw)
        vm.mem_write(BASE + 0x15d989, b'\0')
        vm.mem_write(SP, struct.pack('<II', RETURN, 0))
        vm.reg_write(reg.UC_X86_REG_ESP, SP)
        vm.reg_write(reg.UC_X86_REG_ECX, MANAGER)
        self.mp_mode = True
        try:
            vm.emu_start(BASE + (0x84500 if mode == 'selected' else 0x84560), RETURN, count=1000)
            result = vm.reg_read(reg.UC_X86_REG_EAX)
            cost = struct.unpack_from('<H', raw, 0x42)[0]
            if vm.reg_read(reg.UC_X86_REG_EIP) != RETURN or result != int(raw[0x67] != 0 and mp >= cost):
                raise AssertionError('Native MP predicate differs')
            if bytes(vm.mem_read(SOURCE, 4096)) != bytes(role) or bytes(vm.mem_read(TARGET, 4096)) != bytes(menu):
                raise AssertionError('MP gate modified input state')
            return {'bank': key[0], 'id': key[1], 'mode': mode, 'mp': mp,
                    'displayed_cost': cost, 'record_67': raw[0x67], 'allowed': result}
        finally:
            self.mp_mode = False


def run():
    probe = AmountProbe()
    records = []
    for key in probe.rows:
        for amount in (0, 1, 32767, 32768, 65535):
            for side, slot in ((0, 0), (1, 13)):
                records.append(probe.evaluate(key, amount, side, slot))
    gates = [probe.format_gate(field, gate, amount)
             for field in (0x5e, 0x60, 0x62, 0x64)
             for gate in (0, 1, 65535) for amount in (-32768, -1, 0, 1, 32767)]
    mp_cases = []
    for key, (_, raw) in probe.rows.items():
        cost = struct.unpack_from('<H', raw, 0x42)[0]
        for mp in sorted({0, max(0, cost - 1), cost, cost + 1, 0xffffffff}):
            for mode in ('selected', 'indexed'):
                mp_cases.append(probe.mp_gate(key, mp, mode))
    return {'image_sha256': SHA, 'skill_sha256': hashlib.sha256(probe.source).hexdigest(),
            'skill_definitions': len(probe.rows), 'passed': len(records),
            'formatter_gate_cases': gates,
            'mp_gate_cases': mp_cases,
            'entry_rva': 'dcd30', 'stop_rva': 'dba61',
            'scope': 'Original action-prefix and state preparation, not full battle or captured official packets.',
            'mapping': '17-byte logical opcode80: +15 WORD -> actor+26c on action3; body pointer excludes opcode.',
            'boundary': 'Two sides at representative slots only. Stop immediately after native store; no renderer or formatter. '
                        'Caller packet provenance is static; original action function is executed with staged arguments. '
                        'Formatter gates separately execute D6BE0; CRT sprintf is intercepted to record arguments only. '
                        'MP predicates 84500/84560 execute with valid staged selection pointers and index zero; not resource debit. '
                        'No authoritative damage formula or monster stats inferred.',
            'cases': records}


if __name__ == '__main__':
    report = run()
    output = ROOT / 'artifacts/research/beta-unpack-20260920/skill-amount-probe.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'formatter_gate_cases', 'mp_gate_cases')}))
    print('formatter_gate_cases=' + str(len(report['formatter_gate_cases'])))
    print('mp_gate_cases=' + str(len(report['mp_gate_cases'])))
