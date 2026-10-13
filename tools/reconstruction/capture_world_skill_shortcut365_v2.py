"""Finite TW world skill shortcut source; static hash/PE/Capstone only."""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent
S=Path('C:/Users/risei/Desktop/God2/God2-Server')
P=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
U=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-pk-return-visibility-296/native-companion')
B=0x400000
HEAD='5a21cb97abb20c40080d4bf6be1a67cc4a071278'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists(),n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
 return dict(path=n,bytes=len(b),sha256=sha(b))
def out(n,v):return put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
assert not (D/'capture-complete.json').exists() and not (D/'seal.json').exists()
sb=(U/'seal.json').read_bytes();assert sha(sb)=='c5a65c2971c0cf52ce97a04d701fef853ea8f57688ee58b8cc0bf43a6befc0dd'
z=json.loads(sb);assert type(z['member_count']) is int and type(z['total_bytes']) is int
members=[]
for a in z['members']:
 p=(U/a['path']).resolve();assert p.is_relative_to(U.resolve()) and type(a['bytes']) is int and a['bytes']>=0
 b=p.read_bytes();assert len(b)==a['bytes'] and sha(b)==a['sha256'];members.append(a)
assert len(members)==z['member_count']==111 and sum(a['bytes'] for a in members)==z['total_bytes']==6839078
out('upstream296-individual-verification.json',dict(root=U.as_posix(),seal_sha256=sha(sb),member_count=111,member_bytes=6839078,members=members,all_members_verified_in_place=True,no_previous_helper_executed=True))
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert sha(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);assert pe.OPTIONAL_HEADER.ImageBase==B
out('original-native-input-references.json',dict(mapped=dict(actual_path=(P/'native-image.bin').as_posix(),bytes=len(m),sha256=sha(m)),originalPE=dict(actual_path=(P/'originalPE.bin').as_posix(),bytes=len(r),sha256=sha(r)),whole_images_copied=False,whole_image_equivalence=False,selected_pair_comparison_only=True))
md=Cs(CS_ARCH_X86,CS_MODE_32);cuts=[]
for name,s,e,rets in [('world-shortcut-complete',0x4AE520,0x4AE63F,4),('actual-input-parent-complete',0x4AB650,0x4AB694,2)]:
 b=m[s-B:e-B];offset=pe.get_offset_from_rva(s-B);rb=r[offset:offset+len(b)];assert b==rb
 ins=list(md.disasm(b,s));assert sum(i.size for i in ins)==len(b) and ins[-1].mnemonic=='ret'
 sites={i.address for i in ins};assert len([i for i in ins if i.mnemonic=='ret'])==rets
 edges=[];calls=[]
 for i in ins:
  if i.mnemonic.startswith('j'):
   assert i.op_str.startswith('0x');target=int(i.op_str,16);assert target in sites
   edges.append(dict(va=f'{i.address:08X}',target_va=f'{target:08X}',aligned_within_body=True))
  if i.mnemonic=='call':calls.append(dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),target=i.op_str,callee_expanded=False))
 put('qualified/'+name+'.mapped.bin',b);put('qualified/'+name+'.originalPE.bin',rb)
 put('qualified/'+name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
 cuts.append(dict(name=name,start_va=f'{s:08X}',end_exclusive_va=f'{e:08X}',bytes=len(b),sha256=sha(b),originalPE_offset=offset,selected_mapped_PE_equal=True,sites=len(ins),whole_function=True,branches=edges,calls=calls,returns=[dict(va=f'{i.address:08X}',cleanup=i.op_str) for i in ins if i.mnemonic=='ret'],global_new_method_credit=0))
assert sum(a['bytes'] for a in cuts)==355
out('qualified-whole-boundaries.json',cuts)
# Existing selected-row lookup reused from the immutable296 source, without recapture/credit.
old=(U/'qualified/skill_id_search_complete_leaf.bin').read_bytes();assert len(old)==91 and old==m[0xA9110:0xA916B]
off=pe.get_offset_from_rva(0xA9110);assert old==r[off:off+91]
gate=m[0xA90D0:0xA9110];off2=pe.get_offset_from_rva(0xA90D0);assert len(gate)==64 and gate==r[off2:off2+64]
out('existing-lookup-and-MP-gate-references.json',dict(lookup=dict(actual_path=(U/'qualified/skill_id_search_complete_leaf.bin').as_posix(),start_va='004A9110',end_exclusive_va='004A916B',bytes=len(old),sha256=sha(old),current_selected_mapped_PE_equal=True,recovered_already=True,new_credit=0),MP_gate=dict(start_va='004A90D0',end_exclusive_va='004A9110',bytes=64,sha256=sha(gate),current_selected_mapped_PE_equal=True,raw_cut_not_recaptured=True,existing_source='docs/research/current-skill-mp-gate-20260920.md and tools/strike_lab/current_skill_mp_gate.py',semantics='role=[U+86888]; row=[role+D0]; nonnegative input ordinal; definition=[row+258+4*ordinal]; definitionBYTE67 nonzero and uint32[role+64]>=uint16[definition+42]; no writes',new_credit=0)))
refs=[]
for path in ['AGENTS.md','docs/research/current-skill-mp-gate-20260920.md','docs/research/current-med02-self-supply-20260927.md','docs/research/current-daily-quest-lifecycle-20260927.md','docs/research/tw-native-skill-command-source-20261010.md','docs/research/tw-native-owned-deity-skill-source-20261010.md','docs/research/tw-cn-shared-skills-20261013.md','tools/strike_lab/current_skill_mp_gate.py','src/protocol/TaiwanNativeSkillCommand.h']:
 b=(S/path).read_bytes();refs.append(dict(actual_path=(S/path).as_posix(),bytes=len(b),sha256=sha(b),copied=False,execution=False))
for path in ['004ae520_FUN_004ae520.c','004ab650_FUN_004ab650.c']:
 p=Path('C:/Users/risei/Desktop/God2-解殼EXE原始碼重建/decompiled/functions')/path;b=p.read_bytes();refs.append(dict(actual_path=p.as_posix(),bytes=len(b),sha256=sha(b),copied=False,role='Historical pseudocode authentic-entry lead, not original C++ or byte-boundary authority'))
out('source-reference-hashes.json',refs)
relation=dict(scope='TW original world shortcut type2 arm, distinct from Battle C35',owner='Parent preserves suppliedECX as EDI; child preserves sameECX as ESI. Equality with canonical world U additionally requires actual invocation/lifetime; offsets alone do not prove it.',parent=dict(entry='004AB650',iteration='ESI initialized0; calls opaque418440([U+CFF64],ESI+70h); nonzero return and signed0<=ESI<=9 call4AE520 with sameU/ESI; zero result continues; first nonzero shortcut result returns1; after index9 returns0',actual_call='004AB675 E8A62E0000 ->004AE520',no_new_native_key_permission=True),tuple=dict(mode_field='DWORD[U+A3D08]',mode0='six bytes U+A3D18+6*shortcut',mode1='six bytes U+A3D54+6*(shortcut+10*sign8([U+86888]+CF))',copied='firstDWORD + lastWORD copied to stack; tuple WORD0 type, signedWORD2 kind, signedWORD4 id',unknown_mode='Other mode values skip initialization then read stacktuple. Do not assign zero, reject safety or valid dispatch; mode0/1 and readable current source prerequisites required.',no_own_slot_or_selected_CF_bounds='Child contains no shortcut upper/lower bounds or signedCF bound. Selected parent supplies0..9 only; mode1 CF/pointers remain caller prerequisites.'),type2=dict(branch='004AE5DF CMP AX,2',lookup='004AE5E5 signextend tupleWORD4 id; 004AE5EA signextend tupleWORD2 kind; pushid/pushkind then004AE5F7 CALL4A9110',ordinal_gate='004AE5FC CMP EAX,-1; equality exits0; otherwise pass returnedordinal at004AE601 to004AE604 CALL4A90D0 sameU',MP='Existing client player/menu eligibility only; BYTE67 nonzero, roleDWORD64 unsigned>=definitionWORD42; no debit/discount/refund/commit timing',after_gate='nonzero gate then004AE613 opaque4834E0(U,8,1); no argument identity/source immutability across child assumed',direct_writes=[dict(va='004AE61C',destination='BYTE[U+23D870]',value='BL = lowBYTE of earlier signextended shortcut kind'),dict(va='004AE622',destination='BYTE[U+23D871]',value='DL = lowBYTE of earlier saved signextended shortcut id')],return_value='EAX1; RET4',opaque_child_order_boundary='Even after child returns, fullU/menu/role/cursor fields and generic aliases may have changed; saved operand bytes retain earlier tuple values. No atomic source snapshot or current grant proof.'),other_arms='type1 calls opaque4A6760 and returns1; type0 calls opaque4963C0 and returns1; -1/other returns0; known prior item/dailyquest branch evidence not recredited',next_source='Future exact worldtarget/C56 source497A90 and actual target hit/cursor state supplier; not expanded or qualified here',original_formula=False,server_MP_debit=False,learned_or_grant_authority=False,full_route_credit=0,global_new_method_credit=0,new_opcode_credit=0)
out('shortcut-type2-source-relations.json',relation)
for a in refs:assert sha(Path(a['actual_path']).read_bytes())==a['sha256']
out('capture-complete.json',dict(verdict='PASS bounded static caller/source arm',head_reference=HEAD,code_bytes=355,data_bytes=0,whole_cuts=2,sites=sum(a['sites'] for a in cuts),native_method_coverage_note='4AE520 already historically executed as full method in item/dailyquest arms; type2 field/caller source qualified here; global novelty not asserted',new_global_method_credit=0,new_opcode_credit=0,full_route_credit=0,product_execution=0,successful_execution_count=1))
print(json.dumps(json.loads((D/'capture-complete.json').read_bytes())))
