"""Round177 pinned TW client navigation closure; file-only static provenance.

Never runs a native program, path search, emulator, C++, Lua, codec, DB, API,
server, browser, build or test. Copies originals and disassembles bounded bytes.
"""
from pathlib import Path
import argparse
import hashlib
import json
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-mixed-dispatch-source-01'
OUT=ROUND/'agents/tw-path-frontier'
OWNED='tools/reconstruction/tw_native_path_search177.py'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE='399a29a063b59bccba1f27350e6d91991eba4c0604c979bfb52bf47ab58cf596'
BASE=0x400000
SOURCES=[
 'src/game/TaiwanNativeGrid.h','src/game/TaiwanNativeGrid.cpp',
 'src/protocol/RecoveredTaiwanMapCell.h',
 'src/game/SharedTaiwanNativeMovementScene.h','src/game/SharedTaiwanNativeMovementScene.cpp',
 'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
 'src/scripting/TaiwanMovementRules.h','src/scripting/TaiwanMovementRules.cpp',
 'src/protocol/RecoveredNativeMovement.h',
 'src/game/TaiwanNativeMapAsset.h','src/game/TaiwanNativeMapAsset.cpp',
 'src/game/TaiwanNativeTileMasks.h','src/game/TaiwanNativeTileMasks.cpp',
 'src/game/TaiwanNativeRomAsset.h','src/game/TaiwanNativeRomAsset.cpp',
]
CONTEXT=[
 'AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'docs/research/shared-taiwan-movement-20261007.md',
 'src/game/RecoveredTownNavigation.h','src/game/RecoveredTownNavigation.cpp',
 'tools/reconstruction/tw_native_movement_authority176.py',
 'artifacts/integration/packet-connections-20261006/tw-native-host-composition-source-01/agents/tw-authority-frontier/gaps.json',
 'artifacts/integration/packet-connections-20261006/tw-native-host-composition-source-01/agents/tw-authority-frontier/findings.json',
 'artifacts/integration/packet-connections-20261006/tw-native-movement-scene-source-01/agents/tw-cell-reader/native-spans.json',
]
# Every interval is an actual full function except the explicitly bounded
# constructor binding sites. Old getter/adapter intervals remain retained.
SPANS=[
 (0x61DB0,0x61DF7,'owner constructor: output126-byte buffer and work list','new_algorithm'),
 (0x61E00,0x61E1A,'owner destructor','new_algorithm'),
 (0x61E20,0x61E2A,'actual map-owner binder','new_algorithm'),
 (0x61E30,0x61E4E,'open-node key lookup','new_algorithm'),
 (0x61E50,0x61E6F,'closed-node key lookup','new_algorithm'),
 (0x61E70,0x61E94,'actual map-owner raw-cell probe','new_algorithm'),
 (0x61EA0,0x61EC8,'cost propagation work push','new_algorithm'),
 (0x61ED0,0x61EEC,'cost propagation work pop','new_algorithm'),
 (0x61EF0,0x61F8E,'closed-neighbor unit-cost propagation','new_algorithm'),
 (0x61F90,0x61FC5,'signed score ordered open insertion and equal-score precedence','new_algorithm'),
 (0x61FD0,0x62132,'candidate relaxation: lowWORD coordinates, existing keys, new squared score','new_algorithm'),
 (0x62140,0x62153,'coordinate key x*3072+y DWORD arithmetic','new_algorithm'),
 (0x62160,0x62182,'open pop prepends to closed history','new_algorithm'),
 (0x62190,0x623A9,'actual ordered eight-neighbor raw probes','new_algorithm'),
 (0x623B0,0x6248C,'bounded search producer and partial result','new_algorithm'),
 (0x62490,0x62549,'closed-history reversal, planar WORD output, cleanup','new_algorithm'),
 (0x62550,0x62727,'one midpoint repair per call, fixed count/output copy','new_algorithm'),
 (0x62730,0x62FE2,'all eight signed direction priority branches for midpoint fallback','new_algorithm'),
 (0x62FF0,0x630D5,'complete public search ABI, refinement and circular output count','new_algorithm'),
 (0x651DF,0x65267,'bounded real constructor sites binding both owners to actual world map','new_binding_sites'),
 (0xCD270,0xCD39E,'complete separate entity target chooser consuming search counts','new_other_consumer'),
 (0x1035B0,0x103634,'176 retained movement adapter and raw2 flag producer','retained176_context'),
 (0x46FF0,0x470AD,'171 retained raw getter mode/window branch','retained171_context'),
 (0x36B60,0x36BA6,'171 retained actual mode2 cell getter','retained171_context'),
]

def digest(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,copy):
 raw=path.read_bytes();put(OUT/copy,raw)
 return {'path':path.resolve().as_posix(),'copy':copy,'bytes':len(raw),'sha256':digest(raw)}
def sources(stage,names):
 rows=[original(ROOT/name,f'{stage}/s{n:02d}{Path(name).suffix}') for n,name in enumerate(names)]
 emit(stage+'-source-origins.json',rows);return rows

def recover():
 raw=IMAGE.read_bytes();before=(ROUND/'before-manifest.json').read_bytes()
 if digest(raw)!=PIN or digest(before)!=BEFORE or len(json.loads(before))!=1270:
  raise RuntimeError('Actual pinned input/fresh before mismatch; baseline never reset')
 OUT.mkdir(parents=True,exist_ok=True)
 put(OUT/'root-before.raw',before)
 emit('root-lineage.json',{'before_count':1270,'before_sha256':BEFORE,
  'prior176_members_retained':2290,'prior_verification':'parent fresh receipt','before_never_rewritten':True})
 sources('before',SOURCES)
 emit('new-file-before.json',[{'path':(ROOT/OWNED).as_posix(),'state':'absent in actual root fresh before','copy':None}])
 emit('original-inputs.json',[original(IMAGE,'input/native.bin')])
 emit('context-originals.json',[original(ROOT/name,f'context/c{n:02d}{Path(name).suffix}') for n,name in enumerate(CONTEXT)])
 emit('derived-inputs.json',{'decoded_or_emulated_inputs':[],
  'derived_static_outputs':['native-spans.json','native-sites.json','search-relations.json','stack-ledger.json'],
  'no_algorithm_native_or_CPP_execution':True})
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 records=[];instructions={}
 for index,(start,end,purpose,scope) in enumerate(SPANS):
  body=raw[start:end];copy=f'raw/n{index:02d}.bin';put(OUT/copy,body)
  rows=[]
  for i in decoder.disasm(body,BASE+start):
   item={'va':f'{i.address:08X}','rva':f'{i.address-BASE:08X}','bytes_hex':i.bytes.hex(),
    'mnemonic':i.mnemonic,'operands':i.op_str}
   rows.append(item);instructions[i.address-BASE]=item
  records.append({'start_va':f'{BASE+start:08X}','end_exclusive_va':f'{BASE+end:08X}',
   'start_rva':f'{start:08X}','end_exclusive_rva':f'{end:08X}',
   'copy':copy,'bytes':len(body),'sha256':digest(body),'purpose':purpose,'scope':scope,'instructions':rows})
 emit('native-spans.json',records)
 facts=[
  (0x61DB7,'calloc actual8-byte propagation-list sentinel'),
  (0x61DCB,'full actual output buffer pointer atowner+10'),
  (0x61DF0,'constructor initializes owner raw2flag to0; no permission meaning'),
  (0x61E24,'bind actual map owner atowner+0C'),
  (0x61E32,'open sentinel next at+3C'),(0x61E3D,'open lookup matches DWORD node coordinate key+14'),
  (0x61E53,'closed sentinel next at+3C'),
  (0x61E73,'actual map object comes from bound map owner+BC'),
  (0x61E87,'all path raw probes call actual446FF0 getter'),
  (0x61E8F,'native missing map returns0; absent/incomplete server data must remain separately unqualified'),
  (0x61F14,'unit cost improvement signed compare'),
  (0x61F25,'actual improved parent stored node+18, distinct from list linkage'),
  (0x61F31,'propagation scans contiguous populated child slots up to8'),
  (0x61FAE,'signed score insertion stops before equal score: newer equal-score node precedes'),
  (0x61FD7,'relaxation candidate Y argument'),(0x61FE2,'candidateY narrowed to raw unsigned lowWORD'),
  (0x61FEC,'candidateX narrowed to raw unsigned lowWORD'),
  (0x61FFA,'candidate G = current node G+1, same cost for diagonal/cardinal'),
  (0x62007,'search open first by actual coordinate key'),
  (0x62027,'record observed child pointer in contiguous child slots'),
  (0x6203E,'open improvement updates actual parent+18; no resort call in this branch'),
  (0x62054,'then search closed by coordinate key'),
  (0x62093,'closed improvement propagates costs to retained children'),
  (0x620D9,'new node squared Y distance with actual DWORD IMUL'),
  (0x620DE,'new node squared X distance with actual DWORD IMUL'),
  (0x620F0,'new scoreH+G actual DWORD sum'),
  (0x62104,'node coordinateY storedWORD'),
  (0x62108,'new node inserted into signed score sorted open list'),
  (0x62148,'exact key = (X*3)<<10 +Y, not a guessed map stride'),
  (0x6216E,'pop first open node'),
  (0x62178,'node+3C linked to old closed head: expansion history, not parent chain'),
  (0x62181,'returns actual popped node ornull'),
  (0x621A3,'NW uses lowWORD decrement/wrap before raw getter'),
  (0x621BF,'NW probes only own rawcell AL nonzero, no orthogonal-side gate'),
  (0x621FD,'N rawcell predicate'),(0x6224F,'NE rawcell predicate'),
  (0x6228D,'E rawcell predicate'),(0x622CD,'SE rawcell predicate'),
  (0x6230B,'S rawcell predicate'),(0x6234B,'SW rawcell predicate'),(0x62389,'W rawcell predicate'),
  (0x623C9,'compute goal coordinate key'),
  (0x62404,'initial fullDWORD X distance'),
  (0x6241F,'initial nodeH squared distance'),
  (0x6242C,'initial coordinateX lowWORD'),
  (0x6244F,'terminal compares popped node key to goal key'),
  (0x62457,'actual hard iteration boundary29'),
  (0x6245C,'also actual supplied iteration budget; public entry supplies10'),
  (0x6246D,'expand eight-neighbor routine'),
  (0x62489,'returns current node even on budget stop; partial result is not goal admission'),
  (0x624A7,'reverse node+3C closed history, not parent+18'),
  (0x624D9,'history outputX WORD at planar buffer+2..3C'),
  (0x624E7,'history outputY WORD at planar buffer+40..7A'),
  (0x62502,'planar output maximum30 copied entries'),
  (0x62508,'outputBYTE count equals extracted entries'),
  (0x62541,'returns extracted count after freeing search nodes/sentinels'),
  (0x625AF,'repair asserts signed gapX within[-10,+10]; not a new serverlimit'),
  (0x625E5,'accepts current adjacency with signed dx/dy within[-1,+1]'),
  (0x62627,'midpoint dy divided by2 truncates toward0'),
  (0x6263A,'midpoint dx divided by2 truncates toward0'),
  (0x62648,'probe actual midpoint cell'),
  (0x62675,'blocked midpoint picks first raw-nonzero directional neighbor'),
  (0x62689,'insertion makes repair return0'),
  (0x626CC,'insert one midpoint before first nonadjacent pair'),
  (0x6270E,'preserve original buffer countBYTE'),
  (0x62712,'copy exactly31 DWORD plusWORD =126 bytes'),
  (0x62716,'return repair completion flag, not server Permit'),
  (0x62746,'midpoint priority branch first tests signed dx then dy'),
  (0x62FBC,'asserts output pointers exist, not that a candidate was found'),
  (0x62FDF,'fallback returns with output pointers unchanged if all eight zero'),
  (0x63002,'public entry literal search budget10'),
  (0x63004,'store raw2flag atowner+14; no matching owner read in this complete closure'),
  (0x6301B,'actual public search call'),
  (0x63027,'closed-history output producer'),
  (0x6303D,'one repair pass each time'),
  (0x63046,'save OLD refinement counter before increment'),
  (0x6304C,'oldcounter<=30 repeats: at most32 repair calls'),
  (0x6304E,'assert intermediate count<30; assert behavior not interpreted as success'),
  (0x63096,'append unsignedWORD X to supplied actual caller points'),
  (0x630A4,'append unsignedWORD Y to supplied actual caller points'),
  (0x630AF,'compare incremented caller count to actual output capacity'),
  (0x630B3,'capacity crossing resets caller count0, does not reject or mean destination reached'),
  (0x630D2,'public ABI ret32; no stable semantic bool result'),
  (0x65209,'world real map owner read for actual navigation owner binding'),
  (0x65219,'store movement search owner world+A7E05D0'),
  (0x6521F,'bind same actual map owner through461E20'),
  (0x6525C,'second actual search owner world+A7E05D4'),
  (0x65262,'second owner binds actual map object, no generated address'),
  (0xCD337,'separate entity target selection uses same count-producing pathsearch'),
  (0xCD340,'chooses target by resulting count, not a dynamic blocker mask'),
  (0x103605,'176 retained actual raw2flag qualifier'),
  (0x103628,'176 retained ordinary movement caller; no new opcode'),
 ]
 emit('native-sites.json',[{'va':f'{BASE+address:08X}','rva':f'{address:08X}',
  'instruction':instructions[address],'fact':fact,
  'scope':next(scope for start,end,_,scope in SPANS if start<=address<end)} for address,fact in facts])
 ledger={
  'all_addresses':'VA; corresponding RVA=VA-00400000; complete image fileoffset==RVA',
  'public_00462FF0':{'entry_ESP':'E','ECX':'actual navigation owner',
   'arguments_at_E':['+04 count*','+08 actual caller point buffer*','+0C capacityDWORD',
    '+10 startXDWORD','+14 startYDWORD','+18 destinationXDWORD','+1C destinationYDWORD','+20 raw2flagDWORD'],
   'stdcall_ret_bytes':32,
   'push_ledger':['push ECX -> E-4; readflag E+20 and destX E+18',
    'push EBX,ESI,EDI -> E-16; read destY E+1C',
    'push10 -> E-20; readstartY from [esp+28]=E+14',
    'pushdestY -> E-24; readstartX from[esp+28]=E+10',
    'pushdestX,startY,startX -> E-36; call004623B0(startX,startY,destX,destY,10)'],
   'result':'output pointer/count mutation; EAX not documented/nativequalified as boolean Permit'},
  'search_004623B0':{'args':['startX','startY','destX','destY','actual budget10'],
   'ret_bytes':20,'result':'last popped node pointer ornull, can be budget-limited non-goal'},
  'neighbor_00462190':{'args':['actual node','destinationX','destinationY'],'ret_bytes':12},
  'relax_00461FD0':{'args':['actual current node','candidateX','candidateY','destinationX','destinationY'],'ret_bytes':20},
  'repair_00462550':{'args':['count*','actual126-byte planar buffer*'],'ret_bytes':8,
   'result':'1 means no nonadjacent pair found in inspected fixed count, not server permission'},
  'fallback_00462730':{'args':['outX*','outY*','baseX','baseY','signed dx','signed dy'],'ret_bytes':24,
   'result':'writes first raw-nonzero candidate; if none, outputs stay at caller initialized0; not boolean'},
 }
 emit('stack-ledger.json',ledger)
 relations={
  'owner_fields':{'00':'open sentinel pointer','04':'closed sentinel pointer','08':'8-byte propagation work-list sentinel',
   '0C':'actual map owner, getter+BC','10':'owned126-byte planar output','14':'actual raw2flag stored but not read by this closure'},
  'node_fields':{'00':'signed compare score H+G, DWORD arithmetic','04':'squared-distanceH DWORD',
   '08':'unit-costG DWORD','10/12':'unsigned lowWORDX/Y','14':'DWORDkey X*3072+Y',
   '18':'actual improved parent pointer, NOT output list','1C..38':'8 actual child slots',
   '3C':'open/closed/history next pointer'},
  'output_layout':{'bytes':126,'count_offset':0,'count_width':'BYTE','padding_offset':1,
   'x_words_offset':2,'y_words_offset':64,'entry_capacity':30},
  'neighbor_order':['NW','N','NE','E','SE','S','SW','W'],
  'candidate_raw_rule':'getter returns AL; accept any rawnonzero including2/254/255; no normalization',
  'diagonal_rule':'each candidate checked alone; no side-orthogonal AND rule in actual closure',
  'cost_and_order':'every edgeG+1; H=squaredcoordinate differences; signed score sorted; newer equal score inserted before older; open improvements not re-sorted in that branch',
  'history_output':'00462490 reverses node+3C closed-pop history; parent+18 is not traversed; route is not conventional parent shortest path',
  'partial_search':'budget10/hard29, returns last popped even without goalkey; no reached-destination guarantee',
  'repair':'signed midpoint truncates toward0, one insertion per pass; preserves count* and originalBYTEcount; fixed126-byte copy can drop trailing coordinate; max32passes',
  'fallback_probe_order_by_delta_sign':{
   '+,+':['SE','E','S','NE','SW','N','W','NW'],
   '+,0':['E','NE','SE','N','S','NW','SW','W'],
   '+,-':['NE','N','E','NW','SE','W','S','SW'],
   '0,-':['N','NW','NE','W','E','SW','SE','S'],
   '-,-':['NW','W','N','SW','NE','S','E','SE'],
   '-,0':['W','SW','NW','S','N','SE','NE','E'],
   '-,+':['SW','S','W','SE','NW','E','N','NE'],
   '0,+':['S','SE','SW','E','W','NE','NW','N'],
   '0,0':[]},
  'raw2flag':'public entry writesowner+14; constructor initializes it; no actual owner+14 reads in the whole recovered algorithm closure. node+14 is a separate key field. No global absence claim.',
  'dynamic_entities':'raw getter/map lifecycle may reflect actual resources; this closure has no independent actor-blocker list or separate server entity mask. Other004CD270 target chooser is not movement collision authority',
  'arithmetic':'actual DWORD wrap/IMUL and signed comparison, WORD coordinate wrap/key collisions are not silently replaced. Future checked domain must be explicit, no newnative limit.',
 }
 emit('search-relations.json',relations)
 frontier={
  'next_concrete_source_action':'implement separately tagged immutable client-navigation owner, preserving bounded pop history and repair ABI; bind exact resources/current. Do not replace Authority with nonempty path.',
  'actual_inputs_required':['full qualified rawResources/current generation/map/window lifetime',
   'actual start/destination DWORDs and ordinary native lowWORD domain',
   'actual original caller pointbuffer/count/capacity for circular append',
   'retained raw2flag and original126-byte output provenance'],
  'result_fields_required':['original planar output and count','ordered closed-pop history',
   'fixed-count repaired points','actual caller count mutation','explicit goalkey reached indicator derived from actual termination',
   'unsupported/assert/overflow/incomplete-data states separated from ordinary empty search'],
  'mandatory_qualification':'resource/owner generation and full input identity must be current before/after source use; OOB known-cell fallback cannot replace missing resource data',
  'Authority_CPP_API_change_required':False,
  'actual_existing_API':'Authority::authorize(Candidate) with strongly owned current/publish ticket remains server admission owner',
  'not_recovered_here':['original server dynamic occupancy/collision policy','original server pending/timing/battle/transfer ticket','original full5D producer'],
  'no_game_CPP_edits':True,
  'reject_false_native_substitutes':['generic A* parent path','sqrt/Manhattan/octile heuristic','diagonal cost1.414','invented side-cell corner AND',
   'unknown data normalized0/1','raw2flag=server rights','resultcount>0 means destination permitted'],
 }
 emit('source-field-frontier.json',frontier)
 emit('gaps.json',{
  'algorithm_scope':'complete bounded client algorithm and actual map adapter recovered; not all gameplay/navigation callers or original server collision',
  'server_admission':'OPEN original dynamic occupancy/pending/reset/timing/battle/transfer/5D producer; no client display success promoted',
  'assert_and_unsafe_native_domains':'actual402C70 assertion effects, failed nativeallocation, wrap/keycollision and oversizedcaller buffers not generalized into safe success',
  'no_candidate_midpoint':'actual initialized0 outputs may remain0 ifallneighborcells0; future qualified source must distinguish unresolvedrepair, never fabricate AL1',
  'dynamic_map_current':'actual selected rawmap/window/object/frame resource owner remains mandatory; complete masks alone do not establish current navigation',
  'other_callers':'004CD270 recovered whole target chooser; its004CD200 targeteligibility callee/other interactions not part of collision closure',
  'client_only':'complete clientnavigation does not recover native server authority; fullgame percentages unknown',
  'phase':'no build/test/native/C++/Lua/API/DB/SQL/runtime/deploy or archive restore'})
 emit('findings.json',{'round':'20261008-tw-native-mixed-dispatch-source','owned_sources':[OWNED],
  'game_CPP_modified':0,'new_algorithm_functions':19,'new_bounded_binding_span':1,'new_other_consumer_function':1,
  'retained171_context_spans':2,'retained176_context_spans':1,'all_spans':len(records),
  'new_raw_algorithm_bytes':sum(r['bytes'] for r in records if r['scope']=='new_algorithm'),
  'all_raw_span_bytes':sum(r['bytes'] for r in records),'native_sites':len(facts),
  'original_inputs':1,'full_native_image_bytes':len(raw),'decoded_derived_inputs':0,
  'actual_key_new_facts':['closed-pop history is not parent path','non-goal result on actual10-budget stop',
   'rawnonzero-only eight candidate probes; no corner side-cell gate',
   '32 fixed-count midpoint repair calls, circular count append; not bool Permit',
   'raw2flag stored unused within this closure; no invented mode permission'],
  'native_relations':'search-relations.json','source_action':'source-field-frontier.json',
  'prior_176_gaps_retained':'complete original context copy; no overwrite',
  'new_opcodes':0,'complete_routes_added':0,'whole_game_percentage':None,
  'no_execution_tests_or_build':True})
 sources('intermediate',[OWNED])
 print(json.dumps({'raw_spans':len(records),'native_sites':len(facts),'original_inputs':1,
  'before_sources':len(SOURCES),'tool_bytes':len((ROOT/OWNED).read_bytes()),'tool_sha256':digest((ROOT/OWNED).read_bytes())}))

def final():
 rows=sources('current',SOURCES+[OWNED])
 emit('delivery.json',{'BATCHFINAL_received':True,'current_originals':len(rows),
  'owned_game_CPP':0,'owned_tools':[OWNED],'newopcodes':0,'complete_routes':0,'percentage':None,
  'native_inputs_separate':True,'mutable_root_books_catalog_ledger_not_current_pinned':True})
 members=[]
 for path in sorted(OUT.rglob('*')):
  if path.is_file():
   raw=path.read_bytes();members.append({'path':path.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':digest(raw)})
 emit('seal.json',{'format':'god2-agent-full-artifact-seal-v1','member_count':len(members),
  'members':members,'source_only':True,'whole_game_percentage':None})
 print(json.dumps({'current_originals':len(rows),'sealed_members':len(members),
  'tool_sha256':digest((ROOT/OWNED).read_bytes()),'seal_sha256':digest((OUT/'seal.json').read_bytes())}))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--final',action='store_true',help='only after explicit parent BATCHFINAL')
 final() if parser.parse_args().final else recover()
