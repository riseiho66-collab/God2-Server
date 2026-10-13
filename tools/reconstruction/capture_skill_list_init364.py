from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;A=D.parent;S=Path('C:/Users/risei/Desktop/God2/God2-Server');P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def at(va,size):
 off=pe.get_offset_from_rva(va-base);b=raw[off:off+size];assert len(b)==size;return b
md=Cs(CS_ARCH_X86,CS_MODE_32);lo=0x553bc0;end=0x553e86;b=at(lo,end-lo);ins=list(md.disasm(b,lo));assert len(b)==710 and sum(i.size for i in ins)==710 and ins[0].bytes==b'\x55' and ins[-1].address==0x553e83 and ins[-1].mnemonic=='ret' and ins[-1].op_str=='0x24';by={i.address:i for i in ins};pending=[lo];seen=set();branches=[];calls=[]
for i in ins:
 if i.mnemonic.startswith('j'):
  assert i.op_str.startswith('0x');t=int(i.op_str,16);assert t in by;branches.append(dict(va=f'{i.address:08X}',target=f'{t:08X}'))
 if i.mnemonic=='call':calls.append(dict(va=f'{i.address:08X}',target=i.op_str,opaque=True))
while pending:
 va=pending.pop()
 if va in seen:continue
 assert va in by;seen.add(va);i=by[va]
 if i.mnemonic.startswith('ret'):continue
 if i.mnemonic=='jmp':pending.append(int(i.op_str,16))
 elif i.mnemonic.startswith('j'):pending.extend([int(i.op_str,16),va+i.size])
 else:pending.append(va+i.size)
assert len(seen)==len(ins) and len([i for i in ins if i.mnemonic.startswith('ret')])==1
put('qualified/553bc0-full-code.bin',b);put('qualified/553bc0-full-code.tsv',('va\thex\mnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode());pad=at(end,10);assert pad==b'\xcc'*10;put('qualified/after-ret-padding.bin',pad);nextb=at(0x553e90,6);assert nextb[:3]==b'\x55\x8b\xec';put('qualified/next-authentic-entry-prefix.bin',nextb)
caller=at(0x54a6a5,0x54a6e7-0x54a6a5);ci=list(md.disasm(caller,0x54a6a5));assert sum(i.size for i in ci)==len(caller);call=next(i for i in ci if i.address==0x54a6df);assert call.mnemonic=='call' and call.op_str=='0x553bc0';assert next(i for i in ci if i.address==0x54a6e4).mnemonic=='mov';put('qualified/actual-caller54a6a5-54a6e7.bin',caller);put('qualified/actual-caller54a6a5-54a6e7.tsv',('va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ci)).encode())
formals=[dict(formal=1,EBP='+08',caller='DWORD[H+20]',body_store='DWORD[L+2E28]',affinity='prior H20=U is separate conditional existing source'),dict(formal=2,EBP='+0C',caller='DWORD[H+04]',body_store='DWORD[L+2E20]'),dict(formal=3,EBP='+10',caller='ESI',body_store='DWORD[L+2E24]; DWORD[formal3+8] -> L+2E10',origin_OPEN_in_this_cut=True),dict(formal=4,EBP='+14',caller='H+BE86A8',body_store='DWORD[L+2E2C]'),dict(formal=5,EBP='+18',caller='H+BE86AA',body_store='DWORD[L+2E30]'),dict(formal=6,EBP='+1C',caller='H+BE86AC',body_store='DWORD[L+2E34]'),dict(formal=7,EBP='+20',caller='DWORD[H+14]+90',body_store='row refs base formal7+D8',prior_affinity='H14=R requires prior actual owner/lifetime unchanged'),dict(formal=8,EBP='+24',caller='MOVZX WORD[H+A8CC04]',body_store='WORD[L+2E14]; later CWDE for opaque handle call'),dict(formal=9,EBP='+28',caller='H+9D223C',body_store='DWORD[L+3518]',decompiler_param_name='param_10 includes implicit this')]
out('actual-caller-formal-stack-proof.json',dict(parent_whole_claim=False,known_parent='54A320',call_site='0054A6DF',call_end='0054A6E4',instruction_at54A6E4='MOV ESI,[EBP-4]',implicit_ECX='L=H+A89658',formals=formals))
footprint=dict(primary_groups=16,primary_stride=0x2d0,row_refs=[dict(group=i,destination=0x2d4+i*0x2d0,source_relative_to_formal7=0xd8+i*0x3ec,page_count_destination=0x2dc+i*0x2d0,page_count_literal=1) for i in range(16)],first_requested_zero_calls=[dict(destination=0x10+i*0x2d0,length=0x2d0) for i in range(16)],first_aux_requested_destination_constant=0x26c,first_aux_requested_bytes=100,first_aux_call_repeats=16,primary_word_mask_groups=[dict(group=i,start=0x14+i*0x2d0,words=100,width=2,and_mask=0x7fff,aux_requested_start=0x26c+i*0x2d0,aux_requested_bytes=100,direct_state_byte_zero=0x2d0+i*0x2d0) for i in range(16)],secondary_groups=[dict(group=i,stride=0x54,requested_zero_start=0x2d14+i*0x54,requested_zero_bytes=0x54,page_count_offset=0x2d60+i*0x54,page_count_literal=1,word_mask_start=0x2d14+i*0x54,words=10,width=2,and_mask=0x7fff) for i in range(3)],secondary_selector_WORD_offset=0x2d10,secondary_selector_WORD_literal=0x100,memset_target='0074FC50',zero_effect_conditional_on_native_callee_contract=True,learned_entries_materialized=False,bit15_clear_not_learning_or_grant=True)
out('exact-list-initialization-write-footprint.json',footprint)
refs=[]
for path in ['src/cn/assets/CnNativeSkillCatalog.h','src/cn/protocol/CnBattleSkillUpdate87.h','src/cn/protocol/CnBattleSkillSelection.h','src/cn/protocol/CnBattleCommandGate.h','src/cn/protocol/CnBattleSingleObject.h','docs/research/cn-native-battle-skill-selection-source-20261009.md','docs/research/cn-native-battle-skill-publication-source-20261009.md','docs/research/cn-native-skill-catalog-source-20261008.md','docs/research/cn-native-learned-skill-owner-frontier-20261009.md','artifacts/integration/packet-connections-20261006/cn-battle-deferred-consumer-01/native/00551d50-cfg.asm','artifacts/integration/packet-connections-20261006/cn-native-learned-skill-owner-frontier-01/root-native/00553bc0.c']:
 q=S/path;bb=q.read_bytes();refs.append(dict(actual_path=q.as_posix(),bytes=len(bb),sha256=sha(bb),copied=False))
out('existing-provenance-references-in-place.json',refs)
U=A/'round363-owned-skill-input-continuation-frontier';sb=(U/'seal.json').read_bytes();assert sha(sb)=='cf43e9400c5ceb92f01b3e603b373e09552f011d60674d057ba77a9f3b1bf94f';uv=json.loads(sb);rows=[]
for m in uv['members']:
 bb=(U/m['path']).read_bytes();assert type(m['bytes']) is int and len(bb)==m['bytes'] and sha(bb)==m['sha256'];rows.append(m)
assert len(rows)==26 and sum(m['bytes'] for m in rows)==496254;out('prior363-individual-verification.json',dict(root=U.as_posix(),seal_sha256=sha(sb),member_count=26,member_bytes=496254,members=rows))
proof=dict(authentic_entry='00553BC0',end_exclusive='00553E86',whole_function=True,code_bytes=710,sites=len(ins),reachable_sites=len(seen),sole_RET='00553E83',cleanup_bytes=36,branches=branches,opaque_calls=calls,caller_start='0054A6A5',caller_end_exclusive='0054A6E7',caller_bytes=len(caller),caller_sites=len(ci),parent_whole_claim=False,padding_bytes=10,next_entry_witness_bytes=6,independent_mapped_memory_proof=False,known_method_new_credit=0,local_static_method_evidence=1,new_route_credit=0,old_selected553C7B_to553DF9_bytes=382,no_global_new_coverage_claim=True);out('qualified-own-body-and-caller-boundaries.json',proof)
stores=[dict(va=f'{i.address:08X}',hex=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in ins if i.op_str.split(',')[0].strip().endswith(']') and i.mnemonic in {'mov','and','or','xor','add','sub','inc','dec'}];out('direct-memory-write-inventory.json',stores)
assert sha(P.read_bytes())==PIN;print(json.dumps(dict(code_bytes=710,sites=len(ins),caller_bytes=len(caller),caller_sites=len(ci),direct_stores=len(stores),opaque_calls=len(calls))))
