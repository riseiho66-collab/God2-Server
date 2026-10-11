"""Static WORLD34/35 record format and existing shared-definition source."""
import json,hashlib,difflib,re
from pathlib import Path
import capstone,pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
NAME='cn-world-subject-skill-format-source-01';ROUND='20261008-cn-world-subject-skill-format-source'
SOURCES=['src/cn/protocol/CnWorldSubjectSkillUpdate.h','src/cn/world/CnPrebornSkillReferences.h','src/cn/world/CnPrebornSkillReferences.cpp','docs/research/cn-world-subject-skill-format-source-20261008.md','tools/reconstruction/cn_world_subject_skill_format_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=['Actual common subject/skill identities/qualification/native rules/transaction/save/persistent replay/sender/recipient readiness/Application remain unconfigured.','Actual shared CN rows/binding/issuer/full timing and all TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator and later comprehensive tests/repair/release remain open.']
def sha(d):return hashlib.sha256(d).hexdigest()
def main():
 base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
 if (out/'findings.json').exists():raise RuntimeError('Preserve prior delivery')
 def save(rel,d):
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(d)
 def dump(rel,o):save(rel,(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={q['path']:(out/q['snapshot']).read_bytes() for q in before};protected=[]
 books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'];reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
 for row in before:
  if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before differs')
  if row['path'] not in set(SOURCES+books)|reports:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected differs')
   protected.append(row)
 prior=(out/'retained-prior/cn-preborn-skill-reference-source-01/manifest.json').read_bytes()
 if sha(prior)!='c5f48456409cc5e5b8c751e6b128b5a987f8e49cfc1f63a7a92aa23d16db6387':raise RuntimeError('Prior seal differs')
 catalog=json.loads((base/'endpoint-catalog134/endpoints.json').read_text(encoding='utf-8'))
 scoped=[r for r in catalog if r['version']=='cn' and r['direction']=='S2C' and r['phase']=='world-connection-1' and r['opcode'] in ['34','35']]
 if len(scoped)!=2 or any(r['native_evidence']['length']!=4 for r in scoped):raise RuntimeError('Scoped format differs')
 dump('native/retained-world-endpoints.json',scoped)
 for row in scoped:
  rel=row['native_evidence']['branch_source'];source=Path('C:/Users/risei/Desktop/God2-xjz/God2-Server-CN')/rel
  save('native/branches/'+source.name,source.read_bytes())
 r=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled');path=next(r.glob('part_*/00567b50_*.c'));c=path.read_bytes();save('native/00567B50.c',c)
 raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
 if sha(raw)!='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8':raise RuntimeError('PE differs')
 view=FileView(pefile.PE(data=raw,fast_load=True),raw);size=int(re.search(rb'Size: (\d+) bytes',c).group(1));code=view.read(0x167b50,size);save('native/00567B50.bin',code)
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);instructions=list(md.disasm(code,0x567b50));save('native/00567B50-linear-metadata.asm',('\n'.join(f'{x.address:08x} {x.mnemonic} {x.op_str}' for x in instructions)+'\n').encode())
 # Retain previous qualified consumer CFG evidence, never execute it.
 for rel in ['native/004D5E60-cfg.json','native/004D5E60-cfg.asm','native/004D5CC0-cfg.json','native/004D5CC0-cfg.asm','native/skill-reference-relations.json']:
  save('retained-consumers/'+rel,(base/'cn-preborn-skill-reference-source-01'/rel).read_bytes())
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:134 native skill references sealed',cn_subject_skill_directional_formats_added=2,cn_existing_format_to_shared_definition_bindings_added=1,new_packet_values=0,new_native_phase_source_bindings=2,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,formal_application_hosted=False,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'));ledger['cn_world_subject_skill_format_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name='CN WORLD34/35 full records ->existing qualified shared skill-definition reader',version_scope='pinned-cn-world-connection1-format-and-source-only',status='4-byte format/source records; actual authority/sender/save/recipient/Application unconfigured',source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={'world-connection-1':['34','35']},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND;p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/books[0]).open('a',encoding='utf-8') as f:f.write('\n\n## CN WORLD subject skill update ('+ROUND+')\n\nPinned WORLD34/35 full4B format and actual shared definition reader binding; two phase-format source associations, no new opcode/owner/full route. Three native operands preserved, not common identity or server grant. Actual rules/save/replay/sender/recipient/Application remain open; full goal and phase1 unchanged.\n')
 for rel in SOURCES+books:
  d=(ROOT/rel).read_bytes();save('source/'+rel,d)
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),d.decode('utf-8-sig').splitlines(True)))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 print(json.dumps(dict(round=ROUND,new_native_phase_source_bindings=2,new_complete_bidirectional_routes=0)))
if __name__=='__main__':main()
