#include "game/OwnedTaiwanOrdinaryMovementAuthority.h"
#include <algorithm>
#include <exception>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
bool same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
}
struct OwnedTaiwanOrdinaryMovementAuthority::Operation {
    OwnedTaiwanOrdinaryMovementAuthority& authority;
    explicit Operation(OwnedTaiwanOrdinaryMovementAuthority& value):authority(value) {
        authority.owner();
        if(authority.busy_) {
            authority.failed_=true;authority.pending_.reset();
            throw std::logic_error("TW owned ordinary authority reentry rejected");
        }
        authority.busy_=true;
    }
    ~Operation(){authority.busy_=false;}
};
struct OwnedTaiwanOrdinaryMovementAuthority::Ticket {
    const Scene::Candidate candidate;
    const SharedWorldPresence::ReadyPopulation population;
    const std::vector<SharedWorldPresence::ReadyCharacter> rows;
    const RecoveredPosition after;
    const std::uint64_t credit_us;
    const Clock::time_point clock;
    const TaiwanMovementRules::OrdinaryPolicy effective_policy;
    const std::optional<OwnedOrdinaryMovementPolicies::Observation> observation;
    Ticket(Scene::Candidate input,SharedWorldPresence::ReadyPopulation witness,
        std::vector<SharedWorldPresence::ReadyCharacter> actual,RecoveredPosition next,
        std::uint64_t credit,Clock::time_point sampled,TaiwanMovementRules::OrdinaryPolicy policy,
        std::optional<OwnedOrdinaryMovementPolicies::Observation> observed)
        :candidate(std::move(input)),population(std::move(witness)),rows(std::move(actual)),
         after(next),credit_us(credit),clock(sampled),effective_policy(policy),observation(std::move(observed)) {}
};
OwnedTaiwanOrdinaryMovementAuthority::OwnedTaiwanOrdinaryMovementAuthority(
    const std::shared_ptr<Session>& session,std::shared_ptr<SharedWorldPresence> presence,
    const Lease& lease,Scene::Resources resources,RecoveredPosition position,std::uint8_t direction,
    std::shared_ptr<TaiwanMovementRules> rules,TaiwanMovementRules::OrdinaryPolicy policy,
    std::shared_ptr<OwnedOrdinaryMovementPolicies::Binding> binding)
    :connection_(session),presence_(std::move(presence)),lease_(lease),resources_(std::move(resources)),
     rules_(std::move(rules)),policy_(policy),committed_policy_(policy),binding_(std::move(binding)),
     battle_generation_(session->battle_generation()),
     position_(position),direction_(direction),expected_sequence_(policy.first_sequence),
     publication_revision_(resources_.actual_initial_scene_generation),
     credit_us_(std::uint64_t(policy.initial_credit_steps)*policy.step_interval_us),clock_(Clock::now()) {}
OwnedTaiwanOrdinaryMovementAuthority::~OwnedTaiwanOrdinaryMovementAuthority() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    failed_=true;busy_=true;pending_.reset();
}
void OwnedTaiwanOrdinaryMovementAuthority::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("TW owned ordinary authority game owner mismatch");
}
void OwnedTaiwanOrdinaryMovementAuthority::retire() {
    owner();failed_=true;pending_.reset();
}
bool OwnedTaiwanOrdinaryMovementAuthority::retained_current() const {
    owner();return bound();
}
bool OwnedTaiwanOrdinaryMovementAuthority::bound() const {
    const auto session=connection_.lock();
    return !failed_ && (!binding_ || binding_->available()) && session && !session->closing() && session->id()==lease_.session &&
        session->account_id==lease_.account && session->character_id==lease_.character &&
        session->state()==SessionState::InWorld && session->recovered_world_ready() &&
        session->battle_generation()==battle_generation_ &&
        session->common_world_delivery_current(lease_.account,lease_.character,lease_.generation) &&
        !session->common_world_entry_current(lease_.account,lease_.character,lease_.generation) &&
        presence_->retained_ready_current(lease_);
}
bool OwnedTaiwanOrdinaryMovementAuthority::same_step(
    const TaiwanMovementRules::Step& a,const TaiwanMovementRules::Step& b) {
    return a.request.x==b.request.x && a.request.y==b.request.y &&
        a.request.sequence==b.request.sequence && a.request.opaque_tail==b.request.opaque_tail &&
        a.direction==b.direction && a.native_cell==b.native_cell;
}
bool OwnedTaiwanOrdinaryMovementAuthority::same_candidate(const Scene::Candidate& a,const Scene::Candidate& b) {
    return a.owner.lease==b.owner.lease && a.owner.position==b.owner.position &&
        a.owner.direction==b.owner.direction && a.owner.publication_revision==b.owner.publication_revision &&
        a.actual_resource_generation==b.actual_resource_generation &&
        a.actual_initial_scene_generation==b.actual_initial_scene_generation &&
        a.cell_source==b.cell_source && same_step(a.step,b.step);
}
bool OwnedTaiwanOrdinaryMovementAuthority::candidate_current(const Scene::Candidate& candidate) const {
    if(!bound() || candidate.owner.lease!=lease_ || candidate.owner.position!=position_ ||
       candidate.owner.direction!=direction_ || candidate.owner.publication_revision!=publication_revision_ ||
       candidate.actual_resource_generation!=resources_.actual_resource_generation ||
       candidate.actual_initial_scene_generation!=resources_.actual_initial_scene_generation ||
       candidate.cell_source!=Scene::CellSource::ComposedMode2 ||
       !RecoveredNativeMovement::ordinary_request(candidate.step.request) || candidate.step.direction>7)return false;
    const auto cell=resources_.read(candidate.step.request.x,candidate.step.request.y);
    return cell && *cell==candidate.step.native_cell && *cell!=0;
}
bool OwnedTaiwanOrdinaryMovementAuthority::retained(const std::shared_ptr<const Ticket>& ticket) const {
    return ticket && pending_==ticket && candidate_current(ticket->candidate) &&
        (!binding_ || (ticket->observation && binding_->current(*ticket->observation))) &&
        presence_->retained_population_current(ticket->population);
}
bool OwnedTaiwanOrdinaryMovementAuthority::population_current(
    const std::shared_ptr<const Ticket>& ticket,bool require_after,bool require_before) {
    if(!retained(ticket))return false;
    // Entire registry/root/pose population, including cross-version peers.
    // Only this actor's exact predicted sole-CAS successor may differ.
    const auto fresh=presence_->observe_ready_population();
    if(!fresh || !retained(ticket) || !presence_->retained_population_current(*fresh))return false;
    const auto rows=fresh->characters();
    if(rows.size()!=ticket->rows.size())return false;
    bool own=false;
    for(std::size_t i=0;i<rows.size();++i) {
        const auto& actual=rows[i];const auto& original=ticket->rows[i];
        if(actual.lease!=original.lease || !same_root(actual.character,original.character))return false;
        if(actual.lease==lease_) {
            if(own || original.position!=ticket->candidate.owner.position ||
               (require_after && actual.position!=ticket->after) ||
               (require_before && actual.position!=original.position) ||
               (actual.position!=original.position && actual.position!=ticket->after))return false;
            own=true;
        }else if(actual.position!=original.position)return false;
    }
    return own && retained(ticket) && presence_->retained_population_current(*fresh);
}
std::shared_ptr<OwnedTaiwanOrdinaryMovementAuthority> OwnedTaiwanOrdinaryMovementAuthority::adopt(
    const std::shared_ptr<Session>& session,std::shared_ptr<SharedWorldPresence> presence,
    const Lease& lease,const Scene::Resources& images,RecoveredPosition position,std::uint8_t direction,
    std::shared_ptr<TaiwanMovementRules> rules,TaiwanMovementRules::OrdinaryPolicy policy,
    std::shared_ptr<OwnedOrdinaryMovementPolicies::Binding> binding) {
    if(!session || !presence || !rules || !TaiwanMovementRules::valid_ordinary_policy(policy) ||
       !rules->supports_owned_ordinary() || direction>7 || position.area!=lease.position.area ||
       position.scene!=lease.position.scene || !images.actual_resource_generation ||
       !images.actual_initial_scene_generation || images.cell_source()!=Scene::CellSource::ComposedMode2 ||
       !images.complete())return {};
    auto result=std::shared_ptr<OwnedTaiwanOrdinaryMovementAuthority>(new OwnedTaiwanOrdinaryMovementAuthority(
        session,std::move(presence),lease,images,position,direction,std::move(rules),policy,std::move(binding)));
    Operation operation(*result);
    try {
        if(!result->bound())return {};
        std::optional<OwnedOrdinaryMovementPolicies::Observation> observation;
        if(result->binding_) {
            observation=result->binding_->refresh();
            if(observation->policy()!=policy || !result->bound() || !result->binding_->current(*observation))return {};
        }
        const auto population=result->presence_->observe_ready_population();
        if(!population || !result->bound() || !result->presence_->retained_population_current(*population))return {};
        bool own=false;
        for(const auto& row:population->characters())if(row.lease==lease) {
            if(own || row.position!=position)return {};
            own=true;
        }
        return own && result->bound() && (!result->binding_ || result->binding_->current(*observation)) &&
            result->presence_->retained_population_current(*population)?result:
            std::shared_ptr<OwnedTaiwanOrdinaryMovementAuthority>{};
    }catch(...) {result->retire();throw;}
}
std::optional<OwnedTaiwanOrdinaryMovementAuthority::Scene::Permit>
OwnedTaiwanOrdinaryMovementAuthority::authorize(const Scene::Candidate& input) {
    const auto self=shared_from_this(); // Keep this leaf alive across DB/Lua/population observers.
    Operation operation(*this);
    try {
        const auto candidate=input; // No borrowed public request survives an observer.
        if(pending_ || !candidate_current(candidate) ||
           publication_revision_==std::numeric_limits<std::uint64_t>::max() ||
           position_.revision==std::numeric_limits<std::uint64_t>::max()) {retire();return std::nullopt;}
        std::optional<OwnedOrdinaryMovementPolicies::Observation> observation;
        auto effective_policy=policy_;
        if(binding_) {observation=binding_->refresh();effective_policy=observation->policy();}
        const auto policy_current=[&] {return !binding_ || (observation && binding_->current(*observation));};
        if(!candidate_current(candidate) || !policy_current()) {retire();return std::nullopt;}
        const auto prepared=rules_->prepare(candidate.step.request,position_,direction_,candidate.step.native_cell);
        if(!prepared || !same_step(*prepared,candidate.step) || !candidate_current(candidate) || !policy_current()) {retire();return std::nullopt;}
        const auto population=presence_->observe_ready_population();
        if(!population || !candidate_current(candidate) || !policy_current() || !presence_->retained_population_current(*population)) {
            retire();return std::nullopt;
        }
        const auto observed=population->characters();
        std::vector<SharedWorldPresence::ReadyCharacter> rows(observed.begin(),observed.end());
        bool own=false,occupied=false;
        for(const auto& row:rows) {
            if(row.lease==lease_) {
                if(own || row.position!=position_) {retire();return std::nullopt;}own=true;
            }else if(row.position.area==position_.area && row.position.scene==position_.scene &&
                row.position.x==candidate.step.request.x && row.position.y==candidate.step.request.y)occupied=true;
        }
        const int dx=int(candidate.step.request.x)-position_.x,dy=int(candidate.step.request.y)-position_.y;
        bool sides_clear=true;
        if(dx && dy) {
            const auto horizontal=resources_.read(candidate.step.request.x,position_.y);
            const auto vertical=resources_.read(position_.x,candidate.step.request.y);
            sides_clear=horizontal && vertical && *horizontal && *vertical;
        }
        if(!own || !candidate_current(candidate) || !policy_current() || !presence_->retained_population_current(*population)) {
            retire();return std::nullopt;
        }
        const auto token=rules_->owned_ordinary_token(effective_policy,position_,candidate.step.request,
            expected_sequence_,occupied,sides_clear);
        if(!token || !candidate_current(candidate) || !policy_current() || !presence_->retained_population_current(*population)) {
            retire();return std::nullopt;
        }
        const auto sampled=Clock::now();
        if(sampled<clock_) {retire();return std::nullopt;}
        const auto elapsed=std::chrono::duration_cast<std::chrono::microseconds>(sampled-clock_).count();
        const std::uint64_t cap=std::uint64_t(committed_policy_.burst_steps)*committed_policy_.step_interval_us;
        if(elapsed<0 || credit_us_>cap) {retire();return std::nullopt;}
        const auto old_available=credit_us_+std::min<std::uint64_t>(static_cast<std::uint64_t>(elapsed),cap-credit_us_);
        const std::uint64_t new_cap=std::uint64_t(effective_policy.burst_steps)*effective_policy.step_interval_us;
        // Preserve earned fractional steps across LIVE policy replacement. The
        // checked policy domain bounds the product by39*60000000^2 (<uint64).
        const auto available=std::min(new_cap,old_available*effective_policy.step_interval_us/
            committed_policy_.step_interval_us);
        if(available<effective_policy.step_interval_us) {retire();return std::nullopt;}
        const RecoveredPosition after{position_.area,position_.scene,candidate.step.request.x,
            candidate.step.request.y,position_.revision+1};
        auto ticket=std::make_shared<const Ticket>(candidate,*population,std::move(rows),after,
            available-effective_policy.step_interval_us,sampled,effective_policy,std::move(observation));
        // CUSTOM-0150 complete logical5D uses explicit Lua custom token. This
        // does not recover native server token/echo/timing/reset or ACK receipt.
        const std::weak_ptr<OwnedTaiwanOrdinaryMovementAuthority> weak=shared_from_this();
        Scene::Permit permit({0x5d,*token},
            [weak,ticket](const Scene::Candidate& actual) {
                const auto self=weak.lock();return self && self->current(ticket,actual);
            },
            [weak,ticket](const SharedTaiwanMovement::Committed& committed) {
                const auto self=weak.lock();return self && self->publish(ticket,committed);
            });
        pending_=ticket;
        // Authorization has not crossed the common CAS yet: no observer may
        // preemptively advance even to the predicted durable successor.
        if(!population_current(ticket,false,true)) {retire();return std::nullopt;}
        return permit;
    }catch(...) {retire();throw;}
}
bool OwnedTaiwanOrdinaryMovementAuthority::current(
    const std::shared_ptr<const Ticket>& ticket,const Scene::Candidate& supplied) {
    Operation operation(*this);
    try {
        if(!ticket || pending_!=ticket || failed_)return false;
        const auto candidate=supplied;
        if(!same_candidate(candidate,ticket->candidate) || !population_current(ticket,false)) {
            retire();return false;
        }
        return true;
    }catch(...) {retire();throw;}
}
bool OwnedTaiwanOrdinaryMovementAuthority::publish(
    const std::shared_ptr<const Ticket>& ticket,const SharedTaiwanMovement::Committed& input) {
    Operation operation(*this);
    try {
        if(!ticket || pending_!=ticket || failed_)return false;
        const auto committed=input;
        if(committed.before!=ticket->candidate.owner.position || committed.after!=ticket->after ||
           !same_step(committed.step,ticket->candidate.step) || !population_current(ticket,true)) {
            retire();return false;
        }
        // Sole durable CAS already succeeded outside this owner. Detach before
        // advancing pure local state; no callback, DB writer or send follows.
        pending_.reset();
        position_=ticket->after;direction_=ticket->candidate.step.direction;++publication_revision_;
        expected_sequence_=static_cast<std::uint8_t>((ticket->candidate.step.request.sequence+1)%40);
        credit_us_=ticket->credit_us;clock_=ticket->clock;
        committed_policy_=ticket->effective_policy; // No sequence/pose/revision/initial-credit reset.
        if(!bound() || !presence_->retained_population_current(ticket->population)) {retire();return false;}
        return true;
    }catch(...) {retire();throw;}
}
}
