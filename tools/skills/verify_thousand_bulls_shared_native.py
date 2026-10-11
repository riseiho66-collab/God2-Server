"""Pinned-x86 evidence for shared-target ingestion and native death bookkeeping.

Runs only a memory-image emulator. No game process, desktop or live server.
"""
import json
import struct
from unicorn import x86_const as x
from tools.skills.verify_thousand_bulls_client_flow import Native, SP, RETURN, PIN, OUT


def main():
    cases = []
    for side in (0, 1):
        for count in (1, 2, 14):
            for reverse in (False, True):
                native = Native()
                slots = (side * 14, side * 14 + 13)
                targets = [(1 - side) * 14 + i for i in range(count)]
                for target in targets:
                    native.put(native.actor(target) + 0xde8, 200)
                    native.put(native.actor(target) + 0xdf0, 200)
                def hit(source, target, end):
                    packet = bytearray(15)
                    packet[:3] = bytes((0x83, 3, source))
                    struct.pack_into('<H', packet, 5 + 2 * (1 - side), 1 << target)
                    struct.pack_into('<h', packet, 9, -100)
                    packet[11] = 150
                    packet[14] = end
                    return bytes(packet)
                logical = b''.join(hit(source, target, end)
                    for source, end in ((slots[0], 28), (slots[1], 0))
                    for target in range(count))
                native.dispatch(logical + b'\x88' + bytes(120))
                for target in targets:
                    actor = native.actor(target)
                    assert native.get(actor + 0x277, '<B') == 2
                    assert native.get(actor + 0x232, '<B') == 9
                for i in range(count):
                    assert native.get(native.actor(slots[0]) + 0x224 + i, '<B') == 0
                    assert native.get(native.actor(slots[1]) + 0x224 + i, '<B') == 9
                order = slots[::-1] if reverse else slots
                observations = []
                for turn, source in enumerate(order):
                    values = []
                    for i, target in enumerate(targets):
                        # Execute the original decision block, not a Python
                        # rewrite of its conditions or counter arithmetic.
                        native.put(SP + 0x28, native.actor(source))
                        for register, value in ((x.UC_X86_REG_ESP, SP),
                                (x.UC_X86_REG_ESI, i), (x.UC_X86_REG_EBP, native.actor(target)),
                                (x.UC_X86_REG_EBX, 15), (x.UC_X86_REG_EFLAGS, 2)):
                            native.vm.reg_write(register, value)
                        native.stops = {0x524dcd}
                        native.vm.emu_start(0x524d86, RETURN, count=100, timeout=1000000)
                        assert native.vm.reg_read(x.UC_X86_REG_EIP) == 0x524dcd
                        pending = native.get(native.actor(target) + 0x277, '<B')
                        reaction = native.vm.reg_read(x.UC_X86_REG_EBX)
                        assert pending == 1 - turn
                        assert reaction == (9 if turn else 15)
                        values.append({'pending': pending, 'reaction': reaction})
                    observations.append(values)
                cases.append({'side': side, 'targets': count, 'reverse': reverse,
                    'original_bookkeeping': observations})
    report = {'status': 'PASS', 'image_sha256': PIN, 'cases': cases,
        'scope': 'Original x86 S2C83/88 ingestion and 00524D86..00524DCD death decision block',
        'limitations': 'Synthetic actor/resources; not a complete live-client battle'}
    (OUT / 'shared-target-native-20261001.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: 12 original-x86 shared-target cases; both sides, 1/2/14 targets, both orders')


if __name__ == '__main__':
    main()
