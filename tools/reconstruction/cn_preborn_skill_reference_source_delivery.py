"""Static CN native skill-reference producer and actual source binding."""
import hashlib,json,re,difflib
from pathlib import Path
import capstone,pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg
NAME='cn-preborn-skill-reference-source-01'
ROUND='20261008-cn-preborn-skill-reference-source'
SOURCES=['src/cn/world/CnPrebornSkillReferences.h','src/cn/world/CnPrebornSkillReferences.cpp','src/cn/world/SharedPrebornWindowSource.cpp','docs/research/cn-preborn-skill-reference-source-20261008.md','tools/reconstruction/cn_preborn_skill_reference_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=['Actual shared CN rows/binding/Application/common skill and subject mapping/qualification/native Lua/rules/save/persistent replay/issuer remain unconfigured.','Native84 caller/full initial timing/full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/release remain open.']
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
 if (out/'findings.json').exists():raise RuntimeError('Preserve prior delivery')
 def save(rel,data):
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(data)
 def dump(rel,obj):save(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={q['path']:(out/q['snapshot']).read_bytes() for q in before}
 books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'];reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
 protected=[]
 for row in before:
  if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before snapshot differs')
  if row['path'] not in set(SOURCES+books)|reports:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs')
   protected.append(row)
 if len(before)!=131:raise RuntimeError('Expected131 before inputs')
 prior=(out/'retained-prior/cn-shared-skill-catalog-storage-source-01/manifest.json').read_bytes()
 if sha(prior)!='284f571e5bee8584223b6f44f829e4df050b81c8a87450e5e5560d5e28757fb7':raise RuntimeError('Prior seal differs')
 raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes();native_sha=sha(raw)
 if native_sha!='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8':raise RuntimeError('Pinned PE differs')
 view=FileView(pefile.PE(data=raw,fast_load=True),raw);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled');functions=[]
 for address,size,ret in [(0x4d5e60,479,'004d603c'),(0x4d5cc0,411,'004d5e58')]:
  paths=list(recovery.glob('part_*/'+f'{address:08x}'+'_*.c'));c=paths[0].read_bytes()
  if len(paths)!=1 or int(re.search(rb'Size: (\d+) bytes',c).group(1))!=size:raise RuntimeError('Native metadata differs')
  code=view.read(address-0x400000,size);cfg,ins=local_cfg(md,code,address,{})
  if cfg['frontier'] or cfg['ret_sites']!=[ret]:raise RuntimeError('Local normal CFG differs')
  save(f'native/{address:08X}.c',c);save(f'native/{address:08X}.bin',code);dump(f'native/{address:08X}-cfg.json',cfg)
  save(f'native/{address:08X}-cfg.asm',('\n'.join(f'{x.address:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for _,x in sorted(ins.items()))+'\n').encode())
  functions.append(dict(va=f'{address:08X}',metadata_bytes=size,instruction_sites=len(ins),sha256=sha(code),complete_local_normal_CFG=True))
 receiver=next(recovery.glob('part_*/0048fcc0_*.c')).read_bytes();save('native/0048FCC0-decompiled-context.c',receiver)
 relations=dict(native_sha256=native_sha,native_functions=functions,ordinary_insert_flag_site='004D5F3E',ordinary_insert_raw_flag=0,existing_item_flag_site='004D5D88',existing_item_raw_flag=3,native_pointer_formula='bank+kind*6E04+ID*6E-6A',native_record_file_offset='8+kind*6E04+(ID-1)*6E',receiver_context='WORLD0048FCC0 case34/35 arg=received+1; retained decompiler only, not new phase proof',source_reader='CnPrebornSkillReferences',optional_snapshot_only=True,client_memory_required=False,pointer_dereferenced=False,raw_flags_not_entitlement=True,common_skill_identity_qualified=False,formal_application_hosted=False,complete_route=False)
 dump('native/skill-reference-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:133 shared-table adapter sealed',native_sha256=native_sha,native_primary_metadata_bytes=890,native_local_normal_entry_CFGs=2,native_instruction_sites=241,cn_actual_skill_reference_catalog_resolvers_added=1,cn_existing_optional_snapshot_source_bindings_strengthened=1,new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,formal_application_hosted=False,native_snapshot_required=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'));ledger['cn_preborn_skill_reference_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name='CN actual selected skill-reference producer ->optional snapshot ->qualified shared-store definition source',version_scope='pinned-cn-preborn-recovery-evidence-only',status='Actual optional reference resolver; common authority/rows/binding/rules/save/replay/issuer/Application unconfigured',source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND;p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/books[0]).open('a',encoding='utf-8') as f:f.write('\n\n## CN selected skill references ('+ROUND+')\n\nPrimary4D5E60/4D5CC0 local normal CFGs890B/241sites qualify actual bank record pointer and opaque flag0/3 writers. Added optional actual snapshot ->same shared catalog owning definitions resolver; existing window preparation qualifies supplied evidence only. No client memory requirement or skill entitlement/common identity inference. Full game goal and PHASE1/later comprehensive validation unchanged.\n')
 for rel in SOURCES+books:
  data=(ROOT/rel).read_bytes();save('source/'+rel,data)
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True)))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_bytes','native_instruction_sites','new_complete_bidirectional_routes']}))
if __name__=='__main__':main()
