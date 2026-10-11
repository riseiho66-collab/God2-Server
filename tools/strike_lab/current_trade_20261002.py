"""Pinned x86 PK classification and player-trade presentation oracle.

Only native consumers/producers are executed. External presentation helpers
are stubbed; this is neither a live-client test nor proof of server economics.
Run from server root: python -m tools.strike_lab.current_trade_20261002
"""
import hashlib
import json
import struct
from pathlib import Path
import pefile
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX
from tools.strike_lab.current_party_20261002 import Oracle, UI, BODY
from tools.strike_lab.current_protocol_coverage import qualified_image, NativeLengths
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.recover_companions import parse_sections

ROOT = Path(__file__).resolve().parents[2]


class PresentationOracle(Oracle):
    def __init__(self, raw):
        super().__init__(raw)
        # None of the tested PK/trade functions are replaced here.
        self.helpers = {
            0x50f580: 12, 0x507b20: 4, 0x507bb0: 4,
            0x5077c0: 0, 0x4856d0: 0, 0x5068c0: 16,
            0x507850: 12, 0x4b1a80: 4, 0x4c9c00: 0,
            0x46d340: 4, 0x46e490: 4, 0x47c9e0: 0,
            0x498a60: 4, 0x49e0c0: 8, 0x49e1a0: 12,
            0x49fbd0: 0, 0x48e7a0: 0, 0x4dcd10: 0,
            0x4dd130: 0, 0x4dd5b0: 0, 0x49b7b0: 4,
            0x4c9bd0: 4, 0x498c80: 4, 0x475d60: 16,
        }
        self.display = []
        self.put(UI + 0x232ebc, '<I', 0x30000000)
        # All unrelated modal windows are absent.
        self.vm.mem_write(UI + 0x232da4, b'\xff' * 0x100)
        for offset, widget in ((0x232dae, 1), (0x232db0, 2),
                               (0x232db2, 3), (0x232db4, 4),
                               (0x232de6, 5)):
            self.put(UI + offset, '<h', widget)
        self.put(UI + 0x232ebc, '<I', 0x30000000)
        for widget in range(1, 6):
            self.flags(widget, 0x10)

    def flags(self, widget, flags):
        self.put(UI + 0xe2988 + widget * 0x2a08, '<B', flags)

    def string(self, ptr, maximum=256):
        return self.read(ptr, maximum).split(b'\0', 1)[0]

    def hook(self, vm, address, size, data):
        esp = vm.reg_read(UC_X86_REG_ESP)
        if address in self.helpers:
            args = struct.unpack('<5I', self.read(esp + 4, 20))
            if address in (0x507b20, 0x507bb0):
                widget = args[0] & 0xffff
                if widget < 20:
                    before = self.read(UI + 0xe2988 + widget * 0x2a08, 1)[0]
                    self.flags(widget, before | 0x20 if address == 0x507b20 else before & ~0x28)
            elif address == 0x4856d0:
                # Number-to-text presentation helper, never server validation.
                self.vm.mem_write(args[1], str(args[0]).encode('ascii') + b'\0')
                self.display.append({'money_argument': args[0]})
            elif address == 0x5077c0:
                self.display.append({'widget': args[1] & 0xffff,
                                     'control': args[2], 'format_hex': self.string(args[3]).hex(),
                                     'value_hex': self.string(args[4]).hex() if args[2] == 0 or (args[1] & 0xffff) == 3 else None})
            elif address == 0x50f580:
                self.display.append({'modal_text_hex': self.string(args[0]).hex()})
        super().hook(vm, address, size, data)


def prove():
    raw = qualified_image()
    exe = (ROOT.parent / 'God2/God2.exe').read_bytes()
    mapped = pefile.PE(data=exe).get_memory_mapped_image()
    intervals = [(0x46a015, 0x46a024), (0x46a05f, 0x46a0d7), (0x46ad80, 0x46ae0d),
                 (0x46b5d4, 0x46b9cc), (0x483c80, 0x484620),
                 (0x484620, 0x484890), (0x4970a0, 0x497140),
                 (0x497250, 0x4972ee), (0x497a30, 0x497a82),
                 (0x498d70, 0x498dc9),
                 (0x49e440, 0x49e548),
                 (0x49d980, 0x49e050)]
    for entry, end in intervals:
        assert mapped[entry - 0x400000:end - 0x400000] == raw[entry - 0x400000:end - 0x400000], hex(entry)
    widths = {f'{op:02X}': NativeLengths(raw).query(op)[0]
              for op in (0x27, 0x4e, 0x4f, 0x50, 0x51, 0x52, 0x53, 0x8a)}
    assert widths == {'27': 5, '4E': 19, '4F': 3, '50': 25, '51': 9, '52': 3, '53': 3, '8A': 45}
    dispatch = {op: struct.unpack_from('<I', raw, 0x46b5d4 - 0x400000 + op * 4)[0]
                for op in (0x27, 0x4e, 0x4f, 0x50, 0x51, 0x52, 0x53, 0x8a)}
    assert dispatch == {0x27: 0x46a015, 0x4e: 0x46a05f, 0x4f: 0x46a0a9, 0x50: 0x46a071,
                        0x51: 0x46a083, 0x52: 0x46a097, 0x53: 0x46a0c4,
                        0x8a: 0x46ad80}, dispatch
    source = (ROOT.parent / 'God2/Data2/Patch/Comm/message.csvZ').read_bytes()
    rows = parse_sections(decode_csvz(source), ('ProgramMsg',))['ProgramMsg']['records']
    messages = {int(bytes.fromhex(row['fields_hex'][0])): bytes.fromhex(row['fields_hex'][1])
                for row in rows if len(row['fields_hex']) >= 2}
    assert messages[733].decode('cp950') == '%s 要與你PK，同意嗎？'
    assert messages[726].decode('cp950') == '你確定要交易嗎?'
    cases = []

    def passed(name, **detail):
        cases.append({'case': name, **detail})

    # Actual 69 producer and PK modal behavior, not inferred from opcode name.
    for mode in range(4):
        o = PresentationOracle(raw)
        names = b'Self\0'.ljust(16, b'\0') + b'Peer\0'.ljust(16, b'\0')
        o.vm.mem_write(BODY, names)
        o.call(0x4970a0, 123, 456, mode, BODY, BODY + 16)
        expected = b'\x69' + struct.pack('<II', 123, 456) + names + bytes([mode, 0, 0, 0])
        assert o.queued == [expected]
        passed(f'pk_69_mode_{mode}', record_hex=expected.hex())
    for click, mode in ((0, 1), (1, 2), (0, None)):
        o = PresentationOracle(raw)
        names = b'Self\0'.ljust(16, b'\0') + b'Peer\0'.ljust(16, b'\0')
        o.vm.mem_write(BODY, names)
        # Same argument order as the 8A world callsite: recipient then sender.
        o.call(0x484620, 123, 456, BODY, BODY + 16)
        assert o.read(UI + 0x23d5b0, 8) == struct.pack('<II', 123, 456)
        assert o.read(UI + 0x23d5b8, 5) == b'Self\0'
        assert o.read(UI + 0x23d5c8, 5) == b'Peer\0'
        o.put(BODY + 64, '<I', 0x76543210)
        o.vm.mem_write(BODY + 80, b'PK?\0')
        o.call(0x484710, 19, BODY + 64, BODY + 80)
        assert o.u32(UI + 0x23d5d8) == 19
        assert o.u32(UI + 0x23d5dc) == 0x76543210
        o.call(0x483c80, click, 2 if mode is None else 1)
        if mode is None:
            assert not o.queued
        else:
            assert len(o.queued) == 1 and o.queued[0][41] == mode
        assert o.read(UI + 0xe2988 + 5 * 0x2a08, 1)[0] & 0x28 == 0
        passed('pk_modal_escape' if mode is None else f'pk_modal_reply_{mode}')
    for flags in (0x20, 8):
        o = PresentationOracle(raw)
        o.flags(5, flags)
        o.vm.mem_write(BODY, b'Self\0'.ljust(16, b'\0') + b'Peer\0')
        o.call(0x484620, 123, 456, BODY, BODY + 16)
        assert o.queued[0][41] == 3 and o.u32(UI + 0x23d5b0) == 0
        passed('pk_busy', flags=flags)

    # Native player-trade producers: transports retain opaque bytes as opaque.
    for target in (0, 123, 0x10023, 0xffff):
        o = PresentationOracle(raw)
        o.call(0x49de30, target)
        assert o.queued == [b'\x29' + struct.pack('<HH', target & 0xffff, 0)]
        passed('trade_request_29', target=target, record_hex=o.queued[0].hex())
    for target, item, slot in ((123, 456, 0), (0xabcd, 0xffff, 29), (0x10001, 0x10002, 255),
                               (0x1234, 0x5678, 2)):
        o = PresentationOracle(raw)
        o.call(0x497290, target, item, slot)
        assert o.queued == [b'\x2a' + struct.pack('<HBBH', item & 0xffff, slot, 1, target & 0xffff)]
        passed('trade_item_2A', record_hex=o.queued[0].hex())
    for quantity in (1, 3, 99, 255):
        o = PresentationOracle(raw)
        record = struct.pack('<HBBH', 0x5678, 2, quantity, 0x1234)
        # 4C9ED0 mode5 uses this pointer producer after writing selected qty
        # at UI+23D5FD; this producer copies the six-byte record unchanged.
        o.call(0x4972d0, BODY, body=record)
        assert o.queued == [b'\x2a' + record]
        passed('trade_stack_item_2A_4972D0', quantity=quantity, record_hex=o.queued[0].hex())
    for money in (0, 1, 0x7fffffff, 0x80000000, 0xffffffff, 0x12345678):
        o = PresentationOracle(raw)
        o.call(0x497a30, 123, money)
        body = o.queued[0]
        assert body[:3] == b'\x2b\x7b\0' and len(body) == 9
        assert body[3:5] == b'\xa5\xa5'  # actual uninitialized stack WORD
        assert body[5:] == struct.pack('<I', money)
        passed('trade_money_2B', record_hex=body.hex(), opaque_word='uninitialized, not authoritative')
    fixture_records = []
    o = PresentationOracle(raw)
    o.call(0x49de30, 0x1234)
    o.call(0x497290, 0x1234, 0x5678, 2)
    o.call(0x497a30, 0x1234, 0x12345678)
    o.call(0x497a60, 0x2c, 0)
    o.call(0x497a60, 0x2d, 0)
    fixture_records = [packet.hex() for packet in o.queued]
    assert fixture_records == ['2934120000', '2a785602013412',
                               '2b3412a5a578563412', '2c00', '2d00']
    passed('five_producer_fixture_contract', records=fixture_records)
    o = PresentationOracle(raw)
    bank, table = 0x32000000, 0x33000000
    o.vm.mem_map(bank, 0xb4000)
    o.vm.mem_map(table, 0x1000)
    o.put(UI + 0xcff70, '<I', bank)
    o.put(bank + 0xb2c6c, '<H', 800)
    o.put(bank + 0xb2c68, '<I', table)
    o.put(table + 0xb54, '<I', BODY)
    o.vm.mem_write(BODY, messages[726] + b'\0')
    o.put(UI + 0x855f0, '<h', -1)
    o.call(0x49e440, 11, 0x20)
    assert o.u32(UI + 0x23d5d8) == 2
    assert any(d.get('modal_text_hex') == messages[726].hex() for d in o.display)
    passed('trade_button_to_726_mode2')
    o = PresentationOracle(raw)
    o.put(UI + 0x23d5d8, '<I', 2)
    o.put(UI + 0x866dc, '<I', 1)  # money already posted: avoids UI edit retrieval
    o.flags(5, 0x20)
    o.call(0x483c80, 0, 1)
    assert o.queued == [b'\x2c\0'] and o.u32(UI + 0x866e0) == 1
    passed('trade_confirm_mode2_2C')

    # Real native 4E consumer and start function; list rendering is external.
    for resource_ready in (False, True):
        o = PresentationOracle(raw)
        o.flags(1, 0x10 if resource_ready else 0)
        o.vm.mem_write(UI + 0x866e8, b'\x55' * 384)
        o.call(0x49d980, BODY, body=b'Peer\0'.ljust(16, b'\0') + struct.pack('<H', 456))
        assert o.u32(UI + 0x866e4) == int(resource_ready)
        assert o.read(UI + 0x866e8, 384) == (b'\0' if resource_ready else b'\x55') * 384
        if resource_ready:
            assert o.read(UI + 0x866d0, 2) == struct.pack('<H', 456)
            assert all(o.read(UI + 0xe2988 + widget * 0x2a08, 1)[0] & 0x20 for widget in range(1, 5))
            assert any(d.get('value_hex') == b'Peer'.hex() for d in o.display)
        passed('trade_start_4E', resource_ready=resource_ready)
    for slot in list(range(8)) + [8, 127, 128, 255]:
        o = PresentationOracle(raw)
        record = bytearray(range(24))
        record[1] = slot
        o.call(0x49df10, BODY, body=bytes(record))
        expected = bytearray(192)
        if slot < 8:
            expected[slot * 24:slot * 24 + 24] = record
        assert o.read(UI + 0x867a8, 192) == bytes(expected)
        passed('trade_peer_item_50', raw_slot=slot, accepted=slot < 8)
    for money in (0, 123456, 0x7fffffff, 0x80000000, 0xffffffff):
        o = PresentationOracle(raw)
        o.call(0x49dfb0, money)
        assert {'money_argument': money} in o.display
        assert any(d.get('control') == 1 and d.get('widget') == 3 for d in o.display)
        passed('trade_peer_money_51', value=money, dispatch_source='DWORD packet+5 / payload+4')
    for money in (0, 123456, 0x7fffffff, 0x80000000, 0xffffffff):
        o = PresentationOracle(raw)
        o.call(0x498d70, money)
        assert o.u32(UI + 0x85604) == money
        assert any(a == 0x49b7b0 and args[0] == money for a, args in o.calls)
        passed('wallet_27_498D70', value=money,
               dispatch_source='DWORD packet+1 / payload+0')
    for status in (0, 1, 0xffff):
        o = PresentationOracle(raw)
        o.call(0x49dff0, status)
        if status:
            assert any(a == 0x507850 and args[:3] == (3, 0, 0xffff) for a, args in o.calls)
            assert any(a == 0x475d60 and args[0] == 559 for a, args in o.calls)
        else:
            assert any(a == 0x5068c0 and args == (1, 0x21, 9, 3) for a, args in o.calls)
        passed('trade_peer_status_53', status=status, semantic_scope='confirmation display, not completion')
    for refund in (False, True):
        o = PresentationOracle(raw)
        o.put(UI + 0x85604, '<I', 500)
        o.put(UI + 0x866d4, '<I', 100)
        o.put(UI + 0x866dc, '<I', int(refund))
        o.put(UI + 0x866d0, '<H', 123)
        for base in (0x866e8, 0x867a8):
            for slot in range(8):
                o.put(UI + base + slot * 24, '<BBHH', 9, slot, 0xabcd, 456)
        o.call(0x49de50)
        assert o.u32(UI + 0x85604) == (600 if refund else 500)
        assert o.u32(UI + 0x866dc) == 0 and o.read(UI + 0x866d0, 2) == b'\0\0'
        for base in (0x866e8, 0x867a8):
            for slot in range(8):
                assert o.read(UI + base + slot * 24, 1) == b'\0'
                assert o.read(UI + base + slot * 24 + 4, 2) == b'\0\0'
        passed('trade_reset_49DE50', local_escrow_refund=refund)
    for local_cancel in (False, True):
        o = PresentationOracle(raw)
        o.flags(1, 0x30)
        o.put(UI + 0x866e4, '<I', 1)
        o.put(UI + 0x866e0, '<I', 1)
        o.call(0x49dd40, int(local_cancel))
        assert o.queued == ([b'\x2d\0'] if local_cancel else [])
        assert o.u32(UI + 0x866e4) == o.u32(UI + 0x866e0) == 0
        assert all(o.read(UI + 0xe2988 + widget * 0x2a08, 1)[0] & 0x20 == 0 for widget in range(1, 5))
        passed('trade_close_49DD40', local_cancel=local_cancel)
    return {'qualified_native_sha256': hashlib.sha256(raw).hexdigest(),
            'current_exe_sha256': hashlib.sha256(exe).hexdigest(),
            'qualified_code_intervals': [[hex(a), hex(b)] for a, b in intervals],
            'source_message_sha256': hashlib.sha256(source).hexdigest(),
            'classification': {'69_8A': 'PK challenge, ProgramMsg733',
                               '29_2A_2B_2C_2D_4E_4F_50_51_52_53': 'native player-trade UI, ProgramMsg726 mode2'},
            'S2C_logical_widths': widths,
            'dispatcher': {f'{k:02X}': f'{v:08X}' for k, v in dispatch.items()},
            'five_producer_fixture_records': fixture_records,
            'cases': cases, 'passed': len(cases),
            'open': ['No live-client or network acceptance in this oracle.',
                     'No official server economic/transaction/timeout rules recovered.',
                     '51 payload DWORD+0 is not consumed by its display callsite.',
                     '4F resets local escrow before close; 52 closes without reset. Successful server transfer must be independently verified.',
                     '53 changes confirmation display; it does not close or transfer assets.',
                     'C2S2B opaque WORD is native uninitialized stack; no invented semantics.',
                     'D6/4EAC00 generic consent, 4EAEF0 discard and 4EB440 confirmation are outside player-trade proof.']}


if __name__ == '__main__':
    print(json.dumps(prove(), ensure_ascii=True, indent=2))
