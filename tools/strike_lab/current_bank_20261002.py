"""Pinned original x86 bank transport/storage/presentation oracle.

Execute native functions, with only queue and external presentation helpers
replaced. This does not establish server economic rules, NPC placements, or
live client acceptance. Run: python -m tools.strike_lab.current_bank_20261002
"""
import hashlib
import json
import struct
from pathlib import Path
import pefile
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EIP
from tools.strike_lab.current_party_20261002 import Oracle, UI, BODY, STACK, STOP
from tools.strike_lab.current_protocol_coverage import qualified_image, NativeLengths

ROOT = Path(__file__).resolve().parents[2]


class BankOracle(Oracle):
    def __init__(self, raw):
        super().__init__(raw)
        # Do not replace the tested opening/closing, producers or consumers.
        self.helpers = {
            0x507b20: 4, 0x507bb0: 4, 0x5068c0: 16,
            0x4b1a80: 4, 0x498a60: 4, 0x4d8610: 0,
            0x47e2a0: 0, 0x47e2c0: 0, 0x4ceda0: 0,
            0x498c90: 0, 0x4c9bd0: 4, 0x498c80: 4,
            0x471720: 0, 0x471610: 4, 0x49b7f0: 28,
            0x4856d0: 0, 0x5077c0: 0, 0x475d60: 16,
            0x44e140: 4, 0x402c70: 0, 0x472820: 4, 0x49b7b0: 4,
            0x499a60: 4, 0x506850: 16, 0x5067a0: 12,
        }
        self.display = []
        self.vm.mem_write(UI + 0x232da4, b'\xff' * 0x100)
        self.put(UI + 0x232dd2, '<h', 6)
        self.put(UI + 0x232dd4, '<h', 7)
        self.flags(6, 0x10)
        self.flags(7, 0x10)
        self.put(UI + 0x83994, '<h', -1)

    def flags(self, widget, value):
        self.put(UI + 0xe2988 + widget * 0x2a08, '<B', value)

    def visible(self, widget=6):
        return bool(self.read(UI + 0xe2988 + widget * 0x2a08, 1)[0] & 0x20)

    def cell(self, page, slot):
        return UI + 0x839cc + (page * 50 + slot) * 24

    def hook(self, vm, address, size, data):
        if address in self.helpers:
            esp = vm.reg_read(UC_X86_REG_ESP)
            args = struct.unpack('<5I', self.read(esp + 4, 20))
            if address in (0x507b20, 0x507bb0):
                widget = args[0] & 0xffff
                assert widget in (6, 7)
                old = self.read(UI + 0xe2988 + widget * 0x2a08, 1)[0]
                self.flags(widget, old | 0x20 if address == 0x507b20 else old & ~0x28)
            elif address == 0x4856d0:
                vm.mem_write(args[1], str(args[0]).encode() + b'\0')
                self.display.append({'money_argument': args[0]})
            elif address == 0x5077c0:
                self.display.append({'widget': args[1] & 0xffff, 'control': args[2],
                                     'value_hex': self.read(args[4], 64).split(b'\0', 1)[0].hex()})
        super().hook(vm, address, size, data)


def prove():
    raw = qualified_image()
    exe = (ROOT.parent / 'God2/God2.exe').read_bytes()
    mapped = pefile.PE(data=exe).get_memory_mapped_image()
    intervals = [(0x46a0db, 0x46a1be), (0x46b5d4, 0x46b9cc),
                 (0x471190, 0x4724e0), (0x496860, 0x49688c),
                 (0x497380, 0x497920), (0x498d70, 0x498dc9),
                 (0x49b770, 0x49b7b0), (0x459a60, 0x459a90),
                 (0x49f010, 0x49f8d0), (0x4c9ed0, 0x4ca600)]
    for start, end in intervals:
        assert mapped[start - 0x400000:end - 0x400000] == raw[start - 0x400000:end - 0x400000], hex(start)
    widths = {f'{op:02X}': NativeLengths(raw).query(op)[0] for op in (0x27, 0x46, 0x47, 0x48, 0x49, 0x61, 0x62)}
    assert widths == {'27': 5, '46': 13, '47': 9, '48': 29, '49': 5, '61': 9, '62': 3}
    dispatch = {f'{op:02X}': struct.unpack_from('<I', raw, 0x6b5d4 + op * 4)[0]
                for op in (0x46, 0x47, 0x48, 0x49)}
    assert dispatch == {'46': 0x46a188, '47': 0x46a1ac, '48': 0x46a19a, '49': 0x46a0db}
    cases = []

    def passed(label, **detail):
        cases.append({'case': label, **detail})

    for entry, opcode in ((0x497390, 0x61), (0x497450, 0x62)):
        for target, amount in ((0, 0), (0x1234, 1), (0x10023, 0x12345678),
                               (0xffff, 0x7fffffff), (0x4321, 0x80000000), (1, 0xffffffff)):
            o = BankOracle(raw)
            o.call(entry, target, amount)
            expected = bytes([opcode]) + struct.pack('<IH', amount, target & 0xffff) + b'\xa5\xa5'
            assert o.queued == [expected]
            passed(f'C2S{opcode:02X}_normal', record_hex=expected.hex())
        for mode, subtype in ((1, 0), (2, 0), (2, 2), (2, 3), (3, 3)):
            o = BankOracle(raw)
            o.put(UI + 0x855ed, '<B', mode)
            o.put(UI + 0x855ec, '<B', subtype)
            o.call(entry, 0x1234, 0x12345678)
            if mode == 2 and subtype == 3:
                expected = b'\x7e' + struct.pack('<HB', 0x1234, opcode - 0x61) + b'\xa5' + struct.pack('<I', 0x12345678)
                assert o.queued == [expected]
            else:
                assert not o.queued
            passed('money_storage_mode_gate', producer=hex(entry), mode=mode, subtype=subtype,
                   records=[x.hex() for x in o.queued])

    # The page helper is a real ret 8. Native pages switch without new C2S.
    o = BankOracle(raw)
    o.call(0x497380, 0x1234, 5)
    assert not o.queued
    passed('page_helper_is_native_noop')

    for mode, ready in ((0, True), (11, True), (0, False)):
        o = BankOracle(raw)
        o.flags(6, 0x10 if ready else 0)
        o.put(UI + 0x855ed, '<B', 2)
        o.put(UI + 0x839a4, '<I', 5)
        o.vm.mem_write(UI + 0x839a8, b'\x55' * (24 + 7200))
        body = struct.pack('<I', 0x76541234) + b'\x99' * 6 + bytes([mode, 0xab])
        o.call(0x471f50, BODY, body=body)
        assert o.u32(UI + 0x839c0) == 0x76541234 and o.u32(UI + 0x839a4) == 0
        assert o.read(UI + 0x839a8, 24) == bytes(24)
        assert o.read(UI + 0x839cc, 7200) == bytes(7200)
        assert o.read(UI + 0x855ed, 1)[0] == (mode == 11)
        assert o.visible() == ready and o.visible(7) == ready
        assert not o.queued
        passed('S2C46_open', mode=mode, resources_ready=ready, visible=o.visible())

    # Actual absolute and additive bank balance consumers execute their money
    # text formatting call; wallet update is a separate S2C27 consumer.
    for amount in (0, 1, 500000000, 0x7fffffff):
        o = BankOracle(raw)
        o.call(0x471e10, BODY, body=struct.pack('<II', amount, 0xdeadbeef))
        assert o.u32(UI + 0x839c4) == amount
        assert o.display[-2]['money_argument'] == amount
        assert o.display[-1]['widget'] == 6 and o.display[-1]['control'] == 0
        assert o.display[-1]['value_hex'] == str(amount).encode().hex()
        passed('S2C47_absolute_bank', amount=amount)
    for mode, amount, before, after in ((1, 400, 1000, 1400), (3, 400, 1000, 600)):
        o = BankOracle(raw)
        o.put(UI + 0x839c4, '<I', before)
        body = struct.pack('<I', amount) + b'\xff' * 6 + bytes([mode, 0])
        o.call(0x471f50, BODY, body=body)
        assert o.u32(UI + 0x839c4) == after and o.u32(UI + 0x85604) == 0
        passed('S2C46_bank_delta', mode=mode, before=before, after=after)
    o = BankOracle(raw)
    o.put(UI + 0x839c4, '<I', 333)
    o.call(0x498d70, 123456)
    assert o.u32(UI + 0x85604) == 123456 and o.u32(UI + 0x839c4) == 333
    passed('S2C27_purse_separate_from_bank')

    for page, slot, quantity, visible in ((0, 0, 1, False), (0, 49, 99, True),
                                         (5, 0, 255, False), (5, 49, 0, True)):
        o = BankOracle(raw)
        if visible:
            o.flags(6, 0x30)
        metadata = struct.pack('<H', 3107) + bytes(range(2, 20))
        body = bytes([page, 0xa1, 0xa2, 0xa3, quantity, slot, 0xb1, 0xb2]) + metadata
        o.call(0x471e50, BODY, body=body)
        assert o.read(o.cell(page, slot), 24) == bytes([quantity, slot, 0, 0]) + metadata
        assert o.u32(UI + 0x839a8 + page * 4) == 1
        assert sum(address == 0x471610 for address, _ in o.calls) == (page == 0)
        assert sum(address == 0x44e140 for address, _ in o.calls) == visible
        passed('S2C48_bank_item', page=page, slot=slot, quantity=quantity, metadata_hex=metadata.hex())

    for source_qty in (0, 3):
        o = BankOracle(raw)
        o.put(UI + 0x839a4, '<I', 2)
        for slot in (4, 5):
            o.vm.mem_write(o.cell(2, slot), b'\x77' * 24)
        body = struct.pack('<IHBBBBBB', 0xdeadbeef, 3107, 4, source_qty, 5, 7, 7, 0)
        o.call(0x471f50, BODY, body=body)
        first = o.read(o.cell(2, 4), 24)
        assert first[:2] == (bytes([source_qty, 4]) if source_qty else b'\0\0')
        assert first[4:6] == struct.pack('<H', 3107 if source_qty else 0)
        assert first[6:] == b'\x77' * 18
        second = o.read(o.cell(2, 5), 24)
        assert second[:2] == b'\x07\x05' and second[4:6] == struct.pack('<H', 3107)
        assert second[6:] == b'\x77' * 18
        passed('S2C46_mode7_two_current_page_slots', source_qty=source_qty)
    for page in (0, 5):
        o = BankOracle(raw)
        o.vm.mem_write(o.cell(page, 49), b'\x77' * 24)
        body = b'\xaa' * 8 + bytes([page, 49, 12, 0])
        o.call(0x471f50, BODY, body=body)
        cell = o.read(o.cell(page, 49), 24)
        assert cell[:2] == b'\0\0' and cell[4:6] == b'\0\0' and cell[6:] == b'\x77' * 18
        passed('S2C46_mode12_clear_page_slot', page=page, slot=49)

    for mode, subtype in ((0, 1), (1, 2), (2, 3)):
        o = BankOracle(raw)
        o.flags(6, 0x30)
        o.flags(7, 0x30)
        o.put(UI + 0x855ed, '<B', mode)
        o.put(UI + 0x839c0, '<I', 0x76541234)
        o.put(UI + 0x839c8, '<I', 123)
        o.call(0x471390)
        assert o.queued == [b'\x39' + struct.pack('<HH', 0x1234, subtype)]
        assert not o.visible() and not o.visible(7) and o.u32(UI + 0x839c8) == 0
        passed('bank_native_close_C2S39', mode=mode, subtype=subtype, record_hex=o.queued[0].hex())
    o = BankOracle(raw)
    o.call(0x471390)
    assert not o.queued
    passed('already_closed_no_close_packet')

    for control, amount, balance, sends in ((57, 0, 0, False), (57, 1, 499999999, True),
                                            (57, 1, 500000000, False), (58, 1, 0, True),
                                            (58, 0xffffffff, 0, False), (57, 0x7fffffff, 1, True)):
        o = BankOracle(raw)
        o.put(UI + 0x839c8, '<I', amount)
        o.put(UI + 0x839c4, '<I', balance)
        o.put(UI + 0x839c0, '<I', 0x1234)
        o.call(0x4719b0, control, 1)
        assert bool(o.queued) == sends
        if sends:
            assert o.queued[0][:7] == bytes([0x61 if control == 57 else 0x62]) + struct.pack('<IH', amount, 0x1234)
        passed('bank_native_money_button', control=control, amount=amount, bank_before=balance,
               records=[x.hex() for x in o.queued])
    for edition, start, control, expected in ((1, 0, 55, 1), (0, 0, 55, 2),
                                            (1, 1, 56, 0), (0, 2, 56, 0)):
        o = BankOracle(raw)
        o.put(UI + 0x232f64, '<I', edition)
        o.put(UI + 0x839a4, '<I', start)
        o.call(0x4719b0, control, 1)
        assert o.u32(UI + 0x839a4) == expected and not o.queued
        passed('bank_native_page_wrap_no_packet', edition_field=edition, before=start, after=expected)

    for mode, trade in ((0, False), (1, False), (2, False), (0, True)):
        o = BankOracle(raw)
        o.put(UI + 0x855ed, '<B', mode)
        o.put(UI + 0x855ec, '<B', 3)
        o.put(UI + 0x839a4, '<I', 2)
        o.put(UI + 0x839c0, '<I', 0x1234)
        o.put(UI + 0x866e4, '<I', int(trade))
        o.call(0x497510, 0, 49)
        expected = ([] if trade else [b'\x7f\x34\x12\x02\x02\x00\x31\x01\xa5']
                    if mode == 2 else [b'\x65\x34\x12\x02\x00\x31\x01'])
        assert o.queued == expected
        passed('C2S65_bank_to_bank_move', storage_mode=mode, active_trade=trade,
               records=[x.hex() for x in o.queued])
    for source, destination, quantity in ((0, 49, 1), (29, 0, 99), (255, 255, 255)):
        o = BankOracle(raw)
        o.put(UI + 0x839a4, '<I', 2)
        o.put(UI + 0x839c0, '<I', 0x1234)
        o.call(0x4975f0, source, destination, quantity)
        assert o.queued == [b'\x63' + struct.pack('<HBBBB', 0x1234, 2, source, destination, quantity)]
        passed('C2S63_fields_not_direction_claim', record_hex=o.queued[0].hex())

    for entry, opcode in ((0x4976f0, 0x63), (0x497880, 0x64)):
        for quantity in (1, 3, 99, 255):
            o = BankOracle(raw)
            body = struct.pack('<HBBBB', 0x1234, 2, 0, 49, quantity)
            o.call(entry, BODY, body=body)
            assert o.queued == [bytes([opcode]) + body]
            passed('C2S_bank_stack_pointer_copy', opcode=f'{opcode:02X}', quantity=quantity,
                   record_hex=o.queued[0].hex())
    # Execute actual native bag->bank drop handler AND its compatibility check.
    # Item lookup is a real zero-initialized synthetic catalogue, not a stub.
    # This establishes caller direction only, never eligibility of live items.
    for source, destination in ((0, 2), (29, 49)):
        o = BankOracle(raw)
        catalogue = 0x32000000
        o.vm.mem_map(catalogue, 0xc0000)
        o.put(UI + 0xcff70, '<I', catalogue)
        o.put(UI + 0x839c0, '<I', 0x1234)
        o.put(UI + 0x839a4, '<I', 2)
        o.put(UI + 0x855f0, '<h', source)
        o.put(UI + 0x8560c + source * 24, '<BBHH', 1, source, 0, 3107)
        o.call(0x4723a0, destination, 1)
        assert o.queued == [b'\x63' + struct.pack('<HBBBB', 0x1234, 2, source, destination, 1)]
        assert o.read(UI + 0x855f0, 2) == b'\xff\xff'
        passed('native_bag_to_bank_drop_4723A0', source_bag=source, destination_bank=destination)
    # Execute the actual bank dragging mode17 -> bag drop branch.
    for source, destination in ((0, 0), (49, 29)):
        o = BankOracle(raw)
        o.put(UI + 0x839c0, '<I', 0x1234)
        o.put(UI + 0x839a4, '<I', 2)
        o.put(UI + 0x83994, '<h', source)
        o.put(o.cell(2, source), '<BB', 1, source)
        o.call(0x49f010, 0x17, destination, 1)
        assert o.queued == [b'\x64' + struct.pack('<HBBBB', 0x1234, 2, source, destination, 1)]
        assert o.read(UI + 0x83994, 2) == b'\xff\xff'
        passed('native_bank_to_bag_drop_49F010_mode17', source_bank=source, destination_bag=destination)
    for mode, opcode in ((2, 0x63), (3, 0x64)):
        for quantity in (2, 99):
            o = BankOracle(raw)
            o.put(UI + 0x232dd0, '<h', 8)
            o.flags(8, 0x30)
            o.put(UI + 0x23d5e4, '<I', mode)
            o.put(UI + 0x23d5e8, '<I', quantity)
            o.vm.mem_write(UI + 0x23d5f4, struct.pack('<HBBBB', 0x1234, 2, 0, 49, 1))
            o.call(0x4c9ed0)
            assert o.queued == [bytes([opcode]) + struct.pack('<HBBBB', 0x1234, 2, 0, 49, quantity)]
            passed('native_bank_quantity_confirm_4C9ED0', mode=mode, quantity=quantity,
                   record_hex=o.queued[0].hex())

    result = {
        'scope': 'original x86 function oracle; external queue/UI helpers stubbed; not live-client/server acceptance',
        'passed': len(cases), 'failed': 0, 'cases': cases,
        'mapped_image_sha256': hashlib.sha256(raw).hexdigest(),
        'client_sha256': hashlib.sha256(exe).hexdigest(),
        'matched_intervals': [[hex(a), hex(b)] for a, b in intervals],
        's2c_logical_widths': widths, 'dispatcher': {k: hex(v) for k, v in dispatch.items()},
        'offsets': {'bank_target_dword': 'UI+839C0', 'bank_money_dword': 'UI+839C4',
                    'bank_numeric_input_dword': 'UI+839C8', 'bank_page_dword': 'UI+839A4',
                    'bank_cache_six_dwords': 'UI+839A8', 'bank_300_raw24_cells': 'UI+839CC',
                    'storage_subtype_byte': 'UI+855EC', 'storage_mode_byte': 'UI+855ED',
                    'ordinary_purse_dword': 'UI+85604', 'ordinary_bag_raw24': 'UI+8560C'},
        'open': 'S2C46 mode0 opens ordinary bank through real471190; targetDWORDbody0; zeroes300cells/sixcache; needs resource-ready widget232DD2 bit10',
        'close': 'real471390 closes locally before queuing C2S39 targetWORD/subtypeWORD1, no reply required by that path',
        's2c49': 'not close acknowledgement: dispatcher46A0DB ignores whilebankvisible, otherwise creates modal mode1 from bodyWORD+2; string233; not machine-executed here',
        'unproved': ['formal server authorization/economic rules/capacity/unlock/atomicity',
                     'native NPC37 bank open request chain and exact original NPC placements',
                     'rendered pixels or real Windows client banking UI'],
        'item_caller_direction': 'actual4723A0 bag→bank63; actual49F010 mode17 bank→bag64; actual4C9ED0 quantity modes2/3 preserve six-bytefields with selectedqty; catalogue fixture synthetic',
        'opaque': 'C2S61/62body6..7 native uninitialized; S2C47body4..7 unused; S2C48body1..3/6..7 unused; preserve as opaque',
        'native_guard_limitation': 'depositbutton signed32 bank+input can overflow: input7FFFFFFF,bank1 queues61; servercap/checkedarithmetic is CUSTOM-0064 policy, not supplied by this client guard',
    }
    out = ROOT / 'artifacts/research/native-bank-20261002/oracle.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'passed': len(cases), 'failed': 0, 'evidence': str(out)}))
    return result


if __name__ == '__main__':
    prove()
