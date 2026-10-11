"""Pinned current x86 close/action sequences; request evidence, not quest rules.

Extends NativeAction without replacing game callees. Synthetic empty UI backing
permits bounded cleanup; populated UI, locks and transport remain explicit stops.
"""
import argparse
import json
from pathlib import Path

from tools.strike_lab import current_quest_action as q

BACKING = 0x60000000
SOURCE = BACKING + 0x800
ACTIVE, ACTION_STATE, WIDGET = 0xaff00, 0xaff04, 0x232dee
LIST = 0xcc9d4
BOUNDARIES = {
    0x13370: 'transport-flush entry; no transport execution',
    0x11970: 'lock entry',
    0x11990: 'unlock entry',
    0x75d60: 'action error entry',
    0x2c70: 'native assertion entry',
    0x26700: 'populated text resource setter',
    0x26550: 'populated text resource color setter',
    0x107bed: 'active widget cleanup beyond empty fixture',
    0x1b560: 'selected graphic cleanup beyond pinned absent selection',
    0x1a961: 'cursor state change beyond already-selected fixture',
    0x10d362: 'nonempty selection reset',
    0x10dbf0: 'nonzero list columns',
    0x10d8a0: 'mode-4 event selection continuation',
    0xc8720: 'previous-page continuation',
    0xc8750: 'next-page continuation',
}
CHECKPOINTS = (0xc8350, 0xc83a7, 0xc83b1, 0xc83b9, 0xc83c0,
               0xc83d5, 0xc840f, 0xc8420, 0xc842b, 0xc844c,
               0xc8456, 0xc858e, 0xc8598, 0x97dc0, 0x132e0)
OPEN = ('Original server dispatch/validation of 85 and 86; request/context/source '
        'semantics; actual UI/resource/page production; populated cleanup paths; '
        'locks and transport framing/flush/send; ACTMIS ownership, acceptance, '
        'completion, consumption, prerequisites, rewards and persistence. '
        'No inferred server acceptance and no live playable proof.')


class NativeClose(q.NativeAction):
    def __init__(self, raw):
        self.trace, self.checkpoints, self.stack_writes = [], [], []
        super().__init__(raw)
        self.vm.mem_map(BACKING, 4096)
        self.write(q.UI + LIST + 4, '<I', BACKING)
        # Native 1E500/1E440 read slot 0's resource id, then take >=1388 exit.
        self.write(BACKING + 0x1e, '<H', 0xffff)
        self.write(q.UI + 0x8688c, '<I', SOURCE)
        self.write(q.UI + 0x232ec8, '<I', 1)
        from unicorn import UC_PROT_READ
        self.vm.mem_protect(BACKING, 4096, UC_PROT_READ)

    def _code(self, vm, address, size, context):
        rva = address - q.BASE
        self.trace.append(rva)
        if rva in CHECKPOINTS or rva in BOUNDARIES:
            self.checkpoints.append(dict(rva=rva, **self.state()))
        before = len(self.calls)
        super()._code(vm, address, size, context)
        if len(self.calls) != before:
            call = self.calls[-1]
            if call['opcode'] == 0x86:
                call['tail_before'] = None
            call['caller_rva'] = self.read(self.getreg('ESP'), '<I')[0] - q.BASE
            call['queue_count_at_call'] = self.read(q.QUEUE + q.QUEUE_COUNT, '<I')[0]
            # Snapshot provenance at the call, before later stack reuse.
            call['last_payload_writes'] = []
            for offset in range(call['payload_length']):
                byte_address = call['payload_pointer'] + offset
                writer = next((w.copy() for w in reversed(self.stack_writes)
                               if w['address'] <= byte_address < w['address'] + w['size']), None)
                call['last_payload_writes'].append(writer)

    def _memory(self, vm, access, address, size, value, context):
        from unicorn import UC_MEM_WRITE
        super()._memory(vm, access, address, size, value, context)
        if access == UC_MEM_WRITE and q.STACK <= address < q.STACK + 0x10000:
            self.stack_writes.append(dict(rva=self.getreg('EIP') - q.BASE,
                                          address=address, size=size, value=value))
        if BACKING <= address < BACKING + 4096:
            self.events.append(dict(phase=self.phase, rva=self.getreg('EIP') - q.BASE,
                                    access='write' if access == UC_MEM_WRITE else 'read',
                                    region='backing', offset=address - BACKING, size=size))

    def state(self):
        return dict(active=self.read(q.UI + ACTIVE, '<I')[0],
                    action_state=self.read(q.UI + ACTION_STATE, '<I')[0],
                    high_bit_flag=self.read(q.GLOBALS, '<I')[0],
                    choice=self.read(q.UI + q.CHOICE, '<h')[0],
                    queue_count=self.read(q.QUEUE + q.QUEUE_COUNT, '<I')[0])

    def prepare(self, *, active=1, action_state=0, source_dword=0xdeadbeef,
                widget=0, page=0, page_count=1, mode=1, threshold=0, choice=-1,
                stack_byte=0xa5, queued_count=0, lock_pointer=0):
        """Explicit post-render state; request/reply/context remain from ingest.

        Empty widget flags, zero list columns/entries, absent graphic selection,
        and already-selected cursor are fixture conditions, not successful stubs.
        """
        if not (all(0 <= x <= 0xffffffff for x in
                    (active, action_state, source_dword, lock_pointer))
                and all(-32768 <= x <= 32767 for x in (widget, threshold, choice))
                and all(-0x80000000 <= x < 0x80000000 for x in (page, page_count))
                and 0 <= mode <= 65535 and 0 <= stack_byte <= 255
                and 0 <= queued_count <= 0xa00):
            raise ValueError('State outside bounded native widths')
        self.write(q.UI + ACTIVE, '<II', active, action_state)
        self.write(SOURCE, '<I', source_dword)
        self.write(q.UI + WIDGET, '<h', widget)
        self.write(q.GLOBALS + 4, '<ii', page, page_count)
        self.write(q.UI + q.MODE, '<H', mode)
        self.write(q.UI + q.THRESHOLD, '<h', threshold)
        self.write(q.UI + q.CHOICE, '<h', choice)
        self.write(q.QUEUE + q.QUEUE_COUNT, '<I', queued_count)
        self.write(q.QUEUE + 0x40d4, '<I', lock_pointer)
        self.write(q.QUEUE + 0x2cb8, '<B', 1)
        self.vm.mem_write(q.STACK, bytes([stack_byte]) * 0xf000)
        self.events, self.calls, self.stack_writes = [], [], []
        self.trace, self.checkpoints = [], []
        self.tail_before = None

    def _finish(self, end, before, call_start, trace_start, checkpoint_start):
        after = self.state()
        count = before['queue_count']
        return dict(returned=end == q.RETURN,
                    stop_rva=None if end == q.RETURN else end - q.BASE,
                    boundary='returned' if end == q.RETURN else BOUNDARIES[end - q.BASE],
                    before=before, after=after, esp=self.getreg('ESP'),
                    calls=self.calls[call_start:],
                    appended_hex=bytes(self.vm.mem_read(q.QUEUE + q.QUEUE_BYTES + count,
                                       max(0, after['queue_count'] - count))).hex(),
                    trace=self.trace[trace_start:],
                    checkpoints=self.checkpoints[checkpoint_start:])

    def execute(self, entry='close', *, control=0, flags=1):
        """Run an entire bounded native call, retaining queue/UI state between calls.

        Flush enters the real pending-queue gate, stopping before 13370 executes.
        No native instruction, callee return, or live transport is substituted.
        """
        starts = dict(close=0xc8350, action=0xc8500, event=0xc85b0, flush=0x133f0)
        if entry not in starts or not (0 <= control <= 65535 and 0 <= flags <= 255):
            raise ValueError('Unsupported entry or event width')
        self.phase = entry
        before = self.state()
        indices = (len(self.calls), len(self.trace), len(self.checkpoints))
        self.write(q.SP, '<III', q.RETURN, control, flags)
        self.setreg('ESP', q.SP)
        self.setreg('ECX', q.QUEUE if entry == 'flush' else q.UI)
        end = self.run(starts[entry], q.RETURN, *(q.BASE + r for r in BOUNDARIES))
        return self._finish(end, before, *indices)

    def resume_close(self):
        """Continue a parent NativeAction.action stop with its exact live stack."""
        if self.getreg('EIP') != q.BASE + 0xc8350:
            raise ValueError('Expected exact NativeAction C8350 continuation')
        self.phase = 'close-continuation'
        before = self.state()
        indices = (len(self.calls), len(self.trace), len(self.checkpoints))
        end = self.run(0xc8350, q.RETURN, *(q.BASE + r for r in BOUNDARIES))
        return self._finish(end, before, *indices)


def build_report(path=q.IMAGE):
    raw = q.evidence(path)
    scenarios = []
    for name, entry, reply, mode, choice in (
            ('action', 'action', 0x8002, 1, -1),
            ('direct-close', 'close', 2, 1, -1),
            ('direct-close-with-flag', 'close', 0x8002, 1, -1),
            ('mode4-action-with-flag', 'action', 0x8002, 4, 3)):
        n = NativeClose(raw)
        packet = q.fixture(request_word=0x1234, reply_word=reply, context_byte=0x9a)
        incoming = n.ingest(packet)
        n.prepare(mode=mode, choice=choice)
        result = n.execute(entry)
        flush = n.execute('flush')
        scenarios.append(dict(name=name, fixture_hex=packet.hex(), incoming=incoming,
                              result=result, flush=flush, events=n.events))
    expected = ('85341202009aa5', '86efbe0010',
                '86efbe001085341202009a84', '85341203009aa585341202009a84')
    if tuple(s['result']['appended_hex'] for s in scenarios) != expected:
        raise AssertionError('Bounded native sequence changed')
    if not all(s['result']['returned'] and s['flush']['stop_rva'] == 0x13370
               for s in scenarios):
        raise AssertionError('Expected complete call then unexecuted flush boundary')
    return dict(schema='current-quest-close-v1', image_sha256=q.IMAGE_SHA,
                scenarios=scenarios, requires_85_then_86=False,
                contract='85: two LE words, context byte, producer-uninitialized tail; '
                '86: low word of source dword, high word of saved this pointer.',
                boundary='Synthetic empty UI backing, original native instructions; '
                'no transport flush execution or server acceptance.', open=OPEN)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=q.IMAGE)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    report = build_report(args.image)
    if not args.json:
        for scenario in report['scenarios']:
            scenario.pop('events')
            for key in ('result', 'flush'):
                scenario[key].pop('trace')
                scenario[key].pop('checkpoints')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
