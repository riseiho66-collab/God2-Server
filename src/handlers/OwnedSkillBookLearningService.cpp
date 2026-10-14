#include "handlers/OwnedSkillBookLearningService.h"
#include "db/SqliteSkillBookLearningRepository.h"
#include "handlers/RecoveredOwnedCompanions.h"
#include "game/SharedWorldPresence.h"
#include "game/TaiwanOwnedBagItemMaterial.h"
#include "scripting/LuaEngine.h"
#include "protocol/RecoveredDeityActivation.h"
#include "protocol/RecoveredTaiwanInventoryItemRecord.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <array>
#include <span>
#include <stdexcept>
#include <utility>
namespace god2 {
namespace {
// A projection view over the exact two TW aliases only. The repository keeps
// and validates the full actual regional alias population; it is never dropped.
std::optional<RecoveredTaiwanInventoryItemRecord::Fields> material(
        const OwnedInventoryInstance& item,std::uint8_t slot) {
    const OwnedItemNativeAlias* identity=nullptr;const OwnedItemNativeAlias* full=nullptr;
    for(const auto& alias:item.aliases) {
        if(alias.client_sha256!=NativeEquipmentSnapshot::client_pin)continue;
        if(alias.profile==SharedTaiwanOwnedItemSelectionSource::alias_profile) {
            if(identity)return std::nullopt;identity=&alias;
        } else if(alias.profile==TaiwanOwnedBagItemMaterial::profile) {
            if(full)return std::nullopt;full=&alias;
        }
    }
    if(!identity||!full)return std::nullopt;
    OwnedInventoryInstance view;view.revision=item.revision;view.aliases={*identity,*full};
    return TaiwanOwnedBagItemMaterial::observe(view,slot);
}
const OwnedInventoryInstance* item_at(const OwnedInventorySnapshot& inventory,std::uint8_t slot) {
    const OwnedInventoryInstance* result=nullptr;
    for(const auto& cell:inventory.cells)if(cell.instance)for(const auto& alias:cell.instance->aliases) {
        if(alias.client_sha256!=NativeEquipmentSnapshot::client_pin ||
           alias.profile!=SharedTaiwanOwnedItemSelectionSource::alias_profile || alias.native_slot!=slot)continue;
        if(result)return nullptr;result=&*cell.instance;
    }
    return result;
}
void append_frame(std::vector<std::uint8_t>& wire,std::span<const std::uint8_t> logical) {
    if(logical.empty())return;
    auto frame=RecoveredWorldFrame::encode(logical);wire.insert(wire.end(),frame.begin(),frame.end());
}
}
struct OwnedSkillBookLearningService::Entry {
    std::weak_ptr<Session> session;
    Session::NormalWorldInitialization initialization;
    std::uint64_t account,character,battle;
    SessionState phase;
    std::uint16_t actor;
    std::shared_ptr<const RecoveredOwnedCompanions::Restoration> original_restoration;
    bool bootstrap_complete_without_reply=false;
    std::shared_ptr<SharedWorldPresence> presence;
    std::optional<SharedWorldPresence::Lease> lease;
    std::vector<std::uint8_t> bootstrap_wire;
    std::optional<Session::WorldResponseWrite> bootstrap_response;
    std::optional<SqliteSkillBookLearningRepository::Committed> latest_commit;
    bool revoked=false;
    Entry(Session& source,Session::NormalWorldInitialization init,std::shared_ptr<SharedWorldPresence> common,
          std::optional<SharedWorldPresence::Lease> owned,std::uint16_t native_actor,
          std::shared_ptr<const RecoveredOwnedCompanions::Restoration> restored)
        :session(source.weak_from_this()),initialization(std::move(init)),account(source.account_id),
         character(source.character_id),battle(source.battle_generation()),phase(source.state()),actor(native_actor),
         original_restoration(std::move(restored)),presence(std::move(common)),lease(std::move(owned)) {}
};
struct OwnedSkillBookLearningService::Operation {
    OwnedSkillBookLearningService& service;
    explicit Operation(OwnedSkillBookLearningService& value):service(value) {
        service.owner();
        if(service.busy_) {service.poisoned_=true;throw std::logic_error("Skill book service reentry rejected");}
        if(!service.live_)throw std::logic_error("Skill book service stopped");
        service.busy_=true;service.poisoned_=false;
    }
    ~Operation(){service.busy_=false;}
};
OwnedSkillBookLearningService::OwnedSkillBookLearningService(SqliteSkillBookLearningRepository& repository,
        LuaEngine& lua,std::size_t capacity):repository_(repository),lua_(lua),capacity_(capacity) {
    if(!capacity_)throw std::invalid_argument("Skill book service requires actual session capacity");
}
void OwnedSkillBookLearningService::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Skill book service game owner mismatch");
}
bool OwnedSkillBookLearningService::ready(Session& session,const std::shared_ptr<Entry>& entry,bool written) const {
    if(thread_!=std::this_thread::get_id()||!live_||poisoned_||!entry||entry->revoked||
       entry->session.lock().get()!=&session || !entry->initialization.entry_written() ||
       !session.normal_world_initialization_current_on_game(entry->initialization))return false;
    const auto retained=entries_.find(session.id());
    if(retained==entries_.end() || retained->second!=entry || session.closing() ||
       session.state()!=entry->phase ||
       (entry->phase!=SessionState::CharacterSelected && entry->phase!=SessionState::InWorld) ||
       !session.recovered_world_ready() ||
       session.account_id!=entry->account || session.character_id!=entry->character ||
       session.battle_generation()!=entry->battle)return false;
    if(!entry->actor || !entry->original_restoration)return false;
    if(entry->presence) {
        if(!entry->lease || entry->lease->actor_handle!=entry->actor || !entry->presence->retained_ready_current(*entry->lease) ||
           !session.common_world_delivery_current(entry->account,entry->character,entry->lease->generation) ||
           session.common_world_entry_current(entry->account,entry->character,entry->lease->generation))return false;
    } else if(entry->lease)return false;
    return !written || entry->bootstrap_complete_without_reply || (entry->bootstrap_response &&
        entry->bootstrap_response->status()==Session::WorldResponseWriteStatus::Written &&
        session.world_response_write_current_on_game(*entry->bootstrap_response));
}
bool OwnedSkillBookLearningService::qualify_presence(Session& session,const std::shared_ptr<Entry>& entry,
        const NativeEquipmentSnapshot& equipment) const {
    if(!ready(session,entry,false) || equipment.actor_handle!=entry->actor)return false;
    if(!entry->presence)return true;
    const auto actual=entry->presence->ready_lease(session.id(),entry->account,entry->character);
    const auto position=entry->presence->saved_position(*entry->lease);
    return actual && *actual==*entry->lease && actual->actor_handle==equipment.actor_handle &&
        position && *position==equipment.position && ready(session,entry,false);
}
void OwnedSkillBookLearningService::retire(Session& session,const std::shared_ptr<Entry>& entry) noexcept {
    if(entry)entry->revoked=true;
    const auto found=entries_.find(session.id());
    if(found!=entries_.end()&&found->second==entry)entries_.erase(found);
}
void OwnedSkillBookLearningService::preflight(Session& session) {
    (void)session;owner();
    if(busy_) {poisoned_=true;throw std::logic_error("Skill book facade reentry rejected");}
    if(!live_)throw std::logic_error("Skill book facade stopped");
}
bool OwnedSkillBookLearningService::claims(std::uint16_t item) {
    Operation operation(*this);
    const auto book=repository_.lookup_book(item);
    if(poisoned_||!live_)throw std::logic_error("Skill book claim source changed");
    return bool(book);
}
std::optional<std::vector<std::uint8_t>> OwnedSkillBookLearningService::bootstrap(Session& session,
        const std::shared_ptr<SharedWorldPresence>& presence,const RestorationSupplier& supplier) {
    Operation operation(*this);const auto common=presence;
    std::shared_ptr<Entry> entry;
    const auto old=entries_.find(session.id());
    if(old!=entries_.end()) {
        entry=old->second;
        if(entry->bootstrap_response &&
           entry->bootstrap_response->status()==Session::WorldResponseWriteStatus::Failed) {
            // An actual failed local publication is terminal, not a replay source.
            retire(session,entry);throw std::logic_error("Skill book bootstrap publication failed");
        }
        const bool same=entry->presence==common && ready(session,entry,false);
        if(same && (entry->bootstrap_complete_without_reply || (entry->bootstrap_response &&
           entry->bootstrap_response->status()!=Session::WorldResponseWriteStatus::Failed &&
           session.world_response_write_current_on_game(*entry->bootstrap_response))))
            return std::vector<std::uint8_t>{}; // Do not requery an old roster consumed by real learning.
        retire(session,entry);entry.reset(); // New actual source needed; never rebase an old grant.
    }
    if(entries_.size()>=capacity_ || session.weak_from_this().lock().get()!=&session)return std::nullopt;
    const auto init=session.normal_world_initialization();
    if(!init || !init->entry_written() || !session.normal_world_initialization_current_on_game(*init) ||
       session.closing() || (session.state()!=SessionState::CharacterSelected &&
       session.state()!=SessionState::InWorld))return std::vector<std::uint8_t>{};
    const auto restored=supplier; // Own callable before any observer can retire its caller holder.
    if(!restored)return std::vector<std::uint8_t>{};
    const auto original=restored(session); // Actual original sender's Written source, no second deity replay.
    if(!original)return std::vector<std::uint8_t>{}; // Pending/missing source defers without entry/grant.
    if(!original->owns_learning_repository(repository_) || !original->learning_source() ||
       poisoned_ || !live_ || !session.normal_world_initialization_current_on_game(*init))return std::nullopt;
    const auto& logical=init->entry_logical();
    if(logical.size()!=37 || logical[0]!=0x2a)return std::nullopt;
    const auto actor=static_cast<std::uint16_t>((std::uint16_t(logical[1])|(std::uint16_t(logical[2])<<8))&0x3fff);
    if(!actor)return std::nullopt;
    std::optional<SharedWorldPresence::Lease> lease;
    if(common)lease=common->ready_lease(session.id(),session.account_id,session.character_id);
    if((common&&!lease) || poisoned_ || !live_ || !session.normal_world_initialization_current_on_game(*init) ||
       restored(session)!=original)return std::nullopt;
    entry=std::make_shared<Entry>(session,*init,common,std::move(lease),actor,original);
    entries_.emplace(session.id(),entry); // All slot/ownership allocations before projection observers.
    try {
        const auto& source=*original->learning_source();
        if(!ready(session,entry,false)||!qualify_presence(session,entry,source.equipment())) {
            retire(session,entry);return std::nullopt;
        }
        std::vector<std::uint8_t> books;
        for(std::uint8_t slot=0;slot<30;++slot) {
            const auto* item=item_at(source.inventory(),slot);if(!item)continue;
            const auto identity=std::find_if(item->aliases.begin(),item->aliases.end(),[&](const auto& alias){
                return alias.client_sha256==NativeEquipmentSnapshot::client_pin &&
                    alias.profile==SharedTaiwanOwnedItemSelectionSource::alias_profile && alias.native_slot==slot;
            });
            if(identity==item->aliases.end() || identity->record.size()!=20) {retire(session,entry);return std::nullopt;}
            const auto key=identity->native_key;
            const auto book=repository_.lookup_book(key);
            if(!ready(session,entry,false)) {retire(session,entry);return std::nullopt;}
            if(!book)continue;
            const auto fields=material(*item,slot);if(!fields) {retire(session,entry);return std::nullopt;}
            const auto& witness=source.equipment().record;const auto at=std::size_t(slot)*24;
            if(witness.size()!=NativeEquipmentSnapshot::record_bytes || !item->quantity || item->quantity>99 ||
               witness[at]!=item->quantity || !std::equal(fields->instance.begin(),fields->instance.end(),witness.begin()+at+4)) {
                retire(session,entry);return std::nullopt;
            }
            const auto full=RecoveredTaiwanInventoryItemRecord::encode(*fields);
            const auto absolute=RecoveredInventory::encode_slot_update({key,slot,static_cast<std::uint8_t>(item->quantity)});
            if(!full||!absolute) {retire(session,entry);return std::nullopt;}
            books.insert(books.end(),full->begin(),full->end());books.insert(books.end(),absolute->begin(),absolute->end());
        }
        std::vector<std::uint8_t> wire;append_frame(wire,books);
        if(!ready(session,entry,false)||!qualify_presence(session,entry,source.equipment()) ||
           !repository_.restoration_current(source)||!ready(session,entry,false) ||
           restored(session)!=original || !ready(session,entry,false)) {
            retire(session,entry);return std::nullopt;
        }
        entry->bootstrap_wire=wire;
        // Private proof of no ADDITIONAL output, only after actual original Written
        // restoration + full source/current + exact supplier identity. No dummy FIFO.
        entry->bootstrap_complete_without_reply=wire.empty();
        return std::optional<std::vector<std::uint8_t>>(std::move(wire));
    } catch(...) {retire(session,entry);throw;}
}
void OwnedSkillBookLearningService::bind_bootstrap_response(Session& session,const Session::WorldResponseWrite& response) {
    Operation operation(*this);
    const auto found=entries_.find(session.id());
    const auto entry=found==entries_.end()?std::shared_ptr<Entry>{}:found->second;
    if(!ready(session,entry,false)||entry->bootstrap_response||entry->bootstrap_wire.empty() ||
       response.status()!=Session::WorldResponseWriteStatus::Pending ||
       !session.world_response_write_current(response) || response.wire().size()<entry->bootstrap_wire.size() ||
       !std::equal(entry->bootstrap_wire.rbegin(),entry->bootstrap_wire.rend(),response.wire().rbegin())) {
        retire(session,entry);throw std::logic_error("Skill book bootstrap requires actual final original response custody");
    }
    entry->bootstrap_response.emplace(response); // Private owning receipt copy, no allocation/second capture.
}
std::optional<std::vector<std::uint8_t>> OwnedSkillBookLearningService::use(Session& session,
        const RecoveredInventoryItemRequest::Request& request,const std::shared_ptr<SharedWorldPresence>& presence) {
    const auto owned_request=request;const auto common=presence;
    Operation operation(*this);
    const auto found=entries_.find(session.id());
    const auto entry=found==entries_.end()?std::shared_ptr<Entry>{}:found->second;
    if(owned_request.raw_slot>=30 || !ready(session,entry,true) ||
       entry->presence!=common)return std::nullopt;
    try {
        const auto observed=repository_.observe(entry->account,entry->character,owned_request.raw_slot,owned_request.client_item_id);
        if(!observed||!ready(session,entry,true)||!qualify_presence(session,entry,observed->equipment()) ||
           !repository_.current(*observed)||!ready(session,entry,true))return std::nullopt;
        const auto* item=item_at(observed->inventory(),owned_request.raw_slot);
        if(!item || item->quantity>99)return std::nullopt;
        const auto policy=lua_.skill_book_learning({static_cast<std::uint32_t>(item->quantity),
            static_cast<std::uint32_t>(observed->deity().snapshot.skills.size()),observed->already_learned(),
            RecoveredDeityState::has_current_skill_icon(observed->book().kind,observed->book().definition_id)});
        if(!ready(session,entry,true)||!repository_.current(*observed)||!ready(session,entry,true))return std::nullopt;
        if(!policy.allowed)return std::nullopt;
        if(policy.duplicate)return std::vector<std::uint8_t>{}; // Explicit idempotent no debit/no new activation.
        if(policy.consume!=1)return std::nullopt;
        const auto plan=repository_.plan(*observed);
        if(!plan||!ready(session,entry,true)||!qualify_presence(session,entry,observed->equipment()) ||
           !repository_.current(*observed)||!ready(session,entry,true))return std::nullopt;
        std::vector<std::uint8_t> logical;
        const auto& skill=plan->skill().encode();logical.insert(logical.end(),skill.begin(),skill.end());
        const auto& issued=plan->activation();
        const auto activation=RecoveredDeityActivation::encode(issued.subject,issued.kind,issued.definition_id);
        logical.insert(logical.end(),activation.begin(),activation.end());
        const auto inventory=RecoveredInventory::encode_slot_update(plan->slot_update());
        if(!inventory)return std::nullopt;
        logical.insert(logical.end(),inventory->begin(),inventory->end());
        auto wire=RecoveredWorldFrame::encode(logical); // Entire native-format response PRECOMMIT.
        const auto committed=repository_.commit(*plan,[&]{return ready(session,entry,true);});
        if(!committed)return std::nullopt;
        entry->latest_commit.emplace(*committed); // Own actual after tuple; shared preallocated data only.
        if(!ready(session,entry,true))throw std::logic_error("Skill book durable prefix committed after source retirement");
        // No postCOMMIT query/allocation/retry/rollback/const-vector copy.
        return std::optional<std::vector<std::uint8_t>>(std::move(wire));
    } catch(...) {retire(session,entry);throw;}
}
void OwnedSkillBookLearningService::release(Session& session) {
    owner();if(busy_)poisoned_=true;
    const auto found=entries_.find(session.id());
    if(found!=entries_.end()&&found->second->session.lock().get()==&session) {
        const auto entry=found->second;retire(session,entry);
    }
}
void OwnedSkillBookLearningService::stop() {
    owner();if(busy_)poisoned_=true;live_=false;
    for(const auto& [id,entry]:entries_)entry->revoked=true;
    entries_.clear();
}
}
