#include "db/SqliteOwnedPveRoomRepository.h"
#include "db/SqliteAccountRepository.h"
#include "db/SqliteSupport.h"
#include "game/BattleCheckpointCodec.h"
#include "game/OwnedBattleRowPreference.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <climits>
#include <limits>
#include <mutex>
#include <set>
namespace god2 {
namespace {
using T=OwnedPveRoomTypes;using J=nlohmann::json;using sqlite_detail::Statement;
void need(bool value,const char* message){if(!value)throw DatabaseError(message);}
std::uint64_t next_revision(std::uint64_t n){need(n&&n<std::uint64_t(INT64_MAX),"PvE saved revision exhausted");return n+1;}
void changed(sqlite3* db){need(sqlite3_changes(db)==1,"PvE exact-row CAS failed");}
std::uint64_t number(const J& j){
    need(j.is_number_integer(),"PvE durable integer type invalid");
    if(j.is_number_unsigned()){const auto n=j.get<std::uint64_t>();need(n<=std::uint64_t(INT64_MAX),"PvE durable unsigned integer too wide");return n;}
    const auto n=j.get<std::int64_t>();need(n>=0,"PvE durable negative integer");return std::uint64_t(n);
}
template<class A>A bytes(const J& j){A value{};need(j.is_array()&&j.size()==value.size(),"PvE durable byte width changed");for(std::size_t i=0;i<value.size();++i){const auto n=number(j[i]);need(n<=255,"PvE durable byte out of range");value[i]=std::uint8_t(n);}return value;}
std::vector<std::uint8_t> variable_bytes(const J& j,std::size_t maximum){need(j.is_array()&&j.size()<=maximum,"PvE durable blob out of range");std::vector<std::uint8_t> out;out.reserve(j.size());for(const auto& v:j){const auto n=number(v);need(n<=255,"PvE durable blob byte out of range");out.push_back(std::uint8_t(n));}return out;}
std::uint8_t byte(const J& j){const auto n=number(j);need(n<=255,"PvE byte too wide");return std::uint8_t(n);}
std::uint16_t word(const J& j){const auto n=number(j);need(n<=65535,"PvE word too wide");return std::uint16_t(n);}
std::uint32_t dword(const J& j){const auto n=number(j);need(n<=UINT32_MAX,"PvE dword too wide");return std::uint32_t(n);}
J identity(const T::Identity& i){return {i.session,i.account,i.character,i.world_generation,i.battle_generation,i.channel,i.actor_handle};}
T::Identity identity(const J& j){need(j.is_array()&&j.size()==7,"PvE durable identity width");return {number(j[0]),number(j[1]),number(j[2]),number(j[3]),number(j[4]),byte(j[5]),word(j[6])};}
J position(const RecoveredPosition& p){return {p.area,p.scene,p.x,p.y,p.revision};}
RecoveredPosition position(const J& j){need(j.is_array()&&j.size()==5,"PvE durable position width");return {word(j[0]),word(j[1]),word(j[2]),word(j[3]),number(j[4])};}
J root(const RecoveredCharacter& r){return {{"id",r.id},{"account",r.account_id},{"slot",r.slot},{"profile",r.profile},{"created",r.created_at},{"codepage",r.name_codepage},{"privilege",r.streamer_privilege}};}
RecoveredCharacter root(const J& j){RecoveredCharacter r;r.id=number(j.at("id"));r.account_id=number(j.at("account"));r.slot=byte(j.at("slot"));r.profile=bytes<std::array<std::uint8_t,40>>(j.at("profile"));r.created_at=j.at("created").get<std::string>();r.name_codepage=word(j.at("codepage"));r.streamer_privilege=byte(j.at("privilege"));return r;}
J resources(const CharacterResources& r){return {r.hp,r.max_hp,r.mp,r.max_mp,r.revision,r.design_id};}
CharacterResources resources(const J& j){need(j.is_array()&&j.size()==6,"PvE durable resource width");return {number(j[0]),number(j[1]),dword(j[2]),dword(j[3]),number(j[4]),j[5].get<std::string>()};}
J pet_json(const T::PetInput& p){
    const auto& s=p.saved;need(bool(s.pet)!=bool(s.pet1),"PvE saved pet kind is absent/ambiguous");
    std::vector<std::uint8_t> meta,stats;
    if(s.pet){meta.assign(s.pet->inventory.begin(),s.pet->inventory.end());const auto b=RecoveredPet2Stats::encode_logical(s.pet->stats);stats.assign(b.begin(),b.end());}
    else {meta.assign(s.pet1->inventory.begin(),s.pet1->inventory.end());const auto b=RecoveredPet1Stats::encode_logical(s.pet1->stats);stats.assign(b.begin(),b.end());}
    return {{"actor_slot",p.actor_slot},{"inventory_slot",s.slot},{"kind",s.pet?2:1},{"metadata",meta},{"stats",stats},{"revision",s.revision},
        {"source_sha256",s.provenance.source_sha256},{"authority",s.provenance.authority},{"evidence_id",s.provenance.evidence_id}};
}
T::PetInput pet_json(const J& j,const T::Identity& owner){
    T::PetInput p;p.actor_slot=byte(j.at("actor_slot"));p.saved.slot=byte(j.at("inventory_slot"));p.saved.revision=number(j.at("revision"));
    p.saved.provenance={j.at("source_sha256").get<std::string>(),j.at("authority").get<std::string>(),j.at("evidence_id").get<std::string>()};
    const auto meta=bytes<std::array<std::uint8_t,20>>(j.at("metadata"));const auto stats=variable_bytes(j.at("stats"),73);
    if(number(j.at("kind"))==1){const auto r=RecoveredPet1Stats::parse_logical(stats);need(bool(r),"PvE saved pet1 bytes invalid");p.saved.pet1=RecoveredPet1Lifecycle::Snapshot{{owner.account,owner.character},meta,*r};}
    else {need(number(j.at("kind"))==2,"PvE saved pet kind unknown");const auto r=RecoveredPet2Stats::parse_logical(stats);need(bool(r),"PvE saved pet2 bytes invalid");p.saved.pet=RecoveredPet2Lifecycle::Snapshot{{owner.account,owner.character},meta,*r};}return p;
}
J row_json(const NativeWorldEntrySnapshot& r){return {{"root",root(r.root)},{"position",position(r.position)},
    {"client_sha256",r.client_sha256},{"record_kind",r.record_kind},{"source_sha256",r.source_sha256},
    {"source_record",r.source_record},{"record",r.record},{"revision",r.revision}};}
NativeWorldEntrySnapshot row_json(const J& j){NativeWorldEntrySnapshot r;r.root=root(j.at("root"));r.position=position(j.at("position"));
    r.client_sha256=j.at("client_sha256").get<std::string>();r.record_kind=j.at("record_kind").get<std::string>();
    r.source_sha256=j.at("source_sha256").get<std::string>();r.source_record=j.at("source_record").get<std::string>();
    r.record=variable_bytes(j.at("record"),2);r.revision=number(j.at("revision"));return r;}
J input_json(const T::MemberInput& m){
    return {{"identity",identity(m.identity)},{"root",root(m.root)},{"role",m.role.logical},{"role_revision",m.role.revision},{"role_design",m.role.design_id},
        {"auxiliary",m.auxiliary.logical},{"auxiliary_revision",m.auxiliary.revision},{"auxiliary_origin",m.auxiliary.origin},{"auxiliary_provenance",m.auxiliary.provenance},
        {"resources",resources(m.resources)},{"return_position",position(m.return_position)},{"primary_slot",m.primary_slot},{"pet",m.pet?pet_json(*m.pet):J(nullptr)},{"command_context",m.command_context},
        {"row_preference",m.row_preference?row_json(*m.row_preference):J(nullptr)},
        {"empty_active_pet",m.empty_active_pet?J::array({m.empty_active_pet->slot,m.empty_active_pet->revision,
            m.empty_active_pet->provenance.source_sha256,m.empty_active_pet->provenance.authority,m.empty_active_pet->provenance.evidence_id}):J(nullptr)}};
}
bool released(const T::Member& m){return m.status==T::MemberStatus::Returned||m.status==T::MemberStatus::Retired;}
void structure(const T::Snapshot& s){
    need(s.id&&s.revision&&s.grant_epoch&&s.next_sequence&&s.incarnation.size()==32&&
        s.source_sha256.size()==64&&!s.source_record.empty()&&!s.members.empty()&&s.members.size()<=14&&
        s.checkpoint.snapshot.id==s.id&&s.outbox.size()<=1024,"PvE canonical room structure invalid");
    (void)Battle::restore(s.checkpoint);
    std::set<std::uint64_t> sessions;std::set<std::uint16_t> handles;std::set<std::uint8_t> slots;
    for(const auto& [id,m]:s.members){const auto& i=m.input.identity;
        need(id==i.character&&id&&i.account&&i.session&&i.world_generation&&i.battle_generation&&
            i.channel>=1&&i.channel<=3&&i.actor_handle&&i.actor_handle<0x4000&&m.grant_epoch&&
            m.grant_epoch<=s.grant_epoch&&sessions.insert(i.session).second&&handles.insert(i.actor_handle).second,
            "PvE canonical member identity/grant invalid");
        const auto primary=m.input.primary_slot;need(primary<14&&slots.insert(primary).second&&s.checkpoint.snapshot.actors[primary]&&
            s.checkpoint.snapshot.actors[primary]->controller==id,"PvE canonical primary occupancy changed");
        if(m.input.pet){const auto p=m.input.pet->actor_slot;need(p<14&&slots.insert(p).second&&s.checkpoint.snapshot.actors[p]&&
            s.checkpoint.snapshot.actors[p]->controller==id,"PvE canonical pet occupancy changed");}
        need(!m.secondary_grant||m.input.pet.has_value(),"PvE grant manufactures missing pet");
        if(released(m)||m.status==T::MemberStatus::Withdrawn||m.disconnected||m.return_context)
            need(!m.primary_grant&&!m.secondary_grant,"PvE retired/return member retained a command grant");
        if(m.status==T::MemberStatus::Retired)need(m.disconnected,"PvE retirement is not an actual disconnection");
        if(m.status==T::MemberStatus::Returned)need(m.return_context&&m.return_sequence,"PvE returned history lacks actual context");
        need(bool(m.return_context)==bool(m.return_sequence),"PvE return context/sequence partial");
    }
    for(std::uint8_t p=0;p<28;++p)if(const auto& a=s.checkpoint.snapshot.actors[p])
        need(a->position==p&&(p<14?(slots.contains(p)&&a->controller!=0):a->controller==0),"PvE canonical actor controller/slot mismatch");
    std::set<std::uint64_t> sequences;
    for(const auto& d:s.outbox){const auto m=s.members.find(d.recipient.character);
        need(d.sequence&&d.sequence<s.next_sequence&&sequences.insert(d.sequence).second&&m!=s.members.end()&&m->second.input.identity==d.recipient&&
            !d.logical.empty()&&d.logical.size()<=RecoveredWorldFrame::max_logical_size,"PvE canonical output recipient/sequence invalid");
        if(d.status==T::OutputStatus::Pending)need(!released(m->second)&&!m->second.disconnected,"PvE pending output targets retired member");
        if(d.kind==T::OutputKind::Return)need(m->second.return_context&&m->second.return_sequence>=d.sequence,"PvE return output not owned by exact aggregate context");
    }
    need(s.closed==std::all_of(s.members.begin(),s.members.end(),[](const auto& p){return released(p.second);}),"PvE canonical close state differs from member history");
}
T::MemberInput input_json(const J& j){T::MemberInput m;m.identity=identity(j.at("identity"));m.root=root(j.at("root"));m.role={bytes<RecoveredRoleLevel::Bytes>(j.at("role")),number(j.at("role_revision")),j.at("role_design").get<std::string>()};
    m.auxiliary={bytes<RecoveredRoleAuxiliary::Logical>(j.at("auxiliary")),number(j.at("auxiliary_revision")),j.at("auxiliary_origin").get<std::string>(),j.at("auxiliary_provenance").get<std::string>()};
    m.resources=resources(j.at("resources"));m.return_position=position(j.at("return_position"));m.primary_slot=byte(j.at("primary_slot"));m.command_context=dword(j.at("command_context"));if(!j.at("pet").is_null())m.pet=pet_json(j.at("pet"),m.identity);if(!j.at("row_preference").is_null())m.row_preference=row_json(j.at("row_preference"));
    if(const auto& e=j.at("empty_active_pet");!e.is_null()){need(e.is_array()&&e.size()==5,"PvE empty active pet readset width invalid");StoredPet2Slot p;p.slot=byte(e[0]);p.revision=number(e[1]);p.provenance={e[2].get<std::string>(),e[3].get<std::string>(),e[4].get<std::string>()};m.empty_active_pet=std::move(p);}return m;
}
std::string document(const T::Snapshot& s){J members=J::array(),outputs=J::array();
    for(const auto& [id,m]:s.members)members.push_back({{"character",id},{"input",input_json(m.input)},{"status",int(m.status)},{"grant_epoch",m.grant_epoch},
        {"primary_grant",m.primary_grant},{"secondary_grant",m.secondary_grant},{"disconnected",m.disconnected},{"return_context",m.return_context?J(*m.return_context):J(nullptr)},{"return_sequence",m.return_sequence}});
    for(const auto& d:s.outbox)outputs.push_back({d.sequence,identity(d.recipient),int(d.kind),d.logical,int(d.status)});
    return J{{"version",1},{"design_id","CUSTOM-0161"},{"id",s.id},{"incarnation",s.incarnation},{"revision",s.revision},{"grant_epoch",s.grant_epoch},{"next_sequence",s.next_sequence},
        {"source_sha256",s.source_sha256},{"source_record",s.source_record},{"checkpoint",BattleCheckpointCodec::encode(s.checkpoint)},{"members",members},{"outbox",outputs},{"support_enabled",s.support_enabled},{"closed",s.closed}}.dump();
}
T::Snapshot document(const std::string& text){
    need(text.size()<=16*1024*1024,"PvE durable room exceeds storage bound");const auto j=J::parse(text);need(j.at("version")==1&&j.at("design_id")=="CUSTOM-0161","PvE durable source version mismatch");
    T::Snapshot s;s.id=number(j.at("id"));s.incarnation=j.at("incarnation").get<std::string>();s.revision=number(j.at("revision"));s.grant_epoch=number(j.at("grant_epoch"));s.next_sequence=number(j.at("next_sequence"));s.source_sha256=j.at("source_sha256").get<std::string>();s.source_record=j.at("source_record").get<std::string>();s.checkpoint=BattleCheckpointCodec::decode(j.at("checkpoint").get<std::string>());s.support_enabled=j.at("support_enabled").get<bool>();s.closed=j.at("closed").get<bool>();
    need(j.at("members").is_array()&&j.at("members").size()<=14,"PvE durable member count");
    for(const auto& v:j.at("members")){T::Member m;m.input=input_json(v.at("input"));const auto status=number(v.at("status"));need(status<=4,"PvE durable member status");m.status=T::MemberStatus(status);m.grant_epoch=number(v.at("grant_epoch"));m.primary_grant=v.at("primary_grant").get<bool>();m.secondary_grant=v.at("secondary_grant").get<bool>();m.disconnected=v.at("disconnected").get<bool>();if(!v.at("return_context").is_null())m.return_context=bytes<std::array<std::uint8_t,4>>(v.at("return_context"));m.return_sequence=number(v.at("return_sequence"));need(number(v.at("character"))==m.input.identity.character&&s.members.emplace(m.input.identity.character,std::move(m)).second,"PvE durable member identity duplicate");}
    need(j.at("outbox").is_array()&&j.at("outbox").size()<=1024,"PvE bounded pending flight count");
    for(const auto& v:j.at("outbox")){need(v.is_array()&&v.size()==5,"PvE durable output width");const auto kind=number(v[2]),status=number(v[4]);need(kind<=5&&status<=2,"PvE durable output kind/status");s.outbox.push_back({number(v[0]),identity(v[1]),T::OutputKind(kind),variable_bytes(v[3],RecoveredWorldFrame::max_logical_size),T::OutputStatus(status)});}
    structure(s);need(document(s)==text,"PvE durable document is not canonical/lossless");return s;
}
const std::vector<std::pair<std::string,std::string>>& ddl(){static const std::vector<std::pair<std::string,std::string>> value={
 {"owned_pve_rooms","CREATE TABLE owned_pve_rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, incarnation TEXT NOT NULL UNIQUE, revision INTEGER NOT NULL CHECK(revision>=0), phase TEXT NOT NULL CHECK(phase IN ('reserved','active','finished','closed','abandoned')), document TEXT NOT NULL, design_id TEXT NOT NULL CHECK(design_id='CUSTOM-0161'))"},
 {"owned_pve_members","CREATE TABLE owned_pve_members (room INTEGER NOT NULL REFERENCES owned_pve_rooms(id), character INTEGER NOT NULL, account INTEGER NOT NULL, session INTEGER NOT NULL, world_generation INTEGER NOT NULL, battle_generation INTEGER NOT NULL, channel INTEGER NOT NULL CHECK(channel BETWEEN 1 AND 3), actor_handle INTEGER NOT NULL, primary_slot INTEGER NOT NULL CHECK(primary_slot BETWEEN 0 AND 13), secondary_slot INTEGER NOT NULL CHECK(secondary_slot BETWEEN -1 AND 13), status INTEGER NOT NULL CHECK(status BETWEEN 0 AND 4), grant_epoch INTEGER NOT NULL, primary_grant INTEGER NOT NULL CHECK(primary_grant IN (0,1)), secondary_grant INTEGER NOT NULL CHECK(secondary_grant IN (0,1)), source_document TEXT NOT NULL, PRIMARY KEY(room,character))"},
 {"owned_pve_character_claims","CREATE TABLE owned_pve_character_claims (character INTEGER PRIMARY KEY, room INTEGER NOT NULL REFERENCES owned_pve_rooms(id), account INTEGER NOT NULL, session INTEGER NOT NULL, battle_generation INTEGER NOT NULL)"},
 {"owned_pve_outbox","CREATE TABLE owned_pve_outbox (room INTEGER NOT NULL REFERENCES owned_pve_rooms(id), sequence INTEGER NOT NULL, character INTEGER NOT NULL, kind INTEGER NOT NULL CHECK(kind BETWEEN 0 AND 5), logical BLOB NOT NULL CHECK(length(logical) BETWEEN 1 AND 2560), status INTEGER NOT NULL CHECK(status BETWEEN 0 AND 2), PRIMARY KEY(room,sequence))"},
 {"owned_pve_returns","CREATE TABLE owned_pve_returns (room INTEGER NOT NULL, character INTEGER NOT NULL, sequence INTEGER NOT NULL, context BLOB NOT NULL CHECK(length(context)=4), completed INTEGER NOT NULL CHECK(completed IN (0,1)), PRIMARY KEY(room,character), FOREIGN KEY(room,character) REFERENCES owned_pve_members(room,character))"}};return value;}
std::string phase(const T::Snapshot& s){return s.closed?"closed":s.checkpoint.snapshot.state==BattleState::Finished?"finished":"active";}
void namespaces(sqlite3* db){
    Statement temp(db,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_resources','character_role_snapshots','character_role_auxiliary_snapshots','character_pet2_slots','character_native_world_entries','battle_reservations','battle_settlements','owned_pve_rooms','owned_pve_members','owned_pve_character_claims','owned_pve_outbox','owned_pve_returns') OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_resources','character_role_snapshots','character_role_auxiliary_snapshots','character_pet2_slots','character_native_world_entries','battle_reservations','battle_settlements','owned_pve_rooms','owned_pve_members','owned_pve_character_claims','owned_pve_outbox','owned_pve_returns')");need(!temp.row(),"PvE TEMP source shadow rejected");
    Statement triggers(db,"SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_resources','character_role_snapshots','character_role_auxiliary_snapshots','character_pet2_slots','character_native_world_entries','battle_reservations','battle_settlements','owned_pve_rooms','owned_pve_members','owned_pve_character_claims','owned_pve_outbox','owned_pve_returns')");need(!triggers.row(),"PvE source trigger rejected");
}
std::vector<std::uint8_t> pet_stats(const StoredPet2Slot& p){if(p.pet){const auto b=RecoveredPet2Stats::encode_logical(p.pet->stats);return {b.begin(),b.end()};}need(bool(p.pet1),"PvE pet raw source missing");const auto b=RecoveredPet1Stats::encode_logical(p.pet1->stats);return {b.begin(),b.end()};}
std::array<std::uint8_t,20> pet_metadata(const StoredPet2Slot& p){if(p.pet)return p.pet->inventory;need(bool(p.pet1),"PvE pet metadata source missing");return p.pet1->inventory;}
void no_foreign_pk_claim(sqlite3* db,std::uint64_t character){
    Statement schema(db,"SELECT type FROM main.sqlite_master WHERE name='owned_pk_room_members' COLLATE NOCASE");
    if(!schema.row())return;need(schema.text(0)=="table"&&!schema.row(),"PvE optional PK source is not its actual main table");
    Statement claim(db,"SELECT 1 FROM main.owned_pk_room_members WHERE character=?");claim.bind_id(1,character);
    need(!claim.row(),"PvE character already belongs to a retained paired PK owner");
}
}
struct SqliteOwnedPveRoomRepository::Issuer {
    sqlite3* db;std::thread::id thread=std::this_thread::get_id();bool busy=false,reentered=false;
    std::map<std::uint64_t,std::weak_ptr<const void>> claims;
    struct Operation {
        Issuer& i;
        explicit Operation(Issuer& v):i(v){need(i.thread==std::this_thread::get_id(),"PvE repository GAME executor mismatch");if(i.busy){i.reentered=true;throw DatabaseError("PvE repository callback reentry");}i.busy=true;i.reentered=false;}
        ~Operation(){i.busy=false;}
        void current()const{need(!i.reentered,"PvE repository callback invalidated source");}
        void final(const Types::PureCurrent& f)const{current();need(bool(f)&&f(),"PvE final actual owner source retired");current();}
        bool after(const Types::PureCurrent& f)const noexcept{try{return !i.reentered&&f&&f()&&!i.reentered;}catch(...){return false;}}
    };
};
struct SqliteOwnedPveRoomRepository::TicketData {std::shared_ptr<Issuer> issuer;std::uint64_t id{};std::string incarnation;};
std::uint64_t SqliteOwnedPveRoomRepository::Ticket::id()const noexcept{return data_->id;}
const std::string& SqliteOwnedPveRoomRepository::Ticket::incarnation()const noexcept{return data_->incarnation;}
bool SqliteOwnedPveRoomRepository::Ticket::same_incarnation(const Ticket& v)const noexcept{return data_==v.data_;}
SqliteOwnedPveRoomRepository::SqliteOwnedPveRoomRepository(sqlite3* db,AccountRepository& a,SqliteRecoveredCharacterRepository& c,SqliteRoleAuxiliaryRepository& aux,SqliteCompanionRepository& pets)
 :db_(db),accounts_(a),characters_(c),auxiliary_(aux),companions_(pets){
    const auto actual=dynamic_cast<SqliteAccountRepository*>(&a);
    need(db&&actual&&actual->uses_connection(db)&&c.uses_connection(db)&&aux.uses_connection(db)&&pets.uses_connection(db),"PvE requires all actual owners on the same SQLite connection");
    row_preferences_=std::make_unique<SqliteNativeWorldEntrySnapshotRepository>(db,*actual,c);
    static std::mutex mutex;static std::map<sqlite3*,std::weak_ptr<Issuer>> issuers;
    {std::lock_guard lock(mutex);issuer_=issuers[db].lock();if(!issuer_){issuer_=std::make_shared<Issuer>(Issuer{db});issuers[db]=issuer_;}}
    Issuer::Operation op(*issuer_);require_schema(db_);op.current();
}
SqliteOwnedPveRoomRepository::~SqliteOwnedPveRoomRepository()=default;
bool SqliteOwnedPveRoomRepository::uses_connection(const sqlite3* db)const noexcept{return db_==db;}
std::string SqliteOwnedPveRoomRepository::schema_sql(){std::string text;for(const auto& [name,sql]:ddl()){(void)name;text+=sql+";\n";}return text;}
void SqliteOwnedPveRoomRepository::require_schema(sqlite3* db){need(db,"PvE schema requires actual connection");namespaces(db);for(const auto& [name,sql]:ddl()){Statement q(db,"SELECT type,sql FROM main.sqlite_master WHERE name=? COLLATE NOCASE");q.bind(1,name);need(q.row()&&q.text(0)=="table"&&q.text(1)==sql&&!q.row(),"PvE exact independent schema missing/mismatched");}}
void SqliteOwnedPveRoomRepository::install_schema(sqlite3* db){need(db&&sqlite3_get_autocommit(db),"PvE explicit schema installation needs its own transaction");namespaces(db);sqlite_detail::Transaction tx(db);for(const auto& [name,sql]:ddl()){Statement q(db,"SELECT 1 FROM main.sqlite_master WHERE name=? COLLATE NOCASE");q.bind(1,name);need(!q.row(),"PvE schema installation cannot replace existing objects");sqlite_detail::execute(db,sql);}require_schema(db);tx.commit();}
SqliteOwnedPveRoomRepository::Ticket SqliteOwnedPveRoomRepository::reserve(const Types::PureCurrent& current){
    Issuer::Operation op(*issuer_);op.final(current);need(sqlite3_get_autocommit(db_),"PvE reserve needs its own transaction");
    auto data=std::make_shared<TicketData>();data->issuer=issuer_;sqlite_detail::Transaction tx(db_);namespaces(db_);
    Statement insert(db_,"INSERT INTO main.owned_pve_rooms(incarnation,revision,phase,document,design_id) VALUES(lower(hex(randomblob(16))),0,'reserved','','CUSTOM-0161')");insert.done();changed(db_);data->id=std::uint64_t(sqlite3_last_insert_rowid(db_));
    Statement read(db_,"SELECT incarnation FROM main.owned_pve_rooms WHERE id=? AND phase='reserved' AND revision=0 AND design_id='CUSTOM-0161'");read.bind_id(1,data->id);need(read.row(),"PvE reserved row missing");data->incarnation=read.text(0);need(data->incarnation.size()==32&&!read.row(),"PvE reserved incarnation invalid");op.final(current);tx.commit();return Ticket(std::move(data));
}
void SqliteOwnedPveRoomRepository::abandon(const Ticket& ticket)noexcept{try{if(ticket.data_->issuer!=issuer_||issuer_->busy)return;Issuer::Operation op(*issuer_);sqlite_detail::Transaction tx(db_);Statement q(db_,"UPDATE main.owned_pve_rooms SET phase='abandoned' WHERE id=? AND incarnation=? AND phase='reserved' AND revision=0");q.bind_id(1,ticket.id());q.bind(2,ticket.incarnation());q.done();op.current();tx.commit();}catch(...) {}}
std::shared_ptr<const void> SqliteOwnedPveRoomRepository::claim_runtime(const Ticket& ticket){Issuer::Operation op(*issuer_);need(ticket.data_->issuer==issuer_&&issuer_->claims[ticket.id()].expired(),"PvE room already has a canonical runtime claim");auto claim=std::make_shared<const std::uint8_t>(0);issuer_->claims[ticket.id()]=claim;return claim;}
void SqliteOwnedPveRoomRepository::validate_member(const Types::MemberInput& m){
    const auto& i=m.identity;need(i.account&&i.character&&i.session&&i.world_generation&&i.battle_generation&&i.channel>=1&&i.channel<=3&&
        i.actor_handle&&i.actor_handle<0x4000&&m.primary_slot<14&&m.return_position.revision&&m.resources.valid_health()&&m.resources.mp<=m.resources.max_mp,
        "PvE actual owner/member material invalid");
    const auto account=accounts_.find_by_id(i.account);need(account&&account->id==i.account,"PvE account source missing");
    const auto roots=characters_.list_for_account(i.account);const auto at=std::find_if(roots.begin(),roots.end(),[&](const auto& r){return r.id==i.character;});
    need(at!=roots.end()&&root(*at)==root(m.root)&&m.root.id==i.character&&m.root.account_id==i.account,"PvE whole root changed");
    need(characters_.load_position(i.account,i.character)==std::optional{m.return_position}&&characters_.load_role(i.account,i.character)==std::optional{m.role}&&
        characters_.load_resources(i.account,i.character)==std::optional{m.resources}&&auxiliary_.load(i.account,i.character)==std::optional{m.auxiliary},"PvE saved position/role/resources/auxiliary baseline changed");
    const auto level=RecoveredRoleLevel::parse(m.role.logical);need(level&&level->max_hp()==m.resources.max_hp&&level->max_mp()==m.resources.max_mp,"PvE saved role/resource maxima mismatch");
    no_foreign_pk_claim(db_,i.character);
    need(m.row_preference&&NativeWorldEntrySnapshot::same_root(m.row_preference->root,m.root)&&
        m.row_preference->client_sha256==OwnedBattleRowPreference::client_pin&&
        m.row_preference->record_kind==OwnedBattleRowPreference::record_kind&&
        m.row_preference->source_sha256==OwnedBattleRowPreference::client_pin&&
        m.row_preference->source_record==OwnedBattleRowPreference::source_record&&
        m.row_preference->record.size()==2&&m.row_preference->record[0]==0xe8&&m.row_preference->record[1]<=1&&
        row_preferences_->load(i.account,i.character,OwnedBattleRowPreference::client_pin,OwnedBattleRowPreference::record_kind)==m.row_preference,
        "PvE complete saved B4/E8 choice changed; historical witness position grants no WORLD authority");
    if(m.pet){need(!m.empty_active_pet,"PvE active pet also claims empty slot");const auto& p=m.pet->saved;need(p.slot==44&&m.pet->actor_slot<14&&m.pet->actor_slot!=m.primary_slot&&p.revision&&bool(p.pet)!=bool(p.pet1),"PvE active owned pet source invalid");
        const auto owner=p.pet?p.pet->owner:p.pet1->owner;need(owner.account==i.account&&owner.character==i.character,"PvE saved pet owner mismatch");
        const auto expected_stats=pet_stats(p);const auto expected_metadata=pet_metadata(p);
        Statement q(db_,"SELECT metadata,stats,revision,source_sha256,authority,evidence_id FROM main.character_pet2_slots WHERE character_id=? AND slot=44");q.bind_id(1,i.character);need(q.row(),"PvE actual active pet row missing");
        const auto metadata=q.blob(0,20,20),stats=q.blob(1,1,73);
        need(std::equal(metadata.begin(),metadata.end(),expected_metadata.begin())&&std::vector<std::uint8_t>(stats.begin(),stats.end())==expected_stats&&q.number<std::uint64_t>(2)==p.revision&&
            q.text(3)==p.provenance.source_sha256&&q.text(4)==p.provenance.authority&&q.text(5)==p.provenance.evidence_id&&!q.row(),"PvE exact pet blob/revision/provenance changed");
    }else{
        Statement q(db_,"SELECT metadata,stats,revision,source_sha256,authority,evidence_id FROM main.character_pet2_slots WHERE character_id=? AND slot=44");q.bind_id(1,i.character);
        if(!m.empty_active_pet)need(!q.row(),"PvE previously absent active pet row appeared");
        else{const auto& p=*m.empty_active_pet;need(p.slot==44&&!p.occupied()&&p.revision&&q.row(),"PvE explicit empty active pet row disappeared");
            need(q.blob(0,0,0).empty()&&q.blob(1,0,0).empty()&&q.number<std::uint64_t>(2)==p.revision&&
                q.text(3)==p.provenance.source_sha256&&q.text(4)==p.provenance.authority&&q.text(5)==p.provenance.evidence_id&&!q.row(),
                "PvE explicit empty active pet tuple changed/occupied");}
    }
}
OwnedPveRoomTypes::MemberInput SqliteOwnedPveRoomRepository::updated_resources(Types::MemberInput m,const BattleSnapshot& state,bool withdrawn){
    if(withdrawn)return m;need(m.primary_slot<28&&state.actors[m.primary_slot]&&state.actors[m.primary_slot]->controller==m.identity.character,"PvE primary resource actor mismatch");
    const auto& actor=*state.actors[m.primary_slot];need(actor.max_hp==m.resources.max_hp&&actor.max_mp==m.resources.max_mp,"PvE battle changed saved maximum resources");
    if(actor.hp!=m.resources.hp||actor.mp!=m.resources.mp){m.resources.hp=actor.hp;m.resources.mp=actor.mp;m.resources.revision=next_revision(m.resources.revision);}
    if(m.pet){auto& p=m.pet->saved;const auto slot=m.pet->actor_slot;need(slot<28&&state.actors[slot]&&state.actors[slot]->controller==m.identity.character,"PvE secondary resource actor mismatch");const auto& a=*state.actors[slot];bool changed_pet=false;
        if(p.pet){const auto old=p.pet->stats.vitals();need(a.max_hp==old.maximum_hp&&a.max_mp==old.maximum_mp&&a.hp<=0x3fff&&a.mp<=0x7ff,"PvE pet2 resource cannot be represented losslessly");
            if(a.hp!=old.current_hp||a.mp!=old.current_mp){auto b=RecoveredPet2Stats::encode_logical(p.pet->stats);std::uint32_t word=std::uint32_t(b[5])|(std::uint32_t(b[6])<<8)|(std::uint32_t(b[7])<<16)|(std::uint32_t(b[8])<<24);
                word=(word&0xfe000000u)|std::uint32_t(a.hp)|(a.mp<<14);for(unsigned n=0;n<4;++n)b[5+n]=std::uint8_t(word>>(8*n));const auto next=RecoveredPet2Stats::parse_logical(b);need(bool(next),"PvE updated pet2 raw structure invalid");p.pet->stats=*next;changed_pet=true;}}
        else {need(bool(p.pet1),"PvE saved pet1 missing");const auto old=p.pet1->stats.vitals();need(a.max_hp==old.maximum_hp&&a.max_mp==old.maximum_mp&&a.hp<=65535&&a.mp<=65535,"PvE pet1 resource cannot be represented losslessly");
            if(a.hp!=old.current_hp||a.mp!=old.current_mp){auto b=RecoveredPet1Stats::encode_logical(p.pet1->stats);b[1]=std::uint8_t(a.hp);b[2]=std::uint8_t(a.hp>>8);b[5]=std::uint8_t(a.mp);b[6]=std::uint8_t(a.mp>>8);const auto next=RecoveredPet1Stats::parse_logical(b);need(bool(next),"PvE updated pet1 raw structure invalid");p.pet1->stats=*next;changed_pet=true;}}
        if(changed_pet){p.revision=next_revision(p.revision);p.provenance.authority="CUSTOM_DESIGNED";p.provenance.evidence_id="CUSTOM-0161:HP-MP-only;room="+std::to_string(state.id)+";battle_revision="+std::to_string(state.revision);}
    }return m;
}
namespace {
void write_member(sqlite3* db,std::uint64_t room,const T::Member& m,bool insert){const auto& i=m.input.identity;
    Statement q(db,insert?"INSERT INTO main.owned_pve_members(account,session,world_generation,battle_generation,channel,actor_handle,primary_slot,secondary_slot,status,grant_epoch,primary_grant,secondary_grant,source_document,room,character) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)":
        "UPDATE main.owned_pve_members SET account=?,session=?,world_generation=?,battle_generation=?,channel=?,actor_handle=?,primary_slot=?,secondary_slot=?,status=?,grant_epoch=?,primary_grant=?,secondary_grant=?,source_document=? WHERE room=? AND character=?");
    q.bind_id(1,i.account);q.bind_id(2,i.session);q.bind_id(3,i.world_generation);q.bind_id(4,i.battle_generation);q.bind(5,i.channel);q.bind(6,i.actor_handle);q.bind(7,m.input.primary_slot);q.bind(8,m.input.pet?m.input.pet->actor_slot:-1);q.bind(9,int(m.status));q.bind_id(10,m.grant_epoch);q.bind(11,m.primary_grant?1:0);q.bind(12,m.secondary_grant?1:0);q.bind(13,input_json(m.input).dump());q.bind_id(14,room);q.bind_id(15,i.character);q.done();changed(db);
}
void member_current(sqlite3* db,std::uint64_t room,const T::Member& m){const auto& i=m.input.identity;
    Statement q(db,"SELECT account,session,world_generation,battle_generation,channel,actor_handle,primary_slot,secondary_slot,status,grant_epoch,primary_grant,secondary_grant,source_document FROM main.owned_pve_members WHERE room=? AND character=?");
    q.bind_id(1,room);q.bind_id(2,i.character);need(q.row(),"PvE canonical member mirror missing");
    need(q.number<std::uint64_t>(0)==i.account&&q.number<std::uint64_t>(1)==i.session&&q.number<std::uint64_t>(2)==i.world_generation&&
        q.number<std::uint64_t>(3)==i.battle_generation&&q.integer(4)==i.channel&&q.integer(5)==i.actor_handle&&q.integer(6)==m.input.primary_slot&&
        q.integer(7)==(m.input.pet?m.input.pet->actor_slot:-1)&&q.integer(8)==int(m.status)&&q.number<std::uint64_t>(9)==m.grant_epoch&&
        q.integer(10)==int(m.primary_grant)&&q.integer(11)==int(m.secondary_grant)&&q.text(12)==input_json(m.input).dump()&&!q.row(),
        "PvE whole member mirror CAS baseline changed");
}
void return_current(sqlite3* db,std::uint64_t room,const T::Member& m){
    Statement q(db,"SELECT sequence,context,completed FROM main.owned_pve_returns WHERE room=? AND character=?");q.bind_id(1,room);q.bind_id(2,m.input.identity.character);
    if(!m.return_context){need(!q.row(),"PvE unexpected return ledger row");return;}
    need(q.row(),"PvE original return context ledger missing");const auto b=q.blob(1,4,4);
    need(q.number<std::uint64_t>(0)==m.return_sequence&&std::equal(b.begin(),b.end(),m.return_context->begin())&&
        q.integer(2)==int(m.status==T::MemberStatus::Returned)&&!q.row(),"PvE original return ledger changed");
}
void room_mirrors(sqlite3* db,const T::Snapshot& s){
    Statement count(db,"SELECT count(*) FROM main.owned_pve_members WHERE room=?");count.bind_id(1,s.id);
    need(count.row()&&count.number<std::uint64_t>(0)==s.members.size()&&!count.row(),"PvE member mirror contains missing/extra rows");
    Statement returns(db,"SELECT count(*) FROM main.owned_pve_returns WHERE room=?");returns.bind_id(1,s.id);
    const auto expected=std::count_if(s.members.begin(),s.members.end(),[](const auto& p){return p.second.return_context.has_value();});
    need(returns.row()&&returns.number<std::uint64_t>(0)==std::uint64_t(expected)&&!returns.row(),"PvE return ledger contains missing/extra rows");
    for(const auto& [id,m]:s.members){(void)id;member_current(db,s.id,m);return_current(db,s.id,m);}
}
void insert_claim(sqlite3* db,std::uint64_t room,const T::Identity& i){Statement q(db,"INSERT INTO main.owned_pve_character_claims(character,room,account,session,battle_generation) VALUES(?,?,?,?,?)");q.bind_id(1,i.character);q.bind_id(2,room);q.bind_id(3,i.account);q.bind_id(4,i.session);q.bind_id(5,i.battle_generation);q.done();changed(db);}
void require_claim(sqlite3* db,std::uint64_t room,const T::Identity& i){Statement q(db,"SELECT room,account,session,battle_generation FROM main.owned_pve_character_claims WHERE character=?");q.bind_id(1,i.character);need(q.row()&&q.number<std::uint64_t>(0)==room&&q.number<std::uint64_t>(1)==i.account&&q.number<std::uint64_t>(2)==i.session&&q.number<std::uint64_t>(3)==i.battle_generation&&!q.row(),"PvE exact retained character claim changed");}
void write_output(sqlite3* db,std::uint64_t room,const T::Delivery& d){need(!d.logical.empty()&&d.logical.size()<=RecoveredWorldFrame::max_logical_size,"PvE outbox width invalid");(void)RecoveredWorldFrame::encode(d.logical);Statement q(db,"INSERT INTO main.owned_pve_outbox(room,sequence,character,kind,logical,status) VALUES(?,?,?,?,?,?)");q.bind_id(1,room);q.bind_id(2,d.sequence);q.bind_id(3,d.recipient.character);q.bind(4,int(d.kind));q.bind_blob(5,d.logical);q.bind(6,int(d.status));q.done();changed(db);}
void output_current(sqlite3* db,std::uint64_t room,const T::Delivery& d){Statement q(db,"SELECT character,kind,logical,status FROM main.owned_pve_outbox WHERE room=? AND sequence=?");q.bind_id(1,room);q.bind_id(2,d.sequence);need(q.row(),"PvE original durable output missing");const auto raw=q.blob(2,1,RecoveredWorldFrame::max_logical_size);need(q.number<std::uint64_t>(0)==d.recipient.character&&q.integer(1)==int(d.kind)&&std::vector<std::uint8_t>(raw.begin(),raw.end())==d.logical&&q.integer(3)==int(d.status)&&!q.row(),"PvE original output bytes/status changed");}
}
SqliteOwnedPveRoomRepository::Commit SqliteOwnedPveRoomRepository::activate(const Ticket& ticket,const Types::Snapshot& state,const Types::PureCurrent& current){
    Issuer::Operation op(*issuer_);need(ticket.data_->issuer==issuer_&&state.id==ticket.id()&&state.incarnation==ticket.incarnation()&&state.revision==1,"PvE activation private incarnation mismatch");
    structure(state);const auto text=document(state);op.final(current);need(sqlite3_get_autocommit(db_),"PvE activation needs own transaction");sqlite_detail::Transaction tx(db_);namespaces(db_);
    Statement prior(db_,"SELECT incarnation,revision,phase,document FROM main.owned_pve_rooms WHERE id=? AND design_id='CUSTOM-0161'");prior.bind_id(1,ticket.id());need(prior.row()&&prior.text(0)==ticket.incarnation()&&prior.integer(1)==0&&prior.text(2)=="reserved"&&prior.text(3).empty()&&!prior.row(),"PvE reservation changed before activation");
    for(const auto& [id,m]:state.members){need(id==m.input.identity.character&&m.status==Types::MemberStatus::Entering,"PvE initial member state invalid");validate_member(m.input);op.current();need(!characters_.owned_pending_battle(m.input.identity.account,id),"PvE character has a diagnostic reservation");insert_claim(db_,state.id,m.input.identity);write_member(db_,state.id,m,true);}
    for(const auto& d:state.outbox)write_output(db_,state.id,d);
    Statement update(db_,"UPDATE main.owned_pve_rooms SET revision=1,phase=?,document=? WHERE id=? AND incarnation=? AND revision=0 AND phase='reserved'");update.bind(1,phase(state));update.bind(2,text);update.bind_id(3,state.id);update.bind(4,state.incarnation);update.done();changed(db_);
    const auto final_changes=sqlite3_total_changes64(db_);
    for(const auto& [id,m]:state.members){(void)id;validate_member(m.input);require_claim(db_,state.id,m.input.identity);}for(const auto& d:state.outbox)output_current(db_,state.id,d);
    room_mirrors(db_,state);Statement verify(db_,"SELECT document FROM main.owned_pve_rooms WHERE id=? AND revision=1");verify.bind_id(1,state.id);need(verify.row()&&verify.text(0)==text&&!verify.row(),"PvE activated document readback mismatch");op.final(current);
    need(!sqlite3_get_autocommit(db_)&&sqlite3_total_changes64(db_)==final_changes,"PvE source changed during final complete readset/pure fence");op.current();tx.commit();
    return {true,op.after(current)&&sqlite3_get_autocommit(db_)&&sqlite3_total_changes64(db_)==final_changes};
}
SqliteOwnedPveRoomRepository::Commit SqliteOwnedPveRoomRepository::replace(const Ticket& ticket,const Types::Snapshot& before,const Types::Snapshot& after,const Types::PureCurrent& current){
    Issuer::Operation op(*issuer_);need(ticket.data_->issuer==issuer_&&before.id==ticket.id()&&after.id==before.id&&before.incarnation==ticket.incarnation()&&after.incarnation==before.incarnation&&after.revision==next_revision(before.revision),"PvE replace private incarnation/revision mismatch");
    need(after.source_sha256==before.source_sha256&&after.source_record==before.source_record&&after.checkpoint.snapshot.id==before.checkpoint.snapshot.id&&after.members.size()>=before.members.size(),"PvE immutable encounter/member history changed");
    structure(before);structure(after);const auto old_text=document(before),new_text=document(after);op.final(current);need(sqlite3_get_autocommit(db_),"PvE replacement needs own transaction");sqlite_detail::Transaction tx(db_);namespaces(db_);
    Statement original(db_,"SELECT incarnation,revision,phase,document FROM main.owned_pve_rooms WHERE id=? AND design_id='CUSTOM-0161'");original.bind_id(1,before.id);need(original.row()&&original.text(0)==before.incarnation&&original.number<std::uint64_t>(1)==before.revision&&original.text(2)==phase(before)&&original.text(3)==old_text&&!original.row(),"PvE whole durable room CAS baseline changed");
    room_mirrors(db_,before);
    for(const auto& [id,m]:before.members){need(after.members.contains(id),"PvE member history removed");if(!released(m)){validate_member(m.input);require_claim(db_,before.id,m.input.identity);}op.current();}
    for(const auto& d:before.outbox)output_current(db_,before.id,d);
    for(const auto& [id,m]:after.members){const auto old=before.members.find(id);
        if(old==before.members.end()){need(m.status==Types::MemberStatus::Entering,"PvE late member not entering");validate_member(m.input);need(!characters_.owned_pending_battle(m.input.identity.account,id),"PvE helper has a diagnostic reservation");insert_claim(db_,after.id,m.input.identity);write_member(db_,after.id,m,true);continue;}
        const auto& b=old->second;need(m.input.identity==b.input.identity,"PvE member identity changed without actual rebind custody");
        auto expected=b.input;if(!released(m)&&m.status!=Types::MemberStatus::Withdrawn)expected=updated_resources(std::move(expected),after.checkpoint.snapshot,false);
        need(input_json(expected)==input_json(m.input),"PvE resource delta changed non-resource material/revision");
        if(released(b)){need(m.status==b.status&&m.grant_epoch==b.grant_epoch&&m.primary_grant==b.primary_grant&&
            m.secondary_grant==b.secondary_grant&&m.disconnected==b.disconnected&&m.return_context==b.return_context&&
            m.return_sequence==b.return_sequence,"PvE immutable released member history rewritten");continue;}
        if(m.input.resources!=b.input.resources){const auto& r=b.input.resources;const auto& n=m.input.resources;
            Statement q(db_,"UPDATE main.character_resources SET hp=?,mp=?,revision=? WHERE character_id=? AND hp=? AND max_hp=? AND mp=? AND max_mp=? AND revision=? AND design_id=?");q.bind_id(1,n.hp);q.bind_id(2,n.mp);q.bind_id(3,n.revision);q.bind_id(4,id);q.bind_id(5,r.hp);q.bind_id(6,r.max_hp);q.bind_id(7,r.mp);q.bind_id(8,r.max_mp);q.bind_id(9,r.revision);q.bind(10,r.design_id);q.done();changed(db_);}
        if(m.input.pet&&pet_json(*m.input.pet)!=pet_json(*b.input.pet)){const auto& p=b.input.pet->saved;const auto& n=m.input.pet->saved;const auto old_stats=pet_stats(p),new_stats=pet_stats(n);const auto metadata=pet_metadata(p);
            Statement q(db_,"UPDATE main.character_pet2_slots SET stats=?,revision=?,authority=?,evidence_id=? WHERE character_id=? AND slot=? AND metadata=? AND stats=? AND revision=? AND source_sha256=? AND authority=? AND evidence_id=?");q.bind_blob(1,new_stats);q.bind_id(2,n.revision);q.bind(3,n.provenance.authority);q.bind(4,n.provenance.evidence_id);q.bind_id(5,id);q.bind(6,p.slot);q.bind_blob(7,metadata);q.bind_blob(8,old_stats);q.bind_id(9,p.revision);q.bind(10,p.provenance.source_sha256);q.bind(11,p.provenance.authority);q.bind(12,p.provenance.evidence_id);q.done();changed(db_);}
        write_member(db_,after.id,m,false);
        if(released(m)){
            if(m.status==Types::MemberStatus::Returned){need(m.return_context&&m.return_sequence&&b.return_context==m.return_context&&b.return_sequence==m.return_sequence,"PvE return release changed retained context");
                const auto receipt=std::find_if(before.outbox.begin(),before.outbox.end(),[&](const auto& d){return d.sequence==m.return_sequence;});
                need(receipt!=before.outbox.end()&&receipt->kind==Types::OutputKind::Return&&receipt->recipient==m.input.identity&&receipt->status==Types::OutputStatus::Written&&
                    std::all_of(before.outbox.begin(),before.outbox.end(),[&](const auto& d){return d.recipient!=m.input.identity||d.kind!=Types::OutputKind::Return||
                        (d.sequence<=m.return_sequence&&d.status==Types::OutputStatus::Written);}),"PvE return claim release lacks all original durable aggregate fullwrites");}
            else need(m.disconnected&&!m.primary_grant&&!m.secondary_grant&&std::none_of(after.outbox.begin(),after.outbox.end(),[&](const auto& d){return d.recipient==m.input.identity&&d.status==Types::OutputStatus::Pending;}),"PvE disconnect release retained live input/output");
            Statement q(db_,"DELETE FROM main.owned_pve_character_claims WHERE character=? AND room=? AND account=? AND session=? AND battle_generation=?");q.bind_id(1,id);q.bind_id(2,after.id);q.bind_id(3,m.input.identity.account);q.bind_id(4,m.input.identity.session);q.bind_id(5,m.input.identity.battle_generation);q.done();changed(db_);}
    }
    for(const auto& old:before.outbox){const auto now=std::find_if(after.outbox.begin(),after.outbox.end(),[&](const auto& d){return d.sequence==old.sequence;});
        const auto status=now==after.outbox.end()?(old.status==Types::OutputStatus::Pending?Types::OutputStatus::Written:old.status):now->status;
        if(now!=after.outbox.end())need(now->recipient==old.recipient&&now->kind==old.kind&&now->logical==old.logical,"PvE output bytes/incarnation rewritten");
        need(old.status==Types::OutputStatus::Pending||status==old.status,"PvE final output receipt rewritten");
        if(status!=old.status){Statement q(db_,"UPDATE main.owned_pve_outbox SET status=? WHERE room=? AND sequence=? AND status=?");q.bind(1,int(status));q.bind_id(2,after.id);q.bind_id(3,old.sequence);q.bind(4,int(old.status));q.done();changed(db_);}}
    for(const auto& d:after.outbox)if(std::none_of(before.outbox.begin(),before.outbox.end(),[&](const auto& old){return old.sequence==d.sequence;})){need(d.sequence>=before.next_sequence&&d.status==Types::OutputStatus::Pending,"PvE new output has no original pending status");write_output(db_,after.id,d);}
    for(const auto& [id,m]:after.members)if(m.return_context){const auto old=before.members.find(id);const bool fresh=old==before.members.end()||!old->second.return_context;
        Statement q(db_,fresh?"INSERT INTO main.owned_pve_returns(sequence,context,completed,room,character) VALUES(?,?,?,?,?)":"UPDATE main.owned_pve_returns SET sequence=?,context=?,completed=? WHERE room=? AND character=?");q.bind_id(1,m.return_sequence);q.bind_blob(2,*m.return_context);q.bind(3,m.status==Types::MemberStatus::Returned?1:0);q.bind_id(4,after.id);q.bind_id(5,id);q.done();changed(db_);}
    Statement update(db_,"UPDATE main.owned_pve_rooms SET revision=?,phase=?,document=? WHERE id=? AND incarnation=? AND revision=? AND document=?");update.bind_id(1,after.revision);update.bind(2,phase(after));update.bind(3,new_text);update.bind_id(4,after.id);update.bind(5,after.incarnation);update.bind_id(6,before.revision);update.bind(7,old_text);update.done();changed(db_);
    const auto final_changes=sqlite3_total_changes64(db_);
    for(const auto& [id,m]:after.members){const auto old=before.members.find(id);
        if(!released(m)){validate_member(m.input);require_claim(db_,after.id,m.input.identity);}
        else if(old!=before.members.end()&&!released(old->second)){
            // Newly released source is still part of THIS all-member commit.
            // Historical members released earlier may now change independently.
            validate_member(m.input);Statement absent(db_,"SELECT 1 FROM main.owned_pve_character_claims WHERE character=?");
            absent.bind_id(1,id);need(!absent.row(),"PvE newly released claim reappeared before final fence");
        }
    }for(const auto& d:after.outbox)output_current(db_,after.id,d);
    room_mirrors(db_,after);
    Statement verify(db_,"SELECT document FROM main.owned_pve_rooms WHERE id=? AND revision=?");verify.bind_id(1,after.id);verify.bind_id(2,after.revision);need(verify.row()&&verify.text(0)==new_text&&!verify.row(),"PvE full committed candidate readback mismatch");
    op.final(current);need(!sqlite3_get_autocommit(db_)&&sqlite3_total_changes64(db_)==final_changes,
        "PvE source changed during final complete readset/pure fence");op.current();tx.commit();
    return {true,op.after(current)&&sqlite3_get_autocommit(db_)&&sqlite3_total_changes64(db_)==final_changes};
}
bool SqliteOwnedPveRoomRepository::character_claimed(std::uint64_t account,std::uint64_t character){Issuer::Operation op(*issuer_);namespaces(db_);Statement q(db_,"SELECT account FROM main.owned_pve_character_claims WHERE character=?");q.bind_id(1,character);const bool exists=q.row();if(exists)need(q.number<std::uint64_t>(0)==account&&!q.row(),"PvE character claim belongs to another account");op.current();return exists;}
OwnedPveRoomTypes::Snapshot SqliteOwnedPveRoomRepository::read_retained(std::uint64_t id){Issuer::Operation op(*issuer_);namespaces(db_);Statement q(db_,"SELECT incarnation,revision,phase,document FROM main.owned_pve_rooms WHERE id=? AND phase IN ('active','finished','closed') AND design_id='CUSTOM-0161'");q.bind_id(1,id);need(q.row(),"PvE retained history unavailable");const auto incarnation=q.text(0),state_phase=q.text(2),text=q.text(3);const auto revision=q.number<std::uint64_t>(1);auto state=document(text);need(state.id==id&&state.incarnation==incarnation&&state.revision==revision&&phase(state)==state_phase&&!q.row(),"PvE retained state metadata mismatch");op.current();return state;}
}
