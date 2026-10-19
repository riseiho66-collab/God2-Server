#include "game/SharedWorldPresence.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include <algorithm>
#include <exception>
#include <limits>
#include <set>
#include <stdexcept>

namespace god2 {
namespace {
bool same_character_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
}
SharedWorldPresence::SharedWorldPresence(RecoveredCharacterRepository& characters)
    :SharedWorldPresence(characters,std::make_shared<SharedChannelCharacterOwnership>(characters),0) {}
SharedWorldPresence::SharedWorldPresence(RecoveredCharacterRepository& characters,
        std::shared_ptr<SharedChannelCharacterOwnership> ownership,std::uint8_t channel)
    :characters_(characters),ownership_(std::move(ownership)),world_identity_([&]{
        if(!ownership_||!ownership_->owns_repository(characters))
            throw std::invalid_argument("Channel presence requires the same repository and game owner");
        return ownership_->register_world(channel);
    }()) {}
SharedWorldPresence::~SharedWorldPresence() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    ownership_->unregister_world(world_identity_);
}
void SharedWorldPresence::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Shared presence game owner mismatch");
}
bool SharedWorldPresence::character_reserved(std::uint64_t character) const {
    owner();return ownership_->character_reserved(character);
}
bool SharedWorldPresence::owned(const Lease& lease) const {
    const auto rows=characters_.list_for_account(lease.account);
    if(!std::any_of(rows.begin(),rows.end(),[&](const auto& row) {
        return row.id==lease.character && row.account_id==lease.account;
    }))return false;
    return true;
}
bool SharedWorldPresence::stored(const Lease& lease) const {
    if(!owned(lease))return false;
    const auto saved=characters_.load_position(lease.account,lease.character);
    return saved && *saved==lease.position;
}
std::optional<SharedWorldPresence::Lease> SharedWorldPresence::prepare(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    std::uint16_t handle,const RecoveredPosition& position) {
    owner();
    if(snapshot_busy_)snapshot_reentered_=true;
    if(preparing_){preparation_reentered_=true;return std::nullopt;}
    preparing_=true;preparation_reentered_=false;
    struct EndPreparation {bool& preparing;~EndPreparation(){preparing=false;}} end{preparing_};
    if(!session || !account || !character || handle>0x3fff || sessions_.contains(session))return std::nullopt;
    // Handles are world-local. Cross-channel character/connection exclusion
    // is CUSTOM-0159 and is held before any virtual repository observation.
    for(const auto& [id,entry]:sessions_)
        if(entry.lease.character==character || entry.lease.actor_handle==handle)return std::nullopt;
    if(generation_==std::numeric_limits<std::uint64_t>::max())
        throw std::overflow_error("Shared presence generation exhausted");
    Lease lease{session,account,character,generation_+1,handle,position};
    const auto claim=ownership_->reserve(world_identity_,session,account,character);
    if(!claim)return std::nullopt;
    struct Rollback {
        SharedChannelCharacterOwnership& owner;
        const SharedChannelCharacterOwnership::Claim& claim;
        bool keep=false;
        ~Rollback(){if(!keep)owner.release(claim);}
    } rollback{*ownership_,claim};
    if(!stored(lease))return std::nullopt;
    // Allocate a detached node, not in the live registry. Final insertion
    // transfers that node with the same std::allocator and does not allocate.
    std::map<std::uint64_t,Entry> staged;
    staged.emplace(session,Entry{lease,false,claim});
    if(preparation_reentered_||generation_!=lease.generation-1||
       !ownership_->current(claim)||sessions_.contains(session))return std::nullopt;
    // No borrowed map iterator crosses the repository. A caught nested
    // mutation cannot install a second handle or silently replace this claim.
    for(const auto& [id,entry]:sessions_)
        if(entry.lease.character==character||entry.lease.actor_handle==handle)return std::nullopt;
    if(!sessions_.insert(staged.extract(session)).inserted)return std::nullopt;
    ++generation_;rollback.keep=true;
    return lease;
}
bool SharedWorldPresence::retained_current(const Lease& lease) const {
    const auto found=sessions_.find(lease.session);
    return found!=sessions_.end()&&found->second.lease==lease&&ownership_->current(found->second.ownership);
}
bool SharedWorldPresence::retained_claims_current(const std::map<std::uint64_t,Entry>& registry) const {
    for(const auto& [session,entry]:registry)
        if(session!=entry.lease.session||!ownership_->current(entry.ownership))return false;
    return true;
}
bool SharedWorldPresence::current(const Lease& lease) const {
    owner();const auto held=lease;
    return retained_current(held)&&owned(held)&&retained_current(held);
}
std::optional<SharedWorldPresence::Lease> SharedWorldPresence::prepare_geometry(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,std::uint16_t handle,
    std::uint16_t area,std::uint16_t scene,std::uint16_t x,std::uint16_t y) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    if(!session || !account || !character || handle>0x3fff)return std::nullopt;
    const auto saved=characters_.load_position(account,character);
    if(!saved || saved->area!=area || saved->scene!=scene || saved->x!=x || saved->y!=y)return std::nullopt;
    return prepare(session,account,character,handle,*saved);
}
bool SharedWorldPresence::preparation_current(const Lease& lease) const {
    owner();const auto held=lease;return current(held)&&stored(held)&&retained_current(held);
}
bool SharedWorldPresence::retained_preparation_current(const Lease& lease) const {
    owner();const auto found=sessions_.find(lease.session);
    return found!=sessions_.end() && !found->second.active && found->second.lease==lease&&
        ownership_->current(found->second.ownership);
}
bool SharedWorldPresence::activate(const Lease& lease,std::uint16_t handle) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    if(preparing_)preparation_reentered_=true;
    const auto held=lease;
    if(handle!=held.actor_handle||!retained_preparation_current(held)||!preparation_current(held))return false;
    const auto found=sessions_.find(held.session);
    if(found==sessions_.end()||found->second.active||found->second.lease!=held||
       !ownership_->current(found->second.ownership))return false;
    found->second.active=true;return true;
}
bool SharedWorldPresence::activate_qualified_scene(const Lease& input,std::uint16_t handle) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    if(preparing_)preparation_reentered_=true;
    const auto lease=input;
    if(!qualified_taiwan_scene_handle(handle) || handle!=lease.actor_handle ||
       !retained_preparation_current(lease) || !preparation_current(lease))return false;
    // No iterator or borrowed lease crosses the virtual repository reads.
    const auto found=sessions_.find(lease.session);
    if(found==sessions_.end() || found->second.active || found->second.lease!=lease||
       !ownership_->current(found->second.ownership))return false;
    found->second.active=true;return true;
}
bool SharedWorldPresence::ready(const Lease& lease) const {
    owner();const auto held=lease;
    return retained_ready_current(held)&&current(held)&&retained_ready_current(held);
}
bool SharedWorldPresence::retained_ready_current(const Lease& lease) const {
    owner();const auto found=sessions_.find(lease.session);
    return found!=sessions_.end() && found->second.active && found->second.lease==lease&&
        ownership_->current(found->second.ownership);
}
std::optional<SharedWorldPresence::Lease> SharedWorldPresence::ready_lease(
    std::uint64_t session,std::uint64_t account,std::uint64_t character) const {
    owner();if(!session || !account || !character)return std::nullopt;
    const auto found=sessions_.find(session);
    if(found==sessions_.end() || !found->second.active ||
       found->second.lease.account!=account || found->second.lease.character!=character)return std::nullopt;
    const auto lease=found->second.lease;
    if(!ready(lease))return std::nullopt;
    return lease;
}
struct SharedWorldPresence::ReadyPopulation::Data {
    const std::shared_ptr<const PopulationIdentity> identity;
    const std::map<std::uint64_t,Entry> registry;
    const std::uint64_t generation;
    const std::vector<ReadyCharacter> characters;
    Data(std::shared_ptr<const PopulationIdentity> owner,std::map<std::uint64_t,Entry> entries,
            std::uint64_t epoch,std::vector<ReadyCharacter> rows)
        :identity(std::move(owner)),registry(std::move(entries)),generation(epoch),characters(std::move(rows)) {}
};
std::span<const SharedWorldPresence::ReadyCharacter> SharedWorldPresence::ReadyPopulation::characters() const noexcept {
    return data_?std::span<const ReadyCharacter>{data_->characters}:std::span<const ReadyCharacter>{};
}
bool SharedWorldPresence::retained_population_current(const ReadyPopulation& population) const {
    owner();
    if(snapshot_busy_){snapshot_reentered_=true;return false;}
    const auto data=population.data_;
    return data && data->identity==population_identity_ && data->generation==generation_ &&
        data->registry==sessions_&&retained_claims_current(sessions_);
}
std::optional<std::vector<SharedWorldPresence::ReadyCharacter>> SharedWorldPresence::ready_characters() const {
    const auto observed=observe_ready_population();
    if(!observed)return std::nullopt;
    const auto rows=observed->characters();return std::vector<ReadyCharacter>(rows.begin(),rows.end());
}
std::optional<SharedWorldPresence::ReadyPopulation> SharedWorldPresence::observe_ready_population() const {
    owner();
    if(snapshot_busy_){snapshot_reentered_=true;return std::nullopt;}
    snapshot_busy_=true;snapshot_reentered_=false;
    struct EndSnapshot {bool& busy;~EndSnapshot(){busy=false;}} end{snapshot_busy_};
    // Never keep a map iterator/reference across virtual repository observers.
    // Pending entries qualify the registry epoch but are not chat participants.
    const auto registry=sessions_;
    const auto generation=generation_;
    const auto unchanged=[&] {return !snapshot_reentered_ && generation_==generation && sessions_==registry&&retained_claims_current(registry);};
    const auto read_population=[&]() -> std::optional<std::vector<ReadyCharacter>> {
        std::vector<ReadyCharacter> result;result.reserve(registry.size());
        for(const auto& [session,entry]:registry) {
            if(!entry.active)continue;
            const auto& lease=entry.lease;
            if(!lease.session || session!=lease.session || !lease.account || !lease.character || !lease.generation)
                return std::nullopt;
            if(!unchanged())return std::nullopt;
            const auto roots=characters_.list_for_account(lease.account);
            if(!unchanged())return std::nullopt;
            std::optional<RecoveredCharacter> root;std::set<std::uint64_t> ids;
            for(const auto& candidate:roots) {
                if(!candidate.id || candidate.account_id!=lease.account || !ids.insert(candidate.id).second)
                    return std::nullopt;
                if(candidate.id==lease.character)root=candidate;
            }
            if(!root)return std::nullopt;
            const auto position=characters_.load_position(lease.account,lease.character);
            if(!position || !unchanged())return std::nullopt;
            result.push_back({lease,*root,*position});
        }
        return unchanged()?std::optional{std::move(result)}:std::nullopt;
    };
    auto first=read_population();if(!first)return std::nullopt;
    const auto second=read_population();
    if(!second || first->size()!=second->size() || !unchanged())return std::nullopt;
    for(std::size_t i=0;i<first->size();++i) {
        const auto& a=(*first)[i];const auto& b=(*second)[i];
        if(a.lease!=b.lease || a.position!=b.position || !same_character_root(a.character,b.character))return std::nullopt;
    }
    auto data=std::make_shared<const ReadyPopulation::Data>(population_identity_,registry,generation,std::move(*first));
    if(!unchanged())return std::nullopt;
    return ReadyPopulation(std::move(data));
}
struct SharedWorldPresence::InitialPopulation::Data {
    enum class Phase {Prepared,Activated,Revoked};
    const std::shared_ptr<const PopulationIdentity> identity;
    const std::map<std::uint64_t,Entry> before,successor;
    const std::uint64_t generation;
    const std::vector<ReadyCharacter> characters;
    const std::size_t joining_index;
    mutable Phase phase=Phase::Prepared; // Serial game owner; no IO admission.
    Data(std::shared_ptr<const PopulationIdentity> owner,std::map<std::uint64_t,Entry> original,
        std::map<std::uint64_t,Entry> activated,std::uint64_t epoch,
        std::vector<ReadyCharacter> rows,std::size_t joining)
        :identity(std::move(owner)),before(std::move(original)),successor(std::move(activated)),
         generation(epoch),characters(std::move(rows)),joining_index(joining){}
};
std::span<const SharedWorldPresence::ReadyCharacter> SharedWorldPresence::InitialPopulation::characters() const noexcept {
    return data_->characters;
}
const SharedWorldPresence::ReadyCharacter& SharedWorldPresence::InitialPopulation::joining() const noexcept {
    return data_->characters[data_->joining_index];
}
bool SharedWorldPresence::InitialPopulation::activated() const noexcept {
    return data_->phase==Data::Phase::Activated;
}
bool SharedWorldPresence::retained_initial_population_current(const InitialPopulation& population) const {
    owner();
    if(snapshot_busy_){snapshot_reentered_=true;return false;}
    const auto data=population.data_;
    if(!data||data->identity!=population_identity_||data->generation!=generation_||
       data->phase==InitialPopulation::Data::Phase::Revoked)return false;
    return sessions_==(data->phase==InitialPopulation::Data::Phase::Prepared?data->before:data->successor)&&
        retained_claims_current(sessions_);
}
std::optional<SharedWorldPresence::InitialPopulation> SharedWorldPresence::observe_initial_population(const Lease& input) const {
    owner();
    if(snapshot_busy_){snapshot_reentered_=true;return std::nullopt;}
    const auto joining=input; // No borrowed input crosses repository observers.
    snapshot_busy_=true;snapshot_reentered_=false;
    struct EndSnapshot {bool& busy;~EndSnapshot(){busy=false;}} end{snapshot_busy_};
    auto registry=sessions_;const auto generation=generation_;
    const auto unchanged=[&]{return !snapshot_reentered_&&generation_==generation&&sessions_==registry&&retained_claims_current(registry);};
    const auto joined=registry.find(joining.session);
    if(joined==registry.end()||joined->second.active||joined->second.lease!=joining||!unchanged())return std::nullopt;
    const auto read_population=[&]() -> std::optional<std::vector<ReadyCharacter>> {
        std::vector<ReadyCharacter> result;result.reserve(registry.size());
        for(const auto& [session,entry]:registry){
            if(!entry.active&&entry.lease!=joining)continue;
            const auto lease=entry.lease;
            if(!lease.session||session!=lease.session||!lease.account||!lease.character||!lease.generation||
               !unchanged())return std::nullopt;
            const auto roots=characters_.list_for_account(lease.account);
            if(!unchanged())return std::nullopt;
            std::optional<RecoveredCharacter> root;std::set<std::uint64_t> ids;
            for(const auto& candidate:roots){
                if(!candidate.id||candidate.account_id!=lease.account||!ids.insert(candidate.id).second)return std::nullopt;
                if(candidate.id==lease.character)root=candidate;
            }
            if(!root)return std::nullopt;
            const auto position=characters_.load_position(lease.account,lease.character);
            if(!position||!unchanged()||(lease==joining&&*position!=joining.position))return std::nullopt;
            result.push_back({lease,*root,*position});
        }
        return unchanged()?std::optional{std::move(result)}:std::nullopt;
    };
    auto first=read_population();if(!first)return std::nullopt;
    const auto second=read_population();
    if(!second||first->size()!=second->size()||!unchanged())return std::nullopt;
    std::optional<std::size_t> joining_index;
    for(std::size_t i=0;i<first->size();++i){
        const auto& a=(*first)[i];const auto& b=(*second)[i];
        if(a.lease!=b.lease||a.position!=b.position||!same_character_root(a.character,b.character))return std::nullopt;
        if(a.lease==joining){if(joining_index)return std::nullopt;joining_index=i;}
    }
    if(!joining_index)return std::nullopt;
    // Allocate the sole exact successor and all owning values before final
    // qualification. Only this joining entry's active flag may differ.
    auto successor=registry;successor.at(joining.session).active=true;
    if(!unchanged())return std::nullopt;
    auto data=std::make_shared<const InitialPopulation::Data>(population_identity_,registry,
        std::move(successor),generation,std::move(*first),*joining_index);
    // Re-read the entire ready-plus-joining set after owning Data allocation;
    // allocator callbacks cannot silently change a retained root/pose version.
    const auto matches=[&](const std::optional<std::vector<ReadyCharacter>>& rows){
        if(!rows||rows->size()!=data->characters.size())return false;
        for(std::size_t i=0;i<rows->size();++i){
            const auto& a=(*rows)[i];const auto& b=data->characters[i];
            if(a.lease!=b.lease||a.position!=b.position||!same_character_root(a.character,b.character))return false;
        }
        return true;
    };
    const auto final_first=read_population();if(!matches(final_first))return std::nullopt;
    const auto final_second=read_population();if(!matches(final_second))return std::nullopt;
    if(snapshot_reentered_||generation_!=data->generation||sessions_!=data->before||!retained_claims_current(sessions_)||
       data->phase!=InitialPopulation::Data::Phase::Prepared)return std::nullopt;
    return InitialPopulation(std::move(data));
}
bool SharedWorldPresence::activate_initial_population(const InitialPopulation& population,
        std::uint16_t handle,TaiwanWorldEntryIdentity identity) {
    owner();
    if(preparing_){preparation_reentered_=true;return false;}
    if(snapshot_busy_){snapshot_reentered_=true;return false;}
    const auto data=population.data_;
    if(!data||data->identity!=population_identity_||data->phase!=InitialPopulation::Data::Phase::Prepared||
       !valid_taiwan_world_entry_identity(identity))return false;
    const auto lease=data->characters[data->joining_index].lease;
    if(handle!=lease.actor_handle||
       (identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle&&!qualified_taiwan_scene_handle(handle))||
       data->generation!=generation_||sessions_!=data->before||!retained_claims_current(sessions_))return false;
    snapshot_busy_=true;snapshot_reentered_=false;
    struct EndSnapshot {bool& busy;~EndSnapshot(){busy=false;}} end{snapshot_busy_};
    // Qualification may call the repository. Do not keep a live map iterator
    // across it; nested snapshot/mutation attempts reject this whole activation.
    if(!preparation_current(lease)||snapshot_reentered_||data->identity!=population_identity_||
       data->phase!=InitialPopulation::Data::Phase::Prepared||data->generation!=generation_||
       sessions_!=data->before||!retained_claims_current(sessions_))return false;
    const auto found=sessions_.find(lease.session);
    if(found==sessions_.end()||found->second.active||found->second.lease!=lease||
       !ownership_->current(found->second.ownership))return false;
    // No allocation, observer, DB operation or failure cut follows the actual
    // map flag write. This private token's one-shot successor is now legitimate.
    found->second.active=true;data->phase=InitialPopulation::Data::Phase::Activated;return true;
}
void SharedWorldPresence::retire_initial_population(const InitialPopulation& population) noexcept {
    if(thread_!=std::this_thread::get_id())std::terminate();
    const auto data=population.data_;
    if(data&&data->identity==population_identity_)data->phase=InitialPopulation::Data::Phase::Revoked;
}
bool SharedWorldPresence::release(const Lease& lease) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    if(preparing_)preparation_reentered_=true;
    const auto found=sessions_.find(lease.session);
    if(found==sessions_.end() || found->second.lease!=lease)return false;
    if(!ownership_->release(found->second.ownership))return false;
    sessions_.erase(found);return true;
}
std::optional<RecoveredPosition> SharedWorldPresence::saved_position(const Lease& lease) const {
    owner();const auto held=lease;if(!ready(held))return std::nullopt;
    const auto position=characters_.load_position(held.account,held.character);
    return retained_ready_current(held)?position:std::nullopt;
}
std::optional<RecoveredPosition> SharedWorldPresence::commit_owned_step(const Lease& lease,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    if(preparing_)preparation_reentered_=true;
    const auto held=lease;const auto wanted=expected;
    const auto current=saved_position(held);
    if(!current || *current!=wanted||!retained_ready_current(held))return std::nullopt;
    // Existing common SQLite transaction rechecks ownership and the exact
    // expected position/revision. Same-map step only; no client map identity.
    return characters_.commit_position(held.account,held.character,wanted,
        wanted.area,wanted.scene,x,y);
}
}
