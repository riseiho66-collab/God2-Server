"""Execute beta logical-length and scalar receiver code with diagnostic inputs."""
import hashlib
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as reg

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/research/beta-unpack-20260920/beta-mapped.bin'
SHA = 'ef373960e2cf455916110f81eaff3935c1d950a46ff7de7b4ef562b01a56405f'
BASE, OWNER, ACTOR, PACKET, STACK = 0x400000, 0x3000000, 0x3200000, 0x3300000, 0x3400000
SP, RETURN = STACK + 0x8000, STACK + 0xff00


def run():
    image = IMAGE.read_bytes()
    if hashlib.sha256(image).hexdigest() != SHA:
        raise ValueError('Unqualified beta image')
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(BASE, (len(image) + 4095) & ~4095)
    vm.mem_write(BASE, image)
    for address, size in ((OWNER, 0x200000), (ACTOR, 4096), (PACKET, 4096), (STACK, 65536)):
        vm.mem_map(address, size)
    allowed = ((0x1200, 0x12f4), (0xc9460, 0xc9521), (0xc9530, 0xc95f1),
               (0xcf200, 0xcf28a), (0xdde80, 0xddf75))

    def hook(uc, address, size, unused):
        if address == RETURN:
            uc.emu_stop()
        elif not any(BASE + lo <= address and address + size <= BASE + hi for lo, hi in allowed):
            raise AssertionError(f'Unexpected beta instruction {address:x}')

    vm.hook_add(UC_HOOK_CODE, hook)

    def call(rva, arg):
        vm.mem_write(SP, struct.pack('<II', RETURN, arg))
        vm.reg_write(reg.UC_X86_REG_ESP, SP)
        vm.reg_write(reg.UC_X86_REG_ECX, OWNER)
        vm.reg_write(reg.UC_X86_REG_EFLAGS, 2)
        vm.emu_start(BASE + rva, RETURN, count=10000)
        if vm.reg_read(reg.UC_X86_REG_EIP) != RETURN:
            raise AssertionError('Beta function failed to return')
        return vm.reg_read(reg.UC_X86_REG_EAX)

    lengths = {op: call(0x1200, op) for op in range(256)}
    dispatch = []
    for op in range(0x19, 0xdf):
        index = image[0xc6ae8 + op - 0x19]
        target = struct.unpack_from('<I', image, 0xc6aac + 4 * index)[0] - BASE
        if target != 0xc6a5e:
            dispatch.append({'opcode': hex(op), 'case_rva': hex(target),
                             'length_function_result': lengths[op]})
    cases = []
    for op, entry in ((0x83, 0xc9460), (0x84, 0xc9530)):
        for slot in range(28):
            vm.mem_write(OWNER, bytes(0x200000))
            # The original lookup has 2 sides * 14 slots * 6 actor types.
            vm.mem_write(OWNER + 0xf0884 + 0x38 + slot * 24, struct.pack('<I', ACTOR))
            vm.mem_write(OWNER + 0x68, b'\xff')
            actor = bytearray(4096)
            struct.pack_into('<h', actor, 0x1d8, -1)
            initial = [101, 202, 303, 404]
            struct.pack_into('<4I', actor, 0xdbc, *initial)
            vm.mem_write(ACTOR, bytes(actor))
            value5, value9 = 123456 + slot, 654321 + slot
            packet = bytes((op, slot, 0, 0, 0)) + struct.pack('<II', value5, value9)
            vm.mem_write(PACKET, packet)
            call(entry, PACKET)
            after = list(struct.unpack('<4I', vm.mem_read(ACTOR + 0xdbc, 16)))
            expected = initial[:]
            if slot < 14:
                if op == 0x83:
                    expected[0], expected[2] = value9, value5
                else:
                    expected[1], expected[3] = value9, value5
            if after != expected:
                raise AssertionError((op, slot, after, expected))
            cases.append({'opcode': hex(op), 'slot': slot, 'passed': True,
                          'before': initial, 'after': after})
    return {'image_sha256': SHA, 'length_evaluations': len(lengths),
            'battle_dispatch': dispatch, 'scalar_cases': cases,
            'scope': 'Synthetic diagnostic inputs. Native scalar copies, not official stat values or damage formulas.',
            'boundary': 'Renderer excluded using native negative handle; local UI sync excluded using nonmatching local slot. '
                        'Two receiver entry points exercised, not full socket/frame/dispatch execution.'}


if __name__ == '__main__':
    report = run()
    path = ROOT / 'artifacts/research/beta-unpack-20260920/packet-probe.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'length_evaluations': report['length_evaluations'],
                      'scalar_cases_passed': len(report['scalar_cases']),
                      'battle_dispatch': report['battle_dispatch']}))
