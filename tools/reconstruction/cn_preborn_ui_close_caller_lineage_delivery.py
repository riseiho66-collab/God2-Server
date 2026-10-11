"""Primary native GUI close/caller boundaries; unphased84 source, no runtime."""
import difflib,hashlib,json,re,struct
from pathlib import Path
import capstone,pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg
NAME='cn-preborn-ui-close-caller-lineage-01';ROUND='20261008-cn-preborn-ui-close-caller-lineage'
SOURCES=['src/cn/protocol/CnPrebornSubjectRequest.h','docs/research/cn-preborn-ui-close-caller-lineage-20261008.md','tools/reconstruction/cn_preborn_ui_close_caller_lineage_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=['Native84 indirect/computed/root/phase/subject and common authority remain unqualified; no WORLD84 registration or guessed cancel/reply.',
 'Actual common subject/skill identity/rules/save/persistent replay/issuer/CN rows/providers/Application; full TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/release remain open.']
def sha(d):return hashlib.sha256(d).hexdigest()
def main():
 b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
 if (o/'findings.json').exists():raise RuntimeError('Preserve delivery')
 def save(rel,d):
  p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(d)
 def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'));old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
 if len(before)!=152:raise RuntimeError('Expected152 before inputs')
 books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'];reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']};protected=[]
 for row in before:
  if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before snapshot differs')
  if row['path'] not in set(SOURCES+books)|reports:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 prior=(o/'retained-prior/cn-preborn-skill-choice-source-01/manifest.json').read_bytes()
 if sha(prior)!='208e6e894b3c0be536f3dffd8ecfb23a3852c69454043f9968b4ea38e2002289' or not json.loads(prior)['sealed']:raise RuntimeError('Prior seal differs')
 raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes();native_sha=sha(raw)
 if native_sha!='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8':raise RuntimeError('Pinned image differs')
 pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled');functions=[];decoded={}
 scopes=[(0x5342b0,43),(0x5342e0,56),(0x44e7f0,317),(0x4a89a0,14),(0x4a8470,273),
  (0x497960,86),(0x4c4060,591),(0x4cd960,175),(0x4cda10,249),(0x4cfc40,229),(0x4cfd30,303),(0x4fe9c0,357),(0x5089e0,414)]
 for va,size in scopes:
  paths=list(recovery.glob(f'part_*/{va:08x}_*.c'))
  if len(paths)!=1:raise RuntimeError('Primary recovery not unique')
  c=paths[0].read_bytes()
  if int(re.search(rb'Size: (\d+) bytes',c).group(1))!=size:raise RuntimeError('Metadata differs')
  code=view.read(va-0x400000,size);cfg,ins=local_cfg(md,code,va,{})
  save(f'native/{va:08X}.c',c);save(f'native/{va:08X}.bin',code);dump(f'native/{va:08X}-cfg.json',cfg)
  save(f'native/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
  functions.append(dict(va=f'{va:08X}',metadata_bytes=size,instruction_sites=len(ins),complete_local_normal_CFG=not cfg['frontier'],frontier=cfg['frontier'],sha256=sha(code)));decoded.update(ins)
 # Complete extended producer is prior qualified evidence, not a newly guessed
 # envelope around its162-byte metadata or a new phase proof.
 q=b/'cn-preborn-choice-source-01'
 for rel in ['native/entry-cfg/00534810.json','native/ranges/00534810-entry-rooted.asm','native/ranges/00534810-complete-code.bin','native/preborn-producer-consumer-relations.json']:
  save('retained-producer/'+rel,(q/rel).read_bytes())
 code=(q/'native/ranges/00534810-complete-code.bin').read_bytes()
 if view.read(0x534810-0x400000,len(code))!=code:raise RuntimeError('Pinned prior extended producer differs')
 old_cfg=json.loads((q/'native/entry-cfg/00534810.json').read_text(encoding='utf-8'))
 site=0x534877;ins=next(md.disasm(view.read(site-0x400000,5),site,count=1))
 if f'{site:08x}' not in {e['source'] for e in old_cfg['edges']}:raise RuntimeError('Prior producer site not rooted')
 decoded[site]=ins
 relative=[];literal=[];sections=[]
 for index,s in enumerate(pe.sections):
  data=raw[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData];start=pe.OPTIONAL_HEADER.ImageBase+s.VirtualAddress
  sections.append(dict(index=index,name=s.Name.decode('ascii').strip('\0'),start_va=f'{start:08X}',raw_offset=s.PointerToRawData,file_backed_bytes=len(data),executable_declared=bool(s.Characteristics&0x20000000)))
  for opcode in [0xe8,0xe9]:
   pos=0
   while True:
    pos=data.find(bytes([opcode]),pos)
    if pos<0:break
    if pos+5<=len(data):
     pc=start+pos;target=(pc+5+struct.unpack_from('<i',data,pos+1)[0])&0xffffffff
     if target in [0x5342b0,0x5342e0]:relative.append(dict(section_index=index,site=f'{pc:08X}',target=f'{target:08X}',opcode=f'{opcode:02X}',raw_offset=s.PointerToRawData+pos))
    pos+=1
  for value in [0x5342b0,0x1342b0]:
   pos=0;needle=struct.pack('<I',value)
   while True:
    pos=data.find(needle,pos)
    if pos<0:break
    literal.append(dict(section_index=index,site=f'{start+pos:08X}',value=f'{value:08X}',instruction_or_table_qualified=False));pos+=1
 dump('search/file-backed-sections.json',sections);dump('search/raw-relative-target-candidates.json',relative);dump('search/raw-VA-RVA-pointer-candidates.json',literal)
 expected={0x49798e,0x4c4174,0x4cd9cd,0x4cda9b,0x4cfcc3,0x4cfdcd,0x4fea43,0x508a23,0x534877}
 contexts=[]
 for r in relative:
  a=int(r['site'],16);x=decoded.get(a)
  if r['target']=='005342E0' and a in expected and x and x.mnemonic=='call' and x.op_str=='0x5342e0':
   contexts.append(dict(site=r['site'],target=r['target'],bytes=x.bytes.hex(),entry_rooted_instruction=True,is_direct_C2S84_sender=False,phase_association_added=False))
 if {int(r['site'],16) for r in contexts}!=expected:raise RuntimeError('Qualified local GUI context sites differ')
 sites=[0x5342e1,0x5342e3,0x5342f8,0x534303,0x534309,0x53430e,0x534311,0x4a89a0,0x4a89a7]
 dump('native/actual-owner-and-tail-operands.json',[dict(site=f'{a:08X}',bytes=decoded[a].bytes.hex(),mnemonic=decoded[a].mnemonic,operand=decoded[a].op_str) for a in sites])
 relations=dict(native_sha256=native_sha,native_functions=functions,native84_emitter='005342B0',native84_body_source='WORD at *[actual_this+430AC]+0',native84_body_bytes=2,native84_logical_bytes=3,native84_body_fixed_zero=False,
  native84_direct_relative_target_candidates=sum(r['target']=='005342B0' for r in relative),native84_literal_VA_RVA_candidates=len(literal),native84_caller_qualified=False,native84_phase=None,native84_global_unreachability_claimed=False,
  local_close_helper='005342E0',qualified_local_close_contexts=contexts,close_scene_this_preserved=True,close_gui_root_delta='7785C',close_gui_slot_flags_scene_offset='78074',close_gui_root_slot_flags_offset='818',close_handle_offset='1C8500',close_handle_signed_nonnegative=True,close_wrapper_mask='20',close_helper_independent_mask='2',close_helper_slot_flag_write='(oldFlags&3)|4',
  close_tail='00534311 ->004A89A0',refresh_conditional_tail='004A89A7 ->004A8470',neighbor_004A89B0_not_tail_target=True,other_helper_callbacks_not_exhausted=True,wire84_cancel_inferred=False,native84_to_A0_pairing_inferred=False,
  source_reader='CnPrebornSubjectRequest',source_reader_unphased_format_only=True,WORLD84_registered=False,formal_application_hosted=False,complete_route=False)
 dump('native/ui-close-and-unphased84-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:138 actual native choice consumers/operand and common handoff sealed',cn_unphased_native84_readers_added=1,cn_local_preborn_close_direct_contexts_qualified=9,cn_refresh_tail_target_corrections=1,
  native_primary_metadata_bytes=sum(r['metadata_bytes'] for r in functions),native_local_normal_entry_CFGs=sum(r['complete_local_normal_CFG'] for r in functions),native_instruction_sites=sum(r['instruction_sites'] for r in functions),native84_caller_qualified=False,native84_phase=None,
  new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
  formal_application_hosted=False,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 p=b/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'));ledger['cn_preborn_ui_close_caller_lineage']=dict(facts,evidence=o.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name='CN actual local GUI close callers/tail ->unphased native84 format boundary',version_scope='pinned-cn-M1-unphased-format-and-GUI-source-only',status='Standalone84 format and local GUI lineage; no84 phase/ingress/authority/reply/runtime route',source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND
 ledger['dual_client_execution_plan']['next_source_frontier']='Native indirect/computed84 root remains open; actual common subject/skills/authority/rules/save/replay/issuer/CN rows/providers/Application and full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator. PHASE1.'
 p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/books[0]).open('a',encoding='utf-8') as f:f.write('\n\n## CN local GUI close / unphased84 boundary ('+ROUND+')\n\nQualified nine direct close contexts and actual5342E0 GUI-root/tail lineage;4A89A0 branches to4A8470,not neighboring4A89B0.84 emitter reads actual object WORD+0,not fixedzero. Added exact standalone3-byte reader without WORLD registration or guessed cancel/A0 pairing; indirect/root/phase and full common providers/authority/gameplay remain open. No new packet/phase/owner/complete route; full goal/PHASE1 retained.\n')
 for rel in SOURCES+books:
  d=(ROOT/rel).read_bytes();save('source/current/'+rel,d)
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),d.decode('utf-8-sig').splitlines(True)))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_bytes','native_local_normal_entry_CFGs','native_instruction_sites','cn_local_preborn_close_direct_contexts_qualified','native84_phase','new_complete_bidirectional_routes']}))
if __name__=='__main__':main()
