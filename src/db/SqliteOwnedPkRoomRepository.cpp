#include "db/SqliteOwnedPkRoomRepository.h"
#include "db/SqliteSupport.h"
#include "game/BattleCheckpointCodec.h"
#include "game/OwnedTaiwanPkLaterGrantSource.h"
#include "game/OwnedTaiwanPkTerminalSource.h"
#include "protocol/RecoveredWorldFrame.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <limits>
#include <string_view>
namespace god2 {
namespace {
using sqlite_detail::Statement;
using sqlite_detail::Transaction;
using Json=nlohmann::json;
// CUSTOM-0114 owns one consistent read snapshot. Unlike Transaction this
// uses BEGIN, not BEGIN IMMEDIATE, and performs no DML/schema installation.
struct RecoveryRead {
    sqlite3* db;bool finished=false;
    explicit RecoveryRead(sqlite3* value):db(value){
        if(!sqlite3_get_autocommit(db))throw DatabaseError("PK recovery requires its own read scope");
        sqlite_detail::execute(db,"BEGIN");
    }
    ~RecoveryRead(){if(!finished)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void commit(){sqlite_detail::execute(db,"COMMIT");finished=true;}
};
void require_owned_main_sources(sqlite3* db){
    // Unqualified legacy readers must not be redirected to TEMP substitutes.
    constexpr const char* names="('owned_pk_room_feature','owned_pk_rooms','owned_pk_room_members','owned_pk_room_outbox','owned_pk_round_feature','owned_pk_room_rounds','accounts','recovered_characters','recovered_positions','character_role_snapshots','character_resources','battle_reservations','battle_settlements')";
    const auto shadow_sql=std::string("SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ")+names+" OR tbl_name COLLATE NOCASE IN "+names;
    Statement shadows(db,shadow_sql.c_str());
    if(shadows.row())throw DatabaseError("PK active profile TEMP source shadow rejected");
    const auto table_sql=std::string("SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ")+names;
    Statement tables(db,table_sql.c_str());
    if(!tables.row()||tables.integer(0)!=13||tables.row())
        throw DatabaseError("PK active profile requires its exact main source tables");
}
std::string owned_combat_profile_digest(std::string_view readset){
    auto value=Json::parse(readset);
    value.erase("profile_readset_sha256"); // No recursive/self-supplied hash input.
    value["digest_domain"]="CUSTOM-0106-complete-owned-combat-entry-readset-v1";
    const auto bytes=value.dump();
#ifdef _WIN32
    if(bytes.size()>std::numeric_limits<ULONG>::max())throw DatabaseError("PK combat digest input too large");
    struct Handles{
        BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
        std::vector<std::uint8_t> object;
        ~Handles(){if(hash)BCryptDestroyHash(hash);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);}
    }handles;
    if(!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&handles.algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)))
        throw DatabaseError("PK combat SHA256 provider unavailable");
    DWORD size=0,returned=0;
    auto status=BCryptGetProperty(handles.algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&returned,0);
    if(!BCRYPT_SUCCESS(status))throw DatabaseError("PK combat SHA256 object length failed");
    handles.object.resize(size);std::array<std::uint8_t,32> result{};
    status=BCryptCreateHash(handles.algorithm,&handles.hash,handles.object.data(),size,nullptr,0,0);
    if(BCRYPT_SUCCESS(status))status=BCryptHashData(handles.hash,reinterpret_cast<PUCHAR>(const_cast<char*>(bytes.data())),static_cast<ULONG>(bytes.size()),0);
    if(BCRYPT_SUCCESS(status))status=BCryptFinishHash(handles.hash,result.data(),static_cast<ULONG>(result.size()),0);
    if(!BCRYPT_SUCCESS(status))throw DatabaseError("PK combat SHA256 failed");
    std::string out;out.reserve(64);
    for(const auto byte:result){out+="0123456789abcdef"[byte>>4];out+="0123456789abcdef"[byte&15];}return out;
#else
    throw DatabaseError("Qualified PK combat SHA256 backend unavailable");
#endif
}
Json appearance_root(const RecoveredCharacter& r){
    return Json::array({r.id,r.account_id,r.slot,r.profile,r.created_at,r.name_codepage,r.streamer_privilege});
}
Json appearance_position(const RecoveredPosition& p){
    return Json::array({p.area,p.scene,p.x,p.y,p.revision});
}
Json appearance_inventory(const OwnedInventorySnapshot& snapshot){
    Json cells=Json::array();
    for(const auto& cell:snapshot.cells){
        Json instance=nullptr;
        if(cell.instance){
            const auto& v=*cell.instance;Json aliases=Json::array();
            for(const auto& a:v.aliases)aliases.push_back(Json::array({a.client_sha256,a.profile,a.source_sha256,
                a.source_record,a.native_key,a.native_slot,a.revision,a.record}));
            instance=Json{{"id",v.id},{"definition_key",v.definition_key},{"quantity",v.quantity},
                {"revision",v.revision},{"stackable",v.stackable},{"acquisition_sha256",v.acquisition_sha256},
                {"acquisition_record",v.acquisition_record},{"aliases",aliases}};
        }
        cells.push_back(Json::array({cell.location_kind,cell.location_index,instance}));
    }
    return Json{{"root",appearance_root(snapshot.root)},{"revision",snapshot.revision},
        {"source_sha256",snapshot.source_sha256},{"source_record",snapshot.source_record},{"cells",cells}};
}
Json appearance_material(const OwnedTaiwanPkAppearanceSource::Material& m){
    const auto& w=m.world;const auto& e=m.equipment;const auto& l=m.lease;
    return Json{{"lease",Json::array({l.session,l.account,l.character,l.generation,l.actor_handle})},
        {"initial_position",appearance_position(l.position)},{"battle_generation",m.battle_generation},
        {"entry_frame",m.entry_frame},{"entry_logical",m.entry_logical},{"accepted_tail",m.accepted_tail},
        {"config_flag",m.config_flag},{"world",Json{{"root",appearance_root(w.root)},
            {"position",appearance_position(w.position)},{"client_sha256",w.client_sha256},
            {"record_kind",w.record_kind},{"source_sha256",w.source_sha256},{"source_record",w.source_record},
            {"record",w.record},{"revision",w.revision}}},
        {"inventory",appearance_inventory(m.inventory)},
        {"equipment",Json{{"root",appearance_root(e.root)},{"position",appearance_position(e.position)},
            {"client_sha256",e.client_sha256},{"record_kind",e.record_kind},{"source_sha256",e.source_sha256},
            {"source_record",e.source_record},{"record",e.record},{"revision",e.revision},{"actor_handle",e.actor_handle}}},
        {"ordinary86_4",RecoveredBattlePlayerAppearance::encode(m.appearance)}};
}
bool owned_appearance_current(const SqliteOwnedPkRoomRepository::Input& input,sqlite3* db){
    if(!input.entry.owned_appearances())return true; // Historical path unchanged.
    if(!sqlite3_get_autocommit(db))return false;
    for(std::size_t i=0;i<2;++i){
        const auto& source=(*input.entry.owned_appearances())[i];
        const auto& m=source.material();const auto& p=i==0?input.pair.challenger:input.pair.recipient;
        // SharedWorldPresence generation and Application PK world_generation
        // are distinct namespaces. Retain both, never assert numerical equality.
        if(!source.uses_connection(db)||m.lease.session!=p.session||m.lease.account!=p.account||
           m.lease.character!=p.character||m.lease.actor_handle!=p.character||
           m.battle_generation!=p.battle_generation||m.equipment.position!=p.position||!source.current())return false;
    }
    if(input.combat_sources)for(const auto& source:*input.combat_sources)
        if(!source.uses_connection(db)||!source.current())return false;
    if(input.entry.owned_players())for(const auto& source:*input.entry.owned_players())
        if(!source.uses_connection(db)||!source.current())return false;
    if(input.entry.owned_vitals())for(const auto& source:*input.entry.owned_vitals())
        if(!source.uses_connection(db)||!source.current())return false;
    if(input.entry.owned_initial_grants())for(const auto& source:*input.entry.owned_initial_grants())
        if(!source.uses_connection(db)||!source.current())return false;
    if(input.entry.owned_initial_contexts())for(const auto& source:*input.entry.owned_initial_contexts())
        if(!source.uses_connection(db)||!source.current())return false;
    return true;
}
bool owned_combat_stored_current(const SqliteOwnedPkRoomRepository::Input& input,sqlite3* db){
    if(input.combat_sources)for(const auto& source:*input.combat_sources)
        if(!source.stored_current_in_room_transaction(db))return false;
    if(input.entry.owned_players())for(const auto& source:*input.entry.owned_players())
        if(!source.stored_current_in_room_transaction(db))return false;
    if(input.entry.owned_vitals())for(const auto& source:*input.entry.owned_vitals())
        if(!source.stored_current_in_room_transaction(db))return false;
    if(input.entry.owned_initial_grants())for(const auto& source:*input.entry.owned_initial_grants())
        if(!source.stored_current_in_room_transaction(db))return false;
    if(input.entry.owned_initial_contexts())for(const auto& source:*input.entry.owned_initial_contexts())
        if(!source.stored_current_in_room_transaction(db))return false;
    return true;
}
constexpr const char* feature_schema=R"SQL(
CREATE TABLE IF NOT EXISTS owned_pk_room_feature (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 version INTEGER NOT NULL CHECK(version=1), design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0086'));
CREATE TABLE IF NOT EXISTS owned_pk_rooms (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 state TEXT NOT NULL CHECK(state IN ('reserved','active','finished','abandoned')),
 readset TEXT NOT NULL, checkpoint TEXT NOT NULL,
 revision INTEGER NOT NULL CHECK(revision>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0086'));
CREATE TABLE IF NOT EXISTS owned_pk_room_members (
 room INTEGER NOT NULL REFERENCES owned_pk_rooms(id),
 viewer INTEGER NOT NULL CHECK(viewer IN (0,1)),
 account INTEGER NOT NULL, character INTEGER NOT NULL UNIQUE,
 session INTEGER NOT NULL UNIQUE, world_generation INTEGER NOT NULL CHECK(world_generation>0),
 battle_generation INTEGER NOT NULL CHECK(battle_generation>=0),
 PRIMARY KEY(room,viewer));
CREATE TABLE IF NOT EXISTS owned_pk_room_outbox (
 room INTEGER NOT NULL REFERENCES owned_pk_rooms(id),
 revision INTEGER NOT NULL CHECK(revision>0), viewer INTEGER NOT NULL CHECK(viewer IN (0,1)),
 logical BLOB NOT NULL CHECK(length(logical)>0),
 submitted INTEGER NOT NULL DEFAULT 0 CHECK(submitted IN (0,1)),
 PRIMARY KEY(room,revision,viewer));
)SQL";
constexpr const char* round_schema=R"SQL(
CREATE TABLE IF NOT EXISTS owned_pk_round_feature (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 version INTEGER NOT NULL CHECK(version=1), design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0086'));
CREATE TABLE IF NOT EXISTS owned_pk_room_rounds (
 room INTEGER PRIMARY KEY REFERENCES owned_pk_rooms(id),
 revision INTEGER NOT NULL CHECK(revision>0), document TEXT NOT NULL);
)SQL";
std::string definition_document(const NativeSkillRecord& r){
    const auto& s=r.source;
    return Json{{"source",Json::array({s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,
        s.native_image_sha256,s.source_section,s.loader_rva,s.lookup_rva,s.row_count})},
        {"source_record_index",r.source_record_index},{"source_offset",r.source_offset},
        {"record_sha256",r.record_sha256},{"raw_record",r.raw_record},
        {"kind",r.kind},{"definition_id",r.definition_id}}.dump();
}
std::string normalize_ddl(std::string_view input){
    std::string result;
    for(char c:input){
        if(c==' '||c=='\t'||c=='\n'||c=='\r'||c==';')continue;
        result.push_back(c>='A'&&c<='Z'?static_cast<char>(c-'A'+'a'):c);
    }
    const auto optional=result.find("ifnotexists");
    if(optional!=std::string::npos)result.erase(optional,11);
    return result;
}
void require_ddl(sqlite3* db,std::string_view schema,const char* name){
    const auto prefix=std::string("CREATE TABLE IF NOT EXISTS ")+name+" (";
    const auto start=schema.find(prefix),end=schema.find(';',start);
    if(start==std::string::npos||end==std::string::npos)throw DatabaseError("PK round source DDL missing");
    Statement q(db,"SELECT sql FROM sqlite_master WHERE type='table' AND name=?");q.bind(1,std::string(name));
    if(!q.row()||normalize_ddl(q.text(0))!=normalize_ddl(schema.substr(start,end-start)))
        throw DatabaseError("PK round table schema mismatch");
    Statement trigger(db,"SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name=?");trigger.bind(1,std::string(name));
    if(trigger.row())throw DatabaseError("Unexpected PK round table trigger");
}
void changed(sqlite3* db){if(sqlite3_changes(db)!=1)throw DatabaseError("PK compare-and-swap conflict");}
void replies_valid(const SqliteOwnedPkRoomRepository::Replies& replies){
    for(const auto& bytes:replies)
        if(bytes.empty()||bytes.size()>RecoveredWorldFrame::max_logical_size)
            throw DatabaseError("PK requires two bounded nonempty logical projections");
}
void checkpoint_owned_pair(const SqliteOwnedPkRoomRepository::Input& input,
                           const BattleCheckpoint& before,const BattleCheckpoint& after){
    // This owned entry is still built under the existing legacy policy. Codec
    // support for v2 alone does not authorize a different numeric profile.
    if(before.version!=1 || before.snapshot.numeric_profile!=BattleNumericProfile::LegacyCustom ||
       after.version!=before.version || after.snapshot.numeric_profile!=before.snapshot.numeric_profile)
        throw DatabaseError("PK checkpoint numeric profile changed or is unqualified");
    for(std::size_t i=0;i<28;++i){
        const bool owned=i==0||i==14;
        if(before.snapshot.actors[i].has_value()!=owned||after.snapshot.actors[i].has_value()!=owned)
            throw DatabaseError("PK checkpoint actor topology changed");
        if(owned){
            const auto& original=input.actors[i/14];
            auto prior=*before.snapshot.actors[i],next=*after.snapshot.actors[i];
            prior.hp=next.hp=original.hp;prior.mp=next.mp=original.mp;
            if(prior!=original||next!=original)
                throw DatabaseError("PK checkpoint changed actor authority outside HP/MP");
        }
    }
}
}
void SqliteOwnedPkRoomRepository::require_schema(sqlite3* db){
    const std::string schema(feature_schema);
    for(const auto* name:{"owned_pk_room_feature","owned_pk_rooms","owned_pk_room_members","owned_pk_room_outbox"}){
        const auto prefix=std::string("CREATE TABLE IF NOT EXISTS ")+name+" (";
        const auto start=schema.find(prefix),end=schema.find(';',start);
        if(start==std::string::npos||end==std::string::npos)throw DatabaseError("PK source schema definition missing");
        Statement q(db,"SELECT sql FROM sqlite_master WHERE type='table' AND name=?");q.bind(1,std::string(name));
        if(!q.row()||normalize_ddl(q.text(0))!=normalize_ddl(std::string_view(schema).substr(start,end-start)))
            throw DatabaseError("PK feature table schema mismatch");
        Statement trigger(db,"SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name=?");trigger.bind(1,std::string(name));
        if(trigger.row())throw DatabaseError("Unexpected PK feature table trigger");
    }
    Statement version(db,"SELECT version,design_id FROM owned_pk_room_feature WHERE singleton=1");
    if(!version.row()||version.integer(0)!=1||version.text(1)!="CUSTOM-0086")
        throw DatabaseError("PK feature schema mismatch");
}
void SqliteOwnedPkRoomRepository::install_schema(sqlite3* db){
    Transaction tx(db);
    // No installation into the formal database in the connection phase.
    // AUTOINCREMENT and retained terminal/abandoned rows prevent reuse of a
    // previously returned ID across ordinary process restarts. An old DB
    // restore needs a NEW namespace before any offers; it cannot reuse this
    // database's previously issued reservation contexts.
    sqlite_detail::execute(db,feature_schema);
    sqlite_detail::execute(db,"INSERT OR IGNORE INTO owned_pk_room_feature(singleton,version,design_id) VALUES(1,1,'CUSTOM-0086')");
    require_schema(db);
    tx.commit();
}
void SqliteOwnedPkRoomRepository::require_round_schema(sqlite3* db){
    require_schema(db);
    for(const auto* name:{"owned_pk_round_feature","owned_pk_room_rounds"})require_ddl(db,round_schema,name);
    Statement q(db,"SELECT version,design_id FROM owned_pk_round_feature WHERE singleton=1");
    if(!q.row()||q.integer(0)!=1||q.text(1)!="CUSTOM-0086")throw DatabaseError("PK round feature version mismatch");
}
void SqliteOwnedPkRoomRepository::install_round_schema(sqlite3* db){
    Transaction tx(db);require_schema(db);
    sqlite_detail::execute(db,round_schema);
    sqlite_detail::execute(db,"INSERT OR IGNORE INTO owned_pk_round_feature(singleton,version,design_id) VALUES(1,1,'CUSTOM-0086')");
    require_round_schema(db);tx.commit();
}
void SqliteOwnedPkRoomRepository::validate(const Input& in){
    const auto& a=in.pair.challenger;const auto& b=in.pair.recipient;
    if(!a.session||!b.session||a.session==b.session||!a.account||!b.account||
       !a.character||!b.character||a.character==b.character||a.character>0xfff||b.character>0xfff||
       !a.world_generation||!b.world_generation||!a.ready||!b.ready||a.blocked||b.blocked||
       a.position.area!=b.position.area||a.position.scene!=b.position.scene||
       !a.position.revision||!b.position.revision||
       a.battle_generation>=static_cast<std::uint64_t>(INT64_MAX)||
       b.battle_generation>=static_cast<std::uint64_t>(INT64_MAX)||
       in.entry.characters()!=std::array<std::uint64_t,2>{a.character,b.character})
        throw DatabaseError("Invalid PK owned pair");
    if(in.profile_readset_sha256.size()!=64||!std::all_of(in.profile_readset_sha256.begin(),in.profile_readset_sha256.end(),
       [](char c){return (c>='0'&&c<='9')||(c>='a'&&c<='f');}))
        throw DatabaseError("PK profile readset requires an explicit SHA256 binding");
    if(!in.entry.waiting_control()||!OwnedPkRound::masks_valid(in.initial_control_masks))
        throw DatabaseError("PK persistent rounds require a waiting entry and qualified initial masks");
    if(in.entry.initial_notification_bounds()&&
       in.initial_control_masks!=*in.entry.initial_notification_bounds())
        throw DatabaseError("PK notification entry requires its exact retained roster bounds");
    replies_valid(in.entry.records());
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?a:b;const auto& r=in.resources[i];const auto& actor=in.actors[i];
        const auto role=RecoveredRoleLevel::parse(in.roles[i].logical);
        const auto legacy=r.legacy_vitals();
        if(!r.revision||r.design_id!="CUSTOM-0012"||!r.hp||r.hp>r.max_hp||r.mp>r.max_mp||
           !in.roles[i].revision||in.roles[i].design_id!="CUSTOM-0013"||!role||
           !role->level()||role->max_hp()!=r.max_hp||role->max_mp()!=r.max_mp||
           !legacy||in.entry.resources()[i]!=*legacy||
           in.entry.levels()[i]!=role->level()||
           actor.position!=(i==0?0:14)||actor.controller!=p.character||
           actor.hp!=r.hp||actor.max_hp!=r.max_hp||actor.mp!=r.mp||actor.max_mp!=r.max_mp)
            throw DatabaseError("PK actors must match both saved owner readsets");
    }
    if(in.combat_sources){
        if(!in.entry.owned_appearances())throw DatabaseError("PK combat requires its exact owned appearance sources");
        for(std::size_t i=0;i<2;++i){
            const auto& source=(*in.combat_sources)[i];const auto& rows=source.material();
            if(source.appearance()!=(*in.entry.owned_appearances())[i]||in.resources[i]!=rows.resources||
               in.roles[i]!=rows.role||in.actors[i]!=source.actor(static_cast<std::uint8_t>(i*14)))
                throw DatabaseError("PK combat must consume complete privately retained source values");
        }
        if(in.profile_readset_sha256!=owned_combat_profile_digest(readset(in)))
            throw DatabaseError("PK owned combat digest does not bind the complete retained material");
    }
    if(in.entry.owned_players()){
        if(!in.combat_sources||!in.entry.player_identities())
            throw DatabaseError("PK owned player entry requires complete private combat and identity material");
        const auto& sources=*in.entry.owned_players();
        for(std::size_t i=0;i<2;++i)if(sources[i].combat()!=(*in.combat_sources)[i])
            throw DatabaseError("PK player entry must consume the exact privately retained combat source");
        const auto page0=sources[0].recipient_codepage(),page1=sources[1].recipient_codepage();
        const RecoveredPkEntryProjection::PlayerIdentities expected{
            RecoveredBattleIdentity::encode_logical(sources[0].identity(0,page0)),
            RecoveredBattleIdentity::encode_logical(sources[1].identity(14,page0)),
            RecoveredBattleIdentity::encode_logical(sources[1].identity(0,page1)),
            RecoveredBattleIdentity::encode_logical(sources[0].identity(14,page1))};
        if(*in.entry.player_identities()!=expected)
            throw DatabaseError("PK player identity bytes do not match their exact recipient sources");
    }
    if(in.entry.owned_vitals()){
        // CUSTOM-0109 private actual268 resources, not caller templates. Full
        // six ignored-byte canonicalization is explicit custom serialization.
        if(!in.combat_sources||!in.entry.owned_players()||!in.entry.vital_templates())
            throw DatabaseError("PK owned vitals require exact private combat/player material");
        const auto& sources=*in.entry.owned_vitals();
        RecoveredPkEntryProjection::VitalTemplates expected{};
        for(std::size_t i=0;i<2;++i){
            if(sources[i].combat()!=(*in.combat_sources)[i]||
               sources[i].combat()!=(*in.entry.owned_players())[i].combat())
                throw DatabaseError("PK vital source does not match the exact retained combat receipt");
            expected[i]={RecoveredBattleVitals::encode_logical(sources[i].hp()),
                         RecoveredBattleVitals::encode_logical(sources[i].mp())};
        }
        if(*in.entry.vital_templates()!=expected)
            throw DatabaseError("PK complete vital templates do not match the private producer");
        // Check the actual complete per-view stream, in addition to retained
        // templates. Both own HP/MP and opposite HP must consume the producer;
        // side1 MP is deliberately absent because the native path ignores it.
        constexpr auto own_hp=RecoveredBattleEntry::logical_size+
            2*RecoveredBattlePlayerAppearance::logical_size+RecoveredBattleIdentity::logical_size;
        constexpr auto own_mp=own_hp+RecoveredBattleVitals::logical_size;
        constexpr auto other_hp=own_mp+RecoveredBattleVitals::logical_size+RecoveredBattleIdentity::logical_size;
        constexpr auto total=other_hp+RecoveredBattleVitals::logical_size+RecoveredBattleVitalsBatch::logical_size;
        for(std::size_t viewer=0;viewer<2;++viewer){
            const auto& bytes=in.entry.records()[viewer];
            auto other=expected[1-viewer][0];other[2]=14;
            if(bytes.size()!=total||
               !std::equal(expected[viewer][0].begin(),expected[viewer][0].end(),bytes.begin()+own_hp)||
               !std::equal(expected[viewer][1].begin(),expected[viewer][1].end(),bytes.begin()+own_mp)||
               !std::equal(other.begin(),other.end(),bytes.begin()+other_hp))
                throw DatabaseError("PK actual relative entry does not consume complete private vital records");
        }
    }else if(in.entry.vital_templates()){
        throw DatabaseError("PK derived vital templates lack their private source");
    }
    if(in.entry.owned_initial_grants()){
        // CUSTOM-0110 initial primary UI control only. It grants no learned
        // skill, hit target, damage rule, server turn or later-round authority.
        if(!in.combat_sources||!in.entry.owned_players()||!in.entry.owned_vitals())
            throw DatabaseError("PK initial grants require exact private player/vital/combat sources");
        for(std::size_t i=0;i<2;++i){
            const auto& source=(*in.entry.owned_initial_grants())[i];
            if(source.player()!=(*in.entry.owned_players())[i]||
               source.player().combat()!=(*in.combat_sources)[i]||
               source.player().combat()!=(*in.entry.owned_vitals())[i].combat()||
               RecoveredBattlePlayerGrant::encode(source.grant())!=in.entry.grants()[i])
                throw DatabaseError("PK initial grant must consume the exact private owned primary source");
        }
    }
    if(in.entry.owned_initial_contexts()){
        // CUSTOM-0111 complete initial82/88 source only. Session-scoped next
        // battle generation is not a global nonce or an official timebase.
        if(!in.combat_sources||!in.entry.owned_players()||!in.entry.owned_vitals()||
           !in.entry.owned_initial_grants())
            throw DatabaseError("PK initial contexts require exact private owned entry sources");
        constexpr auto bulk_offset=RecoveredBattleEntry::logical_size+
            2*RecoveredBattlePlayerAppearance::logical_size+2*RecoveredBattleIdentity::logical_size+
            3*RecoveredBattleVitals::logical_size;
        constexpr auto total=bulk_offset+RecoveredBattleVitalsBatch::logical_size;
        for(std::size_t i=0;i<2;++i){
            const auto& source=(*in.entry.owned_initial_contexts())[i];
            const auto& peer=i==0?a:b;
            const auto& bytes=in.entry.records()[i];
            if(source.player()!=(*in.entry.owned_players())[i]||
               source.vital()!=(*in.entry.owned_vitals())[i]||
               source.player().combat()!=(*in.combat_sources)[i]||
               peer.battle_generation>=UINT32_MAX||
               source.context().context_a!=peer.battle_generation+1||
               in.entry.command_contexts()[i]!=source.context().context_a||
               bytes.size()!=total||
               !std::equal(source.context_bytes().begin(),source.context_bytes().end(),bytes.begin())||
               !std::equal(source.bulk_bytes().begin(),source.bulk_bytes().end(),bytes.begin()+bulk_offset))
                throw DatabaseError("PK actual initial82/88 must consume exact private owned source records");
        }
    }
    // Shared Battle validates four attack/defense widths and actor bounds;
    // no formula, numerical profile, skill or world appearance is invented.
    (void)Battle(1,in.actors,in.seed);
}
std::string SqliteOwnedPkRoomRepository::readset(const Input& in){
    Json peers=Json::array(),resources=Json::array(),roles=Json::array();
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?in.pair.challenger:in.pair.recipient;
        const auto& r=in.resources[i];const auto& role=in.roles[i];
        peers.push_back(Json::array({p.session,p.account,p.character,p.world_generation,p.battle_generation,
            p.position.area,p.position.scene,p.position.x,p.position.y,p.position.revision}));
        resources.push_back(Json::array({r.hp,r.max_hp,r.mp,r.max_mp,r.revision,r.design_id}));
        roles.push_back(Json::array({role.logical,role.revision,role.design_id}));
    }
    // Include exact raw projections, stats, seed and profile binding, not just
    // revisions. Different prepared inputs cannot borrow another ticket.
    const auto canonical=Battle(1,in.actors,in.seed).checkpoint();
    auto result=Json{{"version",1},{"design_id","CUSTOM-0086"},{"peers",peers},
        {"resources",resources},{"roles",roles},{"entry",in.entry.records()},
        {"initial_actor_checkpoint",BattleCheckpointCodec::encode(canonical)},
        {"grants",in.entry.grants()},{"command_contexts",in.entry.command_contexts()},
        {"waiting_control",in.entry.waiting_control()},{"initial_control_masks",in.initial_control_masks},
        {"profile_readset_sha256",in.profile_readset_sha256}};
    if(in.entry.initial_notification_bounds()){
        // Only the new profile adds fields; legacy readset bytes stay intact.
        result["initial_control_mode"]="CUSTOM-0104-bounded-notification";
        result["initial_notification_bounds"]=*in.entry.initial_notification_bounds();
    }
    if(in.entry.fight_sources()){
        // New typed source only: never reinterpret old tickets/readset bytes.
        Json views=Json::array();
        for(const auto& selected:*in.entry.fight_sources()){
            Json rows=Json::array();
            for(std::size_t component=0;component<4;++component){
                const auto& row=selected.row(component);
                rows.push_back(Json{{"component",component},{"record_index",row.record_index},
                    {"source_line",row.line},{"key",row.key},{"historical_fields",row.historical_fields},
                    {"family_byte",row.family_byte},{"derived_ordinal_byte",row.derived_ordinal_byte}});
            }
            views.push_back(Json{{"ordinary86_4",selected.input()},{"selected_rows",rows}});
        }
        result["fight_appearance_source"]=Json{{"representation","pinned-historical-parsed-fields-v1"},
            {"audit_sha256",TaiwanNativeFightCatalog::audit_sha256},
            {"audit_image_sha256",TaiwanNativeFightCatalog::audit_image_sha256},
            {"current_helper_image_sha256",TaiwanNativeFightCatalog::current_image_sha256},
            {"encoded_source_sha256",TaiwanNativeFightCatalog::encoded_sha256},
            {"recorded_decoded_sha256",TaiwanNativeFightCatalog::recorded_decoded_sha256},
            {"relative_views",views}};
    }
    if(in.entry.owned_appearances()){
        Json sources=Json::array();
        for(const auto& source:*in.entry.owned_appearances())sources.push_back(appearance_material(source.material()));
        result["owned_appearance_source"]=Json{{"design_id","CUSTOM-0105"},
            {"projection","raw-owned-DA-packed8-mode1-special0-unused-padding0-v1"},{"sources",sources}};
    }
    if(in.combat_sources){
        Json sources=Json::array();
        for(const auto& source:*in.combat_sources){
            const auto& m=source.material();
            sources.push_back(Json{{"role",Json::array({m.role.logical,m.role.revision,m.role.design_id})},
                {"resources",Json::array({m.resources.hp,m.resources.max_hp,m.resources.mp,m.resources.max_mp,
                    m.resources.revision,m.resources.design_id})},
                {"legacy_auxiliary",Json{{"logical",m.auxiliary.logical},{"revision",m.auxiliary.revision},
                    {"origin_label",m.auxiliary.origin},{"provenance",m.auxiliary.provenance},
                    {"client_sha256",OwnedTaiwanPkCombatSource::legacy_client_pin},
                    {"design_id",OwnedTaiwanPkCombatSource::legacy_design}}}});
        }
        result["owned_combat_source"]=Json{{"design_id","CUSTOM-0106"},
            {"authority","CUSTOM-adoption-of-stored-labeled-legacy-absolute-totals"},
            {"origin_label_is_not_native_proof",true},{"numeric_profile","existing-LegacyCustom-no-clamp"},
            {"skills_authorized",false},{"sources",sources}};
    }
    if(in.entry.owned_players()){
        Json sources=Json::array();
        for(const auto& source:*in.entry.owned_players()){
            const auto& m=source.material();const auto& text=m.secondary;
            sources.push_back(Json{{"primary_source16",m.primary_source},{"primary_codepage",m.primary_codepage},
                {"primary_utf8",m.primary_utf8},{"secondary",Json{{"canonical16",text.text},{"utf8",text.utf8},
                    {"codepage",text.codepage},{"revision",text.revision},{"design_id","CUSTOM-0056"},
                    {"client_sha256","149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"}}},
                {"level",m.level},{"recipient_codepage",source.recipient_codepage()}});
        }
        result["owned_player_entry_source"]=Json{{"design_id","CUSTOM-0107"},
            {"authority","CUSTOM-owned-player-strings-with-explicit-normal-status-policy"},
            {"variant_word",0x2000},{"ordinal_word",0},{"status_dword",0},
            {"native_original_producer_recovered",false},{"sources",sources},
            {"relative_identity45",*in.entry.player_identities()}};
    }
    if(in.entry.owned_vitals()){
        if(!in.entry.vital_templates())throw DatabaseError("PK owned vital readset lacks complete templates");
        result["owned_vital_source"]=Json{{"design_id","CUSTOM-0109"},
            {"authority","CUSTOM-canonical-six-ignored-bytes-from-actual-private268-resources"},
            {"numeric_profile","checked-existing-LegacyCustom-DWORD-no-clamp"},
            {"native_original_producer_recovered",false},{"native_padding_claimed",false},
            {"ignored_bytes_scope","current149c-complete-ordinary86-0-and86-1-receivers-no-record-pointer-escape"},
            {"image_sha256","149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"},
            {"owner_hp_mp_templates",*in.entry.vital_templates()},
            {"combat_sources","exact-private-owned_combat_source-receipts-validated"}};
    }
    if(in.entry.owned_initial_grants()){
        result["owned_initial_grant_source"]=Json{{"design_id","CUSTOM-0110"},
            {"authority","CUSTOM-initial-owned-primary-slot0-control-and-explicit-three-digit-label"},
            {"native_original_producer_recovered",false},{"native_padding_claimed",false},
            {"primary_flags",1},{"owned_relative_slot",0},{"raw_label_word",0},
            {"native_three_digit_result","001"},{"label_is_clock_or_round_claim",false},
            {"canonical_zero_offsets",Json::array({2,7,8,9,10,11,12,13,14,15,16})},
            {"source_grants",in.entry.grants()},
            {"player_sources","exact-private-owned_player_entry_source-receipts-validated"},
            {"schedule","existing-CUSTOM0086-initial-two-notifications-then-grants"},
            {"learned_skills_authorized",false},{"later_rounds_authorized",false}};
    }
    if(in.entry.owned_initial_contexts()){
        Json views=Json::array();
        for(const auto& source:*in.entry.owned_initial_contexts())
            views.push_back(Json{{"prebattle_generation",source.player().combat().appearance().material().battle_generation},
                {"context82",source.context_bytes()},{"friendly88",source.bulk_bytes()}});
        result["owned_initial_context_source"]=Json{{"design_id","CUSTOM-0111"},
            {"authority","CUSTOM-private-Session-next-battle-context-and-initial-friendly-vitals"},
            {"native_original_producer_recovered",false},{"native_padding_claimed",false},
            {"context_a","checked-private-prebattle-generation-plus1-Session-scoped-not-global-nonce"},
            {"context_b",0x1400},{"initial_window_seconds",20},{"initial_counter_dword",0},
            {"raw118",0},{"raw118_policy","zero-four-qualified-operational-display-bits-not-skill-permission"},
            {"bulk_canonical_tail_offsets",Json::array({117,119,120})},
            {"friendly_slots","slot0-exact-owned-current-HP-MP;slots1..13-explicit-empty-placeholder-zero"},
            {"native_pointer_prerequisite","successful-normal82-reset-168-inline-actor-pointers;no-fake-identities"},
            {"original_timer_or_round_rule_claimed",false},{"sources",views},{"initial_only",true}};
    }
    return result.dump();
}
bool SqliteOwnedPkRoomRepository::owners_current(const Input& in){
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?in.pair.challenger:in.pair.recipient;
        if(owners_.load_resources(p.account,p.character)!=std::optional{in.resources[i]}||
           owners_.load_role(p.account,p.character)!=std::optional{in.roles[i]}||
           owners_.load_position(p.account,p.character)!=std::optional{p.position}||
           owners_.owned_pending_battle(p.account,p.character))return false;
    }
    return true;
}
bool SqliteOwnedPkRoomRepository::occupied(std::uint64_t account,std::uint64_t character){
    // Owner lookup applies even if the independent feature has no row.
    (void)owners_.load_resources(account,character);
    Statement q(db_,"SELECT 1 FROM owned_pk_room_members WHERE account=? AND character=?");
    q.bind_id(1,account);q.bind_id(2,character);return q.row();
}
SqliteOwnedPkRoomRepository::Ticket SqliteOwnedPkRoomRepository::prepare_owned(Pair pair,
        RecoveredPkEntryProjection::Prepared entry,OwnedCombatSources sources,std::uint32_t seed,
        OwnedPkRound::Masks initial_control_masks){
    const auto& a=sources[0].material();const auto& b=sources[1].material();
    Input input{std::move(pair),std::move(entry),{a.resources,b.resources},{a.role,b.role},
        {sources[0].actor(0),sources[1].actor(14)},seed,{},initial_control_masks,std::move(sources)};
    // The complete custom entry/material readset produces its own binding.
    // It is not proof of native formulas or any learned/issued skill permission.
    input.profile_readset_sha256=owned_combat_profile_digest(readset(input));
    return prepare(std::move(input));
}
SqliteOwnedPkRoomRepository::Ticket SqliteOwnedPkRoomRepository::prepare(Input input){
    validate(input);
    auto snapshot=std::make_shared<const Input>(std::move(input));
    auto document=readset(*snapshot);
    // Concrete joint Current owns read scopes; keep this OUTSIDE room SQL tx.
    // This preflight is not atomic live-Session/queue/SQL admission.
    if(!owned_appearance_current(*snapshot,db_))throw DatabaseError("PK owned appearance source expired");
    Transaction tx(db_);
    if(!owned_combat_stored_current(*snapshot,db_))throw DatabaseError("PK reserved combat source rows changed");
    if(!owners_current(*snapshot)||occupied(snapshot->pair.challenger.account,snapshot->pair.challenger.character)||
       occupied(snapshot->pair.recipient.account,snapshot->pair.recipient.character))
        throw DatabaseError("PK admission owner readset/occupancy conflict");
    Statement insert(db_,"INSERT INTO owned_pk_rooms(state,readset,checkpoint,revision,design_id) VALUES('reserved',?,'',1,'CUSTOM-0086')");
    insert.bind(1,document);insert.done();
    const auto raw_id=sqlite3_last_insert_rowid(db_);
    if(raw_id<=0)throw DatabaseError("PK durable ID exhausted");
    const auto id=static_cast<std::uint64_t>(raw_id);
    const auto initial=BattleCheckpointCodec::encode(Battle(id,snapshot->actors,snapshot->seed).checkpoint());
    Statement checkpoint(db_,"UPDATE owned_pk_rooms SET checkpoint=? WHERE id=? AND state='reserved'");
    checkpoint.bind(1,initial);checkpoint.bind_id(2,id);checkpoint.done();changed(db_);
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?snapshot->pair.challenger:snapshot->pair.recipient;
        Statement member(db_,"INSERT INTO owned_pk_room_members(room,viewer,account,character,session,world_generation,battle_generation) VALUES(?,?,?,?,?,?,?)");
        member.bind_id(1,id);member.bind_id(2,i);member.bind_id(3,p.account);member.bind_id(4,p.character);
        member.bind_id(5,p.session);member.bind_id(6,p.world_generation);member.bind_id(7,p.battle_generation);member.done();
    }
    Ticket ticket(id,std::move(snapshot),std::move(document),issuer_);
    tx.commit();return ticket;
}
void SqliteOwnedPkRoomRepository::require_ticket(const Ticket& ticket,const char* state){
    // RESERVED alone rechecks all admitted source SQL tuples. Active Battle
    // retains immutable selected stats; no old world/aux current is required.
    if(std::string_view(state)=="reserved"&&!owned_combat_stored_current(ticket.input(),db_))
        throw DatabaseError("PK reserved combat source rows changed");
    Statement q(db_,"SELECT state,readset,design_id FROM owned_pk_rooms WHERE id=?");q.bind_id(1,ticket.id());
    if(!q.row()||q.text(0)!=state||q.text(1)!=ticket.readset_||q.text(2)!="CUSTOM-0086"||
       !owners_current(ticket.input()))throw DatabaseError("PK stale room ticket/owner readset");
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?ticket.input().pair.challenger:ticket.input().pair.recipient;
        Statement m(db_,"SELECT account,character,session,world_generation,battle_generation FROM owned_pk_room_members WHERE room=? AND viewer=?");
        m.bind_id(1,ticket.id());m.bind_id(2,i);
        if(!m.row()||m.number<std::uint64_t>(0)!=p.account||m.number<std::uint64_t>(1)!=p.character||
           m.number<std::uint64_t>(2)!=p.session||m.number<std::uint64_t>(3)!=p.world_generation||
           m.number<std::uint64_t>(4)!=p.battle_generation)throw DatabaseError("PK owner lock mismatch");
    }
}
bool SqliteOwnedPkRoomRepository::current(const Ticket& ticket){
    if(!owned_appearance_current(ticket.input(),db_))return false;
    Transaction tx(db_);
    try{require_ticket(ticket,"reserved");}catch(const DatabaseError&){return false;}
    tx.commit();return true;
}
std::string SqliteOwnedPkRoomRepository::require_active_owned_profile(
        const Ticket& ticket,const BattleCheckpoint& supplied_expected){
    const auto expected=supplied_expected;
    RecoveryRead scope(db_);
    auto digest=require_active_owned_profile_in_scope(ticket,expected);
    scope.commit();
    return digest;
}
std::string SqliteOwnedPkRoomRepository::require_active_owned_profile_in_scope(
        const Ticket& ticket,const BattleCheckpoint& supplied_expected){
    if(sqlite3_get_autocommit(db_))throw DatabaseError("PK active profile requires an existing snapshot scope");
    // CUSTOM-0119 active combat keeps its admitted stat/text/appearance
    // readset. RESERVED stored_current/live world Current must NOT run here.
    const auto expected=supplied_expected;
    const auto& input=ticket.input();
    if(!issuer_||ticket.issuer_!=issuer_||!input.combat_sources||
       !input.entry.owned_appearances()||!input.entry.owned_players()||
       !input.entry.owned_vitals()||!input.entry.owned_initial_grants()||
       !input.entry.owned_initial_contexts())
        throw DatabaseError("PK active profile requires original complete private owned input");
    for(std::size_t i=0;i<2;++i)
        if(!(*input.combat_sources)[i].uses_connection(db_)||
           !(*input.entry.owned_appearances())[i].uses_connection(db_)||
           !(*input.entry.owned_players())[i].uses_connection(db_)||
           !(*input.entry.owned_vitals())[i].uses_connection(db_)||
           !(*input.entry.owned_initial_grants())[i].uses_connection(db_)||
           !(*input.entry.owned_initial_contexts())[i].uses_connection(db_))
            throw DatabaseError("PK active profile private sources use another connection");
    validate(input); // Complete retained graph and internally recomputed digest.
    if(readset(input)!=ticket.readset_)
        throw DatabaseError("PK active profile retained readset changed");
    // Existing readers use unqualified names: bind them to the real main
    // tables and reject TEMP substitutes before any owner/round lookup.
    require_owned_main_sources(db_);
    require_round_schema(db_); // Read-only own DDL/version checks, no install.
    require_ticket(ticket,"active");
    Statement members(db_,"SELECT COUNT(*) FROM main.owned_pk_room_members WHERE room=?");
    members.bind_id(1,ticket.id());
    if(!members.row()||members.integer(0)!=2||members.row())
        throw DatabaseError("PK active profile requires both exact member locks");
    Statement room(db_,"SELECT checkpoint,revision FROM main.owned_pk_rooms WHERE id=? AND state='active'");
    room.bind_id(1,ticket.id());
    if(!room.row())throw DatabaseError("PK active profile room is absent");
    const auto checkpoint=BattleCheckpointCodec::decode(room.text(0));
    if(checkpoint!=expected||checkpoint.snapshot.id!=ticket.id()||
       checkpoint.snapshot.revision!=room.number<std::uint64_t>(1)||
       checkpoint.snapshot.state!=BattleState::Active||room.row())
        throw DatabaseError("PK active profile differs from the actual runtime checkpoint");
    (void)Battle::restore(checkpoint); // Full canonical RNG/state, no reseeding.
    const auto initial=Battle(ticket.id(),input.actors,input.seed).checkpoint();
    checkpoint_owned_pair(input,initial,checkpoint);
    if(checkpoint.snapshot.revision==1&&checkpoint!=initial)
        throw DatabaseError("PK active profile initial checkpoint changed");
    const auto phase=read_round(ticket); // Same snapshot, full headers/bounds.
    if(phase.battle_revision()!=checkpoint.snapshot.revision||
       phase.phase()==OwnedPkRound::Phase::Terminal)
        throw DatabaseError("PK active profile round does not match its active checkpoint");
    return input.profile_readset_sha256; // Qualified frozen binding, not a lease.
}
SqliteOwnedPkRoomRepository::RuntimeClaim SqliteOwnedPkRoomRepository::claim_runtime(const Ticket& ticket){
    if(!issuer_||ticket.issuer_!=issuer_)throw DatabaseError("PK runtime claim requires its original repository issuer");
    // Registry exclusion alone does not make this repository/SQLite/RoomState
    // thread-safe: their actual single-game-executor contract still applies.
    // Remove only expired entries; a live claim is never displaced or shared.
    const std::lock_guard lock(issuer_->mutex);
    for(auto at=issuer_->claims.begin();at!=issuer_->claims.end();)
        if(at->second.expired())at=issuer_->claims.erase(at);else ++at;
    if(issuer_->claims.contains(ticket.id()))throw DatabaseError("PK room already has a mutable runtime owner");
    auto owner=std::make_shared<const RuntimeOwner>();
    issuer_->claims.emplace(ticket.id(),owner);
    return RuntimeClaim(std::move(owner));
}
SqliteOwnedPkRoomRepository::RetainedRecovery SqliteOwnedPkRoomRepository::recover_retained(const Ticket& ticket){
    if(!issuer_||ticket.issuer_!=issuer_)throw DatabaseError("PK recovery requires its original repository issuer");
    // Private retained input and persisted full readset, not a supplied digest
    // or new world qualification. Active admission material remains frozen.
    if(readset(ticket.input())!=ticket.readset_)throw DatabaseError("PK retained input/readset mismatch");
    RecoveryRead scope(db_);
    Statement room(db_,"SELECT state,checkpoint,revision FROM owned_pk_rooms WHERE id=?");room.bind_id(1,ticket.id());
    if(!room.row())throw DatabaseError("PK retained room missing");
    const auto state=room.text(0),checkpoint_text=room.text(1);
    const auto revision=room.number<std::uint64_t>(2);
    if(state!="active"&&state!="finished")throw DatabaseError("PK retained recovery requires active or finished state");
    require_ticket(ticket,state.c_str());
    Statement count(db_,"SELECT COUNT(*) FROM owned_pk_room_members WHERE room=?");count.bind_id(1,ticket.id());
    if(!count.row()||count.integer(0)!=2)throw DatabaseError("PK recovery requires both exact owner locks");
    auto checkpoint=BattleCheckpointCodec::decode(checkpoint_text);
    if(checkpoint.snapshot.id!=ticket.id()||checkpoint.snapshot.revision!=revision)
        throw DatabaseError("PK retained checkpoint identity/revision mismatch");
    (void)Battle::restore(checkpoint); // Preserve full canonical RNG, never reseed/replay.
    const auto initial_checkpoint=Battle(ticket.id(),ticket.input().actors,ticket.input().seed).checkpoint();
    checkpoint_owned_pair(ticket.input(),initial_checkpoint,checkpoint);
    if(revision==1&&checkpoint!=initial_checkpoint)
        throw DatabaseError("PK retained revision1 differs from original checkpoint/RNG");
    auto phase=read_round(ticket); // Same read snapshot; headers, bounds and durable state.
    const auto phase_document=Json::parse(phase.document());
    std::vector<RetainedOutbox> outboxes;
    std::array<bool,2> latest_submitted{};
    Statement rows(db_,"SELECT revision,viewer,logical,submitted FROM owned_pk_room_outbox WHERE room=? ORDER BY revision,viewer");
    rows.bind_id(1,ticket.id());
    std::uint64_t previous=0,current=0;std::size_t total_bytes=0;
    std::uint8_t expected_viewer=0;
    while(rows.row()){
        const auto row_revision=rows.number<std::uint64_t>(0);
        const auto viewer=rows.number<std::uint8_t>(1);
        const auto submitted=rows.number<std::uint8_t>(3);
        if(!row_revision||row_revision>revision||viewer!=expected_viewer||submitted>1)
            throw DatabaseError("PK retained outbox identity/pair mismatch");
        if(viewer==0){
            if((!previous&&row_revision!=1)||(previous&&(row_revision<=previous||row_revision-previous>2)))
                throw DatabaseError("PK retained outbox revision history mismatch");
            current=row_revision;
        }else if(row_revision!=current)throw DatabaseError("PK retained outbox pair revision mismatch");
        const auto blob=rows.blob(2,1,RecoveredWorldFrame::max_logical_size);
        std::vector<std::uint8_t> bytes(blob.begin(),blob.end());
        if(bytes.size()>std::numeric_limits<std::size_t>::max()-total_bytes)
            throw DatabaseError("PK retained outbox aggregate size overflow");
        total_bytes+=bytes.size();
        if(row_revision==1&&bytes!=ticket.input().entry.records()[viewer])
            throw DatabaseError("PK retained initial outbox differs from original Prepared");
        if(row_revision<revision&&!submitted)throw DatabaseError("PK older outbox was not submitted before settlement");
        if(row_revision==revision)latest_submitted[viewer]=submitted!=0;
        const auto& peer=viewer==0?ticket.input().pair.challenger:ticket.input().pair.recipient;
        outboxes.push_back({Delivery{ticket.id(),row_revision,peer.session,peer.world_generation,
            peer.battle_generation+1,viewer,std::move(bytes)},submitted!=0});
        expected_viewer=static_cast<std::uint8_t>(1-viewer);
        if(viewer==1)previous=row_revision;
    }
    if(outboxes.empty()||expected_viewer!=0||previous!=revision)
        throw DatabaseError("PK retained outbox lacks complete current revision");
    for(std::size_t viewer=0;viewer<2;++viewer){
        const bool received=phase_document.at("controls").at(viewer).get<bool>();
        const bool needs_both=phase.phase()==OwnedPkRound::Phase::Grants||
            phase.phase()==OwnedPkRound::Phase::Collect||phase.phase()==OwnedPkRound::Phase::Ready;
        if((received||needs_both)&&!latest_submitted[viewer])
            throw DatabaseError("PK retained round control precedes own outbox submission");
    }
    RetainedRecovery result(ticket,std::move(checkpoint),std::move(phase),std::move(outboxes));
    scope.commit();return result;
}
bool SqliteOwnedPkRoomRepository::retained_recovery_current(const RetainedRecovery& snapshot){
    try{
        const auto now=recover_retained(snapshot.ticket_);
        if(now.checkpoint_!=snapshot.checkpoint_||now.round_.document()!=snapshot.round_.document()||
           now.outboxes_.size()!=snapshot.outboxes_.size())return false;
        for(std::size_t i=0;i<now.outboxes_.size();++i){
            const auto& a=now.outboxes_[i];const auto& b=snapshot.outboxes_[i];
            if(a.submitted!=b.submitted||a.delivery.room!=b.delivery.room||a.delivery.revision!=b.delivery.revision||
               a.delivery.viewer!=b.delivery.viewer||a.delivery.session!=b.delivery.session||
               a.delivery.world_generation!=b.delivery.world_generation||a.delivery.battle_generation!=b.delivery.battle_generation||
               a.delivery.logical!=b.delivery.logical)return false;
        }
        return true;
    }catch(const DatabaseError&){return false;}
     catch(const std::invalid_argument&){return false;}
     catch(const Json::exception&){return false;}
}
BattleCheckpoint SqliteOwnedPkRoomRepository::initial(const Ticket& ticket){
    if(!owned_appearance_current(ticket.input(),db_))throw DatabaseError("PK owned appearance source expired");
    Transaction tx(db_);require_ticket(ticket,"reserved");
    Statement q(db_,"SELECT checkpoint,revision FROM owned_pk_rooms WHERE id=?");q.bind_id(1,ticket.id());
    if(!q.row()||q.integer(1)!=1)throw DatabaseError("PK initial checkpoint mismatch");
    const auto result=BattleCheckpointCodec::decode(q.text(0));
    if(result!=Battle(ticket.id(),ticket.input().actors,ticket.input().seed).checkpoint())
        throw DatabaseError("PK initial checkpoint/input mismatch");
    tx.commit();return result;
}
void SqliteOwnedPkRoomRepository::enqueue(const Ticket& ticket,std::uint64_t revision,const Replies& replies){
    replies_valid(replies);
    for(std::size_t i=0;i<2;++i){
        Statement q(db_,"INSERT INTO owned_pk_room_outbox(room,revision,viewer,logical) VALUES(?,?,?,?)");
        q.bind_id(1,ticket.id());q.bind_id(2,revision);q.bind_id(3,i);q.bind_blob(4,replies[i]);q.done();
    }
}
void SqliteOwnedPkRoomRepository::activate(const Ticket& ticket){
    if(!owned_appearance_current(ticket.input(),db_))throw DatabaseError("PK owned appearance source expired");
    Transaction tx(db_);require_ticket(ticket,"reserved");
    const auto expected=BattleCheckpointCodec::encode(Battle(ticket.id(),ticket.input().actors,ticket.input().seed).checkpoint());
    Statement q(db_,"UPDATE owned_pk_rooms SET state='active' WHERE id=? AND state='reserved' AND revision=1 AND checkpoint=?");
    q.bind_id(1,ticket.id());q.bind(2,expected);q.done();changed(db_);
    const auto& contexts=ticket.input().entry.command_contexts();
    const auto headers=std::array{OwnedPkRound::Header{0,0,contexts[0]},OwnedPkRound::Header{0,0,contexts[1]}};
    const auto round=ticket.input().entry.initial_notification_bounds()
        ?OwnedPkRound::waiting_notification(headers,*ticket.input().entry.initial_notification_bounds(),1)
        :OwnedPkRound::waiting(headers,ticket.input().initial_control_masks,1);
    Statement phase(db_,"INSERT INTO owned_pk_room_rounds(room,revision,document) VALUES(?,?,?)");
    phase.bind_id(1,ticket.id());phase.bind_id(2,round.revision());phase.bind(3,round.document());phase.done();
    enqueue(ticket,1,ticket.input().entry.records());tx.commit();
}
void SqliteOwnedPkRoomRepository::advance(const Ticket& ticket,const BattleCheckpoint& expected,
    const BattleCheckpoint& next,const Replies& replies,const std::optional<NativeSkillRecord>& definition){
    const auto before=BattleCheckpointCodec::encode(expected),after=BattleCheckpointCodec::encode(next);
    if(expected.snapshot.id!=ticket.id()||next.snapshot.id!=ticket.id()||expected.snapshot.state!=BattleState::Active||
       expected.snapshot.revision>=static_cast<std::uint64_t>(INT64_MAX)||
       next.snapshot.revision!=expected.snapshot.revision+1)
        throw DatabaseError("PK shared checkpoint transition mismatch");
    checkpoint_owned_pair(ticket.input(),expected,next);
    Transaction tx(db_);require_ticket(ticket,"active");
    // The historical trusted one-action primitive must never bypass the new
    // two-owner collection state. A paired resolver/checkpoint/round commit
    // remains required before these rooms can advance battle HP/MP.
    Statement collected(db_,"SELECT 1 FROM owned_pk_room_rounds WHERE room=?");collected.bind_id(1,ticket.id());
    if(collected.row())throw DatabaseError("PK collection room requires atomic two-intent resolution");
    if(definition){
        if(definition->kind<0||definition->kind>1||definition->definition_id<1||definition->definition_id>255)
            throw DatabaseError("PK scalar definition selector is outside the native branch");
        const auto key=static_cast<std::uint16_t>((static_cast<std::uint16_t>(definition->kind)<<8)|
                                                static_cast<std::uint16_t>(definition->definition_id));
        if(scalar_definition(key)!=*definition)throw DatabaseError("PK native scalar definition readset changed");
    }
    Statement waiting(db_,"SELECT count(*) FROM owned_pk_room_outbox WHERE room=? AND submitted=0");waiting.bind_id(1,ticket.id());
    if(!waiting.row()||waiting.integer(0)!=0)throw DatabaseError("PK previous dual-view transport submission is pending");
    Statement q(db_,"UPDATE owned_pk_rooms SET checkpoint=?,revision=?,state=? WHERE id=? AND state='active' AND revision=? AND checkpoint=?");
    q.bind(1,after);q.bind_id(2,next.snapshot.revision);q.bind(3,next.snapshot.state==BattleState::Finished?std::string("finished"):std::string("active"));
    q.bind_id(4,ticket.id());q.bind_id(5,expected.snapshot.revision);q.bind(6,before);q.done();changed(db_);
    enqueue(ticket,next.snapshot.revision,replies);tx.commit();
    // No character_resources/role/experience mutation, no release of either
    // owner lock on a terminal checkpoint. A qualified terminal/re-entry
    // adapter must first be implemented; no fabricated89/24 here.
}
void SqliteOwnedPkRoomRepository::settle(const Ticket& ticket,const BattleCheckpoint& expected,
    const BattleCheckpoint& next,const OwnedPkRound& expected_round,
    const OwnedPkRound& next_round,const Replies& replies){
    if(expected_round.phase()!=OwnedPkRound::Phase::Ready||
       expected.snapshot.id!=ticket.id()||next.snapshot.id!=ticket.id()||
       expected.snapshot.state!=BattleState::Active||
       expected_round.battle_revision()!=expected.snapshot.revision||
       expected.snapshot.revision>=static_cast<std::uint64_t>(INT64_MAX)-1||
       next.snapshot.revision<=expected.snapshot.revision||
       next.snapshot.revision-expected.snapshot.revision>2||
       (next.snapshot.state!=BattleState::Active&&next.snapshot.state!=BattleState::Finished))
        throw DatabaseError("PK paired settlement checkpoint/round mismatch");
    auto derived=expected_round;
    const bool advanced=next_round.result_notification_bounds()?derived.results_issued_notification(next.snapshot):
        derived.results_issued(next.snapshot.revision,next_round.masks(),next.snapshot.state==BattleState::Finished);
    if(advanced&&next_round.terminal_notification()&&!derived.issue_terminal_notification())
        throw DatabaseError("PK terminal notification policy did not derive from the owned result phase");
    if(!advanced||derived.document()!=next_round.document())
        throw DatabaseError("PK result phase did not derive from both collected intents");
    checkpoint_owned_pair(ticket.input(),expected,next);
    // Reject malformed/corrupt outcome and RNG before durable publication.
    (void)Battle::restore(expected);(void)Battle::restore(next);
    replies_valid(replies);
    if(next_round.terminal_notification()){
        const auto terminal=OwnedTaiwanPkTerminalSource::prepare(ticket,next.snapshot,next_round);
        for(const auto& reply:replies)
            if(!RecoveredTaiwanPkTerminalNotification::matches_result_sequence(reply)||
               !std::equal(terminal.begin(),terminal.end(),reply.end()-terminal.size()))
                throw DatabaseError("PK terminal notification is not the privately derived final outbox tail");
    }
    const auto before=BattleCheckpointCodec::encode(expected),after=BattleCheckpointCodec::encode(next);
    Transaction tx(db_);require_ticket(ticket,"active");
    // Explicit v3 upgrade must qualify the complete original private graph
    // BEFORE any durable writes, including its first v2->v3 transition.
    if(next_round.result_notification_bounds())
        (void)require_active_owned_profile_in_scope(ticket,expected);
    if(read_round(ticket).document()!=expected_round.document())
        throw DatabaseError("PK paired settlement phase is stale");
    Statement pending(db_,"SELECT count(*) FROM owned_pk_room_outbox WHERE room=? AND submitted=0");
    pending.bind_id(1,ticket.id());
    if(!pending.row()||pending.integer(0)!=0)
        throw DatabaseError("PK prior two-view enqueue submissions are pending");
    for(const auto& intent:expected_round.intents()){
        if(!intent)throw DatabaseError("PK settlement lacks collected owner intent");
        if(intent->skill_key&&intent->definition_readset!=scalar_definition_document(*intent->skill_key))
            throw DatabaseError("PK skill definition changed before paired settlement");
    }
    Statement phase(db_,"UPDATE owned_pk_room_rounds SET revision=?,document=? WHERE room=? AND revision=? AND document=?");
    phase.bind_id(1,next_round.revision());phase.bind(2,next_round.document());phase.bind_id(3,ticket.id());
    phase.bind_id(4,expected_round.revision());phase.bind(5,expected_round.document());phase.done();changed(db_);
    Statement room(db_,"UPDATE owned_pk_rooms SET checkpoint=?,revision=?,state=? WHERE id=? AND state='active' AND revision=? AND checkpoint=?");
    room.bind(1,after);room.bind_id(2,next.snapshot.revision);
    room.bind(3,next.snapshot.state==BattleState::Finished?std::string("finished"):std::string("active"));
    room.bind_id(4,ticket.id());room.bind_id(5,expected.snapshot.revision);room.bind(6,before);
    room.done();changed(db_);
    enqueue(ticket,next.snapshot.revision,replies);tx.commit();
    // Terminal stays locked. CUSTOM-0126 only appends its qualified no-message
    // notification; saved-resource/re-entry/original award policies remain open.
}
NativeSkillRecord SqliteOwnedPkRoomRepository::scalar_definition(std::uint16_t key){
    const auto kind=key>>8,id=key&0xff;
    if(kind>1||!id)throw DatabaseError("PK scalar definition requires kind0/1 and nonzero ID");
    auto row=NativeSkillCatalog(db_).lookup(NativeSkillCatalog::current_dataset_id,kind,id);
    if(!row||row->source.native_image_sha256!=RecoveredBattleCommand::image_sha256)
        throw DatabaseError("PK native scalar presentation lacks matching current catalog definition");
    return std::move(*row);
}
std::string SqliteOwnedPkRoomRepository::scalar_definition_document(std::uint16_t key){
    return definition_document(scalar_definition(key));
}
OwnedPkRound SqliteOwnedPkRoomRepository::read_round(const Ticket& ticket){
    Statement q(db_,"SELECT r.revision,r.document,b.revision,b.checkpoint,b.state FROM owned_pk_room_rounds r JOIN owned_pk_rooms b ON b.id=r.room WHERE r.room=?");
    q.bind_id(1,ticket.id());if(!q.row())throw DatabaseError("PK persistent round missing");
    const auto room_state=q.text(4);
    if(room_state!="active"&&room_state!="finished")throw DatabaseError("PK round room is not active or retained-terminal");
    require_ticket(ticket,room_state.c_str());
    const auto result=OwnedPkRound::from_document(q.text(1));
    const auto checkpoint=BattleCheckpointCodec::decode(q.text(3));
    if(result.revision()!=q.number<std::uint64_t>(0)||result.battle_revision()!=q.number<std::uint64_t>(2)||
       checkpoint.version!=1||checkpoint.snapshot.numeric_profile!=BattleNumericProfile::LegacyCustom||
       checkpoint.snapshot.id!=ticket.id()||checkpoint.snapshot.revision!=result.battle_revision()||
       (checkpoint.snapshot.state==BattleState::Finished)!=(result.phase()==OwnedPkRound::Phase::Terminal)||
       (room_state=="finished")!=(result.phase()==OwnedPkRound::Phase::Terminal))
        throw DatabaseError("PK round/shared checkpoint phase mismatch");
    if(result.initial_notification_bounds()&&result.round()==1&&
       (result.phase()==OwnedPkRound::Phase::InitialControl||result.phase()==OwnedPkRound::Phase::Grants||
        result.phase()==OwnedPkRound::Phase::Collect||result.phase()==OwnedPkRound::Phase::Ready)&&
       result.battle_revision()!=1)
        throw DatabaseError("PK notification room advanced before first paired results");
    const auto& contexts=ticket.input().entry.command_contexts();
    if(result.headers()!=std::array{OwnedPkRound::Header{0,0,contexts[0]},OwnedPkRound::Header{0,0,contexts[1]}}||
       result.initial_notification_bounds()!=ticket.input().entry.initial_notification_bounds()||
       (!result.initial_notification_bounds()&&result.phase()==OwnedPkRound::Phase::InitialControl&&
        result.masks()!=ticket.input().initial_control_masks))
        throw DatabaseError("PK round immutable input binding mismatch");
    if(result.result_notification_bounds()){
        // CUSTOM-0122 v3 is an explicit complete owned-entry policy, not
        // permission to upgrade historical exact/raw tickets by JSON alone.
        const auto& input=ticket.input();const auto& entry=input.entry;
        if(!issuer_||ticket.issuer_!=issuer_||!input.combat_sources||
           !entry.owned_appearances()||!entry.owned_players()||!entry.owned_vitals()||
           !entry.owned_initial_grants()||!entry.owned_initial_contexts()||!entry.waiting_control()||
           result.result_notification_battle_revision()!=checkpoint.snapshot.revision)
            throw DatabaseError("PK result notifications require the original complete private owned entry");
        require_owned_main_sources(db_);
        for(std::size_t viewer=0;viewer<2;++viewer)
            if(!(*input.combat_sources)[viewer].uses_connection(db_)||
               !(*entry.owned_appearances())[viewer].uses_connection(db_)||
               !(*entry.owned_players())[viewer].uses_connection(db_)||
               !(*entry.owned_vitals())[viewer].uses_connection(db_)||
               !(*entry.owned_initial_grants())[viewer].uses_connection(db_)||
               !(*entry.owned_initial_contexts())[viewer].uses_connection(db_))
                throw DatabaseError("PK result notification sources use another connection");
        validate(input);
        if(readset(input)!=ticket.readset_)throw DatabaseError("PK result notification retained input changed");
        (void)Battle::restore(checkpoint);
        checkpoint_owned_pair(input,Battle(ticket.id(),input.actors,input.seed).checkpoint(),checkpoint);
        for(const auto position:{0,14})
            if(checkpoint.snapshot.state==BattleState::Active&&!checkpoint.snapshot.actors[position]->hp)
                throw DatabaseError("PK active notification roster contains a defeated participant");
        // These are current-cycle observations, independent of permanent
        // first-entry receipts. A fast viewer needs only ITS full result write.
        // v4 also binds BOTH retained rows to the private terminal source.
        // A JSON policy marker alone cannot qualify arbitrary89/prefix bytes.
        const auto terminal=result.terminal_notification()?
            std::optional{OwnedTaiwanPkTerminalSource::prepare(ticket,checkpoint.snapshot,result)}:std::nullopt;
        Statement rows(db_,"SELECT viewer,submitted,logical FROM main.owned_pk_room_outbox WHERE room=? AND revision=?");
        rows.bind_id(1,ticket.id());rows.bind_id(2,result.result_notification_battle_revision());
        std::array<bool,2> seen{};
        while(rows.row()){
            const auto viewer=rows.number<std::uint8_t>(0);const auto submitted=rows.integer(1);
            if(viewer>1||seen[viewer]||(submitted!=0&&submitted!=1)||
               (result.result_notification_observations()[viewer]&&submitted!=1))
                throw DatabaseError("PK notification receipt precedes its own result submission");
            if(terminal){
                const auto logical=rows.blob(2,1,RecoveredWorldFrame::max_logical_size);
                if(!RecoveredTaiwanPkTerminalNotification::matches_result_sequence(logical)||
                   !std::equal(terminal->begin(),terminal->end(),logical.end()-terminal->size()))
                    throw DatabaseError("PK retained terminal row differs from its private result policy");
            }
            seen[viewer]=true;
        }
        if(!seen[0]||!seen[1])throw DatabaseError("PK result notification cycle lacks both result rows");
    }
    return result;
}
OwnedPkRound SqliteOwnedPkRoomRepository::round(const Ticket& ticket){
    Transaction tx(db_);auto result=read_round(ticket);tx.commit();return result;
}
void SqliteOwnedPkRoomRepository::store_round(const Ticket& ticket,const OwnedPkRound& before,const OwnedPkRound& after){
    if(before.revision()>=static_cast<std::uint64_t>(INT64_MAX)||after.revision()!=before.revision()+1||
       after.battle_revision()!=before.battle_revision()||read_round(ticket).document()!=before.document())
        throw DatabaseError("PK round stale phase/intent CAS");
    Statement q(db_,"UPDATE owned_pk_room_rounds SET revision=?,document=? WHERE room=? AND revision=? AND document=?");
    q.bind_id(1,after.revision());q.bind(2,after.document());q.bind_id(3,ticket.id());
    q.bind_id(4,before.revision());q.bind(5,before.document());q.done();changed(db_);
}
void SqliteOwnedPkRoomRepository::control(const Ticket& ticket,const OwnedPkRound& expected,std::uint8_t viewer,
    const RecoveredBattleCommand::ControlRequest& request){
    if(viewer>1)throw DatabaseError("PK control viewer outside room");
    Transaction tx(db_);
    // Accept a fast peer's0B after ITS queue accepted the corresponding entry
    // or results; the other peer need not have acknowledged enqueue yet.
    // This transport submission is never relabeled as an official/native ACK.
    Statement ready(db_,"SELECT submitted FROM owned_pk_room_outbox WHERE room=? AND revision=? AND viewer=?");
    ready.bind_id(1,ticket.id());ready.bind_id(2,expected.battle_revision());ready.bind_id(3,viewer);
    if(!ready.row()||ready.integer(0)!=1)throw DatabaseError("PK notification before own entry/results submission");
    auto next=expected;if(!next.control(viewer,request))throw DatabaseError("PK unexpected/repeated native notification");
    store_round(ticket,expected,next);tx.commit();
}
void SqliteOwnedPkRoomRepository::submit_intent(const Ticket& ticket,const OwnedPkRound& expected,
    std::uint8_t viewer,OwnedPkRound::Intent intent){
    Transaction tx(db_);
    if(intent.skill_key){
        if(intent.definition_readset!=scalar_definition_document(*intent.skill_key))
            throw DatabaseError("PK selected native definition snapshot changed");
    }else if(!intent.definition_readset.empty())throw DatabaseError("PK basic action cannot borrow a skill definition");
    auto next=expected;if(!next.submit(viewer,std::move(intent)))throw DatabaseError("PK command outside its owned grant epoch");
    store_round(ticket,expected,next);tx.commit();
}
std::vector<SqliteOwnedPkRoomRepository::GrantDelivery> SqliteOwnedPkRoomRepository::pending_grants(const Ticket& ticket){
    return pending_grants_in_scope(ticket,nullptr);
}
std::vector<SqliteOwnedPkRoomRepository::GrantDelivery> SqliteOwnedPkRoomRepository::pending_grants(
        const Ticket& ticket,const BattleCheckpoint& supplied_actual){
    const auto actual=supplied_actual;
    return pending_grants_in_scope(ticket,&actual);
}
std::vector<SqliteOwnedPkRoomRepository::GrantDelivery> SqliteOwnedPkRoomRepository::pending_grants_in_scope(
        const Ticket& ticket,const BattleCheckpoint* actual){
    Transaction tx(db_);
    // The explicit checkpoint overload guards its namespace BEFORE the first
    // unqualified round/owner lookup, even if a shadow would claim round1.
    // Preserve the historical Ticket-only path's existing initial semantics.
    if(actual)require_owned_main_sources(db_);
    const auto phase=read_round(ticket);std::vector<GrantDelivery> result;
    if(actual){
        Statement room(db_,"SELECT checkpoint,revision FROM main.owned_pk_rooms WHERE id=?");
        room.bind_id(1,ticket.id());
        if(!room.row()||BattleCheckpointCodec::decode(room.text(0))!=*actual||
           actual->snapshot.id!=ticket.id()||actual->snapshot.revision!=phase.battle_revision()||
           actual->snapshot.revision!=room.number<std::uint64_t>(1)||room.row())
            throw DatabaseError("PK grant source differs from its actual runtime checkpoint");
    }
    std::optional<std::array<RecoveredBattlePlayerGrant::Bytes,2>> fresh;
    if(phase.phase()==OwnedPkRound::Phase::Grants&&phase.round()!=1){
        if(!actual)throw DatabaseError("PK later-round raw grant/counter authority remains unqualified");
        // The same full active qualification as the room's input dispatcher,
        // inside THIS transaction: original issuer/private graph, exact main
        // schema/readset/member locks, full RNG/checkpoint and frozen actors.
        // No prebattle Current/stored_current refresh or caller raw template.
        (void)require_active_owned_profile_in_scope(ticket,*actual);
        fresh=OwnedTaiwanPkLaterGrantSource::prepare(ticket,actual->snapshot,phase);
    }
    if(phase.phase()==OwnedPkRound::Phase::Grants)for(std::uint8_t i=0;i<2;++i)if(!phase.grant_submissions()[i]){
        const auto& p=i==0?ticket.input().pair.challenger:ticket.input().pair.recipient;
        const auto& raw=fresh?(*fresh)[i]:ticket.input().entry.grants()[i];
        // Separate typed grant epoch: never reuse checkpoint revision as an
        // enqueue receipt or call ordinary outbox submitted for a grant.
        result.push_back({ticket.id(),phase.grant_epoch(),p.session,p.world_generation,
            p.battle_generation+1,i,{raw.begin(),raw.end()}});
    }
    tx.commit();return result;
}
void SqliteOwnedPkRoomRepository::grant_submitted(const Ticket& ticket,std::uint64_t epoch,std::uint8_t viewer){
    Transaction tx(db_);auto before=read_round(ticket);auto after=before;
    if(!after.grant_submitted(epoch,viewer))throw DatabaseError("PK stale/repeated grant submission callback");
    store_round(ticket,before,after);tx.commit();
}
void SqliteOwnedPkRoomRepository::abandon(const Ticket& ticket)noexcept{
    try{
        Transaction tx(db_);
        Statement q(db_,"UPDATE owned_pk_rooms SET state='abandoned' WHERE id=? AND state='reserved' AND readset=? AND design_id='CUSTOM-0086'");
        q.bind_id(1,ticket.id());q.bind(2,ticket.readset_);q.done();
        if(sqlite3_changes(db_)==1){
            Statement release(db_,"DELETE FROM owned_pk_room_members WHERE room=?");release.bind_id(1,ticket.id());release.done();
        }
        tx.commit();
    }catch(...){/* Failed durable cleanup stays occupied; never fake release. */}
}
std::vector<SqliteOwnedPkRoomRepository::Delivery> SqliteOwnedPkRoomRepository::pending(const Ticket& ticket){
    Transaction tx(db_);
    Statement room(db_,"SELECT state,readset FROM owned_pk_rooms WHERE id=?");room.bind_id(1,ticket.id());
    if(!room.row()||room.text(1)!=ticket.readset_||(room.text(0)!="active"&&room.text(0)!="finished"))
        throw DatabaseError("PK outbox ticket mismatch");
    const auto state=room.text(0);require_ticket(ticket,state.c_str());
    Statement q(db_,"SELECT revision,viewer,logical FROM owned_pk_room_outbox WHERE room=? AND submitted=0 ORDER BY revision,viewer");
    q.bind_id(1,ticket.id());std::vector<Delivery> result;
    while(q.row()){
        const auto viewer=q.number<std::uint8_t>(1);if(viewer>1)throw DatabaseError("PK outbox viewer mismatch");
        const auto& p=viewer==0?ticket.input().pair.challenger:ticket.input().pair.recipient;
        const auto bytes=q.blob(2,1,RecoveredWorldFrame::max_logical_size);
        result.push_back({ticket.id(),q.number<std::uint64_t>(0),p.session,p.world_generation,
            p.battle_generation+1,viewer,{bytes.begin(),bytes.end()}});
    }
    tx.commit();return result;
}
void SqliteOwnedPkRoomRepository::submitted(const Ticket& ticket,std::uint64_t revision,std::uint8_t viewer){
    if(viewer>1||!revision)throw DatabaseError("Invalid PK enqueue receipt");
    Transaction tx(db_);
    Statement room(db_,"SELECT state,readset FROM owned_pk_rooms WHERE id=?");room.bind_id(1,ticket.id());
    if(!room.row()||room.text(1)!=ticket.readset_||(room.text(0)!="active"&&room.text(0)!="finished"))
        throw DatabaseError("PK enqueue receipt room mismatch");
    const auto state=room.text(0);require_ticket(ticket,state.c_str());
    Statement q(db_,"UPDATE owned_pk_room_outbox SET submitted=1 WHERE room=? AND revision=? AND viewer=? AND submitted=0");
    q.bind_id(1,ticket.id());q.bind_id(2,revision);q.bind_id(3,viewer);q.done();changed(db_);tx.commit();
}
}
