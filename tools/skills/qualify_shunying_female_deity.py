"""Bounded original x86 deity appearance prefixes; no process or DB writes."""
import hashlib
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_EDI
from tools.strike_lab.omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
WORLD, STACK, INPUT = 0x20000000, 0x2000000, 0x3000000


def qualify_battle_attachment(image):
    """Real reset->mode0 using explicitly cached ROM handles; no fake actors.

    Cached handles are memory fixtures, not rendered-resource acceptance.
    Native file lookup is separately checked against actual source rows/files.
    """
    battle, renderer, stop = 0x20000000, 0x4000000, 0x1000000
    manager = battle + 0x144938
    arena, attachments = manager + 0xa7fbdac, manager + 0xa89738c
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(0x400000, (len(image) + 4095) & ~4095)
    vm.mem_write(0x400000, image)
    for address, size in ((STACK, 0x10000), (INPUT, 0x1000), (stop, 0x1000),
                          (battle, 0x1000), (battle + 0xd0000, 0x64000),
                          (manager & ~4095, 0x2000), (arena & ~4095, 0x9e000)):
        vm.mem_map(address, size)
    vm.mem_write(manager + 0xc, struct.pack('<I', renderer))
    # Explicit already-initialized cwd cache. Only CRT sprintf is adapted;
    # no game routine or resource resolver is replaced.
    vm.mem_write(0x59ddf0, bytes(4))
    vm.mem_write(0x5b93c4, b'C:\\native-fixture\0')
    def cstring(pointer):
        out = bytearray()
        for index in range(1024):
            value = vm.mem_read(pointer + index, 1)[0]
            if value == 0:
                return bytes(out)
            out.append(value)
        raise AssertionError('Bounded native string exceeded')
    def crt(v, address, size, _):
        sp = v.reg_read(UC_X86_REG_ESP)
        ret, dest, fmt, first, second = struct.unpack('<5I', v.mem_read(sp, 20))
        if cstring(fmt) != b'%s%s':
            raise AssertionError('Unexpected CRT format')
        data = cstring(first) + cstring(second)
        v.mem_write(dest, data + b'\0')
        v.reg_write(UC_X86_REG_EAX, len(data))
        v.reg_write(UC_X86_REG_ESP, sp + 4)
        v.reg_write(UC_X86_REG_EIP, ret)
    vm.hook_add(UC_HOOK_CODE, crt, begin=0x547af7, end=0x547af7)
    def call(address, this, args=()):
        sp = STACK + 0x8000
        vm.mem_write(sp, struct.pack('<' + 'I' * (1 + len(args)), stop, *args))
        vm.reg_write(UC_X86_REG_ESP, sp)
        vm.reg_write(UC_X86_REG_ECX, this)
        try:
            vm.emu_start(address, stop, timeout=3000000, count=3000000)
        except Exception as error:
            sp_now = vm.reg_read(UC_X86_REG_ESP)
            raise AssertionError(f'Native {address:x} stopped at {vm.reg_read(UC_X86_REG_EIP):x}; stack={bytes(vm.mem_read(sp_now,24)).hex()}') from error
        if vm.reg_read(UC_X86_REG_EIP) != stop:
            raise AssertionError('Native battle call budget exhausted')
    call(0x51fc40, manager)
    rows = []
    for side in (0, 1):
        slot = 0
        actor4 = arena + ((side * 14 + slot) * 6 + 4) * 0xecc
        attachment = struct.unpack('<I', vm.mem_read(actor4 + 0xec8, 4))[0]
        expected = attachments + (side * 14 + slot) * 0x2c
        if attachment != expected:
            raise AssertionError('Reset did not construct type4 companion attachment')
        paths = []
        for component, sex, handle, file in ((0, 1, 50, 'god1400.romz' if side == 0 else 'god5400.romz'),
                                           (1, 1, 51, 'god1500.romz' if side == 0 else 'god5500.romz'),
                                           (2, 0, 52, 'god1200.romz' if side == 0 else 'god5200.romz')):
            table = battle + 0xd0ce4 + 4 + side * 0x30d2c
            row = table + 0x121ec + ((sex * 4 + component) * 60) * 262
            vm.mem_write(row, struct.pack('<H', handle) + file.encode('ascii') + b'\0')
            call(0x51d1c0, battle + 0xd0ce4, (side, sex, component, 0))
            if vm.reg_read(UC_X86_REG_EAX) != row + 2:
                raise AssertionError('Native GodDoll path lookup mismatch')
            raw = (ROOT.parent / 'God2/Data/Fight/GodDoll' / file).read_bytes()
            paths.append(dict(component=component, sex=sex, path=file, sha256=hashlib.sha256(raw).hexdigest()))
        # Real mode0 consumes record at logical86+1; type4 is an attachment
        # to the player's slot, not a seventh battle actor or enemy identity.
        packet = bytes((0x86, 4, side * 14, 0, 0x81, 0x81, 1, 0)) + bytes(9)
        vm.mem_write(INPUT, packet)
        call(0x5177c0, battle, (INPUT + 1,))
        cached = struct.unpack('<4h', vm.mem_read(attachment + 0x1a, 8))
        if cached != (50, 51, 52, -1):
            raise AssertionError(f'Native female component attachment mismatch: {cached}')
        rows.append(dict(side=side, packet_hex=packet.hex(), attachment=hex(attachment),
                         component_handles=cached, sources=paths))
    # Qualify the original subtype7 packet decoder independently from renderer
    # execution. Existing sprite1 is an explicit memory fixture which takes
    # the native already-created branch; it is NOT a visual-render result.
    actor0 = arena
    actor4 = arena + 4 * 0xecc
    attachment = attachments
    vm.mem_write(attachment + 6, struct.pack('<H', 1))
    vm.mem_write(actor0 + 0x1a, struct.pack('<H', 1))
    vm.mem_write(battle + 0x51, b'\xff')  # Exclude local UI-only refresh path.
    summon = bytes.fromhex('830700000001000000660000000000')
    vm.mem_write(INPUT, summon)
    sp = STACK + 0x8000
    vm.mem_write(sp, bytes(0x200))
    vm.mem_write(sp + 0x148, struct.pack('<I', INPUT))
    vm.reg_write(UC_X86_REG_ESP, sp)
    vm.reg_write(UC_X86_REG_ESI, battle)
    vm.emu_start(0x516bb1, 0x5169f0, timeout=1000000, count=10000)
    if vm.reg_read(UC_X86_REG_EIP) != 0x5169f0:
        raise AssertionError('Summon packet did not reach native action dispatch')
    if struct.unpack('<H', vm.mem_read(actor0 + 0x2e, 2))[0] != 0x200:
        raise AssertionError('Native named-deity composite marker missing')
    if struct.unpack('<I', vm.mem_read(actor0 + 0xdb4, 4))[0] & 0x3ff != 102:
        raise AssertionError('Native named-deity key mismatch')
    # Actual original action queue copies subtype7 packed key into player+286.
    call(0x52c520, manager, (INPUT + 1, 0, 0, 0, 0))
    if struct.unpack('<H', vm.mem_read(actor0 + 0x286, 2))[0] != 102:
        raise AssertionError('Original summon action did not retain key102')
    if vm.mem_read(actor0 + 0x1ea, 1) != b'\x89':
        raise AssertionError('Original summon action state mismatch')
    # Renderer-ready frame boundary: the original frame handler propagates
    # the composite marker to the existing type4 attachment. We stop before
    # renderer operations, so no animation frame completion is fabricated.
    vm.reg_write(UC_X86_REG_EDI, actor0)
    vm.reg_write(UC_X86_REG_ESI, actor4)
    vm.emu_start(0x5276c7, 0x5276d8, timeout=1000000, count=100)
    if struct.unpack('<H', vm.mem_read(actor4 + 0x24, 2))[0] != 0x200:
        raise AssertionError('Original frame did not select composite deity')
    sp = STACK + 0x8000
    vm.mem_write(sp, struct.pack('<III', stop, actor4, 0))
    vm.reg_write(UC_X86_REG_ESP, sp)
    vm.reg_write(UC_X86_REG_ECX, manager)
    vm.emu_start(0x529f30, 0x51cc80, timeout=1000000, count=100)
    if vm.reg_read(UC_X86_REG_EIP) != 0x51cc80 or vm.reg_read(UC_X86_REG_ECX) != attachment:
        raise AssertionError('Original summon did not select composite sprite creator')
    return dict(status='PASS', cases=rows,
                summon=dict(packet_hex=summon.hex(), named_key=102, composite_marker=512,
                            action_state=137, sprite_creator='0x51CC80',
                            scope='Original packet decoder/action queue and separated renderer-ready frame prefix; actual renderer and animation timing not executed.'),
                scope='Original51FC40 reset constructs all type4 contexts; original5177C0 mode0 binds cached GodDoll handles. Cached handles are explicit fixtures, actual rendering not executed.')


def qualify():
    image = IMAGE.read_bytes()
    if hashlib.sha256(image).hexdigest() != PIN:
        raise ValueError('Native image mismatch')
    results = []
    for opcode in (0x36, 0x37):
        for key in range(101, 109):
            vm = Uc(UC_ARCH_X86, UC_MODE_32)
            vm.mem_map(0x400000, (len(image) + 4095) & ~4095)
            vm.mem_write(0x400000, image)
            for address, size in ((STACK, 0x10000), (INPUT, 0x1000), (WORLD + 0x15396000, 0x6000)):
                vm.mem_map(address, size)
            packet = bytes((opcode, 1, 1, 1, 0, key, 0, 6, 0, 0, 0))
            vm.mem_write(INPUT, packet)
            vm.mem_write(WORLD + 0x1539683c, struct.pack('<I', 6))
            vm.reg_write(UC_X86_REG_EBP, WORLD)
            vm.reg_write(UC_X86_REG_EBX, INPUT)
            vm.reg_write(UC_X86_REG_ESP, STACK + 0x8000)
            def step(v, address, size, _):
                if address == 0x4614a0:
                    v.emu_stop()
                    return
                if not (0x469c09 <= address < 0x469d03 or 0x5038a0 <= address < 0x50390e):
                    raise AssertionError(f'Unqualified execution {address:x}')
            vm.hook_add(UC_HOOK_CODE, step)
            entry = struct.unpack_from('<I', image, 0x6b5d4 + 4 * opcode)[0]
            vm.emu_start(entry, 0, timeout=1000000, count=500)
            if vm.reg_read(UC_X86_REG_EIP) != 0x4614a0:
                raise AssertionError('Native resolver boundary not reached')
            stack = vm.reg_read(UC_X86_REG_ESP)
            pointer, bank, output = struct.unpack('<III', vm.mem_read(stack + 4, 12))
            if pointer != INPUT + 1 or (bank & 255) != ((key - 99) & 1):
                raise AssertionError('Native deity sex/resource argument mismatch')
            results.append(dict(opcode=opcode, key=key, bank=bank & 255, resolver_pointer_offset=1))
    # Native CSV loader scans r2 as integer2 then decrements to sex bank1.
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    vm.mem_map(0x400000, (len(image) + 4095) & ~4095)
    vm.mem_write(0x400000, image)
    vm.mem_map(STACK, 0x10000)
    vm.reg_write(UC_X86_REG_ESP, STACK + 0x8000)
    vm.reg_write(UC_X86_REG_EAX, 2)
    vm.emu_start(0x455374, 0x4553a1, timeout=1000000, count=100)
    if struct.unpack('<I', vm.mem_read(STACK + 0x8014, 4))[0] != 1:
        raise AssertionError('Original r2 selector is not bank1')
    sources = []
    definitions = (
        ('Data/Patch/GodDoll.csvZ', '768c3a68cddd1443c5c19207a21b17d00990e596aedd74d27f13d0bde5ef02df'),
        ('Data/Patch/FightGodDoll01.csvZ', 'f463dea42b2f310e264f3e5eba4c35ec7ab84d3f709205a6348e1f176e6e4ee9'),
        ('Data/Patch/FightGodDoll05.csvZ', '3d4a9eb66503a28cdae9c1f306d2517b49a12013936a045b0008fd755a623b22'),
    )
    for path, pin in definitions:
        raw = (ROOT.parent / 'God2' / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin:
            raise ValueError('Original GodDoll CSV mismatch')
        lines = decode_csvz(raw).decode('cp950').splitlines()
        if 'r2,女' not in lines:
            raise AssertionError('Female source label missing')
        rows = [dict(line=n, text=line) for n, line in enumerate(lines, 1)
                if line.startswith(('r2,h00,', 'r2,b00,', 'r0,w00,'))]
        sources.append(dict(path=path, sha256=pin, rows=rows))
    return dict(status='PASS', native_image_sha256=PIN, cases=results,
                battle_attachment=qualify_battle_attachment(image),
                female_named_key=102, csv_r2_bank=1, sources=sources,
                scope='Original36/37 resolver prefixes, CSV r2 conversion, battle type4 attachment loading and summon action prefixes. Cached handles are explicit fixtures; actual ROM rendering and frame timing are not executed.')


if __name__ == '__main__':
    print(json.dumps(qualify(), ensure_ascii=True, indent=2))
