"""File-only CN receiver reference recovery across bounded function CFGs.

This is static decoding/abstract interpretation, never native execution or a
test. Constants describe instruction relations, not owner/phase qualification.
"""
import csv
import hashlib
import io
import json
from collections import Counter, deque

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_CALL, CS_GRP_RET
from capstone.x86_const import X86_OP_REG, X86_OP_IMM, X86_OP_MEM

from .cn_wrapper_route_frontier import ROOT, CN, PIN, RECOVERY
from .cn_pe_import_directory import FileView
from .cn_computed_receiver_references import TARGETS, canonical

NAME = 'cn-cfg-receiver-references-01'
ROUND = '20261007-cn-cfg-receiver-references'
SOURCES = ('tools/reconstruction/cn_cfg_receiver_references.py',
           'docs/research/cn-cfg-receiver-references-20261007.md')
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')
MASK = 0xffffffff


def digest(data):
    return hashlib.sha256(data).hexdigest()


def join(left, right):
    # Missing values are unknown. A constant survives only equal predecessors.
    regs = {k: left[0][k] for k in left[0]
            if k in right[0] and left[0][k][0] == right[0][k][0]}
    stack = ()
    if len(left[1]) == len(right[1]):
        stack = tuple(a if a is not None and b is not None and a[0] == b[0]
                      else None for a, b in zip(left[1], right[1]))
    return regs, stack


def key(state):
    return (tuple(sorted((r, v[0]) for r, v in state[0].items())),
            tuple(v[0] if v is not None else None for v in state[1]))


def scan_function(md, code, base, counts):
    """Entry-rooted worklist; branch targets decoded directly, no guessed roots."""
    end = base + len(code)
    instructions, states, edges, unresolved = {}, {base: ({}, ())}, {}, set()
    pending, queued = deque([base]), {base}
    # A per-span static resource bound. Exceeding it is an explicit open frontier.
    budget = max(1024, len(code) * 24)
    steps = 0

    def decode(pc):
        if pc not in instructions:
            ins = next(md.disasm(code[pc-base:pc-base+15], pc, count=1), None)
            instructions[pc] = ins
        return instructions[pc]

    def value(op, regs):
        if op.type == X86_OP_IMM:
            return op.imm & MASK, ()
        if op.type == X86_OP_REG:
            name = md.reg_name(op.reg)
            fact = regs.get(canonical(name))
            if fact is not None:
                shift = 8 if name in ('ah', 'bh', 'ch', 'dh') else 0
                return ((fact[0] >> shift) & ((1 << (op.size*8))-1), fact[1])
        return None

    def step(ins, state):
        before, oldstack = state
        regs, stack = dict(before), list(oldstack)
        ops, mn = ins.operands, ins.mnemonic
        trace = (ins.address, bytes(ins.bytes).hex(), mn+' '+ins.op_str)
        dest = md.reg_name(ops[0].reg) if ops and ops[0].type == X86_OP_REG else None
        assigned = {}
        if dest in REGS and ops[0].size == 4:
            old = before.get(dest)
            result = None
            if mn == 'mov' and len(ops) == 2:
                result = value(ops[1], before)
            elif mn in ('movzx', 'movsx') and len(ops) == 2:
                source = value(ops[1], before)
                if source is not None:
                    v = source[0]
                    if mn == 'movsx' and v & (1 << (ops[1].size*8-1)):
                        v -= 1 << (ops[1].size*8)
                    result = v & MASK, source[1]
            elif mn == 'lea' and len(ops) == 2 and ops[1].type == X86_OP_MEM:
                mem = ops[1].mem
                a = (0, ()) if not mem.base else before.get(md.reg_name(mem.base))
                b = (0, ()) if not mem.index else before.get(md.reg_name(mem.index))
                if a is not None and b is not None:
                    result = (a[0]+b[0]*mem.scale+mem.disp) & MASK, a[1]+b[1]
            elif mn in ('xor', 'sub') and len(ops) == 2 and ops[1].type == X86_OP_REG and ops[0].reg == ops[1].reg:
                result = 0, ()
            elif mn in ('add', 'sub', 'xor', 'and', 'or', 'shl', 'sal', 'shr', 'sar', 'rol', 'ror') and len(ops) == 2:
                right = value(ops[1], before)
                if old is not None and right is not None:
                    a, b = old[0], right[0]
                    n = b & 31
                    signed = a if a < 0x80000000 else a-0x100000000
                    v = {'add': lambda: a+b, 'sub': lambda: a-b,
                         'xor': lambda: a^b, 'and': lambda: a&b, 'or': lambda: a|b,
                         'shl': lambda: a<<n, 'sal': lambda: a<<n,
                         'shr': lambda: a>>n, 'sar': lambda: signed>>n,
                         'rol': lambda: ((a<<n)|(a>>(32-n))) if n else a,
                         'ror': lambda: ((a>>n)|(a<<(32-n))) if n else a}[mn]()
                    result = v & MASK, old[1]+right[1]
            elif mn in ('inc', 'dec', 'neg', 'not') and old is not None:
                a = old[0]
                result = {'inc': a+1, 'dec': a-1, 'neg': -a, 'not': ~a}[mn] & MASK, old[1]
            elif mn == 'imul' and len(ops) == 3:
                a, b = value(ops[1], before), value(ops[2], before)
                if a is not None and b is not None:
                    result = (a[0]*b[0]) & MASK, a[1]+b[1]
            elif mn == 'pop' and stack:
                result = stack[-1]
            if result is not None:
                assigned[dest] = result
        if mn == 'xchg' and len(ops) == 2 and all(op.type == X86_OP_REG and op.size == 4 for op in ops):
            a, b = (md.reg_name(op.reg) for op in ops)
            if a in REGS and b in REGS:
                if b in before:
                    assigned[a] = before[b]
                if a in before:
                    assigned[b] = before[a]
        if mn == 'push' and ops and ops[0].size == 4:
            stack.append(value(ops[0], before))
            stack = stack[-32:]
        elif mn == 'pop' and ops and ops[0].size == 4:
            if stack:
                stack.pop()
        elif mn in ('push', 'pop'):
            stack.clear()
        if mn == 'pop' and dest == 'esp':
            # POP ESP assigns the popped pointer, rather than merely advancing
            # ESP by four. Earlier tracked cells no longer describe the stack.
            stack.clear()
        _, writes = ins.regs_access()
        for reg in writes:
            root = canonical(md.reg_name(reg))
            regs.pop(root, None)
            if root == 'esp' and mn not in ('push', 'pop'):
                stack.clear()
        # Any explicit memory write can alias tracked native stack cells. This
        # includes MOV [esp/ebp/...], XCHG memory and string instructions.
        if any(op.type == X86_OP_MEM and op.access & 2 for op in ops):
            stack.clear()
        if any(word.startswith(('stos', 'movs', 'ins')) for word in mn.split()):
            # Also cover implicit string stores when no explicit memory operand
            # access is exposed by the disassembler.
            stack.clear()
        if mn in ('enter', 'leave', 'pushal', 'popal', 'pushaw', 'popaw', 'pushfd', 'popfd', 'pushf', 'popf'):
            stack.clear()
        for r, fact in assigned.items():
            regs[r] = fact[0], (fact[1]+(trace,))[-32:]
        # No calling convention/preservation/returned constants are assumed.
        if ins.group(CS_GRP_CALL):
            regs.clear()
            stack.clear()
        return regs, tuple(stack)

    def successors(ins):
        mn, ops = ins.mnemonic, ins.operands
        fall = ins.address + ins.size
        if ins.group(CS_GRP_RET) or mn in ('int', 'int3', 'iret', 'iretd', 'hlt', 'ud2', 'sysenter', 'sysexit'):
            return []
        if mn.startswith('j') or mn.startswith('loop'):
            target = ops[0].imm & MASK if ops and ops[0].type == X86_OP_IMM else None
            result = [] if mn in ('jmp', 'ljmp') else [fall]
            if target is None:
                unresolved.add((ins.address, 'indirect_branch'))
            elif base <= target < end:
                result.append(target)
            else:
                unresolved.add((ins.address, 'branch_outside_metadata_span', target))
            return result
        return [fall] if fall < end else []

    while pending and steps < budget:
        pc = pending.popleft()
        queued.discard(pc)
        steps += 1
        ins = decode(pc)
        if ins is None:
            unresolved.add((pc, 'invalid_decode'))
            continue
        after = step(ins, states[pc])
        edges[pc] = successors(ins)
        for target in edges[pc]:
            if not base <= target < end:
                unresolved.add((pc, 'fallthrough_outside_metadata_span', target))
                continue
            current = states.get(target)
            merged = after if current is None else join(current, after)
            if current is None or key(merged) != key(current):
                states[target] = merged
                if target not in queued:
                    pending.append(target)
                    queued.add(target)
    if pending:
        counts['worklist_budget_exhausted_spans'] += 1
        # Provisional facts in a nonconverged graph cannot be reported candidates.
        return instructions, edges, unresolved, [], False
    candidates = []

    def candidate(ins, fact, kind):
        if fact is None:
            return
        for helper, (lo, hi) in TARGETS.items():
            if lo <= fact[0] < hi:
                candidates.append({'owner': f'{base:08x}', 'site': f'{ins.address:08x}',
                    'target': f'{fact[0]:08x}', 'helper': helper, 'kind': kind,
                    'instruction': ins.mnemonic+' '+ins.op_str, 'bytes': bytes(ins.bytes).hex(),
                    'derivation': [{'va': f'{a:08x}', 'bytes': b, 'instruction': text}
                                   for a, b, text in fact[1]],
                    'phase_proven': False, 'ecx_owner_proven': False})
    for pc, ins in instructions.items():
        if ins is None:
            continue
        before = states[pc]
        ops, mn = ins.operands, ins.mnemonic
        if mn in ('call', 'jmp') and ops and ops[0].type == X86_OP_REG:
            counts['register_indirect_transfers_at_fixpoint'] += 1
            fact = value(ops[0], before[0])
            if fact is not None:
                counts['constant_resolved_register_transfers_at_fixpoint'] += 1
            candidate(ins, fact, 'cfg_register_indirect_transfer')
        if mn.startswith('ret') and before[1]:
            candidate(ins, before[1][-1], 'cfg_constant_push_ret')
        after = step(ins, before)
        for r, fact in after[0].items():
            if r not in before[0] or fact != before[0][r]:
                candidate(ins, fact, 'cfg_constant_address_materialization')
    counts['abstract_steps'] += steps
    return instructions, edges, unresolved, candidates, True


def main():
    root = ROOT/'artifacts/integration/packet-connections-20261006'
    out = root/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before snapshot; preserve previous artifacts')
    image = CN.parent/'XJZ-CN/God2_opt.exe'
    raw = image.read_bytes()
    if digest(raw) != PIN:
        raise RuntimeError('Pinned native input changed')
    pe = pefile.PE(data=raw, fast_load=True)
    view = FileView(pe, raw)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    metadata = (RECOVERY/'functions.tsv').read_bytes()
    rows = list(csv.DictReader(io.StringIO(metadata.decode('utf-8')), delimiter='\t'))
    counts, candidates, expanded, frontiers = Counter(), [], [], []
    files = []

    def save(rel, data, original):
        p = out/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(data)
        files.append({'path': rel, 'original': str(original), 'bytes': len(data), 'sha256': digest(data)})

    def dump(rel, obj):
        save(rel, (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode('utf-8'), 'current static native decoding')

    for rel in SOURCES:
        save('source/'+rel, (ROOT/rel).read_bytes(), ROOT/rel)
    save('metadata/functions.tsv', metadata, RECOVERY/'functions.tsv')
    prior = root/'cn-computed-receiver-references-01'
    for rel in ('computed-reference-scan.json', 'integration-manifest.json'):
        save('prior/'+rel, (prior/rel).read_bytes(), prior/rel)
    for helper, (lo, hi) in TARGETS.items():
        save('native/'+helper+'.bin', view.read(lo-pe.OPTIONAL_HEADER.ImageBase, hi-lo), image)
    for row in rows:
        if row['status'] != 'ok':
            counts['metadata_not_ok'] += 1
            continue
        size, base = int(row['bytes']), int(row['address'], 16)
        if not size or size > 1024*1024:
            counts['empty_or_over_budget_metadata_spans'] += 1
            continue
        try:
            code = view.read(base-pe.OPTIONAL_HEADER.ImageBase, size)
        except ValueError as error:
            counts['nonunique_or_incomplete_file_backing'] += 1
            frontiers.append({'owner': row['address'], 'reason': str(error)})
            continue
        counts['function_spans_scanned'] += 1
        counts['native_bytes_in_scanned_spans'] += size
        # Prior domain was linear disassembly only up to the first invalid byte.
        prefix = sum(ins.size for ins in md.disasm(code, base))
        decoded, edges, gaps, found, converged = scan_function(md, code, base, counts)
        live = {pc: ins for pc, ins in decoded.items() if ins is not None}
        counts['entry_rooted_instruction_sites'] += len(live)
        counts['cfg_edges'] += sum(len(e) for e in edges.values())
        counts['unresolved_exit_or_decode_records'] += len(gaps)
        candidates.extend(found)
        extra = [ins for pc, ins in live.items() if pc >= base+prefix]
        if extra:
            counts['spans_with_decode_beyond_prior_linear_prefix'] += 1
            counts['instruction_sites_beyond_prior_linear_prefix'] += len(extra)
            records = [{'va': f'{ins.address:08x}', 'bytes': bytes(ins.bytes).hex(),
                        'instruction': ins.mnemonic+' '+ins.op_str} for ins in sorted(extra, key=lambda i: i.address)]
            rel = 'expanded-native/'+row['address']+'.bin'
            save(rel, code, image)
            expanded.append({'owner': row['address'], 'span_bytes': size, 'linear_prefix_bytes': prefix,
                             'native_path': rel, 'native_sha256': digest(code), 'converged': converged,
                             'additional_instruction_sites': records,
                             'entry_rooted_edges': [{'from': f'{pc:08x}', 'to': [f'{a:08x}' for a in e]}
                                                   for pc, e in sorted(edges.items())],
                             'unresolved': [list(g) for g in sorted(gaps)]})
        if not converged or gaps:
            frontiers.append({'owner': row['address'], 'converged': converged,
                              'unresolved': [list(g) for g in sorted(gaps)]})
        if counts['function_spans_scanned'] % 10000 == 0:
            print(json.dumps({'static_spans': counts['function_spans_scanned'],
                              'entry_rooted_sites': counts['entry_rooted_instruction_sites']}), flush=True)
    dump('expanded-control-flow.json', expanded)
    dump('unresolved-frontiers.json', frontiers)
    dump('receiver-candidates.json', candidates)
    findings = {'round': ROUND, 'native_sha256': PIN, 'metadata_sha256': digest(metadata),
        'previous_goal_turn_classification': 'progress: sealed common character-offer invalidation source; level reply reaffirmed unchanged scope',
        'analysis_domain': 'entry-rooted function CFG, equal-value predecessor joins, unique file backing, fixed-point constants; no loaded memory/interprocedural/runtime inference',
        'counts': dict(counts), 'candidate_count': len(candidates), 'new_confirmed_phases': 0,
        'new_complete_bidirectional_routes': 0, 'unreachable_proven': False,
        'levels_changed': False, 'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'remaining': ['Actual ECX owner construction/registration and current network phase for0047DE70/004812B0 remain required; candidate addresses are not phase assignments.',
                      'Computed memory/encoded registration, interprocedural constants, loader/module mutation and metadata-omitted roots remain outside this domain.',
                      'All native request/authority/storage/reply/consumer routes and whole-game denominator remain incomplete.'],
        'build_run': False, 'tests_run': False, 'runtime_run': False, 'database_access': False, 'deployed': False}
    dump('findings.json', findings)
    dump('source-manifest.json', {'files': files})
    print(json.dumps({'round': ROUND, 'counts': dict(counts), 'candidates': len(candidates), 'new_complete_routes': 0}))


if __name__ == '__main__':
    main()
