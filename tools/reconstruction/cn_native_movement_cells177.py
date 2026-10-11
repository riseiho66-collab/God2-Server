"""Round177 bounded CN path-refinement consumers; file/PE/static only.

Existing CnMapPassability remains the raw-cell/composition implementation.
No native execution, guessed pathfinder, permission, reply or complete route.
"""
from pathlib import Path
import csv
import io
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'tw-native-mixed-dispatch-source-01/agents/cn-cell-frontier'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_native_movement_cells177.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
    'src/cn/world/SharedMovement.h', 'src/cn/world/SharedMovement.cpp',
    'src/cn/world/SharedNativeMovementScene.h', 'src/cn/world/SharedNativeMovementScene.cpp',
    'src/cn/world/CnMapPassability.h', 'src/cn/world/CnMapPassability.cpp',
    'src/cn/world/SharedWorldGameplay.cpp',
    'src/cn/scripting/CnMovementRules.h', 'src/cn/scripting/CnMovementRules.cpp',
    'src/cn/protocol/CnMovement.h', 'src/cn/protocol/CnRemoteActorMove.h',
    'src/cn/protocol/CnWorldEntry.h', 'src/protocol/RecoveredTaiwanMapCell.h',
    'scripts/cn/native_movement.lua', 'scripts/tw/native_movement.lua',
    'src/cn/world/CnNativePathCompletion.h', 'src/cn/world/CnNativePathCompletion.cpp',
    'docs/research/cn-native-path-completion-20261007.md',
    'tools/reconstruction/cn_native_path_completion_delivery.py',
    'tools/reconstruction/cn_receiver_owner_frontier169.py']
NEW = {'00486920', '00487190'}
RETAINED = {'004866a0', '00470310', '00486b80', '00535d80'}


def dump(rel, value):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write((json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode())


def retain(rel, p, repository=False):
    raw = p.read_bytes()
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open('xb') as f:
        f.write(raw)
    return {'path': p.relative_to(SERVER).as_posix() if repository else str(p.resolve()),
            'copy': rel, 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    if OUT.exists():
        raise RuntimeError('Preserve existing round177 evidence')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('CN pinned native input changed')
    OUT.mkdir(parents=True)
    before = [retain(f'before/b{n:02d}{Path(rel).suffix}', SERVER / rel, True)
              for n, rel in enumerate(SOURCE)]
    dump('before-source-origins.json', before)
    dump('source-absence.json', {'new_tool_absent_from_freshbefore1270': OWN,
        'CnNativeMapCell_h_cpp_not_present': True,
        'existing_equivalent': ['src/cn/world/CnMapPassability.h',
                                'src/cn/world/CnMapPassability.cpp'],
        'cpp_edits': [], 'scope': 'Repository inventory only; not global native absence.'})
    old = ROOT / 'cn-shared-movement-owner-01/native/20261006-cn-map-passability-01/map-passability-evidence.json'
    old_full = json.loads(old.read_text())
    prior = [old, ROOT / 'cn-shared-movement-owner-01/integration-manifest.json',
             ROOT / 'tw-native-mixed-dispatch-source-01/before-manifest.json']
    dump('derived-inputs.json', [retain(f'derived/d{n:02d}.json', p)
                               for n, p in enumerate(prior)])
    # This is scoped comparison against this actual old evidence, not a global
    # claim that a native address was never encountered by any previous task.
    dump('new-span-scope.json', {'old_whole_function_addresses':
        [r['va'] for r in old_full['functions']],
        'new_complete_spans': sorted(NEW),
        'old_calls_tsv_mentions_retained_not_new': True})
    metadata = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in metadata if r['address'].lower() in NEW | RETAINED]
    if len(selected) != len(NEW | RETAINED):
        raise ValueError('Actual native function metadata incomplete')
    originals = [retain('inputs/pe.exe', EXE)]
    for n, filename in enumerate(('functions.tsv', 'calls.tsv')):
        originals.append(retain(f'inputs/t{n}.tsv', RECOVERY / filename))
    for row in selected:
        originals.append(retain('inputs/' + row['address'] + '.c', RECOVERY / row['file']))
    dump('native-original-inputs.json', originals)
    dump('native/selected-original-metadata.json', selected)
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    sites, previous, instructions = [], [], {}
    for row in selected:
        lo, size = int(row['address'], 16), int(row['bytes'])
        off, native = mapped(pe, raw, lo, lo + size)
        decoded = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
            'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
            for i in md.disasm(native, lo)]
        instructions.update({r['va']: r for r in decoded})
        scope = 'new' if row['address'] in NEW else 'retained'
        prefix = 'native/' + scope + '/' + row['address']
        p = OUT / (prefix + '.bin'); p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(native)
        dump(prefix + '.json', decoded)
        item = {'owner': row['address'], 'start_va': f'{lo:08x}',
            'end_va_exclusive': f'{lo+size:08x}', 'file_offset': off,
            'raw_bytes': native.hex(), 'bytes': size, 'sha256': sha(native),
            'decoded_bytes': sum(len(bytes.fromhex(r['bytes'])) for r in decoded),
            'scope': scope, 'phase_or_opcode_inventory_increment': False}
        (sites if row['address'] in NEW else previous).append(item)
    dump('native/new-sites.json', sites)
    dump('native/retained-sites.json', previous)
    calls = list(csv.DictReader(io.StringIO((RECOVERY / 'calls.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    dump('native/bounded-original-calls.json', [r for r in calls
        if r['caller'].lower() in NEW | RETAINED])

    def relation(key, addresses, scope):
        return {'key': key, 'scope': scope,
                'raw_sites': [instructions[address] for address in addresses],
                'new_server_authority': False, 'new_complete_route': False}

    relations = [
        relation('actual_map_owner_delegate_AL',
            ['00486923', '00486926', '0048692c', '0048692e', '00486931', '00486936', '00486939'],
            'ECX path owner+0x0C -> actual object+0xBC map pointer. Non-null tail-jumps00470310 with original two stack arguments; null zeroes AL only, returns ret8. Upper EAX is not boolean or a cell.'),
        relation('packed_path_words_and_count',
            ['004871a5', '004871b0', '004871b3', '004871c1', '004871dc', '004871fd',
             '00487205', '00487210', '00487214', '00487272', '00487276', '0048727a', '00487292'],
            'Argument2 packed path: unsigned WORD x at+0x02,y at+0x40, stride2 in separate arrays. Argument1 DWORD count is read, not updated in this full span. Tests delta in[-1,1] each axis before choosing a non-adjacent pair; no packet coordinates/layout inference.'),
        relation('signed_midpoint_raw_AL_choice',
            ['0048734e', '00487351', '0048735d', '0048735f', '00487363', '00487364',
             '00487366', '00487368', '00487377', '00487378', '0048737a', '0048737c',
             '0048737f', '00487392', '00487394', '00487396', '0048739a'],
            'Original path-owner+0x0C then object+0xBC supplies ECX to rawreader. Signed delta/2 truncates toward zero before adding previous unsigned-WORD coordinate. Nonzero AL chooses midpoint; null map or zero AL chooses fallback. Does not prove full segment/corner collision or server permission.'),
        relation('actual_fallback_ECX_and_return_contract',
            ['004873d3', '004873d4', '004873d5', '004873db', '004873e1', '004873e3',
             '004873e4', '004873eb', '004873ec', '00487405', '0048732c', '0048733f'],
            'Fallback00485730 receives original path owner ECX and six pushed arguments including two local output pointers and preceding coordinates/deltas. This consumer returns EAX0 after refinement; ordinary no-selection return initializes EAX1. Full fallback algorithm/outputs not recovered here.'),
        relation('refinement_copy_and_retained_retry',
            ['004872c5', '004872c9', '004872d8', '004872e3', '004872f2', '00487318',
             '0048731a', '00487320', '00487325', '00487327', '00486815', '00486818',
             '0048681b', '00486820', '00486825', '00486827', '00486833', '00486836',
             '0048683e', '00486841', '00486846', '00486848'],
            'Chosen index inserts local WORD pair into temporary array and shifts copied entries; preserves original header byte, copies0x1F DWORDs+WORD (126B) into argument2. Caller004866A0 invokes/refines again according to actual EAX status. Original packed-count pointer is not incremented by00487190; do not substitute an invented path append/count rule. Retained caller calls not counted as new spans.'),
    ]
    gaps = [
        {'gap': 'Fallback00485730 complete branch algorithm and output provenance',
         'next_actual_root': '004873EC original ECX and six stack arguments ->00485730; existing call-table references to00486920 remain old metadata, not newly recovered full helper span.'},
        {'gap': 'Native full pathsearch, list ownership and packed-count/capacity behavior',
         'next_actual_root': 'Retained004866A0 00486820/00486841 EAX checks; new00487190 packed126B write; actual constructor of search owner+0C and object+BC before claiming source lifecycle.'},
        {'gap': 'Real shared-movement authority and native5D source',
         'next_actual_root': 'SharedNativeMovementScene::Authority::authorize actual caller/producers, including timing/ring/pending/battle/transfer and full reply source. Client path selection cannot supply these rights.'},
        {'gap': 'CN/TW layout independence',
         'next_actual_root': 'CN5E17B vs TW13B; CN2E7B trailing opaque byte and5D byte/ring-pop semantics remain separately qualified. Equal scalar directions or opcode numbers do not prove shared layouts.'},
    ]
    dump('gaps.json', gaps)
    dump('findings.json', {'round': 177, 'client_sha256': PIN,
        'new_bounded_native_spans': len(sites),
        'new_bounded_native_bytes': sum(s['bytes'] for s in sites),
        'retained_bounded_native_spans': len(previous),
        'new_native_relations': relations,
        'cpp_edits': [], 'new_source_bindings': 0,
        'existing_actual_reader': 'src/cn/world/CnMapPassability.h/.cpp',
        'current_actual_caller': 'SharedMovement ->WorldOwner.scene ->CnMapPassability.cell_at ->CnMovementRules native_neighbor_passable ->actual WorldOwner.authorize source required',
        'receiver_contexts': 14, 'qualified_receiver_contexts': 12,
        'unresolved_helpers': [{'va': v, 'phase': None, 'slot': None, 'producer': None}
                               for v in ['0047DE70', '004812B0']],
        'new_phase_bindings': 0, 'new_opcodes': 0, 'new_complete_routes': 0,
        'whole_game_route_denominator': None, 'whole_game_percentage': None,
        'native_original_inputs': len(originals), 'gaps': gaps,
        'source_scope': 'New bounded client packed-path consumers only; existing map reader is retained and no duplicate unattached C++ class introduced.',
        'builds_tests_runtime_deploy': False, 'awaiting_BATCHFINAL': True})


if __name__ == '__main__':
    main()
