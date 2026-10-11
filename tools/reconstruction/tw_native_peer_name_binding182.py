"""TW native peer-name publication qualification, static original files only.

Bounded actual receive paths are not an original server6F producer, permissions,
common64 ID namespace or native player-class proof. No runtime/codecs/tests.
"""
from pathlib import Path
import argparse
import hashlib
import json
import capstone

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/native-published-chat-identity-source-01'
OUT=ROUND/'agents/tw-peer-name-binding-frontier'
OWNED='tools/reconstruction/tw_native_peer_name_binding182.py'
IMAGE=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BEFORE='7468461b1c1d42d636de67dd909fb2ac0c666180cd398f4cb9269f37af7640a7'
BASE=0x400000
SOURCES=[
 'src/game/SharedChatIdentitySource.h','src/game/SharedChatIdentitySource.cpp',
 'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
 'src/protocol/RecoveredRemoteActor.h','src/protocol/RecoveredPlayerAppearanceUpdate.h',
 'src/text/OwnedCharacterNameText.h','src/text/OwnedCharacterNameText.cpp',
 'src/game/RecoveredCharacter.h','src/db/RecoveredCharacterRepository.h',
 'src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
]
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md',
 'tools/reconstruction/tw_native_whisper_identity181.py']
# New byte intervals are outside181 spans. This is qualified caller behavior,
# not a recovered server producer or a new opcode. Known field projections are
# expanded retained context rather than newly discovered gameplay semantics.
SPANS=[
 (0x695C8,0x69767,'new_bounded','6F actual pre-store text-state branch and in-place three-field adaptation; not complete6F case'),
 (0x131C10,0x131C2D,'new_complete','actual two-globalWORD selector returns1 only for4/2; loaded source/current remains OPEN'),
 (0xFB460,0xFB4E5,'new_complete','actual peer publication replace-by-low12-ID caller then complete known6F store'),
 (0xFC62E,0xFC654,'new_bounded','cleanup actual conditionalID sentinel and name firstBYTE clear; unrelated resource callees not followed'),
 (0xFC33F,0xFC3BE,'expanded_known_field_projection','packed native selectors/rawbytes -> actor fields; no ordinary-player authority proved'),
 (0x699FD,0x69A28,'new_bounded','actual world6F normal resource-qualified call into peer publication wrapper; not whole enclosingcase'),
 (0xFC1C0,0xFC2C3,'retained181','known native table128slots/stride268hex and EBPbase18, prior fullraw preserved'),
 (0xFC2C3,0xFC33F,'retained181_clean_copy_boundary','known raw body1C/2C/3C strings to peer1C/2C/3C; post-adaptation body only'),
 (0xFC960,0xFC98A,'retained178_181','actual peer lookup compares fullDWORD nativeID, notcommon64'),
 (0xFAC70,0xFAD19,'retained181','complete actual peer getter, no new recovery/count'),
 (0x66E8A,0x66EC9,'retained181','actual nativepeer firstname -> private selector caller'),
 (0x7DCF0,0x7DD40,'retained181','complete actual private target selection; no new recovery/count'),
]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def emit(name,value):put(OUT/name,(json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode())
def original(path,target):
 raw=path.read_bytes();put(OUT/target,raw)
 return {'path':path.resolve().as_posix(),'copy':target,'bytes':len(raw),'sha256':sha(raw)}

def recover():
 raw=IMAGE.read_bytes();fresh=(ROUND/'before-manifest.json').read_bytes();manifest=json.loads(fresh)
 if sha(raw)!=PIN or sha(fresh)!=BEFORE or len(manifest)!=1300:
  raise RuntimeError('Pinned actual original/fresh before mismatch; never replace baseline')
 OUT.mkdir(parents=True,exist_ok=True);put(OUT/'epoch/root-before.raw',fresh)
 emit('epoch.json',{'freshbefore_count':1300,'freshbefore_sha256':BEFORE,'prior181_members_retained':2318,
  'prior_scope':'parent whole-member preservation','baseline_replaced':False,'client_live_state_observed':False})
 lookup={row['path']:row for row in manifest};before=[]
 for n,name in enumerate(SOURCES):
  row=lookup[name];body=(ROUND/row['snapshot']).read_bytes()
  if sha(body)!=row['sha256']:raise RuntimeError('Preserved full original before changed')
  target=f'before/s{n:02d}{Path(name).suffix}';put(OUT/target,body)
  before.append({'path':(ROOT/name).as_posix(),'copy':target,'bytes':len(body),'sha256':sha(body)})
 emit('before-source-origins.json',before)
 emit('new-file-before.json',[{'path':(ROOT/OWNED).as_posix(),'copy':None,'state':'absent in root freshbefore'}])
 emit('original-inputs.json',[original(IMAGE,'inputs/native.bin')])
 emit('context-originals.json',[original(ROOT/name,f'context/c{n:02d}{Path(name).suffix}') for n,name in enumerate(CONTEXT)])
 emit('intermediate-source-origins.json',[original(ROOT/OWNED,'intermediate/writer-01.py')])
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);spans=[];instructions={}
 for n,(a,z,scope,purpose) in enumerate(SPANS):
  body=raw[a:z];target=f'raw/n{n:02d}.bin';put(OUT/target,body);rows=[]
  for i in cs.disasm(body,BASE+a):
   row={'va':f'{i.address:08X}','rva':f'{i.address-BASE:08X}','bytes_hex':i.bytes.hex(),
    'mnemonic':i.mnemonic,'operands':i.op_str};rows.append(row);instructions[i.address-BASE]=row
  spans.append({'start_va':f'{BASE+a:08X}','end_exclusive_va':f'{BASE+z:08X}',
   'start_rva':f'{a:08X}','end_exclusive_rva':f'{z:08X}','scope':scope,'purpose':purpose,
   'copy':target,'bytes':len(body),'sha256':sha(body),'instructions':rows})
 emit('native-spans.json',spans)
 targets=[
 (0x695CB,'logical opcode skipped once; EBX now actual6F body'),
 (0x695E3,'known native low12 actor handle used in pre-store scene callback'),
 (0x695F6,'read actual globaltext state through531C10'),
 (0x695FB,'actual6F packed firstDWORD after opcode'),
 (0x695FF,'extract actual bit25'),(0x69602,'bit25 constrained to0/1'),
 (0x69605,'compare wire bit25 to actual global selector result'),
 (0x69607,'same state skips all text transformation to469767'),
 (0x6960D,'different state branch tests actualwire bit25'),
 (0x69619,'bit25=1 and globalstate0 qualifies first conversion branch'),
 (0x69628,'firstname actual body+1C/logical29 source'),
 (0x6962D,'callee52F330 static target only, no codec execution/algorithm claim'),
 (0x69637,'firstconversion false skips in-place conversions'),
 (0x69656,'conversion result overwrites actual first body text'),
 (0x69665,'second conversion local output after firstcdeclcleanup'),
 (0x6966E,'second actualtext helper call'),(0x6968C,'overwrite secondactual text body+2C'),
 (0x696A4,'thirdactualtext helper call'),
 (0x696AE,'bit25=0 requires globalstate1 for inverse branch'),
 (0x696BE,'inverse conversion first raw body1C'),
 (0x696C3,'inverse helper52F170 static target only'),
 (0x696CD,'inverse firsthelper false skips in-place conversion'),
 (0x696EC,'inverse result firsttext copied to actualbody'),
 (0x69704,'inverse secondactualtext helper'),(0x69722,'inverse secondtext body2C overwrite'),
 (0x6973A,'inverse thirdactualtext helper'),
 (0x6974B,'twooutstanding cdeclcalls release16bytes beforethirdresult copy'),
 (0x69758,'third result overwrites actualbody3C in both branches'),
 (0x131C10,'globalWORD59DFD8 mustequal4'),(0x131C1A,'globalWORD59DFDA mustequal2'),
 (0x131C24,'exact global4/2 returns1'),(0x131C2A,'otherstates return0'),
 (0xFB462,'actual bodyargument original pointer'),(0xFB46A,'mask nativepackedID low12 only'),
 (0xFB470,'lookup old sameID native record'),(0xFB478,'missingrecord skipscleanup'),
 (0xFB488,'actual oldpeer recordbase+18 pointer'),
 (0xFB48D,'cleanup oldsameID before newstore; no reusablecommon64generation'),
 (0xFB49A,'known6F store invoked aftercleanup'),
 (0xFB4A2,'failed insertion rejects subsequent localupdates'),
 (0xFC631,'cleanup loads actualownermode+13418'),
 (0xFC637,'only mode1 invalidates storednativeID'),
 (0xFC63C,'cleanup sets DWORDID sentinelFFFFFFFF'),
 (0xFC64A,'cleanup clears firstnameBYTE at ESI+4 (absolutepeer+1C)'),
 (0xFC35C,'knownpacked high3bit selector branch, not playerownership'),
 (0xFC367,'knownnonzero selector subtracts1: packed0/1 both map0'),
 (0xFC36C,'store projectedselector WORD EBP+3A'),
 (0xFC39C,'knownnative bits12..13 projection'),
 (0xFC3A2,'store projected2bit BYTE EBP+260'),
 (0xFC3A8,'knownfull body+4E rawappearancebyte'),
 (0xFC3B1,'knownfull body+4F rawappearancebyte'),
 (0x69A16,'actual postadaptation6F body suppliedto publication'),
 (0x69A1E,'actual6F call full4FB460 wrapper afterresourcepath qualification'),
 (0xFC1CA,'retained tablebase18 startingnativeID record'),
 (0xFC1D8,'retained slot stride268hex=616decimal'),
 (0xFC2C8,'retained store packed low12 nativeID'),
 (0xFC2D0,'retained nativeID low12 assigned fullDWORD record'),
 (0xFC2C5,'retained nativebody firsttext+1C afteradaptation'),
 (0xFC2DA,'retained destination EBP+4=actor firsttext+1C'),
 (0xFC33D,'retained thirdrawtext finalbytecopy, nextinstruction beginsFC33F'),
 (0xFAC89,'retained peer getter fullDWORD lookup'),
 (0xFACA8,'retained exact postadaptation firstpeername+1C'),
 (0x66EC4,'retained actual nativepeername -> private target helper'),
 ]
 sites=[]
 for a,meaning in targets:
  if a not in instructions:raise RuntimeError(f'Actual native instruction boundary not captured {a:X}')
  sites.append(dict(instructions[a],meaning=meaning))
 emit('instruction-sites.json',sites)
 state=raw[0x19DFD8:0x19DFDC];put(OUT/'raw/d00.bin',state)
 emit('data-sites.json',[{'va':'0059DFD8','rva':'0019DFD8','copy':'raw/d00.bin',
  'bytes':len(state),'sha256':sha(state),'raw_hex':state.hex(),
  'scope':'original imagebytes only; not loaded/live selector or initialization proof'}])
 source_sites=[]
 needles={
 'src/game/SharedWorldPresence.h':['generation','actor_handle','ready_characters','DB character'],
 'src/game/SharedWorldPresence.cpp':['generation_','list_for_account','same_character_root','registry','lease','active'],
 'src/game/SharedChatIdentitySource.h':['no permission','Raw target','current','Common ready'],
 'src/game/SharedChatIdentitySource.cpp':['strict_names','from_encoded','original_utf8','same_population','same_root','identity_'],
 'src/protocol/RecoveredRemoteActor.h':['identity()','runtime_emission_enabled','29u','with_identity','with_text_fields','15','transform_key'],
 'src/protocol/RecoveredPlayerAppearanceUpdate.h':['Wire projection','transform','actor_identity'],
 'src/text/OwnedCharacterNameText.cpp':['14','from_encoded','from_utf8','round','encode('],
 'src/game/RecoveredCharacter.h':['uint64_t','profile','name_codepage'],
 'src/text/LegacyChineseCodec.cpp':['encode_display','substituted','truncated','encoded="?"']}
 for name in SOURCES:
  for number,line in enumerate((ROOT/name).read_text(encoding='utf-8-sig').splitlines(),1):
   if any(word in line for word in needles.get(name,[])):
    source_sites.append({'path':name,'line':number,'text':line})
 emit('source-sites.json',source_sites)
 counts={'spans':len(spans),'span_bytes':sum(row['bytes'] for row in spans),
  'new_complete':sum(row['scope']=='new_complete' for row in spans),
  'new_bounded':sum(row['scope']=='new_bounded' for row in spans),
  'new_bytes':sum(row['bytes'] for row in spans if row['scope'].startswith('new')),
  'expanded_known':sum(row['scope'].startswith('expanded') for row in spans),
  'retained':sum(row['scope'].startswith('retained') for row in spans),
  'instruction_sites':len(sites),'data_sites':1,'source_sites':len(source_sites),
  'native_originals':1,'stable_source_files':len(SOURCES),'new_CPP':0,'new_opcodes':0}
 facts={
  'counts':counts,'qualification_change':'native firstpeername is copied from postadaptation6F body; rawwire logical29 equality is qualified, never unconditional',
  'native_address_domain':'mappedimageoffset==RVA;VA=00400000+RVA',
  'namespace':{'stored_actorID':'fullDWORD peer+18 receives low12 actual6F packedID',
   'lookup':'fullDWORD comparison does not imply common64 identity; distinct native12bitnamespace',
   'first_rawtext':'body+1C/logical29 -> peer+1C after actualworldtext adaptation',
   'stride':'0x268=616decimal, 128slots','common_ID':'fulluint64 actualrepository/session lease, never maskcast',
   'firsttext_field_capacity':16,'native_private_getter_bytes':15,'common_strict_encoded_bytes':14,
   'history_slot_bytes':72,'history_max_strlen':71},
  'no_adaptation_domain':{'instruction':'469607 jumps469767 iff wirefirstDWORD bit25 ==531C10 actualreturn',
   'selector':'returns1 iff actualglobals WORD59DFD8==4 && WORD59DFDA==2; otherwise0',
   'qualified_state_fields':'retain both complete actualuint16 global values plus issuer-owned text-state revision/current; revision is source lifecycle, not nativewire field',
   'receiver_scope':'state belongs to actual6F receiverclient/current issuer observation; senderprofile/Sessionlanguage or anotherreceiver state cannot qualify everyrecipient',
   'limitations':'global loaded/current identity must be genuinely supplied, not inferred from image rawdata/client locale/profile displaypreference'},
  'adaptation_domain':{'bit1_global0':'52F330 first/second/third helper outputs overwrite body1C/2C/3C',
   'bit0_global1':'52F170 first/second/third helper outputs overwrite body1C/2C/3C',
   'first_failure':'first helperfalse skips allfieldoverwrites; laterhelperresults are not individuallychecked',
   'scope':'static callerdataflow only; helpers/Windows mapping/currentconversionconfiguration not recovered/executed here'},
  'replacement':'4FB460 lookup oldlow12ID ->4FC560cleanup ->4FC1C0store. SameID can replace name/object; nativeincarnation notcommon leasegeneration.',
  'cleanup':'bounded4FC62E..654 mode1 setsIDFFFFFFFF; clearsnamefirstBYTE unconditionally; resource/render callees deliberately notfollowed',
  'ordinary_player_scope':'known selectors/bits/appearance geometry are fieldprojections only; no originalserver actorowner/playerclass producer or permission proof recovered',
  'next_source_actions':['qualify postadaptation exactpublished name, or actualwire/globalstate equality before treatingrawlogical29 as authoritativeprivate target',
   'TaiwanRawNameState must retain complete twoWORD actualstate and genuine issuerrevision/current; never narrowWORD toBYTE or use rawimagezero asloadedstate',
   'keep originalrawfull6F bytes and actualprivatecapability/fullcommonlease/root/codepage/current and publication replacement epoch',
   'actualvisibility-issued privateplayer cap needed: parser/namejoin/maskednativeID alone cannot makeplayer authority',
   'retain owner-required Traditional/Simplified conversion; rawsubset qualifications never shrink wholeTW/CN/web goal',
   'exclude NativePromptMarker, substituted/truncated encode_display and opaque actor categories fromidentityproof'],
  'gaps':['originalserver6F producer and ordinaryplayer authorization remainOPEN',
   'actualglobal4/2 initializer/current transport text-state issuer remainOPEN',
   'postadaptation namebytes/codec branch exactmapping and loadedconfiguration remainOPEN; no codec executed',
   'no common64 ID or generation is carried or implied by examined native12bit actor/name fields',
   'replacement/visibility delivery lifecycle and legitimate peer permissions remain realgameowner responsibility'],
  'retained_scope':'181 all19raw spans remainsealed; this round only six selective retained intervals and one expanded fieldprojection, never recounted asnew181recovery',
  'corrections':'181 rawtext interval endedFC340 and included1 byte of nextFC33Finstruction; complete original preserved. This round cleanretainedcopy endsFC33F, no baseline rewrite.',
  'executed':{'build':0,'tests':0,'native':0,'C++':0,'codec':0,'emulation':0,'DB':0,'SQL':0,'API':0},
  'whole_game_completion_percent':None,
 }
 emit('findings.json',facts)
 emit('derived-inputs.json',[{'source':'inputs/native.bin','derived':'native-spans.json','kind':'file-only bounded Capstone records'},
  {'source':'actual stable source originals','derived':'source-sites.json','kind':'literal source excerpts; no C++ execution'}])
 put(OUT/'findings.md',('The actualTW world6F consumer can overwrite first/second/third text before peer storage, depending on bit25 versus531C10 loadedglobal selector. '
  'Thus181 raw peer-name lineage refers to postadaptation bytes; direct equality with originalwirelogical29 requires that actual branch qualification or realpostadapted issuer. '
  '4FB460 replaces old same-low12-ID peer before storingfull6F again. Native actorIDs/names are not common64 ownership/generation, and no client fieldprojection proves ordinaryplayer authorization. '
  'Visibility-issued privateplayer capability must bind actualcommonlease/profile/current and the immutable originalfullpublication. '
  'The owner-required text conversion remains scope; rawqualified subset is not the wholegoal. No codec/render/formatter/glyph/155 chain was executed or pursued forclosure.\n').encode())
 print(json.dumps(counts))

def capture():
 rows=[original(ROOT/name,f'current/s{n:02d}{Path(name).suffix}') for n,name in enumerate(SOURCES+[OWNED])]
 emit('current-source-origins.json',rows)
 put(OUT/'README.md',('Round182 actual native publication/name qualification. CPP edits0; originalimage and derivedinstructions separated. '
  'Mutable visibility/publishedname/CNchat/TWchat sources, rootbooks/catalog/report/artifactreceipts excluded fromcurrentpins. '
  'Former181 evidence and freshbefore epochs retained unchanged. Source qualifications are not server native authority/runtime acceptance.\n').encode())
 members=[]
 for path in sorted(OUT.rglob('*')):
  if path.is_file():
   raw=path.read_bytes();members.append({'path':path.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
 emit('seal.json',members)
 print(json.dumps({'current_source_originals':len(rows),'sealed_members':len(members),
  'seal_sha256':sha((OUT/'seal.json').read_bytes()),'tool_bytes':len((ROOT/OWNED).read_bytes()),'tool_sha256':sha((ROOT/OWNED).read_bytes())}))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['recover','capture']);args=parser.parse_args()
 if args.mode=='recover':recover()
 else:capture()
