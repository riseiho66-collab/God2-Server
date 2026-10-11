"""Read-only full-source inventory of shared chat authority frontiers.

File bytes/hash/site capture only. Never imports database/codec/native tools,
runs SQL, builds/tests or executes server/client/C++/Lua/Windows/API calls.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
ROUND=ROOT/'artifacts/integration/packet-connections-20261006/cn-native-chat-consumer-source-01'
OUT=ROUND/'agents/shared-chat-authority-frontier'
OWNED='tools/reconstruction/shared_chat_authority180.py'
BEFORE='b82c93aba7604dd3ad4e107013068220b364836f36c1a37057bd1bd55d3097f7'
SOURCES=[
 'src/handlers/OwnedPartyChatService.h','src/handlers/OwnedPrivateChatService.h',
 'src/handlers/OwnedGuildChatService.h','src/game/NativeParty.h',
 'src/db/SqliteGuildRepository.h','src/db/SqliteGuildRepository.cpp',
 'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
 'src/db/RecoveredCharacterRepository.h','src/game/RecoveredCharacter.h',
 'src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteRecoveredCharacterRepository.cpp',
 'src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp','src/text/ChineseText.h',
 'src/core/Application.h','src/core/Application.cpp',
]
CONTEXT=['AGENTS.md','docs/IMPLEMENTATION_PROVENANCE.md','docs/GOAL_ACCEPTANCE.md']
# Each literal is an actual retained source anchor, not behavioral execution.
SITES=[
 ('src/handlers/OwnedPartyChatService.h','// CUSTOM-0073:', 'TW custom transient-party chat audience provenance'),
 ('src/handlers/OwnedPartyChatService.h','parties.party_size(sender)<2','custom admission minimum2, not recovered CN permission'),
 ('src/handlers/OwnedPartyChatService.h','group.size()>5','custom party ceiling and one sender membership'),
 ('src/handlers/OwnedPartyChatService.h','if(!old || !fresh || !owns(*old,fresh->member,id))','cached/fresh session/account/character owner check'),
 ('src/handlers/OwnedPartyChatService.h','for(const auto& [id,peer]:current)if(peer.member.ready)','ready group recipients, custom audience fanout'),
 ('src/handlers/OwnedPartyChatService.h','if(parties.participants(sender)!=group','late exactgroup recheck after callbacks'),
 ('src/handlers/OwnedPartyChatService.h','return actor==source.member.character;','TW 5C actor suppliedfrombounded partycharacter, noCN proof'),
 ('src/handlers/OwnedPrivateChatService.h','// CUSTOM-0074:', 'TW custom online exactname source+target policy'),
 ('src/handlers/OwnedPrivateChatService.h','std::uint64_t session{},account{};std::uint32_t character{};','mixedwide owner tuple and32bit legacy Peer.character'),
 ('src/handlers/OwnedPrivateChatService.h','if(peer.name==text->recipient)','rawdecoded owned name exactcomparison, no translatedalias'),
 ('src/handlers/OwnedPrivateChatService.h','if(target)return {};target=&peer;','lateambiguity rejected, not nativeequivalence policy'),
 ('src/handlers/OwnedPrivateChatService.h','target->session==sender','custom self-private rejection'),
 ('src/handlers/OwnedPrivateChatService.h','for(const auto* recipient:{&*source,target})','custom source+target recipients, not nativeCN audience'),
 ('src/handlers/OwnedPrivateChatService.h','if(index(audience_())!=audience)','wholeonline snapshot late recheck'),
 ('src/handlers/OwnedPrivateChatService.h','return name.find_first_of(','custom delimiter restriction of exactownednames'),
 ('src/handlers/OwnedPrivateChatService.h','peer.character<=0x3fff','legacy bounded character identity cannotbecommon64/nativeCN map'),
 ('src/handlers/OwnedPrivateChatService.h','return actor==source.character;','legacyTW5C actor character assumptions'),
 ('src/handlers/OwnedGuildChatService.h','// CUSTOM-0075:', 'persistentadmin membership provenance, not CN nativeguild rights'),
 ('src/handlers/OwnedGuildChatService.h','StoredGuildMembership membership;','immutable observed membership/guild revisions asfreshsnapshot carriers'),
 ('src/handlers/OwnedGuildChatService.h','const auto group=members(audience_(),source->membership.guild_id);','custom onlinegroup filteredbyexisting storedguild identity'),
 ('src/handlers/OwnedGuildChatService.h','if(members(audience_(),source->membership.guild_id)!=group)','wholemembership audience current recheck'),
 ('src/game/NativeParty.h','// CUSTOM-0062:', 'transientpartyconsent andmax5 custom design'),
 ('src/game/NativeParty.h','std::uint64_t session{},account{};std::uint16_t character{},area{},scene{},x{},y{};','legacy14bit/16bit character andwireposition carrier'),
 ('src/game/NativeParty.h','member.character>0x3fff','legacybounded party registry admission'),
 ('src/game/NativeParty.h','pending_.emplace(sender,Pending{*target,now+std::chrono::seconds(30)})','custom30sec offerwindow notCN nativechat rate/permission'),
 ('src/game/NativeParty.h','static bool compatible(const Member& a,const Member& b)','custom ready+samearea/scene partyjoin policy'),
 ('src/db/SqliteGuildRepository.h','// CUSTOM-0075:','maintenance storageexplicit provenance'),
 ('src/db/SqliteGuildRepository.h','std::optional<StoredGuildMembership> load(std::uint64_t account,std::uint64_t character);','existingowner-qualified load primitive; no memberenumerator'),
 ('src/db/SqliteGuildRepository.h','std::uint64_t admin_create(','adminwrites notclient-native permission APIs'),
 ('src/db/SqliteGuildRepository.cpp','for(const auto simplified:{false,true})','maintenance names requirelossless both936/950, not universalCNname rule'),
 ('src/db/SqliteGuildRepository.cpp','row.text(offset)!="CUSTOM_DESIGNED"','stored provenance mandatory, sourcehashalone isnotnativeprovenance'),
 ('src/db/SqliteGuildRepository.cpp','CREATE TABLE owned_guilds (','shared existingcustom tables retained; no duplicate _cn tables neededfromwire difference'),
 ('src/db/SqliteGuildRepository.cpp','CREATE TABLE owned_guild_members (','membercharacter FK existingcommonrecovered_characters'),
 ('src/db/SqliteGuildRepository.cpp','SqliteGuildRepository::load(std::uint64_t account,std::uint64_t character)','exact64bit storageownership reader, neverexecutedhere'),
 ('src/db/SqliteGuildRepository.cpp','if(membership_revision>guild.revision)','currentmembership/guild revision relationship'),
 ('src/db/SqliteGuildRepository.cpp','if(before.has_value()!=expected_revision.has_value()','adminassign expectedmembership revision CAS'),
 ('src/game/SharedWorldPresence.h','std::uint64_t session,account,character,generation;','common exactfull64bit leaseidentity, independent16bit suppliedactorhandle'),
 ('src/game/SharedWorldPresence.h','std::uint16_t actor_handle;','sceneactorhandle isnotnativefullchatactorDWORD'),
 ('src/game/SharedWorldPresence.h','Both adapters must use the same registry','legacyTW presence notimplicitly registered; actualcrossprotocol binding mandatory'),
 ('src/game/SharedWorldPresence.h','std::optional<Lease> ready_lease(std::uint64_t session,std::uint64_t account,','directread-only exactactivetuple API'),
 ('src/game/SharedWorldPresence.cpp','row.id==lease.character && row.account_id==lease.account','commoncharacter ownership read, protocol-neutral identity'),
 ('src/game/SharedWorldPresence.cpp','entry.lease.character==character || entry.lease.actor_handle==handle','globalexclusionexplicit serverpolicy, not originalnativeaudience'),
 ('src/game/SharedWorldPresence.cpp','found->second.lease==lease && owned(lease)','generation-qualified currentlease plusactualownership'),
 ('src/game/SharedWorldPresence.cpp','if(!ready(lease))return std::nullopt;','exactactive ready_lease qualification, no reservation/default'),
 ('src/game/SharedWorldPresence.cpp','return characters_.load_position(lease.account,lease.character);','actualcurrent savedposition separatefromimmutableinitialleaseposition'),
 ('src/db/RecoveredCharacterRepository.h','virtual std::vector<RecoveredCharacter> list_for_account','commoncurrentfullaccount roots interface'),
 ('src/game/RecoveredCharacter.h','std::uint64_t id = 0;','common64bit identity, not wireactor projection'),
 ('src/game/RecoveredCharacter.h','std::uint16_t name_codepage=950;','storedrawname codepage explicit0/936/950 lifecycle'),
 ('src/db/SqliteRecoveredCharacterRepository.cpp','const auto name = statement.blob(4, 1, 14);','fullcommonlegacyname provenance profile/name_bytes consistency'),
 ('src/db/SqliteRecoveredCharacterRepository.cpp','if(result.name_codepage!=0 && result.name_codepage!=936 && result.name_codepage!=950)','unknown0 encoding cannot silentlydecode currentname'),
 ('src/db/SqliteRecoveredCharacterRepository.cpp','SqliteRecoveredCharacterRepository::list_for_account(std::uint64_t account_id)','owner-qualified commonrows, existing2slots domain notCN nativecatalog default'),
 ('src/text/LegacyChineseCodec.cpp','return narrow(wide(bytes,simplified?936:950),CP_UTF8);','explicitCPboundary viaBoolean API; no nativeprotocol/scriptauthority fromname'),
 ('src/text/LegacyChineseCodec.cpp','encoded="?";','existingdisplay substitution notlosslessidentity conversion'),
 ('src/text/ChineseText.h','// CUSTOM-0029:','user-required presentation conversion, notauthority or nativegameplay rule'),
 ('src/core/Application.cpp','const auto party_member=[&](Session& session)','actualTW legacy source adapter start'),
 ('src/core/Application.cpp','session.character_id>0x3fff','actuallegacy party/chat qualification boundedbeforecast'),
 ('src/core/Application.cpp','m.name=LegacyChineseCodec::decode','actualownedname uses storedname_codepage, notclaim headerlanguage'),
 ('src/core/Application.cpp','OwnedPartyChatService party_chat(','actualTWparty caller strongdependency onparty_sessions/recoveredmovement'),
 ('src/core/Application.cpp','const auto private_chat_peer=[&]','actualTW privatepeer registry/native_chat_sessions'),
 ('src/core/Application.cpp','// Session locale owns decoding, not the sender\'s header flag.','legacyTW decoding profile; newCNprofile/script mustindependently qualify'),
 ('src/core/Application.cpp','source.name+": ["+target.name+"] "','legacyprivate presentation customprefix notgenericCN header/format'),
 ('src/core/Application.cpp','const auto guild_chat_peer=[&]','actualTW guildpeer resolver isCUSTOM0075 path'),
 ('src/core/Application.cpp','const auto membership=database.guilds().load(actor->account,actor->character);','actualexistingadmin-membership storage input'),
 ('src/core/Application.cpp','for(const auto& [id,unused]:native_chat_sessions)if(auto peer=guild_chat_peer(id))','audienceenumeratedfromTW sessions, no durable/currentCNenumerator'),
 ('src/core/Application.cpp','// CUSTOM-0075: mode3 stays guild-only','actualtyped guild branch beforefrozencommon, notnew sharedsource authority'),
 ('src/core/Application.cpp','auto deliveries=guild_batch?guild_chat.prepare','actualTWcustom guildrequest ->prepare'),
 ('src/core/Application.cpp','auto deliveries=private_batch?private_chat.prepare','actualTWcustom privaterequest ->prepare'),
 ('src/core/Application.cpp','auto deliveries=party_chat_batch?party_chat.prepare','actualTWcustom partyrequest ->prepare'),
 ('src/core/Application.cpp','native_chat_sessions.insert_or_assign(session.id(),session.shared_from_this());','actualTWregistry admission unlikeCNConnection/commonleasegeneration'),
 ('src/core/Application.cpp','native_chat_sessions.erase(session->id());','actuallegacydisconnect cleanup notautomaticsharedregistry registration'),
]
EXCERPTS=[
 ('src/core/Application.cpp',1265,1391,'actual legacy TW party/private/guild source factories'),
 ('src/core/Application.cpp',3216,3368,'actual typed CUSTOM chat dispatch and movement reorder/fanout'),
 ('src/core/Application.cpp',1979,1996,'actual legacy Session entry registries'),
 ('src/core/Application.cpp',1827,1839,'actual legacy Session disconnect registries'),
 ('src/db/SqliteRecoveredCharacterRepository.cpp',69,111,'actualcommon fullcharacter/profile/rawname/codepage reader'),
 ('src/db/SqliteRecoveredCharacterRepository.cpp',906,948,'actualcommon owner-qualified list/position reader'),
 ('src/db/SqliteRecoveredCharacterRepository.cpp',1001,1008,'historicalname_codepage binding mutator sourceonly, nevercalled'),
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

def capture():
 before=(ROUND/'before-manifest.json').read_bytes()
 if digest(before)!=BEFORE or len(json.loads(before))!=1290:
  raise RuntimeError('Fresh actual before mismatch; do not reset baseline')
 OUT.mkdir(parents=True,exist_ok=True);put(OUT/'root-before.raw',before)
 emit('root-lineage.json',{'before_inputs':1290,'before_sha256':BEFORE,
  'prior179_members_retained':2226,'prior_scope':'parent full-member preservation receipt','baseline_replaced':False})
 rows=sources('before',SOURCES)
 # These actual original inputs are full source files, not native images or DBs.
 emit('original-inputs.json',rows)
 emit('native-original-inputs.json',[])
 emit('new-file-before.json',[{'path':(ROOT/OWNED).as_posix(),'state':'absent in root fresh before','copy':None}])
 emit('context-originals.json',[original(ROOT/name,f'context/c{n:02d}.md') for n,name in enumerate(CONTEXT)])
 source_bytes={name:(ROOT/name).read_bytes() for name in SOURCES}
 source_manifest={name:row for name,row in zip(SOURCES,rows)}
 site_rows=[]
 for n,(name,literal,fact) in enumerate(SITES):
  raw=source_bytes[name];needle=literal.encode();a=raw.find(needle)
  if a<0:raise RuntimeError('Missing actualsource anchor: '+name+' '+literal)
  line=raw.count(b'\n',0,a)+1;begin=raw.rfind(b'\n',0,a)+1
  end=raw.find(b'\n',a);end=len(raw) if end<0 else end+1
  site_rows.append({'id':n,'path':(ROOT/name).as_posix(),'copy':source_manifest[name]['copy'],
   'source_bytes':len(raw),'source_sha256':digest(raw),'line':line,'byte_offset':a,
   'literal':literal,'source_line_hex':raw[begin:end].hex(),'fact':fact,
   'scope':'actualserver C++ source, notnative/DB execution'})
 emit('source-sites.json',site_rows)
 snippets=[]
 for n,(name,start,end,purpose) in enumerate(EXCERPTS):
  raw=source_bytes[name];lines=raw.splitlines(keepends=True)
  chunk=b''.join(lines[start-1:end]);copy=f'excerpts/e{n:02d}.txt';put(OUT/copy,chunk)
  snippets.append({'path':(ROOT/name).as_posix(),'complete_source_copy':source_manifest[name]['copy'],
   'complete_source_bytes':len(raw),'complete_source_sha256':digest(raw),
   'first_line':start,'last_line':end,'copy':copy,'bytes':len(chunk),'sha256':digest(chunk),
   'purpose':purpose,'scope':'source interval only; fulloriginal kept; no execution'})
 emit('source-excerpts.json',snippets)
 emit('neutral-source-map.json',{
  'direct_existing_shared_primitives':[
   {'source':'SharedWorldPresence::ready_lease/current/ready','identity':'exact64bit session/account/character/generation plus actualsupplied16bit actorhandle',
    'must_retain':'same actualsharedregistry/repository, initialimmutablelease distinct savedcurrentposition, actualSession/CNphase separate',
    'does_not_supply':'chatpermission/audience/visiblefullactorDWORD/CNcodepage'},
   {'source':'RecoveredCharacterRepository::list_for_account andStored RecoveredCharacter','identity':'ownedcommon64bit roots/full40byteprofile/rawname/name_codepage',
    'must_retain':'explicit0/936/950 sourceencoding, fullrow/name provenance; no transformedname alias or16bit projection',
    'does_not_supply':'nativeCNcharacter layout/namepolicy/membership'},
   {'source':'SqliteGuildRepository::load(account,character)','identity':'existingowned guild/memberfull64bit identities/guild_revision/membership_revision',
    'must_retain':'CUSTOM0075 provenance andactualcurrent existingrows; do notrelabelasCNnativegrant',
    'does_not_supply':'nativeguild creation/joinpermission/economics/memberenumeration/CNfanout'},
   {'source':'LegacyChineseCodec explicit936/950 edge andChineseText projection interface','identity':'raw source bytes ->UTF8 original ->recipientdisplay script ->actualwireencoding',
    'must_retain':'protocol/profile/script preference separate, exactnames/control unchanged, losslessidentity andsourceproof',
    'does_not_supply':'decode authority fromheader tag ororiginNativeRule; no codec executedhere'},
  ],
  'not_reusable_as_CN_native_authority':[
   {'sources':['OwnedPartyChatService','NativeParty'],'designs':['CUSTOM0073','CUSTOM0062'],
    'limits':['16bit/3FFFcharacter','group2..5','same-scene consent/max5/30sec customoffer','TWcached member registry'],
    'avoid':'do not seedCNmembership orfullnative actor fromtransientTWparty'},
   {'source':'OwnedPrivateChatService','design':'CUSTOM0074',
    'limits':['uint32character<=3FFF','source+targetonly','selfprivate prohibited','exactonlineUTF8name withdelimiterrestrictions'],
    'avoid':'actualCNaudience/name-equivalence/selfpolicy cannotbeassumedfromTWclient'},
   {'source':'OwnedGuildChatService/SqliteGuildRepository','design':'CUSTOM0075',
    'limits':['administratorconfiguredmembership','TWonlineaudienceonly','maintenancebothcodepage15Bname rule'],
    'avoid':'nativeguild actorstring/channel3 never grants membership; existingCASgeneration notCNnativecounter'},
   {'source':'Application.cpp frozenchat callbacks',
    'limits':['TWSessionweakregistries/recovered_movement','254serializedtext budget','custom streamerannotation','manufacturedlegacy displayheaders/nameprefix'],
    'avoid':'newCNnative path mustremainexplicit withactualwhole5C/cipher/owner/consumercontract; do not calllegacy defaultfunctions'},
  ],
  'no_new_tables_or_SQL':'Onlysource read. Existingcommonstorage preferred; no regionaltable split justifiedbywire difference.',
  'audit_not_implementation':'No newauthority/gameCPPchanges fromthisagent; parent ownsactualCNsource increment'})
 emit('identity-frontier.json',{
  'common_tuple':'uint64 session/account/character/generation; exact activelease andtrue authenticatedtransport tuple',
  'separate_wire_identities':['fullnative32bit5Cactor','actual16bit scene/renderhandle','common64bitcharacter'],
  'forbid':['low16/commonID narrowing to nativeactor','usingclientheaderWORD forrecipient','assumingoldTWregistryhasCNconnections',
   'name/codepage defaultwhenstored0','translated/displayreplacement name grants','membership fromActor+6/tab/channel'],
  'current_scope':'fulllease/currentroot/rawname+name_codepage/sourceaudience revisions/battlephase/currentactualrecipientresources',
  'ready_limits':'presence.ready validatesactiveexactlease+commonownership; nottransportnativephase/visibility/permission proof',
  'private_target':'exactrawtarget bytes and qualifiedsourcecodepage; actualowner resolvesexactownedfullidentity, noaliasguess',
  'guild_members':'repositoryload onlyperaccount/character; actualmemberaudienceenumerator remainsrealqualifiedprovider',
  'party_members':'transientTWNativeParty list isCUSTOM0062 only; newnative-neutral/CN actualmembershipowner stillneeded'})
 emit('next-source-increment-map.json',[
  {'increment':'explicit CNchat consumer/source bounddomain','reuse':'current actualnative request/header plusSharedWorldPresence ready_lease',
   'required':'actualsource inputform/prose/rawtarget/bodyrange/UTF8original/profile andtrueCNconsumerchannel contract',
   'forbidden':'callingTW CUSTOM prepare or defaultsuccess', 'authority_gap':'originalnative permissions/5Copaqueheader issuer'},
  {'increment':'actualnative current audience owner','reuse':'fullcommoncharacter owner roots andgenerationlease carriers',
   'required':'realparty/private/guildgroup provider withcompletelease/snapshot revisions checkedbefore/aftercallbacks',
   'forbidden':'fromTWregistry orclienttab inferCNmembers', 'authority_gap':'nativegroup permission/audience/currentprovider'},
  {'increment':'perrecipient wire projection/publication','reuse':'shared UTF8-original text projection andqualifiedwireencoding',
   'required':'actualwhole5C actor/header/bodyoffset/prefix/suffix/loadedcapacity/currentresources/cipher/ordered senderframes',
   'forbidden':'CNfromTW0..8table orsame254budget or14bitactor', 'authority_gap':'actualCNconsumer proof/provider whereunknown'},
  {'increment':'common durablemembership whennativeowner supplied','reuse':'existingcommonowned storage identities andCASprovenance',
   'required':'nativepermission andoriginqualifiedvalues separatefromCUSTOMmaintenance; actualcompleteaudience/source lifecycle',
   'forbidden':'new _cn tables solelybecauseprotocol differs; admin API becomesclientauthorization',
   'authority_gap':'do notpromoteCUSTOM0075membershipasCNnative'}])
 emit('gaps.json',{
  'native_group_authority':'OPEN nativeoriginalparty/guild/private permissions/rate/name-equivalence/audience andexactcurrent provider',
  'original_native5C':'OPEN actualopaqueheader actor/tablebytes issuer; retainedTW source cannotcertifyCNwire',
  'full_memberenumerator':'OPEN neutral/native currentgroup API; existingGuildload plusTWweakregistry isnotcrossclientmemberlist',
  'legacy_integration':'oldTW presence/parties/chat notautomatically registeredinto sharedowner registry',
  'nameencoding':'stored0 unbound/rawprofile provenance mustnotguess; losslessidentity distinctrecipientdisplay substitutions',
  'frozen_sources':'No App/handler/repository/codec/grammar changes; parentmutableCNsources excluded',
  'native_reads_this_round':0,'native_inputs':[],
  'phase':'purefile source/hashes; no native/codec/API/DB/SQL/build/test/runtime or155retry'})
 emit('findings.json',{'round':'20261008-cn-native-chat-consumer-source','owned_sources':[OWNED],
  'source_before_originals':len(rows),'actual_CPP_original_inputs':len(rows),
  'actual_CPP_original_bytes':sum(r['bytes'] for r in rows),'source_sites':len(site_rows),
  'source_excerpt_intervals':len(snippets),'native_inputs':0,'native_spans':0,'new_native_recovered_functions':0,
  'game_CPP_modified':0,'derived_codec_emulated_inputs':0,'DB_reads_SQL_executions':0,
  'keyfacts':['CUSTOM0073/0074/0075/0062 authority provenance kept','legacy boundedcharacter andTWregistries are notCNidentity',
   'existingSharedWorldPresence exactactive64bit lease isdirectneutralprimitive','actualstorednamecodepage/rawname preserved',
   'Guildload isexistingCUSTOMmaintenance input withno nativegroupenumerator','concrete explicitCNsource/audience/wire increments mapped'],
  'new_opcode_values':0,'complete_routes_added':0,'whole_game_percentage':None,
  'existing_inventory_not_recounted':{'C2S':156,'S2C':252,'variants':30},'source_static_only':True})
 emit('derived-inputs.json',{'codec_or_emulated_inputs':[],
  'derived_source_outputs':['source-sites.json','source-excerpts.json','neutral-source-map.json','next-source-increment-map.json'],
  'actual_originals_kind':'completeC++text only, no nativebinary/DB/decodedcodecinput'})
 sources('intermediate',[OWNED])
 print(json.dumps({'before_sources':len(rows),'CPP_input_bytes':sum(r['bytes'] for r in rows),
  'sites':len(site_rows),'excerpts':len(snippets),'native_inputs':0,'native_spans':0,
  'tool_bytes':len((ROOT/OWNED).read_bytes()),'tool_sha256':digest((ROOT/OWNED).read_bytes())}))

def final():
 for row in json.loads((OUT/'before-source-origins.json').read_text()):
  if digest(Path(row['path']).read_bytes())!=row['sha256']:
   raise RuntimeError('Stable actualsource changed; retain before andcoordinate parent')
 rows=sources('current',SOURCES+[OWNED])
 emit('delivery.json',{'BATCHFINAL_received':True,'current_originals':len(rows),
  'owned_tools':[OWNED],'game_CPP_changes':0,'native_inputs':0,'source_CPP_originals_separate':True,
  'mutable_CN_sources_rootbooks_reports_catalog_excluded':True,
  'new_opcodes':0,'complete_routes':0,'percentage':None})
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
 final() if parser.parse_args().final else capture()
