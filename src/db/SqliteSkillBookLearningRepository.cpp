#include "db/SqliteSkillBookLearningRepository.h"
#include "db/SqliteSupport.h"
#include "game/TaiwanOwnedBagItemMaterial.h"
#include <algorithm>
#include <array>
#include <limits>
#include <string_view>

namespace god2 {
namespace {
using sqlite_detail::Statement;
constexpr char design[]="CUSTOM-0148";
constexpr char alias_profile[]="tw149c-item20";
constexpr std::uint64_t revision_limit=std::numeric_limits<std::int64_t>::max();
bool has_book_material(const OwnedInventoryInstance& original,std::uint8_t slot) {
    auto projection=original;projection.aliases.clear();
    for(const auto& alias:original.aliases)
        if(alias.client_sha256==NativeEquipmentSnapshot::client_pin&&
           (alias.profile==alias_profile||alias.profile==TaiwanOwnedBagItemMaterial::profile))projection.aliases.push_back(alias);
    return TaiwanOwnedBagItemMaterial::observe(projection,slot).has_value();
}
std::uint64_t advance(std::uint64_t value) {
    if(!value||value>=revision_limit)throw DatabaseError("Skill book revision overflow");
    return value+1;
}
std::vector<std::uint8_t> skill_bytes(const StoredDeity& row) {
    std::vector<std::uint8_t> result;result.reserve(row.snapshot.skills.size()*4);
    for(const auto& skill:row.snapshot.skills)result.insert(result.end(),skill.encode().begin(),skill.encode().end());
    return result;
}
std::vector<std::uint8_t> row_bytes(const StoredDeity& row) {
    std::vector<std::uint8_t> result;result.reserve(48+row.snapshot.skills.size()*4);
    result.insert(result.end(),row.snapshot.declaration.encode().begin(),row.snapshot.declaration.encode().end());
    result.insert(result.end(),row.snapshot.status.encode().begin(),row.snapshot.status.encode().end());
    for(const auto& skill:row.snapshot.skills)result.insert(result.end(),skill.encode().begin(),skill.encode().end());
    return result;
}
struct ActivationEvent {
    SqliteSkillBookLearningRepository::Activation activation;
    std::uint64_t account{},character{},book_instance{},book_revision{},deity_revision{};
    std::uint16_t item{};
    std::string source,record_sha,parsed_sha;
    std::vector<std::uint8_t> raw,parsed;
    bool operator==(const ActivationEvent&) const=default;
};
struct ActivationHeader {
    std::uint8_t subject{};
    std::uint64_t revision{};
    CompanionProvenance provenance;
    std::vector<std::uint8_t> raw;
    std::vector<ActivationEvent> events;
    bool operator==(const ActivationHeader&) const=default;
};
std::string bounded_text(Statement& s,int column,std::size_t limit) {
    auto text=s.text(column);
    if(text.empty()||text.size()>limit||text.find('\0')!=std::string::npos)
        throw DatabaseError("Malformed skill book event text");
    return text;
}
std::vector<ActivationHeader> headers(sqlite3* db,std::uint64_t account,std::uint64_t character) {
    std::vector<ActivationHeader> result;
    Statement rows(db,"SELECT row_key,deity_revision,raw_row,source_sha256,authority,evidence_id,design FROM main.deity_skill_activation_headers WHERE character_id=? ORDER BY row_key");
    rows.bind_id(1,character);
    while(rows.row()) {
        ActivationHeader header;
        header.subject=rows.number<std::uint8_t>(0);header.revision=rows.number<std::uint64_t>(1);
        const auto raw=rows.blob(2,48,448);header.raw.assign(raw.begin(),raw.end());
        header.provenance={bounded_text(rows,3,64),bounded_text(rows,4,64),bounded_text(rows,5,512)};
        if(!header.revision||rows.text(6)!=design||header.raw.size()%4||header.raw[0]!=0x30||header.raw[19]!=0x31||
           header.raw[20]!=header.subject||!RecoveredDeityState::has_current_portrait(header.subject))
            throw DatabaseError("Malformed skill activation header");
        for(std::size_t offset=48;offset<header.raw.size();offset+=4)
            if(header.raw[offset]!=0x34||header.raw[offset+1]!=header.subject)
                throw DatabaseError("Malformed activation header saved skill");
        Statement events(db,"SELECT l.ordinal,e.event_id,e.account_id,e.character_id,e.row_key,e.kind,e.skill_id,e.book_item,e.book_instance,e.book_revision,e.deity_before_revision,e.book_source,e.record_sha256,e.parsed_sha256,e.raw_book,e.parsed_book,e.design FROM main.deity_skill_activation_links l JOIN main.skill_book_learning_events e ON e.event_id=l.event_id WHERE l.character_id=? AND l.row_key=? ORDER BY l.ordinal");
        events.bind_id(1,character);events.bind(2,header.subject);
        while(events.row()) {
            ActivationEvent event;
            if(events.number<std::size_t>(0)!=header.events.size())throw DatabaseError("Malformed activation order");
            event.activation.event_id=bounded_text(events,1,512);
            event.account=events.number<std::uint64_t>(2);event.character=events.number<std::uint64_t>(3);
            event.activation.subject=events.number<std::uint8_t>(4);event.activation.kind=events.number<std::uint8_t>(5);
            event.activation.definition_id=events.number<std::uint8_t>(6);event.item=events.number<std::uint16_t>(7);
            event.book_instance=events.number<std::uint64_t>(8);event.book_revision=events.number<std::uint64_t>(9);
            event.deity_revision=events.number<std::uint64_t>(10);event.source=bounded_text(events,11,64);
            event.record_sha=bounded_text(events,12,64);event.parsed_sha=bounded_text(events,13,64);
            const auto raw_book=events.blob(14,1,4095),parsed=events.blob(15,396,396);
            event.raw.assign(raw_book.begin(),raw_book.end());event.parsed.assign(parsed.begin(),parsed.end());
            const auto& a=event.activation;
            if(events.text(16)!=design||event.account!=account||event.character!=character||a.subject!=header.subject||
               a.kind>=4||!a.definition_id||!event.book_instance||!event.book_revision||!event.deity_revision||
               event.item<6501||event.item>7199||event.source!=SqliteCompanionRepository::source_sha256||
               event.record_sha.size()!=64||event.parsed_sha.size()!=64)
                throw DatabaseError("Malformed skill book learning event");
            bool found=false;
            for(std::size_t at=48;at<header.raw.size();at+=4)
                if(header.raw[at+2]==a.kind&&header.raw[at+3]==a.definition_id)found=true;
            if(!found)throw DatabaseError("Activation event has no matching saved skill");
            for(const auto& prior:header.events)
                if(prior.activation.kind==a.kind&&prior.activation.definition_id==a.definition_id)
                    throw DatabaseError("Duplicate skill activation");
            header.events.push_back(std::move(event));
            if(header.events.size()>RecoveredDeityState::skill_capacity)throw DatabaseError("Too many skill activations");
        }
        Statement count(db,"SELECT count(*) FROM main.deity_skill_activation_links WHERE character_id=? AND row_key=?");
        count.bind_id(1,character);count.bind(2,header.subject);
        if(!count.row()||count.number<std::size_t>(0)!=header.events.size()||count.row())
            throw DatabaseError("Dangling skill activation event");
        result.push_back(std::move(header));
        if(result.size()>256)throw DatabaseError("Too many activation headers");
    }
    Statement orphan(db,"SELECT 1 FROM main.deity_skill_activation_links l LEFT JOIN main.deity_skill_activation_headers h ON h.character_id=l.character_id AND h.row_key=l.row_key WHERE l.character_id=? AND h.character_id IS NULL LIMIT 1");
    orphan.bind_id(1,character);if(orphan.row())throw DatabaseError("Orphan skill activation link");
    return result;
}
bool coherent_bank(const OwnedInventorySnapshot& inventory,const NativeEquipmentSnapshot& equipment) {
    if(equipment.record.size()!=NativeEquipmentSnapshot::record_bytes||
       !NativeEquipmentSnapshot::same_root(inventory.root,equipment.root))return false;
    for(const auto& cell:inventory.cells)if(cell.instance)for(const auto& alias:cell.instance->aliases)
        if(alias.client_sha256==NativeEquipmentSnapshot::client_pin&&alias.profile==alias_profile&&alias.native_slot>=50)return false;
    for(std::size_t slot=0;slot<50;++slot) {
        const auto at=slot*24;const auto count=equipment.record[at];
        const auto key=std::uint16_t(equipment.record[at+4]+256u*equipment.record[at+5]);
        std::size_t found=0;
        for(const auto& cell:inventory.cells)if(cell.instance)for(const auto& alias:cell.instance->aliases) {
            const auto& item=*cell.instance;
            if(alias.client_sha256!=NativeEquipmentSnapshot::client_pin||alias.profile!=alias_profile||alias.native_slot!=slot)continue;
            if(!count||count>99||!key||item.quantity!=count||(!item.stackable&&count!=1)||alias.native_key!=key||
               alias.revision!=item.revision||alias.record.size()!=20||
               !std::equal(alias.record.begin(),alias.record.end(),equipment.record.begin()+at+4))return false;
            ++found;
        }
        if(count?(!key||found!=1):(key||found))return false;
    }
    return true;
}
struct ReadScope {
    sqlite3* db;bool done=false;
    explicit ReadScope(sqlite3* value):db(value) {if(!sqlite3_get_autocommit(db))throw DatabaseError("Skill book read requires own transaction");sqlite_detail::execute(db,"BEGIN");}
    ~ReadScope(){if(!done)sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);}
    void finish(){sqlite_detail::execute(db,"COMMIT");done=true;}
};
}

struct SqliteSkillBookLearningRepository::State {
    const SqliteSkillBookLearningRepository* repository;
    std::weak_ptr<const std::uint8_t> identity;
    OwnedInventorySnapshot inventory;
    NativeEquipmentSnapshot equipment;
    OwnedDeityRosterReadset roster;
    std::vector<ActivationHeader> headers;
    std::vector<Activation> activations;
};
struct SqliteSkillBookLearningRepository::ObservationData {
    std::shared_ptr<const State> state;
    std::size_t deity_index,cell_index;
    std::uint8_t slot;
    NativeSkillBookRecord book;
    SharedSkillDefinition common;
    bool learned;
};
struct SqliteSkillBookLearningRepository::PlanData {
    std::shared_ptr<const ObservationData> before;
    std::shared_ptr<const State> after;
    RecoveredDeityState::Skill skill;
    ActivationEvent event;
    RecoveredInventory::SlotUpdate update;
};
struct SqliteSkillBookLearningRepository::Operation {
    enum class Scope {Own,ExistingTransactionRead};
    SqliteSkillBookLearningRepository& repo;
    const Scope scope;
    explicit Operation(SqliteSkillBookLearningRepository& value,Scope mode=Scope::Own):repo(value),scope(mode) {
        repo.owner();
        if(repo.busy_||repo.inventory_.writing_||repo.equipment_.writing_||repo.companions_.readset_reading_||
           (scope==Scope::ExistingTransactionRead&&(repo.inventory_.issuer_active_||repo.equipment_.issuer_active_))) {
            repo.poisoned_=true;repo.inventory_.reentered_=repo.equipment_.reentered_=true;
            repo.companions_.readset_reentered_=true;throw DatabaseError("Skill book operation reentered");
        }
        if(scope==Scope::Own) {
            if(!sqlite3_get_autocommit(repo.inventory_.db_))throw DatabaseError("Skill book operation requires own transaction");
        } else if(sqlite3_get_autocommit(repo.inventory_.db_))
            throw DatabaseError("Skill book closed restoration requires existing transaction");
        repo.busy_=true;repo.poisoned_=false;
        repo.inventory_.writing_=repo.equipment_.writing_=true;
        repo.inventory_.reentered_=repo.equipment_.reentered_=false;
    }
    ~Operation(){repo.busy_=false;repo.inventory_.writing_=repo.equipment_.writing_=false;
        if(scope==Scope::Own)repo.inventory_.issuer_active_=repo.equipment_.issuer_active_=false;}
};

SqliteSkillBookLearningRepository::SqliteSkillBookLearningRepository(SqliteOwnedInventoryRepository& inventory,
    SqliteNativeEquipmentSnapshotRepository& equipment,SqliteCompanionRepository& companions,
    const NativeSkillBookCatalog& books,const NativeSkillCatalog& skills)
    :inventory_(inventory),equipment_(equipment),companions_(companions),books_(books),skills_(skills) {
    owner();
    if(inventory_.db_!=equipment_.db_||&inventory_.accounts_!=&equipment_.accounts_||
       &inventory_.characters_!=&equipment_.characters_||!companions_.uses_connection(inventory_.db_)||
       !books_.uses_connection(inventory_.db_)||!skills_.uses_connection(inventory_.db_))
        throw DatabaseError("Skill book learning requires the same actual common sources");
}
void SqliteSkillBookLearningRepository::owner() const {
    if(std::this_thread::get_id()!=thread_)throw DatabaseError("Skill book learning requires its game thread");
    inventory_.owner();equipment_.owner();
}
std::string SqliteSkillBookLearningRepository::schema() {
    return R"SQL(
CREATE TABLE main.skill_book_learning_events(
 event_id TEXT PRIMARY KEY,account_id INTEGER NOT NULL,character_id INTEGER NOT NULL,
 row_key INTEGER NOT NULL CHECK(row_key BETWEEN 1 AND 255),kind INTEGER NOT NULL CHECK(kind BETWEEN 0 AND 3),
 skill_id INTEGER NOT NULL CHECK(skill_id BETWEEN 1 AND 255),book_item INTEGER NOT NULL CHECK(book_item BETWEEN 6501 AND 7199),
 book_instance INTEGER NOT NULL,book_revision INTEGER NOT NULL,deity_before_revision INTEGER NOT NULL,
 book_source TEXT NOT NULL,record_sha256 TEXT NOT NULL,parsed_sha256 TEXT NOT NULL,
 raw_book BLOB NOT NULL,parsed_book BLOB NOT NULL CHECK(length(parsed_book)=396),
 design TEXT NOT NULL CHECK(design='CUSTOM-0148'),
 FOREIGN KEY(character_id) REFERENCES recovered_characters(id));
CREATE TABLE main.deity_skill_activation_headers(
 character_id INTEGER NOT NULL,row_key INTEGER NOT NULL,deity_revision INTEGER NOT NULL,
 raw_row BLOB NOT NULL,source_sha256 TEXT NOT NULL,authority TEXT NOT NULL,evidence_id TEXT NOT NULL,
 design TEXT NOT NULL CHECK(design='CUSTOM-0148'),PRIMARY KEY(character_id,row_key),
 FOREIGN KEY(character_id) REFERENCES recovered_characters(id));
CREATE TABLE main.deity_skill_activation_links(
 character_id INTEGER NOT NULL,row_key INTEGER NOT NULL,ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 99),
 event_id TEXT NOT NULL UNIQUE,PRIMARY KEY(character_id,row_key,ordinal),
 FOREIGN KEY(character_id,row_key) REFERENCES deity_skill_activation_headers(character_id,row_key),
 FOREIGN KEY(event_id) REFERENCES skill_book_learning_events(event_id));
)SQL";
}
void SqliteSkillBookLearningRepository::namespaces() const {
    auto* db=inventory_.db_;
    constexpr const char* names="('accounts','recovered_characters','recovered_positions','battle_reservations','battle_settlements','owned_inventory_headers','owned_item_instances','owned_inventory_cells','owned_item_native_aliases','character_native_equipment_snapshots','native_companion_metadata','character_deities','character_deity_selection','native_skill_book_bindings','native_skill_books','native_data_sources','native_skill_catalog','skill_book_learning_events','deity_skill_activation_headers','deity_skill_activation_links')";
    const std::string shadow_sql=std::string("SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ")+names+" OR tbl_name COLLATE NOCASE IN "+names;
    Statement shadow(db,shadow_sql.c_str());if(shadow.row())throw DatabaseError("Skill book TEMP shadow rejected");
    const std::string tables_sql=std::string("SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ")+names;
    Statement tables(db,tables_sql.c_str());
    if(!tables.row()||tables.integer(0)!=20||tables.row())throw DatabaseError("Skill book requires actual installed main tables");
    const std::string trigger_sql=std::string("SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name COLLATE NOCASE IN ")+names;
    Statement triggers(db,trigger_sql.c_str());if(triggers.row())throw DatabaseError("Skill book source-table triggers rejected");
    if(poisoned_||inventory_.reentered_||equipment_.reentered_||sqlite3_get_autocommit(db))
        throw DatabaseError("Skill book source reentered or lost transaction");
}

std::shared_ptr<SqliteSkillBookLearningRepository::State> SqliteSkillBookLearningRepository::read_state(OwnedDeityRosterReadset roster) {
    const auto changes=sqlite3_total_changes64(inventory_.db_);
    namespaces();
    if(!companions_.deity_roster_current_in_transaction(roster))throw DatabaseError("Skill book saved roster changed");
    auto inventory=inventory_.load(roster.account(),roster.character());
    auto equipment=equipment_.load(roster.account(),roster.character(),NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind);
    if(!inventory||!equipment||!coherent_bank(*inventory,*equipment)||!inventory_.root_current(inventory->root)||
       inventory_.characters_.load_position(roster.account(),roster.character())!=std::optional{equipment->position})
        throw DatabaseError("Skill book requires complete current owned inventory material");
    companions_.require_no_pending_battle(roster.character());
    auto stored=headers(inventory_.db_,roster.account(),roster.character());
    std::vector<Activation> active;
    for(const auto& header:stored) {
        const auto row=std::find_if(roster.rows().begin(),roster.rows().end(),[&](const auto& value){return value.snapshot.status.key_raw()==header.subject;});
        if(row==roster.rows().end()||row->revision!=header.revision||row->provenance!=header.provenance||row_bytes(*row)!=header.raw)continue;
        for(const auto& event:header.events) {
            const auto book=books_.lookup_item(event.item);
            if(!book||book->kind!=event.activation.kind||book->definition_id!=event.activation.definition_id||
               book->source.source_sha256!=event.source||book->record_sha256!=event.record_sha||book->parsed_sha256!=event.parsed_sha||
               book->raw_record!=event.raw||book->parsed_record!=event.parsed)
                throw DatabaseError("Skill activation book source changed");
            active.push_back(event.activation);
        }
    }
    auto result=std::make_shared<State>(State{this,identity_,std::move(*inventory),std::move(*equipment),std::move(roster),std::move(stored),std::move(active)});
    if(!state_current(*result)||sqlite3_total_changes64(inventory_.db_)!=changes)throw DatabaseError("Skill book observation changed before completion");
    return result;
}
bool SqliteSkillBookLearningRepository::state_current(const State& wanted) {
    const auto changes=sqlite3_total_changes64(inventory_.db_);
    namespaces();
    if(wanted.repository!=this||wanted.identity.lock()!=identity_||
       !companions_.deity_roster_current_in_transaction(wanted.roster))return false;
    const auto account=wanted.roster.account(),character=wanted.roster.character();
    const auto equipment=equipment_.load(account,character,NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind);
    const auto inventory=inventory_.load(account,character);
    if(equipment!=std::optional{wanted.equipment}||inventory!=std::optional{wanted.inventory}||
       headers(inventory_.db_,account,character)!=wanted.headers||!inventory_.root_current(wanted.inventory.root)||
       inventory_.characters_.load_position(account,character)!=std::optional{wanted.equipment.position})return false;
    for(const auto& header:wanted.headers) {
        const auto row=std::find_if(wanted.roster.rows().begin(),wanted.roster.rows().end(),[&](const auto& d){return d.snapshot.status.key_raw()==header.subject;});
        if(row==wanted.roster.rows().end()||row->revision!=header.revision||row->provenance!=header.provenance||row_bytes(*row)!=header.raw)continue;
        for(const auto& event:header.events) {
            const auto book=books_.lookup_item(event.item);
            if(!book||book->kind!=event.activation.kind||book->definition_id!=event.activation.definition_id||
               book->source.source_sha256!=event.source||book->record_sha256!=event.record_sha||book->parsed_sha256!=event.parsed_sha||
               book->raw_record!=event.raw||book->parsed_record!=event.parsed)return false;
        }
    }
    companions_.require_no_pending_battle(character);
    namespaces();return companions_.deity_roster_current_in_transaction(wanted.roster)&&sqlite3_total_changes64(inventory_.db_)==changes;
}
bool SqliteSkillBookLearningRepository::observation_current(const ObservationData& wanted) {
    if(!state_current(*wanted.state))return false;
    const auto book=books_.lookup_item(wanted.book.item_id);
    const auto common=skills_.lookup_shared_definition_main(wanted.book.kind,wanted.book.definition_id);
    const auto native=skills_.lookup_main_digest_checked(skills_.taiwan_dataset_id(),wanted.book.kind,wanted.book.definition_id);
    return book==std::optional{wanted.book}&&common&&native&&common->requested_native==native&&
        common->definition==wanted.common&&state_current(*wanted.state);
}
std::optional<NativeSkillBookRecord> SqliteSkillBookLearningRepository::lookup_book(std::uint16_t item) const {
    owner();
    if(busy_){poisoned_=true;throw DatabaseError("Skill book lookup reentered coordinator");}
    return books_.lookup_item(item);
}
SqliteSkillBookLearningRepository::Restoration SqliteSkillBookLearningRepository::restore(std::uint64_t account,std::uint64_t character) {
    Operation operation(*this);
    auto roster=companions_.load_deity_roster(account,character);
    ReadScope read(inventory_.db_);auto state=read_state(std::move(roster));
    Restoration result(std::move(state));read.finish();return result;
}
bool SqliteSkillBookLearningRepository::restoration_current(const Restoration& value) {
    Operation operation(*this);ReadScope read(inventory_.db_);
    const bool same=state_current(*value.state_);read.finish();return same;
}
bool SqliteSkillBookLearningRepository::restoration_current_in_transaction(
    const Restoration& value,sqlite3* actual_connection) {
    owner();
    const auto owned=value; // Retain the original private issuer before SQL hooks.
    if(!actual_connection||actual_connection!=inventory_.db_||!owned.state_||
       owned.state_->repository!=this||owned.state_->identity.lock()!=identity_)return false;
    Operation operation(*this,Operation::Scope::ExistingTransactionRead);
    const auto changes=sqlite3_total_changes64(actual_connection);
    const bool same=state_current(*owned.state_);
    namespaces();
    return same&&owned.state_->repository==this&&owned.state_->identity.lock()==identity_&&
        sqlite3_total_changes64(actual_connection)==changes;
}
std::optional<SqliteSkillBookLearningRepository::Observation> SqliteSkillBookLearningRepository::observe(
    std::uint64_t account,std::uint64_t character,std::uint8_t slot,std::uint16_t item) {
    Operation operation(*this);
    if(slot>=30)return std::nullopt; // CUSTOM-0148 ordinary bag only, not equipment slots.
    auto roster=companions_.load_deity_roster(account,character);
    ReadScope read(inventory_.db_);auto state=read_state(std::move(roster));
    const auto book=books_.lookup_item(item);
    if(!book||!state->roster.selection())return std::nullopt;
    const auto selected=std::find_if(state->roster.rows().begin(),state->roster.rows().end(),[&](const auto& value){return value.snapshot.status.key_raw()==state->roster.selection()->key;});
    if(selected==state->roster.rows().end())throw DatabaseError("Skill book selection is dangling");
    if(!RecoveredDeityState::has_current_skill_icon(book->kind,book->definition_id))return std::nullopt;
    const auto common=skills_.lookup_shared_definition_main(book->kind,book->definition_id);
    const auto native=skills_.lookup_main_digest_checked(skills_.taiwan_dataset_id(),book->kind,book->definition_id);
    if(!common||!native||common->requested_native!=native||!common->definition.chosen_profile)return std::nullopt;
    if(std::none_of(common->definition.profiles.begin(),common->definition.profiles.end(),[&](const auto& profile){
        // Original skills only: installed equivalence retains the exact original
        // bytes under its own453 epoch; reserves/custom/CN never become rights.
        return profile.region==SharedSkillRegion::Taiwan&&
            native_taiwan_skill_source_matches(profile.source,skills_.taiwan_profile())&&
            ((skills_.taiwan_profile()==NativeTaiwanSkillProfile::Historical448&&
              profile.qualification==SharedSkillRowQualification::OriginalRowPinned)||
             (skills_.taiwan_profile()==NativeTaiwanSkillProfile::Installed453&&
              profile.qualification==SharedSkillRowQualification::InstalledEquivalentRowPinned));
    }))return std::nullopt;
    std::optional<std::size_t> cell_index;
    for(std::size_t index=0;index<state->inventory.cells.size();++index) {
        const auto& cell=state->inventory.cells[index];if(!cell.instance)continue;
        for(const auto& alias:cell.instance->aliases)if(alias.client_sha256==NativeEquipmentSnapshot::client_pin&&alias.profile==alias_profile&&alias.native_slot==slot) {
            if(cell_index)throw DatabaseError("Duplicate book slot alias");
            if(alias.native_key!=item||cell.location_kind!="bag"||cell.location_index!=slot||
               !has_book_material(*cell.instance,slot))return std::nullopt;
            cell_index=index;
        }
    }
    if(!cell_index)return std::nullopt;
    const bool learned=std::any_of(selected->snapshot.skills.begin(),selected->snapshot.skills.end(),[&](const auto& skill){return skill.encode()[2]==book->kind&&skill.encode()[3]==book->definition_id;});
    auto data=std::make_shared<ObservationData>(ObservationData{state,static_cast<std::size_t>(selected-state->roster.rows().begin()),*cell_index,slot,*book,common->definition,learned});
    if(!observation_current(*data))return std::nullopt;
    std::optional<Observation> result{Observation(std::move(data))};read.finish();return result;
}
bool SqliteSkillBookLearningRepository::current(const Observation& value) {
    Operation operation(*this);ReadScope read(inventory_.db_);
    const bool same=observation_current(*value.data_);read.finish();return same;
}

std::optional<SqliteSkillBookLearningRepository::Plan> SqliteSkillBookLearningRepository::plan(const Observation& value) {
    Operation operation(*this);ReadScope read(inventory_.db_);
    const auto before=value.data_;
    if(!observation_current(*before)||before->learned)return std::nullopt;
    auto after=std::make_shared<State>(*before->state);
    auto rows=after->roster.rows();auto& deity=rows[before->deity_index];
    if(deity.snapshot.skills.size()>=RecoveredDeityState::skill_capacity)return std::nullopt;
    const auto subject=deity.snapshot.status.key_raw();
    const std::array<std::uint8_t,4> raw_skill{0x34,subject,static_cast<std::uint8_t>(before->book.kind),static_cast<std::uint8_t>(before->book.definition_id)};
    const auto skill=RecoveredDeityState::Skill::parse(raw_skill);
    if(!skill)throw DatabaseError("Skill book planned S34 shape invalid");
    deity.snapshot.skills.push_back(*skill);deity.revision=advance(deity.revision);
    deity.provenance.authority="CUSTOM_DESIGNED";
    constexpr std::string_view marker=";CUSTOM-0148:book-learning";
    if(deity.provenance.evidence_id.find(marker)==std::string::npos) {
        if(deity.provenance.evidence_id.size()>512-marker.size())throw DatabaseError("Skill book deity provenance overflow");
        deity.provenance.evidence_id.append(marker);
    }
    if(!RecoveredDeityState::valid(deity.snapshot,after->roster.template_keys()))throw DatabaseError("Skill book planned deity display invalid");
    after->roster=OwnedDeityRosterReadset(&companions_,companions_.readset_identity_,after->roster.account(),
        after->roster.character(),std::move(rows),after->roster.selection(),after->roster.template_keys());
    const auto& old_item=*before->state->inventory.cells[before->cell_index].instance;
    auto& cell=after->inventory.cells[before->cell_index];
    const auto remaining=old_item.quantity-1;
    after->inventory.revision=advance(after->inventory.revision);
    after->equipment.revision=advance(after->equipment.revision);
    const auto tag=[](std::string& source) {
        constexpr std::string_view suffix=";CUSTOM-0148:book-debit";
        if(source.find(suffix)!=std::string::npos)return;
        if(source.size()>2048-suffix.size())throw DatabaseError("Skill book material provenance overflow");
        source.append(suffix);
    };
    tag(after->inventory.source_record);tag(after->equipment.source_record);
    if(remaining) {
        cell.instance->quantity=remaining;cell.instance->revision=advance(old_item.revision);
        // A common custody epoch advances on every regional alias. Their opaque
        // raw records are retained; this does not qualify any CN projection.
        for(auto& alias:cell.instance->aliases)alias.revision=cell.instance->revision;
    }else cell.instance.reset();
    const auto offset=std::size_t(before->slot)*24;
    after->equipment.record[offset]=static_cast<std::uint8_t>(remaining);
    if(!remaining)after->equipment.record[offset+4]=after->equipment.record[offset+5]=0;
    if(!coherent_bank(after->inventory,after->equipment))throw DatabaseError("Skill book planned bank incoherent");
    inventory_.validate_change(before->state->inventory,after->inventory);
    equipment_.validate_change(before->state->equipment,after->equipment);
    const auto event_id=std::string(design)+":"+std::to_string(after->roster.account())+":"+
        std::to_string(after->roster.character())+":"+std::to_string(subject)+":"+
        std::to_string(before->book.kind)+":"+std::to_string(before->book.definition_id)+":"+
        std::to_string(old_item.id)+":"+std::to_string(old_item.revision)+":"+
        std::to_string(before->state->roster.rows()[before->deity_index].revision);
    ActivationEvent event{Activation{subject,raw_skill[2],raw_skill[3],event_id},after->roster.account(),
        after->roster.character(),old_item.id,old_item.revision,before->state->roster.rows()[before->deity_index].revision,
        static_cast<std::uint16_t>(before->book.item_id),before->book.source.source_sha256,
        before->book.record_sha256,before->book.parsed_sha256,before->book.raw_record,before->book.parsed_record};
    const auto& planned_deity=after->roster.rows()[before->deity_index];
    ActivationHeader header{subject,planned_deity.revision,planned_deity.provenance,row_bytes(planned_deity),{}};
    // Carry only activations whose old complete-row header actually matched.
    for(const auto& prior:before->state->headers)if(prior.subject==subject) {
        const auto& old=before->state->roster.rows()[before->deity_index];
        if(prior.revision==old.revision&&prior.provenance==old.provenance&&prior.raw==row_bytes(old))header.events=prior.events;
    }
    header.events.push_back(event);
    auto existing=std::find_if(after->headers.begin(),after->headers.end(),[&](const auto& h){return h.subject==subject;});
    if(existing==after->headers.end())after->headers.push_back(header);else *existing=header;
    std::sort(after->headers.begin(),after->headers.end(),[](const auto& a,const auto& b){return a.subject<b.subject;});
    after->activations.clear();
    for(const auto& h:after->headers) {
        const auto row=std::find_if(after->roster.rows().begin(),after->roster.rows().end(),[&](const auto& d){return d.snapshot.status.key_raw()==h.subject;});
        if(row!=after->roster.rows().end()&&row->revision==h.revision&&row->provenance==h.provenance&&row_bytes(*row)==h.raw)
            for(const auto& e:h.events)after->activations.push_back(e.activation);
    }
    auto planned=std::make_shared<PlanData>(PlanData{before,after,*skill,std::move(event),
        RecoveredInventory::SlotUpdate{static_cast<std::uint16_t>(remaining?before->book.item_id:0),before->slot,static_cast<std::uint8_t>(remaining)}});
    if(!observation_current(*before))return std::nullopt;
    std::optional<Plan> result{Plan(std::move(planned))};read.finish();return result;
}

std::optional<SqliteSkillBookLearningRepository::Committed> SqliteSkillBookLearningRepository::commit(const Plan& plan,Current current) {
    Operation operation(*this);
    if(!current||!plan.data_||plan.data_->before->state->repository!=this||
       plan.data_->before->state->identity.lock()!=identity_)return std::nullopt;
    const auto data=plan.data_;const auto& before=*data->before;const auto& after=*data->after;
    auto* db=inventory_.db_;
    {Statement fk(db,"PRAGMA foreign_keys");if(!fk.row()||fk.integer(0)!=1||fk.row())throw DatabaseError("Skill book learning requires foreign keys");}
    sqlite_detail::Transaction transaction(db);
    const auto check_before=[&] {if(!observation_current(before))throw DatabaseError("Skill book before CAS changed");};
    const auto pure_current=[&] {
        const auto changes=sqlite3_total_changes64(db);
        inventory_.issuer_active_=equipment_.issuer_active_=true;
        struct End {bool& a;bool& b;~End(){a=b=false;}} end{inventory_.issuer_active_,equipment_.issuer_active_};
        const bool allowed=current();
        if(poisoned_||inventory_.reentered_||equipment_.reentered_||companions_.readset_reentered_||
           sqlite3_get_autocommit(db)||sqlite3_total_changes64(db)!=changes)
            throw DatabaseError("Skill book Current reentered or changed transaction");
        return allowed;
    };
    check_before();if(!pure_current())return std::nullopt;check_before();
    if(!pure_current())return std::nullopt; // Final pure live cut after every before-read observer.
    // Complete reply preparation is the actual caller's job before this method.
    // The immutable after carrier already exists. No receipt escapes staging.
    std::optional<Committed> result{Committed(data)};
    const auto start=sqlite3_total_changes64(db);
    std::int64_t intended=0;
    for(const auto& cell:before.state->inventory.cells)if(cell.instance)intended+=static_cast<std::int64_t>(cell.instance->aliases.size());
    intended+=static_cast<std::int64_t>(before.state->inventory.cells.size())+1;
    for(const auto& cell:after.inventory.cells) {
        ++intended;if(cell.instance)intended+=static_cast<std::int64_t>(cell.instance->aliases.size());
    }
    inventory_.stage_replace(before.state->inventory,after.inventory);
    if(sqlite3_total_changes64(db)!=start+intended)throw DatabaseError("Skill book inventory write interval drift");
    equipment_.stage_replace(before.state->equipment,after.equipment);++intended;
    if(sqlite3_total_changes64(db)!=start+intended)throw DatabaseError("Skill book equipment write interval drift");
    const auto& old_deity=before.state->roster.rows()[before.deity_index];
    const auto& next_deity=after.roster.rows()[before.deity_index];
    {
        Statement write(db,"UPDATE main.character_deities SET skills=?,revision=?,source_sha256=?,authority=?,evidence_id=? WHERE character_id=? AND row_key=? AND revision=?");
        const auto bytes=skill_bytes(next_deity);write.bind_blob(1,bytes);write.bind_id(2,next_deity.revision);
        write.bind(3,next_deity.provenance.source_sha256);write.bind(4,next_deity.provenance.authority);write.bind(5,next_deity.provenance.evidence_id);
        write.bind_id(6,after.roster.character());write.bind(7,next_deity.snapshot.status.key_raw());write.bind_id(8,old_deity.revision);
        write.done();if(sqlite3_changes(db)!=1)throw DatabaseError("Skill book selected row CAS failed");++intended;
    }
    const auto& event=data->event;
    {
        Statement insert(db,"INSERT INTO main.skill_book_learning_events(event_id,account_id,character_id,row_key,kind,skill_id,book_item,book_instance,book_revision,deity_before_revision,book_source,record_sha256,parsed_sha256,raw_book,parsed_book,design) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)");
        insert.bind(1,event.activation.event_id);insert.bind_id(2,event.account);insert.bind_id(3,event.character);
        insert.bind(4,event.activation.subject);insert.bind(5,event.activation.kind);insert.bind(6,event.activation.definition_id);
        insert.bind(7,event.item);insert.bind_id(8,event.book_instance);insert.bind_id(9,event.book_revision);insert.bind_id(10,event.deity_revision);
        insert.bind(11,event.source);insert.bind(12,event.record_sha);insert.bind(13,event.parsed_sha);
        insert.bind_blob(14,event.raw);insert.bind_blob(15,event.parsed);insert.bind(16,std::string(design));insert.done();++intended;
    }
    const auto header=std::find_if(after.headers.begin(),after.headers.end(),[&](const auto& h){return h.subject==event.activation.subject;});
    {
        Statement remove(db,"DELETE FROM main.deity_skill_activation_links WHERE character_id=? AND row_key=?");
        remove.bind_id(1,event.character);remove.bind(2,event.activation.subject);remove.done();intended+=sqlite3_changes(db);
        Statement write(db,"INSERT INTO main.deity_skill_activation_headers(character_id,row_key,deity_revision,raw_row,source_sha256,authority,evidence_id,design) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(character_id,row_key) DO UPDATE SET deity_revision=excluded.deity_revision,raw_row=excluded.raw_row,source_sha256=excluded.source_sha256,authority=excluded.authority,evidence_id=excluded.evidence_id,design=excluded.design");
        write.bind_id(1,event.character);write.bind(2,header->subject);write.bind_id(3,header->revision);write.bind_blob(4,header->raw);
        write.bind(5,header->provenance.source_sha256);write.bind(6,header->provenance.authority);write.bind(7,header->provenance.evidence_id);
        write.bind(8,std::string(design));write.done();++intended;
        for(std::size_t i=0;i<header->events.size();++i) {
            Statement link(db,"INSERT INTO main.deity_skill_activation_links(character_id,row_key,ordinal,event_id) VALUES(?,?,?,?)");
            link.bind_id(1,event.character);link.bind(2,header->subject);link.bind_id(3,i);link.bind(4,header->events[i].activation.event_id);link.done();++intended;
        }
    }
    const auto check_after=[&] {
        if(sqlite3_total_changes64(db)!=start+intended||!state_current(after))throw DatabaseError("Skill book complete staged after changed");
        const auto book=books_.lookup_item(before.book.item_id);
        const auto common=skills_.lookup_shared_definition_main(before.book.kind,before.book.definition_id);
        const auto native=skills_.lookup_main_digest_checked(skills_.taiwan_dataset_id(),before.book.kind,before.book.definition_id);
        if(book!=std::optional{before.book}||!common||!native||common->requested_native!=native||common->definition!=before.common||
           sqlite3_total_changes64(db)!=start+intended||!state_current(after))throw DatabaseError("Skill book definition changed before COMMIT");
    };
    check_after();if(!pure_current())return std::nullopt;check_after();
    if(!pure_current())return std::nullopt; // No consumed-source read follows this final pure cut.
    transaction.commit();return result; // Only noexcept carrier moves/destruction, no post-COMMIT query/retry/allocation.
}

bool SqliteSkillBookLearningRepository::retained_plan_issuer(const PlanData& data) const noexcept {
    if(std::this_thread::get_id()!=thread_||!data.before||!data.before->state||!data.after)return false;
    const auto issued=[&](const State& state) noexcept {
        return state.repository==this&&state.identity.lock()==identity_&&
            state.roster.repository_==&companions_&&
            state.roster.identity_.lock()==companions_.readset_identity_;
    };
    return issued(*data.before->state)&&issued(*data.after);
}
std::optional<SqliteSkillBookLearningRepository::Restoration>
SqliteSkillBookLearningRepository::committed_after_source(const Committed& value) const noexcept {
    if(!value.data_||!retained_plan_issuer(*value.data_))return std::nullopt;
    return Restoration(value.data_->after); // SAME original after State/controlblock.
}
bool SqliteSkillBookLearningRepository::committed_matches_plan(const Committed& committed,
        const Plan& plan) const noexcept {
    return committed.data_&&plan.data_&&committed.data_==plan.data_&&
        !committed.data_.owner_before(plan.data_)&&!plan.data_.owner_before(committed.data_)&&
        retained_plan_issuer(*committed.data_);
}
bool SqliteSkillBookLearningRepository::committed_matches_restoration_before(
        const Committed& committed,const Restoration& before) const noexcept {
    if(!committed.data_ || !retained_plan_issuer(*committed.data_))return false;
    return plan_matches_restoration(Plan(committed.data_),before); // SAME actual PlanData owner, no allocation.
}
std::optional<SqliteSkillBookLearningRepository::Restoration>
SqliteSkillBookLearningRepository::planned_after_source(const Plan& value) const noexcept {
    if(!value.data_||!retained_plan_issuer(*value.data_))return std::nullopt;
    return Restoration(value.data_->after); // PROVISIONAL storage only; never commit/readiness evidence.
}
bool SqliteSkillBookLearningRepository::plan_matches_restoration(const Plan& plan,
        const Restoration& restoration) const noexcept {
    if(!plan.data_||!restoration.state_||!retained_plan_issuer(*plan.data_))return false;
    const auto& before=*plan.data_->before->state;const auto& expected=*restoration.state_;
    if(expected.repository!=this||expected.identity.lock()!=identity_||
       expected.roster.repository_!=&companions_||
       expected.roster.identity_.lock()!=companions_.readset_identity_||
       before.inventory!=expected.inventory||before.equipment!=expected.equipment||
       before.headers!=expected.headers||before.activations!=expected.activations||
       before.roster.account()!=expected.roster.account()||before.roster.character()!=expected.roster.character()||
       before.roster.selection()!=expected.roster.selection()||before.roster.template_keys()!=expected.roster.template_keys()||
       before.roster.rows().size()!=expected.roster.rows().size())return false;
    for(std::size_t i=0;i<before.roster.rows().size();++i) {
        const auto& a=before.roster.rows()[i];const auto& b=expected.roster.rows()[i];
        if(a.revision!=b.revision||a.provenance!=b.provenance||
           a.snapshot.declaration.encode()!=b.snapshot.declaration.encode()||
           a.snapshot.status.encode()!=b.snapshot.status.encode()||
           a.snapshot.skills.size()!=b.snapshot.skills.size())return false;
        for(std::size_t j=0;j<a.snapshot.skills.size();++j)
            if(a.snapshot.skills[j].encode()!=b.snapshot.skills[j].encode())return false;
    }
    return true;
}
const OwnedInventorySnapshot& SqliteSkillBookLearningRepository::Restoration::inventory() const noexcept {return state_->inventory;}
const NativeEquipmentSnapshot& SqliteSkillBookLearningRepository::Restoration::equipment() const noexcept {return state_->equipment;}
const OwnedDeityRosterReadset& SqliteSkillBookLearningRepository::Restoration::roster() const noexcept {return state_->roster;}
const std::vector<SqliteSkillBookLearningRepository::Activation>& SqliteSkillBookLearningRepository::Restoration::activations() const noexcept {return state_->activations;}
const OwnedInventorySnapshot& SqliteSkillBookLearningRepository::Observation::inventory() const noexcept {return data_->state->inventory;}
const NativeEquipmentSnapshot& SqliteSkillBookLearningRepository::Observation::equipment() const noexcept {return data_->state->equipment;}
const OwnedDeityRosterReadset& SqliteSkillBookLearningRepository::Observation::roster() const noexcept {return data_->state->roster;}
const StoredDeity& SqliteSkillBookLearningRepository::Observation::deity() const noexcept {return data_->state->roster.rows()[data_->deity_index];}
const StoredDeitySelection& SqliteSkillBookLearningRepository::Observation::selection() const noexcept {return *data_->state->roster.selection();}
const NativeSkillBookRecord& SqliteSkillBookLearningRepository::Observation::book() const noexcept {return data_->book;}
const SharedSkillDefinition& SqliteSkillBookLearningRepository::Observation::common_definition() const noexcept {return data_->common;}
const std::vector<SqliteSkillBookLearningRepository::Activation>& SqliteSkillBookLearningRepository::Observation::activations() const noexcept {return data_->state->activations;}
std::uint8_t SqliteSkillBookLearningRepository::Observation::slot() const noexcept {return data_->slot;}
bool SqliteSkillBookLearningRepository::Observation::already_learned() const noexcept {return data_->learned;}
const RecoveredDeityState::Skill& SqliteSkillBookLearningRepository::Plan::skill() const noexcept {return data_->skill;}
const SqliteSkillBookLearningRepository::Activation& SqliteSkillBookLearningRepository::Plan::activation() const noexcept {return data_->event.activation;}
RecoveredInventory::SlotUpdate SqliteSkillBookLearningRepository::Plan::slot_update() const noexcept {return data_->update;}
const OwnedInventorySnapshot& SqliteSkillBookLearningRepository::Plan::inventory() const noexcept {return data_->after->inventory;}
const NativeEquipmentSnapshot& SqliteSkillBookLearningRepository::Plan::equipment() const noexcept {return data_->after->equipment;}
const StoredDeity& SqliteSkillBookLearningRepository::Plan::deity() const noexcept {return data_->after->roster.rows()[data_->before->deity_index];}
const std::vector<SqliteSkillBookLearningRepository::Activation>& SqliteSkillBookLearningRepository::Plan::activations() const noexcept {return data_->after->activations;}
const OwnedInventorySnapshot& SqliteSkillBookLearningRepository::Committed::inventory() const noexcept {return data_->after->inventory;}
const NativeEquipmentSnapshot& SqliteSkillBookLearningRepository::Committed::equipment() const noexcept {return data_->after->equipment;}
const StoredDeity& SqliteSkillBookLearningRepository::Committed::deity() const noexcept {return data_->after->roster.rows()[data_->before->deity_index];}
const std::vector<SqliteSkillBookLearningRepository::Activation>& SqliteSkillBookLearningRepository::Committed::activations() const noexcept {return data_->after->activations;}
}
