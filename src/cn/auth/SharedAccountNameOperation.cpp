#include "cn/auth/SharedAccountSelection.h"
#include "cn/protocol/CnCharacterSummary.h"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
bool name_same_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot && a.profile==b.profile &&
        a.created_at==b.created_at && a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
bool name_same_roots(const std::vector<RecoveredCharacter>& a,const std::vector<RecoveredCharacter>& b) {
    if(a.size()!=b.size())return false;
    for(const auto& row:a) {
        const auto at=std::find_if(b.begin(),b.end(),[&](const auto& r){return r.id==row.id;});
        if(at==b.end() || !name_same_root(row,*at))return false;
    }
    return true;
}
}
SharedAccountSelection::NameDecision::NameDecision(NameScope scope,
    std::optional<CnSelectionNameProjection> candidate,
    std::shared_ptr<const NativeSummary> summary,god2cn::Bytes failure,Current current)
    :scope_(std::move(scope)),candidate_(std::move(candidate)),summary_(std::move(summary)),
     failure_(std::move(failure)),current_(std::move(current)) {}
std::optional<SharedAccountSelection::NameDecision> SharedAccountSelection::NameDecision::from_native_success(
    NameScope scope,CnSelectionNameProjection candidate,
    NativeSummary summary,Current current) {
    if(!scope.account || !scope.account_session || !scope.character || !scope.attempt || !current)
        return std::nullopt;
    return NameDecision(std::move(scope),std::move(candidate),
        std::make_shared<const NativeSummary>(std::move(summary)),{},std::move(current));
}
std::optional<SharedAccountSelection::NameDecision> SharedAccountSelection::NameDecision::from_native_failure(
    NameScope scope,god2cn::Bytes record,Current current) {
    if(!scope.account || !scope.account_session || !scope.character || !scope.attempt || !current ||
       record.size()!=2 || record[0]!=0x1e)return std::nullopt;
    return NameDecision(std::move(scope),{}, {},std::move(record),std::move(current));
}
bool SharedAccountSelection::NameDecision::current(const NameScope& scope,NameCheck check) const {
    return scope==scope_ && current_ && current_(scope_,check);
}
bool SharedAccountSelection::install_name_sources(NameSources sources) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN name source game owner mismatch");
    const auto connection=connection_.lock();
    if(name_sources_ || active_name_ || selection_queue_pending_ || !sources ||
       static_cast<RecoveredCharacterRepository*>(sources.characters)!=&characters_ ||
       !sources.presence->owns_repository(characters_) || !connection || connection->closing() ||
       connection->role()!=Connection::Transport::Role::Account ||
       connection->verified_account_id()!=grant_.key.account ||
       !admission_->account_owned(grant_,account_session_,grant_.key.account,Admission::Clock::now()))return false;
    name_sources_=std::move(sources);return true;
}
bool SharedAccountSelection::name_roots_current(const std::vector<RecoveredCharacter>& expected) {
    return name_same_roots(characters_.list_for_account(grant_.key.account),expected);
}
bool SharedAccountSelection::name_operation_current(const NameScope& scope,
    const std::optional<Admission::QueuedSelection>& queued) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN name operation game owner mismatch");
    const auto connection=connection_.lock();
    if(!active_name_ || *active_name_!=scope || !name_sources_ || !connection || connection->closing() ||
       connection->role()!=Connection::Transport::Role::Account || scope.account!=grant_.key.account ||
       scope.account_session!=account_session_ || connection->verified_account_id()!=scope.account)return false;
    const auto registry_current=[&] {
        return queued?admission_->queued_selection_current(*queued,Admission::Clock::now()):
            admission_->account_target_allowed(grant_,account_session_,scope.target,Admission::Clock::now());
    };
    return registry_current() && name_sources_->current_phase() && registry_current() &&
        connection->verified_account_id()==scope.account && active_name_ && *active_name_==scope;
}
void SharedAccountSelection::receive_name(god2cn::Bytes bytes,Connection::Transport::Completion done) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN name receive game owner mismatch");
    if(!done)throw std::invalid_argument("CN name completion required");
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    const auto finish=[completion](bool accepted) {
        auto callback=std::move(*completion);if(callback)callback(accepted);
    };
    std::optional<Admission::QueuedSelection> ticket;
    const auto stop=[&] {
        if(ticket)admission_->cancel_selection_queue(*ticket);
        selection_queue_pending_=false;active_name_.reset();
        if(const auto connection=connection_.lock())connection->close();
        // Never undo a real saved-name COMMIT after queue/local failure.
    };
    try {
        const auto request=god2cn::CnSelectionNameSubmission::read(bytes);
        if(!name_sources_ || !request || active_name_ || selection_queue_pending_) {finish(false);return;}
        auto identity=resolve_name_submission(*request,name_sources_->current_phase);
        if(!identity || !published_summary_) {finish(false);return;}
        auto expected=std::make_shared<const std::vector<RecoveredCharacter>>(identity->expected_roots());
        auto scope=std::make_shared<const NameScope>(NameScope{identity->account(),account_session_,identity->character(),
            published_summary_->scope_.target,identity->native_row_ordinal(),std::shared_ptr<const NameAttempt>(new NameAttempt)});
        active_name_=scope;
        if(!name_operation_current(*scope,{}) || !identity->current() || !name_roots_current(*expected)) {
            stop();finish(false);return;
        }
        auto supplied=name_sources_->prepare(*scope,*request,*expected);
        if(!supplied || !name_operation_current(*scope,{}) || !identity->current() ||
           !name_roots_current(*expected) || !supplied->current(*scope,NameCheck::BeforeReplace)) {
            stop();finish(false);return;
        }
        auto decision=std::make_shared<const NameDecision>(std::move(*supplied));
        auto next=std::make_shared<std::vector<RecoveredCharacter>>(*expected);
        auto old_identity=std::make_shared<const NameIdentity>(std::move(*identity));
        bool committed=false;
        std::vector<god2cn::Bytes> frames;
        if(decision->candidate_) {
            if(!decision->summary_ || !decision->candidate_->matches(*request)) {stop();finish(false);return;}
            const auto& candidate=decision->candidate_->storage_candidate();
            const auto at=std::find_if(next->begin(),next->end(),[&](const auto& row){return row.id==scope->character;});
            if(at==next->end()) {stop();finish(false);return;}
            std::copy(candidate.common_name_bytes.begin(),candidate.common_name_bytes.end(),at->profile.begin());
            at->name_codepage=candidate.name_codepage;
            const auto& summary=*decision->summary_;
            const auto native=god2cn::CnCharacterSummary::read(summary.record_);
            const auto row_id=std::find(summary.character_ids_.begin(),summary.character_ids_.end(),scope->character);
            const auto row=native && row_id!=summary.character_ids_.end()?
                native->character(static_cast<unsigned>(row_id-summary.character_ids_.begin())):std::nullopt;
            if(summary.scope_!=NativeSummary::Scope{scope->account,scope->target} ||
               !name_same_roots(summary.account_snapshot_,*next) || !row || row->name_bytes()!=request->submitted_name_bytes()) {
                stop();finish(false);return;
            }
            frames.push_back(summary.record_); // Complete native bytes copied BEFORE SQL.
            const auto current=[&](SharedCharacterNameReplacement::Phase phase) {
                const bool before=phase==SharedCharacterNameReplacement::Phase::BeforeReplace;
                const auto check=before?NameCheck::BeforeReplace:NameCheck::BeforeCommit;
                return name_operation_current(*scope,{}) &&
                    (before?old_identity->current():name_roots_current(*next)) &&
                    decision->current(*scope,check) && name_operation_current(*scope,{}) &&
                    (before?old_identity->current():name_roots_current(*next));
            };
            auto updated=SharedCharacterNameReplacement::commit(*name_sources_->characters,*admission_,
                *name_sources_->presence,scope->account,*expected,scope->character,candidate,current);
            if(!updated || !name_same_root(*updated,*at)) {stop();finish(false);return;}
            committed=true;
        }else {
            frames.push_back(decision->failure_); // Exact source-issued1E; no error guess.
        }
        const auto state_current=[&] {
            return name_operation_current(*scope,{}) && name_roots_current(committed?*next:*expected) &&
                (committed?name_sources_->presence->unreserved(scope->account,scope->character):old_identity->current());
        };
        if(!state_current() || !decision->current(*scope,NameCheck::BeforePublish) || !state_current() ||
           (committed && !qualify(scope->target,*decision->summary_,NativeSummary::Check::BeforePublish))) {
            stop();finish(false);return;
        }
        if(committed) {
            ticket=admission_->begin_selection_queue(grant_,account_session_,scope->target,
                decision->summary_->character_ids_,Admission::Clock::now(),decision->summary_->record_);
            if(!ticket) {stop();finish(false);return;}
            selection_queue_pending_=true;
        }
        const auto published=std::make_shared<bool>(false);
        const auto registry=admission_;
        const auto connection=connection_.lock();
        if(!connection || connection->closing()) {stop();finish(false);return;}
        connection->send_account_batch_with_publication(std::move(frames),
            [weak=weak_from_this(),scope,decision,expected,next,old_identity,token=ticket,committed,published] {
                const auto self=weak.lock();if(!self)return false;
                const auto current=[&] {
                    return self->name_operation_current(*scope,token) &&
                        self->name_roots_current(committed?*next:*expected) &&
                        (committed?self->name_sources_->presence->unreserved(scope->account,scope->character):old_identity->current());
                };
                if(!current() || !decision->current(*scope,NameCheck::QueueAccepted) || !current())return false;
                if(committed) {
                    if(!self->qualify(scope->target,*decision->summary_,NativeSummary::Check::QueueAccepted) ||
                       !current() || !self->admission_->commit_selection_queue(*token,Admission::Clock::now()))return false;
                    // No callback/yield/allocation after COMMIT and before
                    // retaining this exact full07/revision. World can claim
                    // only after the IO barrier releases the native record.
                    self->published_summary_=decision->summary_;self->published_ticket_=*token;
                }
                *published=true;return true;
            },
            [weak=weak_from_this(),registry,scope,token=ticket,published,completion,finish](bool queued) {
                if(!*completion)return;
                const auto self=weak.lock();const auto connection=self?self->connection_.lock():std::shared_ptr<Connection>{};
                const bool valid=queued && *published && self && self->active_name_==scope &&
                    connection && !connection->closing() && connection->verified_account_id()==scope->account;
                if(self && self->active_name_==scope) {self->active_name_.reset();self->selection_queue_pending_=false;}
                if(!valid) {
                    if(token)registry->cancel_selection_queue(*token);
                    if(connection)connection->close();
                }
                // Exact source was qualified before IO release. A fast peer
                // may already own the world; no late old-offer/root veto or
                // revocation of Reserved/WorldOwned from this queue callback.
                finish(valid);
            });
    }catch(...) {stop();finish(false);}
}
}
