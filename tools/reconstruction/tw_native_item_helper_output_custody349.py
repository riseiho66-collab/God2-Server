"""Ordered manual source findings and integer individual-member custody; no report."""
from pathlib import Path
import hashlib,json,subprocess
import pefile
O=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def js(n,v):
    with (O/n).open('xb') as f:f.write((json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
v=json.loads((O/'native-inputs.json').read_bytes())
m=Path(v['mapped']['path']).read_bytes();p=Path(v['originalPE']['path']).read_bytes()
assert H(m)==v['mapped']['sha256'] and H(p)==v['originalPE']['sha256']
pe=pefile.PE(data=p,fast_load=True)
P=O.parent/'tw-native-spi-generic-record-write-source-340'
dep=[]
for r in json.loads((P/'native/cuts.json').read_bytes()):
    if r.get('kind')!='known-complete-method':continue
    b=(P/'native'/str(r['name']+'.bin')).read_bytes()
    lo=int(r['start_va'],16);off=pe.get_offset_from_rva(lo-0x400000)
    assert len(b)==r['bytes'] and H(b)==r['sha256'] and b==m[lo-0x400000:lo-0x400000+len(b)] and b==p[off:off+len(b)]
    dep.append(dict(name=r['name'],bytes=len(b),sha256=H(b),start_va=r['start_va'],originalPE_offset=off,mapped_PE_equal=True,reused_method_credit=0))
js('known-generic-methods-PE-readback.json',dep)
text=(P/'native/known-generic-row-loader-complete.tsv').read_text().splitlines()
parser=(P/'native/known-generic-parser-complete.tsv').read_text().splitlines()
selected=[l for l in text if any(x in l for x in ['004599C3','00459A03','00459A07','00459A0A','00459A1E','00459A20','00459A33','00459A3C','00459A42'])]
selected += [l for l in parser if any(x in l for x in ['00459943','0045994A','00459674','00459687'])]
js('existing-generic-selected-source-sites.json',dict(base=str(P),scope='Already complete/verified340 methods, source/namespace relation only; not recredited',selected_TSV_lines=selected))
cuts=json.loads((O/'cuts.json').read_bytes())
first,second=cuts['cuts'][:2]
notes=dict(
    scope='Only actual sameU output producers49B720 and49B770 and prior complete459A60 source dependency; no formatter descendants or target execution',
    identities=dict(newly_closed_in_audited_frontier=['49B720','49B770'],previously_complete_not_recounted=['49B850','459A60','4599B0','459420'],historical_global_first_claim=False,new_opcode_format_route_credits=0),
    first=dict(entry='49B720',end_exclusive='49B768',bytes=72,sites=18,returns=['49B750 RET0C','49B765 RET0C'],authentic_call='49B89A in complete348parent',formal_inputs=['ECX sameU','DWORD arg1 key','arg2 writableWORD output1 pointer','arg3 writableWORD output2 pointer'],
        ordered_source=['49B720 loads fullDWORD key;49B724 loads live Context fromU+CFF70;49B72B calls known459A60','nonnull:49B734 loads output1 pointer,49B738 reads WORD definition+116,49B73F writes WORD output1','49B742 reloads output2 pointer from own argument after first store,49B746 reads WORD definition+118,49B74D writes WORD output2,49B750 RET0C','null:49B753 loads output1 pointer,49B757 loads output2 pointer BEFORE either fallback store,49B75B stores0041,49B760 storesFFFF,49B765 RET0C'],
        writes='Exactly two ordered WORD output stores on each selected normal-return path; leaves adjacent/upper WORD bytes untouched. No calls after these stores.',
        return_EAX='nonnull:original definition pointer high16 with low16 overwritten by fetchedWORD118 atMOV AX; null:the output2 pointer. This is not a boolean/status/permit return.',
        alias_conditions='Generic output pointers may alias each other, stack argument cells or definition fields. First success store precedes second pointer reload/record118 read; cannot model both fields as sampled before stores without explicit nonalias/stability. Selected49B850 supplies distinct caller stack addresses, not global queue/U fields.'),
    second=dict(entry='49B770',end_exclusive='49B7AB',bytes=59,sites=18,returns=['49B79C RET8','49B7A8 RET8'],authentic_call='49B8DC in complete348parent',formal_inputs=['ECX sameU','DWORD arg1 key','arg2 writableWORD output pointer'],
        ordered_source=['49B770 key load,49B774 live Context=U+CFF70,49B77B known459A60','nonnull:49B784 loads BYTE definition+11B intoCL;49B78A loads output pointer;49B78E AND CL1;49B791 NEG CL;49B793 SBB ECX,ECX;49B795 AND ECX,29;49B798 INC ECX;49B799 storesCX WORD;49B79C RET8','null:49B79F loads output pointer,49B7A3 storesWORD1,49B7A8 RET8'],
        exact_CF_unsigned_recipe='b=byte11B&1; NEG low8 produces CF0 ifb0,CF1 ifb1. SBB ECX,ECX becomes00000000 orFFFFFFFF independently of preexisting ECX high bits. AND1Dh/INC yields exact DWORD1 or30; lowWORD store matches. No signed overflow/high-register assumption.',
        output='WORD30 when populated definition byte11B bit0=1; otherwiseWORD1 (including null lookup). This is a client formatter value/threshold, not authoritative shared stack limit, grant or equipment rights.',
        return_EAX='nonnull:definition pointer unchanged; null:output pointer. No status/eligibility contract.',writes='One WORD output store, no post-store calls; no actual owned inventory/native-bank mutation.'),
    lookup=dict(identity='459A60 already qualified30B, eight instruction sites/two RET4/no calls',
        source='DWORD input key is compared only viaunsigned AX to7F58h; >= returnszero. If below, AND EAX,FFFF then returnDWORD Context+B2D40+4*key.',
        accepted_low_WORD_domain='0..32599 inclusive; key0 is permitted by this lookup. High inputDWORD bits are discarded before table access. Actual49B850 passes already masked lowWORD.',
        bounds_limit='The observed comparison establishes effective lookup access bound/domain32600, not physical allocation capacity, populated count, current pointer validity or loader OOB protection.',
        category_namespace='Verified prior340 full4599B0 requests signed positive physicalcount*396 allocation, advances396 per physical input row including skippedkey, and for parsed token0 DWORD>=1 registers allocation+rowoffset in shared Context+B2D40+4*token0. It has NO upperkey check at that registration. Token0 key, category/physical row count and metadataDWORD0/token5 differ. Generic396 pointer namespace is distinct from ProgramMsg pointer/count atB2C68/B2C6C.',
        currentness='Finite historical records and valid original load/allocation/key-table conditions can qualify particular field provenance; no actual current bank/load status observed here.'),
    selected_parent_composition=dict(
        stack='LetS be49B850 ESP before call setup:49B720 output1=S+18h,output2=S+1Ch (own formal argument storage);49B770 output=S+12h (reserved stackWORD). Stores are stack results, not request IDs/queue/global owned cells.',
        consumer='After first child, parent MOVSX readsWORDoutput2 intofullEAX,WORDoutput1 intofullECX; defaults therefore signed65 and-1. Partial widgetWORD load intoDX still leaves its upperDWORD argument unqualified. Parent originalEDI upper16 remains unqualified.',
        conditional_field_provenance='Prior generic parser writesWORD116 from459FC0 RomMaps result then forcesWORD118FFFF; prior11B lowbits come from source22..25 lowbits (bit0 source22). Only under actual qualified category/physical input/allocation/conversion/current bank conditions; not universal record or current locale claim.',
        formatter='Parent consumes49B770 WORD using signed>1; output30 takes its signed row-count formatter branch, output1 skips it. This same source11Bbit0 is prior3B add-count branch with native signed30clamp, distinct from custom shared99.',
        remaining_opaque=['5068C0','5077C0','all current U/definition/row changes outside these selected method paths']),
    source_limits=['valid caller frame/stack/ordinary call return and fault-free reads/stores','nonnull Context/key table and valid populated record pointers require actual native loading provenance','output-pointer nonalias assumptions only when supplied by actual selected stack caller; no globalpure claim','no actual Session/owned definition/instance/acquisition issuer','no full25/full1215/DA producer or native accepted gameplay','no server policy derived from formatter1/30 or field selectors'],
    report_invocation=False,tracked_source_edits=False,target_execution=False,SQL_execution=False,
    read_failure='read-discovery-failure.txt preserves initially absent prior346 TSV path; known lookup actual .bin/.json reference subsequently located. Additional direct rg attempted absent guessed conditional-record doc suffix; final file was discovered by rg --files as tw-native-spi-conditional-record-source-20261012.md. No conclusions derive from failed discovery.')
js('manual-output-source-findings.json',notes)
head=subprocess.run(['git','rev-parse','HEAD'],cwd='C:/Users/risei/Desktop/God2/God2-Server',capture_output=True,check=True).stdout.decode().strip()
js('source-state.json',dict(head=head,scope='Native static source, immutable upstream packages unchanged; no tracked writes or report invocation'))
members=[]
for f in sorted(O.rglob('*')):
    if f.is_file() and f.name!='seal.json':
        b=f.read_bytes();members.append(dict(path=f.relative_to(O).as_posix(),bytes=len(b),sha256=H(b)))
seal=dict(schema='individual-member-sha256-v1',member_count=len(members),member_bytes=sum(x['bytes'] for x in members),new_complete_method_identities=['49B720','49B770'],new_opcode_format_route_credits=0,members=members)
js('seal.json',seal)
for r in members:
    b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
sb=(O/'seal.json').read_bytes()
print(json.dumps(dict(members=len(members),bytes=seal['member_bytes'],seal_bytes=len(sb),seal_sha256=H(sb),head=head,first_sha256=first['sha256'],second_sha256=second['sha256'])))
