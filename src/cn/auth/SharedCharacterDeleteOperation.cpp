#include "cn/auth/SharedCharacterDeleteOperation.h"
#include <algorithm>
#include <stdexcept>
#include <utility>
#include <set>
#include <tuple>

namespace god2::cn {
namespace {
bool same_row(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage &&
        a.streamer_privilege==b.streamer_privilege;
}
bool same_roots(std::span<const RecoveredCharacter> a,std::span<const RecoveredCharacter> b) {
    return a.size()==b.size() && std::equal(a.begin(),a.end(),b.begin(),same_row);
}
}
SharedCharacterDeleteOperation::SummaryDecision::SummaryDecision(Scope scope,RecoveredCharacter expected,
    SummaryObservation observation,Current current)
    :scope_(std::move(scope)),expected_(std::move(expected)),observation_(std::move(observation)),current_(std::move(current)) {}
std::optional<SharedCharacterDeleteOperation::SummaryDecision>
SharedCharacterDeleteOperation::SummaryDecision::from_actual_issuer(Scope scope,RecoveredCharacter expected,
    SummaryObservation observation,Current current) {
    if(!scope.account || !scope.world_session || !scope.character || scope.native_slot>=8 || !scope.attempt ||
       !current || expected.account_id!=scope.account || expected.id!=scope.character)return std::nullopt;
    std::set<std::uint64_t> ids;bool selected=false;
    for(const auto& row:observation.roots) {
        if(!row.id || row.account_id!=scope.account || !ids.insert(row.id).second)return std::nullopt;
        if(row.id==scope.character){if(!same_row(row,expected))return std::nullopt;selected=true;}
    }
    if(!selected)return std::nullopt;
    std::optional<std::tuple<std::uint16_t,std::uint16_t,std::string>> previous;
    for(const auto& summary:observation.summaries) {
        const auto key=std::tuple{summary.group,summary.server,summary.client_sha256};
        if(summary.account!=scope.account || !summary.revision || summary.record.empty() ||
           (previous && key<=*previous))return std::nullopt;
        previous=key;
        for(const auto& row:summary.rows)if(!ids.contains(row.character))return std::nullopt;
    }
    return SummaryDecision(std::move(scope),std::move(expected),std::move(observation),std::move(current));
}
bool SharedCharacterDeleteOperation::SummaryDecision::matches_removal_inputs(
    std::span<const NativeCharacterSummarySnapshot> summaries,std::span<const RecoveredCharacter> roots) const {
    return summaries.size()==observation_.summaries.size() &&
        std::equal(summaries.begin(),summaries.end(),observation_.summaries.begin()) && same_roots(roots,observation_.roots);
}
bool SharedCharacterDeleteOperation::SummaryDecision::matches(const Scope& scope,
    const RecoveredCharacter& expected,const SummaryObservation& observation) const {
    return scope==scope_ && same_row(expected,expected_) && matches_removal_inputs(observation.summaries,observation.roots);
}
bool SharedCharacterDeleteOperation::SummaryDecision::current(const Scope& scope,Check check) const {
    return scope==scope_ && current_ && current_(scope_,check,observation_);
}
SharedCharacterDeleteOperation::Decision::Decision(Scope scope,RecoveredCharacter expected,
    std::array<std::uint8_t,23> record,std::uint16_t status,Current current)
    :scope_(std::move(scope)),expected_(std::move(expected)),record_(record),status_(status),
     current_(std::move(current)) {}
std::optional<SharedCharacterDeleteOperation::Decision>
SharedCharacterDeleteOperation::Decision::from_native(Scope scope,RecoveredCharacter expected,
    std::span<const std::uint8_t> bytes,Current current) {
    const auto status=god2cn::CnWorldSelectionStatus::read(bytes);
    if(!scope.account || !scope.world_session || !scope.character || scope.native_slot>=8 ||
       !scope.attempt || !current || !status || expected.id!=scope.character ||
       expected.account_id!=scope.account)return std::nullopt;
    std::array<std::uint8_t,23> record;
    std::copy(bytes.begin(),bytes.end(),record.begin());
    return Decision(std::move(scope),std::move(expected),record,status->status,std::move(current));
}
bool SharedCharacterDeleteOperation::Decision::current(const Scope& scope,Check check) const {
    return scope==scope_ && current_ && current_(scope_,check);
}
SharedCharacterDeleteOperation::SharedCharacterDeleteOperation(
    const std::shared_ptr<Connection>& connection,std::shared_ptr<SharedWorldAdmission> admission,
    SharedCharacterDeleteIdentity identity,Scope scope,RecoveredCharacter expected,
    Sources sources,CurrentSelection selection)
    :connection_(connection),admission_(std::move(admission)),identity_(std::move(identity)),
     scope_(std::move(scope)),expected_(std::move(expected)),sources_(std::move(sources)),
     selection_(std::move(selection)) {}
void SharedCharacterDeleteOperation::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN delete operation game owner mismatch");
}
std::shared_ptr<SharedCharacterDeleteOperation> SharedCharacterDeleteOperation::prepare(
    const std::shared_ptr<Connection>& connection,RecoveredCharacterRepository& characters,
    std::shared_ptr<SharedWorldAdmission> admission,SharedCharacterDeleteIdentity identity,
    Sources sources,CurrentSelection selection) {
    if(!connection || connection->closing() || !admission || !sources || !selection ||
       static_cast<RecoveredCharacterRepository*>(sources.characters)!=&characters ||
       !sources.presence->owns_repository(characters) ||
       (sources.native_summary_removal && !sources.native_summary_removal->snapshots.get().owns_characters(characters)) ||
       !identity.current() ||
       connection->verified_account_id()!=identity.account() ||
       connection->world_session_id()!=identity.world_session() || !connection->world_admission_current())return {};
    std::optional<RecoveredCharacter> expected;
    for(const auto& row:characters.list_for_account(identity.account()))
        if(row.id==identity.character() && row.account_id==identity.account()) {
            if(expected)return {};expected=row;
        }
    if(!expected || !identity.current())return {};
    Scope scope{identity.account(),identity.world_session(),identity.character(),identity.native_slot(),
                std::shared_ptr<const Attempt>(new Attempt)};
    // Designation happens in Selection before any actual supplier is called.
    return std::shared_ptr<SharedCharacterDeleteOperation>(new SharedCharacterDeleteOperation(
        connection,std::move(admission),std::move(identity),std::move(scope),std::move(*expected),
        std::move(sources),std::move(selection)));
}
bool SharedCharacterDeleteOperation::selection_current() const {
    owner();const auto connection=connection_.lock();
    return connection && !connection->closing() && connection->role()==Connection::Transport::Role::World &&
        connection->verified_account_id()==scope_.account &&
        connection->world_session_id()==scope_.world_session && connection->world_admission_current() &&
        selection_ && selection_(scope_);
}
bool SharedCharacterDeleteOperation::stored_current(bool removed) const {
    owner();unsigned matches=0;
    for(const auto& row:sources_.characters->list_for_account(scope_.account))
        if(row.id==scope_.character) {
            ++matches;if(row.account_id!=scope_.account || !same_row(row,expected_))return false;
        }
    return removed?matches==0:matches==1;
}
void SharedCharacterDeleteOperation::stop() {
    owner();phase_=committed()?Phase::CommittedFailure:Phase::Stopped;
    if(const auto connection=connection_.lock())connection->close();
    // A committed removal is never undone by local queue/connection failure.
    // Actual durable recovery/receipts remain required before hosting this source.
}
bool SharedCharacterDeleteOperation::summary_queue_current(Check check) const {
    owner();
    if(!sources_.native_summary_removal)return !summary_decision_;
    if(!decision_)return false;
    if(!decision_->removal_required())return !committed() && !summary_decision_;
    return committed() && summary_decision_ && summary_decision_->current(scope_,check);
}
bool SharedCharacterDeleteOperation::commit_held_reply() {
    owner();
    try {
        // The strand/game handoff yielded since preparation. Requalify the
        // same retained operation, full root and original offered identity.
        // The actual writer subsequently CAS-checks the whole summary tuple.
        if(phase_!=Phase::ReplyHeld || removal_observation_.attempted() || !decision_ || !selection_current() ||
           !identity_.current() || !stored_current(false) ||
           (decision_->removal_required() && bool(sources_.native_summary_removal)!=bool(summary_decision_)) ||
           (!decision_->removal_required() && summary_decision_)) {
            stop();return false;
        }
        if(decision_->removal_required()) {
            phase_=Phase::Removing;
            const auto current=[this](SharedCharacterRemoval::Phase phase) {
                const auto check=phase==SharedCharacterRemoval::Phase::BeforeErase?
                    Check::BeforeErase:Check::BeforeCommit;
                // Staged absence invalidates the old identity; actual rule,
                // lease and full CAS must authorize BeforeCommit instead.
                return phase_==Phase::Removing && selection_current() &&
                    (phase!=SharedCharacterRemoval::Phase::BeforeErase || identity_.current()) &&
                    decision_->current(scope_,check) && phase_==Phase::Removing && selection_current() &&
                    (phase!=SharedCharacterRemoval::Phase::BeforeErase || identity_.current());
            };
            bool removed=false;
            if(sources_.native_summary_removal) {
                const auto actual=[this,&current](SharedCharacterRemoval::Phase phase,
                    std::span<const NativeCharacterSummarySnapshot> inventory,std::span<const RecoveredCharacter> roots) {
                    const auto check=phase==SharedCharacterRemoval::Phase::BeforeErase?Check::BeforeErase:Check::BeforeCommit;
                    return current(phase) && summary_decision_ && summary_decision_->matches_removal_inputs(inventory,roots) &&
                        summary_decision_->current(scope_,check) && current(phase);
                };
                // These synchronous observers cannot outlive current. Own the
                // entire expected inventory before any removal SQL executes.
                auto expected_summaries=summary_decision_->observation().summaries;
                removed=SharedCharacterRemoval::commit_with_native_summaries_observed(*sources_.characters,
                    sources_.native_summary_removal->snapshots.get(),*admission_,*sources_.presence,expected_,
                    std::move(expected_summaries),actual,removal_observation_);
            }else removed=SharedCharacterRemoval::commit_observed(*sources_.characters,*admission_,*sources_.presence,
                expected_,current,removal_observation_);
            if(!removed || !removal_observation_.offers_invalidated() ||
               removal_observation_.account()!=scope_.account || removal_observation_.character()!=scope_.character) {
                stop();return false;
            }
        }
        const auto expected_phase=committed()?Phase::Removing:Phase::ReplyHeld;
        // COMMIT invalidated offers of this ID. The retained exact world ticket
        // and receipt authority qualify release without demanding old raw07.
        if(phase_!=expected_phase || !selection_current() || !stored_current(committed()) ||
           (committed() && !sources_.presence->unreserved(scope_.account,scope_.character)) ||
           (!committed() && !identity_.current()) || !decision_->current(scope_,Check::BeforeQueue) ||
           !summary_queue_current(Check::BeforeQueue) || phase_!=expected_phase ||
           !selection_current() || !stored_current(committed()) ||
           (committed() && !sources_.presence->unreserved(scope_.account,scope_.character)) ||
           (!committed() && !identity_.current())) {
            stop();return false;
        }
        phase_=Phase::ReplyQueued;return true;
    }catch(...) {stop();return false;}
}
void SharedCharacterDeleteOperation::start(Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN deletion queue completion required");
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    const auto finish=[completion](bool accepted) {
        if(!*completion)return;auto callback=std::move(*completion);*completion={};callback(accepted);
    };
    try {
        if(phase_!=Phase::Prepared || !selection_current() || !identity_.current() || !stored_current(false)) {
            stop();finish(false);return;
        }
        phase_=Phase::Deciding;
        auto supplied=sources_.prepare(scope_,expected_);
        if(!supplied || phase_!=Phase::Deciding || !selection_current() || !identity_.current() ||
           !same_row(supplied->expected(),expected_) || !stored_current(false)) {
            stop();finish(false);return;
        }
        decision_=std::make_shared<const Decision>(std::move(*supplied));
        const auto record=decision_->record_bytes();
        // Prepare exact native bytes and owned decisions before held transport
        // staging. A failed transaction never releases this native02 reply.
        std::vector<god2cn::Bytes> sequence;sequence.emplace_back(record.begin(),record.end());
        if(decision_->removal_required() && sources_.native_summary_removal) {
            auto& source=*sources_.native_summary_removal;
            auto observed=source.snapshots.get().read_removal_observation(scope_.account);
            auto summary=source.prepare(scope_,expected_,observed);
            if(!summary || !summary->matches(scope_,expected_,observed) || phase_!=Phase::Deciding ||
               !selection_current() || !identity_.current() || !stored_current(false)) {
                stop();finish(false);return;
            }
            summary_decision_=std::make_shared<const SummaryDecision>(std::move(*summary));
        }
        phase_=Phase::ReplyHeld;
        const auto connection=connection_.lock();
        if(!connection || connection->closing()) {stop();finish(false);return;}
        // Both callbacks, PendingSend, native encryption and bounded wire queue
        // are prepared before commit_held_reply can invoke removal SQL.
        connection->send_world_batch_with_commit(std::move(sequence),[weak=weak_from_this()] {
            const auto self=weak.lock();return self && self->commit_held_reply();
        },[weak=weak_from_this(),finish](bool accepted) {
            const auto self=weak.lock();bool valid=false;
            try {
                if(self)self->owner();
                valid=accepted && self && self->phase_==Phase::ReplyQueued && self->selection_current() &&
                    self->stored_current(self->committed()) &&
                    (!self->committed() || self->sources_.presence->unreserved(self->scope_.account,self->scope_.character)) &&
                    (self->committed() || self->identity_.current()) && self->decision_ &&
                    self->decision_->current(self->scope_,Check::AfterQueue) &&
                    self->summary_queue_current(Check::AfterQueue) &&
                    self->phase_==Phase::ReplyQueued && self->selection_current() &&
                    self->stored_current(self->committed()) &&
                    (!self->committed() || self->sources_.presence->unreserved(self->scope_.account,self->scope_.character)) &&
                    (self->committed() || self->identity_.current());
                if(valid)self->phase_=self->committed()?Phase::Completed:Phase::Failed;
            }catch(...) {valid=false;}
            if(!valid && self)self->stop();finish(valid);
        });
    }catch(...) {stop();finish(false);}
}
bool SharedCharacterDeleteOperation::terminal_quiescent() const {
    owner();return phase_==Phase::Completed || phase_==Phase::Failed;
}
bool SharedCharacterDeleteOperation::failure_reply_complete() const {
    owner();return phase_==Phase::Failed && !committed();
}
SharedCharacterDeleteOperation::RemovalOutcome SharedCharacterDeleteOperation::removal_outcome() const {
    owner();return {removal_observation_.attempted(),committed(),removal_observation_.offers_invalidated()};
}
}
