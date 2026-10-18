#include "db/SqliteOwnedPkRoomRepository.h"
#include "db/SqliteSupport.h"
#include "game/BattleCheckpointCodec.h"
#include "game/OwnedTaiwanPkLaterGrantSource.h"
#include "game/OwnedTaiwanPkTerminalSource.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredWorldEntryView.h"
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
Json companion_definition(const NativeSkillRecord& record){
    const auto& s=record.source;
    return Json{{"source",Json::array({s.dataset_id,s.source_path,s.source_sha256,s.decoded_sha256,
        s.native_image_sha256,s.source_section,s.loader_rva,s.lookup_rva,s.row_count})},
        {"index",record.source_record_index},{"offset",record.source_offset},
        {"sha256",record.record_sha256},{"raw",record.raw_record},
        {"kind",record.kind},{"definition_id",record.definition_id}};
}
Json companion_material(const OwnedTaiwanPkCompanionSource::Material& m){
    const auto& roster=m.restoration.deity_roster();Json rows=Json::array();
    for(const auto& row:roster.rows()){
        Json skills=Json::array();for(const auto& skill:row.snapshot.skills)skills.push_back(skill.encode());
        rows.push_back(Json{{"declaration",row.snapshot.declaration.encode()},
            {"status",row.snapshot.status.encode()},{"skills",skills},{"revision",row.revision},
            {"provenance",Json::array({row.provenance.source_sha256,row.provenance.authority,row.provenance.evidence_id})}});
    }
    Json selected=nullptr;if(roster.selection())selected=Json::array({roster.selection()->key,roster.selection()->revision});
    Json prefix_rows=Json::array(),definitions=Json::array(),writes=Json::array();
    for(const auto& row:m.prefix.rows()){
        Json learned=Json::array(),auxiliary=Json::array();
        for(const auto& d:row.learned_definitions)learned.push_back(d?companion_definition(*d):Json(nullptr));
        for(const auto& d:row.auxiliary_definitions)auxiliary.push_back(d?companion_definition(*d):Json(nullptr));
        prefix_rows.push_back(Json{{"key",row.row_key},{"learned_count",row.learned_count},
            {"learned_flags",row.learned_flags},{"learned_definitions",learned},
            {"auxiliary_count",row.auxiliary_count},{"auxiliary_definitions",auxiliary}});
    }
    for(const auto& d:m.prefix.catalog_records())definitions.push_back(companion_definition(d));
    for(const auto& w:m.writes)writes.push_back(w.logical());
    auto result=Json{{"owner",Json::array({m.session,m.account,m.character,m.battle_generation,static_cast<int>(m.phase)})},
        {"normal_entry",m.initialization.entry_frame()},{"normal_logical",m.initialization.entry_logical()},
        {"accepted_tail",m.initialization.accepted_tail()},{"config_flag",m.initialization.config_flag()},
        {"roster_owner",Json::array({roster.account(),roster.character()})},{"roster",rows},
        {"saved_selection",selected},{"template_keys",roster.template_keys()},
        {"issued_batches",m.restoration.batches()},{"written_batches",writes},
        {"prefix_rows",prefix_rows},{"prefix_count",m.prefix.roster_count()},
        {"prefix_selected",m.prefix.selected_row()},{"prefix_catalog",definitions},
        {"prefix_batches",m.prefix.actual_batches()}};
    if(m.whole_response){
        const auto& coverage=*m.whole_response;
        if(!m.writes.empty())throw DatabaseError("PK whole companion readset cannot mix per-frame observations");
        // ONLY the new private whole-response source adds this binding. Keep
        // historical written_batches as the actual old per-frame observations;
        // restoration bytes never manufacture individual socket receipts.
        result["whole_response_transport"]=Json{{"design_id","CUSTOM-0129"},
            {"observation","actual-one-original-WWR-local-complete-write-with-restored-ordered-suffix"},
            {"original_wire",coverage.wire()},{"encoded_restoration_suffix",coverage.suffix()},
            {"suffix_offset",coverage.suffix_offset()},{"suffix_size",coverage.suffix_size()},
            {"batch_count",coverage.batch_count()},
            {"scope","full-original-response-coverage;not-per-frame-receipts-native-ACK-or-companion-HP"}};
    }
    if(m.zero_publication){
        if(!m.whole_response||!m.restoration.batches().empty()||!m.writes.empty()||
           !m.restoration.deity_roster().rows().empty()||m.restoration.deity_roster().selection()||
           m.prefix.roster_count()!=0||m.prefix.selected_row()!=-1||
           m.whole_response->batch_count()!=0||!m.whole_response->suffix().empty()||
           m.whole_response->suffix_offset()!=m.whole_response->wire().size())
            throw DatabaseError("PK zero deity readset requires its original empty saved publication");
        const auto& zero=*m.zero_publication;
        const auto& lease=zero.player().combat().appearance().material().lease;
        result["whole_response_transport"]["observation"]="actual-original-written-initial-player-response-with-zero-owned-deity-records";
        result["zero_deity_publication"]=Json{{"design_id","CUSTOM-0129"},
            {"player_frame",zero.player_frame()},{"player_frame_offset",zero.player_offset()},
            {"original_lease",Json::array({lease.session,lease.account,lease.character,lease.generation,lease.actor_handle,
                lease.position.area,lease.position.scene,lease.position.x,lease.position.y,lease.position.revision})},
            {"scope","same-private-initial-player-graph-and-original-response;no-new-frame-receipt-reset-ACK-or-return-renewal"}};
    }
    if(m.learning_successor||m.selection_successor){
        // Artifact provenance only. Walk immutable backwards nodes once and
        // serialize chronological transport, without recursively copying the
        // complete sixteen-row prefix or rehydrating any private capability.
        std::vector<const OwnedTaiwanPkCompanionSource::Material*> nodes;
        const auto* root=&m;
        while(root->learning_successor||root->selection_successor){
            if(root->learning_successor&&root->selection_successor)
                throw DatabaseError("PK companion history has two transition owners");
            nodes.push_back(root);
            root=root->selection_successor?&root->selection_successor->predecessor().material():
                &root->learning_successor->predecessor().material();
        }
        Json origin={{"batch_count",root->restoration.batches().size()}};
        if(root->whole_response){
            const auto& whole=*root->whole_response;
            origin["whole_response"]=Json{{"original_wire",whole.wire()},
                {"suffix_offset",whole.suffix_offset()},{"suffix_size",whole.suffix_size()},
                {"batch_count",whole.batch_count()},{"zero_deity_publication",bool(root->zero_publication)}};
        }else{
            Json logical=Json::array();for(const auto& write:root->writes)logical.push_back(write.logical());
            origin["per_frame_logical"]=std::move(logical);
        }
        Json history=Json::array();
        for(auto at=nodes.rbegin();at!=nodes.rend();++at){
            const auto& node=**at;
            const auto& before=node.selection_successor?node.selection_successor->predecessor().material():
                node.learning_successor->predecessor().material();
            if(node.restoration.batches().size()<before.restoration.batches().size())
                throw DatabaseError("PK companion history lost its prior batches");
            Json step={{"before_batch_count",before.restoration.batches().size()},
                {"added_batch_count",node.restoration.batches().size()-before.restoration.batches().size()}};
            if(node.selection_successor){
                const auto& source=node.selection_successor->publication();Json components=Json::array();
                std::size_t ordinal=0;
                for(const auto& publication:source.publications()){
                    const auto& commit=publication.committed();const auto& deity=commit.deity();
                    Json skills=Json::array();for(const auto& skill:deity.snapshot.skills)skills.push_back(skill.encode());
                    components.push_back(Json{{"ordinal",ordinal++},{"owner",Json::array({commit.account(),commit.character()})},
                        {"before_selection",commit.before()?Json::array({commit.before()->key,commit.before()->revision}):Json(nullptr)},
                        {"after_selection",Json::array({commit.after().key,commit.after().revision})},{"changed",commit.changed()},
                        {"selected_deity",Json{{"declaration",deity.snapshot.declaration.encode()},
                            {"status",deity.snapshot.status.encode()},{"skills",skills},{"revision",deity.revision},
                            {"provenance",Json::array({deity.provenance.source_sha256,deity.provenance.authority,deity.provenance.evidence_id})}}},
                        {"component_frame",publication.wire()}});
                }
                step["kind"]="written_selection";step["whole_source_wire"]=source.response().wire();
                step["ordered_components"]=std::move(components);
            }else{
                const auto& source=node.learning_successor->publication();
                step["kind"]="written_learning";step["whole_source_wire"]=source.response().wire();
                step["logical_delta"]=source.logical_delta();
            }
            history.push_back(std::move(step));
        }
        result["source_transport_history"]=Json{{"origin",std::move(origin)},{"transitions",std::move(history)},
            {"scope","local-original-whole-Written-history;components-are-not-separate-receipts;not-native-ACK-cast-grant-or-restorable-capability"}};
    }
    return result;
}
bool owned_appearance_current(const SqliteOwnedPkRoomRepository::Input& input,sqlite3* db){
    if(!input.entry.owned_appearances())return true; // Historical path unchanged.
    if(!sqlite3_get_autocommit(db))return false;
    for(std::size_t i=0;i<2;++i){
        const auto& source=(*input.entry.owned_appearances())[i];
        const auto& m=source.material();const auto& p=i==0?input.pair.challenger:input.pair.recipient;
        // SharedWorldPresence generation and Application PK world_generation
        // are distinct namespaces. Retain both, never assert numerical equality.
        const auto actor=p.native_actor();
        if(!source.uses_connection(db)||m.lease.session!=p.session||m.lease.account!=p.account||
           m.lease.character!=p.character||!actor||!qualified_taiwan_scene_handle(m.lease.actor_handle)||
           m.lease.actor_handle!=*actor||m.battle_generation!=p.battle_generation||
           m.equipment.position!=p.position)return false;
        if(p.native_identity&&(!p.native_identity->retained_matches_appearance(source)||
           !p.native_identity->current()))return false; // Live INIT/presence only outside room SQL.
        if(!source.current())return false;
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
    if(input.companion_sources)for(const auto& source:*input.companion_sources)
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
    if(input.companion_sources)for(const auto& source:*input.companion_sources)
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
constexpr const char* finished_return_schema=R"SQL(
CREATE TABLE IF NOT EXISTS owned_pk_finished_return_feature (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 version INTEGER NOT NULL CHECK(version=1), design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0133'));
CREATE TABLE IF NOT EXISTS owned_pk_finished_returns (
 room INTEGER PRIMARY KEY REFERENCES owned_pk_rooms(id),
 document TEXT NOT NULL CHECK(length(document)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0133'));
)SQL";
constexpr const char* terminal_resource_schema=R"SQL(
CREATE TABLE IF NOT EXISTS owned_pk_terminal_resource_feature (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 version INTEGER NOT NULL CHECK(version=1), design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0127'));
CREATE TABLE IF NOT EXISTS owned_pk_terminal_resources (
 room INTEGER PRIMARY KEY REFERENCES owned_pk_rooms(id),
 document TEXT NOT NULL CHECK(length(document)>0),
 design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0127'));
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
void SqliteOwnedPkRoomRepository::require_terminal_resource_schema(sqlite3* db){
    require_owned_main_sources(db);require_round_schema(db);
    Statement shadows(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('owned_pk_terminal_resource_feature','owned_pk_terminal_resources') OR tbl_name COLLATE NOCASE IN ('owned_pk_terminal_resource_feature','owned_pk_terminal_resources')");
    if(shadows.row())throw DatabaseError("PK terminal resource TEMP namespace rejected");
    Statement triggers(db,"SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name COLLATE NOCASE='character_resources'");
    if(triggers.row())throw DatabaseError("Unexpected PK terminal resource storage trigger");
    for(const auto* name:{"owned_pk_terminal_resource_feature","owned_pk_terminal_resources"})
        require_ddl(db,terminal_resource_schema,name);
    Statement q(db,"SELECT version,design_id FROM main.owned_pk_terminal_resource_feature WHERE singleton=1");
    if(!q.row()||q.integer(0)!=1||q.text(1)!="CUSTOM-0127"||q.row())
        throw DatabaseError("PK terminal resource feature version mismatch");
}
void SqliteOwnedPkRoomRepository::install_terminal_resource_schema(sqlite3* db){
    Transaction tx(db);require_round_schema(db);
    sqlite_detail::execute(db,terminal_resource_schema);
    sqlite_detail::execute(db,"INSERT OR IGNORE INTO main.owned_pk_terminal_resource_feature(singleton,version,design_id) VALUES(1,1,'CUSTOM-0127')");
    require_terminal_resource_schema(db);tx.commit();
}
void SqliteOwnedPkRoomRepository::require_finished_return_schema(sqlite3* db){
    require_terminal_resource_schema(db);
    Statement shadows(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('owned_pk_finished_return_feature','owned_pk_finished_returns') OR tbl_name COLLATE NOCASE IN ('owned_pk_finished_return_feature','owned_pk_finished_returns')");
    if(shadows.row())throw DatabaseError("PK finished return TEMP namespace rejected");
    for(const auto* name:{"owned_pk_finished_return_feature","owned_pk_finished_returns"})
        require_ddl(db,finished_return_schema,name);
    Statement q(db,"SELECT version,design_id FROM main.owned_pk_finished_return_feature WHERE singleton=1");
    if(!q.row()||q.integer(0)!=1||q.text(1)!="CUSTOM-0133"||q.row())
        throw DatabaseError("PK finished return feature version mismatch");
}
void SqliteOwnedPkRoomRepository::install_finished_return_schema(sqlite3* db){
    Transaction tx(db);require_terminal_resource_schema(db);
    sqlite_detail::execute(db,finished_return_schema);
    sqlite_detail::execute(db,"INSERT OR IGNORE INTO main.owned_pk_finished_return_feature(singleton,version,design_id) VALUES(1,1,'CUSTOM-0133')");
    require_finished_return_schema(db);tx.commit();
}
void SqliteOwnedPkRoomRepository::validate(const Input& in){
    const auto& a=in.pair.challenger;const auto& b=in.pair.recipient;
    if(!a.session||!b.session||a.session==b.session||!a.account||!b.account||
       !a.character||!b.character||a.character==b.character||
       (!a.native_identity&&a.character>0xfff)||(!b.native_identity&&b.character>0xfff)||
       !a.world_generation||!b.world_generation||!a.ready||!b.ready||a.blocked||b.blocked||
       a.position.area!=b.position.area||a.position.scene!=b.position.scene||
       !a.position.revision||!b.position.revision||
       a.battle_generation>=static_cast<std::uint64_t>(INT64_MAX)||
       b.battle_generation>=static_cast<std::uint64_t>(INT64_MAX)||
       in.entry.characters()!=std::array<std::uint64_t,2>{a.character,b.character})
        throw DatabaseError("Invalid PK owned pair");
    const bool independent_actor=a.native_identity.has_value()||b.native_identity.has_value();
    if(independent_actor!=in.entry.native_actor_handles().has_value())
        throw DatabaseError("PK native actor profile differs from its private Prepared source");
    if(independent_actor){
        // Qualified native identities require the actual complete owned entry,
        // not a public scalar handle or a wider saved ID cast into native bytes.
        if(!in.combat_sources||!in.entry.owned_appearances()||!in.entry.owned_players()||
           !in.entry.owned_vitals()||!in.entry.owned_initial_grants()||!in.entry.owned_initial_contexts())
            throw DatabaseError("PK native actor profile lacks complete private owned entry sources");
        const auto& handles=*in.entry.native_actor_handles();
        if(!qualified_taiwan_scene_handle(handles[0])||!qualified_taiwan_scene_handle(handles[1])||
           handles[0]==handles[1])throw DatabaseError("PK native actors must be exact distinct scene handles");
    }
    for(std::size_t i=0;i<2;++i){
        const auto& peer=i==0?a:b;const auto actor=peer.native_actor();
        if(!actor||!*actor||*actor>0xfff||
           (independent_actor&&(*in.entry.native_actor_handles())[i]!=*actor))
            throw DatabaseError("PK native actor does not match its original peer and private Prepared");
        if(in.entry.owned_players()){
            const auto profile=(*in.entry.owned_players())[i].identity_profile();
            if(profile!=(peer.native_identity?TaiwanWorldEntryIdentity::QualifiedSceneHandle:
                    TaiwanWorldEntryIdentity::SelectedCharacter))
                throw DatabaseError("PK owned player profile differs from its original peer identity");
        }
        if(peer.native_identity){
            const auto& source=(*in.entry.owned_appearances())[i];
            const auto& material=source.material();
            if(!peer.native_identity->retained_matches_appearance(source)||
               material.lease.session!=peer.session||material.lease.account!=peer.account||
               material.lease.character!=peer.character||material.battle_generation!=peer.battle_generation||
               material.lease.actor_handle!=*actor)
                throw DatabaseError("PK native actor proof differs from exact private INIT/presence/appearance");
            // Retained graph only: ACTIVE/Finished/recovery must not demand an
            // old live normal-world Current after its original battle consume.
        }
    }
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
    if(in.companion_sources){
        if(!in.combat_sources||!in.entry.owned_appearances()||!in.entry.owned_players())
            throw DatabaseError("PK companion lineage requires complete private owned player sources");
        for(std::size_t i=0;i<2;++i){
            const auto& m=(*in.companion_sources)[i].material();
            const auto& original=(*in.entry.owned_appearances())[i].material();
            const auto& p=i==0?a:b;
            if(m.session!=p.session||m.account!=p.account||m.character!=p.character||
               m.battle_generation!=p.battle_generation||
               (m.phase!=SessionState::CharacterSelected&&m.phase!=SessionState::InWorld)||
               m.initialization.entry_frame()!=original.entry_frame||
               m.initialization.entry_logical()!=original.entry_logical||
               m.initialization.accepted_tail()!=original.accepted_tail||
               m.initialization.config_flag()!=original.config_flag)
                throw DatabaseError("PK companion lineage differs from original admitted initialization");
            if(m.zero_publication&&(m.zero_publication->player()!=(*in.entry.owned_players())[i]||
               !m.zero_publication->player().combat().appearance().owns_initialization(m.initialization)||
               m.zero_publication->player().combat().appearance().material().lease!=original.lease))
                throw DatabaseError("PK zero deity publication requires the same original prepared player graph");
            if(!(*in.companion_sources)[i].learning_player_matches((*in.entry.owned_players())[i]))
                throw DatabaseError("PK learned companion requires the same paired prepared player graph");
        }
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
    if(in.pair.challenger.native_identity||in.pair.recipient.native_identity){
        // ONLY the opted private identity profile adds this binding. Historical
        // peers, source objects, JSON keys and digest bytes stay unchanged.
        if(!in.entry.native_actor_handles()||!in.entry.owned_appearances())
            throw DatabaseError("PK native identity readset lacks exact private Prepared/appearance");
        Json mappings=Json::array();
        for(std::size_t i=0;i<2;++i){
            const auto& peer=i==0?in.pair.challenger:in.pair.recipient;
            const auto actor=peer.native_actor();
            if(!actor||!*actor||*actor>0xfff||(*in.entry.native_actor_handles())[i]!=*actor)
                throw DatabaseError("PK native identity readset differs from exact peer/Prepared actor");
            auto row=Json{{"owner",Json::array({peer.session,peer.account,peer.character,
                    peer.world_generation,peer.battle_generation})},
                {"identity_profile",peer.native_identity?"qualified-scene-handle":"selected-character-legacy"},
                {"native_actor",*actor}};
            if(peer.native_identity){
                const auto& source=(*in.entry.owned_appearances())[i];const auto& material=source.material();
                if(!peer.native_identity->retained_matches_appearance(source))
                    throw DatabaseError("PK native identity readset private namespace/INIT changed");
                row["original_lease"]=Json::array({material.lease.session,material.lease.account,
                    material.lease.character,material.lease.generation,material.lease.actor_handle});
                row["initial_position"]=appearance_position(material.lease.position);
                row["normal_entry_frame"]=material.entry_frame;
                row["normal_entry_logical"]=material.entry_logical;
                row["accepted_tail"]=material.accepted_tail;
                row["config_flag"]=material.config_flag;
                row["source_battle_generation"]=material.battle_generation;
            }
            mappings.push_back(std::move(row));
        }
        result["native_actor_mapping"]=Json{{"design_id","CUSTOM-0107"},
            {"authority","private-current-normal-INIT-and-exact-presence-lease-at-admission;retained-original-identity-after-battle"},
            {"saved_controller_domain","full-uint64-DB-identity;never-native-actor-alias"},
            {"prepared_native_actor_handles",*in.entry.native_actor_handles()},{"sources",mappings}};
    }
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
    if(in.companion_sources){
        Json sources=Json::array();for(const auto& source:*in.companion_sources)sources.push_back(companion_material(source.material()));
        result["owned_companion_source"]=Json{{"design_id","CUSTOM-0129"},
            {"authority","saved-roster-expected-reset-data-prefix-and-local-fullwrites-not-native-RAM-HP-or-ACK"},
            {"physical_order_or_later_companion_traffic_qualified",false},
            {"native_resource_offsets_qualified",false},{"sources",sources}};
    }
    return result.dump();
}
bool SqliteOwnedPkRoomRepository::owners_current(const Input& in){
    // CUSTOM-0129 old inputs stay unchanged; opted-in rooms retain this exact
    // saved roster/catalog through ACTIVE/Finished, without live-world calls.
    if(in.companion_sources)for(const auto& source:*in.companion_sources)
        if(!source.stored_current_in_room_transaction(db_))return false;
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?in.pair.challenger:in.pair.recipient;
        if(owners_.load_resources(p.account,p.character)!=std::optional{in.resources[i]}||
           owners_.load_role(p.account,p.character)!=std::optional{in.roles[i]}||
           owners_.load_position(p.account,p.character)!=std::optional{p.position}||
           owners_.owned_pending_battle(p.account,p.character))return false;
    }
    return true;
}
std::optional<std::string> SqliteOwnedPkRoomRepository::terminal_resource_ledger(const Ticket& ticket){
    // Historical schemas stay readable with their original exact resources.
    // Partial/redirected extension tables never grant a settled-owner bypass.
    Statement shadows(db_,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('owned_pk_terminal_resource_feature','owned_pk_terminal_resources') OR tbl_name COLLATE NOCASE IN ('owned_pk_terminal_resource_feature','owned_pk_terminal_resources')");
    if(shadows.row())throw DatabaseError("PK terminal resource TEMP namespace rejected");
    Statement tables(db_,"SELECT count(*) FROM main.sqlite_master WHERE name COLLATE NOCASE IN ('owned_pk_terminal_resource_feature','owned_pk_terminal_resources')");
    if(!tables.row())throw DatabaseError("PK terminal resource namespace unreadable");
    if(tables.integer(0)==0)return std::nullopt;
    require_terminal_resource_schema(db_);
    Statement row(db_,"SELECT document,design_id FROM main.owned_pk_terminal_resources WHERE room=?");
    row.bind_id(1,ticket.id());if(!row.row())return std::nullopt;
    if(row.text(1)!="CUSTOM-0127")throw DatabaseError("PK terminal resource provenance mismatch");
    auto document=row.text(0);if(row.row())throw DatabaseError("PK duplicate terminal resource ledger");
    return document;
}
SqliteOwnedPkRoomRepository::TerminalResources
SqliteOwnedPkRoomRepository::terminal_resources_in_scope(const Ticket& ticket,const BattleCheckpoint* actual,bool released_history){
    // No require_ticket/read_round here: the Finished owner guard calls this
    // before deciding whether current rows must equal original or saved ones.
    if(sqlite3_get_autocommit(db_))throw DatabaseError("PK terminal resources require an existing snapshot");
    require_terminal_resource_schema(db_);
    const auto& input=ticket.input();const auto& entry=input.entry;
    if(!issuer_||ticket.issuer_!=issuer_||!input.combat_sources||!entry.owned_appearances()||
       !entry.owned_players()||!entry.owned_vitals()||!entry.owned_initial_grants()||
       !entry.owned_initial_contexts()||!entry.waiting_control())
        throw DatabaseError("PK terminal resources require original complete private input");
    for(std::size_t i=0;i<2;++i)
        if(!(*input.combat_sources)[i].uses_connection(db_)||!(*entry.owned_appearances())[i].uses_connection(db_)||
           !(*entry.owned_players())[i].uses_connection(db_)||!(*entry.owned_vitals())[i].uses_connection(db_)||
           !(*entry.owned_initial_grants())[i].uses_connection(db_)||!(*entry.owned_initial_contexts())[i].uses_connection(db_))
            throw DatabaseError("PK terminal resource source connection changed");
    validate(input);
    if(readset(input)!=ticket.readset_)throw DatabaseError("PK terminal resource private readset changed");
    Statement room(db_,"SELECT state,readset,checkpoint,revision,design_id FROM main.owned_pk_rooms WHERE id=?");
    room.bind_id(1,ticket.id());
    if(!room.row()||room.text(0)!="finished"||room.text(1)!=ticket.readset_||room.text(4)!="CUSTOM-0086")
        throw DatabaseError("PK terminal resource room binding mismatch");
    const auto checkpoint_text=room.text(2);const auto checkpoint=BattleCheckpointCodec::decode(checkpoint_text);
    if(checkpoint.snapshot.id!=ticket.id()||checkpoint.snapshot.revision!=room.number<std::uint64_t>(3)||
       checkpoint.snapshot.state!=BattleState::Finished||BattleCheckpointCodec::encode(checkpoint)!=checkpoint_text||
       (actual&&checkpoint!=*actual)||room.row())
        throw DatabaseError("PK terminal resources differ from actual Finished checkpoint");
    (void)Battle::restore(checkpoint);
    checkpoint_owned_pair(input,Battle(ticket.id(),input.actors,input.seed).checkpoint(),checkpoint);
    Statement rounds(db_,"SELECT revision,document FROM main.owned_pk_room_rounds WHERE room=?");
    rounds.bind_id(1,ticket.id());if(!rounds.row())throw DatabaseError("PK terminal resource round missing");
    const auto phase_text=rounds.text(1);const auto phase=OwnedPkRound::from_document(phase_text);
    const auto& contexts=entry.command_contexts();
    if(phase.revision()!=rounds.number<std::uint64_t>(0)||!phase.terminal_notification()||
       phase.headers()!=std::array{OwnedPkRound::Header{0,0,contexts[0]},OwnedPkRound::Header{0,0,contexts[1]}}||
       phase.initial_notification_bounds()!=entry.initial_notification_bounds()||rounds.row())
        throw DatabaseError("PK terminal resource round/private input mismatch");
    const auto terminal=OwnedTaiwanPkTerminalSource::prepare(ticket,checkpoint.snapshot,phase);
    Statement count(db_,"SELECT count(*) FROM main.owned_pk_room_members WHERE room=?");count.bind_id(1,ticket.id());
    if(!count.row()||count.integer(0)!=(released_history?0:2)||count.row())
        throw DatabaseError("PK terminal resources have inconsistent retained/released member locks");
    if(released_history&&!finished_return_ledger(ticket))
        throw DatabaseError("PK released terminal history lacks its separate release ledger");
    Json members=Json::array(),before=Json::array(),after=Json::array();
    TerminalResources result{input.resources,{},{},true};
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?input.pair.challenger:input.pair.recipient;
        if(!released_history){
            Statement member(db_,"SELECT account,character,session,world_generation,battle_generation FROM main.owned_pk_room_members WHERE room=? AND viewer=?");
            member.bind_id(1,ticket.id());member.bind_id(2,i);
            if(!member.row()||member.number<std::uint64_t>(0)!=p.account||member.number<std::uint64_t>(1)!=p.character||
               member.number<std::uint64_t>(2)!=p.session||member.number<std::uint64_t>(3)!=p.world_generation||
               member.number<std::uint64_t>(4)!=p.battle_generation||member.row())
                throw DatabaseError("PK terminal resource member lock changed");
        }
        members.push_back(Json::array({i,p.account,p.character,p.session,p.world_generation,p.battle_generation}));
        const auto& actor=*checkpoint.snapshot.actors[14*i];const auto& original=input.resources[i];
        if(!original.revision||original.revision>=static_cast<std::uint64_t>(INT64_MAX)||
           actor.max_hp!=original.max_hp||actor.max_mp!=original.max_mp||actor.mp>std::numeric_limits<std::uint32_t>::max())
            throw DatabaseError("PK terminal resource projection/revision exhausted");
        auto& saved=result.after[i];saved.hp=actor.hp;saved.mp=static_cast<std::uint32_t>(actor.mp);++saved.revision;
        if(!saved.valid_health()||saved.mp>saved.max_mp)throw DatabaseError("PK terminal resources outside exact stored domain");
        before.push_back(Json::array({original.hp,original.max_hp,original.mp,original.max_mp,original.revision,original.design_id}));
        after.push_back(Json::array({saved.hp,saved.max_hp,saved.mp,saved.max_mp,saved.revision,saved.design_id}));
    }
    Statement rows(db_,"SELECT viewer,logical,submitted FROM main.owned_pk_room_outbox WHERE room=? AND revision=? ORDER BY viewer");
    rows.bind_id(1,ticket.id());rows.bind_id(2,checkpoint.snapshot.revision);Json outputs=Json::array();std::size_t viewer=0;
    while(rows.row()){
        const auto bytes=rows.blob(1,1,RecoveredWorldFrame::max_logical_size);const auto submitted=rows.integer(2);
        if(viewer>=2||rows.number<std::uint8_t>(0)!=viewer||(submitted!=0&&submitted!=1)||
           !RecoveredTaiwanPkTerminalNotification::matches_retained_result_sequence(bytes)||
           !std::equal(terminal.begin(),terminal.end(),bytes.end()-terminal.size()))
            throw DatabaseError("PK terminal resource final output mismatch");
        result.outputs[viewer].assign(bytes.begin(),bytes.end());
        outputs.push_back(Json::array({viewer,result.outputs[viewer],1}));
        result.both_submitted=result.both_submitted&&submitted==1;++viewer;
    }
    if(viewer!=2)throw DatabaseError("PK terminal resources require both exact final rows");
    if(result.both_submitted){
        Statement pending(db_,"SELECT 1 FROM main.owned_pk_room_outbox WHERE room=? AND submitted=0");pending.bind_id(1,ticket.id());
        if(pending.row())throw DatabaseError("PK terminal resources have an older pending output");
    }
    result.document=Json{{"version",1},{"design_id","CUSTOM-0127"},{"room",ticket.id()},
        {"profile",input.profile_readset_sha256},{"original_readset",ticket.readset_},{"checkpoint",checkpoint_text},
        {"round",phase_text},{"members",members},{"before",before},{"after",after},{"final_outputs",outputs},
        {"scope","HP-MP-only;XP-awards-return-revival-unresolved;locks-retained"}}.dump();
    return result;
}
bool SqliteOwnedPkRoomRepository::finished_owners_current(const Ticket& ticket){
    if(ticket.input().companion_sources)for(const auto& source:*ticket.input().companion_sources)
        if(!source.stored_current_in_room_transaction(db_))return false;
    const auto ledger=terminal_resource_ledger(ticket);
    if(!ledger)return owners_current(ticket.input());
    const auto material=terminal_resources_in_scope(ticket);
    if(!material.both_submitted||*ledger!=material.document)return false;
    const auto& input=ticket.input();
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?input.pair.challenger:input.pair.recipient;
        if(owners_.load_resources(p.account,p.character)!=std::optional{material.after[i]}||
           owners_.load_role(p.account,p.character)!=std::optional{input.roles[i]}||
           owners_.load_position(p.account,p.character)!=std::optional{p.position}||
           owners_.owned_pending_battle(p.account,p.character))return false;
    }
    return true;
}
void SqliteOwnedPkRoomRepository::commit_terminal_resources(const Ticket& ticket,const BattleCheckpoint& actual,
                                                           const Replies& actually_written){
    Transaction tx(db_);require_ticket(ticket,"finished");
    const auto material=terminal_resources_in_scope(ticket,&actual);
    if(!material.both_submitted||material.outputs!=actually_written)
        throw DatabaseError("PK terminal resource save differs from both actual final fullwrites");
    if(const auto ledger=terminal_resource_ledger(ticket)){
        if(*ledger!=material.document)throw DatabaseError("PK terminal resource retry differs");
        tx.commit();return; // Exact original private source/current after rows; no second increment.
    }
    for(std::size_t i=0;i<2;++i){
        const auto& p=i==0?ticket.input().pair.challenger:ticket.input().pair.recipient;
        const auto& before=ticket.input().resources[i];const auto& after=material.after[i];
        Statement write(db_,"UPDATE main.character_resources SET hp=?,mp=?,revision=? WHERE character_id=? AND hp=? AND max_hp=? AND mp=? AND max_mp=? AND revision=? AND design_id=?");
        write.bind_id(1,after.hp);write.bind_id(2,after.mp);write.bind_id(3,after.revision);write.bind_id(4,p.character);
        write.bind_id(5,before.hp);write.bind_id(6,before.max_hp);write.bind_id(7,before.mp);write.bind_id(8,before.max_mp);
        write.bind_id(9,before.revision);write.bind(10,before.design_id);write.done();changed(db_);
        if(owners_.load_resources(p.account,p.character)!=std::optional{after})
            throw DatabaseError("PK terminal resource exact readback mismatch");
    }
    Statement ledger(db_,"INSERT INTO main.owned_pk_terminal_resources(room,document,design_id) VALUES(?,?,'CUSTOM-0127')");
    ledger.bind_id(1,ticket.id());ledger.bind(2,material.document);ledger.done();changed(db_);
    require_ticket(ticket,"finished"); // Both staged rows + complete ledger/unchanged locks before COMMIT.
    tx.commit();
}
void SqliteOwnedPkRoomRepository::require_terminal_resources_saved(const Ticket& ticket,const BattleCheckpoint& actual,
                                                                  const Replies& actually_written){
    // CUSTOM-0132 actual paired transport observations come from Publication;
    // this private snapshot proves the prior CUSTOM0127 save still exists.
    // Own early1C remains weaker and continues to use require_terminal_context.
    RecoveryRead scope(db_);
    const auto material=terminal_resources_in_scope(ticket,&actual);
    const auto ledger=terminal_resource_ledger(ticket);
    if(!ledger || !material.both_submitted || material.outputs!=actually_written || *ledger!=material.document)
        throw DatabaseError("PK return preparation lacks the exact existing paired resource save");
    require_ticket(ticket,"finished"); // Exact saved after rows, complete readset and both original locks.
    scope.commit(); // Read-only: no resource increment, missing-ledger repair or lock release.
}
void SqliteOwnedPkRoomRepository::require_terminal_context(const Ticket& ticket,const BattleCheckpoint& actual,
        std::uint8_t viewer,const std::array<std::uint8_t,4>& payload,
        const std::vector<std::uint8_t>& actually_written){
    // CUSTOM-0128 caller supplies a private Binding's actual fullwrite bytes;
    // RoomState supplies its own runtime-claimed checkpoint. This snapshot
    // accepts the first viewer before the peer's write/resource COMMIT.
    if(viewer>1)throw DatabaseError("PK terminal context viewer outside owned pair");
    RecoveryRead scope(db_);
    const auto material=terminal_resources_in_scope(ticket,&actual);
    require_ticket(ticket,"finished"); // Original before OR exact CUSTOM0127 saved after.
    if(material.outputs[viewer]!=actually_written)
        throw DatabaseError("PK terminal context differs from its actual final fullwrite");
    Statement own(db_,"SELECT submitted FROM main.owned_pk_room_outbox WHERE room=? AND revision=? AND viewer=?");
    own.bind_id(1,ticket.id());own.bind_id(2,actual.snapshot.revision);own.bind_id(3,viewer);
    if(!own.row()||own.integer(0)!=1||own.row())
        throw DatabaseError("PK terminal context requires its own submitted final row");
    require_terminal_identity(ticket,viewer,payload);
    // Native4157F0/531C10: locale describes GetSystemDefaultLangID, not
    // win/loss, wire profile, CP936/950 or the retained display config_flag.
    // No both_submitted requirement, new ledger/schema or SQL mutation.
    scope.commit();
}
struct SqliteOwnedPkRoomRepository::FinishedReturnReleasePlan::Data {
    Data(Ticket retained,std::weak_ptr<const RuntimeOwner> runtime,sqlite3* db,BattleCheckpoint checkpoint,
            Replies outputs,TerminalInputs inputs,std::string ledger)
        :ticket(std::move(retained)),claim(std::move(runtime)),connection(db),actual(std::move(checkpoint)),
         final_writes(std::move(outputs)),payloads(inputs),document(std::move(ledger)),thread(std::this_thread::get_id()){}
    const Ticket ticket;
    const std::weak_ptr<const RuntimeOwner> claim;
    sqlite3* const connection;
    const BattleCheckpoint actual;
    const Replies final_writes;
    const TerminalInputs payloads;
    const std::string document;
    const std::thread::id thread;
    bool claimed=false,committed=false; // Recorded game thread only; sticky commit survives later failure.
};
bool SqliteOwnedPkRoomRepository::FinishedReturnReleasePlan::durably_committed()const noexcept{
    return data_&&data_->thread==std::this_thread::get_id()&&data_->committed;
}
void SqliteOwnedPkRoomRepository::require_runtime_claim(const Ticket& ticket,const RuntimeClaim& claim)const{
    if(!issuer_||ticket.issuer_!=issuer_||!claim.owner_)
        throw DatabaseError("PK finished return lacks its original runtime owner");
    const std::lock_guard lock(issuer_->mutex);
    const auto at=issuer_->claims.find(ticket.id());
    if(at==issuer_->claims.end()||at->second.lock()!=claim.owner_)
        throw DatabaseError("PK finished return runtime claim retired");
}
bool SqliteOwnedPkRoomRepository::finished_return_release_runtime_current(const Ticket& ticket,
        const RuntimeClaim& claim,const BattleSnapshot& snapshot,const FinishedReturnReleaseReceipt& receipt)const noexcept{
    try{
        const auto& data=receipt.data_;
        if(!data||data->thread!=std::this_thread::get_id()||!data->committed||data->connection!=db_||
           !issuer_||ticket.issuer_!=issuer_||!data->ticket.same_incarnation(ticket)||
           !claim.owner_||data->claim.lock()!=claim.owner_||data->actual.snapshot!=snapshot||
           snapshot.state!=BattleState::Finished)return false;
        const std::lock_guard lock(issuer_->mutex);
        const auto at=issuer_->claims.find(ticket.id());
        return at!=issuer_->claims.end()&&at->second.lock()==claim.owner_;
    }catch(...){return false;}
}
void SqliteOwnedPkRoomRepository::require_finished_return_plan(const Ticket& ticket,const RuntimeClaim& claim,
        const BattleCheckpoint& actual,const FinishedReturnReleasePlan& plan)const{
    const auto& data=plan.data_;
    if(!data||data->thread!=std::this_thread::get_id()||data->connection!=db_||
       !data->ticket.same_incarnation(ticket)||data->actual!=actual||
       data->claim.lock()!=claim.owner_||actual.snapshot.state!=BattleState::Finished)
        throw DatabaseError("PK finished return plan differs from its actual runtime Room");
    require_runtime_claim(ticket,claim);
}
void SqliteOwnedPkRoomRepository::require_terminal_identity(const Ticket& ticket,std::uint8_t viewer,
        const std::array<std::uint8_t,4>& payload){
    if(viewer>1||!ticket.input().entry.owned_appearances())
        throw DatabaseError("PK terminal identity lacks original viewer source");
    const auto& original=(*ticket.input().entry.owned_appearances())[viewer].material();
    const auto entry=RecoveredWorldEntryView::read(original.entry_frame);
    const auto identity=std::uint16_t{payload[0]}|(std::uint16_t{payload[1]}<<8);
    const auto locale=std::uint16_t{payload[2]}|(std::uint16_t{payload[3]}<<8);
    if(!entry||entry->actor_handle!=original.lease.actor_handle||identity!=entry->actor_handle||locale>1)
        throw DatabaseError("PK terminal context native identity/locale mismatch");
}
std::optional<std::string> SqliteOwnedPkRoomRepository::finished_return_ledger(const Ticket& ticket){
    // Optional extension absence preserves historical repositories. Partial,
    // redirected or trigger-altered namespaces never grant a release bypass.
    Statement shadows(db_,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('owned_pk_finished_return_feature','owned_pk_finished_returns') OR tbl_name COLLATE NOCASE IN ('owned_pk_finished_return_feature','owned_pk_finished_returns')");
    if(shadows.row())throw DatabaseError("PK finished return TEMP namespace rejected");
    Statement tables(db_,"SELECT count(*) FROM main.sqlite_master WHERE name COLLATE NOCASE IN ('owned_pk_finished_return_feature','owned_pk_finished_returns')");
    if(!tables.row())throw DatabaseError("PK finished return namespace unreadable");
    if(tables.integer(0)==0)return {};
    require_finished_return_schema(db_);
    Statement row(db_,"SELECT document,design_id FROM main.owned_pk_finished_returns WHERE room=?");
    row.bind_id(1,ticket.id());if(!row.row())return {};
    if(row.text(1)!="CUSTOM-0133")throw DatabaseError("PK finished return provenance changed");
    auto document=row.text(0);if(row.row())throw DatabaseError("PK finished return ledger duplicate");
    return document;
}
std::string SqliteOwnedPkRoomRepository::finished_return_document(const Ticket& ticket,
        const TerminalResources& material,const TerminalInputs& payloads){
    if(sqlite3_get_autocommit(db_)||!material.both_submitted)
        throw DatabaseError("PK finished return document requires exact submitted history snapshot");
    for(std::uint8_t i=0;i<2;++i)require_terminal_identity(ticket,i,payloads[i]);
    Json history=Json::array();
    Statement rows(db_,"SELECT revision,viewer,logical,submitted FROM main.owned_pk_room_outbox WHERE room=? ORDER BY revision,viewer");
    rows.bind_id(1,ticket.id());std::uint64_t prior=0,current=0;std::uint8_t expected_viewer=0;
    const auto terminal=Json::parse(material.document);
    const auto checkpoint=BattleCheckpointCodec::decode(terminal.at("checkpoint").get<std::string>());
    while(rows.row()){
        const auto revision=rows.number<std::uint64_t>(0);const auto viewer=rows.number<std::uint8_t>(1);
        const auto bytes=rows.blob(2,1,RecoveredWorldFrame::max_logical_size);
        const auto submitted=rows.integer(3);
        if(!revision||revision>checkpoint.snapshot.revision||viewer!=expected_viewer||submitted!=1)
            throw DatabaseError("PK finished return history has pending or mispaired outboxes");
        if(viewer==0){
            if((!prior&&revision!=1)||(prior&&(revision<=prior||revision-prior>2)))
                throw DatabaseError("PK finished return outbox revision history changed");
            current=revision;
        }else if(revision!=current)throw DatabaseError("PK finished return outbox pair revision changed");
        std::vector<std::uint8_t> logical(bytes.begin(),bytes.end());
        if(revision==1&&logical!=ticket.input().entry.records()[viewer])
            throw DatabaseError("PK finished return initial outbox differs from original entry");
        history.push_back(Json::array({revision,viewer,logical,submitted}));
        expected_viewer=static_cast<std::uint8_t>(1-viewer);if(viewer==1)prior=revision;
    }
    if(history.empty()||expected_viewer||prior!=checkpoint.snapshot.revision)
        throw DatabaseError("PK finished return history lacks exact final pair");
    return Json{{"version",1},{"design_id","CUSTOM-0133"},{"room",ticket.id()},
        {"terminal_resources",material.document},{"terminal_inputs",payloads},{"outbox_history",history},
        {"scope","exact-two-owner-lock-release;history-retained;local-SocketWritten;not-native-ACK-or-input-grant"}}.dump();
}
std::optional<std::string> SqliteOwnedPkRoomRepository::released_finished_in_scope(const Ticket& ticket){
    if(sqlite3_get_autocommit(db_))throw DatabaseError("PK released history requires an existing snapshot");
    const auto ledger=finished_return_ledger(ticket);if(!ledger)return {};
    const auto document=Json::parse(*ledger);
    const auto payloads=document.at("terminal_inputs").get<TerminalInputs>();
    const auto material=terminal_resources_in_scope(ticket,nullptr,true);
    const auto saved=terminal_resource_ledger(ticket);
    if(!saved||*saved!=material.document||!material.both_submitted||
       *ledger!=finished_return_document(ticket,material,payloads))
        throw DatabaseError("PK released Finished history differs from its exact canonical ledger");
    // Saved player rows may legitimately advance in WORLD after release.
    // Historical identity/source/checkpoint/outboxes stay exact; no live grant.
    return ledger;
}
SqliteOwnedPkRoomRepository::FinishedReturnReleasePlan SqliteOwnedPkRoomRepository::prepare_finished_return_release(
        const Ticket& ticket,const RuntimeClaim& claim,const BattleCheckpoint& actual,
        const Replies& actually_written,const TerminalInputs& payloads){
    require_runtime_claim(ticket,claim);
    if(actual.snapshot.state!=BattleState::Finished)
        throw DatabaseError("PK finished return preparation lacks actual Finished Battle");
    RecoveryRead scope(db_);require_finished_return_schema(db_);require_ticket(ticket,"finished");
    const auto material=terminal_resources_in_scope(ticket,&actual);
    const auto saved=terminal_resource_ledger(ticket);
    if(!saved||*saved!=material.document||material.outputs!=actually_written||!material.both_submitted)
        throw DatabaseError("PK finished return preparation lacks original saved final fullwrite pair");
    auto plan=FinishedReturnReleasePlan(std::make_shared<FinishedReturnReleasePlan::Data>(
        ticket,claim.owner_,db_,actual,actually_written,payloads,finished_return_document(ticket,material,payloads)));
    require_finished_return_plan(ticket,claim,actual,plan);scope.commit();
    require_finished_return_plan(ticket,claim,actual,plan);
    return plan; // All release-document/receipt ownership allocated before outer scene observers.
}
SqliteOwnedPkRoomRepository::FinishedReturnReleaseReceipt SqliteOwnedPkRoomRepository::commit_finished_return_release(
        const Ticket& ticket,const RuntimeClaim& claim,const BattleCheckpoint& actual,
        const FinishedReturnReleasePlan& plan,const std::function<void(sqlite3*)>& final_stored_fence){
    require_finished_return_plan(ticket,claim,actual,plan);
    const auto data=plan.data_;
    if(data->claimed||data->committed||!final_stored_fence)
        throw DatabaseError("PK finished return release already consumed or lacks stored observer");
    data->claimed=true; // One-use attempt; a failed transaction never renews this plan.
    Transaction tx(db_);require_finished_return_schema(db_);require_ticket(ticket,"finished");
    const auto material=terminal_resources_in_scope(ticket,&actual);
    const auto saved=terminal_resource_ledger(ticket);
    if(!saved||*saved!=material.document||material.outputs!=data->final_writes||!material.both_submitted||
       finished_return_document(ticket,material,data->payloads)!=data->document)
        throw DatabaseError("PK finished return durable readset changed before release");
    require_finished_return_plan(ticket,claim,actual,plan);final_stored_fence(db_);
    require_finished_return_plan(ticket,claim,actual,plan);
    {
        Statement insert(db_,"INSERT INTO main.owned_pk_finished_returns(room,document,design_id) VALUES(?,?,'CUSTOM-0133')");
        insert.bind_id(1,ticket.id());insert.bind(2,data->document);insert.done();changed(db_);
    }
    for(std::uint8_t i=0;i<2;++i){
        const auto& p=i==0?ticket.input().pair.challenger:ticket.input().pair.recipient;
        Statement release(db_,"DELETE FROM main.owned_pk_room_members WHERE room=? AND viewer=? AND account=? AND character=? AND session=? AND world_generation=? AND battle_generation=?");
        release.bind_id(1,ticket.id());release.bind_id(2,i);release.bind_id(3,p.account);release.bind_id(4,p.character);
        release.bind_id(5,p.session);release.bind_id(6,p.world_generation);release.bind_id(7,p.battle_generation);
        release.done();changed(db_); // Exactly this original two-owner lock pair only.
    }
    if(released_finished_in_scope(ticket)!=std::optional{data->document})
        throw DatabaseError("PK finished return staged release/history changed");
    require_finished_return_plan(ticket,claim,actual,plan);final_stored_fence(db_);
    require_finished_return_plan(ticket,claim,actual,plan);
    tx.commit();
    data->committed=true; // MUST precede any postCOMMIT observer/claim failure.
    require_finished_return_plan(ticket,claim,actual,plan);
    return FinishedReturnReleaseReceipt(data); // Shared pointer copy only; no fallible publication allocation.
}
void SqliteOwnedPkRoomRepository::require_finished_return_release(const Ticket& ticket,const RuntimeClaim& claim,
        const BattleCheckpoint& actual,const FinishedReturnReleaseReceipt& receipt){
    const auto plan=FinishedReturnReleasePlan(receipt.data_);
    require_finished_return_plan(ticket,claim,actual,plan);
    if(!receipt.data_->committed)throw DatabaseError("PK finished return lacks actual COMMIT receipt");
    RecoveryRead scope(db_);
    if(released_finished_in_scope(ticket)!=std::optional{receipt.data_->document})
        throw DatabaseError("PK finished return postCOMMIT retained history changed");
    require_finished_return_plan(ticket,claim,actual,plan);scope.commit();
    require_finished_return_plan(ticket,claim,actual,plan);
}
bool SqliteOwnedPkRoomRepository::occupied(std::uint64_t account,std::uint64_t character){
    // Owner lookup applies even if the independent feature has no row.
    (void)owners_.load_resources(account,character);
    Statement q(db_,"SELECT 1 FROM owned_pk_room_members WHERE account=? AND character=?");
    q.bind_id(1,account);q.bind_id(2,character);return q.row();
}
SqliteOwnedPkRoomRepository::Ticket SqliteOwnedPkRoomRepository::prepare_owned(Pair pair,
        RecoveredPkEntryProjection::Prepared entry,OwnedCombatSources sources,std::uint32_t seed,
        OwnedPkRound::Masks initial_control_masks,std::optional<OwnedCompanionSources> companion_sources){
    const auto& a=sources[0].material();const auto& b=sources[1].material();
    Input input{std::move(pair),std::move(entry),{a.resources,b.resources},{a.role,b.role},
        {sources[0].actor(0),sources[1].actor(14)},seed,{},initial_control_masks,std::move(sources),
        std::move(companion_sources)};
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
    // Released history is never an old active/Finished lock or outbox permit.
    if(finished_return_ledger(ticket))throw DatabaseError("PK Finished room was durably returned");
    // RESERVED alone rechecks all admitted source SQL tuples. Active Battle
    // retains immutable selected stats; no old world/aux current is required.
    if(std::string_view(state)=="reserved"&&!owned_combat_stored_current(ticket.input(),db_))
        throw DatabaseError("PK reserved combat source rows changed");
    Statement q(db_,"SELECT state,readset,design_id FROM owned_pk_rooms WHERE id=?");q.bind_id(1,ticket.id());
    if(!q.row()||q.text(0)!=state||q.text(1)!=ticket.readset_||q.text(2)!="CUSTOM-0086"||
       !(std::string_view(state)=="finished"?finished_owners_current(ticket):owners_current(ticket.input())))
        throw DatabaseError("PK stale room ticket/owner readset");
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
    {
        RecoveryRead scope(db_);
        if(released_finished_in_scope(ticket))
            throw DatabaseError("PK released Finished history cannot claim a mutable runtime owner");
        scope.commit();
    }
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
    auto finished_return=state=="finished"?released_finished_in_scope(ticket):std::nullopt;
    if(!finished_return)require_ticket(ticket,state.c_str());
    Statement count(db_,"SELECT COUNT(*) FROM owned_pk_room_members WHERE room=?");count.bind_id(1,ticket.id());
    if(!count.row()||count.integer(0)!=(finished_return?0:2)||count.row())
        throw DatabaseError("PK recovery has inconsistent retained/released owner locks");
    auto checkpoint=BattleCheckpointCodec::decode(checkpoint_text);
    if(checkpoint.snapshot.id!=ticket.id()||checkpoint.snapshot.revision!=revision)
        throw DatabaseError("PK retained checkpoint identity/revision mismatch");
    (void)Battle::restore(checkpoint); // Preserve full canonical RNG, never reseed/replay.
    const auto initial_checkpoint=Battle(ticket.id(),ticket.input().actors,ticket.input().seed).checkpoint();
    checkpoint_owned_pair(ticket.input(),initial_checkpoint,checkpoint);
    if(revision==1&&checkpoint!=initial_checkpoint)
        throw DatabaseError("PK retained revision1 differs from original checkpoint/RNG");
    auto phase=read_round(ticket,finished_return.has_value()); // Same history snapshot; never a released live grant.
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
    auto terminal_resources=state=="finished"?terminal_resource_ledger(ticket):std::nullopt;
    RetainedRecovery result(ticket,std::move(checkpoint),std::move(phase),std::move(outboxes),std::move(terminal_resources),std::move(finished_return));
    scope.commit();return result;
}
bool SqliteOwnedPkRoomRepository::retained_recovery_current(const RetainedRecovery& snapshot){
    try{
        const auto now=recover_retained(snapshot.ticket_);
        if(now.checkpoint_!=snapshot.checkpoint_||now.round_.document()!=snapshot.round_.document()||
           now.outboxes_.size()!=snapshot.outboxes_.size()||now.terminal_resources_!=snapshot.terminal_resources_||
           now.finished_return_!=snapshot.finished_return_)return false;
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
    // New rows must use the actual per-action native HP policy. Legacy all-HP86
    // compatibility belongs only to retained reads, never fresh settlement.
    for(const auto& reply:replies)
        if(!RecoveredTaiwanPkTerminalNotification::matches_output_sequence(reply)||
           RecoveredTaiwanPkTerminalNotification::matches_result_sequence(reply)!=next_round.terminal_notification())
            throw DatabaseError("PK fresh result differs from its native consumer HP policy");
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
    const NativeSkillCatalog catalog(db_,taiwan_profile_);
    // The installed epoch is independently qualified; it never falls back to
    // an old dataset or accepts a different source merely sharing its image.
    auto row=taiwan_profile_==NativeTaiwanSkillProfile::Installed453?
        catalog.lookup_main_digest_checked(catalog.taiwan_dataset_id(),kind,id):
        catalog.lookup(catalog.taiwan_dataset_id(),kind,id);
    if(taiwan_profile_==NativeTaiwanSkillProfile::Installed453 && row) {
        const auto counts=native_taiwan_skill_bank_counts(taiwan_profile_);
        std::int64_t ordinal=id-1;
        for(std::size_t i=0;i<std::size_t(kind);++i)ordinal+=counts[i];
        if(!native_taiwan_skill_source_matches(row->source,taiwan_profile_) ||
           id>counts[std::size_t(kind)] || row->source_record_index!=ordinal)
            throw DatabaseError("PK installed Taiwan skill source epoch or row geometry mismatch");
    }
    if(!row||row->source.native_image_sha256!=RecoveredBattleCommand::image_sha256)
        throw DatabaseError("PK native scalar presentation lacks matching current catalog definition");
    return std::move(*row);
}
std::string SqliteOwnedPkRoomRepository::scalar_definition_document(std::uint16_t key){
    return definition_document(scalar_definition(key));
}
OwnedPkRound SqliteOwnedPkRoomRepository::read_round(const Ticket& ticket,bool released_history){
    Statement q(db_,"SELECT r.revision,r.document,b.revision,b.checkpoint,b.state FROM owned_pk_room_rounds r JOIN owned_pk_rooms b ON b.id=r.room WHERE r.room=?");
    q.bind_id(1,ticket.id());if(!q.row())throw DatabaseError("PK persistent round missing");
    const auto room_state=q.text(4);
    if(room_state!="active"&&room_state!="finished")throw DatabaseError("PK round room is not active or retained-terminal");
    if(released_history){
        if(room_state!="finished"||!released_finished_in_scope(ticket))
            throw DatabaseError("PK released round has no exact retained history");
    }else require_ticket(ticket,room_state.c_str());
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
                if(!RecoveredTaiwanPkTerminalNotification::matches_retained_result_sequence(logical)||
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
