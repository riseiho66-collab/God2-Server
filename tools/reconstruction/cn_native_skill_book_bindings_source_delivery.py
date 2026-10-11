"""Pinned file/CFG/SKB accounting and actual source handoff; no runtime or DB."""
import csv,difflib,hashlib,json,re,struct
from collections import Counter
from pathlib import Path
import capstone,pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView,import_directory
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-native-skill-book-bindings-source-01'
ROUND='20261008-cn-native-skill-book-bindings-source'
NATIVE_SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/assets/CnNativeSkillBookBindings.h','src/cn/assets/CnNativeSkillBookBindings.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'docs/research/cn-native-skill-book-bindings-source-20261008.md',
 'tools/reconstruction/cn_native_skill_book_bindings_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=['Actual shared CN rows/providers/common subject and skill identity/eligibility/Lua/rules/save/persistent replay/issuer/Application remain unconfigured.',
 'Native no-match out-item caller state, full timing/native84 callers, TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/release remain open.']
def sha(d):return hashlib.sha256(d).hexdigest()
def main():
 b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
 if (o/'findings.json').exists():raise RuntimeError('Preserve prior delivery')
 def save(rel,d):
  p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(d)
 def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'));old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
 if len(before)!=144:raise RuntimeError('Expected144 before inputs')
 books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
 reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']};protected=[]
 for row in before:
  if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before snapshot differs')
  if row['path'] not in set(SOURCES+books)|reports:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 prior=(o/'retained-prior/cn-world-subject-skill-publication-source-01/manifest.json').read_bytes()
 if sha(prior)!='d4917a8948dc96ebe2afb3c9a61ee561e78d1cc158e08116b46ef92896dc842c' or not json.loads(prior)['sealed']:raise RuntimeError('Prior seal differs')
 raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
 if sha(raw)!=NATIVE_SHA:raise RuntimeError('Pinned PE differs')
 pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
 targets=struct.unpack('<9I',view.read(0x42d4f4-0x400000,36));mapping=view.read(0x42d518-0x400000,39)
 save('native/tables/0042D4F4.bin',view.read(0x42d4f4-0x400000,36));save('native/tables/0042D518.bin',mapping)
 if targets[mapping[5]]!=0x42d41f or targets[mapping[8]]!=0x42d494:raise RuntimeError('SKB/PFD parser branches differ')
 function_rows=[];all_ins={}
 for va,size in [(0x4d2bb0,378),(0x4283a0,37),(0x428c80,8176),(0x42cfb0,1345),
                 (0x42d6b0,603),(0x4231b0,115),(0x423270,93),(0x423140,9),(0x423150,20),
                 (0x76c3bf,11),(0x790027,93)]:
  paths=list(recovery.glob(f'part_*/{va:08x}_*.c'))
  if len(paths)!=1:raise RuntimeError('Primary source not unique')
  c=paths[0].read_bytes()
  if int(re.search(rb'Size: (\d+) bytes',c).group(1))!=size:raise RuntimeError('Metadata differs')
  code=view.read(va-0x400000,size)
  tables={0x42d244:('dword ptr [eax*4 + 0x42d4f4]',targets)} if va==0x42cfb0 else {}
  cfg,ins=local_cfg(md,code,va,tables);all_ins.update(ins)
  complete=not cfg['frontier']
  qualified_tails={0x76c3bf:'00790027',0x423140:'00423270'}
  if not complete and (va not in qualified_tails or cfg['frontier']!=[dict(site=qualified_tails[va],reason='outside_metadata_code')]):raise RuntimeError('Local normal CFG frontier: '+hex(va))
  save(f'native/functions/{va:08X}.c',c);save(f'native/functions/{va:08X}.bin',code);dump(f'native/functions/{va:08X}-cfg.json',cfg)
  save(f'native/functions/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
  function_rows.append(dict(va=f'{va:08X}',metadata_bytes=size,instruction_sites=len(ins),complete_local_normal_CFG=complete,qualified_tail_target=qualified_tails.get(va),sha256=sha(code)))
 # Primary literals/tables, including the type-name pointer table and each tag.
 bases=struct.unpack('<4I',view.read(0x7f3b44-0x400000,16))
 if bases!=(6500,6600,6700,6800):raise RuntimeError('Category item bases differ')
 save('native/tables/007F3B44.bin',view.read(0x7f3b44-0x400000,16))
 pointers=struct.unpack('<40I',view.read(0x886338-0x400000,160));tags=[view.string(p-0x400000) for p in pointers]
 if tags[6]!='SKB' or tags[9]!='PFD':raise RuntimeError('Actual native item type tags differ')
 save('native/tables/00886338.bin',view.read(0x886338-0x400000,160));dump('native/tables/item-type-tags.json',list(enumerate(tags)))
 for va in set(pointers)|{0x7f3b90,0x7f3b98,0x7f3ba4,0x7f3bb0,0x7f3bbc}:
  value=view.string(va-0x400000).encode('ascii')+b'\0';save(f'native/strings/{va:08X}.bin',value)
 imports=import_directory(pe,raw)
 dump('native/calloc-heap-allocation-operands.json',dict(calloc_heap_zero_flag_site='00790060',flag=8,
  calls=[dict(va=f'{a:08X}',mnemonic=x.mnemonic,operand=x.op_str) for a,x in all_ins.items() if 0x790027<=a<0x790084 and x.group(capstone.CS_GRP_CALL)],
  declared_HeapAlloc_bindings=[r for r in imports['bindings'] if r['name']=='HeapAlloc'],loaded_binding_observed=False))
 decoded=(b/'cn-current-npc-name-source-01/inputs/current-gamedata.csv').read_bytes()
 encoded=(b/'cn-current-npc-name-source-01/inputs/current-gamedata.csvZ').read_bytes()
 if sha(decoded)!='16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3' or sha(encoded)!='8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a':raise RuntimeError('Pinned resource pair differs')
 save('inputs/current-gamedata.csv',decoded);save('inputs/current-gamedata.csvZ',encoded)
 lines=decoded.splitlines(keepends=True);offsets=[];offset=0
 for line in lines:offsets.append(offset);offset+=len(line)
 header=next(i for i,line in enumerate(lines) if line.startswith(b'ItemType,'));types=[]
 for i in range(header+1,header+51):
  fields=next(csv.reader([lines[i].decode('cp936')]));types.append(fields[2])
 save('inputs/ItemType-raw-lines.bin',b''.join(lines[header:header+51]));dump('material/item-type-section-names.json',types)
 sections={};current=None;left=0;range_rows=[]
 for i,line in enumerate(lines):
  fields=next(csv.reader([line.decode('cp936')]))
  if len(fields)==2 and fields[0] in types and fields[1].isdigit():current=fields[0];left=int(fields[1]);continue
  if left:
   left-=1
   if not fields[0].isdigit():continue
   item=int(fields[0])
   if 6501<=item<=7199:
    row=dict(section=current,item_id=item,source_line=i+1,decoded_offset=offsets[i],fields=fields,raw_hex=line.hex(),record_sha256=sha(line))
    range_rows.append(row);sections.setdefault(current,[]).append(row)
 if set(sections)!={'SKB','PFD','GEH'} or len(sections['SKB'])!=386 or len(sections['PFD'])!=65 or len(sections['GEH'])!=47 or len({r['item_id'] for r in range_rows})!=498:raise RuntimeError('Actual pointer-range section census differs')
 if any(tag[:3]=='GEH' for tag in tags):raise RuntimeError('GEH native type mapping differs')
 dump('material/non-SKB-alias-exclusions.json',dict(PFD=dict(records=65,native_type=9,parser_default=True),GEH=dict(records=47,native_type=0,no_matching_primary_tag=True,parser_default=True),calloc_zero_alias=True))
 dump('material/all-pointer-range-rows.json',range_rows)
 skb=sections['SKB'];skb_header=lines[skb[0]['source_line']-2]
 if skb_header!=b'SKB,386\r\n' or skb[0]['decoded_offset']!=739107 or skb[-1]['decoded_offset']+len(bytes.fromhex(skb[-1]['raw_hex']))!=806862:raise RuntimeError('Actual SKB offsets differ')
 if any(b'"' in bytes.fromhex(r['raw_hex']) or len(r['fields']) not in (29,30) for r in skb):raise RuntimeError('Pinned bounded SKB shape differs')
 skill=(b/'cn-shared-skill-catalog-storage-source-01/inputs/cn/cbspec2.bin').read_bytes()
 if sha(skill)!='857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004':raise RuntimeError('Actual skill catalog differs')
 save('inputs/cn-current-cbspec2.bin',skill)
 bindings=[];counts=[125,130,87,111];letters=['A','D','C','B']
 for kind,count in enumerate(counts):
  for definition_id in range(1,count+1):
   selector='Spc'+letters[kind]+str(definition_id).zfill(2);width=6 if definition_id<100 else 7
   candidates=sorted([r for r in skb if bases[kind]<r['item_id']<bases[kind]+400 and r['fields'][26][:width]==selector[:width]],key=lambda r:r['item_id'])
   at=8+kind*0x6e04+(definition_id-1)*110;record=skill[at:at+110]
   bindings.append(dict(kind=kind,definition_id=definition_id,definition_offset=at,definition_sha256=sha(record),
    native_selector=selector,compare_bytes=width,candidate_item_ids=[r['item_id'] for r in candidates],
    matching_item_id=candidates[0]['item_id'] if candidates else None,common_gameplay_identity_qualified=False))
 matched=sum(r['matching_item_id'] is not None for r in bindings)
 if matched!=386:raise RuntimeError('Static first-match census differs')
 dump('material/native-skill-book-bindings.json',bindings)
 relations=dict(native_sha256=NATIVE_SHA,native_functions=function_rows,native_base_table='007F3B44',native_bases=list(bases),category_letters=letters,
  native_item_lookup='004283A0',actual_item_owner_operand='[actual_this+65364]',native_lookup='004D2BB0',native_parser='0042CFB0',
  item_pointer_loader='00428C80',type_name_loader='0042D6B0',SKB_type=6,PFD_type=9,SKB_type_branch='0042D41F',PFD_type_branch='0042D494',
  alias_source_column=26,alias_parsed_offset='11C',alias_nul_offset='12B',compare_lengths=[6,7],first_ascending_item_match=True,
  native_no_match_existing_out_item_preserved=True,native_no_match_caller_state_qualified=False,other_range_items=112,other_range_item_alias_bytes_zero=True,
  decoded_sha256=sha(decoded),encoded_sha256=sha(encoded),book_records=386,matched_definitions=matched,no_match_definitions=453-matched,
  definition_store='existing native_skill_catalog/native_data_sources',TW_native_skill_book_reader_unchanged=True,CN_full_parsed396_reconstruction_claimed=False,
  client_memory_required=False,native_execution=False,actual_shared_supplier_configured=False,formal_application_hosted=False,complete_route=False)
 dump('native/book-binding-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='no progress: user requested status only; resumed available native SKB source work',
  cn_native_skill_book_binding_suppliers_added=1,cn_existing_common_operation_book_handoffs_strengthened=1,
  native_primary_metadata_bytes=sum(r['metadata_bytes'] for r in function_rows),native_local_normal_entry_CFGs=sum(r['complete_local_normal_CFG'] for r in function_rows),native_instruction_sites=sum(r['instruction_sites'] for r in function_rows),
  cn_skill_book_records=386,cn_skill_book_matching_definitions=386,cn_skill_definitions_without_matching_book=67,
  new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
  actual_CN_skill_rows_imported=False,actual_shared_supplier_configured=False,actual_common_skill_identity_configured=False,formal_application_hosted=False,
  whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,
  protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 p=b/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'));ledger['cn_native_skill_book_bindings_source']=dict(facts,evidence=o.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name='CN actual SKB first-item binding ->same shared CN definition ->retained common preborn apply/delivery source',version_scope='pinned-cn-resource-identity-only',status='Actual supplier/optional common handoff; common identity/rules/save/replay/providers/Application unconfigured',source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND
 ledger['dual_client_execution_plan']['next_source_frontier']='Actual native skill-book callers/eligibility/common skill and subject mapping/rules/save/replay/issuer/Application; full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator. PHASE1.'
 p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/books[0]).open('a',encoding='utf-8') as f:f.write('\n\n## CN native skill-book bindings ('+ROUND+')\n\nRecovered primary category base/order/prefix-first lookup and SKB type6 alias writer; retained386 bindings/67 no-book definitions and112 zero-alias PFD/GEH candidates. Added pinned actual pair supplier with same shared CN catalog and optional owning common preborn apply/post-commit handoff. No common identity/learned ownership/rule/save/replay/provider/Application completion, no DB/native execution. Whole goal and PHASE1 preserved.\n')
 for rel in SOURCES+books:
  d=(ROOT/rel).read_bytes();save('source/current/'+rel,d)
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),d.decode('utf-8-sig').splitlines(True)))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_bytes','native_local_normal_entry_CFGs','native_instruction_sites','cn_skill_book_records','cn_skill_definitions_without_matching_book','new_complete_bidirectional_routes']}))
if __name__=='__main__':main()
