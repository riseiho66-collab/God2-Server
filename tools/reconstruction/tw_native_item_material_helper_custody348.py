"""Manual findings and individual hash custody only; no packet/report invocation."""
from pathlib import Path
import hashlib,json,subprocess
O=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def js(n,v):
    with (O/n).open('xb') as f:f.write((json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
prior=O.parent/'round346-initial-owned-material-main-plan'
receipts=[]
s=json.loads((prior/'seal.json').read_bytes())
rows=[]
for r in s['members']:
    b=(prior/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
    rows.append(dict(name=r['path'],bytes=len(b),sha256=H(b)))
receipts.append(dict(base=str(prior),seal_file='seal.json',seal_sha256=H((prior/'seal.json').read_bytes()),member_count=len(rows),member_bytes=sum(x['bytes'] for x in rows),members=rows))
v=json.loads((prior/'prior238-individual-verification.json').read_bytes())
root=Path(v['seal']['path']).parent;rows=[]
for r in v['members']:
    b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
    rows.append(dict(name=Path(r['path']).relative_to(root).as_posix(),bytes=len(b),sha256=H(b)))
receipts.append(dict(base=str(root),seal_file=Path(v['seal']['path']).name,seal_sha256=H(Path(v['seal']['path']).read_bytes()),member_count=len(rows),member_bytes=sum(x['bytes'] for x in rows),members=rows))
js('prior-individual-member-receipts.json',receipts)
f=json.loads((O/'cuts.json').read_bytes())['cuts'][0]
assert f['begin']==0x49B850 and f['end_exclusive']==0x49BAE0 and f['bytes']==656 and f['sites']==224
assert len(f['returns'])==9
notes=dict(
    selected_identity='49B850',authentic_entry='Direct CALL at498EF3 from already-sealed complete3B498DD0; preceding34249B820 RET18h at49B840/padding to49B850; next distinct method49BAE0',
    provenance='Mapped149c and originalPE5fcf exact static bytes, in-place hash inputs from315; no current runtime data observation.',
    boundary=dict(begin='49B850',end_exclusive='49BAE0',bytes=656,sites=224,ret_sites=[f"{x['va']:08X}" for x in f['returns']],all_RET_pop_bytes=8,all_local_jump_targets_aligned_within_body=True,indirect_jumps=0),
    formal_inputs=dict(ECX='Same U from existing3B EBP; this body saves U in ESI',arg1='row pointer at incomingESP+4, retained EBP; caller selects U+8560C+24*signextend(bodyBYTE1)',arg2='DWORD at incomingESP+8, retained EDI; only lowWORD DI is signed-gated0..49. Upper16 not canonicalized by this body or caller MOVSX CX,AL/PUSH ECX.'),
    source_alias=dict(caller_copy='Existing498E0A..498E30: logical3B record EBX+4 full20 -> U+85610+24*signextend(recordBYTE1), REP MOVSD5; row passed later starts4B earlier atU+8560C.',row_count='row+0 / U+8560C+24*s signed BYTE; direct count-header only',full20_relative_reads=[dict(row_offset=4,full20_offset=0,width=4,uses='lowWORD key and003F0000 mask from staged live rereads'),dict(row_offset=12,full20_offset=8,width=1,uses='equals1 on selected mask00050000 branch')],unread_direct='row+1..3 and other full20 bytes have no direct loads in this method; opaque child effects remain unqualified.'),
    ordered_stages=[
        dict(va='49B85B..49B868',source='signed lowWORD DI',condition='DI<0 or DI>=50 -> common RET8, before row dereference/calls'),
        dict(va='49B86E..49B87E',source='row EBP and signedBYTE row+0',condition='nullrow or signed count<=0 -> empty UI path49BA73; no full20 loads on that selected direct path'),
        dict(va='49B884..49B89A',source='first liveDWORD row+4 low16',action='49B720 sameU(key, address of own stackarg1, address of own stackarg2); exact writer/effects opaque'),
        dict(va='49B89F..49B8BC',source='signedWORD outputs from own stackarg2/arg1, lowWORD U+232DC8, original fullEDI',action='5068C0 withECX U+E2170; widget/output authority opaque; partial WORD register loads do not canonicalize upperDWORD argument bits'),
        dict(va='49B8C1',condition='signed DI<=29 ordinary; else only42/43 get the additional selected text branches'),
        dict(va='49B8CB..49B8DC',source='second liveDWORD row+4 low16',action='49B770 sameU(key, address of own reserved stackWORD atESP+12h); output semantics and effects opaque'),
        dict(va='49B8E1..49B8F9',source='third liveDWORD row+4 and signed localWORD from49B770',condition='lowWORD zero -> fallback; else signed localWORD>1 -> formatter path with newly reread signedBYTE row+0 and pointer58D300'),
        dict(va='49B91F..49B92E',source='thirdDWORD masked003F0000 and liveBYTE row+0C',condition='mask00050000 and byte==1 -> selected live context branch; no type/eligibility name inferred'),
        dict(va='49B930..49B982',source='liveDWORD U+CFF70; signedWORD pointed+B2C6C; if>=01A2h liveDWORD pointed+B2C68 then DWORD+684',action='Pass that selected DWORD or literal0 to opaque5077C0; native string/object semantics unknown'),
        dict(va='49B9BE..49BA71',source='slots42/43: signedlowWORD s ->52*s; liveWORD U+9E6C+52*s, fourth liveDWORD row+4 mask, liveDWORD U+9E80+52*s',condition='zeroWORD, mask00220000 or zeroDWORD -> fallback pointer5B4640 with indexs-12; otherwise live U+CFF70 signedWORD+B2C6C>=036Ah selects pointed+B2C68 DWORD+DA4 else literal0'),
        dict(va='49BA73..49BADD',source='empty row selected path and validDI',action='5068C0 receives lowWORD U+232DC8,31,indexEDI,-1. Ordinary0..29 additionally opaque fallback5077C0;42/43 fallback uses fullEDI-12; other30..49 return after primary widget call.'),
    ],
    direct_effects='No explicit non-stack memory store in49B850; its ordinary code changes registers/ESP only. Stack addresses are supplied to49B720/49B770. Opaque child calls can write U/row/global state, emit queues or fail; no global absence/final-state claim.',
    opaque_children=['49B720','49B770','5068C0','5077C0'],
    unsupported=['Server eligibility/entitlement/acquisition','owned common definition/instance identity','native full25 issuer','full1215/DA producer','caller/live row or U stability across opaque calls','native child argument upperDWORD canonical values after partial WORD loads','response/order/native accepted gameplay'],
    next_actual_source='If a separate bounded task is selected later,49B720 and49B770 are the direct sameU keyed stack-output producers. Their authentic input/output provenance would qualify UI material formatting only; real server acquisition/rules remain a separate authority supplier. No descendant expansion performed here.',
    accounting=dict(new_complete_method_identities=['49B850'],known_parent_method_credit=0,new_opcode_format_credits=0,new_complete_routes=0,native_acceptance=0,verified_safe_selected_code_bytes=806,preserved_misaligned_parent_draft_bytes=38,preserved_boundary_preview_bytes=2080),
    corrections='draft-correction-appendix.txt preserves/excludes initial misaligned parent-copy draft; aligned correction validates every instruction start against sealed full parent. Preview partial is not a method completeness claim.',
    target_execution=False,SQL_execution=False,repository_changes=False,report_invocation=False)
js('manual-source-findings.json',notes)
state=subprocess.run(['git','rev-parse','HEAD'],cwd='C:/Users/risei/Desktop/God2/God2-Server',capture_output=True,check=True).stdout.decode().strip()
js('source-state.json',dict(head=state,scope='Read-only native cuts/JSON findings; no tracked changes/no report invocation'))
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='seal.json':
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=H(b)))
seal=dict(schema='individual-member-sha256-v1',member_count=len(members),member_bytes=sum(x['bytes'] for x in members),new_complete_method_identities=['49B850'],new_opcode_format_route_credits=0,members=members)
js('seal.json',seal)
for r in members:
    b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
sb=(O/'seal.json').read_bytes()
print(json.dumps(dict(members=len(members),bytes=seal['member_bytes'],seal_bytes=len(sb),seal_sha256=H(sb),full_method_sha256=f['sha256'])))
