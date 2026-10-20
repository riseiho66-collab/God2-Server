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
bool same_roster(const OwnedDeityRosterReadset& a,const OwnedDeityRosterReadset& b) {
    if(a.account()!=b.account()||a.character()!=b.character()||a.selection()!=b.selection()||
       a.template_keys()!=b.template_keys()||a.rows().size()!=b.rows().size())return false;
    for(std::size_t i=0;i<a.rows().size();++i){
        const auto& x=a.rows()[i];const auto& y=b.rows()[i];
        if(x.revision!=y.revision||x.provenance!=y.provenance||
           x.snapshot.declaration.encode()!=y.snapshot.declaration.encode()||
           x.snapshot.status.encode()!=y.snapshot.status.encode()||x.snapshot.skills.size()!=y.snapshot.skills.size())return false;
        for(std::size_t n=0;n<x.snapshot.skills.size();++n)
            if(x.snapshot.skills[n].encode()!=y.snapshot.skills[n].encode())return false;
    }
    return true;
}
bool same_learning(const SqliteSkillBookLearningRepository::Restoration& a,
        const SqliteSkillBookLearningRepository::Restoration& b) {
    return a.inventory()==b.inventory()&&a.equipment()==b.equipment()&&
        a.activations()==b.activations()&&same_roster(a.roster(),b.roster());
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
    struct SelectionAnchor {
        const SelectionSource source;
        bool current(Session& session)const {
            return std::visit([&](const auto& actual){return actual.current(session);},source);
        }
        template<class Source> bool same_source(const Source& candidate)const {
            const auto* held=std::get_if<Source>(&source);
            return held && held->same_source(candidate);
        }
    };
    std::shared_ptr<const SelectionAnchor> selection_anchor;
    std::shared_ptr<WrittenMaterialSource::Data> material_anchor;
    bool bootstrap_complete_without_reply=false;
    std::shared_ptr<SharedWorldPresence> presence;
    std::optional<SharedWorldPresence::Lease> lease;
    std::vector<std::uint8_t> bootstrap_wire;
    std::optional<Session::WorldResponseWrite> bootstrap_response;
    std::optional<SqliteSkillBookLearningRepository::Committed> latest_commit;
    std::shared_ptr<LearningPublication::Data> pending_publication,latest_publication;
    bool revoked=false;
    Entry(Session& source,Session::NormalWorldInitialization init,std::shared_ptr<SharedWorldPresence> common,
          std::optional<SharedWorldPresence::Lease> owned,std::uint16_t native_actor,
          std::shared_ptr<const RecoveredOwnedCompanions::Restoration> restored)
        :session(source.weak_from_this()),initialization(std::move(init)),account(source.account_id),
         character(source.character_id),battle(source.battle_generation()),phase(source.state()),actor(native_actor),
         original_restoration(std::move(restored)),presence(std::move(common)),lease(std::move(owned)) {}
};
struct OwnedSkillBookLearningService::Lifetime {OwnedSkillBookLearningService* owner;};
struct OwnedSkillBookLearningService::MaterialEpoch {
    std::weak_ptr<Session> session;
    Session::NormalWorldInitialization initialization;
    bool retired=false;
};
struct OwnedSkillBookLearningService::WrittenMaterialSource::Data {
    std::weak_ptr<Lifetime> life;
    std::weak_ptr<Session> session;
    Session::NormalWorldInitialization initialization;
    Session::WorldResponseWrite response;
    std::shared_ptr<const RecoveredOwnedCompanions::Restoration> material;
    std::shared_ptr<SqliteOwnedEquipmentTransaction> joint;
    SqliteOwnedEquipmentTransaction::Committed committed;
    std::uint64_t account,character,battle;
    SessionState phase;
    bool valid=true;
};
struct OwnedSkillBookLearningService::MaterialAdmission::Data {
    std::weak_ptr<Lifetime> life;
    std::weak_ptr<Session> session;
    std::shared_ptr<Entry> entry;
    std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,original;
    std::shared_ptr<LearningPublication::Data> latest,pending;
    std::shared_ptr<const Entry::SelectionAnchor> selection;
    std::shared_ptr<WrittenMaterialSource::Data> material;
    Session::NormalWorldInitialization initialization;
    std::uint64_t account,character,battle;
    SessionState phase;
    bool valid=true;
};
struct OwnedSkillBookLearningService::LearningPublication::Data {
    enum class Phase {Prepared,Committed,Bound,Revoked};
    const std::weak_ptr<Lifetime> life;
    const std::weak_ptr<Entry> entry;
    const std::weak_ptr<Session> session;
    const Session::NormalWorldInitialization initialization;
    const std::shared_ptr<const RecoveredOwnedCompanions::Restoration> original_restoration;
    const SqliteSkillBookLearningRepository::Restoration before;
    const SqliteSkillBookLearningRepository::Plan plan;
    const SqliteSkillBookLearningRepository::Restoration after;
    const std::array<std::uint8_t,13> logical_delta;
    const std::vector<std::uint8_t> wire;
    const std::weak_ptr<Data> previous;
    const std::thread::id thread=std::this_thread::get_id();
    std::atomic<Phase> phase{Phase::Prepared};
    std::optional<SqliteSkillBookLearningRepository::Committed> committed;
    std::optional<Session::WorldResponseWrite> response;
    Data(std::weak_ptr<Lifetime> owner,std::shared_ptr<Entry> source,
         const SqliteSkillBookLearningRepository::Plan& p,SqliteSkillBookLearningRepository::Restoration b,
         SqliteSkillBookLearningRepository::Restoration a,std::array<std::uint8_t,13> delta,
         std::vector<std::uint8_t> bytes,std::shared_ptr<Data> prior)
        :life(std::move(owner)),entry(source),session(source->session),initialization(source->initialization),
         original_restoration(source->original_restoration),before(std::move(b)),plan(p),after(std::move(a)),
         logical_delta(delta),wire(std::move(bytes)),previous(std::move(prior)){}
};
struct OwnedSkillBookLearningService::Operation {
    OwnedSkillBookLearningService& service;
    explicit Operation(OwnedSkillBookLearningService& value,bool allow_unbound=false):service(value) {
        service.owner();
        if(service.busy_) {service.poisoned_=true;throw std::logic_error("Skill book service reentry rejected");}
        if(!service.live_)throw std::logic_error("Skill book service stopped");
        if(!allow_unbound)if(const auto active=service.active_publication_.lock();active&&
           active->phase.load()!=LearningPublication::Data::Phase::Bound&&
           active->phase.load()!=LearningPublication::Data::Phase::Revoked) {
            service.poisoned_=true;service.revoke_publication(active,true);
            throw std::logic_error("Skill book committed result was not handed to its original response");
        }
        service.busy_=true;service.poisoned_=false;
    }
    ~Operation(){service.busy_=false;}
};
OwnedSkillBookLearningService::OwnedSkillBookLearningService(SqliteSkillBookLearningRepository& repository,
        LuaEngine& lua,std::size_t capacity):repository_(repository),lua_(lua),capacity_(capacity),lifetime_(std::make_shared<Lifetime>(Lifetime{this})) {
    if(!capacity_)throw std::invalid_argument("Skill book service requires actual session capacity");
}
OwnedSkillBookLearningService::~OwnedSkillBookLearningService() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    stop();
}
const SqliteSkillBookLearningRepository::Restoration& OwnedSkillBookLearningService::LearningPublication::after_source()const noexcept{return data_->after;}
const SqliteSkillBookLearningRepository::Committed& OwnedSkillBookLearningService::LearningPublication::committed()const noexcept{return *data_->committed;}
const std::shared_ptr<const RecoveredOwnedCompanions::Restoration>& OwnedSkillBookLearningService::LearningPublication::original_restoration()const noexcept{return data_->original_restoration;}
const Session::NormalWorldInitialization& OwnedSkillBookLearningService::LearningPublication::initialization()const noexcept{return data_->initialization;}
const SqliteSkillBookLearningRepository::Restoration& OwnedSkillBookLearningService::WrittenLearningSource::before_source()const noexcept{return publication_.data_->before;}
const SqliteSkillBookLearningRepository::Restoration& OwnedSkillBookLearningService::WrittenLearningSource::after_source()const noexcept{return publication_.data_->after;}
const SqliteSkillBookLearningRepository::Committed& OwnedSkillBookLearningService::WrittenLearningSource::committed()const noexcept{return *publication_.data_->committed;}
const std::vector<std::uint8_t>& OwnedSkillBookLearningService::WrittenLearningSource::wire()const noexcept{return publication_.data_->wire;}
const std::array<std::uint8_t,13>& OwnedSkillBookLearningService::WrittenLearningSource::logical_delta()const noexcept{return publication_.data_->logical_delta;}
const std::shared_ptr<const RecoveredOwnedCompanions::Restoration>& OwnedSkillBookLearningService::WrittenLearningSource::original_restoration()const noexcept{return publication_.data_->original_restoration;}
const Session::NormalWorldInitialization& OwnedSkillBookLearningService::WrittenLearningSource::initialization()const noexcept{return publication_.data_->initialization;}
bool OwnedSkillBookLearningService::WrittenLearningSource::follows(const std::optional<LearningPublication>& prior)const noexcept {
    const auto& previous=publication_.data_->previous;
    if(prior) {
        if(!prior->data_)return false;
        return previous.lock()==prior->data_ && !previous.owner_before(prior->data_) && !prior->data_.owner_before(previous);
    }
    const std::weak_ptr<LearningPublication::Data> empty;
    // An expired nonempty controlblock is NOT the first learning event.
    return !previous.owner_before(empty) && !empty.owner_before(previous);
}
bool OwnedSkillBookLearningService::WrittenLearningSource::current(Session& session)const {
    const auto owned=*this;const auto data=owned.publication_.data_;
    if(!data || data->thread!=std::this_thread::get_id())return false;
    const auto peer=data->session.lock();if(peer.get()!=&session)return false;
    const auto life=data->life.lock();if(!life || !life->owner)return false;
    // Actual serial game-owned service/dependencies must outlive source calls.
    return life->owner->written_learning_source_current(session,owned);
}
const Session::NormalWorldInitialization& OwnedSkillBookLearningService::WrittenMaterialSource::initialization()const noexcept{return data_->initialization;}
const std::shared_ptr<const RecoveredOwnedCompanions::Restoration>& OwnedSkillBookLearningService::WrittenMaterialSource::material()const noexcept{return data_->material;}
bool OwnedSkillBookLearningService::WrittenMaterialSource::current(Session& session)const {
    const auto held=data_;if(!held)return false;
    const auto life=held->life.lock();if(!life || !life->owner)return false;
    return life->owner->material_current(session,held);
}
OwnedSkillBookLearningService::UseResult::UseResult(std::vector<std::uint8_t> wire,std::optional<LearningPublication> publication)noexcept
    :wire_(std::move(wire)),publication_(std::move(publication)),owns_unbound_(bool(publication_)){}
OwnedSkillBookLearningService::UseResult::UseResult(UseResult&& other)noexcept
    :wire_(std::move(other.wire_)),publication_(std::move(other.publication_)),
     owns_unbound_(std::exchange(other.owns_unbound_,false)){}
OwnedSkillBookLearningService::UseResult& OwnedSkillBookLearningService::UseResult::operator=(UseResult&& other)noexcept {
    if(this!=&other) {
        if(owns_unbound_&&publication_)OwnedSkillBookLearningService::abandon_unbound(*publication_);
        wire_=std::move(other.wire_);publication_=std::move(other.publication_);
        owns_unbound_=std::exchange(other.owns_unbound_,false);
    }
    return *this;
}
OwnedSkillBookLearningService::UseResult::~UseResult(){if(owns_unbound_&&publication_)OwnedSkillBookLearningService::abandon_unbound(*publication_);}
void OwnedSkillBookLearningService::discard_publication(const std::shared_ptr<LearningPublication::Data>& data)noexcept {
    if(const auto entry=data->entry.lock()) {
        if(entry->pending_publication==data)entry->pending_publication.reset();
        if(entry->latest_publication==data)entry->latest_publication.reset();
    }
    if(active_publication_.lock()==data)active_publication_.reset();
}
void OwnedSkillBookLearningService::revoke_publication(const std::shared_ptr<LearningPublication::Data>& data,bool close_unsettled)noexcept {
    if(!data)return;
    const auto old=data->phase.exchange(LearningPublication::Data::Phase::Revoked);
    // Non-game callers may only poison and close the exact weak Session. No
    // Entry/map/Lifetime.owner/optional-response access crosses that boundary.
    if(data->thread!=std::this_thread::get_id()) {
        if(close_unsettled&&old==LearningPublication::Data::Phase::Committed)
            if(const auto peer=data->session.lock())try{peer->close();}catch(...){}
        return;
    }
    const bool written=data->response&&data->response->status()==Session::WorldResponseWriteStatus::Written;
    if(close_unsettled&&data->committed&&!written)
        if(const auto peer=data->session.lock())try{peer->close();}catch(...){}
    if(const auto life=data->life.lock();life&&life->owner)life->owner->discard_publication(data);
}
void OwnedSkillBookLearningService::abandon_unbound(const LearningPublication& publication)noexcept {
    const auto data=publication.data_;if(!data)return;
    auto phase=data->phase.load();
    for(;;) {
        if(phase==LearningPublication::Data::Phase::Bound||phase==LearningPublication::Data::Phase::Revoked)return;
        if(data->phase.compare_exchange_weak(phase,LearningPublication::Data::Phase::Revoked))break;
    }
    if(phase==LearningPublication::Data::Phase::Committed)
        if(const auto peer=data->session.lock())try{peer->close();}catch(...){}
    if(data->thread==std::this_thread::get_id())
        if(const auto life=data->life.lock();life&&life->owner)life->owner->discard_publication(data);
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
    if(entry->material_anchor && (!entry->material_anchor->valid ||
       entry->material_anchor->response.status()!=Session::WorldResponseWriteStatus::Written ||
       !session.world_response_write_current_on_game(entry->material_anchor->response)))return false;
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
    if(const auto epoch=material_epochs_.find(session.id());epoch!=material_epochs_.end() && epoch->second->session.lock().get()==&session)
        epoch->second->retired=true;
    if(const auto admission=material_admissions_.find(session.id());admission!=material_admissions_.end() && admission->second->session.lock().get()==&session) {
        admission->second->valid=false;material_admissions_.erase(admission);
    }
    if(const auto source=material_sources_.find(session.id());source!=material_sources_.end() && source->second->session.lock().get()==&session) {
        source->second->valid=false;material_sources_.erase(source);
    }
    if(entry) {
        entry->revoked=true;
        const auto pending=entry->pending_publication,latest=entry->latest_publication;
        revoke_publication(pending,true);if(latest!=pending)revoke_publication(latest,true);
    }
    const auto found=entries_.find(session.id());
    if(found!=entries_.end()&&found->second==entry)entries_.erase(found);
}
void OwnedSkillBookLearningService::preflight(Session& session) {
    (void)session;owner();
    if(busy_) {
        poisoned_=true;revoke_publication(active_publication_.lock(),true);
        throw std::logic_error("Skill book facade reentry rejected");
    }
    if(!live_)throw std::logic_error("Skill book facade stopped");
    if(const auto active=active_publication_.lock();active&&
       active->phase.load()!=LearningPublication::Data::Phase::Bound&&
       active->phase.load()!=LearningPublication::Data::Phase::Revoked) {
        poisoned_=true;revoke_publication(active,true);
        throw std::logic_error("Skill book original result reentered before response handoff");
    }
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
    if(!admit_material_epoch(session,*init))return std::nullopt;
    const auto restored=supplier; // Own callable before any observer can retire its caller holder.
    if(!restored)return std::vector<std::uint8_t>{};
    const auto invoke_restored=[&] {
        if(passive_material_window_ || material_reading_) {
            poisoned_=true;throw std::logic_error("Skill-book bootstrap passive source window reentered");
        }
        const auto at=material_sources_.find(session.id());
        const auto window=at==material_sources_.end()?std::shared_ptr<WrittenMaterialSource::Data>{}:at->second;
        const auto existing=entries_.find(session.id());
        const auto current_entry=existing==entries_.end()?std::shared_ptr<Entry>{}:existing->second;
        passive_material_window_=window;passive_material_entry_=current_entry;
        struct WindowEnd {OwnedSkillBookLearningService& self;~WindowEnd(){self.passive_material_window_.reset();self.passive_material_entry_.reset();}} window_end{*this};
        try {
            auto result=restored(session);
            if(poisoned_ || !live_)throw std::logic_error("Skill-book bootstrap supplier poisoned its passive source");
            return result;
        } catch(...) {retire(session,current_entry);throw;}
    };
    const auto original=invoke_restored(); // Actual original sender's Written source, no second deity replay.
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
       invoke_restored()!=original)return std::nullopt;
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
           invoke_restored()!=original || !ready(session,entry,false)) {
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
bool OwnedSkillBookLearningService::reanchor_selection(Session& session,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical,
        SharedTaiwanOwnedDeitySkillSource::WrittenSelectionSource source) {
    return reanchor_selection_impl(session,std::move(predecessor),std::move(canonical),SelectionSource{std::move(source)});
}
bool OwnedSkillBookLearningService::reanchor_selection(Session& session,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical,
        LegacyTaiwanOwnedDeitySelectionRegistry::WrittenSelectionSource source) {
    return reanchor_selection_impl(session,std::move(predecessor),std::move(canonical),SelectionSource{std::move(source)});
}
bool OwnedSkillBookLearningService::reanchor_selection_impl(Session& session,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
        std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical,
        SelectionSource selection_source) {
    Operation operation(*this);
    return std::visit([&](const auto& source)->bool {
    const auto found=entries_.find(session.id());
    if(found==entries_.end()) {
        const bool current=predecessor && canonical && source.current(session) && !poisoned_;
        if(current)if(const auto material=material_sources_.find(session.id());material!=material_sources_.end() &&
            material->second->session.lock().get()==&session)material->second->valid=false;
        return current; // No Entry is minted, but a real selection retires prior material Current.
    }
    const auto entry=found->second;const auto original=entry->original_restoration;
    const auto latest=entry->latest_publication;const auto anchor=entry->selection_anchor;
    const auto material_anchor=entry->material_anchor;
    const auto local=[&]{
        return ready(session,entry,true)&&entry->original_restoration==original&&
            entry->latest_publication==latest&&entry->selection_anchor==anchor&&entry->material_anchor==material_anchor&&
            source.initialization().same_initialization(entry->initialization);
    };
    if(!predecessor||!canonical||!predecessor->owns_learning_repository(repository_)||
       !canonical->owns_learning_repository(repository_)||!predecessor->learning_source()||!canonical->learning_source()||
       !local()||(anchor&&anchor->same_source(source))||!source.current(session)||!local())return false;
    if(latest && (latest->phase.load()!=LearningPublication::Data::Phase::Bound||!latest->response||
       latest->response->status()!=Session::WorldResponseWriteStatus::Written||
       !session.world_response_write_current_on_game(*latest->response)))return false;
    if(entry->pending_publication && entry->pending_publication!=latest)return false;
    const auto& before=(anchor||material_anchor)?*original->learning_source():
        (latest?latest->after:*original->learning_source());
    if(!same_learning(before,*predecessor->learning_source()))return false;
    std::vector<const SqliteCompanionRepository::CommittedDeitySelection*> commits;
    commits.reserve(source.publications().size());auto history=predecessor->batches();
    for(const auto& publication:source.publications()){
        commits.push_back(&publication.committed());
        const auto raw=publication.committed().deity().snapshot.status.encode();
        if(raw.size()!=29||raw[0]!=0x31||RecoveredWorldFrame::encode(raw)!=publication.wire())return false;
        history.emplace_back(raw.begin(),raw.end());
    }
    const auto after=repository_.selection_successor(before,commits);
    if(!after||!local()||!same_learning(*after,*canonical->learning_source())||
       !same_roster(canonical->deity_roster(),after->roster())||history!=canonical->batches()||
       !qualify_presence(session,entry,after->equipment())||!local()||!source.current(session)||!local())return false;
    const auto next=std::make_shared<const Entry::SelectionAnchor>(Entry::SelectionAnchor{selection_source});
    if(!local())return false;
    if(const auto prior_material=material_sources_.find(session.id());prior_material!=material_sources_.end() &&
       prior_material->second->session.lock().get()==&session)prior_material->second->valid=false;
    if(material_anchor)material_anchor->valid=false;
    entry->material_anchor.reset();
    entry->original_restoration=std::move(canonical);entry->selection_anchor=next;
    entry->pending_publication.reset(); // Historical Bound token is not revived.
    return ready(session,entry,true);
    },selection_source);
}
bool OwnedSkillBookLearningService::material_current(Session& session,const std::shared_ptr<WrittenMaterialSource::Data>& data) {
    owner();
    const bool borrowed=busy_;
    if(material_reading_ || (borrowed && (!data || passive_material_window_!=data ||
       data->session.lock().get()!=&session))) {
        poisoned_=true;throw std::logic_error("Skill-book material source read reentered outside its exact bootstrap window");
    }
    std::optional<Operation> operation;
    if(!borrowed)operation.emplace(*this,true);
    material_reading_=true;
    struct ReadEnd {bool& flag;~ReadEnd(){flag=false;}} read_end{material_reading_};
    if(!data)return false;
    const auto connection=data->session.lock();
    const auto expected_entry=borrowed?passive_material_entry_:std::shared_ptr<Entry>{};
    const auto local=[&] {
        const auto at=material_sources_.find(session.id());
        const auto life=data->life.lock();
        const auto entry=entries_.find(session.id());
        return life && life->owner==this && live_ && !poisoned_ && data->valid && connection.get()==&session &&
            (!borrowed || (passive_material_window_==data && passive_material_entry_==expected_entry &&
                (expected_entry?(entry!=entries_.end() && entry->second==expected_entry && !expected_entry->revoked &&
                    expected_entry->session.lock()==connection && expected_entry->original_restoration==data->material &&
                    expected_entry->initialization.same_initialization(data->initialization)):
                    entry==entries_.end()))) &&
            at!=material_sources_.end() && at->second==data && !session.closing() && session.recovered_world_ready() &&
            session.account_id==data->account && session.character_id==data->character && session.battle_generation()==data->battle &&
            session.state()==data->phase && (data->phase==SessionState::CharacterSelected || data->phase==SessionState::InWorld) &&
            data->initialization.entry_written() && session.normal_world_initialization_current_on_game(data->initialization) &&
            data->response.status()==Session::WorldResponseWriteStatus::Written && session.world_response_write_current_on_game(data->response);
    };
    try {
        return local() && data->joint->committed_current(data->committed) && local() &&
            data->material->learning_source() && repository_.restoration_current(*data->material->learning_source()) && local();
    } catch(...) {poisoned_=true;throw;}
}
std::optional<OwnedSkillBookLearningService::MaterialAdmission> OwnedSkillBookLearningService::prepare_material(
    Session& session,std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor) {
    Operation operation(*this);
    const auto initialization=session.normal_world_initialization();
    if(!predecessor || !predecessor->owns_learning_repository(repository_) || !initialization ||
       !initialization->entry_written() || !session.normal_world_initialization_current_on_game(*initialization) ||
       session.closing() || !session.recovered_world_ready())return {};
    if(!admit_material_epoch(session,*initialization))return {};
    const auto at=entries_.find(session.id());const auto entry=at==entries_.end()?std::shared_ptr<Entry>{}:at->second;
    if(entry && !ready(session,entry,true))return {};
    const auto previous=material_admissions_.find(session.id());
    if(previous==material_admissions_.end() && material_admissions_.size()>=capacity_)return {};
    auto next=std::make_shared<MaterialAdmission::Data>(MaterialAdmission::Data{
        lifetime_,session.weak_from_this(),entry,predecessor,entry?entry->original_restoration:nullptr,
        entry?entry->latest_publication:nullptr,entry?entry->pending_publication:nullptr,
        entry?entry->selection_anchor:nullptr,entry?entry->material_anchor:nullptr,*initialization,
        session.account_id,session.character_id,session.battle_generation(),session.state(),true});
    if(previous!=material_admissions_.end())previous->second->valid=false;
    material_admissions_.insert_or_assign(session.id(),next);
    return MaterialAdmission(std::move(next));
}
void OwnedSkillBookLearningService::abandon_material(const MaterialAdmission& source) noexcept {
    const auto data=source.data_;if(!data)return;
    if(thread_!=std::this_thread::get_id())return;
    const auto life=data->life.lock();if(!life || life->owner!=this)return;
    data->valid=false;
    if(const auto session=data->session.lock()) {
        const auto at=material_admissions_.find(session->id());
        if(at!=material_admissions_.end() && at->second==data)material_admissions_.erase(at);
    }
}
std::optional<OwnedSkillBookLearningService::WrittenMaterialSource> OwnedSkillBookLearningService::reanchor_material(
    Session& session,std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
    std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical,
    std::shared_ptr<SqliteOwnedEquipmentTransaction> joint,const SqliteOwnedEquipmentTransaction::Committed& committed,
    const Session::NormalWorldInitialization& supplied_initialization,const Session::WorldResponseWrite& supplied_response,
    const MaterialAdmission& supplied_admission) {
    const std::array<const SqliteOwnedEquipmentTransaction::Committed*,1> chain{&committed};
    return reanchor_material_chain(session,std::move(predecessor),std::move(canonical),std::move(joint),chain,
        supplied_initialization,supplied_response,supplied_admission);
}
bool OwnedSkillBookLearningService::admit_material_epoch(Session& session,const Session::NormalWorldInitialization& initialization) {
    const auto found=material_epochs_.find(session.id());
    if(found!=material_epochs_.end()) {
        if(found->second->session.lock().get()!=&session)return false;
        if(found->second->initialization.same_initialization(initialization))return !found->second->retired;
        // Only a different actual private INIT can start a new epoch. A
        // release/rebootstrap of the same values/Entry absence cannot do so.
        found->second=std::make_shared<MaterialEpoch>(MaterialEpoch{session.weak_from_this(),initialization,false});
        return true;
    }
    if(material_epochs_.size()>=capacity_) {
        for(auto it=material_epochs_.begin();it!=material_epochs_.end();)
            if(it->second->session.expired())it=material_epochs_.erase(it);else ++it;
        if(material_epochs_.size()>=capacity_)return false;
    }
    material_epochs_.emplace(session.id(),std::make_shared<MaterialEpoch>(MaterialEpoch{session.weak_from_this(),initialization,false}));
    return true;
}
std::optional<OwnedSkillBookLearningService::WrittenMaterialSource> OwnedSkillBookLearningService::reanchor_material_chain(
    Session& session,std::shared_ptr<const RecoveredOwnedCompanions::Restoration> predecessor,
    std::shared_ptr<const RecoveredOwnedCompanions::Restoration> canonical,
    std::shared_ptr<SqliteOwnedEquipmentTransaction> joint,std::span<const SqliteOwnedEquipmentTransaction::Committed* const> commits,
    const Session::NormalWorldInitialization& supplied_initialization,const Session::WorldResponseWrite& supplied_response,
    const MaterialAdmission& supplied_admission) {
    Operation operation(*this);
    if(commits.empty() || commits.size()>8192 || !commits.back())return {};
    const auto& committed=*commits.back();
    const auto admission=supplied_admission.data_;
    if(!admission || !admission->valid)return {};
    const auto initialization=supplied_initialization;const auto response=supplied_response;
    const auto connection=session.weak_from_this().lock();
    const auto phase=session.state();const auto battle=session.battle_generation();
    const auto account=session.account_id,character=session.character_id;
    const auto entry=admission->entry;
    const auto prior=[&]{const auto found=material_sources_.find(session.id());return found==material_sources_.end()?
        std::shared_ptr<WrittenMaterialSource::Data>{}:found->second;}();
    if(!prior && material_sources_.size()>=capacity_)return {};
    const auto original=admission->original;
    const auto latest=admission->latest;
    const auto selection=admission->selection;
    const auto material=admission->material;
    const auto local=[&] {
        const auto now=entries_.find(session.id());const auto source=material_sources_.find(session.id());
        const auto actual_admission=material_admissions_.find(session.id());const auto life=admission->life.lock();
        return life && life->owner==this && admission->valid && actual_admission!=material_admissions_.end() &&
            actual_admission->second==admission && admission->session.lock()==connection && admission->predecessor==predecessor &&
            admission->initialization.same_initialization(initialization) && admission->account==account &&
            admission->character==character && admission->battle==battle && admission->phase==phase &&
            live_ && !poisoned_ && connection.get()==&session && !session.closing() && session.recovered_world_ready() &&
            session.account_id==account && session.character_id==character && session.state()==phase && session.battle_generation()==battle &&
            (phase==SessionState::CharacterSelected || phase==SessionState::InWorld) && initialization.entry_written() &&
            session.normal_world_initialization_current_on_game(initialization) && response.status()==Session::WorldResponseWriteStatus::Written &&
            session.world_response_write_current_on_game(response) &&
            (prior?(source!=material_sources_.end() && source->second==prior):source==material_sources_.end()) &&
            (entry?(now!=entries_.end() && now->second==entry && ready(session,entry,true) &&
                entry->original_restoration==original && entry->latest_publication==latest && entry->selection_anchor==selection &&
                entry->material_anchor==material && entry->pending_publication==admission->pending &&
                entry->initialization.same_initialization(initialization)):
                now==entries_.end());
    };
    if(!joint || !predecessor || !canonical || !predecessor->owns_learning_repository(repository_) ||
       !canonical->owns_learning_repository(repository_) || !local())return {};
    if(entry) {
        if(entry->pending_publication && entry->pending_publication!=latest)return {};
        if(latest && (latest->phase.load()!=LearningPublication::Data::Phase::Bound || !latest->response ||
           latest->response->status()!=Session::WorldResponseWriteStatus::Written ||
           !session.world_response_write_current_on_game(*latest->response)))return {};
        const auto& before=(material||selection)?*original->learning_source():
            (latest?latest->after:*original->learning_source());
        if(!same_learning(before,*predecessor->learning_source()))return {};
    }
    auto qualified=repository_.material_successor_chain(*predecessor->learning_source(),*joint,commits);
    if(!qualified || !same_learning(*qualified,*canonical->learning_source()) ||
       !same_roster(predecessor->deity_roster(),canonical->deity_roster()) ||
       predecessor->batches()!=canonical->batches() || !local() ||
       (entry && !qualify_presence(session,entry,qualified->equipment())) || !local())return {};
    auto next=std::make_shared<WrittenMaterialSource::Data>(WrittenMaterialSource::Data{
        lifetime_,connection,initialization,response,canonical,joint,committed,account,character,battle,phase,true});
    if(!joint->committed_current(committed) || !local() ||
       !repository_.restoration_current(*canonical->learning_source()) || !local())return {};
    // All source construction/SQL happened before publication. Keep prior
    // learning chronology as history, but never revive its stale Current.
    material_sources_.insert_or_assign(session.id(),next);
    if(prior)prior->valid=false;
    if(entry) {
        entry->original_restoration=canonical;entry->material_anchor=next;
        entry->selection_anchor.reset();entry->pending_publication.reset();
    }
    admission->valid=false;material_admissions_.erase(session.id());
    return WrittenMaterialSource(std::move(next));
}
bool OwnedSkillBookLearningService::publication_local(Session& session,const std::shared_ptr<Entry>& entry,
        const std::shared_ptr<LearningPublication::Data>& data)const {
    if(!data||data->thread!=std::this_thread::get_id()||!ready(session,entry,true)||
       data->phase.load()!=LearningPublication::Data::Phase::Bound||!data->committed||!data->response)return false;
    const auto life=data->life.lock();
    return life&&life->owner==this&&data->entry.lock()==entry&&data->session.lock().get()==&session&&
        entry->latest_publication==data&&data->original_restoration==entry->original_restoration&&
        data->initialization.same_initialization(entry->initialization)&&
        data->response->wire()==data->wire&&data->response->status()==Session::WorldResponseWriteStatus::Written&&
        session.world_response_write_current_on_game(*data->response);
}
bool OwnedSkillBookLearningService::publication_current(Session& session,const std::shared_ptr<LearningPublication::Data>& data) {
    if(!data||data->thread!=std::this_thread::get_id())return false;
    const auto entry=data->entry.lock();
    if(!publication_local(session,entry,data))return false;
    if(!qualify_presence(session,entry,data->after.equipment())||!publication_local(session,entry,data))return false;
    const bool stored=repository_.restoration_current(data->after);
    return stored&&publication_local(session,entry,data);
}
bool OwnedSkillBookLearningService::learning_publication_current(Session& session,const LearningPublication& publication) {
    Operation operation(*this,true);return publication_current(session,publication.data_);
}
std::optional<OwnedSkillBookLearningService::LearningPublication> OwnedSkillBookLearningService::latest_learning_publication(Session& session) {
    Operation operation(*this,true);
    const auto at=entries_.find(session.id());const auto entry=at==entries_.end()?std::shared_ptr<Entry>{}:at->second;
    const auto data=entry?entry->latest_publication:std::shared_ptr<LearningPublication::Data>{};
    if(!publication_current(session,data))return std::nullopt;
    return LearningPublication(data);
}
std::optional<OwnedSkillBookLearningService::WrittenLearningSource>
OwnedSkillBookLearningService::written_learning_source(Session& session,const LearningPublication& supplied) {
    owner();const auto publication=supplied;const auto data=publication.data_;
    if(!data || data->thread!=std::this_thread::get_id())return std::nullopt;
    const auto peer=data->session.lock();if(peer.get()!=&session)return std::nullopt;
    const auto life=data->life.lock();if(!life || life->owner!=this)return std::nullopt;
    Operation operation(*this,true);
    if(!publication_current(session,data) || !data->committed ||
       !repository_.committed_matches_plan(*data->committed,data->plan) ||
       !repository_.committed_matches_restoration_before(*data->committed,data->before))return std::nullopt;
    const auto response=*data->response; // Copy only the actual same private Written receipt.
    WrittenLearningSource source(publication,response); // No allocation/controlblock/SQL.
    if(!publication_local(session,data->entry.lock(),data) ||
       source.response().status()!=Session::WorldResponseWriteStatus::Written ||
       source.response().wire()!=data->wire || !session.world_response_write_current_on_game(source.response()))return std::nullopt;
    return source;
}
bool OwnedSkillBookLearningService::written_learning_source_current(Session& session,const WrittenLearningSource& supplied) {
    owner();const auto source=supplied;const auto data=source.publication_.data_;
    if(!data || data->thread!=std::this_thread::get_id())return false;
    const auto peer=data->session.lock();if(peer.get()!=&session)return false;
    const auto life=data->life.lock();if(!life || life->owner!=this)return false;
    Operation operation(*this,true);
    if(!publication_current(session,data) || !data->committed ||
       !repository_.committed_matches_plan(*data->committed,data->plan) ||
       !repository_.committed_matches_restoration_before(*data->committed,data->before))return false;
    return publication_local(session,data->entry.lock(),data) &&
        source.response().status()==Session::WorldResponseWriteStatus::Written && source.response().wire()==data->wire &&
        session.world_response_write_current_on_game(source.response());
}
void OwnedSkillBookLearningService::bind_learning_response(Session& session,const LearningPublication& publication,
        const Session::WorldResponseWrite& response) {
    Operation operation(*this,true);const auto data=publication.data_;
    const auto entry=data?data->entry.lock():std::shared_ptr<Entry>{};
    // Refuse foreign/stale issuers BEFORE any phase/revoke/Entry mutation.
    const auto issuer=data?data->life.lock():std::shared_ptr<Lifetime>{};
    const auto actual=entries_.find(session.id());
    if(!data||data->thread!=std::this_thread::get_id()||!issuer||issuer->owner!=this||data->session.lock().get()!=&session||!entry||
       actual==entries_.end()||actual->second!=entry||entry->session.lock().get()!=&session)
        throw std::logic_error("Skill book binding requires its own exact issuer, Entry and Session");
    const auto local=[&] {
        const auto life=data->life.lock();
        return life&&life->owner==this&&ready(session,entry,true)&&entry->pending_publication==data&&
            entry->latest_publication==data->previous.lock()&&data->original_restoration==entry->original_restoration&&
            data->initialization.same_initialization(entry->initialization)&&data->committed&&
            repository_.committed_matches_plan(*data->committed,data->plan)&&
            response.status()==Session::WorldResponseWriteStatus::Pending&&response.wire()==data->wire&&
            session.world_response_write_current(response);
    };
    if(data->phase.load()!=LearningPublication::Data::Phase::Committed||data->response||!local()) {
        revoke_publication(data,true);throw std::logic_error("Skill book original learning response custody changed");
    }
    data->response.emplace(response); // Shared receipt owner only, no allocation/query/second capture.
    auto expected=LearningPublication::Data::Phase::Committed;
    if(!local()||!data->phase.compare_exchange_strong(expected,LearningPublication::Data::Phase::Bound)) {
        revoke_publication(data,true);throw std::logic_error("Skill book response handoff lost its exact publication");
    }
    if(const auto material=material_sources_.find(session.id());material!=material_sources_.end() &&
       material->second->session.lock().get()==&session)material->second->valid=false;
    if(entry->material_anchor)entry->material_anchor->valid=false;
    entry->material_anchor.reset();
    entry->latest_publication=data;entry->selection_anchor.reset();active_publication_.reset();
    if(!ready(session,entry,true)||entry->pending_publication!=data||entry->latest_publication!=data||
       data->phase.load()!=LearningPublication::Data::Phase::Bound||
       !session.world_response_write_current(response)||response.status()!=Session::WorldResponseWriteStatus::Pending) {
        revoke_publication(data,true);throw std::logic_error("Skill book bound response source retired");
    }
}
std::optional<std::vector<std::uint8_t>> OwnedSkillBookLearningService::use(Session& session,
        const RecoveredInventoryItemRequest::Request& request,const std::shared_ptr<SharedWorldPresence>& presence) {
    auto result=use_request(session,UseRequest{request},presence,false);
    if(!result)return std::nullopt;return std::move(*result).take_wire();
}
std::optional<std::vector<std::uint8_t>> OwnedSkillBookLearningService::use(Session& session,
        const RecoveredTargetItemRequest::Request& request,const std::shared_ptr<SharedWorldPresence>& presence) {
    auto result=use_request(session,UseRequest{request},presence,false);
    if(!result)return std::nullopt;return std::move(*result).take_wire();
}
std::optional<OwnedSkillBookLearningService::UseResult> OwnedSkillBookLearningService::use_with_source(Session& session,
        const RecoveredInventoryItemRequest::Request& request,const std::shared_ptr<SharedWorldPresence>& presence) {
    return use_request(session,UseRequest{request},presence,true);
}
std::optional<OwnedSkillBookLearningService::UseResult> OwnedSkillBookLearningService::use_with_source(Session& session,
        const RecoveredTargetItemRequest::Request& request,const std::shared_ptr<SharedWorldPresence>& presence) {
    return use_request(session,UseRequest{request},presence,true);
}
std::optional<OwnedSkillBookLearningService::UseResult> OwnedSkillBookLearningService::use_request(Session& session,
        UseRequest owned_request,const std::shared_ptr<SharedWorldPresence>& presence,bool with_source) {
    const auto common=presence; // Own both native variants before any observer.
    Operation operation(*this);
    const auto found=entries_.find(session.id());
    const auto entry=found==entries_.end()?std::shared_ptr<Entry>{}:found->second;
    if(entry&&entry->pending_publication) {
        const auto pending=entry->pending_publication;
        if(pending->phase.load()!=LearningPublication::Data::Phase::Bound||!pending->response||
           pending->response->status()==Session::WorldResponseWriteStatus::Failed) {
            revoke_publication(pending,true);throw std::logic_error("Skill book prior publication failed or remained unbound");
        }
        if(pending->response->status()!=Session::WorldResponseWriteStatus::Written)return std::nullopt;
        if(!publication_current(session,pending))return std::nullopt;
        if(entry->pending_publication==pending)entry->pending_publication.reset();
    }
    const auto previous=entry?entry->latest_publication:std::shared_ptr<LearningPublication::Data>{};
    const auto selection=entry?entry->selection_anchor:std::shared_ptr<const Entry::SelectionAnchor>{};
    const auto material_anchor=entry?entry->material_anchor:std::shared_ptr<WrittenMaterialSource::Data>{};
    if(selection&&(!selection->current(session)||!ready(session,entry,true)))return std::nullopt;
    std::shared_ptr<LearningPublication::Data> data;
    const auto slot=std::visit([](const auto& request){return request.raw_slot;},owned_request);
    const auto item_id=std::visit([](const auto& request){return request.client_item_id;},owned_request);
    const auto request_current=[&] {
        // PURE throughout repository.commit: no before/after-source query here.
        if(!ready(session,entry,true)||entry->presence!=common||entry->selection_anchor!=selection||entry->material_anchor!=material_anchor||
           (with_source&&entry->latest_publication!=previous))return false;
        if(data&&(entry->pending_publication!=data||
           (data->phase.load()!=LearningPublication::Data::Phase::Prepared&&
            data->phase.load()!=LearningPublication::Data::Phase::Committed)))return false;
        const auto* targeted=std::get_if<RecoveredTargetItemRequest::Request>(&owned_request);
        // Original shortcut copies actor WORD unchanged. Never mask incoming
        // targets, truncate DB identity, or use raw_tail as quantity/nonce.
        return !targeted||targeted->raw_target==entry->actor;
    };
    if(slot>=30||!request_current())return std::nullopt;
    try {
        const auto observed=repository_.observe(entry->account,entry->character,slot,item_id);
        if(!observed||!request_current()||!qualify_presence(session,entry,observed->equipment())||
           !repository_.current(*observed)||!request_current())return std::nullopt;
        const auto* item=item_at(observed->inventory(),slot);
        if(!item||item->quantity>99)return std::nullopt;
        const auto policy=lua_.skill_book_learning({static_cast<std::uint32_t>(item->quantity),
            static_cast<std::uint32_t>(observed->deity().snapshot.skills.size()),observed->already_learned(),
            RecoveredDeityState::has_current_skill_icon(observed->book().kind,observed->book().definition_id)});
        if(!request_current()||!repository_.current(*observed)||!request_current())return std::nullopt;
        if(!policy.allowed)return std::nullopt;
        if(policy.duplicate)return UseResult({},std::nullopt); // No debit/event/publication/receipt.
        if(policy.consume!=1)return std::nullopt;
        std::optional<SqliteSkillBookLearningRepository::Restoration> before_source;
        if(with_source) {
            if(material_anchor){
                if(!material_anchor->valid || !entry->original_restoration->learning_source())return std::nullopt;
                before_source.emplace(*entry->original_restoration->learning_source());
                if(!repository_.restoration_current(*before_source)||!request_current())return std::nullopt;
            }else if(selection){
                if(!entry->original_restoration->learning_source()||!selection->current(session)||!request_current())return std::nullopt;
                before_source.emplace(*entry->original_restoration->learning_source());
                if(!repository_.restoration_current(*before_source)||!request_current())return std::nullopt;
            }else if(previous) {
                if(!publication_current(session,previous)||!request_current())return std::nullopt;
                before_source.emplace(previous->after);
            }else {
                if(!entry->original_restoration->learning_source())return std::nullopt;
                before_source.emplace(*entry->original_restoration->learning_source());
                if(!repository_.restoration_current(*before_source)||!request_current())return std::nullopt;
            }
        }
        const auto plan=repository_.plan(*observed);
        if(!plan||!request_current()||!qualify_presence(session,entry,observed->equipment())||
           !repository_.current(*observed)||!request_current())return std::nullopt;
        if(with_source&&!repository_.plan_matches_restoration(*plan,*before_source))return std::nullopt;
        std::vector<std::uint8_t> logical;
        const auto& skill=plan->skill().encode();logical.insert(logical.end(),skill.begin(),skill.end());
        const auto& issued=plan->activation();
        const auto activation=RecoveredDeityActivation::encode(issued.subject,issued.kind,issued.definition_id);
        logical.insert(logical.end(),activation.begin(),activation.end());
        const auto inventory=RecoveredInventory::encode_slot_update(plan->slot_update());
        if(!inventory)return std::nullopt;
        logical.insert(logical.end(),inventory->begin(),inventory->end());
        auto wire=RecoveredWorldFrame::encode(logical); // Entire native-format response PRECOMMIT.
        if(!with_source) {
            const auto committed=repository_.commit(*plan,request_current);
            if(!committed)return std::nullopt;
            entry->latest_commit.emplace(*committed);
            if(!request_current())throw std::logic_error("Skill book durable prefix committed after source retirement");
            return UseResult(std::move(wire),std::nullopt); // Raw legacy mode creates no typed pending state.
        }
        const auto planned=repository_.planned_after_source(*plan);
        if(!planned||!request_current())return std::nullopt;
        if(logical.size()!=13)return std::nullopt;
        std::array<std::uint8_t,13> delta;std::copy(logical.begin(),logical.end(),delta.begin());
        data=std::make_shared<LearningPublication::Data>(lifetime_,entry,*plan,*before_source,*planned,delta,wire,previous);
        UseResult result(std::move(wire),LearningPublication(data)); // ALL carrier/wire allocations BEFORE COMMIT.
        entry->pending_publication=data;active_publication_=data; // Existing Entry slot, no map allocation.
        if(!request_current())return std::nullopt;
        const auto committed=repository_.commit(*plan,request_current);
        if(!committed)return std::nullopt;
        data->committed.emplace(*committed); // Mark actual durable prefix BEFORE any fallible rejection.
        auto prepared=LearningPublication::Data::Phase::Prepared;
        if(!data->phase.compare_exchange_strong(prepared,LearningPublication::Data::Phase::Committed)) {
            revoke_publication(data,true);throw std::logic_error("Skill book result abandoned during its durable commit");
        }
        const auto after=repository_.committed_after_source(*committed);
        if(!after||!repository_.committed_matches_plan(*committed,data->plan)||!request_current()) {
            revoke_publication(data,true);throw std::logic_error("Skill book committed publication identity changed");
        }
        entry->latest_commit.emplace(*committed);
        return std::optional<UseResult>(std::move(result)); // No after-COMMIT query/copy/allocation.
    }catch(...) {retire(session,entry);throw;}
}
void OwnedSkillBookLearningService::release(Session& session) {
    owner();if(busy_)poisoned_=true;
    if(const auto epoch=material_epochs_.find(session.id());epoch!=material_epochs_.end() && epoch->second->session.lock().get()==&session)
        epoch->second->retired=true;
    if(const auto admission=material_admissions_.find(session.id());admission!=material_admissions_.end() && admission->second->session.lock().get()==&session) {
        admission->second->valid=false;material_admissions_.erase(admission);
    }
    if(const auto source=material_sources_.find(session.id());source!=material_sources_.end() && source->second->session.lock().get()==&session) {
        source->second->valid=false;material_sources_.erase(source);
    }
    const auto found=entries_.find(session.id());
    if(found!=entries_.end()&&found->second->session.lock().get()==&session) {
        const auto entry=found->second;retire(session,entry);
    }
}
void OwnedSkillBookLearningService::stop() {
    owner();if(busy_)poisoned_=true;live_=false;
    lifetime_->owner=nullptr; // Tombstone before borrowed dependencies/Entry teardown.
    for(const auto& [id,epoch]:material_epochs_)epoch->retired=true;
    material_epochs_.clear();
    for(const auto& [id,admission]:material_admissions_)admission->valid=false;
    material_admissions_.clear();
    for(const auto& [id,source]:material_sources_)source->valid=false;
    material_sources_.clear();
    for(const auto& [id,entry]:entries_) {
        entry->revoked=true;
        const auto pending=entry->pending_publication,latest=entry->latest_publication;
        revoke_publication(pending,true);if(latest!=pending)revoke_publication(latest,true);
    }
    active_publication_.reset();entries_.clear();
}
}
