"""Bounded actual TW spectator callers; file copies and static Capstone only.

No process, codec, native, C++, Lua, SQL, DB, API, build or gameplay execution.
Client input/UI conditions are never spectator authorization or an ACK producer.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / 'artifacts/integration/packet-connections-20261006/shared-native-world-transport-source-01'
OUT = ROUND / 'agents/tw-spectator-source-frontier'
OWNED = 'tools/reconstruction/tw_native_spectator_entry184.py'
IMAGE = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
IMAGEPIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE = '008a860dc868ac80a91cd6410b852f9e4b4623033cf17317288a7ee3da051148'
BASE = 0x400000
SOURCES = [
    'src/protocol/RecoveredSpectator6E.h', 'src/protocol/RecoveredWorldRecords.h',
    'src/protocol/RecoveredBattleEntry.h', 'src/protocol/RecoveredRemoteActor.h',
    'src/game/SharedWorldPresence.h', 'src/game/SharedWorldPresence.cpp',
    'src/game/RecoveredCharacter.h', 'src/db/RecoveredCharacterRepository.h',
]
CONTEXT = [
    'AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
    'tools/reconstruction/spectator_6e_contract.py',
    'docs/research/current-spectator6e-20261006.md',
    'docs/research/current-world-interaction-candidate-20260921.md',
    'docs/research/current-battle-entry-20260919.md',
    'docs/research/current-battle-initializer-20260919.md',
    'tools/reconstruction/tw_native_whisper_identity181.py',
    'tools/reconstruction/enemy_native_fields_frontier_v3.py',
    'docs/research/current-battle-command-gate-20260919.md',
]
# All ranges are half-open actual mapped-image RVAs, never virtual fixtures.
SPANS = [
    (0x119B00, 0x119B12, 'retained_battle_command_gate', 'full control wrapper retained conservatively with known119B20 path'),
    (0x119B20, 0x119B32, 'retained_battle_command_gate', 'existing command-gate post-control helper clears local9E9C2C'),
    (0x7B440, 0x7B463, 'new_bounded', 'UI handler entry: selected outer WORD must be nonnegative'),
    (0x7B4B4, 0x7B560, 'new_bounded', 'click bit1, selected record bit4 and local UI selector gates'),
    (0x7B6E6, 0x7B770, 'new_bounded', 'selector3 two-row page target IDs and record lowbits2 to mode1'),
    (0x18950, 0x1896C, 'new_bounded', 'input event dispatcher arg1 minus200, seven entries'),
    (0x18A72, 0x18A8C, 'new_bounded', 'event204 input latch12018 set1,12024 cleared'),
    (0x18AAA, 0x18AC8, 'new_bounded', 'event205 input latch12018/1201C clear,12024 set1'),
    (0x1159BC, 0x1159CA, 'new_bounded', 'battle-loop caller passes local490 input material to113080'),
    (0x66490, 0x666AC, 'expanded_known_caller', 'complete second mode1 caller function including real arg selectors and action table'),
    (0x113080, 0x1130C5, 'retained_frontier_v3', 'exact earlier frontier_v3 observer_exit range; not complete113080 function'),
    (0x97D40, 0x97D71, 'retained_6e', 'existing complete6E raw producer9B, padding unwritten, signed-negative context suppressed'),
    (0x65FA0, 0x65FC5, 'retained_world_interaction', 'existing action plus24 dispatch prefix, action minus17'),
    (0x66229, 0x66285, 'retained_world_interaction', 'existing first selected role-pool DWORD target and mode1 caller'),
    (0xDCF80, 0xDD0F2, 'retained181', 'complete saved181 context menu with action4 selected20B-record DWORD to mode1'),
    (0xFAC70, 0xFAD19, 'retained181', 'existing fullDWORD role-pool name getter, not authorization'),
    (0xFC960, 0xFC98A, 'retained181', 'existing128 role slots stride268 with stored fullDWORD ID lookup'),
    (0x1113B6, 0x1113CC, 'retained_battle_entry', 'existing context secondDWORD lowbyteFF equality -> local9EA4C8'),
    (0x6AE12, 0x6AE2D, 'retained_battle_entry', 'existing S2C82 raw fields -> transition context28/2C'),
]
TABLES = [
    (0x6643C, 80, 'retained_world_interaction', '20 action destinations'),
    (0x666AC, 36, 'new_data', '9 second-caller action destinations'),
    (0x666D0, 19, 'new_data', '19 action selectors, action-16/index8 -> destination4'),
    (0x18B58, 28, 'new_data', '7 input-event destinations,204/205 map to latch writers'),
    (0xDD0F4, 60, 'retained181', '15 context menu action destinations'),
]

def sha(raw): return hashlib.sha256(raw).hexdigest()

def put(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream: stream.write(raw)

def emit(name, value): put(OUT / name, (json.dumps(value, ensure_ascii=True, indent=2) + '\n').encode())

def original(path, target):
    raw = path.read_bytes()
    put(OUT / target, raw)
    return {'path': path.resolve().as_posix(), 'copy': target, 'bytes': len(raw), 'sha256': sha(raw)}

def recover():
    native = IMAGE.read_bytes()
    fresh = (ROUND / 'before-manifest.json').read_bytes()
    manifest = json.loads(fresh)
    if sha(native) != IMAGEPIN or len(native) != 3174400 or sha(fresh) != BEFORE or len(manifest) != 1313:
        raise RuntimeError('Exact actual native/freshbefore differs; do not replace baseline')
    put(OUT / 'epoch/root-before.raw', fresh)
    emit('epoch.json', {'round': 184, 'before_inputs': 1313, 'before_sha256': BEFORE,
                       'baseline_replaced': False, 'source_static_only': True})
    emit('original-inputs.json', [original(IMAGE, 'originals/native-image.bin')])
    emit('context-origins.json', [original(ROOT / f, f'context/c{n:02}{Path(f).suffix}') for n, f in enumerate(CONTEXT)])
    index = {row['path']: row for row in manifest}
    before = []
    for n, f in enumerate(SOURCES):
        row = index[f]
        raw = (ROUND / row['snapshot']).read_bytes()
        if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
            raise RuntimeError('Root original before does not match exact manifest')
        target = f'before/b{n:02}{Path(f).suffix}'
        put(OUT / target, raw)
        before.append({'path': (ROOT / f).resolve().as_posix(), 'copy': target, 'bytes': len(raw), 'sha256': sha(raw)})
    before.append({'path': (ROOT / OWNED).resolve().as_posix(), 'present': False, 'reason': 'NEW file absent from root freshbefore'})
    emit('before-source-origins.json', before)
    emit('intermediate-origins.json', [original(ROOT / OWNED, 'intermediate/writer-01.py')])
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    spans, sites = [], []
    for n, (lo, hi, category, purpose) in enumerate(SPANS):
        raw = native[lo:hi]
        target = f'raw/s{n:02}.bin'
        put(OUT / target, raw)
        rows = [{'rva': i.address-BASE, 'va': i.address, 'bytes': i.bytes.hex(),
                 'mnemonic': i.mnemonic, 'operands': i.op_str} for i in decoder.disasm(raw, BASE+lo)]
        if sum(len(bytes.fromhex(i['bytes'])) for i in rows) != len(raw):
            raise RuntimeError('Bounded span does not end at an actual complete instruction')
        emit(f'derived/s{n:02}.json', rows)
        spans.append({'rva_start': lo, 'rva_end': hi, 'va_start': BASE+lo, 'va_end': BASE+hi,
                      'copy': target, 'bytes': len(raw), 'sha256': sha(raw), 'classification': category,
                      'purpose': purpose, 'instructions': len(rows)})
        for row in rows:
            if row['mnemonic'].startswith(('j', 'ret')) or row['mnemonic'] in ('call', 'cmp', 'test', 'sete'):
                sites.append(dict(row, span=n, classification=category))
    emit('native-spans.json', spans)
    emit('instruction-sites.json', sites)
    tables = []
    for n, (rva, length, category, purpose) in enumerate(TABLES):
        raw = native[rva:rva+length];target = f'raw/t{n:02}.bin';put(OUT / target, raw)
        values = list(raw) if length == 19 else list(struct.unpack('<'+'I'*(length//4), raw))
        tables.append({'rva': rva, 'va': BASE+rva, 'bytes': length, 'copy': target,
                       'sha256': sha(raw), 'classification': category, 'purpose': purpose, 'values': values})
    emit('data-sites.json', tables)
    source_sites = []
    keys = ('spectator', 'Spectator', 'context()', 'actor_handle', 'ready_lease', 'uint64_t', 'reserve_battle', 'settle_battle')
    for f in SOURCES:
        raw = (ROOT / f).read_bytes()
        for n, line in enumerate(raw.decode('utf-8-sig').splitlines(), 1):
            if any(key in line for key in keys):
                source_sites.append({'path': f, 'line': n, 'text': line, 'actual_source_sha256': sha(raw)})
    emit('source-sites.json', source_sites)
    categories = {}
    for row in spans:
        totals = categories.setdefault(row['classification'], {'spans': 0, 'bytes': 0})
        totals['spans'] += 1;totals['bytes'] += row['bytes']
    findings = {
        'round': 184, 'scope': 'bounded native spectator UI/input/target source; no game C++ edits',
        'native_originals': 1, 'native_original_bytes': len(native), 'spans': len(spans),
        'span_bytes': sum(row['bytes'] for row in spans), 'span_categories': categories,
        'instruction_sites': len(sites), 'data_sites': len(tables), 'source_sites': len(source_sites),
        'retained_contract': 'C2S6E total9, raw body1..3 unwritten stack bytes, mode1 four callers, mode2/context0 one; not new opcode',
        'new_relations': [
            '466490: arg2 selector3 gets world1539683C self ID; selector>=4 gets selector-4; selector<4 gets arg1. selector2 restricts action-12. After self-target comparison action-16 selector table routes66661E/666642. Role lookup uses15383410. Both role-pool mode1 callers ignore the FAC70 lookup result; sending does not prove the raw target exists.',
            '47B440: outer signedWORD232E48>=0; click bit1; selected signedWORD232E4A>=0; selected indexed record E2988 bit4; local89E3C=1,89BD6=1,89E28=3; control14..24 or25..35 with page89BBC selects rawDWORD89A2C/89AF4. ID!=-1 and record88A95 low2bits=2 -> mode1. Source generation and ID supplier not recovered.',
            '12018 is an input event latch: event204 sets1, event205 clears it through actual418950 table. It is not a server battle-state or authorization field.',
            '1159C5 calls113080 with B+490 input material during the battle loop. Existing S2C82 secondDWORD lowbyteFF sets [B+0xA9EA4C8] in1113BF. This retained predicate ties the new UI branch to a received entry context, not to proof of server authorization.',
        ],
        'retained_relations': [
            '113080: local[B+0xA9EA4C8]=1 and input[B+4]+12018!=0 -> mode2/context0; then119B20 clears[B+0xA9E9C2C] and forwards control1/1 through119B00 to4834E0; [B+0xAB3B8B8] becomesFFFF. The entire69B branch was already saved frontier_v3; command-gate history already records119B20.',
            'Old frontier_v3 also records cursor10 watch selection ->82013 action-17 ->66229 and the82 lowbyteFF observer-exit connection. These are historical retained relationships, not new184 qualification or server rights.',
        ],
        'source_actions': [
            'The first two mode1 callers prove a role-pool lookup namespace for the raw native DWORD, not valid actor existence. Resolve an independently qualified published actor to an exact common session/account/character lease and battle incarnation, with publication epoch/current proof. The other UI-list and external-menu target supplier namespaces remain OPEN; do not universalize the role-pool proof across all four callers. Never cast/mask a target into common64 character ID or directly treat it as battle ID.',
            'Mode2 context0 must use an already owned spectator membership and exact current battle incarnation/entry provenance. Zero is not a globally valid target or unrestricted leave right.',
            'Actual server policy, full entry fields, participant audience, current battle lifetime and spectator eligibility must be supplied by their owning authority. These client-side gates do not supply those rights.',
        ],
        'gaps': [
            'UI89A2C/89AF4 actual ID supplier/generation and UI menu40614 original issuer remain OPEN.',
            'Ordinary actor vs battle incarnation source binding and server spectator admission/exit policy remain OPEN.',
            'No S2C6E ACK or server82 authoritative fields are inferred; opposite-direction6E is independent.',
            'Input event204/205 latch and downstream4834E0 control behavior are not generalized into server battle semantics.',
        ],
        'source_before': len(SOURCES), 'source_current_expected': len(SOURCES)+1,
        'new_cpp': 0, 'new_opcodes': 0, 'fully_connected_routes': 0, 'whole_game_percent': None,
        'execution': {'build': 0, 'tests': 0, 'native': 0, 'codec': 0, 'database': 0, 'API': 0, 'deployment': 0},
        'forbidden_chain_followed': False,
    }
    emit('findings.json', findings)
    emit('derived-inputs.json', [{'path': f'derived/s{n:02}.json', 'kind': 'Capstone static decode of exact saved original raw span'} for n in range(len(spans))])
    print(json.dumps(findings, ensure_ascii=True))

def capture():
    current = [original(ROOT / f, f'current/c{n:02}{Path(f).suffix}') for n, f in enumerate(SOURCES+[OWNED])]
    emit('current-source-origins.json', current)
    findings = json.loads((OUT/'findings.json').read_bytes())
    put(OUT/'README.txt', (
        'Round184, phase1 source/static only. Native image offset==RVA, VA=400000+RVA.\n'
        '19 bounded/complete saved spans; category totals in findings. Prior facts stay retained; no new opcode.\n'
        'Mode1 native role/UI actor DWORD is distinct from common64 character/battle IDs.\n'
        'Mode2 context0 is gated by received-entry localFF sentinel plus an input event latch, not server rights.\n'
        'Actual owner policy and current spectator/battle incarnation remain mandatory.\n'
        'Original full native/source/before copies are listed separately from derived decode and historical context.\n'
        'No game CPP edits, runtime/build/tests/codec/DB/API/deployment. Connected routes0; percent unknown.\n'
    ).encode())
    members = []
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name != 'seal.json':
            raw = path.read_bytes();members.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)})
    emit('seal.json', {'round': 184, 'members': members, 'member_count': len(members),
                       'all_originals_fully_copied': True, 'whole_game_percent': None})
    print(json.dumps({'seal_sha256': sha((OUT/'seal.json').read_bytes()), 'sealed_members': len(members),
                      'total_files': len(members)+1, 'current_originals': len(current),
                      'native_originals': findings['native_originals'], 'tool_sha256': sha((ROOT/OWNED).read_bytes()),
                      'tool_bytes': len((ROOT/OWNED).read_bytes())}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('action', choices=('recover', 'capture'))
    args = parser.parse_args()
    (recover if args.action == 'recover' else capture)()
