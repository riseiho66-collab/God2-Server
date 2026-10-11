"""Bounded actual TW typed chat linkage and initialized prefix facts.

Source/static files only. No codecs/emulation/client/server/C++/Lua/build/tests,
DB/API/Windows calls. Original header bytes are not authentication evidence.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-chat-family-source-01'
OUT=ROUND/'agents/tw-chat-family-frontier'
OWNED='tools/reconstruction/tw_native_chat_family179.py'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE='84ef1dbd91fc9cf22107e947a2630b274a6b8169f5ee457be5f81a15ac6a33f7'
BASE=0x400000
SOURCES=[
 'src/protocol/RecoveredChat.h','src/protocol/RecoveredPartyChat.h',
 'src/protocol/RecoveredPrivateChat.h','src/protocol/RecoveredGuildChat.h',
 'src/protocol/RecoveredWorldRecords.h','src/protocol/RecoveredTaiwanServerRecords.h',
 'src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
 'src/cn/protocol/CnChat.h','src/cn/protocol/CnChatConsumerContract.h',
 'src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp',
 'src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
 'src/text/ChineseText.h','src/text/ChineseText.cpp',
]
CONTEXT=[
 'AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'docs/research/private-locale-native-chat-20260923.md',
 'docs/research/town-chat-channel-20260924.md',
 'docs/research/server-chinese-conversion-20260923.md',
 'docs/research/cn-shared-native-chat-owner-20261007.md',
 'docs/research/chat-repair-and-freeze-20260927.md',
 'tools/reconstruction/tw_native_chat_source178.py',
]
# End offsets are exclusive. Existing178 complete paths are deliberately retained,
# never relabeled as new. The new UI interval is not the whole enclosing handler.
SPANS=[
 (0x7DC20,0x7DC84,'complete actual12-slot ESC prefix initialization and owner defaults','new_complete_prefix_initializer'),
 (0x7DC90,0x7DCA4,'complete local tab equality selector, not server permission','new_complete_tab_selector'),
 (0xB12B0,0xB15B8,'complete local tab setter with party/guild local state gates and private tab3','new_complete_tab_setter'),
 (0xB29B0,0xB29C5,'complete actual automatic private text accessor, original index0 caller and51-byte stride','new_complete_reply_accessor'),
 (0xB31D1,0xB32A6,'bounded additional private-target UI input caller, not whole event handler','new_bounded_UI_caller'),
 (0x968E0,0x9698C,'178 retained special $gmsoft01 channel2 producer, not ordinary identity','retained178_special_producer'),
 (0x96990,0x96F7C,'178 retained complete channel producer, allraw request fields/target/header/gates','retained178_channel_producer'),
 (0x132E0,0x13368,'178 retained exact opcode+body queue producer','retained178_queue'),
 (0x6AE96,0x6B022,'178 retained complete world5C case; opaque server header remains supplied','retained178_world_consumer'),
 (0x75E00,0x7652A,'178 retained complete panel family including0/8 and2/9 aliases and private callbacks','retained178_panel'),
 (0x7DE00,0x7E0AD,'178 retained scratch256 andprefix+text+NUL capacity domain, no glyph closure','retained178_scratch_sink'),
 (0xC7610,0xC766D,'178 retained local common/party/private/guild settings visibility helper','retained178_filter'),
 (0x7DD60,0x7DDBE,'178 retained raw legacy-byte name-prefix splitter, not authoritative identity','retained178_name_splitter'),
 (0x7DDC0,0x7DDFD,'178 retained received private history helper','retained178_private_history'),
 (0xB2EA5,0xB2F9B,'178 retained bounded ordinary/private-tab UI callers0/defaultWORD0','retained178_UI_callers'),
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
 if digest(raw)!=PIN or digest(before)!=BEFORE or len(json.loads(before))!=1285:
  raise RuntimeError('Pinned actual original/fresh before mismatch; retain baseline')
 OUT.mkdir(parents=True,exist_ok=True)
 put(OUT/'root-before.raw',before)
 emit('root-lineage.json',{'before_inputs':1285,'before_sha256':BEFORE,
  'prior178_members_retained':2258,'prior_scope':'parent full-member preservation receipt',
  'baseline_replaced':False})
 sources('before',SOURCES)
 emit('new-file-before.json',[{'path':(ROOT/OWNED).as_posix(),'state':'absent in root fresh before','copy':None}])
 emit('original-inputs.json',[original(IMAGE,'input/native.bin')])
 emit('context-originals.json',[original(ROOT/name,f'context/c{n:02d}{Path(name).suffix}') for n,name in enumerate(CONTEXT)])
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 records=[];instructions={}
 for n,(a,b,purpose,scope) in enumerate(SPANS):
  body=raw[a:b];copy=f'raw/n{n:02d}.bin';put(OUT/copy,body)
  rows=[]
  for i in cs.disasm(body,BASE+a):
   row={'va':f'{i.address:08X}','rva':f'{i.address-BASE:08X}',
    'bytes_hex':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}
   rows.append(row);instructions[i.address-BASE]=row
  records.append({'start_va':f'{BASE+a:08X}','end_exclusive_va':f'{BASE+b:08X}',
   'start_rva':f'{a:08X}','end_exclusive_rva':f'{b:08X}',
   'copy':copy,'bytes':len(body),'sha256':digest(body),
   'scope':scope,'purpose':purpose,'instructions':rows})
 emit('native-spans.json',records)
 sites=[
  (0x7DC2F,'initializer actual owner39E18 state clear'),
  (0x7DC4F,'initializer starts first actual prefixslot58EBE8'),
  (0x7DC5B,'initializer native destination settings39E04=0F'),
  (0x7DC66,'eachactualprefix firstBYTE patched toESC1B; rawimage31 is not initialized value'),
  (0x7DC69,'actual prefix slot stride4'),
  (0x7DC6C,'stop at58EC18 exclusive, exactly12 prefixslots'),
  (0x7DC7C,'actual owner39DFA initialized, not server ready/permission'),
  (0x7DC90,'read fullDWORD actual owner localtab39E00'),
  (0x7DC9C,'compare localtab to actualargument; no membership lookup'),
  (0xB12F4,'localtab setter actualsecondargument mode0..4'),
  (0xB1301,'complete native5case localtab setter table'),
  (0xB136A,'mode4 stores localtab4, producerlater mapschannel13style'),
  (0xB13DB,'mode0 stores localtab0'),
  (0xB13EA,'mode1 loadsactual relatedclientowner86888'),
  (0xB13F0,'mode1 actualrelatedowner DWORD3F98 localgate'),
  (0xB13F8,'party localgate failure jumpssetter false'),
  (0xB1470,'qualified mode1 storeslocaltab1'),
  (0xB147B,'mode2 loadsactualrelatedclientowner86888'),
  (0xB1481,'mode2 actualrelatedowner BYTE6 localgate'),
  (0xB1486,'guild localgate failure jumpssetter false'),
  (0xB14FF,'qualified mode2 storeslocaltab2, producerlater mapswire3'),
  (0xB152B,'localgate failure returnsfalse; not serverpermission'),
  (0xB15A3,'mode3 storeslocaltab3, private-target UI selector'),
  (0xB29B0,'accessor actualindexargument'),
  (0xB29BB,'accessor returnsglobal5B7698 +51*actualindex; no targetauthority'),
  (0xB31F7,'private UI actualtab3 predicate47DC90'),
  (0xB3228,'bounded UI copiesactual51B suppliedtext domain from real widget'),
  (0xB3262,'bounded UI rawtext suppliedfromlocal A4, targetfromlocal14'),
  (0xB3269,'bounded UI pushesrawtarget pointer unchanged'),
  (0xB326A,'bounded UI calleropaqueWORD argument0'),
  (0xB326C,'bounded UI callerselectionargument0, producerusesactualtab/target'),
  (0xB3271,'actual complete-boundary E8 ordinary496990 caller'),
  (0x968F6,'retained178 specialactualGM-like literal $gmsoft01 %s'),
  (0x96931,'retained178 speciallow7channel2 not ordinarycommon0'),
  (0x96959,'retained178 specialopaqueWORDFFFF is not exclusiveGMidentity'),
  (0x96A88,'retained ! localparty gate relatedowner3F98'),
  (0x96AA4,'retained # localguild gate relatedownerBYTE6'),
  (0x96AD4,'retained $ rawtarget/body delimiter ASCIIspace viaactualCRT'),
  (0x96AEE,'retained split atfirstspace beforetargetcopy'),
  (0x96B1E,'retained skiprepeatedASCIIspaces beforebody'),
  (0x96B47,'retained successfulnamedtarget selects2'),
  (0x96BC1,'retained tab3predicate compares actualstate, not permission'),
  (0x96BD1,'retained private-tab selection requiresactualtargetpointer nonnull'),
  (0x96BD5,'retained tab3+target selects2'),
  (0x96BEE,'retained tab1 selectsactualwire1'),
  (0x96BF5,'retained tab2 selectsactualwire3'),
  (0x96CBA,'retained exact wireformatter $%s %s usesrawtarget andpreparedbody'),
  (0x96CFB,'retained actualcaller9 override separatebranch'),
  (0x96D15,'retained actualcaller9 forceswirechannel9'),
  (0x96D25,'retained actualcaller9 same $%s %s formatter'),
  (0x96D79,'retained bodyWORDpreparedtextsize+8 includesopcode'),
  (0x96D94,'retained ordinary opaqueWORD fromactualcaller thirdarg'),
  (0x96D9B,'retained low16 storeofactualcallerWORD, no targetIDauthority'),
  (0x96DBA,'retained actualtag/channelBYTE store; residueBYTElogical4 neverwritten'),
  (0x96E64,'retained channel9 bypass of localrepeatthreshold, not serverrate'),
  (0x96E98,'retained wire9 skips ambiguousleading$ recovery'),
  (0x96E9C,'retained wire2 skips ambiguousleading$ recovery'),
  (0x96EF8,'retained ambiguousleading$ recovery rewriteswire2 too, no ordinary-prose inference'),
  (0x96EFA,'retained recovery opaqueWORDFFFF overlapsnamed/specialheader'),
  (0x96F24,'retained actual2F queuecaller withallbody bytes'),
  (0x13338,'retained queuecopiesallbodybytes unchanged'),
  (0x6AE9E,'retained5C actualchannel/tagBYTE9'),
  (0x6B018,'retained actuallow7channel fedinto475E00'),
  (0x75E31,'retained full17case paneltable, includingwire8 alias0 and9 alias2'),
  (0x75E9A,'retained0/8 panel localfilterchoice0'),
  (0x75EB1,'retained1 panel localfilterchoice1'),
  (0x75EC8,'retained1 scratchsinkselector1'),
  (0x75EDE,'retained2/9 panel localfilterchoice2'),
  (0x75EF5,'retained2/9 scratchsinkselector2 notwire9'),
  (0x75F3C,'retained private namehistory sideeffect whenprefixnotlocalname'),
  (0x75F8D,'retained privatewire9 automodebranch exitsviaUI reset'),
  (0x75FAA,'retained privateautomaticbody actualtextaccessorindex0'),
  (0x75FE4,'retained automaticprivatecalleropaqueWORDFFFF'),
  (0x75FE9,'retained automaticprivatecallerselector9'),
  (0x75FEE,'retained exactautomatic9 producer496990 call'),
  (0x76000,'retained ordinaryprivate continuation validatesactual receivedname'),
  (0x76074,'retained secondautomaticprivatecaller2 withopaqueWORDFFFF'),
  (0x7618F,'retained3 localguildfilterchoice3'),
  (0x761A6,'retained3 scratchsinkselector3'),
  (0x761C2,'retained5 directscratchsinkselector5'),
  (0x7626E,'retained6 localfilterchoice0'),
  (0x76285,'retained6 scratchsinkselector6'),
  (0x76514,'retained0/8 commonscratchsinkselector0'),
  (0x76518,'retained commonscratch47DE00'),
  (0x7DE73,'retained scratchclear63DWORD plusfirstBYTE WORD BYTE =256'),
  (0x7DF00,'retained scratch usesmapped sinkselector*4 actualinitializedprefix'),
  (0x7DF4F,'retained appendfulltext unchecked,252 domain independentof254producer'),
  (0xC7642,'retained partydisplayfilter actualsettingsbit5'),
  (0xC7657,'retained privatedisplayfilter actualsettingsbit6'),
  (0xC7660,'retained guilddisplayfilter unconditionaltrue localpolicy only'),
  (0x7DD7E,'retained rawname splitter actualcolon followedASCIIspace'),
  (0xB2F30,'retained ordinaryUI opaqueWORD0'),
  (0xB2F37,'retained actualordinary/private target UI producer'),
 ]
 emit('native-sites.json',[{'va':f'{BASE+a:08X}','rva':f'{a:08X}',
  'instruction':instructions[a],'fact':fact,
  'scope':next(scope for start,end,_,scope in SPANS if start<=a<end)} for a,fact in sites])
 data=[]
 for n,(a,length,role) in enumerate([
  (0xB15B8,20,'new complete localtab setter5target VA cells'),
  (0x18EBE8,48,'retained178 full12prefix slots; initializer actualESC mutation newly linked'),
  (0x96F7C,20,'retained178 complete5prefix targets'),
  (0x96F90,94,'retained178 complete94prefix selectors'),
  (0x96FF0,20,'retained178 complete5localtab target cells'),
  (0x97004,24,'retained178 complete6channel producer targets'),
  (0x9701C,14,'retained178 complete14channel selectors'),
  (0x7652C,68,'retained178 complete17panel targets including aliases0/8 and2/9'),
  (0x7E0B0,56,'retained178 complete14scratch local visibility targets'),
  (0xC7670,16,'retained178 complete4panel visibility filtertargets'),
  (0x190168,13,'retained178 originalspecial $gmsoft01 %s includingNUL'),
  (0x1901A0,8,'retained178 named2/9 $%s %s exactformatter'),
  (0x1823C8,2,'retained178 actual rawASCIIspace delimiter'),
 ]):
  body=raw[a:a+length];copy=f'raw/d{n:02d}.bin';put(OUT/copy,body)
  data.append({'va':f'{BASE+a:08X}','rva':f'{a:08X}','copy':copy,
   'bytes':len(body),'sha256':digest(body),'raw_hex':body.hex(),'purpose':role})
 emit('native-data.json',data)
 panel=struct.unpack_from('<17I',raw,0x7652C)
 setter=struct.unpack_from('<5I',raw,0xB15B8)
 prefixslots=[raw[0x18EBE8+n*4:0x18EBE8+n*4+4] for n in range(12)]
 # This is a byte-based source relation, not execution/emulation of native code.
 # The documented complete initializer writes only BYTE0=1B for each4Bslot.
 choices={0:0,1:1,2:2,3:3,5:5,6:6,8:0,9:2}
 family=[]
 for channel,sink in choices.items():
  literal=prefixslots[sink]
  family.append({'wire_channel':channel,'panel_branch_va':f'{panel[channel]:08X}',
   'scratch_selector':sink,'prefix_slot_va':f'{BASE+0x18EBE8+sink*4:08X}',
   'raw_original_slot_hex':literal.hex(),'initialized_three_bytes_hex':(b'\x1b'+literal[1:3]).hex(),
   'initializer':'0047DC20..0047DC84 / write0047DC66, stride4, end0058EC18',
   'scratch_prefix_bytes':3,'scratch_buffer_bytes':256,'safe_whole_text_bytes':252,
   'not_all_destination_lifecycle_proof':True,
   'additional_private_history_auto_reply_state':channel in (2,9)})
 emit('plain-sink-families.json',family)
 emit('local-tab-linkage.json',{'actual_table_va':'004B15B8',
  'setter_branches':[{'actual_mode':n,'target_va':f'{va:08X}'} for n,va in enumerate(setter)],
  'mapping':{'0':{'stored_tab':0,'wire_selection':0,'local_gate':'none inactualsetter'},
   '1':{'stored_tab':1,'wire_selection':1,'local_gate':'actualrelatedowner86888->DWORD3F98 nonzero'},
   '2':{'stored_tab':2,'wire_selection':3,'local_gate':'actualrelatedowner86888->BYTE6 nonzero'},
   '3':{'stored_tab':3,'wire_selection':'2 onlyif actualrawtarget pointer supplied, else unresolvedFF path'},
   '4':{'stored_tab':4,'wire_selection':13,'plain_player_domain':False}},
  'predicate':'47DC90 returnslocaltab39E00==actualargument; no actualserverauthority',
  'party_guild_lexical_prefixes':'!/# gatedlocally; onfailure do not silently classify wireparty/guild',
  'source_permission':'OPEN actualserviceparty/guild/current audience mustsupply, not tab/header-derived'})
 emit('exact-request-fields.json',{
  'logical_layout':{'0':'opcode2F','1/2':'LEWORD full logicaltotal','3':'actualtagbit7 pluslow7channel',
   '4':'unwrittenstackresidue retainedraw','5/6':'LEWORD actualcallerthirdarg low16 exceptstyle13',
   '7..end-2':'fullprepared rawtext','end-1':'NUL'},
  'typed_dispatch':'RecoveredWorldRecords creates Party1 / Private2,9 / Guild3 retaining allfourheaderbytes andfulltext',
  'ordinary_UI_actual_WORD':0,'automatic_private_actual_WORD':65535,
  'WORD_never_proves':['recipientidentity','party/guildmembership','GMpermission','ordinaryprose'],
  'native_prepared_max_text':254,'native_total_formula':'preparedstrlen+8 includingopcode andNUL',
  'raw_named_input':'leading$ target untilfirstASCIIspace,skiprepeatedseparatorASCIIspaces,requirebody nonempty',
  'actual_named_wire':'$ +originalrawtarget +oneASCIIspace +preparedrawbody',
  'actual9_override':'caller9 independently forces9 withsame $%s %s formatter; clientrepeat exception only',
  'GM_overlap':'4968E0 special $gmsoft01 %s forces2/FFFF; ordinary NamedWhisper2 callerFFFF canmatchsamebytes, residue/tag domains overlap',
  'required_prose_identity':'explicit actualsource issuer/PlayerText orNamedWhisper qualification; header or $name structurealone cannot identifyGMvsordinary',
  'no_roundtrip_fixtures_created':True})
 emit('caller-linkage.json',{
  'additional_bounded_UI':{'span':'004B31D1..004B32A6','actualproducer_call':'004B3271',
   'input_text':'actualwidget localA4','input_target':'actualwidget local14',
   'pushes':['rawtargetpointer','opaqueWORD0','callerchannel0','rawtextpointer'],
   'domain':'actual localtab3 canqualifytarget branch; producerowns finalchannelselection'},
  'retained178_UI':{'span':'004B2EA5..004B2F9B','calls':['004B2F37','004B2F83'],
   'scope':'original retained boundedcaller, never wholeeventfunction'},
  'retained178_automatic':{'actual9':'00475FEE','actual2':'00476074',
   'pushes':['actualreceived rawnameprefix','opaqueWORDFFFF','caller9 or2','actualgetterindex0 text'],
   'rawtext_accessor':'004B29B0 returns005B7698+51*actualindex',
   'scope':'local receive-driven autoreply flow not evidenceofserver permission/defaultmessage'},
  'unknown_caller_coverage':'other indirect/direct producers and UI permissions remainunclaimed; no fullcaller denominator'})
 emit('stack-ledger.json',{
  'address_domain':'VA=00400000+RVA; pinnedmapped imagefileoffset=RVA',
  '47DC20':'thisECX; noargs; actualrelatedowner settingsand12 globalprefixbytes changed; no executionhere',
  '47DC90':'thisECX; argatentryESP+4; returnsEAX actualDWORDtab==argument; ret4',
  '4B12B0':'thisECX; arg1 atentryESP+4 display operand, arg2+8 localmode; sub20 plus3push =>argsESP+30/+34; ret8',
  '4B29B0':'index atentryESP+4; pointer005B7698+51*index; ret4; nativehelperhasnobounds butcallerindex0 onlyqualified',
  '496990_retained178':'thisECX; args rawtext,callerchannel,opaqueWORD,rawtarget; ret10hex; bodyESP+24 writesWORDtotal/BYTEchannel/WORDarg; bodyESP+27 residueunwritten',
  '4B3271':'prepushlocals textESP+A4 targetESP+14; fourpushes16B thennative call ret16; no guessedlocalpermission',
  '475E00_retained178':'thisECX; args actualchannel/fulltext; ret8; wire0/8 and2/9 tablealiases explicit',
  '47DE00_retained178':'entryESP E; sub104 plus4 savedregisters givesE-114; bufferE-100..E exclusive256; selectedprefix3 thenwholetext thenNUL',
  'preservation':'actualrequest total/4rawheaderbytes/originaltext andactualserver5C opaqueheader remaincomplete'})
 emit('qualification-frontier.json',{
  'source_caller_needed':'existingtyped Party/Private/Guild records musteachdispatch toexactnewSource afterfullraw request reconstruction/retention',
  'source_no_permission_from':['low7channel','opaqueWORD','tabselection','rawtargetname','clientfilter','GM-like literalshape'],
  'must_require':['actualPlayerText/NamedWhisper issuer domain','exactoriginalsource fullrequest/rawtarget/bodyrange/codepage identity',
   'actualcurrentparty/guild/private recipient leases and actualpermission/rate decisions',
   'fulloriginalnative5C perrecipient header32bitactor/opaquebytes/low7channel/tag',
   'plain8channels wholetext252 inclactualprefix/suffix; allothersink domains OPEN',
   'actualrecipient loadedrenderer/current/resources/history/autoreply states',
   'actualcipher andoriginal mixedsenderwireorder/current callback qualification'],
  'prefix_scope':'actualinitializer setsESC A x; raworiginalimage1 A x keptseparate; prefix isclientinternal notnewserverwire',
  'frozen_sources':'grammar/codec/handlers/nativefonts unchanged byagent',
  'scope':'sourceintegration only; actor authority/audience/originalserver5C issuer stillactualownerobligations'})
 emit('gaps.json',{
  'loaded_full_destinations':'OPEN initialization/currentgraphics/layout ofallsinks; do notretry glyph/capacity/WindowsCharNext/codecchains',
  'original_server_chat':'OPEN server2F parser/5C issuer/fullopaque fields/party/guild/private permissions andactualaudience',
  'GM_named_identification':'OPEN ifonlyrawsame2F bytes given; explicitactualsource qualification mandatory',
  'control_otherchannels':'OPEN13style/board/system/battle/structured text andformatter branches, no plainprose fallback',
  'headerWORD':'actualcaller low16 not authoritative target/membership/GM identifier',
  'new_prefix_fact':'actual ESC initialization qualifies178rawprefixdescription; previousevidence retainedwithoutbaseline refresh',
  'new_callback_permission':'NONE inferred; exactclientgates are clientstate only',
  'phase':'source/static; no codecs/emulation/native/C++/Lua/API/DB/SQL/build/test/runtime',
  'accounting':'retained178 functions notnew; no newopcodes/fullroutes; percentageunknown'})
 emit('findings.json',{'round':'20261008-tw-native-chat-family-source','owned_sources':[OWNED],
  'game_CPP_modified':0,'new_complete_functions':4,'new_bounded_caller_spans':1,
  'retained178_spans':10,'all_spans':len(records),'all_raw_span_bytes':sum(r['bytes'] for r in records),
  'new_raw_span_bytes':sum(r['bytes'] for r in records if r['scope'].startswith('new_')),
  'native_sites':len(sites),'data_spans':len(data),'complete_actualoriginal_inputs':1,
  'source_before_originals':len(SOURCES),'derived_codecs_emulated_inputs':0,
  'keyactualfacts':['actual native12slot ESC-prefix initializer','fulllocaltab setter gates andpredicate linkedproducer',
   'additional actual private-targetUIcaller andautomatic rawtext accessor',
   'exactplain8wirechannel->scratchselector mapping and252domain',
   'fullrawtyped1/2,9/3 request/header plusGM/Named structuralambiguity'],
  'new_opcode_values':0,'complete_routes_added':0,'whole_game_percentage':None,
  'existing_inventory_not_recounted':{'C2S':156,'S2C':252,'variants':30},
  'no_tests_runtime_build_or_client_changes':True})
 emit('derived-inputs.json',{'codec_or_emulated_inputs':[],
  'source_relation_outputs':['plain-sink-families.json','local-tab-linkage.json','exact-request-fields.json'],
  'originalimage_and_sources_separate':True,'nativeexecution':False})
 sources('intermediate',[OWNED])
 print(json.dumps({'spans':len(records),'new_full':4,'new_bounded':1,'retained178':10,
  'all_span_bytes':sum(r['bytes'] for r in records),'new_span_bytes':sum(r['bytes'] for r in records if r['scope'].startswith('new_')),
  'sites':len(sites),'data':len(data),'before_sources':len(SOURCES),
  'tool_bytes':len((ROOT/OWNED).read_bytes()),'tool_sha256':digest((ROOT/OWNED).read_bytes())}))

def final():
 # Source stability accounting only, not behavior/testing. Root-owned mutable
 # adapter/source/contract sources and books/catalog never join this list.
 before=json.loads((OUT/'before-source-origins.json').read_text())
 for row in before:
  if digest(Path(row['path']).read_bytes())!=row['sha256']:
   raise RuntimeError('Actual stable current source changed; retain before, coordinate parent')
 rows=sources('current',SOURCES+[OWNED])
 emit('delivery.json',{'BATCHFINAL_received':True,'current_originals':len(rows),
  'owned_tools':[OWNED],'game_CPP_changes':0,'native_inputs_separate':True,
  'no_mutable_root_or_new_contract_CPP_current_pins':True,'new_opcodes':0,'complete_routes':0,'percentage':None})
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
