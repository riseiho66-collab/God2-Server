"""Current S2C02 equipment-refusal presentation, original native callees.

Offline fixture only. No server/game process, no DB changes, no game callee
stubs. A source-backed refusal message is not an operation-success response.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_equipment_projection_20260926 import (
    Oracle, NativeItemMetadata, ROOT, PIN, require, pefile, UI, SLOTS,
    DEFINITIONS, PACKET, BASE, SP, RETURN, UC_PROT_READ, UC_PROT_WRITE)
from .omega_assets import decode_csvz
from unicorn import x86_const as x

MESSAGE_SHA = '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
DECODED_SHA = '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'
CATALOG, VISIBLE, ROLE = 0x66000000, 0x66100000, 0x66200000


def cstring(vm, address, limit=512):
    raw = bytes(vm.mem_read(address, limit))
    require(b'\0' in raw, 'Unterminated native text')
    return raw.split(b'\0', 1)[0]


def source():
    raw = (ROOT.parent/'God2/Data2/Patch/Comm/message.csvZ').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == MESSAGE_SHA, 'Message source SHA')
    plain = decode_csvz(raw)
    require(hashlib.sha256(plain).hexdigest() == DECODED_SHA, 'Decoded message SHA')
    lines = plain.splitlines()
    start = lines.index(b'SystemMessage,1950')
    row = lines[start+27]
    parts = row.split(b',')
    require(parts[:2] == [b'27', b'1'], 'Message27 identity/display mode')
    require(parts[2] == '%s 無法使用或裝備。'.encode('cp950'), 'Message27 text')
    return parts[2], dict(source_sha256=MESSAGE_SHA, decoded_sha256=DECODED_SHA,
                         line=start+28, raw_row_hex=row.hex(), row_sha256=hashlib.sha256(row).hexdigest())


class RejectionOracle(Oracle):
    def __init__(self, image, definitions, template):
        self.formatted = []
        super().__init__(image, definitions)
        v = self.vm
        for address, size in ((CATALOG, 0x20000), (VISIBLE, 0x7000), (ROLE, 0x5000)):
            v.mem_map(address, size)
        # Relocation of a pinned source row, not execution of its CSV loader.
        v.mem_write(CATALOG+0x10000, template+b'\0')
        v.mem_write(CATALOG+26*16, struct.pack('<IIII', 1, *([CATALOG+0x10000]*3)))
        v.mem_protect(CATALOG, 0x20000, UC_PROT_READ)
        v.mem_protect(DEFINITIONS, 0xe0000, UC_PROT_READ|UC_PROT_WRITE)
        v.mem_write(DEFINITIONS+0xb2c60, struct.pack('<IH', CATALOG, 1950))
        v.mem_protect(DEFINITIONS, 0xe0000, UC_PROT_READ)
        v.mem_write(UI+0x39de8, struct.pack('<I', VISIBLE))
        v.mem_write(UI+0x86888, struct.pack('<I', ROLE))
        v.mem_write(UI+0x232e10, b'\xff\xff')
        v.mem_write(UI+0x232db6, b'\xff\xff')
        # Real handler executes refresh with absent widget (native sentinel).
        v.mem_write(BASE+0x1b63bc, struct.pack('<I', 10))

    def observe(self, v, address, size, context):
        super().observe(v, address, size, context)
        if address == 0x47de00:
            sp = v.reg_read(x.UC_X86_REG_ESP)
            channel, color, text = struct.unpack('<III', v.mem_read(sp+4, 12))
            self.formatted.append((channel, color, cstring(v, text)))

    def reset_chat(self, private):
        self.vm.mem_write(VISIBLE, bytes(0x6800))
        self.vm.mem_write(UI+0x39e20, bytes(0x6800))
        self.vm.mem_write(UI+0x39e18, bytes([private]))
        self.vm.mem_write(UI+0x39df6, bytes(2))
        self.formatted.clear()

    def ring(self, address):
        v = self.vm
        count, oldest, next_write = struct.unpack('<III', v.mem_read(address+0x67e8, 12))
        require(count <= 200 and oldest < 200 and next_write < 200, 'Chat ring bounds')
        rows = []
        for i in range(count):
            physical = (oldest+i) % 200
            rows.append(dict(physical_index=physical,
                raw_hex=cstring(v, address+physical*128, 128).hex(),
                channel=v.mem_read(address+0x6400+physical, 1)[0],
                color=struct.unpack('<I', v.mem_read(address+0x64c8+4*physical, 4))[0]))
        return dict(count=count, oldest=oldest, next_write=next_write, rows=rows)


def verify():
    raw = (ROOT.parent/'God2/God2.exe').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PIN, 'Current PE SHA')
    image = pefile.PE(data=raw).get_memory_mapped_image()
    require(image[0x1234:0x123a] == bytes.fromhex('b817000000c3'), 'Native logical length23')
    require(struct.unpack_from('<I', image, 0x1324+8)[0] == 0x401234, 'Opcode02 length dispatch')
    template, pin = source()
    loader = NativeItemMetadata()
    require(all(image[a:b] == loader.image[a:b] for a, b in loader.CODE), 'Definition parser current-code match')
    definitions = {key: loader.item_row('WPN' if key < 19000 else 'TWP', key-1 if key < 19000 else key-19001)
                   for key in (1, 2, 19071, 19072)}
    n = RejectionOracle(image, definitions, template)
    n.put(1, bytes.fromhex('0100010000000018000000000600000000000000'))
    cases = []
    for private in (0, 1):
        for key in definitions:
            for selector in (0, 0x80):
                n.reset_chat(private)
                n.set_pending(1)
                before = bytes(n.vm.mem_read(SLOTS, 1200))
                role = bytes(n.vm.mem_read(ROLE, 0x5000))
                logical = struct.pack('<BHH', 2, 27, key)+bytes(16)+bytes([selector, 0xa5])
                require(len(logical) == 23, 'Logical width')
                n.vm.mem_write(PACKET, logical)
                # Execute the actual world case through its native consumer and
                # all callees, stopping only at the enclosing switch join.
                n.vm.reg_write(x.UC_X86_REG_EBP, UI-0xa7f2f6c)
                n.vm.reg_write(x.UC_X86_REG_EBX, PACKET)
                n.vm.reg_write(x.UC_X86_REG_ESP, SP)
                n.vm.emu_start(0x46929e, 0x46b517, count=500000)
                require(n.vm.reg_read(x.UC_X86_REG_EIP) == 0x46b517, 'World consumer return/budget')
                require(n.vm.reg_read(x.UC_X86_REG_ESP) == SP, 'World case stack')
                name = definitions[key]['record'][8:].split(b'\0', 1)[0]
                expected = template.replace(b'%s', b'/c3'+name+b'/c9')
                require(n.formatted == [(4, 0xff80ff, expected)], 'Native formatted message')
                require(n.pending() == 1 and bytes(n.vm.mem_read(SLOTS, 1200)) == before, 'Refusal changed inventory/pending')
                require(bytes(n.vm.mem_read(ROLE, 0x5000)) == role, 'Refusal changed role')
                archive, visible = n.ring(UI+0x39e20), n.ring(VISIBLE)
                require(archive['count'] > 0 and all(r['channel'] == 4 and r['color'] == 0xff80ff for r in archive['rows']), 'Archive channel/color')
                require(archive['count'] == 1 and archive['rows'][0]['raw_hex'] == (b'1A4'+expected).hex(), 'Exact source-backed chat bytes')
                require(visible == archive if private == 0 else visible['count'] == 0, 'Visible/private chat delivery')
                next_request = n.ui_request(1)
                cases.append(dict(item_key=key, private_chat=private, selector=selector,
                    logical_hex=logical.hex(), formatted_cp950_hex=expected.hex(),
                    archive=archive, visible=visible, pending_after=1, next_legal_request=next_request))
    guards = []
    for message, selector in ((0, 0), (1951, 0), (27, 3), (27, 0xff)):
        n.reset_chat(0)
        n.vm.mem_write(PACKET, struct.pack('<HH', message, 1)+bytes(16)+bytes([selector, 0]))
        n.call(0x84e00, PACKET, budget=500000)
        require(not n.formatted and n.ring(UI+0x39e20)['count'] == 0, 'Invalid message produced output')
        guards.append(dict(message=message, selector=selector))
    require({0x84e00, 0x84ae0, 0x7de00, 0x5ff00, 0x7e380, 0x15ad0, 0x147af7}.issubset(n.pcs), 'Native callee coverage')
    prefix = cstring(n.vm, BASE+0x18ebe8+4*4)
    require(prefix == b'1A4', 'Channel4 prefix')
    return dict(status='PASS', current_pe_sha256=PIN, message_source=pin,
        cases=cases, guard_cases=guards, counts={'world_refusals':len(cases), 'guards':len(guards)},
        channel4_prefix_hex=prefix.hex(), native_callee_stubs=0,
        scope='Complete original world case02 through formatter, archive and normal visible ring, refresh with absent widget sentinel; retry cached28. Source-row relocation and synthetic state. No actual display-device/client/server acceptance.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix+'.pending')
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(args.output)
    print(json.dumps(result if not args.output else {'status':result['status'], 'counts':result['counts'], 'output':str(args.output)}, ensure_ascii=False))
