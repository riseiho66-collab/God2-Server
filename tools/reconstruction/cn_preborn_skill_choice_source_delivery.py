"""Primary CN choice consumers and actual source integration; files/CFG only."""
import difflib,hashlib,json,re
from collections import Counter
from pathlib import Path
import capstone,pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg
NAME='cn-preborn-skill-choice-source-01';ROUND='20261008-cn-preborn-skill-choice-source'
SOURCES=['src/cn/world/CnPrebornSkillChoiceSource.h','src/cn/world/CnPrebornSkillChoiceSource.cpp',
 'src/cn/world/CnPrebornSubjectState.h','src/cn/world/CnPrebornSubjectState.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'docs/research/cn-preborn-skill-choice-source-20261008.md','tools/reconstruction/cn_preborn_skill_choice_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py']
REMAINING=['Actual common subject/skill identity/native eligibility/rules/Lua/single transaction/save/persistent replay/issuer/CN rows/providers/Application remain unconfigured.',
 'Native no-book caller stack/output state, full initial timing/native84 callers/TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/release remain open.']
def sha(d):return hashlib.sha256(d).hexdigest()
def main():
 b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
 if (o/'findings.json').exists():raise RuntimeError('Preserve prior delivery')
 def save(rel,d):
  p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(d)
 def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'));old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
 if len(before)!=148:raise RuntimeError('Expected148 before inputs')
 books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'];reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']};protected=[]
 for row in before:
  if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before snapshot differs')
  if row['path'] not in set(SOURCES+books)|reports:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 prior=(o/'retained-prior/cn-native-skill-book-bindings-source-01/manifest.json').read_bytes()
 if sha(prior)!='d784e9767c3d2b38e96e64d26aa28cbe8197c5c2da49aba4304c3ab265601f0c' or not json.loads(prior)['sealed']:raise RuntimeError('Prior seal differs')
 raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes();native_sha=sha(raw)
 if native_sha!='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8':raise RuntimeError('Pinned PE differs')
 view=FileView(pefile.PE(data=raw,fast_load=True),raw);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled');functions=[];instructions={}
 for va,size in [(0x532b20,763),(0x5331b0,81),(0x533850,538),(0x533bc0,482),(0x534640,408)]:
  paths=list(recovery.glob(f'part_*/{va:08x}_*.c'))
  if len(paths)!=1:raise RuntimeError('Individual primary source not unique')
  c=paths[0].read_bytes()
  if int(re.search(rb'Size: (\d+) bytes',c).group(1))!=size:raise RuntimeError('Primary metadata differs')
  code=view.read(va-0x400000,size);cfg,ins=local_cfg(md,code,va,{})
  if cfg['frontier']:raise RuntimeError('Normal CFG frontier: '+hex(va))
  save(f'native/{va:08X}.c',c);save(f'native/{va:08X}.bin',code);dump(f'native/{va:08X}-cfg.json',cfg)
  save(f'native/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
  functions.append(dict(va=f'{va:08X}',metadata_bytes=size,instruction_sites=len(ins),ret_sites=cfg['ret_sites'],complete_local_normal_CFG=True,sha256=sha(code)));instructions.update(ins)
 # Keep operands from their actual entry CFG sites, not mid-instruction slices.
 sites=[0x532b69,0x532b79,0x532b8a,0x532b94,0x532ba2,0x532bac,0x532bba,0x532bc4,0x532bd2,0x532bda,0x532be0,
        0x5338b3,0x5338c2,0x5339b1,0x5339cc,0x5339de,0x533c23,0x533c32,
        0x53466c,0x53467a,0x534696,0x5346a1,0x5346a4,0x5346a5,0x5346a7,0x5346cb,0x5346da,0x5346df,0x5346e5]
 dump('native/choice-operand-sites.json',[dict(va=f'{a:08X}',bytes=instructions[a].bytes.hex(),mnemonic=instructions[a].mnemonic,operand=instructions[a].op_str) for a in sites])
 old_art=b/'cn-native-skill-book-bindings-source-01'
 for rel in ['native/book-binding-relations.json','native/functions/004D2BB0.c','native/functions/004D2BB0.bin','native/functions/004D2BB0-cfg.json','native/functions/0042CFB0.c','material/all-pointer-range-rows.json','material/native-skill-book-bindings.json']:
  save('retained-books/'+rel,(old_art/rel).read_bytes())
 for rel in ['native/preborn-producer-consumer-relations.json','native/entry-cfg/00534810.json','native/ranges/00534810-entry-rooted.asm','native/ranges/00534810-complete-code.bin']:
  save('retained-producer/'+rel,(b/'cn-preborn-choice-source-01'/rel).read_bytes())
 rows=json.loads((old_art/'material/all-pointer-range-rows.json').read_text(encoding='utf-8'));skb=[r for r in rows if r['section']=='SKB']
 ranges=[(0x19a8,0x19af),(0x1a09,0x1a0d),(0x1a6b,0x1a6d),(0x1ae4,0x1ae6)];material=[]
 for r in skb:
  token=r['fields'][27]
  if len(token)!=1 or token not in '01234':raise RuntimeError('Pinned raw27 token differs')
  operand=int(token);item=r['item_id'];excluded=any(first<=item<=last for first,last in ranges)
  material.append(dict(item_id=item,native_alias=r['fields'][26],source_line=r['source_line'],decoded_offset=r['decoded_offset'],record_sha256=r['record_sha256'],raw_column27=token,native_12c=operand,in_literal_exclusion_ranges=excluded,native_server_eligibility_qualified=False))
 counts=dict(Counter(r['raw_column27'] for r in material))
 if counts!={'0':367,'1':8,'2':5,'3':3,'4':3}:raise RuntimeError('Pinned byte operand census differs')
 if any((r['native_12c']!=0)!=r['in_literal_exclusion_ranges'] for r in material):raise RuntimeError('Actual native predicate sets differ')
 dump('material/native-choice-book-operands.json',material)
 relations=dict(native_sha256=native_sha,native_functions=functions,duplicate_helper='005331B0',native_selected_list_count_offset='C3C',native_selected_list_pointer_array='A48',duplicate_identity_bytes=['kind:1','id:0'],
  native_insert_helper='00532B20',native_insert_limit_offset='F75',native_literal_excluded_item_ranges=ranges,
  native_available_list_helper='00533850',book_gate_consumer_site='005339B1',book_gate_offset='12C',book_gate_source_column=27,
  book_operand_counts=counts,nonzero_book_gate_records=19,native_no_match_out_item_caller_state_qualified=False,native_stack_fallback_fabricated=False,
  offered_list_filter_helper='00534640',family_word_reader_site='005346A1',family_word_actual_object_offset='90',object0_not_used_as_family_operand=True,
  native_family_formula='BYTE(signed16(actual_inline_role_word)/2), division toward zero',native_offered_predicate='flags&1 AND (kind==family_byte OR signed16(selected_identifier)>100 OR selected_byte5B!=0)',
  same_actual_shared_skill_catalog_required=True,optional_native_snapshot_only=True,client_memory_required=False,retained_facts_to_common_apply_and_post_commit=True,
  UI_gates_not_server_authority=True,request_duplicate_not_persistent_replay=True,actual_common_identity_rule_save_owner_configured=False,formal_application_hosted=False,complete_route=False)
 dump('native/skill-choice-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:137 actual SKB supplier and common operation handoff sealed',cn_preborn_skill_choice_source_resolvers_added=1,cn_actual_inline_role_word_projections_added=1,cn_existing_common_choice_fact_handoffs_strengthened=1,
  native_primary_metadata_bytes=sum(r['metadata_bytes'] for r in functions),native_local_normal_entry_CFGs=len(functions),native_instruction_sites=sum(r['instruction_sites'] for r in functions),cn_book_nonzero_gate_records=19,cn_book_zero_gate_records=367,
  new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
  actual_common_identity_rule_save_owner_configured=False,actual_supplier_and_rows_configured=False,formal_application_hosted=False,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 p=b/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'));ledger['cn_preborn_skill_choice_source']=dict(facts,evidence=o.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name='CN actual selected-skill and book/UI predicates ->same owning definitions ->common preborn apply/delivery source',version_scope='pinned-cn-preborn-source-facts-only',status='Actual native predicates/operand/resolver/common handoff; common identity/authority/rules/save/replay/providers/Application unconfigured',source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND
 ledger['dual_client_execution_plan']['next_source_frontier']='Actual common subject/skill identity/native rule/save/replay/issuer/CN rows/providers/Application; no-book caller state and native84/full timing; full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator. PHASE1.'
 p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/books[0]).open('a',encoding='utf-8') as f:f.write('\n\n## CN preborn skill-choice facts ('+ROUND+')\n\nRecovered2272B/712sites five primary consumers: duplicate identity,19 book12C/literal exclusions and actual optional subject filter using object+90 WORD rather than object+0. Added actual shared selection resolver and retained owning facts into common apply/post-commit delivery, no native memory requirement or authority inferred from UI. No new packet/phase/network owner/complete route; actual common authority/providers/rows/rules/save/replay/Application open. Full goal and PHASE1 preserved.\n')
 for rel in SOURCES+books:
  d=(ROOT/rel).read_bytes();save('source/current/'+rel,d)
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),d.decode('utf-8-sig').splitlines(True)))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_bytes','native_local_normal_entry_CFGs','native_instruction_sites','cn_book_nonzero_gate_records','new_complete_bidirectional_routes']}))
if __name__=='__main__':main()
