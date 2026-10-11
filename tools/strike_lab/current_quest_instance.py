"""Pinned current x86: logical 3B record -> storage -> ACTMIS serial read.

Synthetic inputs, original instructions, explicit stop boundaries; no runtime
codec, game-function replacements, file writes, or quest transition claims.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE, UI, VIEW = 0x400000, 0x10000000, 0x20000000
PACKET, STACK, SP, RESOURCE = 0x30000000, 0x40000000, 0x40008000, 0x50000000
SLOTS, SELECTED, DISPLAY = 0x85610, 0x855f0, 0x22928
RETURN = STACK + 0xf000


def evidence(path=IMAGE):
    raw = Path(path).read_bytes()
    qualify(raw)
    return raw


def qualify(raw):
    if hashlib.sha256(raw).hexdigest() != IMAGE_SHA:
        raise ValueError('Pinned image changed; requalification required')


def fixture(slot=0, serial=169, low_word=0x1234, category=20):
    """Adversarial synthetic bytes, not captured item IDs or server truth."""
    if not (0 <= slot <= 255 and 0 <= serial <= 65535
            and 0 <= low_word <= 65535 and 0 <= category <= 63):
        raise ValueError('Fixture field outside native width')
    instance = bytearray(range(20))
    struct.pack_into('<I', instance, 0, category << 16 | low_word)
    struct.pack_into('<H', instance, 8, serial)
    return bytes([0x3b, 0x17, slot, 0xa5, 0x5a]) + instance


class NativeInstance:
    def __init__(self, raw):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
        from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
        from unicorn import x86_const
        qualify(raw)
        self.raw, self.reg = raw, x86_const
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(BASE, (len(raw) + 4095) & ~4095)
        self.vm.mem_write(BASE, raw)
        self.vm.mem_protect(BASE, (len(raw) + 4095) & ~4095,
                            UC_PROT_READ | UC_PROT_EXEC)
        for address, size in ((UI, 0x240000), (VIEW, 0x24000),
                              (PACKET, 4096), (STACK, 0x10000),
                              (RESOURCE, 0xe0000)):
            self.vm.mem_map(address, size)
        self.write(UI + 0xcff70, '<I', RESOURCE)
        self.write(UI + 0x574c0, '<I', VIEW)
        self.write(VIEW + 0x24, '<I', 0)  # Avoid conditional widget call for slots 38..41.
        self.write(VIEW + 0xdc, '<I', UI)
        self.vm.mem_write(UI + SLOTS - 4, b'\xcc' * (50 * 24 + 8))
        self.vm.mem_write(VIEW + DISPLAY - 4, b'\xdd' * 28)
        self.events, self.stops, self.phase = [], set(), None
        self.vm.hook_add(UC_HOOK_CODE, self._code)
        self.vm.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._memory)

    def write(self, address, fmt, *values):
        self.vm.mem_write(address, struct.pack(fmt, *values))

    def read(self, address, fmt):
        return struct.unpack(fmt, self.vm.mem_read(address, struct.calcsize(fmt)))

    def setreg(self, name, value):
        self.vm.reg_write(getattr(self.reg, 'UC_X86_REG_' + name), value)

    def getreg(self, name):
        return self.vm.reg_read(getattr(self.reg, 'UC_X86_REG_' + name))

    def _code(self, vm, address, size, context):
        if address in self.stops:
            vm.emu_stop()
        elif not BASE <= address < BASE + len(self.raw):
            raise AssertionError('Execution escaped pinned image')

    def _memory(self, vm, access, address, size, value, context):
        from unicorn import UC_MEM_WRITE
        for name, start, length in (
                ('packet', PACKET, 4096), ('slots', UI + SLOTS, 50 * 24),
                ('display', VIEW + DISPLAY, 20)):
            if start <= address < start + length:
                self.events.append(dict(phase=self.phase, rva=self.getreg('EIP') - BASE,
                                        access='write' if access == UC_MEM_WRITE else 'read',
                                        region=name, offset=address - start, size=size))
                break

    def run(self, start, *stops):
        self.stops = set(stops)
        self.vm.emu_start(BASE + start, 0, count=20000)
        end = self.getreg('EIP')
        if end not in self.stops:
            raise AssertionError('Native slice exceeded instruction bound')
        return end

    def length(self):
        target = self.read(BASE + 0x1324 + 4 * 0x3b, '<I')[0]
        self.setreg('ESP', SP)
        self.write(SP, '<I', RETURN)
        self.run(target - BASE, RETURN)
        return self.getreg('EAX')

    def ingest(self, packet):
        """Run opcode dispatch and slot guards; stop immediately after copy.

        Input ends at an unmapped page. Invalid slots return to dispatcher join.
        Everything after the copy, including definition lookup, is excluded.
        """
        from unicorn import UC_PROT_READ
        if not 1 <= len(packet) <= 25 or packet[0] != 0x3b:
            raise ValueError('Only nonempty 3B prefixes up to 25 bytes are in scope')
        self.packet_address = PACKET + 4096 - len(packet)
        self.vm.mem_write(self.packet_address, bytes(packet))
        self.vm.mem_protect(PACKET, 4096, UC_PROT_READ)
        self.setreg('ESP', SP)
        self.setreg('EBP', UI - 0xa7f2f6c)
        self.setreg('EBX', self.packet_address)
        self.phase = 'ingest'
        end = self.run(0x68b4e, BASE + 0x98e2d, BASE + 0x6b517)
        return end == BASE + 0x98e2d

    def selection_gate(self, slot, *, control=0x17, flags=0x20,
                       matching_context=True, definition=True, definition_record=None):
        """Original event-to-copy path with explicit inactive widget fixtures.

        Rendering is not emulated: the real widget helpers see an inactive
        widget and an out-of-range render resource. No function is replaced.
        """
        if not -1<=slot<50 or not 0<=control<=65535 or not 0<=flags<=0xffffffff:
            raise ValueError('Selection input outside qualified bounds')
        if definition_record is not None and (not definition or len(definition_record)!=0x18c):
            raise ValueError('Expected complete native item definition')
        definition_address=RESOURCE+0x4000
        if definition_record is not None:
            self.vm.mem_write(definition_address,bytes(definition_record))
        self.write(UI+SELECTED,'<h',slot)
        self.write(UI+0x8688c,'<I',RESOURCE+0x180)
        self.write(RESOURCE+0x180,'<I',7)
        self.write(VIEW+0x22900,'<I',7 if matching_context else 8)
        self.write(UI+0x232dc8,'<h',0)
        self.write(UI+0xe2170+8,'<I',RESOURCE+0x2000)
        self.write(UI+0xe2170+0x818,'<H',0)
        self.write(UI+0xe2170+0x81c,'<H',0)
        self.write(RESOURCE+0x2000+0x1e,'<H',0xffff)
        if slot>=0:
            key=self.read(UI+SLOTS+24*slot,'<H')[0]
            if key<0x7f58:
                self.write(RESOURCE+0xb2d40+key*4,'<I',definition_address if definition else 0)
        self.setreg('ECX',VIEW)
        self.setreg('ESP',SP)
        self.write(SP,'<III',RETURN,control,flags)
        self.phase='selection_gate'
        end=self.run(0x91390,BASE+0x91431,BASE+0x91494,BASE+0x914dc,RETURN)
        return {'stop_rva':end-BASE if end!=RETURN else None,
                'copied':end==BASE+0x91431,'returned':end==RETURN}

    def forward(self, slot, low_word):
        """Execute known UI copy and wrapper, then bounded tooltip slices."""
        if not 0 <= slot < 50 or not 0 <= low_word < 0x7f58:
            raise ValueError('Forward fixture outside tested slot/lookup bounds')
        header = self.read(UI + SLOTS + 24 * slot, '<I')[0]
        if header & 0xffff != low_word or (header >> 16) & 63 != 20:
            raise ValueError('Forward slice requires category 20 and matching lookup key')
        self.write(UI + SELECTED, '<h', slot)
        self.setreg('EBX', VIEW)
        self.setreg('ESP', SP)
        self.phase = 'display_copy'
        self.run(0x9140b, BASE + 0x91431)
        # Real lookup runs against a synthetic nonnull definition pointer.
        self.write(RESOURCE + 0xb2d40 + low_word * 4, '<I', RESOURCE + 0x100)
        self.setreg('EBX', VIEW)
        self.setreg('ESP', SP)
        self.phase = 'tooltip_caller'
        self.run(0x90a11, BASE + 0xb5be0)
        tooltip_sp = self.getreg('ESP')
        argument = self.read(tooltip_sp + 24, '<I')[0]
        self.run(0xb5be0, BASE + 0xb5c11)
        frame_pointer = self.read(self.getreg('ESP') + 0x11ac, '<I')[0]
        if argument != VIEW + DISPLAY or frame_pointer != argument:
            raise AssertionError('Native tooltip instance pointer changed')
        # Skip title/render/cache work. Keep the native prologue stack and EBP.
        self.setreg('EAX', self.read(argument, '<I')[0])
        self.phase = 'serial_read'
        self.run(0xb6424, BASE + 0xb9f9e)
        return dict(instance_pointer=argument, serial=self.getreg('EDX') & 0xffff,
                    tooltip_frame_pointer=frame_pointer)


def build_report(path=IMAGE):
    native = NativeInstance(evidence(path))
    packet = fixture(slot=7)
    if native.length() != 25 or not native.ingest(packet):
        raise AssertionError('Native length/ingest contract changed')
    storage = bytes(native.vm.mem_read(UI + SLOTS + 24 * 7, 20))
    result = native.forward(7, 0x1234)
    if storage != packet[5:] or result['serial'] != 169:
        raise AssertionError('Native writer/reader binding failed')
    return dict(schema='current-quest-instance-v1', image_sha256=IMAGE_SHA,
                logical_opcode=0x3b, logical_length=25, fixture_hex=packet.hex(),
                storage_hex=storage.hex(), result=result, events=native.events,
                proven='logical.u16[13] -> UI+85610+24*slot+8 -> '
                       'view+22928+8 -> B9F9A ACTMIS serial read',
                boundary='Synthetic logical input; stop after storage copy. '
                         'UI copy starts after earlier eligibility checks. '
                         'Tooltip title/cache/render code is excluded.',
                open='Original server serial selection, transport/live acceptance, '
                     'category-20 UI reachability before 9140B, turn-in and rewards')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=IMAGE)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    report = build_report(args.image)
    if not args.json:
        report = {k: v for k, v in report.items() if k != 'events'}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
