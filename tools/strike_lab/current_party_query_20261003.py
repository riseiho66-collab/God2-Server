"""Bounded build-pinned native party-position query evidence; no live processes.

Executes original x86 producers and consumers, observing existing UI/queue/time
boundaries. Never a server route or rendered-current-client acceptance gate.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import capstone
import pefile
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools.strike_lab.current_party_20261002 import Oracle, UI, ACTOR, BODY, STOP
from tools.strike_lab.current_protocol_coverage import qualified_image, IMAGE_SHA256

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent.parent / 'God2-解殼EXE原始碼重建/decompiled/functions'
EXE = ROOT.parent / 'God2/God2.exe'
CLIENT_SHA256 = 'c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
REGIONS = ((0x497210, 0x497230), (0x4ea530, 0x4ea770),
           (0x4ea140, 0x4ea340), (0x4ea470, 0x4ea510),
           (0x4ea410, 0x4ea470), (0x418950, 0x418b80),
           (0x4820a0, 0x483150),
           (0x504620, 0x504c30), (0x4c3b10, 0x4c3b60),
           (0x4e9bc0, 0x4e9eb0), (0x597598, 0x5975b4))


def digest(value):
    return hashlib.sha256(value).hexdigest()


class QueryOracle(Oracle):
    def __init__(self, raw):
        self.now = 123456
        self.observed = []
        super().__init__(raw)
        # Execute the real clear-label routine, rather than the earlier oracle's
        # boundary stub. Rendering/map helpers remain observed external limits.
        del self.helpers[0x4ea410]
        self.helpers.update({0x4c2e40: 0, 0x4c4250: 4})
        self.put(UI + 0x232df6, '<h', 7)
        self.put(ACTOR + 0x3f98, '<I', 2)
        for i, (identity, name) in enumerate(((513, b'Peer'), (514, b'Other'))):
            self.put(ACTOR + 0x3f9c + i * 24, '<H', identity)
            self.vm.mem_write(ACTOR + 0x3fa4 + i * 24, name + bytes(16 - len(name)))
            self.vm.mem_write(ACTOR + 0x4064 + i, b'\x01')

    def hook(self, vm, address, size, context):
        esp = vm.reg_read(UC_X86_REG_ESP)
        if address == STOP + 16:
            ret = self.u32(esp)
            vm.reg_write(UC_X86_REG_EAX, self.now)
            vm.reg_write(UC_X86_REG_EIP, ret)
            vm.reg_write(UC_X86_REG_ESP, esp + 4)
            return
        if address == 0x547af7:
            # External CRT formatting is a declared boundary. The original x86
            # performs all coordinate remainder/floor arithmetic before it.
            ret, dst, fmt, name, first, second, third = struct.unpack('<7I', self.read(esp, 28))
            text = self.read(name, 16).split(b'\0', 1)[0].decode('ascii')
            if fmt == 0x597598:
                numbers = [first, second]
                label = f'{text} {first:4d}/{second}'
            else:
                assert fmt == 0x5975a4
                numbers = [first, second, third]
                label = f'{text} {first}F {second:4d}/{third}'
            self.observed.append({'function': '00547AF7', 'format_va': f'{fmt:08X}',
                                  'native_numeric_arguments': numbers,
                                  'output_is_external_boundary_model': True})
            self.vm.mem_write(dst, label.encode('ascii') + b'\0')
            vm.reg_write(UC_X86_REG_EAX, len(label))
            vm.reg_write(UC_X86_REG_EIP, ret)
            vm.reg_write(UC_X86_REG_ESP, esp + 4)
            return
        if address in (0x505680, 0x4c2660):
            args = list(struct.unpack('<4I', self.read(esp + 4, 16)))
            row = {'function': f'{address:08X}', 'args': args}
            if address == 0x505680:
                row['text_hex'] = self.read(args[3], 64).split(b'\0', 1)[0].hex()
            self.observed.append(row)
        super().hook(vm, address, size, context)

    def state(self):
        return {'selected': struct.unpack('<H', self.read(UI + 0xafee4, 2))[0],
                'cooldown': self.read(ACTOR + 0x406c, 1)[0],
                'received_at': self.u32(ACTOR + 0x4070),
                'positions': [list(struct.unpack('<3H', self.read(ACTOR + 0x3ffc + i * 6, 6))) for i in range(2)],
                'position_valid': list(self.read(ACTOR + 0x4068, 2))}


def build_report():
    raw = qualified_image()
    exe = EXE.read_bytes()
    assert digest(exe) == CLIENT_SHA256, 'Current EXE identity changed'
    current = pefile.PE(data=exe).get_memory_mapped_image()
    intervals = []
    for start, end in REGIONS:
        rva, stop = start - 0x400000, end - 0x400000
        assert current[rva:stop] == raw[rva:stop], f'Current code differs at {start:08X}'
        intervals.append({'start_va': f'{start:08X}', 'end_va_exclusive': f'{end:08X}',
                          'sha256': digest(raw[rva:stop]), 'current_exe_equal': True})
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    producer_disassembly = [{'va': f'{i.address:08X}', 'hex': i.bytes.hex(),
                             'instruction': f'{i.mnemonic} {i.op_str}'}
                            for i in cs.disasm(raw[0x97210:0x97230], 0x497210)]
    calls = []
    for i in cs.disasm(raw[0xea530:0xea770], 0x4ea530):
        if i.mnemonic == 'call' and i.op_str == '0x497210':
            calls.append({'va': f'{i.address:08X}', 'hex': i.bytes.hex()})
    assert len(calls) == 2
    pins = []
    for entry in ('00497210', '004ea530', '004ea140', '004ea470', '004ea410',
                  '004820a0', '00418950', '00504620', '004c2660', '004e9340',
                  '004c3b10', '004e9bc0'):
        source = SOURCE / f'{entry}_FUN_{entry}.c'
        pins.append({'path': str(source.resolve()), 'sha256': digest(source.read_bytes())})

    producer = []
    for identity in (0, 1, 2999, 3000, 65535):
        v = QueryOracle(raw)
        payload = struct.pack('<H', identity) + bytes(range(16))
        v.call(0x497210, BODY, body=payload)
        assert v.queued == ([b'\x59' + payload] if identity < 3000 else [])
        assert v.read(BODY, 18) == payload
        producer.append({'id': identity, 'input_hex': payload.hex(),
                         'queued_hex': [b.hex() for b in v.queued], 'input_unchanged': True})

    caller = []
    for control, event, available, mode, cooling, elapsed, expected in (
        (4, 4, 1, 0, 0, 0, True), (5, 4, 1, 1, 0, 0, True),
        (4, 4, 1, 2, 0, 0, True), (4, 4, 1, 3, 0, 0, False),
        (4, 1, 1, 0, 0, 0, False), (4, 5, 1, 0, 0, 0, False),
        (4, 4, 0, 0, 0, 0, False), (3, 4, 1, 0, 0, 0, False),
        (6, 4, 1, 0, 0, 0, False), (4, 4, 1, 0, 1, 3000, False),
        (4, 4, 1, 0, 1, 3001, True)):
        v = QueryOracle(raw)
        v.put(UI + 0x232f36, '<h', mode)
        v.vm.mem_write(ACTOR + 0x4064, bytes([available]) * 2)
        v.vm.mem_write(ACTOR + 0x406c, bytes([cooling]))
        v.put(ACTOR + 0x4070, '<I', v.now - elapsed)
        v.call(0x4ea530, control, event)
        assert bool(v.queued) == expected
        if expected:
            identity = 513 + control - 4
            assert v.queued[0][:3] == b'\x59' + struct.pack('<H', identity)
            assert len(v.queued[0]) == 19
            assert v.state()['selected'] == identity
        caller.append({'control': control, 'event': event, 'available': available,
                       'mode': mode, 'cooling': cooling, 'elapsed_ms': elapsed,
                       'queued_hex': [b.hex() for b in v.queued], 'state': v.state(),
                       'observed_ui_boundaries': v.observed})

    consumer = []
    for selected, identity in ((513, 513), (513, 514), (513, 999)):
        v = QueryOracle(raw)
        v.put(UI + 0xafee4, '<H', selected)
        v.call(0x4ea140, BODY, body=struct.pack('<HHH', identity, 129, 126))
        state = v.state()
        if identity in (513, 514):
            index = identity - 513
            assert state['positions'][index] == [identity, 129, 126]
            assert state['position_valid'][index] == 1
            assert state['cooldown'] == 1 and state['received_at'] == v.now
            highlights = [r for r in v.observed if r['function'] == '004C2660']
            assert highlights[0]['args'][:2] == [int(selected == identity), index]
            labels = [r for r in v.observed if r['function'] == '00505680']
            assert bool(labels) == (selected == identity)
        else:
            assert not v.observed and state['cooldown'] == 0
        consumer.append({'selected': selected, 'response_hex': (b'\x56' + struct.pack('<HHH', identity, 129, 126)).hex(),
                         'state': state, 'observed_ui_boundaries': v.observed})

    timeout = []
    for elapsed in (2999, 3000, 3001):
        v = QueryOracle(raw)
        v.put(UI + 0xafee4, '<H', 513)
        v.call(0x4ea140, BODY, body=struct.pack('<HHH', 513, 129, 126))
        v.observed.clear()
        v.now += elapsed
        v.call(0x4ea470)
        state = v.state()
        assert state['cooldown'] == int(elapsed <= 3000)
        assert state['selected'] == (513 if elapsed <= 3000 else 65535)
        if elapsed > 3000:
            assert len([r for r in v.observed if r['function'] == '00505680']) == 2
            assert [r for r in v.observed if r['function'] == '004C2660'][0]['args'][0] == 0
        timeout.append({'elapsed_ms': elapsed, 'state': state, 'observed_ui_boundaries': v.observed})

    map_cases = []
    for tiled, x, y, expected in ((False, 321, 226, [1, 26]),
                                 (True, 321, 226, [9, 1, 26]),
                                 (True, 160, 100, [4, 0, 0]),
                                 (True, 0, 0, [0, 0, 0])):
        v = QueryOracle(raw)
        descriptor = BODY + 0x200
        v.put(UI + 0x8aa4c, '<I', descriptor)
        v.put(descriptor + 0xf4, '<I', 3 if tiled else 0)
        v.put(descriptor + 0xf8, '<hhh', 160, 100, 3)
        v.put(UI + 0xafee4, '<H', 513)
        v.call(0x4ea140, BODY, body=struct.pack('<HHH', 513, x, y))
        arithmetic = [r for r in v.observed if r['function'] == '00547AF7'][0]
        assert arithmetic['native_numeric_arguments'] == expected
        assert v.state()['positions'][0] == [513, x, y]
        map_cases.append({'tiled_map': tiled, 'x': x, 'y': y, 'map_width': 160,
                          'map_height': 100, 'map_floor_stride': 3,
                          'arithmetic': arithmetic, 'state': v.state()})

    parser = ROOT / 'src/protocol/RecoveredWorldRecords.h'
    parser_has_59 = 'case 0x59:' in parser.read_text('utf-8')
    return {'format': 'native-party-position-query-20261003-v1',
            'native_image_sha256': IMAGE_SHA256, 'current_exe_sha256': CLIENT_SHA256,
            'code_intervals': intervals, 'source_pins': pins,
            'producer_disassembly': producer_disassembly, 'caller_to_producer_calls': calls,
            'queue_call_pin': {'va': '00497226', 'target_va': '004132E0',
                               'hex': raw[0x97226:0x9722b].hex()},
            'c2s': {'opcode': '59', 'logical_size': 19, 'payload_size': 18,
                    'layout': 'target WORD little-endian, raw name16',
                    'native_target_condition': 'target WORD < 3000',
                    'caller_name_tail': 'Caller copies through NUL only; remaining name16 bytes are unwritten stack residue.'},
            'producer_cases': producer, 'caller_cases': caller,
            'consumer_cases': consumer, 'timeout_cases': timeout,
            'map_arithmetic_cases': map_cases,
            'normal_ui_trigger': {
                'panel_word_offset': 'UI+232DF6', 'control': '4+member row index',
                'entry': 'UI+E2170 + panel*2A08 + 8B8 + control*100',
                'hit_index': 'signed WORD entry+8',
                'hit_manager': 'DWORD UI+E2174',
                'rect': 'active,left,top,right,bottom DWORDs at hit_manager+hit_index*24',
                'input': 'WM_MOUSEMOVE(200), settled left click/release, WM_LBUTTONDBLCLK(203), delayed WM_LBUTTONUP(202)',
                'native_chain': '418950:203 sets input+12014;504620 emits event bit4 after hover hit;4820A0 routes panel232DF6 to4EA530',
                'prerequisites': 'Nonempty roster; available flagactor+4064+i; mode WORD UI+232F36 is0/1/2; eventbit1 clear; cooldown expired strictly>3000ms.'},
            's2c_reuse': {'opcode': '56', 'logical_size': 7,
                         'layout': 'member WORD,x WORD,y WORD little-endian',
                         'consumer': '004EA140',
                         'effect': 'Selected member gets roster position label and selected map marker; all known members update storedposition/validflag. Labels/selection clear after strict3000ms timeout.',
                         'coordinate_domain': 'Exact rawx/yWORDS stored. Normal label uses unsignedx%current-map signedwidth andunsignedy%current-map signedheight. Tiled maplow2bitsF4==3 adds4C3B10floor=(signedy/height)*signedWORD+FC+(signedx-1+width)/width. Division truncates towardzero. Marker4C2660casts coordinate operands to signedWORD. No area/sceneID in56.',
                         'native_formats': {'00597598': '%s %4d/%d', '005975A4': '%s %dF %4d/%d'},
                         'availability': '4E9BC0 uses rosterID0xFFDC as unavailable sentinel,zeroesavailable4064/positionvalid4068 andsetspositionx/y7FFF. Availability is not cross-map proof.',
                         'limitations': 'Native name-copy andcoordinate/floor arithmetic executed. CRT stringformatting andUI/marker render are declaredexternal boundaries; markerpixels untested. Different-area/scene query policy unknown; gate samearea/scene pending independentproof.'},
            'runtime_gap': {'path': str(parser), 'sha256': digest(parser.read_bytes()),
                            'status': ('Parser59case present; runtime/acceptance not audited' if parser_has_59 else 'UNCONNECTED: no C2S59 parser case')},
            'next_step': 'Add separately typed59 query; authorize only current same-party member ID/name within nativeWORDbound; respond only requester with existing56 authoritative currentposition. Preserve every acceptedparty action/projector. Reject forged/stale/outsideparty requests without success. Prove originalproducer and transientselectedrow/marker against ownserver.',
            'native_rule_scope': 'Native query bytes/UI effects recovered; original server authorization/cross-map policy unverified. Any selected server policy requires documented CUSTOM provenance.',
            'scope': 'Immutable mapped x86 execution with queue,time,UIrender/map boundary observation; no services,clients,windows,network or database mutation.',
            'current_client_accepted': False}


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--output', type=Path)
    options = args.parse_args()
    report = json.dumps(build_report(), indent=2, ensure_ascii=False) + '\n'
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(report, encoding='utf-8')
        print(f'wrote {options.output}')
    else:
        print(report, end='')
