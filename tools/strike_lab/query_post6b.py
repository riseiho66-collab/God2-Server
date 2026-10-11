"""Bounded captured-tail query. Unknown memory is never synthesized as evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_READ_UNMAPPED, UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_ESI

IMAGE = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
TRACE = 'artifacts/runs/ui-gate-real-04/network-events.jsonl'
TRACE_SHA = '179babb69b9fd726e7c790605aa72406b53165721a8d212b777310565e36e73d'
WIRE = 'artifacts/runs/ui-gate-real-04/C2S_SERVER_SELECT_0001.bin'
WIRE_SHA = 'bd1d63babf8850007f21a4130adc00749e9171f769b7edfc38822115b7146fae'


def captured_context(events):
    entries = [e for e in events if e.get('sequence') == 146]
    returns = [e for e in events if e.get('sequence') == 147]
    if len(entries) != 1 or len(returns) != 1:
        raise ValueError('Missing or ambiguous frozen send pair')
    entry, returned = entries[0], returns[0]
    if not (entry.get('api') == returned.get('api') == 'send'
            and entry.get('event_type') == 'API_ENTRY'
            and returned.get('event_type') == 'API_RETURN'
            and returned.get('matched') is True and returned.get('entry') == 146
            and returned.get('pc') == entry.get('ret') == 0x412506
            and returned.get('eax') == entry.get('a2') == 6
            and returned.get('pid') == entry.get('pid')
            and returned.get('tid') == entry.get('tid')
            and returned.get('run_id') == entry.get('run_id') == 'ui-gate-real-04'
            and returned.get('sp') == entry.get('sp', -100) + 20
            and returned.get('a1') == 0x4133b3):
        raise ValueError('Captured return identity/stack mismatch')
    for key in ('sp', 'ret', 'a0', 'a1', 'a2', 'a3'):
        if type(returned.get(key)) is not int or not 0 <= returned[key] < 2**32:
            raise ValueError('Invalid captured x86 value')
    return returned


def run_query(root=ROOT):
    start = time.perf_counter()
    image = (root / IMAGE).read_bytes()
    wire = (root / WIRE).read_bytes()
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA or hashlib.sha256(wire).hexdigest() != WIRE_SHA:
        raise ValueError('Frozen code or wire identity mismatch')
    trace = (root / TRACE).read_bytes()
    if hashlib.sha256(trace).hexdigest() != TRACE_SHA:
        raise ValueError('Frozen send trace identity mismatch')
    events = [json.loads(line) for line in trace.splitlines() if line.strip()]
    event = captured_context(events)
    # These are actual stack words in the return marker, not API arguments.
    stack = struct.pack('<5I', *(event[k] for k in ('ret', 'a0', 'a1', 'a2', 'a3')))
    sp = event['sp']
    vm = Uc(UC_ARCH_X86, UC_MODE_32)
    for rva in (0x12000, 0x13000):
        vm.mem_map(0x400000 + rva, 4096, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(0x400000 + rva, image[rva:rva + 4096])
    base, end = sp & ~4095, (sp + len(stack) + 4095) & ~4095
    vm.mem_map(base, end - base, UC_PROT_READ)
    vm.mem_write(sp, stack)
    vm.reg_write(UC_X86_REG_EIP, event['pc'])
    vm.reg_write(UC_X86_REG_ESP, sp)
    vm.reg_write(UC_X86_REG_EAX, 6)
    path, dependency = [], {}
    # The four allowed tail instructions only read captured ESP/EAX or stack.
    # ESI/EDI become known from pops before any use. Stop before any other code.
    allowed = {0x412506, 0x412507, 0x412509, 0x41250a, 0x4133b3}

    def instruction(uc, address, size, _):
        if address not in allowed:
            dependency.update(kind='OUTSIDE_BOUNDED_SLICE', pc=address)
            uc.emu_stop()
            return
        path.append(address - 0x400000)

    def missing(uc, access, address, size, value, _):
        dependency.update(kind='UNCAPTURED_MEMORY_READ',
                          instruction_rva=uc.reg_read(UC_X86_REG_EIP) - 0x400000,
                          object_root=uc.reg_read(UC_X86_REG_ESI),
                          offset=address - uc.reg_read(UC_X86_REG_ESI), size=size)
        uc.emu_stop()
        return False

    vm.hook_add(UC_HOOK_CODE, instruction)
    vm.hook_add(UC_HOOK_MEM_READ_UNMAPPED, missing)
    from unicorn import UcError
    try:
        vm.emu_start(event['pc'], 0, timeout=100000, count=8)
    except UcError:
        if dependency.get('kind') != 'UNCAPTURED_MEMORY_READ':
            raise
    if path != [0x12506, 0x12507, 0x12509, 0x1250a, 0x133b3] or not (
            dependency.get('offset') == 0x40d4 and dependency.get('size') == 4
            and dependency.get('object_root') == event['ret']):
        raise ValueError('Bounded continuation did not match the cached dependency')
    return {
        'query': 'Q_POST6B_DIRECTION', 'substrate': 'STATIC_SLICE',
        'verdict': 'NEED_MORE_EVIDENCE', 'next_direction': 'UNKNOWN',
        'state_before_hash': None, 'state_after_hash': None,
        'qualification': 'PARTIAL_CAPTURE_REPLAY_NOT_LIVE_CLIENT_EXECUTION',
        'completed_rvas': path[:-1], 'faulting_rva': path[-1],
        'first_missing_dependency': dependency,
        'next_query': 'CAPTURE_POST6B_PROTOCOL_ROOT_PLUS_0x40D4_AND_CALLER_STACK',
        'codegen_allowed': False, 'new_edge_accepted': False,
        'evidence': [{'path': p, 'sha256': hashlib.sha256(data).hexdigest()}
                     for p, data in ((IMAGE, image), (TRACE, trace), (WIRE, wire))],
        'query_cost_ms': (time.perf_counter() - start) * 1000,
        'limits': ['Registers not used by this slice are not reconstructed',
                   'Uncaptured memory is not mapped or supplied',
                   'Restored static code is not a live code-byte capture at sequence 147',
                   'Queue housekeeping is not a certified protocol-state transition'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run_query()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in
                     ('query', 'verdict', 'next_direction', 'first_missing_dependency', 'query_cost_ms')}))
