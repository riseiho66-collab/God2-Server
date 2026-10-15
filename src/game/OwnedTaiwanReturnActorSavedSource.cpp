#include "game/OwnedTaiwanReturnActorSavedSource.h"
#include "db/SqliteNativeWorldEntrySnapshotRepository.h"
#include "db/SqliteNativeEquipmentSnapshotRepository.h"
#include "db/SqliteOwnedInventoryRepository.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <set>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
bool same_actor(const SharedWorldPresence::ReadyCharacter& a,const SharedWorldPresence::ReadyCharacter& b) noexcept {
    return a.lease==b.lease&&a.position==b.position&&NativeWorldEntrySnapshot::same_root(a.character,b.character);
}
}
struct OwnedTaiwanReturnActorSavedSource::Data {
    const OwnedTaiwanReturnActorSavedSource* const owner;
    const std::shared_ptr<const Identity> identity;
    const std::vector<Material> rows;
    const std::optional<SharedWorldPresence::InitialPopulation> initial; // LAST, privately captured domain.
    Data(const OwnedTaiwanReturnActorSavedSource* source,std::shared_ptr<const Identity> key,std::vector<Material> material,
        std::optional<SharedWorldPresence::InitialPopulation> population={})
        :owner(source),identity(std::move(key)),rows(std::move(material)),initial(std::move(population)){}
};
struct OwnedTaiwanReturnActorSavedSource::ProfileData {
    const OwnedTaiwanReturnActorSavedSource* const owner;
    const std::shared_ptr<const Identity> identity;
    const Readset saved;
    const std::size_t index;
    const SqliteOwnedEquipmentTransaction::Committed committed;
    ProfileData(const OwnedTaiwanReturnActorSavedSource* source,std::shared_ptr<const Identity> key,
        Readset readset,std::size_t row,SqliteOwnedEquipmentTransaction::Committed receipt)
        :owner(source),identity(std::move(key)),saved(std::move(readset)),index(row),committed(std::move(receipt)){}
};
const OwnedTaiwanReturnActorSavedSource::Readset&
OwnedTaiwanReturnActorSavedSource::ProfileEquipment::saved_readset() const noexcept{return data_->saved;}
std::size_t OwnedTaiwanReturnActorSavedSource::ProfileEquipment::row_index() const noexcept{return data_->index;}
const OwnedInventorySnapshot& OwnedTaiwanReturnActorSavedSource::ProfileEquipment::inventory() const noexcept {
    return data_->committed.inventory().snapshot();
}
const NativeEquipmentSnapshot& OwnedTaiwanReturnActorSavedSource::ProfileEquipment::equipment() const noexcept {
    return data_->committed.equipment().snapshot();
}
bool OwnedTaiwanReturnActorSavedSource::Material::operator==(const Material& b) const {
    return same_actor(actor,b.actor)&&world==b.world&&equipment==b.equipment&&inventory==b.inventory;
}
const std::vector<OwnedTaiwanReturnActorSavedSource::Material>&
OwnedTaiwanReturnActorSavedSource::Readset::materials() const noexcept {return data_->rows;}
bool OwnedTaiwanReturnActorSavedSource::Readset::matches_population(
        std::span<const SharedWorldPresence::ReadyCharacter> rows) const noexcept {
    if(rows.size()!=data_->rows.size())return false;
    for(std::size_t i=0;i<rows.size();++i)if(!same_actor(rows[i],data_->rows[i].actor))return false;
    return true;
}
bool OwnedTaiwanReturnActorSavedSource::Readset::matches_initial_population(
        const SharedWorldPresence::InitialPopulation& population) const noexcept {
    return data_&&data_->initial&&*data_->initial==population&&matches_population(population.characters());
}
std::span<const SharedWorldPresence::ReadyCharacter>
OwnedTaiwanReturnActorSavedSource::PopulationInput::characters() const noexcept {
    return std::visit([](const auto& value){return value.characters();},population_);
}
const SharedWorldPresence::InitialPopulation*
OwnedTaiwanReturnActorSavedSource::PopulationInput::initial_population() const noexcept {
    return std::get_if<SharedWorldPresence::InitialPopulation>(&population_);
}
bool OwnedTaiwanReturnActorSavedSource::PopulationInput::population_current(
        const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    return source_&&source_->input_population_current(*this,presence);
}
struct OwnedTaiwanReturnActorSavedSource::InitialIssuer::Operation {
    const InitialIssuer& issuer;
    explicit Operation(const InitialIssuer& owner):issuer(owner){
        if(issuer.thread_!=std::this_thread::get_id())throw DatabaseError("Initial saved issuer owner mismatch");
        if(issuer.reading_){issuer.poisoned_=true;throw DatabaseError("Initial saved issuer reentered");}
        // Never touch Role's borrowed database owners after Saved lifetime ends.
        if(issuer.poisoned_||!issuer.source_||!issuer.role_||!issuer.source_->owns_database())
            throw DatabaseError("Initial saved issuer retired");
        issuer.reading_=true;
    }
    ~Operation(){issuer.reading_=false;}
};
bool OwnedTaiwanReturnActorSavedSource::InitialIssuer::owns_presence(
        const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    try{
        if(thread_!=std::this_thread::get_id())return false;
        if(reading_){poisoned_=true;return false;}
        return !poisoned_&&source_&&role_&&source_->owns_database()&&
            source_->owns_presence(presence)&&role_->owns_presence(presence);
    }catch(...){return false;}
}
std::shared_ptr<const OwnedTaiwanReturnActorSavedSource::PopulationInput>
OwnedTaiwanReturnActorSavedSource::InitialIssuer::observe(const SharedWorldPresence::InitialPopulation& supplied) const {
    try{
        Operation operation(*this);const auto population=supplied;
        const auto source=source_;const auto role=role_;const auto presence=source->presence_;
        if(!source->owns_presence(presence)||!role->owns_presence(presence)||
           !presence->retained_initial_population_current(population))return {};
        const auto saved=source->observe_initial_population(population);
        if(poisoned_||!saved||!saved->matches_initial_population(population)||
           !presence->retained_initial_population_current(population))return {};
        const auto input=std::shared_ptr<const PopulationInput>(new PopulationInput(source,population,*saved,role));
        // Input/control-block allocation may reenter or modify storage. Qualify
        // the entire stored tuple AFTER allocation, then only pure witnesses.
        if(poisoned_||!source->current(input->readset())||poisoned_||
           !input->population_current(presence))return {};
        return input;
    }catch(const std::exception&){return {};}
}
struct OwnedTaiwanReturnActorSavedSource::Operation {
    const OwnedTaiwanReturnActorSavedSource& source;
    explicit Operation(const OwnedTaiwanReturnActorSavedSource& value):source(value) {
        if(source.thread_!=std::this_thread::get_id())throw DatabaseError("TW actor saved source game owner mismatch");
        if(source.reading_){source.poisoned_=true;throw DatabaseError("TW actor saved source reentry");}
        if(source.poisoned_||!source.owns_database())throw DatabaseError("TW actor saved source retired");
        source.reading_=true;
    }
    ~Operation(){source.reading_=false;}
};
struct OwnedTaiwanReturnActorSavedSource::ReadScope {
    const OwnedTaiwanReturnActorSavedSource& source;
    bool own=false,finished=false;
    explicit ReadScope(const OwnedTaiwanReturnActorSavedSource& value):source(value){}
    void begin(sqlite3_int64 changes) {
        if(source.own_read_scope_)throw DatabaseError("TW actor saved source already owns a read scope");
        source.fence(changes,true);sqlite_detail::execute(source.db_,"BEGIN");
        own=true;source.own_read_scope_=this;source.fence(changes,false);
    }
    ~ReadScope(){
        if(own&&!finished&&!source.database_lifetime_.expired()&&!sqlite3_get_autocommit(source.db_))
            sqlite3_exec(source.db_,"ROLLBACK",nullptr,nullptr,nullptr);
        if(source.own_read_scope_==this)source.own_read_scope_=nullptr;
    }
    void finish(sqlite3_int64 changes) {
        source.fence(changes,false);sqlite_detail::execute(source.db_,"COMMIT");finished=true;
        own=false;if(source.own_read_scope_==this)source.own_read_scope_=nullptr;
        source.fence(changes,true);
    }
};
OwnedTaiwanReturnActorSavedSource::OwnedTaiwanReturnActorSavedSource(sqlite3* db,SqliteAccountRepository& accounts,
        SqliteRecoveredCharacterRepository& characters,SqliteNativeWorldEntrySnapshotRepository& worlds,
        SqliteNativeEquipmentSnapshotRepository& equipment,SqliteOwnedInventoryRepository& inventory,
        std::shared_ptr<SharedWorldPresence> presence,std::weak_ptr<const void> lifetime)
    :db_(db),accounts_(accounts),characters_(characters),worlds_(worlds),equipment_(equipment),inventory_(inventory),joint_(inventory,equipment),
     presence_(std::move(presence)),database_lifetime_(std::move(lifetime)) {
    if(!owns_database()||!presence_||!presence_->owns_repository(characters_))
        throw DatabaseError("TW actor saved source requires exact private same-DB owners");
}
bool OwnedTaiwanReturnActorSavedSource::owns_database() const noexcept {
    return !database_lifetime_.expired()&&db_&&accounts_.uses_connection(db_)&&characters_.uses_connection(db_)&&
        worlds_.owns_sources(accounts_,characters_)&&equipment_.owns_sources(accounts_,characters_)&&
        inventory_.owns_sources(accounts_,characters_)&&joint_.owns_writers(inventory_,equipment_)&&!poisoned_;
}
bool OwnedTaiwanReturnActorSavedSource::owns_presence(const std::shared_ptr<SharedWorldPresence>& p) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(reading_){poisoned_=true;return false;}
    return p&&p==presence_&&owns_database();
}
bool OwnedTaiwanReturnActorSavedSource::owns_readset(const Readset& value) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(reading_){poisoned_=true;return false;}
    return identity_current(value);
}
bool OwnedTaiwanReturnActorSavedSource::profile_shape(const ProfileEquipment& value) const noexcept {
    if(!value.data_||value.data_->owner!=this||value.data_->identity!=identity_||
       !identity_current(value.data_->saved)||value.data_->index>=value.data_->saved.materials().size())return false;
    const auto& row=value.data_->saved.materials()[value.data_->index];
    const auto& equipment=value.equipment();
    return row.equipment&&row.actor.lease.actor_handle&&row.actor.lease.actor_handle<=0xfff&&
        value.inventory()==row.inventory&&equipment==*row.equipment&&
        NativeEquipmentSnapshot::same_root(equipment.root,row.actor.character)&&
        equipment.position==row.actor.position&&equipment.actor_handle==row.actor.lease.actor_handle;
}
bool OwnedTaiwanReturnActorSavedSource::owns_profile_equipment(const ProfileEquipment& value) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(reading_){poisoned_=true;return false;}
    return profile_shape(value);
}
bool OwnedTaiwanReturnActorSavedSource::profile_equipment_matches(const ProfileEquipment& value,
        const Readset& saved,std::size_t index) const noexcept {
    if(thread_!=std::this_thread::get_id())return false;
    if(reading_){poisoned_=true;return false;}
    return profile_shape(value)&&value.data_->saved==saved&&value.data_->index==index;
}
bool OwnedTaiwanReturnActorSavedSource::profiles_stored(const Readset& saved,
        std::span<const ProfileEquipment> profiles,sqlite3_int64 changes) const {
    for(const auto& profile:profiles){
        if(!profile_shape(profile)||profile.data_->saved!=saved)return false;
        if(!joint_.committed_current_in_scope(db_,profile.data_->committed))return false;
        fence(changes,false);
    }
    return true;
}
std::optional<OwnedTaiwanReturnActorSavedSource::ProfileEquipment>
OwnedTaiwanReturnActorSavedSource::observe_profile_equipment(const Readset& value,std::size_t index) const {
    try{
        Operation operation(*this);const Readset saved=value;
        if(!identity_current(saved)||index>=saved.materials().size()||!saved.materials()[index].equipment)return {};
        const auto changes=sqlite3_total_changes64(db_);fence(changes,true);
        const auto& row=saved.materials()[index];
        auto receipt=joint_.observe_committed(row.actor.lease.account,row.actor.lease.character);
        fence(changes,true);if(!receipt)return {};
        ProfileEquipment result(std::make_shared<const ProfileData>(this,identity_,saved,index,std::move(*receipt)));
        if(!profile_shape(result))return {};
        for(const auto& member:saved.materials()){if(!row_live_current(saved,member.actor))return {};fence(changes,true);}
        {
            ReadScope scope(*this);scope.begin(changes);
            if(!stored(saved,changes)||!profiles_stored(saved,std::span<const ProfileEquipment>(&result,1),changes))return {};
            fence(changes,false);scope.finish(changes);
        }
        if(!profile_shape(result)||!registry_current(saved))return {};fence(changes,true);return result;
    }catch(const std::exception&){return {};}
}
bool OwnedTaiwanReturnActorSavedSource::profile_equipment_current(const ProfileEquipment& value) const {
    if(thread_!=std::this_thread::get_id())return false;
    const ProfileEquipment retained=value;
    return current_with_role_text(retained.saved_readset(),{}, {}, {},std::span<const ProfileEquipment>(&retained,1));
}
bool OwnedTaiwanReturnActorSavedSource::profile_equipment_stored_current_in_scope(
        sqlite3* connection,const ProfileEquipment& value) const {
    if(thread_!=std::this_thread::get_id())return false;
    const ProfileEquipment retained=value;
    return stored_current_in_scope(connection,retained.saved_readset(),std::span<const ProfileEquipment>(&retained,1));
}
void OwnedTaiwanReturnActorSavedSource::fence(sqlite3_int64 changes,bool autocommit) const {
    // Once an ended owned transaction is observed, retire rollback ownership
    // BEFORE throwing. Later statement-finalization hooks may start a foreign
    // successor, which this abandoned read scope must never roll back.
    if(own_read_scope_&&!database_lifetime_.expired()&&db_&&sqlite3_get_autocommit(db_)){
        own_read_scope_->own=false;own_read_scope_=nullptr;
    }
    if(thread_!=std::this_thread::get_id()||!reading_||!owns_database()||
       (sqlite3_get_autocommit(db_)!=0)!=autocommit||sqlite3_total_changes64(db_)!=changes)
        throw DatabaseError("TW actor saved source connection/transaction/rows changed");
}
void OwnedTaiwanReturnActorSavedSource::namespaces(sqlite3_int64 changes) const {
    sqlite_detail::Statement shadow(db_,"SELECT 1 FROM temp.sqlite_master WHERE name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_native_world_entries','character_native_equipment_snapshots','owned_inventory_headers','owned_inventory_cells','owned_item_instances','owned_item_native_aliases') OR tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_native_world_entries','character_native_equipment_snapshots','owned_inventory_headers','owned_inventory_cells','owned_item_instances','owned_item_native_aliases')");
    if(shadow.row())throw DatabaseError("TW actor saved source TEMP namespace rejected");fence(changes,false);
    sqlite_detail::Statement tables(db_,"SELECT count(*) FROM main.sqlite_master WHERE type='table' AND name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_native_world_entries','character_native_equipment_snapshots','owned_inventory_headers','owned_inventory_cells','owned_item_instances','owned_item_native_aliases')");
    if(!tables.row()||tables.integer(0)!=9||tables.row())throw DatabaseError("TW actor saved source requires existing main tables");
    fence(changes,false);
    sqlite_detail::Statement triggers(db_,"SELECT 1 FROM main.sqlite_master WHERE type='trigger' AND tbl_name COLLATE NOCASE IN ('accounts','recovered_characters','recovered_positions','character_native_world_entries','character_native_equipment_snapshots','owned_inventory_headers','owned_inventory_cells','owned_item_instances','owned_item_native_aliases')");
    if(triggers.row())throw DatabaseError("TW actor saved source trigger namespace rejected");fence(changes,false);
}
bool OwnedTaiwanReturnActorSavedSource::identity_current(const Readset& value) const noexcept {
    return value.data_&&value.data_->owner==this&&value.data_->identity==identity_&&owns_database();
}
bool OwnedTaiwanReturnActorSavedSource::row_retained_current(const Readset& value,
        const SharedWorldPresence::ReadyCharacter& row) const {
    const auto& initial=value.data_->initial;
    if(!initial)return presence_->retained_ready_current(row.lease);
    if(!value.matches_initial_population(*initial)||!presence_->retained_initial_population_current(*initial))return false;
    const bool active=row.lease!=initial->joining().lease||initial->activated();
    return (active?presence_->retained_ready_current(row.lease):presence_->retained_preparation_current(row.lease))&&
        presence_->retained_initial_population_current(*initial);
}
bool OwnedTaiwanReturnActorSavedSource::row_live_current(const Readset& value,
        const SharedWorldPresence::ReadyCharacter& row) const {
    const auto& initial=value.data_->initial;
    if(!initial)return presence_->ready(row.lease); // Legacy all-ready domain.
    if(!value.matches_initial_population(*initial)||!presence_->retained_initial_population_current(*initial))return false;
    const bool activated=initial->activated();
    const bool active=row.lease!=initial->joining().lease||activated;
    const bool valid=active?presence_->ready(row.lease):presence_->preparation_current(row.lease);
    return valid&&initial->activated()==activated&&row_retained_current(value,row);
}
bool OwnedTaiwanReturnActorSavedSource::registry_current(const Readset& value) const {
    for(const auto& row:value.data_->rows)if(!row_retained_current(value,row.actor))return false;
    return !value.data_->initial||presence_->retained_initial_population_current(*value.data_->initial);
}
bool OwnedTaiwanReturnActorSavedSource::input_population_current(const PopulationInput& input,
        const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    try{
        if(thread_!=std::this_thread::get_id())return false;
        if(reading_){poisoned_=true;return false;}
        if(input.source().get()!=this||!presence||presence!=presence_||!identity_current(input.readset())||
           !input.readset().matches_population(input.characters()))return false;
        if(const auto* initial=input.initial_population())
            return input.readset().matches_initial_population(*initial)&&presence_->retained_initial_population_current(*initial);
        return !input.readset().data_->initial&&presence_->retained_population_current(input.population());
    }catch(...){return false;}
}
std::optional<OwnedTaiwanReturnActorSavedSource::Material> OwnedTaiwanReturnActorSavedSource::read_actor(
        const SharedWorldPresence::ReadyCharacter& request,sqlite3_int64 changes) const {
    const auto& lease=request.lease;
    // Saved storage observes the complete common registry's0..3FFF domain.
    // Nonzero12-bit remote rendering belongs to the later eligible profile.
    if(!lease.session||!lease.account||!lease.character||!lease.generation||lease.actor_handle>0x3fff||
       request.character.account_id!=lease.account||request.character.id!=lease.character||!request.position.revision)return {};
    std::optional<RecoveredCharacter> root;
    for(const auto& row:characters_.list_for_account(lease.account))if(row.id==lease.character){if(root)return {};root=row;}
    fence(changes,false);
    const auto pose=characters_.load_position(lease.account,lease.character);fence(changes,false);
    if(!root||!NativeWorldEntrySnapshot::same_root(*root,request.character)||pose!=std::optional{request.position})return {};
    auto inventory=inventory_.load(lease.account,lease.character);fence(changes,false);
    if(!inventory||!OwnedInventorySnapshot::same_root(inventory->root,*root))return {};
    auto world=worlds_.load(lease.account,lease.character,NativeEquipmentSnapshot::client_pin,"tw.world-entry.2a.zero-seed");
    fence(changes,false);
    if(world){
        if(world->record.size()!=RecoveredWorldEntry::Frame{}.size()||world->root.account_id!=lease.account||world->root.id!=lease.character)return {};
        RecoveredWorldEntry::Frame frame;std::copy(world->record.begin(),world->record.end(),frame.begin());
        const auto entry=RecoveredWorldEntryView::read(frame);
        // The recorded native handle belongs to this historical witness, not
        // necessarily today's Ready lease. Keep it unchanged for later profile
        // qualification; a mismatch must never be relabelled as absence.
        if(!entry)return {};
    }
    auto equipment=equipment_.load(lease.account,lease.character,NativeEquipmentSnapshot::client_pin,NativeEquipmentSnapshot::kind);
    fence(changes,false);
    if(equipment){
        const auto da=equipment->appearance();
        if(equipment->root.account_id!=lease.account||equipment->root.id!=lease.character||
           !da||da->actor_identity()!=equipment->actor_handle)return {};
    }
    return Material{request,std::move(world),std::move(equipment),std::move(*inventory)};
}
bool OwnedTaiwanReturnActorSavedSource::stored(const Readset& value,sqlite3_int64 changes) const {
    if(!identity_current(value))return false;namespaces(changes);
    for(const auto& original:value.data_->rows){
        const auto actual=read_actor(original.actor,changes);
        if(!actual||*actual!=original)return false;
    }
    namespaces(changes);fence(changes,false);return true;
}
std::optional<OwnedTaiwanReturnActorSavedSource::Readset> OwnedTaiwanReturnActorSavedSource::observe_population(
        std::span<const SharedWorldPresence::ReadyCharacter> supplied) const {
    try{
        Operation operation(*this);
        const std::vector<SharedWorldPresence::ReadyCharacter> requests(supplied.begin(),supplied.end());
        const auto changes=sqlite3_total_changes64(db_);fence(changes,true);
        std::set<std::uint64_t> sessions,characters;std::set<std::uint16_t> handles;
        for(const auto& row:requests){
            if(!sessions.insert(row.lease.session).second||!characters.insert(row.lease.character).second||
               !handles.insert(row.lease.actor_handle).second||!presence_->ready(row.lease))return {};
            fence(changes,true);
        }
        std::vector<Material> material;material.reserve(requests.size());
        ReadScope scope(*this);scope.begin(changes);namespaces(changes);
        for(const auto& row:requests){auto actual=read_actor(row,changes);if(!actual)return {};material.push_back(std::move(*actual));}
        Readset result(std::make_shared<const Data>(this,identity_,std::move(material)));
        if(!stored(result,changes))return {};scope.finish(changes);
        // Any live Presence/repository observer follows SQL, then the ENTIRE
        // saved set is re-read. Only pure registry/owner fences follow that cut.
        for(const auto& row:result.materials()){if(!row_live_current(result,row.actor))return {};fence(changes,true);}
        {ReadScope final(*this);final.begin(changes);if(!stored(result,changes))return {};final.finish(changes);}
        if(!registry_current(result))return {};fence(changes,true);return result;
    }catch(const std::exception&){return {};}
}
std::optional<OwnedTaiwanReturnActorSavedSource::Readset> OwnedTaiwanReturnActorSavedSource::observe_initial_population(
        const SharedWorldPresence::InitialPopulation& supplied) const {
    try{
        Operation operation(*this);const auto population=supplied;
        if(!presence_->retained_initial_population_current(population))return {};
        const auto rows=population.characters();
        const std::vector<SharedWorldPresence::ReadyCharacter> requests(rows.begin(),rows.end());
        const auto changes=sqlite3_total_changes64(db_);fence(changes,true);
        if(!presence_->retained_initial_population_current(population))return {};
        std::set<std::uint64_t> sessions,characters;std::set<std::uint16_t> handles;
        bool joining_found=false;
        for(const auto& row:requests){
            if(!sessions.insert(row.lease.session).second||!characters.insert(row.lease.character).second||
               !handles.insert(row.lease.actor_handle).second)return {};
            if(row.lease==population.joining().lease){
                if(joining_found||!same_actor(row,population.joining())||row.position!=row.lease.position)return {};
                joining_found=true;
            }
        }
        if(!joining_found)return {};
        std::vector<Material> material;material.reserve(requests.size());
        ReadScope scope(*this);scope.begin(changes);namespaces(changes);
        for(const auto& row:requests){auto actual=read_actor(row,changes);if(!actual)return {};material.push_back(std::move(*actual));}
        Readset result(std::make_shared<const Data>(this,identity_,std::move(material),population));
        if(!result.matches_initial_population(population)||!stored(result,changes))return {};scope.finish(changes);
        for(const auto& row:result.materials()){if(!row_live_current(result,row.actor))return {};fence(changes,true);}
        {ReadScope final(*this);final.begin(changes);if(!stored(result,changes))return {};final.finish(changes);}
        if(!registry_current(result))return {};fence(changes,true);return result;
    }catch(const std::exception&){return {};}
}
bool OwnedTaiwanReturnActorSavedSource::current(const Readset& value) const {
    return current_with_role_text(value,{}, {}, {});
}
bool OwnedTaiwanReturnActorSavedSource::current_with_role_text(const Readset& value,
        const std::shared_ptr<OwnedTaiwanPkReturnRoleTextSource>& role,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::Observation> texts,
        std::span<const OwnedTaiwanPkReturnRoleTextSource::EndpointObservation> endpoints,
        std::span<const ProfileEquipment> profiles) const {
    try{
        Operation operation(*this);
        // Own inputs before any live/SQLite observer can replace the caller's
        // public value or release its backing vectors and shared owner.
        const Readset retained=value;const auto role_owner=role;
        const std::vector<OwnedTaiwanPkReturnRoleTextSource::Observation> text_rows(texts.begin(),texts.end());
        const std::vector<OwnedTaiwanPkReturnRoleTextSource::EndpointObservation> endpoint_rows(endpoints.begin(),endpoints.end());
        const std::vector<ProfileEquipment> profile_rows(profiles.begin(),profiles.end());
        if(!identity_current(retained)||(!role_owner&&(!text_rows.empty()||!endpoint_rows.empty())))return false;
        for(const auto& profile:profile_rows)if(!profile_shape(profile)||profile.data_->saved!=retained)return false;
        const auto changes=sqlite3_total_changes64(db_);fence(changes,true);
        if(role_owner&&!role_owner->owns_presence(presence_))return false;
        fence(changes,true);
        for(const auto& row:retained.materials()){if(!row_live_current(retained,row.actor))return false;fence(changes,true);}
        {
            ReadScope scope(*this);scope.begin(changes);
            if(!stored(retained,changes)||(role_owner&&!role_owner->stored_current_in_scope(db_,text_rows,endpoint_rows)))return false;
            if(!profiles_stored(retained,profile_rows,changes))return false;
            fence(changes,false);scope.finish(changes);
        }
        if(!registry_current(retained))return false;fence(changes,true);return true;
    }catch(const std::exception&){return false;}
}
bool OwnedTaiwanReturnActorSavedSource::stored_current_in_scope(sqlite3* connection,const Readset& value,
        std::span<const ProfileEquipment> profiles) const {
    try{
        Operation operation(*this);
        const Readset retained=value;
        const std::vector<ProfileEquipment> profile_rows(profiles.begin(),profiles.end());
        if(connection!=db_||sqlite3_get_autocommit(db_)||!identity_current(retained))return false;
        for(const auto& profile:profile_rows)if(!profile_shape(profile)||profile.data_->saved!=retained)return false;
        const auto changes=sqlite3_total_changes64(db_);fence(changes,false);
        if(!stored(retained,changes)||!profiles_stored(retained,profile_rows,changes))return false;
        fence(changes,false);return true;
    }catch(const std::exception&){return false;}
}
}
