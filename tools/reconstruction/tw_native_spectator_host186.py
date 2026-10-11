"""Round186 static source provenance; file copying/hashing only, no code execution."""
from pathlib import Path
import hashlib
import json

SERVER = Path(__file__).resolve().parents[2]
ROUND = SERVER / 'artifacts/integration/packet-connections-20261006/tw-native-spectator-record-source-01'
OUT = ROUND / 'agents/tw-spectator-mixed-host'
OWN = 'tools/reconstruction/tw_native_spectator_host186.py'
MODIFIED = ['src/game/SharedTaiwanNativeRecordHandlerSource.h',
    'src/game/SharedTaiwanNativeRecordHandlerSource.cpp',
    'src/core/SharedTaiwanNativeWorldHostPlan.h',
    'src/core/SharedTaiwanNativeWorldHostPlan.cpp']
STABLE = MODIFIED + ['src/game/SharedWorldHost.h', 'src/game/SharedWorldHost.cpp',
    'src/core/SharedWorldHostPlan.h', 'src/game/SharedTaiwanNativeChatSource.h',
    'src/game/SharedTaiwanNativeChatSource.cpp', 'src/protocol/RecoveredSpectator6E.h',
    'src/protocol/RecoveredWorldRecords.h', 'src/game/SharedWorldPresence.h',
    'src/game/SharedWorldPresence.cpp', 'src/protocol/RecoveredWorldFrame.h']
CONTEXT = ['src/core/Application.cpp', 'src/game/SharedTaiwanWorldRecordSource.h',
    'src/game/SharedTaiwanWorldRecordSource.cpp', 'src/game/SharedNativeWorldTransports.h',
    'src/game/SharedNativeWorldTransports.cpp', 'src/game/SharedTaiwanNativeSpectatorSource.h',
    'src/game/SharedTaiwanNativeSpectatorSource.cpp', 'src/protocol/RecoveredSpectatorTargetsD0.h',
    'AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(rel, value, replace=False):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('wb' if replace else 'xb') as stream:
        stream.write((json.dumps(value, indent=2) + '\n').encode())


def retain(rel, path, original=None):
    raw = path.read_bytes()
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as stream:
        stream.write(raw)
    return {'path': original or path.relative_to(SERVER).as_posix(), 'copy': rel,
        'bytes': len(raw), 'sha256': sha(raw)}


def main():
    if (OUT / 'seal.json').exists():
        raise RuntimeError('Immutable prior capture must not be overwritten')
    before = json.loads((OUT / 'before-source-origins.json').read_bytes())
    intermediate = json.loads((OUT / 'intermediate-source-origins.json').read_bytes())
    manifest = ROUND / 'before-manifest.json'
    if sha(manifest.read_bytes()) != '8200c1fca67e3d2d2b4c42714c0b294e953481731060e78f9bf3a645275529aa':
        raise ValueError('Exact freshbefore1325 manifest required')
    fresh = {row['path']: row for row in json.loads(manifest.read_bytes())}
    for row in before + intermediate:
        raw = (OUT / row['copy']).read_bytes()
        if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
            raise ValueError('Actual epoch copy changed: ' + row['copy'])
    absent = []
    for n, rel in enumerate(STABLE[4:] + CONTEXT):
        if rel not in fresh:
            absent.append(rel)
            continue
        row = fresh[rel]
        p = ROUND / row['snapshot']
        raw = p.read_bytes()
        if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
            raise ValueError('Freshbefore source copy changed: ' + rel)
        saved = retain(f'before/s{n:02d}{Path(rel).suffix}', p, rel)
        saved.update({'snapshot_original': str(p.resolve()),
            'epoch': 'Full actual freshbefore1325 source, not current original'})
        before.append(saved)
    dump('before-source-origins.json', before, True)
    ready = [retain(f'source-ready/r{n:02d}{Path(rel).suffix}', SERVER / rel)
        for n, rel in enumerate(MODIFIED + [OWN])]
    dump('source-ready-source-origins.json', ready)
    current = [retain(f'current/c{n:02d}{Path(rel).suffix}', SERVER / rel)
        for n, rel in enumerate(STABLE + [OWN])]
    context = [retain(f'context-final/k{n:02d}{Path(rel).suffix}', SERVER / rel)
        for n, rel in enumerate(CONTEXT)]
    dump('current-source-origins.json', current)
    dump('context-final-source-origins.json', context)
    dump('original-inputs.json', [{**row, 'path': str((SERVER / row['path']).resolve())}
        for row in current + context])
    dump('native-original-inputs.json', [])
    dump('derived-inputs.json', [retain('derived/freshbefore1325.json', manifest,
        str(manifest.resolve()))])
    dump('source-epochs.json', {'before': 'Actual pre-edit own4 plus full freshbefore1325 sources.',
        'intermediate': 'Actual first implementation own4 before make_binding rename and initial current check moved inside guarded try.',
        'source_ready': 'Actual complete own4/tool capture after parent BATCHFINAL186; not fabricated earlier capture.',
        'current': 'Actual stable source originals after BATCHFINAL186.',
        'context_final': 'Actual Root5/common3 plus governing documents, separate from current pins.',
        'absent_freshbefore1325': absent + [OWN], 'excluded_current_pins': CONTEXT,
        'missing_transient_epochs': []})
    sites = []
    for rel in MODIFIED + CONTEXT[:8]:
        for n, line in enumerate((SERVER / rel).read_text(encoding='utf-8').splitlines(), 1):
            if any(key in line for key in ['spectator6e', 'with_native_chat_and_spectator',
                    'registry_current', 'std::vector<Source::Record> owned', 'make_binding',
                    'spectator->dispatch', 'spectator->release', 'spectator->invalidate_active']):
                sites.append({'path': rel, 'line': n, 'source': line,
                    'scope': 'Actual C++ source operand/caller, not native instruction or route proof'})
    dump('source-sites.json', sites)
    dump('findings.json', {'round': 186, 'BATCHFINAL_received': True,
        'owned_cpp_edits': 4, 'source_files_modified': MODIFIED,
        'native_original_inputs': 0, 'new_bounded_native_spans': 0,
        'new_bounded_native_bytes': 0, 'new_native_relations': [],
        'retained_bounded_native_spans': 0, 'retained_bounded_native_bytes': 0,
        'new_opcodes': 0, 'new_phase_bindings': 0, 'new_complete_routes': 0,
        'receiver_contexts': 14, 'qualified_receiver_contexts': 12,
        'unresolved_helpers': [{'va': va, 'phase': None, 'slot': None, 'producer': None}
            for va in ['0047DE70', '004812B0']],
        'whole_game_route_denominator': None, 'whole_game_percentage': None,
        'actual_source_connections': [
            {'key': 'mixed_typed_owner', 'scope': 'Explicit chat/spectator/remaining overload requires all actual child callbacks. Only installed typed owner intercepts exact Spectator6E Request; legacy overload leaves6E to remaining source.'},
            {'key': 'complete_batch_before_effects', 'scope': 'Complete Record vector and all exact chat/8B spectator requests are copied and segmented before child dispatch; executes original chat/spectator/maximal-remaining ordering.'},
            {'key': 'encrypted_reply_order', 'scope': 'Actual returned encrypted frames append in dispatch order with existing no_reply consistency and byte budget; no invented6E ACK or D0 emission.'},
            {'key': 'all_child_cleanup', 'scope': 'Each actual chat/spectator/remaining invalidator and release is independently attempted despite exceptions. Recursive invalidation guarded; nested active release poisons observing invocation. First failure preserved after all child attempts.'},
            {'key': 'same_context_factories', 'scope': 'New with_native_chat_and_spectator captures actual common host presence/transports once; both concrete sources use same actual pointers/capacity. Existing with_native_chat routing remains unchanged.'},
            {'key': 'actual_framing_capability', 'scope': 'Adapter actual typed source flag passes WorldRecordSource create, HostPlan actual returned binding and Application installed records parser. Flag is typed framing availability, never gameplay permission.'},
            {'key': 'registry_token_context', 'scope': 'Root registry_current exact copied token retains actual endpoint/incarnation after explicit owner phase transitions; it is not readiness/phase/battle authority.'}],
        'gaps': ['Actual spectator WorldOwner/admission/battle mutation/expected postphase suppliers remain mandatory OPEN.',
            'Actual D0 target mapping/update/reset/issuer/native transmission remain OPEN.',
            'Application/Main installation and enabled gameplay cannot be inferred from optional source factory/capability.',
            'No new native producer/consumer source or complete game route recovered; whole-game percentage unknown.'],
        'builds_tests_runtime_native_api_codec_db_deploy': False})
    with (OUT / 'README.txt').open('xb') as stream:
        stream.write(('Round186 actual TW mixed spectator source composition.\n'
            'Own4 C++ sources; native inputs/spans/relations/opcodes/phases/fullroutes0.\n'
            'Explicit typed owner, full batch copied before effects, actual encrypted reply ordering, all child cleanup attempted.\n'
            'Same actual common host source factories; installed typed framing flag propagates actual returned binding to parser.\n'
            'Legacy routing preserved; spectator authority/target issuer/Main remain OPEN.\n'
            'Full actual before/first intermediate/current/final context copies; static file capture only.\n').encode())
    paths = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT / 'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(sorted(paths + ['LIST.txt'])) + '\n').encode())
    members = [{'path': p.relative_to(OUT).as_posix(), 'bytes': p.stat().st_size,
        'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    seal = {'round': 186, 'immutable': True, 'members': members,
        'member_count': len(members), 'member_bytes': sum(row['bytes'] for row in members),
        'current_source_count': len(current), 'context_original_count': len(context),
        'all_actual_original_count': len(current + context), 'native_original_count': 0}
    dump('seal.json', seal)
    print(json.dumps({key: seal[key] for key in ['member_count', 'member_bytes',
        'current_source_count', 'context_original_count', 'all_actual_original_count', 'native_original_count']}
        | {'files_including_seal': len(members) + 1,
           'seal_sha256': sha((OUT / 'seal.json').read_bytes()),
           'tool_sha256': sha((SERVER / OWN).read_bytes())}))


if __name__ == '__main__':
    main()
