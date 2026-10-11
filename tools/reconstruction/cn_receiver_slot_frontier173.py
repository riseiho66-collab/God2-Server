"""Round173 file-only lifetime gates for CN unqualified receiver owners.

Actual activation/invalidation is distinct from selecting a receive helper.
No execution, phase invention, global scan or framing-algorithm recount.
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
OUT = ROOT / 'tw-native-mask-material-source-01/agents/cn-slot-frontier'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_receiver_slot_frontier173.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
          'tools/reconstruction/cn_receiver_owner_frontier169.py',
          'tools/reconstruction/cn_receiver_slot_frontier171.py',
          'tools/reconstruction/cn_receiver_slot_frontier172.py', OWN]
NEW = {'0047fc50', '0047f310', '0047c5e0'}
RETAINED = {'0047de70', '004812b0'}


def dump(rel, value):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode())


def retain(rel, path, repository=False):
    raw = path.read_bytes()
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    return {'path': path.relative_to(SERVER).as_posix() if repository else str(path),
            'copy': rel, 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    if OUT.exists():
        raise RuntimeError('Preserve previous round173 evidence')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('Pinned CN native input changed')
    OUT.mkdir(parents=True)
    originals = [retain('native-original-inputs/God2_opt.exe', EXE)]
    for filename in ('functions.tsv', 'calls.tsv'):
        originals.append(retain('native-original-inputs/' + filename, RECOVERY / filename))
    for address in sorted(NEW | RETAINED):
        originals.append(retain('native-original-inputs/' + address + '.c',
            RECOVERY / 'part_0007' / (address + '_FUN_' + address + '.c')))
    dump('native-original-inputs.json', originals)
    dump('before-source-origins.json', [retain('before/' + rel, SERVER / rel, True) for rel in SOURCE])
    dump('new-source-absence.json', {'new_absent_from_root_before1238': [OWN], 'existing_cpp_edits': []})
    old = ROOT / 'tw-native-grid-composition-source-01/agents/cn-slot-frontier'
    prior = [old / 'findings.json', old / 'seal.json', old / 'native/new-sites.json',
        ROOT / 'tw-native-movement-scene-source-01/agents/cn-slot-frontier/findings.json',
        ROOT / 'tw-native-record-grammar-source-01/agents/cn-receiver/findings.json',
        ROOT / 'cn-receiver-reachability-agent-01/findings.json']
    dump('retained-prior/originals.json', [retain('retained-prior/' + str(n) + '-' + p.name, p)
                                       for n, p in enumerate(prior)])
    pe = pefile.PE(data=raw, fast_load=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    metadata = list(csv.DictReader(io.StringIO((RECOVERY / 'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in metadata if r['address'].lower() in NEW | RETAINED]
    dump('native/selected-original-metadata.json', selected)
    new_sites, old_sites, instructions = [], [], {}
    for row in selected:
        address = row['address'].lower()
        lo, size = int(address, 16), int(row['bytes'])
        offset, native = mapped(pe, raw, lo, lo + size)
        decoded = [{'va': f'{i.address:08x}', 'bytes': bytes(i.bytes).hex(),
                    'instruction': i.mnemonic + (' ' + i.op_str if i.op_str else '')}
                   for i in md.disasm(native, lo)]
        instructions.update({r['va']: r for r in decoded})
        section = 'new-owner-lifetime-spans' if address in NEW else 'retained-helper-gate-witnesses'
        target = OUT / ('native/' + section + '/' + address + '.bin')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(native)
        dump('native/' + section + '/' + address + '.json', decoded)
        item = {'owner': address, 'start_va': f'{lo:08x}', 'end_va_exclusive': f'{lo+size:08x}',
            'file_offset': offset, 'raw_bytes': native.hex(), 'sha256': sha(native),
            'decoded_instruction_count': len(decoded),
            'decoded_bytes': sum(len(bytes.fromhex(r['bytes'])) for r in decoded),
            'new_round173_lifetime_scope': address in NEW,
            'native_phase_or_opcode_inventory_increment': False}
        (new_sites if address in NEW else old_sites).append(item)
    dump('native/new-sites.json', new_sites)
    dump('native/retained-helper-gate-sites.json', old_sites)
    calls = list(csv.DictReader(io.StringIO((RECOVERY / 'calls.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    dump('native/selected-original-calls.json', [r for r in calls
        if any(v.lower() in NEW | RETAINED for v in r.values())])

    def relation(identifier, scope, new_vas, old_vas=(), **fields):
        return {'id': identifier, 'scope': scope,
            'rawsites': [instructions[va] for va in new_vas],
            'retained_helper_rawsites_not_recounted': [instructions[va] for va in old_vas], **fields}

    relations = [
        relation('actual-initializer-result-gates-owner-active-byte',
            'Exact initializer invokes0047C270 with fullowner+104. Nonzero result clears fullowner+2CB8 and returns1; zero clears outbound count, sets active1 and returns0. Eligibility is not receiver selection.',
            ['0047fc6a', '0047fcd5', '0047fcdb', '0047fce0', '0047fce2', '0047fce4',
             '0047fceb', '0047fd04', '0047fd06', '0047fd12'],
            incoming_full_owner_register='esi', base_displacement=0x104,
            actual_provider_target='0047c270', active_full_owner_offset=0x2cb8,
            nonzero_provider_result={'active': 0, 'wrapper_return': 1},
            zero_provider_result={'active': 1, 'wrapper_return': 0, 'outbound_count_offset_cleared': 0x36c4},
            helper_phase_determined=False),
        relation('actual-disconnect-invalidates-same-full-owner',
            'Exact disconnect retains incoming fullowner in EDI, invokes0047C5E0 with owner+104, then clears the same owner+2CB8 regardless of optional request branch.',
            ['0047f32f', '0047f3ac', '0047f3b0', '0047f3e6', '0047f3ec', '0047f3f4'],
            incoming_full_owner_register='edi', base_displacement=0x104,
            actual_close_target='0047c5e0', active_full_owner_offset=0x2cb8,
            optional_branch_control='second explicit argument byte!=0',
            helper_selected_by_disconnect=False),
        relation('actual-base-socket-close-invalidation',
            'Exact base close reads base+64C, skips declared close call forFFFFFFFF, otherwise passes that actual value to the declared closesocket IAT and storesFFFFFFFF. No OS call was executed.',
            ['0047c5e1', '0047c5e3', '0047c5e9', '0047c5ec', '0047c5ee', '0047c5ef', '0047c5f5'],
            base_socket_offset=0x64c, mapped_full_owner_socket_offset=0x750,
            invalid_socket_bits=0xffffffff, declared_close_iat_va='007ebd54',
            actual_loaded_binding_observed=False),
        relation('lifetime-writes-correlate-with-existing-helper-entry-gates',
            'New initializer/disconnect writes target the identical fullowner byte read by both retained unknown-helper prologues. This recovers eligibility/invalidation only; no call into either helper is established.',
            ['0047fce4', '0047fd12', '0047f3f4'],
            ['0047de75', '0047de77', '0047de7e', '0047de80', '004812b4', '004812b6', '004812bd', '004812c3'],
            shared_active_full_owner_offset=0x2cb8,
            inactive_0047de70='returns zero without selecting a phase',
            inactive_004812b0='writes only first output byte zero and returns zero',
            invocation_or_producer_pair_proven=False),
    ]
    byte_count = sum(int(r['end_va_exclusive'], 16)-int(r['start_va'], 16) for r in new_sites)
    findings = {'round': 173, 'version_scope': 'cn', 'native_sha256': PIN,
        'new_native_relations': relations, 'new_bounded_native_spans': len(new_sites),
        'new_bounded_native_bytes': byte_count, 'retained_old_helper_spans_not_recounted': len(old_sites),
        'old169_170_171_172_spans_or_relations_recounted': 0,
        'old_global_cfg_spans_or_sites_recounted': 0,
        'receiver_contexts': 14, 'qualified_receiver_contexts': 12,
        'unresolved_helpers': [{'address': '0047de70', 'phase': None, 'slot': None, 'producer_pair': None},
                               {'address': '004812b0', 'phase': None, 'slot': None, 'producer_pair': None}],
        'new_phase_opcode_bindings': 0, 'new_formal_source_owner_chains': 0,
        'new_complete_bidirectional_routes': 0, 'new_cpp_files': 0,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'unreachable_proven': False, 'build_run': False, 'tests_run': False,
        'native_run': False, 'emulation_run': False, 'database_access': False, 'deployed': False}
    dump('findings.json', findings)
    dump('stage-accounting.json', {'direction': 'S2C-unknown-receiver-owner-lifetime',
        'known_prior_receiver_contexts': 14, 'known_prior_qualified_contexts': 12,
        'new_confirmed_contexts': 0, 'new_actual_lifetime_relations': len(relations),
        'new_bounded_native_spans': len(new_sites), 'retained_helper_spans_not_recounted': len(old_sites),
        'new_opcode_inventory': 0, 'complete_routes_added': 0})
    dump('gaps.json', [
        'Exact caller/deferred/encoded selection of0047DE70/004812B0 remains missing; recovered lifetime gates do not assign phase, slot or producer pair.',
        'Provider0047C270 result gates eligibility, but its actual selector/endpoint rule and complete downstream object lifetime remain outside these three new spans.',
        'Base socket at fullowner+750 is distinct from nested receive object fullowner+758; do not substitute socket validity or active byte for calling phase.',
        'Next concrete original root: actual0047FC50/0047FAA0 callsites on the scene-selected owner, then exact success continuation where a conditional receiver would be invoked; recover target and ECX there.',
        'No dead-code/global absence or whole-game completion claim follows from bounded eligibility and close writes.',
        'Old173 helper prologues/172 buffer relations/171 lock relations/169/170/global79/3735 stay retained history; no recount or155titleformatter/capacity-chain pursuit.',
        'Original whole function files preserve unrelated logging instructions only for provenance; no logging formatter or capacity analysis is performed.',
    ])
    print(json.dumps({'artifact': str(OUT), 'new_native_relations': len(relations),
        'new_bounded_native_spans': len(new_sites), 'new_bounded_native_bytes': byte_count,
        'retained_helper_spans_not_recounted': len(old_sites),
        'new_confirmed_phases': 0, 'new_complete_routes': 0, 'cpp_edits': 0}))


def capture():
    if not (OUT / 'findings.json').is_file() or (OUT / 'seal.json').exists():
        raise RuntimeError('No unsealed delivery')
    dump('current-source-origins.json', [retain('current/' + rel, SERVER / rel, True) for rel in SOURCE])
    listing = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT / 'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(listing + ['LIST.txt']) + '\n').encode())
    rows = [{'path': p.relative_to(OUT).as_posix(), 'bytes': p.stat().st_size,
             'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    dump('seal.json', {'kind': 'immutable round173 CN conditional receiver-owner lifetime frontier',
        'files': rows, 'native_input_sha256': PIN, 'source_original_count': len(SOURCE),
        'complete_routes_added': 0, 'build_run': False, 'tests_run': False,
        'native_run': False, 'database_access': False})
    print(json.dumps({'sealed': str(OUT), 'seal_sha256': sha((OUT / 'seal.json').read_bytes()),
        'members': len(rows), 'current_source_originals': len(SOURCE)}))


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--capture-after-batchfinal']:
        capture()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit('Only static extraction or explicit BATCHFINAL capture is supported')
