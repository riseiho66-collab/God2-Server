"""Current native NPC mission dialogue -> bounded 85 request producer.

Offline original x86, explicit synthetic state, no replacement game functions.
This is a request contract, not authoritative quest acceptance/completion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE, UI, RESOURCE, TABLE = 0x400000, 0x10000000, 0x20000000, 0x20100000
PACKET, STACK, SP, QUEUE = 0x30000000, 0x40000000, 0x40008000, 0x50000000
RETURN = STACK + 0xf000
GLOBALS = BASE + 0x1b7bec
MODE, CHOICE, THRESHOLD, CONTEXT = 0xccc1c, 0xccc20, 0xccd32, 0xccd36
QUEUE_COUNT, QUEUE_BYTES = 0x36c4, 0x36c8
OPEN = ('Original server construction of 7A request/reply words and context; '
        'server dispatch/validation of 85; ACTMIS ownership/consumption, '
        'acceptance, completion, prerequisites, rewards and persistence. '
        'Next native anchors: C7F10 inbound, C8780/C8920 page production, '
        '97DC0 request and 13370 transport flush. No live playable proof.')


def evidence(path=IMAGE):
    raw = Path(path).read_bytes()
    qualify(raw)
    return raw


def qualify(raw):
    if hashlib.sha256(raw).hexdigest() != IMAGE_SHA:
        raise ValueError('Pinned image changed; requalification required')


def fixture(*, request_word, reply_word, context_byte):
    """Synthetic mode-1 input to the decoded-record dispatcher, not wire framing.

    The first payload word is opaque here: 27 is a fixture value, not a
    recovered variable-length framing formula. No text substitution is used.
    """
    if not (0 <= request_word <= 65535 and 0 <= reply_word <= 65535
            and 0 <= context_byte <= 255):
        raise ValueError('Field outside native width')
    return b'\x7a' + struct.pack('<HBBHHH16s', 27, 1, context_byte,
                                request_word, 1, reply_word, bytes(16))


class NativeAction:
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
        # Native globals are data, not patched instructions; only these pages write.
        self.vm.mem_protect(BASE + 0x1b5000, 4096, 3)
        self.vm.mem_protect(BASE + 0x1b7000, 4096, 3)
        for address, size in ((UI, 0x240000), (RESOURCE, 0xe0000),
                              (TABLE, 4096), (PACKET, 4096),
                              (STACK, 0x10000), (QUEUE, 0x5000)):
            self.vm.mem_map(address, size)
        self.write(UI + 0xcff70, '<I', RESOURCE)
        self.write(UI + 0x86874, '<I', QUEUE)
        self.write(UI + 0x232dee, '<h', 0)
        self.write(RESOURCE + 0xb2c48, '<h', 1)
        self.write(RESOURCE + 0xb2c4c, '<I', TABLE)
        # Synthetic pointer table selects the pinned native empty string.
        self.write(TABLE, '<I', BASE + 0x1b4640)
        self.vm.mem_protect(RESOURCE, 0xe0000, UC_PROT_READ)
        self.vm.mem_protect(TABLE, 4096, UC_PROT_READ)
        self.vm.mem_write(QUEUE + QUEUE_BYTES, b'\xcc' * (0xa00 + 8))
        self.events, self.calls, self.stops = [], [], set()
        self.phase, self.tail_before = None, None
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
            return
        if not BASE <= address < BASE + len(self.raw):
            raise AssertionError('Execution escaped pinned image')
        if address == BASE + 0x97dc0:
            self.tail_before = self.read(self.getreg('ESP') - 3, '<B')[0]
        if address == BASE + 0x132e0:
            _, opcode, pointer, length = self.read(self.getreg('ESP'), '<4I')
            self.calls.append(dict(opcode=opcode, payload_pointer=pointer,
                                   payload_length=length,
                                   payload_hex=bytes(vm.mem_read(pointer, length)).hex(),
                                   tail_before=self.tail_before))

    def _memory(self, vm, access, address, size, value, context):
        from unicorn import UC_MEM_WRITE
        for region, start, length in (
                ('packet', PACKET, 4096), ('ui', UI, 0x240000),
                ('globals', GLOBALS, 16), ('table', TABLE, 4096),
                ('queue', QUEUE + QUEUE_COUNT, 0xa10),
                ('stack', SP - 0x1000, 0x1100)):
            if start <= address < start + length:
                self.events.append(dict(phase=self.phase, rva=self.getreg('EIP') - BASE,
                                        access='write' if access == UC_MEM_WRITE else 'read',
                                        region=region, offset=address - start, size=size))
                break

    def run(self, start, *stops):
        self.stops = set(stops)
        self.vm.emu_start(BASE + start, 0, count=20000)
        end = self.getreg('EIP')
        if end not in self.stops:
            raise AssertionError('Native slice exceeded instruction bound')
        return end

    def ingest(self, packet):
        """7A dispatch through mode-1 NPCMissionMessage reference to header setup.

        The NPCMissionMessage table is synthetic. Formatting/render/page
        production is excluded, with native global setup stopped at C8234.
        Short prefixes are allowed solely for unmapped-read boundary probes.
        """
        from unicorn import UC_PROT_READ
        if not 1 <= len(packet) <= 27 or packet[0] != 0x7a:
            raise ValueError('Only 7A prefixes up to 27 bytes are in scope')
        if len(packet) > 3 and packet[3] != 1:
            raise ValueError('Only mode-1 inbound slice is qualified')
        self.packet_address = PACKET + 4096 - len(packet)
        self.vm.mem_write(self.packet_address, bytes(packet))
        self.vm.mem_protect(PACKET, 4096, UC_PROT_READ)
        self.setreg('ESP', SP)
        self.setreg('EBP', UI - 0xa7f2f6c)
        self.setreg('EBX', self.packet_address)
        self.phase = 'incoming'
        end = self.run(0x68b4e, BASE + 0xc8234, BASE + 0x6b517,
                       BASE + 0x2c70)
        return dict(stop_rva=end - BASE, mode=self.read(UI + MODE, '<H')[0],
                    context_byte=self.read(UI + CONTEXT, '<B')[0],
                    normalized_reply_word=self.read(GLOBALS + 12, '<H')[0],
                    request_word=self.read(GLOBALS + 14, '<H')[0],
                    high_bit_flag=self.read(GLOBALS, '<I')[0])

    def action(self, *, page, page_count, mode, threshold, choice,
               stack_byte, queued_count, lock_pointer):
        """Explicit post-render state -> original C8500 -> original queue append.

        Opaque request/reply/context fields remain from ingest(). Mode, page,
        choice and transport object state are explicit synthetic inputs. Stop
        before UI close/error/flush/lock work, never substitute their returns.
        """
        if not (-0x80000000 <= page < 0x80000000
                and -0x80000000 <= page_count < 0x80000000
                and 0 <= mode <= 65535 and -32768 <= threshold <= 32767
                and -32768 <= choice <= 32767 and 0 <= stack_byte <= 255
                and 0 <= queued_count <= 0xa00 and 0 <= lock_pointer <= 0xffffffff):
            raise ValueError('State outside bounded native widths')
        self.write(GLOBALS + 4, '<ii', page, page_count)
        self.write(UI + MODE, '<H', mode)
        self.write(UI + THRESHOLD, '<h', threshold)
        self.write(UI + CHOICE, '<h', choice)
        self.write(UI + 0xaff04, '<I', 0x12345678)
        self.write(QUEUE + QUEUE_COUNT, '<I', queued_count)
        self.write(QUEUE + 0x40d4, '<I', lock_pointer)
        self.vm.mem_write(STACK, bytes([stack_byte]) * 0xf000)
        self.write(SP, '<I', RETURN)
        self.setreg('ECX', UI)
        self.setreg('ESP', SP)
        self.phase, self.calls, self.tail_before = 'action', [], None
        end = self.run(0xc8500, RETURN, BASE + 0xc8350, BASE + 0x75d60,
                       BASE + 0x13370, BASE + 0x11970, BASE + 0x11990)
        after = self.read(QUEUE + QUEUE_COUNT, '<I')[0]
        return dict(stop_rva=None if end == RETURN else end - BASE,
                    returned=end == RETURN, calls=self.calls.copy(),
                    queue_count_before=queued_count, queue_count_after=after,
                    appended_hex=bytes(self.vm.mem_read(
                        QUEUE + QUEUE_BYTES + queued_count, max(0, after - queued_count))).hex(),
                    action_state=self.read(UI + 0xaff04, '<I')[0],
                    high_bit_flag=self.read(GLOBALS, '<I')[0], esp=self.getreg('ESP'))


def build_report(path=IMAGE):
    n = NativeAction(evidence(path))
    packet = fixture(request_word=0x1234, reply_word=0x8002, context_byte=0x9a)
    incoming = n.ingest(packet)
    result = n.action(page=0, page_count=1, mode=1, threshold=0, choice=-1,
                      stack_byte=0xa5, queued_count=0, lock_pointer=0)
    if (incoming['stop_rva'] != 0xc8234 or result['appended_hex'] != '85341202009aa5'
            or result['action_state'] != 1):
        raise AssertionError('Native request contract changed')
    return dict(schema='current-quest-action-v1', image_sha256=IMAGE_SHA,
                fixture_hex=packet.hex(), incoming=incoming, action=result,
                events=n.events, contract='7A mode-1 NPCMissionMessage state -> '
                'C8500 -> 97DC0 -> opcode 85, six payload bytes -> 132E0 queue',
                boundary='Synthetic resource/page/UI/queue state; stop before rendering, '
                'close, errors, locks or transport flush. Sixth payload byte is untouched '
                'stack memory, not zero padding or a recovered field.', open=OPEN)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=IMAGE)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    report = build_report(args.image)
    if not args.json:
        report.pop('events')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
