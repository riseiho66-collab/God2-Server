"""210 bounded static original Taiwan2A caller inputs; no codec/runtime."""
from pathlib import Path
import hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/integration/packet-connections-20261006/tw-stored-entry-host-composition-01/agents/tw-entry-caller-inputs'
PRIOR=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-entry-material-source-01/agents/tw-entry-native-fields'
PE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(name,v):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copies(paths,folder):
    rows=[]
    for i,p in enumerate(paths):
        p=Path(p);p=p if p.is_absolute() else ROOT/p;b=p.read_bytes();copy=f'{folder}/{i:02d}-{p.name}'
        q=OUT/copy;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        rows.append(dict(path=str(p.resolve()),copy=copy,bytes=len(b),sha256=sha(b)))
    return rows
def main():
    if (OUT/'seal.json').exists():raise RuntimeError('Preserve sealed210')
    OUT.mkdir(parents=True,exist_ok=True)
    guides=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
    source=['src/protocol/RecoveredWorldEntryView.h','src/protocol/RecoveredWorldEntry.h',
        'src/game/SharedTaiwanWorldEntrySource.h','src/game/SharedTaiwanWorldEntrySource.cpp']
    own='tools/reconstruction/tw_native_entry_caller210.py'
    current=copies(guides+[own]+source,'current');dump('current-source-origins.json',current)
    originals=current+copies(['docs/research/current-login-character-socket-topology-20260919.md',
        'docs/research/current-world-initialization-sequence-20260919.md',
        'docs/research/current-world-startup-20260919.md',
        'tools/strike_lab/current_world_startup.py'],'originals')
    dump('original-inputs.json',originals)
    priorseal=PRIOR/'seal.json';sealraw=priorseal.read_bytes()
    if sha(sealraw)!='283ac937eff019b1fdd18cb522caad09ad38ca49397a228764807999fdfec801':
        raise RuntimeError('Prior209 seal differs')
    inventory=[]
    for p in sorted(PRIOR.rglob('*')):
        if p.is_file():
            b=p.read_bytes();inventory.append(dict(path=str(p.resolve()),relative=p.relative_to(PRIOR).as_posix(),bytes=len(b),sha256=sha(b)))
    dump('prior209-whole-inplace-references.json',inventory)
    retained=copies([PRIOR/n for n in ['seal.json','findings.json','field-groups.json',
        'logical37-byte-map.json','native-spans.json','native/retained-normal-initializer.bin',
        'native/retained-normal-initializer.instructions.json','native-input-references.json']], 'retained209')
    dump('retained-source-origins.json',retained)
    raw=PE.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Actual native master hash mismatch')
    dump('native-input-references.json',[dict(path=str(PE.resolve()),bytes=len(raw),sha256=sha(raw),
        copied=False,full_inplace_hash=True,old_capture_path_currently_missing=not (ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').exists(),
        scope='No archive restore, identity substitution, native execution or refreshed historical baseline.')])
    md=Cs(CS_ARCH_X86,CS_MODE_32);spans=[]
    # Each target is an actual data-transfer/call boundary. UI/render/text callees are not followed.
    selected=[('application-outflag-pointer',0xdec3,0xded2),
        ('selected-output-call-boundary',0xdf74,0xdf95),
        ('normal-world-sixargs',0xe0bd,0xe0db),
        ('world-prologue-argument-storage',0x64910,0x649b2),
        ('initializer-threeargs',0x65157,0x651a1),
        ('retained-selected40-data-copy',0x5bb6,0x5bdd),
        ('retained-2a-waiter-copy-consume',0x156ec,0x1571f)]
    for name,start,end in selected:
        b=raw[start:end];ins=list(md.disasm(b,start+0x400000))
        if sum(i.size for i in ins)!=len(b):raise RuntimeError('Partial instruction boundary '+name)
        copy='native/'+name+'.bin';q=OUT/copy;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        rows=[dict(va=f'{i.address:08X}',file_offset=i.address-0x400000,bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in ins]
        dump('native/'+name+'.instructions.json',rows)
        spans.append(dict(name=name,va=f'{start+0x400000:08X}',end_exclusive_va=f'{end+0x400000:08X}',
            file_offset=start,bytes=len(b),sha256=sha(b),copy=copy,instructions=len(rows),
            classification='Retained known native data/call relation re-read. Prior bounded raw span coverage not asserted globally.'))
    dump('native-spans.json',spans)
    diagram=dict(addresses='VA=400000+RVA; hexadecimal object offsets; scalar lengths decimal',
        application_owner='A is ECX copied to EBP at0040DEA3; W is A+440 pointer during normal call',
        normal_top_call=dict(va='0040E0D6',callee='00464910',this='W',
            stackargs=['A','pointer to current DE80 local+30 selected40 buffer','A+A4 out-flag DWORD pointer',
                       'DE80 local1C','DE80 local18','literal1']),
        selection_buffer=dict(va='0040DF74..0040DF87',
            pointer='first4DA0 argument: lea ECX,[ESP+3C] after3pushes ->original DE80 local+30',
            actual_copy='00405BB6..00405BDD: sign-extended selectedWORD; rawList+2+36*selected ->caller outputpointer; exactly10 DWORDs/40 bytes',
            limitation='Wire row stride36 and copied40 remain distinct. Source selection/root/name current is not common64 identity or whole profile authority.'),
        initializer_call=dict(va='00465194',callee='00468160',this='W',
            stackargs=['64910 arg2 namepointer when G byte+2CB8 nonzero; NULL otherwise',
                       'R=&W+1539683C','64910 arg3, normally&A+A4'],
            stackproof='64910 SEH3push +locals254+4savedregs =>270; initial ESP+27C=arg3; after2push ESP+280=originalarg2'),
        role_and_outflag=dict(role='R is caller-owned inline world role, not arbitrary decoded packet pointer',
            outflag='681FD..68204 writes body0 bit31 through thirdargument and W+A7F2F3C',
            actual_actor_name='209-retained004687A8 reads firstargument and copies its C-string toR+B7; not a2A body field; no textcallee followed'),
        connected_receive=dict(G='W+A7E05E0 retained fromA+438 at649A6/649AC',
            producer='681A3 calls15690 with36-byte destination;156EC matches2A,15700 usespacket+1,1571A consumespacket',
            later_dispatch='Later WORLD2A default join6B517 is independent from dedicated initial waiter; not an alternate complete initializer.'),
        disconnected='65190 passesNULL firstargument ->6817B branch688D0 internal actor fallback; not authenticated entry/name/profile or supported offline startup.')
    dump('call-argument-diagram.json',diagram)
    dump('findings.json',dict(round=210,scope='Bounded original caller source reconciliation; no C++ changes',
        actual_full_PE_sha256=PIN,call_argument_diagram='call-argument-diagram.json',
        useful_reconciled_relation='DE80 selected40 outputbuffer ->64910 secondarg ->68160 firstarg ->R+B7 externalname, independently from full2A; outflag usesA+A4 and role usesinlineW1539683C.',
        next_source_action='Keep actual selected-name/raw encoding/provenance/current with its complete source epoch. Bind that independently from stored full2A/profile/resource/status issuer; do not insertname into2A or substitute current name/source from historical fixture.',
        qualifiers=['Same actual application/world/selected-buffer epoch and retained G, not a static address-to-account equivalence.',
            'Name byte encoding and bounded termination require independently qualified selected record; raw copy does not establish CP950/default alias.',
            'Native role/outflag storage are client inputs, not server battle/appearance permissions or common ID.',
            'No renderer/UI/text callee interiors followed; selection routine is represented only by old qualified data-copy sites and actual top-level call boundary.'],
        new_native_spans=0,new_native_bytes=0,retained_bounded_spans=len(spans),
        retained_bounded_bytes=sum(s['bytes'] for s in spans),retained_instruction_sites=sum(s['instructions'] for s in spans),
        new_opcodes=0,new_complete_routes=0,whole_game_percentage=None,
        prior209_immutable_fullfiles=len(inventory),root_mutable_core_sources_read=False,
        original_input_files=len(originals),current_files=len(current),retained_copies=len(retained),
        no_native_execution=True,no_codec=True,no_DB=True,no_tests=True,no_build=True,
        still_open=['Complete actual stored2A issuer and selected-name/profile/resource Current suppliers',
                    'Main actualSourceFactory selection and initial world peers/resources','Native gameplay/state/variant complete denominator'],
        stop='One bounded210 delivery; parent goal remains TW-first active.'))
    members=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p!=OUT/'seal.json' and p!=OUT/'LIST.json':
            b=p.read_bytes();members.append(dict(path=p.relative_to(OUT).as_posix(),bytes=len(b),sha256=sha(b)))
    dump('LIST.json',members);b=(OUT/'LIST.json').read_bytes()
    members.append(dict(path='LIST.json',bytes=len(b),sha256=sha(b)))
    dump('seal.json',dict(members=sorted(members,key=lambda r:r['path']),count=len(members),bytes=sum(r['bytes'] for r in members),excludes='Only top-levelseal.json'))
    print(json.dumps(dict(members=len(members),files=len(members)+1,seal_sha256=sha((OUT/'seal.json').read_bytes()),
        tool_sha256=sha(Path(__file__).read_bytes()),current=len(current),originals=len(originals),
        prior209_inplace=len(inventory),retained=len(retained),span_bytes=sum(s['bytes'] for s in spans)),indent=2))
if __name__=='__main__':main()
