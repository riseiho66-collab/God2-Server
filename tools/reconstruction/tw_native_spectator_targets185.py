"""Actual TW spectator target publication; file/static Capstone only.

No codec, client, native, C++, SQL/DB, API, build, tests or emulation execution.
Raw native WORD targets do not identify a common character or battle by themselves.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT/'artifacts/integration/packet-connections-20261006/native-world-transport-host-composition-01'
OUT = ROUND/'agents/tw-spectator-target-publication'
OWNED = 'tools/reconstruction/tw_native_spectator_targets185.py'
IMAGE = ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE = 'a859ae7a16f0f7e331ccd54416e6273a9a9149635c108d8d2a8c3a9688323fc9'
BASE = 0x400000
SOURCES = [
    'src/protocol/RecoveredSpectator6E.h', 'src/protocol/RecoveredWorldRecords.h',
    'src/protocol/RecoveredTaiwanServerRecords.h', 'src/protocol/RecoveredRemoteActor.h',
    'src/game/SharedWorldPresence.h', 'src/game/SharedWorldPresence.cpp',
]
CONTEXT = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
           'tools/reconstruction/tw_native_spectator_entry184.py']
SPANS = [
    (0x78CC0,0x78D08,'new_complete','full D0 consumer writes two zeroextendedWORD UI targets and exactflagbits'),
    (0x78D10,0x78E19,'new_complete','full CD consumer updates flags/metadata/raw22B fields, no targetarray write'),
    (0x69DE2,0x69E06,'new_bounded','exact world CD/D0 cases pass body after opcode, no server authority'),
    (0x77850,0x778E0,'expanded_prior_read_reset','bounded initializer clears records and sets two targetarrays FFFFFFFF; not full function'),
    (0x12BE,0x12C4,'retained169_grammar','existing native fixed CD length65, not length inferred from largest field'),
    (0x12CA,0x12D0,'retained169_grammar','existing native fixed D0 length7'),
    (0x7B6E6,0x7B770,'retained184','existing two rows select targetDWORD and lowflagbits2 then send6E mode1'),
    (0x97D40,0x97D71,'retained6e','existing full 6E producer writes mode/context, leaves three padding bytes untouched'),
]
TABLES = [(0x1324+0xCD*4,'CD lengthtable entry'),(0x1324+0xD0*4,'D0 lengthtable entry'),
          (0x6B5D4+0xCD*4,'CD worldtable entry'),(0x6B5D4+0xD0*4,'D0 worldtable entry')]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
    raw=path.read_bytes();put(OUT/target,raw)
    return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)}

def recover():
    native=IMAGE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();before=json.loads(fresh)
    if len(native)!=3174400 or sha(native)!=PIN or len(before)!=1320 or sha(fresh)!=BEFORE:
        raise RuntimeError('Exact original input/before differs; do not replace baseline')
    put(OUT/'epoch/root-before.raw',fresh)
    emit('epoch.json',{'round':185,'root_before_inputs':1320,'root_before_sha256':BEFORE,
                      'baseline_replaced':False,'phase':'source/static only'})
    emit('original-inputs.json',[original(IMAGE,'originals/native-image.bin')])
    emit('context-origins.json',[original(ROOT/f,f'context/c{n:02}{Path(f).suffix}') for n,f in enumerate(CONTEXT)])
    index={row['path']:row for row in before};origins=[]
    for n,f in enumerate(SOURCES):
        row=index[f];raw=(ROUND/row['snapshot']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Protected before differs')
        target=f'before/b{n:02}{Path(f).suffix}';put(OUT/target,raw)
        origins.append({'path':(ROOT/f).resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)})
    origins.append({'path':(ROOT/OWNED).resolve().as_posix(),'present':False,'reason':'new file absent at root freshbefore'})
    emit('before-source-origins.json',origins)
    emit('intermediate-origins.json',[original(ROOT/OWNED,'intermediate/writer-01.py')])
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];sites=[];counts={}
    for n,(lo,hi,classification,purpose) in enumerate(SPANS):
        raw=native[lo:hi];target=f'raw/s{n:02}.bin';put(OUT/target,raw)
        rows=[{'rva':i.address-BASE,'va':i.address,'bytes':i.bytes.hex(),
               'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoder.disasm(raw,BASE+lo)]
        if sum(len(bytes.fromhex(row['bytes'])) for row in rows)!=len(raw):
            raise RuntimeError('Range is not an exact complete-instruction span')
        emit(f'derived/s{n:02}.json',rows)
        spans.append({'rva_start':lo,'rva_end':hi,'va_start':BASE+lo,'va_end':BASE+hi,
                      'copy':target,'bytes':len(raw),'sha256':sha(raw),'classification':classification,
                      'purpose':purpose,'instructions':len(rows)})
        total=counts.setdefault(classification,{'spans':0,'bytes':0});total['spans']+=1;total['bytes']+=len(raw)
        for row in rows:
            if row['mnemonic'] in ('mov','movzx','cmp','test','call','ret','and','or','rep stosd','rep movsd','add') or row['mnemonic'].startswith('j'):
                sites.append(dict(row,span=n,classification=classification))
    emit('native-spans.json',spans);emit('instruction-sites.json',sites)
    tables=[]
    for n,(rva,purpose) in enumerate(TABLES):
        raw=native[rva:rva+4];target=f'raw/t{n:02}.bin';put(OUT/target,raw)
        tables.append({'rva':rva,'va':BASE+rva,'bytes':4,'copy':target,'sha256':sha(raw),
                       'classification':'retained169_table','purpose':purpose,'value_va':struct.unpack('<I',raw)[0]})
    emit('data-sites.json',tables)
    source_sites=[]
    keys=('spectator','Spectator','context()','identity()','actor_handle','ready_lease','uint64_t','/*C0*/','/*D0*/','native_lengths')
    for f in SOURCES:
        raw=(ROOT/f).read_bytes()
        for n,line in enumerate(raw.decode('utf-8-sig').splitlines(),1):
            if any(k in line for k in keys):source_sites.append({'path':f,'line':n,'text':line,'actual_source_sha256':sha(raw)})
    emit('source-sites.json',source_sites)
    findings={
        'round':185,'scope':'bounded UI target publication D0/CD and reset; source/static only',
        'native_originals':1,'native_original_bytes':len(native),'spans':len(spans),
        'span_bytes':sum(row['bytes'] for row in spans),'span_categories':counts,
        'instruction_sites':len(sites),'data_sites':len(tables),'source_sites':len(source_sites),
        'new_relations':[
            'S2C D0 worldcase69DF4 increments record pointer to body and calls78CC0. Body0 unsignedBYTE slot writes zeroextended body+2/+4 WORDs to owner+89A28+4*slot /89AF0+4*slot. For slot1..50 these are arrays89A2C/89AF4 at slot-1.',
            'D0 body1 is not consumed by this callee. Flag at owner+88A59+60*slot equals record88A95 at slot-1; exact operation (old & FE)|02 sets low2bits to2, preserving bits2..7.',
            'D0 targetWORD FFFF becomes DWORD0000FFFF, not FFFFFFFF. The retained caller only rejects FFFFFFFF, and97D40 accepts a nonnegative context. Do not invent a FFFF invalid-target sentinel.',
            'S2C CD worldcase69DE2 passes body to78D10. Body4 is unsigned one-based slot; body1 selector2 writes flags=(old&3C)|(body5&C3), copies body10/26 to two22B raw fields. Selector1 writes rawDWORD body8/C to88A98/88A9C. Selector0 adds body6 WORD modulo16bits, changes onlyflag30bits and writes those metadataDWORDs. MetadataDWORDs are not D0 targetarrays.',
            'CD fixed logical65 includes64 bodybytes. This function maximum read is body59; remaining bytes are opaque and length must remain65. D0 fixed logical7 includes six rawbodybytes.',
        ],
        'retained_and_expanded':[
            '184 caller7B6E6..7B770 already chooses two UI arrays by page/control and requires flags low2bits2, then queues mode1; no new opcode or connected route.',
            'Reset77850..778E0 was locally read184 but not recovered as a full function; retain as expanded prior-read context. It clears750 DWORDs=3000B=50*60B at88A94, initializes page89BBC=0, and writes50DWORDs ofFFFFFFFF to each targetarray. Do not claim the whole initializer or loaded runtime state.',
            '169 native length grammar already records CD65 and D07. Exact leaf/table originals retained, not new format endpoints.',
        ],
        'source_constraints':[
            'Future source admission can explicitly qualify slot1..50 against the proven50-record storage; native78CC0/78D10 do not check this range. Body slot0 and51..255 are not native rejection cases and must not be generalized into a safe native bound.',
            'Bind the exact D0 publication, recipient/entry UI owner generation, slot, both original WORD target operands and retained rawbody to an actual owner-supplied target identity mapping and currentbattle incarnation. Do not use a value cast,6F low12 mask, rolepool lookup or displayname join as that proof.',
            'CD can modify state flags separately while old targetarray values persist. Current qualification must cover both publication and subsequent update/reset/replacement lifecycle; lowbits2 alone cannot make an old target current.',
            'TargetWORD namespace, issuing server policy, audience, battle creation/membership and true owner lifecycle issuer remain OPEN. No guessed S2C6E ACK or unconditional target admission.',
        ],
        'open':{'D0_target_namespace':None,'D0_server_identity_issuer':None,'current_entry_binding_issuer':None,
                'server_spectator_authorization':None,'server_S2C6E_ACK':None},
        'source_before':len(SOURCES),'source_current_expected':len(SOURCES)+1,
        'new_cpp':0,'new_opcodes':0,'fully_connected_routes':0,'whole_game_percent':None,
        'execution':{'native':0,'codec':0,'build':0,'tests':0,'API':0,'DB':0,'deployment':0},
        'forbidden_formatter_chain_followed':False,
    }
    emit('findings.json',findings)
    emit('derived-inputs.json',[{'path':f'derived/s{n:02}.json','kind':'static Capstone decode of copied original native span'} for n in range(len(spans))])
    print(json.dumps(findings,ensure_ascii=True))

def capture():
    current=[original(ROOT/f,f'current/c{n:02}{Path(f).suffix}') for n,f in enumerate(SOURCES+[OWNED])]
    emit('current-source-origins.json',current)
    put(OUT/'README.txt',(
        '185 bounded target publication source; no game C++ edits. VA=400000+RVA, mapped file offset==RVA.\n'
        'D0 two raw WORDs zeroextend into UI DWORD arrays; CD flags/metadata are separate.\n'
        'Unchecked native slot writer is not a server range/rights proof. Namespace and currentissuer remain OPEN.\n'
        'Whole original input/source/before copies are separate from derived disassembly and retained context.\n'
        'No execution/native/codec/build/tests/API/DB/deploy. New routes0; wholegame percent unknown.\n'
    ).encode())
    members=[]
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name!='seal.json':
            raw=path.read_bytes();members.append({'path':path.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    emit('seal.json',{'round':185,'members':members,'member_count':len(members),'all_actual_originals_fully_copied':True})
    tool=(ROOT/OWNED).read_bytes()
    print(json.dumps({'seal_sha256':sha((OUT/'seal.json').read_bytes()),'sealed_members':len(members),
                      'total_files':len(members)+1,'current_originals':len(current),'current_original_bytes':sum(r['bytes'] for r in current),
                      'tool_bytes':len(tool),'tool_sha256':sha(tool)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('recover','capture'))
    args=parser.parse_args();(recover if args.action=='recover' else capture)()
