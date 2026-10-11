"""Pinned TW chat producer/consumer source qualification, static files only.

No codecs, emulation, native/C++/Lua, DB/API, browser, build, test or server run.
Only complete original preservation, byte accounting and bounded Capstone.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/tw-native-chat-record-source-01'
OUT=ROUND/'agents/tw-chat-frontier'
OWNED='tools/reconstruction/tw_native_chat_source178.py'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE='c13dab36dbf2e0b6db741e34cf0f2845e25e6646d51a4976c8426251c6df3318'
BASE=0x400000
SOURCES=[
 'src/protocol/RecoveredChat.h','src/cn/world/SharedNativeChat.h','src/cn/world/SharedNativeChat.cpp',
 'src/cn/protocol/CnChat.h','src/cn/protocol/CnChatConsumerContract.h',
 'src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp',
 'src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
 'src/text/ChineseText.h','src/text/ChineseText.cpp','src/protocol/RecoveredTaiwanServerRecords.h',
]
CONTEXT=[
 'AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'docs/research/private-locale-native-chat-20260923.md',
 'docs/research/town-chat-channel-20260924.md',
 'docs/research/server-chinese-conversion-20260923.md',
 'docs/research/cn-shared-native-chat-owner-20261007.md',
 'docs/research/chat-repair-and-freeze-20260927.md',
]
SPANS=[
 (0x968E0,0x9698C,'complete known special $gmsoft01 formatter; newly corrected literal/header relation','retained_special_producer'),
 (0x96990,0x96F7C,'complete ordinary/channel producer with native prefix/selector/throttle/target branches','expanded_known_producer'),
 (0x132E0,0x13368,'complete known queue appender: opcode then original body bytes','retained_transport'),
 (0x13370,0x133D7,'complete known queue flush helper, not chat audience producer','retained_transport'),
 (0x6AE96,0x6B022,'complete known world5C case; bounded shared dispatcher branch','expanded_known_consumer'),
 (0xFB690,0xFB8DB,'complete known peer bubble path, board rewrite/name/lookup/renderer branches','expanded_known_bubble'),
 (0xFC960,0xFC98A,'complete known128-slot DWORD actor lookup','retained_actor_lookup'),
 (0x10A090,0x10A3B1,'complete known bubble render consumer with real handles/destinations','expanded_known_renderer'),
 (0x75E00,0x7652A,'complete known channel panel function expanded to all native formatter cases','expanded_known_panel'),
 (0x7DE00,0x7E0AD,'complete assembled256-byte panel destination and prefix/filter/layout branches','new_complete_sink'),
 (0x7E0F0,0x7E1C2,'complete panel color/control analyzer','new_complete_sink'),
 (0x7DD60,0x7DDBE,'complete legacy-byte-aware name-prefix splitter','new_complete_sink'),
 (0x7DDC0,0x7DDFD,'complete received whisper-history name consumer','new_complete_sink'),
 (0xC7610,0xC766D,'complete known local channel visibility preference selector','retained_local_filter'),
 (0x12F500,0x12F54C,'complete known conversion router, codec callees not executed/recovered here','retained_conversion_router'),
 (0x131C10,0x131C2D,'complete known language tag selector from actual WORD globals','retained_language_selector'),
 (0x19220,0x192F6,'complete line extraction with actual loaded owner/count/capacity and NUL','new_complete_sink'),
 (0x10F580,0x10F644,'complete loaded bubble line feed and graphic handle publication','new_complete_sink'),
 (0x18EB0,0x19086,'complete original text feed/control/line state consumer','new_complete_sink'),
 (0x19120,0x19191,'complete loaded line clearing with current capacity array','new_complete_sink'),
 (0x19A20,0x19AC9,'complete original byte feed/legacy pair/control byte handling','new_complete_sink'),
 (0x19E50,0x1A08E,'complete original text insertion/current line update','new_complete_sink'),
 (0x19C90,0x19E4B,'complete actual loaded capacity preflight/reflow/copy','new_complete_sink'),
 (0x19C50,0x19C83,'complete next-token control/Windows character boundary adapter','new_complete_sink'),
 (0xB2EA5,0xB2F9B,'bounded real ordinary UI branches and two actual channel0/default caller sites','new_bounded_caller'),
 (0x1318,0x131E,'known169 variable logical length leaf -2 for5C','retained169_length_leaf'),
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
 if digest(raw)!=PIN or digest(before)!=BEFORE or len(json.loads(before))!=1277:
  raise RuntimeError('Pinned actual original/fresh before mismatch; do not reset baseline')
 OUT.mkdir(parents=True,exist_ok=True)
 put(OUT/'root-before.raw',before)
 emit('root-lineage.json',{'before_inputs':1277,'before_sha256':BEFORE,
  'prior177_members_retained':2231,'prior_verification':'parent fresh whole-member receipt',
  'no_historical_baseline_refresh':True})
 sources('before',SOURCES)
 emit('new-file-before.json',[{'path':(ROOT/OWNED).as_posix(),'state':'absent in root fresh before','copy':None}])
 emit('original-inputs.json',[original(IMAGE,'input/native.bin')])
 emit('context-originals.json',[original(ROOT/name,f'context/c{n:02d}{Path(name).suffix}') for n,name in enumerate(CONTEXT)])
 decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 records=[];instructions={}
 for n,(start,end,purpose,scope) in enumerate(SPANS):
  body=raw[start:end];copy=f'raw/n{n:02d}.bin';put(OUT/copy,body)
  rows=[]
  for i in decoder.disasm(body,BASE+start):
   row={'va':f'{i.address:08X}','rva':f'{i.address-BASE:08X}',
    'bytes_hex':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}
   rows.append(row);instructions[i.address-BASE]=row
  records.append({'start_va':f'{BASE+start:08X}','end_exclusive_va':f'{BASE+end:08X}',
   'start_rva':f'{start:08X}','end_exclusive_rva':f'{end:08X}',
   'copy':copy,'bytes':len(body),'sha256':digest(body),'purpose':purpose,'scope':scope,'instructions':rows})
 emit('native-spans.json',records)
 sites=[
  (0x968F6,'actual sprintf literal is $gmsoft01 %s; not ordinary common text'),
  (0x96917,'reject empty formatted string'),(0x9691A,'actual strlen+NUL<=255 so formatted bytes<=254'),
  (0x96929,'special producer keeps only oldheader bits82'),
  (0x96931,'special producer forces low7 channel2'),
  (0x96959,'special opaqueWORDFFFF; header byte4 and old tag remain stack provenance'),
  (0x96960,'body count=formattedstrlen+7; queued opcode adds1'),
  (0x9697A,'actual special2F queue appender call'),
  (0x96A10,'optional raw target argument is copied separately'),
  (0x96A6D,'actual ASCII prefix selector table, not inferred server permissions'),
  (0x96A88,'! prefix local related owner DWORD3F98 gate'),
  (0x96AA4,'# prefix local related owner BYTE6 gate'),
  (0x96AD4,'$ prefix locates actual first raw space for target/body'),
  (0x96B1E,'named body skips repeated raw ASCII spaces'),
  (0x96B68,'/board prefix special channel selection'),
  (0x96BB9,'unprefixed local tab selection uses actual owner'),
  (0x96BE7,'actual local channel-choice0..4 table'),
  (0x96C46,'actual selected channel0/1/2/3/13 producer cases'),
  (0x96C57,'channel13 style source sign-extends actual BYTE85ABC'),
  (0x96CBA,'actual named-whisper $%s %s formatter'),
  (0x96CFB,'caller channel9 override path is separate variant'),
  (0x96D5B,'ordinary send rejects empty prepared text'),
  (0x96D62,'ordinary prepared bytes+NUL<=255'),
  (0x96D79,'body totalWORD includes queued opcode'),
  (0x96D85,'channel low7 replaced preserving oldtag until actual locale helper'),
  (0x96D9B,'opaqueWORD low16 from actual caller or channel13 style; not playerID'),
  (0x96DA0,'actual locale selector supplies ordinary producer language bit'),
  (0x96DBA,'ordinary tag bit7 plus actual selected low7 channel'),
  (0x96DF0,'client repeat-state offset actualchannel*132'),
  (0x96E28,'client repeated-message count increments'),
  (0x96E5B,'client count>=3 throttle'),
  (0x96E64,'caller channel9 bypasses client repeat suppression; no inferred server-rate rule'),
  (0x96EF8,'unresolved leading $ rewrite uses actual channel2, not ordinary text'),
  (0x96F24,'ordinary/channel2F queue producer call'),
  (0x132F4,'existing queuedlogical plusbody+opcode cap0xA00'),
  (0x13320,'queue appender writes exact opcodeBYTE'),
  (0x13338,'queue appender copies full supplied body untouched'),
  (0x1334C,'queued bytecount actualmutation, no original server audience'),
  (0x6AE96,'full5C text starts13; precedingheader opaque except observed consumers'),
  (0x6AE9E,'actual channel/tagBYTE9'),
  (0x6AEAB,'native conversion selection applies low7channel<=9 only'),
  (0x6AEB8,'compare actual tag to native locale; bit is not trusted codepage authority'),
  (0x6AEC6,'conversion router writes into actual caller local temporary'),
  (0x6AEDE,'channel0 local bubble path'),(0x6AEE0,'channel6 local bubble path'),
  (0x6AEE4,'channel12 separate timestamp/display consumer'),
  (0x6AF03,'special : $ control substring probe'),
  (0x6AF33,'special : /board control substring probe'),
  (0x6AF43,'full senderactorDWORD5 for local identity branch'),
  (0x6AF4E,'compare full actual local world actor identity'),
  (0x6AFB5,'actual local renderer handleWORD supplies bubble target'),
  (0x6AFF2,'full original peer actorDWORD5 passed to real lookup path'),
  (0x6AFFD,'peer bubble4FB690'),
  (0x6B018,'low7 channel and full supplied text to475E00 panel'),
  (0xFB6AA,'real peer actor lookup4FC960'),
  (0xFB6AF,'missing native actor returns before bubble'),
  (0xFB6D6,'actor record stride0x268'),
  (0xFB6DF,'actual peername atrecord+1C used by board/control processing'),
  (0xFB86E,'board-prefix-specific probe is not ordinary name-prefix requirement'),
  (0xFB8A9,'real peer renderer handleWORD from record+60'),
  (0xFB8B2,'publish actual text into renderer50A090'),
  (0xFC974,'complete DWORD identity match at record+18'),
  (0xFC97B,'actual table128 entries; no commonID truncation'),
  (0x10A0A2,'actual renderer handle must be<4096'),
  (0x10A0CB,'actual renderer model state+24 must be valid'),
  (0x10A0D9,'actual graphics handle/state+A4 must be valid'),
  (0x10A0E1,'bubble local plainwork area1024 bytes'),
  (0x10A1FC,'actual loaded line owner50F580'),
  (0x10A214,'bubble line extractor supplied copy capacity256; NUL is separate'),
  (0x75E1C,'actual legacy-byte prefix splitter before panelchannel routing'),
  (0x75E2B,'channel>16 default returns; not generic native audience'),
  (0x75E31,'actual full17-entry panel case table'),
  (0x75E9A,'ordinarychannel0 local visibility preference check'),
  (0x76518,'panel path calls actual destination47DE00'),
  (0x7DE53,'assembled panelbuffer firstbyte'),
  (0x7DE73,'63DWORD thenWORD+BYTE fills total256-byte localbuffer'),
  (0x7DEF6,'channel-specific prefix onlywhen<12'),
  (0x7DF00,'actual3-byte prefix table1Ax strings'),
  (0x7DF4F,'append complete rawtext without native length guard'),
  (0x7DF67,'color/control analyzer seesassembledprefix and rawtext'),
  (0x7DF8A,'actual archive/layout path consumes assembledtext'),
  (0x7DFB9,'actual serverbound archive/control route, not S2C5C producer'),
  (0x7DD70,'prefix scanner treats negative leadBYTE as legacy pair; not Unicode rewrite'),
  (0x7DD7E,'name separator ASCII colon-space'),
  (0x7DDB0,'prefix destinationNUL aftercopy; unknown name capacity cannot be guessed'),
  (0xC7627,'ordinarypanel actual loadedsettingsBYTE449C'),
  (0xC762D,'common local filterbit4'),
  (0x131C10,'native language WORD primary4'),
  (0x131C1A,'native language WORD secondary2'),
  (0x12F51D,'conversion route tag/locales case1->0'),
  (0x12F539,'conversion route tag/locales case0->1'),
  (0x19236,'line extractor actual loadedline count+148'),
  (0x19248,'line bufferactual+564+line*0x101'),
  (0x1926F,'copy min(actualstrlen,actualsuppliedcopycapacity)'),
  (0x19285,'separate NUL atdest+copied count; budgetnottransport'),
  (0x10F59B,'actual loaded text feed418EB0'),
  (0x10F5A0,'actual graphics state+A614 boundedhandle'),
  (0x10F5D7,'perline extraction into actual256B local destination'),
  (0x18EB9,'actual loaded linecapacity clearing beforefeed'),
  (0x1903C,'originalbyte appender419A20, not customUnicode insertion'),
  (0x1913E,'loaded perline capacity arrayowner+8+4*line'),
  (0x19151,'actual line stride0x101'),
  (0x19A53,'native byte/pair feeder419E50'),
  (0x19A84,'native percent special replacement bytes, not plainsemanticidentity'),
  (0x19F8F,'actual loaded capacity preflight419C90'),
  (0x19F94,'failed capacity check doesnotadmit text'),
  (0x19CD4,'actual loaded currentline capacity comparison'),
  (0x19CDC,'actual loaded maxlines count+148'),
  (0x19D20,'loaded capacity exhausted returnsAL0'),
  (0x19DDA,'copy checked linebytes to actual loaded line buffer'),
  (0x19C54,'native ESC controltoken handling'),
  (0x19C7A,'native character-next import; loadedCP/locale stillneeded'),
  (0xB2F2F,'actual UI optionaltarget, opaqueWORD0, channel0, preparedtext arguments'),
  (0xB2F37,'actual ordinary producercaller with target argument'),
  (0xB2F76,'ordinary UI caller hasnulltarget/channel0/opaqueWORD0'),
  (0xB2F83,'actual ordinary producercaller, notspecial4968E0'),
  (0x1318,'known5C totalWORD variable length leaf'),
 ]
 emit('native-sites.json',[{'va':f'{BASE+a:08X}','rva':f'{a:08X}',
  'instruction':instructions[a],'fact':fact,
  'scope':next(scope for start,end,_,scope in SPANS if start<=a<end)} for a,fact in sites])
 data=[]
 for n,(start,length,role) in enumerate([
  (0x190168,13,'exact special formatter $gmsoft01 %s includingNUL'),
  (0x190198,8,'actual named-whisper local presentation [%s] %s'),
  (0x1901A0,8,'actual named-whisper wireformatter $%s %s'),
  (0x1901A8,7,'actual /board literal'),(0x1901B0,8,'actual /board-space literal'),
  (0x18CBF4,4,'actual : $ marker'),(0x18CBE8,10,'actual : /board marker'),
  (0x1823C8,2,'actual ASCII space delimiter'),
  (0x18EBE8,48,'complete12 channel-prefix slots, each3B+NUL'),
  (0x96F7C,20,'complete5 prefix branch VA cells'),(0x96F90,94,'complete94 prefix byte selector cells'),
  (0x96FF0,20,'complete5 localchannel selector VA cells'),
  (0x97004,24,'complete6 actual channelproducer branch VA cells'),
  (0x9701C,14,'complete14 actual channelproducer selector bytes'),
  (0x7652C,68,'complete17 channelpanel target VA cells'),
  (0x7E0B0,56,'complete14 destination preference-case VA cells'),
  (0xC7670,16,'complete4 localvisibility preference-case VA cells'),
  (0x1324+0x5C*4,4,'known1695C logical length resolver pointer'),
 ]):
  body=raw[start:start+length];copy=f'raw/d{n:02d}.bin';put(OUT/copy,body)
  data.append({'va':f'{BASE+start:08X}','rva':f'{start:08X}','copy':copy,
   'bytes':len(body),'sha256':digest(body),'raw_hex':body.hex(),'purpose':role})
 emit('native-data.json',data)
 emit('stack-ledger.json',{
  'address_domain':'VA=00400000+RVA; originalimage fileoffset=RVA',
  '4968E0_special':{'entryESP':'E','arg1':'actual raw input string',
   'formatted_temp':'E-100 from actual $gmsoft01 %s',
   'body_start':'E-208, queued opcode addslogical offset1',
   'actual_stores':{'logical1/2':'formattedstrlen+8 WORD','logical3':'(oldBYTE&82)|2',
    'logical4':'unwritten stack residue','logical5/6':'FFFF','logical7':'full formattedtext includingNUL'},
   'queue_pushes':['bodylen=formattedstrlen+7','bodyptrE-208','opcode2F'],
   'ret_bytes':4,'ordinary_common_source':False},
  '496990_ordinary_channel':{'entryESP':'E','arguments':['+4 rawtext','+8 callerchannel','+C opaquecallerWORD','+10 rawtarget pointer'],
   'body_start':'after prologue ESP+24','body_stores':['WORD0 totalpreparedstrlen+8',
    'BYTE2 selectedchannel low7 plus actual531C10tagbit7','BYTE3 unwritten stack residue',
    'WORD4 low16 callerarg3 or actualchannel13 style','text6 andNUL'],
   'ret_bytes':16,'client_throttle':'repeatcount>=3 suppressed unless actualcallerchannel9; not server rate'},
  '4132E0':{'arguments':['opcodeBYTE','actualbodypointer','actualbodysize'],
   'output':'opcode thenalloriginalbodybytes; appender createsneitherchatlengthnorheader','ret_bytes':12},
  'world5C':{'recordbase':'EBX','rawtext':'EBX+13','nativeactor':'DWORD EBX+5',
   'channel':'BYTE EBX+9 &7F','tag':'BYTE EBX+9>>7',
   'unknownheader':['bytes3/4','bytes10/11/12'],
   'localactor':'actualworld+1539683C DWORD','localrenderer':'actualworld+1539AD80 WORD',
   'bubblechannels':[0,6],'timestampchannel':12},
  '47DE00_plain_local':{'entryESP':'E','frame':'sub104 +four saved registers ->currentESP=E-114',
   'bufferbegin':'currentESP+14=E-100','bufferend_exclusive':'E',
   'clear':'firstBYTE +63DWORD +WORD +BYTE =256 bytes',
   'prefix_source':'58EBE8+channel*4,3bytes+NUL forchannel<12',
   'ordinary_max_fulltext':252,'derivation':'3 prefix+252fulltext+1NUL=256',
   'body_budget':'252 -actualbodyprefix.size -actualbodysuffix.size, not justinputlimit254'},
  '4FC960':{'table_entries':128,'record_stride':0x268,'actor_field':0x18,
   'identity_width':'DWORD untruncated','return':'signedWORDindex orFFFF'},
  '4FB690':{'actual_name_field':0x1C,'actual_renderer_field':0x60,
   'ordinary_nameprefix_requirement':False,
   'note':'board-specific transformation usesactualname; ordinarynonboard fulltext reaches renderer'},
  'loaded_text_owner':{'maxlines_count_offset':'148','linecapacity_array':'8+4*line',
   'line_bytes':'564+101*line','currentline':'158','currentbyteposition':'154',
   'actualgraphicshandle':'A614','actualgraphicsowner':'A618',
   'preflight':'419C90 returnsAL0 ifrealcapacity/linecount exhausted',
   'extract':'419220 min(strlen,suppliedcopycap) then separateNUL; no fabricatedloadedcapacity'},
 })
 emit('qualification-frontier.json',{
  'preserved_frozen_sources':'RecoveredChat.h/CN SharedNativeChat and existingtextconversion unchanged',
  'new_adapter_must_require':['actual ownedTWSession/readyLease/common deliveryidentity',
   'allfouroriginal2F header bytes and exactrawtext retained',
   'explicit recovered PlayerText orNamedWhisper form, not defaultcommon',
   'raw targetidentity neverconverted; actual sourcecodepage/identity independent ofclaimedtag',
   'actual sourceauthority determines permissions/mute/rate/recipientleases',
   'eachrecipient supplieswholeoriginal5C withactual32bitactorandallopaqueheader bytes',
   'actualbodyrange plus originalUTF8bodyprovenance; names/controlprefix/suffixunchanged',
   'separate252Bwholetext paneldomain for0/1/2/3/5/6/8/9 plain branches, loadedrecipientdestination qual stillmandatory',
   'currentactor visibility/real preceding6F andrenderhandle qualification forordinarypeerbubble',
   'immutable audience/source/resource/publication revisions checked before/aftercallbacks',
   'sender encryptedresponse appended in original mixedaccumulator order; actualotherfanoutowner not guessed'],
  'ordinary_source_tables':{'prefixes':{'!':'localgate->channel1','#':'localgate->channel3','$':'NamedWhisperchannel2','~':'channel0'},
   'localtab_choices':{'0':'channel0','1':'channel1','2':'channel3','3':'retains unresolved FF branch','4':'channel13style'},
   'callerchannel9':'separate NamedWhisper override',
   'board':'/board exact/prefix overrideschannel0, separatecontrolflow'},
  'must_not_infer':['$gmsoft01 asordinarycommon','channel/tag aspermission orauthoritativecodepage',
   'opaqueWORD ascommonplayerID','nativeactorDWORD fromtruncatedcommoncharacterID',
   'same-map broadcast fromclientdisplay','genericzeroheader fromconsumer',
   'producer254 asallconsumercapacity','clientrepeatcount asservermuterate',
   'Native5C headerissuer/audience fromclientbubble success','clientlocalpreview asserverreply'],
  'named_prefix_scope':'optional source-qualified name: body domain is narrower provenance, not a mandatory ordinary bubble consumer format',
  'native_phase_scope':'worldordinarycases only; battle/board/structured/otherchannel variants remainseparate',
  'S2C_server_producer':'OPEN; client suppliesconsumer not original fullserver5C issuance',
  'no_CPP_edits':True,
 })
 emit('gaps.json',{
  'native_server_5C_issuer':'OPEN full actor/header/unknownbytes/audience/permissions/rate/source revision, not client-consumer-derived',
  'loaded_destination_current':'OPEN actual currentrecipienttext capacities/lineinstances/graphic resources/layout lifecycle; fixed252 domainalone isnotallSinkproof',
  'new_recovered_source_limit':'independent actualTW47DE00 scratch256 prefix3 wholetext252, neverrewritefrozen254serializer',
  'special_producer_correction':'historical4968E0 common label incomplete; actualliteral $gmsoft01 %s andchannel2 retainedseparately, frozencommentnotedited',
  'encoding_helper_callees':'52F170/52F330 codec internals andWindows character-next loadedcodepage notfullyrecovered/executed here',
  'formatter_controls':'board/namedcontrol/structured/system/timestamp/global/battle variants needactualstate/formatter/authority',
  'input_C2S_consumer':'originalserverconsumer not supplied; strictshape/sourcequalification doesnotrecoverpermissions',
  'phase':'source/static only, no codecs/API/DB/build/test/native/C++/Lua/server/browser/deploy',
  'accounting':'existingC2S156/S2C252 and30 inventoryvariants not re-counted; newopcodes0/fullroutes0/percentage null'})
 emit('findings.json',{'round':'20261008-tw-native-chat-record-source','owned_sources':[OWNED],
  'game_CPP_modified':0,'new_complete_sink_functions':12,'new_bounded_caller_spans':1,
  'expanded_known_spans':5,'retained_context_spans':8,'all_spans':len(records),
  'native_sites':len(sites),'data_spans':len(data),'all_raw_span_bytes':sum(r['bytes'] for r in records),
  'complete_actualoriginal_inputs':1,'full_nativeimage_bytes':len(raw),
  'source_before_originals':len(SOURCES),'derived_codecs_emulated_inputs':0,
  'keyactualfacts':['special4968E0 $gmsoft01 andchannel2, not common0',
   'ordinary496990 fullchannels/header4/native tag/repeat/local gates',
   'world5Cfullactor32/low7channel/tag/text13 withotherheaderunknown',
   '0/6bubble exactreal128slot actorlookup,actualrenderer notcommonID',
   'TWpanel256B minus3Bprefix minusNUL ->252Bwholetext',
   'actualloadedowner linecount/capacity array andgraphic instances must qualify'],
  'new_opcode_values':0,'complete_routes_added':0,'whole_game_percentage':None,
  'existing_inventory_not_recounted':{'C2S':156,'S2C':252,'variants':30},
  'no_tests_runtime_build_or_client_changes':True})
 emit('derived-inputs.json',{'decoded_codec_emulated_files':[],
  'derived_outputs':['native-spans.json','native-sites.json','stack-ledger.json','qualification-frontier.json'],
  'all_actual_originals_separate':True})
 sources('intermediate',[OWNED])
 print(json.dumps({'spans':len(records),'sites':len(sites),'data':len(data),'before_sources':len(SOURCES),
  'tool_bytes':len((ROOT/OWNED).read_bytes()),'tool_sha256':digest((ROOT/OWNED).read_bytes())}))

def final():
 rows=sources('current',SOURCES+[OWNED])
 emit('delivery.json',{'BATCHFINAL_received':True,'current_originals':len(rows),
  'owned_tools':[OWNED],'game_CPP_changes':0,'native_inputs_separate':True,
  'no_mutable_root_or_peer_new_CPP_current_pins':True,'new_opcodes':0,'complete_routes':0,'percentage':None})
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
