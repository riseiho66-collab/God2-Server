"""211 original Taiwan07 receive/selection data boundaries, static file only."""
from pathlib import Path
import json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-character-list-source-01/agents/tw-list-selected-record'
PRIOR=ROOT/'artifacts/integration/packet-connections-20261006/tw-stored-entry-host-composition-01/agents/tw-entry-caller-inputs'
PE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(name,v):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copies(paths,folder):
    result=[]
    for i,p in enumerate(paths):
        p=Path(p);p=p if p.is_absolute() else ROOT/p;b=p.read_bytes();copy=f'{folder}/{i:02d}-{p.name}'
        q=OUT/copy;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        result.append(dict(path=str(p.resolve()),copy=copy,bytes=len(b),sha256=sha(b)))
    return result
def main():
    if (OUT/'seal.json').exists():raise RuntimeError('Preserve sealed211')
    OUT.mkdir(parents=True,exist_ok=True)
    guides=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
    current=copies(guides+['tools/reconstruction/tw_native_character_list211.py',
        'src/protocol/RecoveredCharacterListCandidate.h','src/protocol/LegacyCharacterListCandidate.h'],'current')
    originals=current+copies(['docs/research/current-login-character-socket-topology-20260919.md',
        'docs/research/original-client-create-profile-20260919.md',
        'docs/research/recovered-character-persistence-20260919.md',
        'tests/research/test_current_character_list_handler.py',
        'tests/research/test_current_existing_character_selection.py'],'originals')
    dump('current-source-origins.json',current);dump('original-inputs.json',originals)
    sr=(PRIOR/'seal.json').read_bytes()
    if sha(sr)!='4ad3a0c0db0341f81a1833e8d0f7e9f2f09ce021e7965fddad1a9c3760312d9f':raise RuntimeError('Prior210 differs')
    refs=[]
    for p in sorted(PRIOR.rglob('*')):
        if p.is_file():
            b=p.read_bytes();refs.append(dict(path=str(p.resolve()),relative=p.relative_to(PRIOR).as_posix(),bytes=len(b),sha256=sha(b)))
    dump('prior210-whole-inplace-references.json',refs)
    retained=copies([PRIOR/n for n in ['seal.json','findings.json','call-argument-diagram.json','native-spans.json',
        'native/retained-selected40-data-copy.bin','native/retained-selected40-data-copy.instructions.json']], 'retained210')
    dump('retained-source-origins.json',retained)
    raw=PE.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Native image identity differs')
    dump('native-input-references.json',[dict(path=str(PE.resolve()),bytes=len(raw),sha256=sha(raw),copied=False,
        full_inplace_hash=True,old_master_present=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').exists(),
        qualification='Mapped native master only; no installedfont restored99c substitution or current baseline refresh.')])
    slices=[('list-size-leaf',0x12d6,0x12dc),('main-initializer-stack',0x4010,0x4035),
        ('caller-six-arguments',0xdf29,0xdf52),('raw-list-pointer-binding',0x456c,0x4592),
        ('main-list-request-boundary',0xb490,0xb4d5),('list-opcode-discriminator',0x14830,0x14844),
        ('receive-raw74',0x148b9,0x148cb),('optional-conversion-and-lowflag',0x148cb,0x1495e),
        ('selected-count-compare',0x5b76,0x5b89),('selected-copy40',0x5bb6,0x5be9),
        ('route-token-and-routing-byte',0x12310,0x12362)]
    md=Cs(CS_ARCH_X86,CS_MODE_32);spans=[]
    for name,a,z in slices:
        b=raw[a:z];ins=list(md.disasm(b,a+0x400000))
        if sum(i.size for i in ins)!=len(b):raise RuntimeError('Partial static instruction boundary: '+name)
        copy='native/'+name+'.bin';q=OUT/copy;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        rows=[dict(va=f'{i.address:08X}',file_offset=i.address-0x400000,bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in ins]
        dump('native/'+name+'.instructions.json',rows)
        spans.append(dict(name=name,va=f'{a+0x400000:08X}',end_exclusive_va=f'{z+0x400000:08X}',file_offset=a,
            bytes=len(b),sha256=sha(b),copy=copy,instructions=len(rows),
            classification='Retained known native source re-read; new global coverage not asserted. Current211 bounded capture may extend prior210 local span inventory.'))
    dump('native-spans.json',spans)
    layout=dict(logical_bytes=75,body_bytes=74,standalone_outer_bytes=78,
        opcode=dict(logical_offset=0,value='07'),
        count=dict(body_offset=0,logical_offset=1,width='BYTE',not_LE_WORD=True),
        flags=dict(body_offset=1,logical_offset=2,width='BYTE',observed_mask='01',destination='L+4200 thenG+4200'),
        rows=dict(body_offsets=[2,38],logical_offsets=[3,39],stride=36,physical_wire_rows=2,
                  name='raw row0..15; caller name must terminate within actual bounded owned name region, native scans do not enforce16'),
        token=dict(row_offset=19,mask='07',scope='Opaque native selected-routing token, not commonID/slot permission'),
        route=dict(row_offset=32,scope='Matches actual separately advertised04/05/06 endpoint route; not IP/port in07'),
        count_guard='Receiver copies fixed74 and optional projection iterates rawcount; no receiver clamp<=2 in bounded sites. Existing server capacity policy must not be described as native validation.',
        order='Physical raw order retained; token low3 and display ordinal are separate namespaces. No reorder/dedup/commonID inference.')
    dump('wire-layout.json',layout)
    boundary=dict(application='A is real DE80 application owner; M is login/selection object A+43C',
        raw_pointer='DF29/DF2F/DF35/DF3C pass6th&A+1A4 and5th&A+158 to4010;4010 entrySEH+locals108+4registers=124, ESP138 isarg5;456C/458C store&A158 toM178CE0.',
        incoming='148BD sourcepacket+1;18DWORD+WORD=74 bytes into actual&A158; no copying checksum or bytes beyond74.',
        selected0=dict(raw_span='[2,42)',wire_row='[2,38)',tail4='[38,42) equals first4 bytes of second physical wire row, even when inactive.'),
        selected1=dict(raw_span='[38,78)',wire_row='[38,74)',tail4='[74,78) outside74receivedbody',
            actual_addresses='A+1A2..A+1A5; first2 lie after raw body, next2 overlap separate caller input region rooted&A+1A4',
            unknown='Backing/tail current values and initialization unknown. Do not appendzero/checksum/nextpacket or copycreateprofile to invent this suffix.'),
        selected_check='5B80 signed WORDordinal compared to zeroextendedBYTEcount; selectedcopy movsxWORD. Boundedcopy has no independent lower-bound check, no new safe ordinal authority inferred.',
        name_chain='210 already proves copiedbufferDE80local30 ->64910arg2 ->68160 firstarg ->R+B7; name prefix lies inside selected36row independently of trailing4.',
        not_equivalent=['raw36 wire row','optional projected40 record','selected40 backing-memory copy','create40 owned profile'],
        optional_projection='Null on mainB490 path. When selected:124bytes destinationzeroed; count copied; per40row name/rawW16/W17/W18/tokenW19&7 are projected. RawW20..35/hightokenbits/namepadding discarded, not invertible.',
        actual_encoding='No codepage field recovered in07 or memcpy; source/name bytes require external actual native selection/name-codepage/current/provenance qualifier. Default CP950 or displayconversion cannot replace originalbytes.',
        next_action='Supply immutable full raw75logical/74body with actual count/flags/order/token/routes and own selected-root/name/source-epoch Current. If selected40 semantics required, retain separately qualified backing4; for name-only use original boundedrow prefix rather than fabricated40profile.')
    dump('source-boundaries.json',boundary)
    dump('findings.json',dict(round=211,scope='TW07 receive/selected data boundary static reconciliation',
        wire_layout='wire-layout.json',actual_source_boundaries='source-boundaries.json',
        key_change_to_next_action='Fullselected40 lastrow suffix is not sent in07. Store rawwire and selectedname qualification distinctly; reject fabricatedtail/profile equivalence.',
        source_paths=[r['path'] for r in originals],prior210_inplace_files=len(refs),
        root_mutable_cpp_read=False,no_CPP_changes=True,no_codec=True,no_runtime=True,no_DB=True,no_tests=True,
        retained_spans=len(spans),retained_bytes=sum(s['bytes'] for s in spans),retained_instructions=sum(s['instructions'] for s in spans),
        new_native_coverage=0,new_opcode=0,new_complete_routes=0,whole_game_percentage=None,
        unresolved=['actualserver-owned raw07 serializer/current issuer','selectedname fullcommonroot/current and encoding qualification',
            'clientbacking bytes74..77 source/lifetime','fullnative entry/resources/initialpeers/Main','all TW branch/state/variant source denominator'],
        evidence_levels='Existing synthetic test source files were read only as retained source context; not executed and do not prove current native acceptance.',
        stop='Bounded211 agent ends; parent TW-first goal remains active.'))
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p!=OUT/'seal.json' and p!=OUT/'LIST.json':
            b=p.read_bytes();members.append(dict(path=p.relative_to(OUT).as_posix(),bytes=len(b),sha256=sha(b)))
    dump('LIST.json',members);b=(OUT/'LIST.json').read_bytes();members.append(dict(path='LIST.json',bytes=len(b),sha256=sha(b)))
    dump('seal.json',dict(members=sorted(members,key=lambda r:r['path']),count=len(members),bytes=sum(r['bytes'] for r in members),excludes='Top-level seal.json only'))
    print(json.dumps(dict(members=len(members),files=len(members)+1,seal_sha256=sha((OUT/'seal.json').read_bytes()),
        tool_sha256=sha(Path(__file__).read_bytes()),current=len(current),originals=len(originals),retained=len(retained),
        native_span_bytes=sum(s['bytes'] for s in spans),instructions=sum(s['instructions'] for s in spans)),indent=2))
if __name__=='__main__':main()
