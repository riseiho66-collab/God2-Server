"""Round187 static source provenance; file copying/hashing only, no code execution."""
from pathlib import Path
import hashlib
import json

SERVER = Path(__file__).resolve().parents[2]
ROUND = SERVER / 'artifacts/integration/packet-connections-20261006/native-spectator-ui-publication-source-01'
OUT = ROUND / 'agents/tw-spectator-publication-host'
OWN = 'tools/reconstruction/tw_spectator_publication_host187.py'
MODIFIED = ['src/game/SharedTaiwanNativeSpectatorSource.h',
    'src/game/SharedTaiwanNativeSpectatorSource.cpp',
    'src/core/SharedTaiwanNativeWorldHostPlan.h',
    'src/core/SharedTaiwanNativeWorldHostPlan.cpp']
STABLE = MODIFIED + ['src/game/SharedTaiwanNativeRecordHandlerSource.h',
    'src/game/SharedTaiwanNativeRecordHandlerSource.cpp', 'src/core/SharedWorldHostPlan.h',
    'src/protocol/RecoveredSpectator6E.h', 'src/protocol/RecoveredSpectatorTargetsD0.h',
    'src/protocol/RecoveredWorldRecords.h', 'src/game/SharedWorldPresence.h',
    'src/game/SharedWorldPresence.cpp', 'src/protocol/RecoveredWorldFrame.h']
CONTEXT = ['src/game/SharedWorldHost.h', 'src/game/SharedWorldHost.cpp',
    'src/game/SharedNativeWorldTransports.h', 'src/game/SharedNativeWorldTransports.cpp',
    'src/game/SharedNativeSpectatorPublication.h', 'src/game/SharedNativeSpectatorPublication.cpp',
    'src/cn/protocol/CnSpectatorTargetsD0.h',
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
    if sha(manifest.read_bytes()) != '4bd04968a085573630848601024f740b49f5e72fcb513b0efdac6c044ab45f13':
        raise ValueError('Exact freshbefore1333 manifest required')
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
            'epoch': 'Full actual freshbefore1333 source, not current original'})
        before.append(saved)
    dump('before-source-origins.json', before, True)
    ready = json.loads((OUT / 'source-ready-source-origins.json').read_bytes())
    for row in ready:
        raw = (OUT / row['copy']).read_bytes()
        if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
            raise ValueError('Actual source-ready copy changed: ' + row['copy'])
    current = [retain(f'current/c{n:02d}{Path(rel).suffix}', SERVER / rel)
        for n, rel in enumerate(STABLE + [OWN])]
    context = [retain(f'context-final/k{n:02d}{Path(rel).suffix}', SERVER / rel)
        for n, rel in enumerate(CONTEXT)]
    dump('current-source-origins.json', current)
    dump('context-final-source-origins.json', context)
    dump('source-changes.json', [{'path': rel,
        'before_sha256': next(row['sha256'] for row in before if row['path'] == rel),
        'first_draft_sha256': next(row['sha256'] for row in intermediate if row['path'] == rel),
        'source_ready_sha256': next(row['sha256'] for row in ready if row['path'] == rel),
        'final_sha256': next(row['sha256'] for row in current if row['path'] == rel)} for rel in MODIFIED])
    dump('original-inputs.json', [{**row, 'path': str((SERVER / row['path']).resolve())}
        for row in current + context])
    dump('native-original-inputs.json', [])
    dump('derived-inputs.json', [retain('derived/freshbefore1333.json', manifest,
        str(manifest.resolve()))])
    dump('source-epochs.json', {'before': 'Actual pre-edit own4 plus full freshbefore1333 sources.',
        'intermediate': 'Actual first187 draft own4 and unrun provenance tool against common exact API draft, before final common/Host source integration.',
        'source_ready': 'Actual complete own4/tool capture before parent BATCHFINAL187, separate saved epoch.',
        'current': 'Actual stable source originals after BATCHFINAL187.',
        'context_final': 'Actual root Host/common publication/view and governing documents, separate from current pins.',
        'absent_freshbefore1333': absent + [OWN], 'excluded_current_pins': CONTEXT,
        'missing_transient_epochs': []})
    sites = []
    for rel in MODIFIED + CONTEXT:
        for n, line in enumerate((SERVER / rel).read_text(encoding='utf-8').splitlines(), 1):
            if any(key in line for key in ['native_ui', 'with_native_chat_spectator_and_publication',
                    'registry_current', 'publication->', 'native_spectator_publication', 'selected!=publication']):
                sites.append({'path': rel, 'line': n, 'source': line,
                    'scope': 'Actual C++ source operand/caller, not native instruction or route proof'})
    dump('source-sites.json', sites)
    dump('findings.json', {'round': 187, 'BATCHFINAL_received': True,
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
            {'key': 'optional_actual_ui_source', 'scope': 'Spectator create preserves original five-input call and accepts optional exact same-presence/transports publication source. Scope.native_ui nullopt means NotSelected; actual selected statuses remain distinct immutable UI history observations, not permissions.'},
            {'key': 'registered_recipient_history', 'scope': 'snapshot observes publication through saved actual recipient registry Token, qualifies full Lease and same_registration private cap; no actor-low12, name, alias or client raw context is used to select common history.'},
            {'key': 'ui_current_root_brackets', 'scope': 'Pure WorldOwner current is bracketed by complete snapshots; publication current observations are followed by actual root reread and pure UI private-version/endpoint registry checks. Whole UI view/private source identity must remain the same across current.'},
            {'key': 'single_execution_new_postscope', 'scope': 'Actual execute still occurs exactly once. Post-execution snapshot rereads actual UI history/phase/battle incarnation; does not force the original preScope history to remain current after a legitimate mutation. Same-current checks remain mandatory independently.'},
            {'key': 'negative_ui_states', 'scope': 'Missing/Pending/Retired/Unavailable are observable actual facts, not implicit admission or blanket rejection. Publication current means exact observation remains current; InWorld-only native publication queue does not replace C2S WorldOwner authority in legitimate battle transition/mode2.'},
            {'key': 'actual_host_selected_factory', 'scope': 'Explicit with_native_chat_spectator_and_publication validates supplied same-source publication, installs it in actual Context host, rereads exact pointer, constructs typed spectator source from same actual host source. Chat uses the same host presence/transports and does not receive an unused UI pointer. Legacy with_native_chat_and_spectator is unchanged and does not opt into UI history.'}],
        'gaps': ['Actual spectator WorldOwner/admission/battle mutation/expected postphase suppliers remain mandatory OPEN.',
            'Actual CD/D0 target mapping/update/reset/issuer/UI epoch lifecycle/native release suppliers remain mandatory OPEN.',
            'Application/Main installation and enabled gameplay cannot be inferred from optional source factory/capability.',
            'No new native producer/consumer source or complete game route recovered; whole-game percentage unknown.'],
        'builds_tests_runtime_native_api_codec_db_deploy': False})
    with (OUT / 'README.txt').open('xb') as stream:
        stream.write(('Round187 actual TW spectator UI publication source composition.\n'
            'Own4 C++ sources; native inputs/spans/relations/opcodes/phases/fullroutes0.\n'
            'Optional immutable actual recipient UI history in pre/post Scope, saved actual registered Token, current/root/private-version bracketing.\n'
            'Explicit supplied same-source publication installed in actual common host and passed to typed spectator source.\n'
            'Legacy routing preserved; spectator authority/target issuer/Main remain OPEN.\n'
            'Full actual before/first intermediate/current/final context copies; static file capture only.\n').encode())
    paths = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    with (OUT / 'LIST.txt').open('xb') as stream:
        stream.write(('\n'.join(sorted(paths + ['LIST.txt'])) + '\n').encode())
    members = [{'path': p.relative_to(OUT).as_posix(), 'bytes': p.stat().st_size,
        'sha256': sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file()]
    seal = {'round': 187, 'immutable': True, 'members': members,
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
