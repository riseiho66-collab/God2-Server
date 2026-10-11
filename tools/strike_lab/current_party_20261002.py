"""Build-pinned native party producer/consumer oracle, never a live-client gate."""
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX
from tools.strike_lab.current_protocol_coverage import qualified_image, NativeLengths

ROOT = Path(__file__).resolve().parents[2]
UI, STACK, BODY, STOP, ROOT_ACTOR = 0x10000000, 0x20000000, 0x21000000, 0x22000000, 0x30000000
ACTOR = ROOT_ACTOR + 0x90


class Oracle:
    def __init__(self, raw):
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(0x400000, (len(raw) + 4095) & ~4095)
        self.vm.mem_write(0x400000, raw)
        self.vm.mem_map(UI, 0x240000)
        self.vm.mem_map(ROOT_ACTOR, 0x6000)
        for page in (STACK, BODY, STOP):
            self.vm.mem_map(page, 4096)
        self.put(UI + 0x86874, '<I', 0x31000000)
        self.put(UI + 0x86888, '<I', ACTOR)
        self.put(UI + 0x8688c, '<I', ROOT_ACTOR)
        self.vm.mem_write(ACTOR + 0x27, b'Leader\0')
        self.vm.mem_write(ROOT_ACTOR + 0xb7, b'Leader\0')
        self.put(UI + 0x232df6, '<h', -1)
        self.put(0x5707bc, '<I', STOP + 16)  # external timeGetTime import only
        self.queued, self.calls = [], []
        self.helpers = {0x4e9890: 0, 0x4e8fb0: 0, 0x4eb8b0: 0,
                        0x4eb880: 0, 0x4ea100: 8, 0x4c2660: 16,
                        0x4ea410: 0, 0x47dd40: 0, 0x5060f0: 16,
                        0x505680: 0, 0x4c2890: 0}
        self.vm.hook_add(UC_HOOK_CODE, self.hook)

    def put(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def read(self, address, count):
        return bytes(self.vm.mem_read(address, count))

    def u32(self, address):
        return struct.unpack('<I', self.read(address, 4))[0]

    def hook(self, v, address, size, _):
        if address == STOP:
            v.emu_stop()
            return
        esp = v.reg_read(UC_X86_REG_ESP)
        if address == 0x4132e0:
            ret, opcode, ptr, count = struct.unpack('<4I', v.mem_read(esp, 16))
            assert v.reg_read(UC_X86_REG_ECX) == 0x31000000
            self.queued.append(bytes([opcode]) + self.read(ptr, count))
            cleanup = 12
        elif address == STOP + 16:
            ret, = struct.unpack('<I', v.mem_read(esp, 4))
            cleanup = 0
            v.reg_write(UC_X86_REG_EAX, 123456)
        elif address in self.helpers:
            ret, = struct.unpack('<I', v.mem_read(esp, 4))
            cleanup = self.helpers[address]
            args = struct.unpack('<4I', v.mem_read(esp + 4, 16))
            self.calls.append((address, args))
        else:
            return
        v.reg_write(UC_X86_REG_EIP, ret)
        v.reg_write(UC_X86_REG_ESP, esp + 4 + cleanup)

    def call(self, entry, *args, body=None):
        if body is not None:
            self.vm.mem_write(BODY, body)
        # Deterministic stack residue makes unwritten transport bytes visible.
        self.vm.mem_write(STACK, bytes([0xa5]) * 4096)
        self.put(STACK + 0x800, '<' + 'I' * (1 + len(args)), STOP, *args)
        self.vm.reg_write(UC_X86_REG_ECX, UI)
        self.vm.reg_write(UC_X86_REG_ESP, STACK + 0x800)
        self.vm.emu_start(entry, STOP, count=10000)
        assert self.vm.reg_read(UC_X86_REG_EIP) == STOP, hex(entry)
        assert self.vm.reg_read(UC_X86_REG_ESP) == STACK + 0x804 + 4 * len(args)


def name(value):
    return value.encode('ascii').ljust(16, b'\0')


def member(identity, value, leader=0, hud=b'\x12\x34\x56\x78'):
    return struct.pack('<HBB', identity, 0, leader) + hud + name(value)


def profession_proof(raw):
    import pefile
    from tools.strike_lab.omega_assets import decode_csvz
    from tools.strike_lab.recover_companions import parse_sections
    from tools.strike_lab.current_dialogue_mode4_native_20260926 import Native, UI as CLASS_UI, PACKET
    exe = (ROOT.parent / 'God2/God2.exe').read_bytes()
    exe_sha = hashlib.sha256(exe).hexdigest()
    assert exe_sha == 'c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
    pe = pefile.PE(data=exe)
    mapped = pe.get_memory_mapped_image()
    # These actual create/event/sender intervals remain identical to qualified native.
    for entry, end in ((0x4097a0, 0x4098d0), (0x40c680, 0x40c7c0),
                       (0x40c0b0, 0x40c160), (0x40c160, 0x40c210)):
        offset = entry - 0x400000
        assert mapped[offset:end - 0x400000] == raw[offset:end - 0x400000]
    source = (ROOT.parent / 'God2/Data2/Patch/Comm/message.csvZ').read_bytes()
    plain = decode_csvz(source)
    rows = parse_sections(plain, ('ProgramMsg',))['ProgramMsg']['records']
    labels = {int(bytes.fromhex(row['fields_hex'][0]).decode('ascii')): bytes.fromhex(row['fields_hex'][1])
              for row in rows[:8]}
    # Source text is not guessed from synthetic pointer strings.
    expected = ['a86bbc43', 'a46bbc43', 'a86ba550', 'a46ba550',
                'a86bbfd1', 'a46bbfd1', 'a86bc3c4', 'a46bc3c4']
    assert [labels[i].hex() for i in range(1, 9)] == expected
    o = Oracle(raw)
    bank, table, strings = 0x32000000, 0x33000000, 0x33001000
    o.vm.mem_map(bank, 0xb4000)
    o.vm.mem_map(table, 0x2000)
    o.put(UI + 0xcff70, '<I', bank)
    o.put(bank + 0xb2c68, '<I', table)
    o.put(bank + 0xb2c6c, '<H', 9)
    for identity in range(1, 10):
        ptr = strings + identity * 16
        o.put(table + (identity - 1) * 4, '<I', ptr)
        o.vm.mem_write(ptr, labels.get(identity, b'') + b'\0')
    o.call(0x4e8e80)
    indices = struct.unpack('<9H', raw[0x5974c8 - 0x400000:0x5974da - 0x400000])
    assert indices == (9, 1, 2, 3, 4, 5, 6, 7, 8)
    for wire in range(1, 9):
        ptr = o.u32(0x5b83b0 + wire * 4)
        assert o.read(ptr, 5) == labels[wire] + b'\0'
    cases = []
    for entry, refresh, sender, builder, opcode in ((0x4097a0, 0x409680, 0x40c0b0, 0x414cf0, 0x17),
                                                  (0x40c680, 0x40c580, 0x40c160, 0x414cc0, 0x1b)):
        for category in range(4):
            for sex in range(2):
                n = Native(pe, [b''])
                profile = bytearray(40)
                profile[0], profile[33] = 65, sex
                n.vm.mem_write(CLASS_UI + 0x15280, bytes(profile))
                n.setup(11 + category, 1)
                n.run(entry, [refresh])
                pre = bytes(n.vm.mem_read(CLASS_UI + 0x15280, 40))
                assert pre[29] == 2 * category + sex
                n.setup(PACKET, PACKET + 4)
                n.run(sender, [builder])
                ptr = n.read(n.reg('ESP') + 4, 'I')
                wire = bytes(n.vm.mem_read(ptr, 40))
                assert wire[29] == 2 * category + sex + 1
                cases.append({'opcode': f'{opcode:02X}', 'category': category, 'sex': sex,
                              'wire29': wire[29], 'party54_label_hex': labels[wire[29]].hex(),
                              'party54_label': labels[wire[29]].decode('cp950')})
    return {'client_sha256': exe_sha, 'source_message_sha256': hashlib.sha256(source).hexdigest(),
            'source_message_plain_sha256': hashlib.sha256(plain).hexdigest(), 'cases': cases,
            'code_anchors': ['004097A0/0040C680 class event', '0040C0B0/0040C160 create sender',
                             '004E8E80 initializes DAT_005B83B0 from WORD indices at005974C8',
                             '004EA8A0 indexes DAT_005B83B0 by payload+18 low nibble'],
            'conclusion': 'Raw persisted create wire profile29 (1..8) is directly the party54 low-nibble profession index: male/female sword,taoist,warlock,pharmacist. High nibble/transfer count provenance remains open.'}


def prove():
    raw = qualified_image()
    profession = profession_proof(raw)
    widths = {f'{op:02X}': NativeLengths(raw).query(op)[0] for op in (0x54, 0x55, 0x56, 0x57, 0x58)}
    assert widths == {'54': 29, '55': 25, '56': 7, '57': 19, '58': 21}, widths
    o = Oracle(raw)
    producer_cases = 0
    for source, target in ((4, 5), (0xabcd1234, 0x7654fedc), (0xffffffff, 0)):
        o.queued.clear()
        o.call(0x497140, source, target)
        assert o.queued == [b'\x6a' + struct.pack('<II', source, target)]
        producer_cases += 1
        o.queued.clear()
        o.call(0x497170, source, target)
        assert o.queued == [b'\x57' + struct.pack('<I', target)]
        producer_cases += 1
    for value in (b'\0' * 4, bytes.fromhex('341201fe'), bytes.fromhex('ffff02a5')):
        o.queued.clear()
        o.call(0x497230, BODY, body=value)
        assert o.queued == [b'\x58' + value]
        producer_cases += 1
    for identity, value in ((4, 'Leader'), (0x1234, 'MixedName123456')):
        o.put(ROOT_ACTOR, '<H', identity)
        o.vm.mem_write(ROOT_ACTOR + 0xb7, name(value))
        o.queued.clear()
        o.call(0x4971b0)
        body = o.queued[0]
        assert body[:3] == b'\x5a' + struct.pack('<H', identity) and len(body) == 19
        assert body[3:3 + len(value) + 1] == value.encode('ascii') + b'\0'
        assert body[3 + len(value) + 1:] == bytes([0xa5]) * (15 - len(value))
        producer_cases += 1
    # Roster consumer itself executes; only presentation helpers are stubbed.
    o.vm.mem_write(ACTOR + 0x27, name('Leader'))
    roster_cases = 0
    o.call(0x4e9bc0, BODY, body=member(4, 'Leader', 1))
    assert o.u32(ACTOR + 0x3f98) == 0
    assert o.read(UI + 0xafeea, 1) == b'\x01' and o.u32(UI + 0xafed0) == 4
    assert o.read(UI + 0xafed4, 7) == b'Leader\0'
    roster_cases += 1
    for index, value in enumerate(('PeerA', 'PeerB', 'PeerC', 'PeerD')):
        body = member(5 + index, value)
        o.call(0x4e9bc0, BODY, body=body)
        assert o.u32(ACTOR + 0x3f98) == index + 1
        assert o.read(ACTOR + 0x3f9c + 24 * index, 24) == body
        roster_cases += 1
    full = o.read(ACTOR + 0x3f98, 100)
    o.call(0x4e9bc0, BODY, body=member(9, 'Overflow'))
    assert o.read(ACTOR + 0x3f98, 100) == full
    roster_cases += 1
    updated = member(15, 'PeerB', 1, b'\xaa\xbb\xcc\xdd')
    o.call(0x4e9bc0, BODY, body=updated)
    assert o.u32(ACTOR + 0x3f98) == 4
    assert o.read(ACTOR + 0x3fb4, 24) == updated
    assert o.u32(UI + 0xafed0) == 15
    roster_cases += 1
    prior_roster = o.read(ACTOR + 0x3f98, 100)
    o.call(0x4e9bc0, BODY, body=member(4, 'Leader', 0))
    assert o.read(UI + 0xafeea, 1) == b'\0'
    assert o.read(ACTOR + 0x3f98, 100) == prior_roster
    roster_cases += 1
    # Position and all four 32-bit vitals remain intact in the native arrays.
    position_cases = vitals_cases = 0
    for index, identity in enumerate((5, 15, 7, 8)):
        pos = struct.pack('<HHH', identity, 120 + index, 220 + index)
        o.call(0x4ea140, BODY, body=pos)
        assert o.read(ACTOR + 0x3ffc + index * 6, 6) == pos
        assert o.read(ACTOR + 0x4068 + index, 1) == b'\1'
        assert o.u32(ACTOR + 0x4070) == 123456
        position_cases += 1
        # Native order: hp, mp, max_hp, max_mp, not hp/max_hp/mp/max_mp.
        vitals = struct.pack('<HHIIII', identity, 0, 0x12340001 + index,
                             0x23450002 + index, 0x34560003 + index, 0x45670004 + index)
        o.call(0x4e9ad0, BODY, body=vitals)
        assert o.read(ACTOR + 0x4014 + index * 20, 20) == vitals
        vitals_cases += 1
    prior = o.read(ACTOR + 0x3ffc, 104)
    o.call(0x4ea140, BODY, body=struct.pack('<HHH', 99, 1, 2))
    o.call(0x4e9ad0, BODY, body=struct.pack('<HHIIII', 99, 0, 1, 2, 3, 4))
    assert o.read(ACTOR + 0x3ffc, 104) == prior
    position_cases += 1
    vitals_cases += 1
    # Removal shifts roster, position and vitals together; remaining actor IDs stay paired.
    o.call(0x4e9eb0, BODY, 0, body=struct.pack('<H', 15) + name('PeerB'))
    assert o.u32(ACTOR + 0x3f98) == 3
    for index, identity in enumerate((5, 7, 8)):
        assert struct.unpack('<H', o.read(ACTOR + 0x3f9c + index * 24, 2))[0] == identity
        assert struct.unpack('<H', o.read(ACTOR + 0x3ffc + index * 6, 2))[0] == identity
        assert struct.unpack('<H', o.read(ACTOR + 0x4014 + index * 20, 2))[0] == identity
    removal_cases = 1
    for identity, value in ((5, 'PeerA'), (7, 'PeerC'), (8, 'PeerD')):
        o.call(0x4e9eb0, BODY, 0, body=struct.pack('<H', identity) + name(value))
        removal_cases += 1
    assert o.u32(ACTOR + 0x3f98) == 0 and o.read(UI + 0xafeea, 1) == b'\0'
    # Execute signed x87 bar arithmetic including real CRT __ftol.
    o.put(UI + 0x232df6, '<h', 1)
    scale, = struct.unpack('<f', raw[0x570fb0 - 0x400000:0x570fb4 - 0x400000])
    assert scale == 100.0
    bar_cases = []
    for entry, control in ((0x4e9990, 20), (0x4e9a30, 24)):
        for current, maximum in ((0, 0), (100, 0), (0, 100), (65536, 100), (100, 65536),
                                 (1, 1), (100, 200), (0x7fff, 0x7fff), (0x8000, 0x7fff),
                                 (0x7fff, 0x8000), (0x8000, 0x8000), (0xffff, 0x7fff),
                                 (0x7fff, 0xffff), (0xffff, 0xffff), (99999, 99999)):
            o.calls.clear()
            o.call(entry, 0, current, maximum)
            bars = [args for addr, args in o.calls if addr == 0x5060f0]
            assert len(bars) == 1 and bars[0][:2] == (1, control)
            signed = lambda v: struct.unpack('<h', struct.pack('<H', v & 0xffff))[0]
            expected = int(signed(current) * scale / signed(maximum)) if signed(maximum) else 0
            got = struct.unpack('<i', struct.pack('<I', bars[0][2]))[0]
            assert got == expected, (entry, current, maximum, got, expected)
            bar_cases.append({'function': f'{entry:08X}', 'current': current, 'maximum': maximum,
                              'percent': got, 'signed_low_word': True})
    return {'native_image_sha256': hashlib.sha256(raw).hexdigest(), 's2c_logical_widths': widths,
            'producer_cases': producer_cases, 'roster_cases': roster_cases,
            'position_cases': position_cases, 'vitals_cases': vitals_cases,
            'removal_cases': removal_cases, 'bar_cases': bar_cases,
            'c2s': {'6A': 'self DWORD,target DWORD', '57': 'target DWORD; self argument ignored',
                    '58': 'raw four bytes preserved', '5A': 'self WORD,name16; bytes after NUL unwritten'},
            's2c_58': 'id WORD,opaque WORD,hp DWORD,mp DWORD,max_hp DWORD,max_mp DWORD',
            'bar_limit': 'Arrays retain DWORD values; bar percentage uses signed low WORD. Large equal values may render 100%; mixed signed ranges may render negative or oversized percentages.',
            'profession_54': profession,
            'transfer_54': 'Byte+19 is consumed; source not recovered; zero is not proven native.',
            'scope': 'Native machine code with external UI/time/queue boundaries stubbed. No service, real client, actor world renderer, screen or network acceptance.',
            'current_client_accepted': False}


if __name__ == '__main__':
    result = prove()
    output = ROOT / 'artifacts/research/native-party-20261002.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
