"""Deterministic local-only x86 capsule runner; never launches a client.

Entry snapshots are SYNTHETIC_EMULATOR_ENTRY fixtures, not live captures.
init_session zeroes the entire object and sets enabled DWORD +8 to 1 before
calling the seed setter. The seed setter does not itself enable the codec.
Callers must keep independent copies of the returned state for TX and RX.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


ROOT = Path(__file__).resolve().parents[2]
LOCAL_PACKAGES = ROOT / 'artifacts/tooling/crypto-oracle-python'
if LOCAL_PACKAGES.is_dir():
    sys.path.insert(0, str(LOCAL_PACKAGES))


STATE_SIZE = 0x255C
OBJECT = 0x10000000
INPUT = 0x20000000
STACK = 0x30000000
STACK_SIZE = 0x10000
SENTINEL = 0x40000000
PAGE = 0x1000
MAX_INPUT = 16 * 1024 * 1024


class OracleError(RuntimeError):
    """Invalid capsule, forbidden access, or incomplete execution."""


def _integer(value):
    return int(value, 0) if isinstance(value, str) else int(value)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _load_capsule(path):
    if __package__:
        from .capsule import load_capsule
    else:
        from capsule import load_capsule
    return load_capsule(path)


class ClientCryptoOracle:
    def __init__(self, capsule_path, *, instruction_budget=2_000_000,
                 timeout_us=5_000_000):
        self.path = Path(capsule_path).absolute()
        # The capsule loader owns original/restored-image binding validation.
        raw = self.path.read_bytes()
        self.manifest = _load_capsule(self.path)
        if self.path.read_bytes() != raw:
            raise OracleError('Capsule manifest changed during validation')
        self.capsulehash = hashlib.sha256(raw).hexdigest()
        self.instruction_budget = int(instruction_budget)
        self.timeout_us = int(timeout_us)
        if self.instruction_budget <= 0 or self.timeout_us <= 0:
            raise ValueError("Execution limits must be positive")
        self.regions = []
        for item in self.manifest['regions']:
            address, size = _integer(item['address']), _integer(item['size'])
            kind = item['kind'].upper()
            if kind not in ('CODE', 'CONSTANT_TABLE', 'KEY_TABLE', 'SESSION_STATE'):
                raise OracleError('Unsupported capsule region kind: ' + kind)
            data = (self.path.parent / item['file']).read_bytes()
            if len(data) != size or hashlib.sha256(data).hexdigest() != item['sha256'].lower():
                raise OracleError('Capsule region size/hash mismatch')
            self.regions.append(dict(address=address, size=size, kind=kind, data=data))
        self.entries = {}
        for name in ('init_session', 'encrypt', 'decrypt'):
            entry = self.manifest['entries'][name]
            self.entries[name] = _integer(entry['va'] if isinstance(entry, dict) else entry)

    def init_session(self, seed: bytes, *, trace=False) -> dict:
        seed = bytes(seed)
        if len(seed) != 16:
            raise ValueError('Session seed must be exactly 16 bytes')
        state = bytearray(STATE_SIZE)
        struct.pack_into('<I', state, 8, 1)
        return self._run('init_session', bytes(state), seed, trace)

    def encrypt(self, state: bytes, input_bytes: bytes, *, trace=False) -> dict:
        return self._run('encrypt', bytes(state), bytes(input_bytes), trace)

    def decrypt(self, state: bytes, input_bytes: bytes, *, trace=False) -> dict:
        return self._run('decrypt', bytes(state), bytes(input_bytes), trace)

    def replay(self, snapshot: dict, *, trace=False) -> dict:
        """Replay only an exact deterministic entry fixture, never a live snapshot.

        The layout digest detects accidental changes; it is not a signature.
        Every register and mapped byte must also match the canonical fixture
        reconstructed from the supplied state/input and freshly verified capsule.
        """
        try:
            # Detach caller-owned dictionaries and reject non-JSON values.
            saved = json.loads(_canonical(snapshot))
            if not isinstance(saved, dict):
                raise ValueError('Snapshot must be an object')
            digest = saved.pop('entry_layout_sha256')
            if hashlib.sha256(_canonical(saved).encode('utf-8')).hexdigest() != digest:
                raise ValueError('Snapshot entry layout hash mismatch')
            saved['entry_layout_sha256'] = digest
            mode = saved['mode']
            if mode not in self.entries:
                raise ValueError('Unsupported snapshot mode')
            state = bytes.fromhex(saved['state']['hex'])
            source = bytes.fromhex(saved['input']['hex'])
            if mode == 'init_session':
                fixture = bytearray(STATE_SIZE)
                struct.pack_into('<I', fixture, 8, 1)
                if len(source) != 16 or state != bytes(fixture):
                    raise ValueError('Invalid seed initializer fixture')
            # Recheck on-disk source bindings and regions before every replay.
            verified = ClientCryptoOracle(self.path, instruction_budget=self.instruction_budget,
                                          timeout_us=self.timeout_us)
            if saved['capsulehash'] != self.capsulehash or verified.capsulehash != self.capsulehash:
                raise ValueError('Snapshot capsule hash mismatch')
            return verified._run(mode, state, source, trace, expected_snapshot=saved)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise OracleError('Invalid deterministic entry snapshot: ' + str(exc)) from exc

    def _run(self, mode, state, source, trace, *, expected_snapshot=None):
        import unicorn as uc
        from unicorn import x86_const as x86

        if len(state) != STATE_SIZE:
            raise ValueError('State must be exactly 0x255c bytes')
        if len(source) > MAX_INPUT:
            raise ValueError('Input exceeds 16 MiB limit')
        emulator = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        registers = {name: getattr(x86, 'UC_X86_REG_' + name) for name in
                     ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP', 'ESP', 'EIP', 'EFLAGS')}

        def regs():
            return {name: emulator.reg_read(reg) for name, reg in registers.items()}

        regions = [dict(r) for r in self.regions]
        stack = bytearray(STACK_SIZE)
        esp = STACK + STACK_SIZE - 0x100
        args = [SENTINEL, INPUT] + ([] if mode == 'init_session' else [len(source)])
        struct.pack_into('<' + 'I' * len(args), stack, esp - STACK, *args)
        regions += [dict(address=OBJECT, size=STATE_SIZE, kind='SESSION_STATE', data=state),
                    dict(address=INPUT, size=max(1, len(source)), kind='INPUT',
                         data=source or b'\0'),
                    dict(address=STACK, size=STACK_SIZE, kind='STACK', data=bytes(stack))]
        pages = {}
        previous_end = 0
        for region in sorted(regions, key=lambda r: r['address']):
            start, size = region['address'], region['size']
            end = start + size
            if size <= 0 or start < previous_end or start < 0 or end > 0x100000000:
                raise OracleError('Overlapping or invalid capsule memory ranges')
            if start <= SENTINEL < end:
                raise OracleError('Capsule overlaps return sentinel')
            previous_end = end
            permissions = uc.UC_PROT_READ
            if region['kind'] == 'CODE':
                permissions |= uc.UC_PROT_EXEC
            elif region['kind'] in ('SESSION_STATE', 'INPUT', 'STACK'):
                permissions |= uc.UC_PROT_WRITE
            for page in range(start & -PAGE, (end + PAGE - 1) & -PAGE, PAGE):
                pages[page] = pages.get(page, 0) | permissions
        for page in pages:
            emulator.mem_map(page, PAGE, uc.UC_PROT_ALL)
        for region in regions:
            emulator.mem_write(region['address'], region['data'])
        for page, permissions in pages.items():
            emulator.mem_protect(page, PAGE, permissions)
        for reg in registers.values():
            emulator.reg_write(reg, 0)
        emulator.reg_write(registers['EFLAGS'], 2)
        emulator.reg_write(registers['ECX'], OBJECT)
        emulator.reg_write(registers['ESP'], esp)
        emulator.reg_write(registers['EIP'], self.entries[mode])
        snapshot = dict(format_version=1, origin='SYNTHETIC_EMULATOR_ENTRY',
                        mode=mode, capsulehash=self.capsulehash,
                        regs=regs(), stack=dict(address=STACK, hex=bytes(stack).hex()),
                        input=dict(address=INPUT, hex=source.hex()),
                        state=dict(address=OBJECT, hex=state.hex()),
                        memorymap=[dict(address=r['address'], size=r['size'], kind=r['kind'],
                                        sha256=hashlib.sha256(r['data']).hexdigest(),
                                        hex=r['data'].hex()) for r in regions])
        snapshot['entry_layout_sha256'] = hashlib.sha256(_canonical(snapshot).encode('utf-8')).hexdigest()
        if expected_snapshot is not None:
            if _canonical(expected_snapshot) != _canonical(snapshot):
                raise OracleError('Snapshot differs from canonical deterministic entry layout')
            # Use the validated saved register values, including EFLAGS and ESP.
            for name, value in expected_snapshot['regs'].items():
                emulator.reg_write(registers[name], value)
        reads, writes, fetches, instructions, errors = {}, {}, {}, [], []
        count = 0
        limit = self.instruction_budget + len(source) * 100
        decoder = None
        if trace:
            import capstone
            decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            decoder.detail = True

        def fail(message):
            errors.append(message)
            emulator.emu_stop()

        def containing(address, size):
            return next((r for r in regions if r['address'] <= address and
                         address + size <= r['address'] + r['size'] and
                         not (r['address'] == INPUT and not source)), None)

        def classify(address, size, writing, region):
            if region['address'] == OBJECT and OBJECT + 0x2420 <= address and address + size <= OBJECT + 0x2520:
                return 'KEY_TABLE'
            if region['kind'] == 'INPUT' and writing:
                return 'OUTPUT'
            return region['kind']

        def memory_hook(_emu, access, address, size, value, _user):
            writing = access == uc.UC_MEM_WRITE
            region = containing(address, size)
            if (region is None or
                    (writing and region['kind'] not in ('SESSION_STATE', 'INPUT', 'STACK')) or
                    (writing and mode == 'init_session' and region['address'] == INPUT)):
                fail('Forbidden memory access at 0x%x size %d' % (address, size))
                return
            pc = emulator.reg_read(registers['EIP'])
            kind = classify(address, size, writing, region)
            key = (pc, address, size, kind)
            target = writes if writing else reads
            target[key] = target.get(key, 0) + 1
            if trace and instructions:
                event = dict(pc=pc, address=address, size=size, kind=kind,
                             before_hex=bytes(emulator.mem_read(address, size)).hex())
                if writing:
                    event['after_hex'] = (value & ((1 << (size * 8)) - 1)).to_bytes(size, 'little').hex()
                instructions[-1]['memory_writes' if writing else 'memory_reads'].append(event)

        def invalid_hook(_emu, access, address, size, value, _user):
            fail('Unmapped/protected memory access %d at 0x%x size %d' % (access, address, size))
            return False

        def code_hook(_emu, address, size, _user):
            nonlocal count
            region = containing(address, size)
            if region is None or region['kind'] != 'CODE':
                fail('Execution outside code allowlist at 0x%x' % address)
                return
            count += 1
            if count > limit:
                fail('Instruction budget exhausted')
                return
            key = (address, address, size, 'CODE')
            fetches[key] = fetches.get(key, 0) + 1
            if trace:
                before = regs()
                if instructions:
                    instructions[-1]['register_after'] = before
                decoded = next(decoder.disasm(bytes(emulator.mem_read(address, size)), address), None)
                if decoded is None:
                    fail('Unable to decode traced instruction')
                    return
                read_regs, write_regs = decoded.regs_access()
                instructions.append(dict(pc=address,
                    rva=address - _integer(self.manifest.get('image_base', 0x400000)),
                    instruction=decoded.mnemonic + ' ' + decoded.op_str,
                    register_reads=[decoded.reg_name(r) for r in read_regs],
                    register_writes=[decoded.reg_name(r) for r in write_regs],
                    register_before=before, memory_reads=[], memory_writes=[]))

        emulator.hook_add(uc.UC_HOOK_MEM_READ | uc.UC_HOOK_MEM_WRITE, memory_hook)
        emulator.hook_add(uc.UC_HOOK_MEM_INVALID, invalid_hook)
        emulator.hook_add(uc.UC_HOOK_CODE, code_hook)
        try:
            emulator.emu_start(self.entries[mode], SENTINEL, timeout=self.timeout_us,
                               count=limit + 1)
        except uc.UcError as exc:
            raise OracleError(errors[0] if errors else str(exc)) from exc
        if errors:
            raise OracleError(errors[0])
        after_regs = regs()
        if after_regs['EIP'] != SENTINEL:
            raise OracleError('Execution did not return (timeout or instruction budget)')
        if after_regs['ESP'] != esp + 4 * len(args):
            raise OracleError('Entry calling convention mismatch: unexpected final ESP')
        after = bytes(emulator.mem_read(OBJECT, STATE_SIZE))
        modified = [dict(offset=i, before=a, after=b) for i, (a, b) in enumerate(zip(state, after)) if a != b]
        ranges = []
        for byte in modified:
            offset = byte['offset']
            if ranges and ranges[-1]['offset'] + ranges[-1]['size'] == offset:
                ranges[-1]['size'] += 1
            else:
                ranges.append(dict(offset=offset, size=1))
        for item in ranges:
            start, end = item['offset'], item['offset'] + item['size']
            item.update(before_hex=state[start:end].hex(), after_hex=after[start:end].hex())

        def footprint(events):
            return [dict(pc=pc, address=address, size=size, kind=kind, count=n)
                    for (pc, address, size, kind), n in sorted(events.items())]

        result = dict(output_hex=bytes(emulator.mem_read(INPUT, len(source))).hex() if source else '',
                      state_after_hex=after.hex(), register_after=after_regs,
                      memory_reads=footprint(reads), memory_writes=footprint(writes),
                      code_fetches=footprint(fetches),
                      modified_state=dict(bytes=modified, ranges=ranges), snapshot=snapshot,
                      capsulehash=self.capsulehash, instruction_count=count)
        if trace:
            if instructions:
                instructions[-1]['register_after'] = after_regs
            result['instruction_trace'] = instructions
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capsule', required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ('init-session', 'encrypt', 'decrypt', 'replay'):
        modes.add_argument('--' + name, action='store_true')
    modes.add_argument('--batch', metavar='REQUEST_FILE')
    parser.add_argument('--request')
    parser.add_argument('--output', required=True)
    parser.add_argument('--trace', action='store_true', help='Enable only when investigating a mismatch')
    args = parser.parse_args(argv)
    try:
        oracle = ClientCryptoOracle(args.capsule)
        path = args.batch or args.request
        if not path:
            parser.error('--request is required outside batch mode')
        requests = json.loads(Path(path).read_text(encoding='utf-8-sig'))

        def execute(request, mode):
            mode = mode.replace('-', '_')
            if mode not in ('init_session', 'encrypt', 'decrypt', 'replay'):
                raise ValueError('Unknown oracle mode: ' + mode)
            tracing = args.trace or request.get('trace', False)
            if mode == 'replay':
                return oracle.replay(request.get('snapshot', request), trace=tracing)
            if mode == 'init_session':
                return oracle.init_session(bytes.fromhex(request['seed_hex']), trace=tracing)
            return getattr(oracle, mode)(bytes.fromhex(request['state_hex']),
                                        bytes.fromhex(request['input_hex']), trace=tracing)

        if args.batch:
            if not isinstance(requests, list):
                raise ValueError('Batch request must be a JSON list')
            result = [execute(request, request['mode']) for request in requests]
        else:
            mode = ('replay' if args.replay else 'init_session' if args.init_session
                    else 'encrypt' if args.encrypt else 'decrypt')
            result = execute(requests, mode)
        with Path(args.output).open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
        return 0
    except (OracleError, ValueError, KeyError, OSError, ImportError) as exc:
        print('crypto oracle: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
