#include "cn/auth/SharedCharacterCreateOperation.h"
#include <algorithm>
#include <set>
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
bool scope_valid(const SharedCharacterCreateOperation::Scope& scope) {
    return scope.account && scope.world_session && scope.request;
}
bool same_row(const RecoveredCharacter& left,const RecoveredCharacter& right) {
    return left.id==right.id && left.account_id==right.account_id && left.slot==right.slot &&
        left.profile==right.profile && left.created_at==right.created_at &&
        left.name_codepage==right.name_codepage && left.streamer_privilege==right.streamer_privilege;
}
}
SharedCharacterCreateOperation::NativeCreatePlan::NativeCreatePlan(Scope scope,
    std::array<std::uint8_t,23> record,
    std::optional<CnCreationNameProjection> candidate,
    std::vector<std::uint8_t> choices,Current current)
    :scope_(std::move(scope)),record_(record),candidate_(std::move(candidate)),
     choices_(std::move(choices)),current_(std::move(current)) {}
std::optional<SharedCharacterCreateOperation::NativeCreatePlan>
SharedCharacterCreateOperation::NativeCreatePlan::from_native(Scope scope,
    std::span<const std::uint8_t> bytes,
    std::optional<CnCreationNameProjection> candidate,
    std::vector<std::uint8_t> choices,Current current) {
    const auto reply=god2cn::CnCharacterCreateStatus::read(bytes);
    if(!scope_valid(scope) || !reply || !current || ((reply->status()==0)!=candidate.has_value()))return std::nullopt;
    if(candidate) {
        if(!candidate->matches(*scope.request) || choices.empty())return std::nullopt;
        std::set<std::uint8_t> unique;
        for(const auto choice:choices)
            if(!god2cn::CnCreationLocationProjection::from_choice(choice) || !unique.insert(choice).second)
                return std::nullopt;
    }else if(!choices.empty())return std::nullopt;
    std::array<std::uint8_t,23> record;std::copy(bytes.begin(),bytes.end(),record.begin());
    return NativeCreatePlan(std::move(scope),record,std::move(candidate),std::move(choices),std::move(current));
}
bool SharedCharacterCreateOperation::NativeCreatePlan::current(const Scope& scope,CreateCheck check) const {
    return scope==scope_ && current_ && current_(scope_,check);
}
SharedCharacterCreateOperation::CreateResult::CreateResult(Scope scope,
    std::array<std::uint8_t,23> record,std::uint16_t status,std::optional<Created> created,Current current)
    :scope_(std::move(scope)),record_(record),status_(status),created_(std::move(created)),
     current_(std::move(current)) {}
std::optional<SharedCharacterCreateOperation::CreateResult>
SharedCharacterCreateOperation::CreateResult::from_native(Scope scope,
    std::span<const std::uint8_t> bytes,std::optional<Created> created,Current current) {
    const auto native=god2cn::CnCharacterCreateStatus::read(bytes);
    if(!scope_valid(scope) || !native || !current || ((native->status()==0)!=created.has_value()))
        return std::nullopt;
    if(created) {
        if(!created->character.id || created->character.account_id!=scope.account ||
           created->permitted_choices.empty())return std::nullopt;
        const auto& row=created->character;
        // Both the direct transaction mode and concrete CAS mode must return
        // the same original submitted name before exposing native success02.
        // This is result qualification, never a rollback of a real COMMIT.
        if(!CnCreationNameProjection::from_common_candidate(*scope.request,
            {row.slot,row.profile,row.name_codepage,row.streamer_privilege}))return std::nullopt;
        std::set<std::uint8_t> unique;
        for(const auto choice:created->permitted_choices)
            if(!god2cn::CnCreationLocationProjection::from_choice(choice) ||
               !unique.insert(choice).second)return std::nullopt;
    }
    std::array<std::uint8_t,23> record;
    std::copy(bytes.begin(),bytes.end(),record.begin());
    return CreateResult(std::move(scope),record,native->status(),std::move(created),std::move(current));
}
bool SharedCharacterCreateOperation::CreateResult::current(const Scope& scope,ReplyCheck check) const {
    return scope==scope_ && current_ && current_(scope_,check);
}
SharedCharacterCreateOperation::ChoiceResult::ChoiceResult(Scope scope,std::uint64_t character,
    std::uint8_t choice,std::array<std::uint8_t,3> record,Current current)
    :scope_(std::move(scope)),character_(character),choice_(choice),record_(record),
     current_(std::move(current)) {}
std::optional<SharedCharacterCreateOperation::ChoiceResult>
SharedCharacterCreateOperation::ChoiceResult::from_native(Scope scope,std::uint64_t character,
    std::uint8_t choice,std::span<const std::uint8_t> bytes,Current current) {
    if(!scope_valid(scope) || !character || !current ||
       !god2cn::CnCreationLocationProjection::from_choice(choice) ||
       !god2cn::CnCharacterLocationChoice::read_confirmation(bytes))return std::nullopt;
    std::array<std::uint8_t,3> record;
    std::copy(bytes.begin(),bytes.end(),record.begin());
    return ChoiceResult(std::move(scope),character,choice,record,std::move(current));
}
bool SharedCharacterCreateOperation::ChoiceResult::current(
    const Scope& scope,std::uint64_t character,std::uint8_t choice,ReplyCheck check) const {
    return scope==scope_ && character==character_ && choice==choice_ && current_ &&
        current_(scope_,character_,choice_,record_[1]&7,check);
}
SharedCharacterCreateOperation::NativeChoicePlan::NativeChoicePlan(Scope scope,
    std::uint64_t character,std::uint8_t choice,std::array<std::uint8_t,3> record,
    SqliteRecoveredCharacterRepository::InitialOwnedPosition position,Current current)
    :scope_(std::move(scope)),character_(character),choice_(choice),record_(record),
     position_(position),current_(std::move(current)) {}
std::optional<SharedCharacterCreateOperation::NativeChoicePlan>
SharedCharacterCreateOperation::NativeChoicePlan::from_native(Scope scope,std::uint64_t character,
    std::uint8_t choice,std::span<const std::uint8_t> bytes,
    SqliteRecoveredCharacterRepository::InitialOwnedPosition position,Current current) {
    if(!scope_valid(scope) || !character || !current ||
       !god2cn::CnCreationLocationProjection::from_choice(choice) ||
       !god2cn::CnCharacterLocationChoice::read_confirmation(bytes) || position.area>63 || position.scene>1023)
        return std::nullopt;
    std::array<std::uint8_t,3> record;std::copy(bytes.begin(),bytes.end(),record.begin());
    return NativeChoicePlan(std::move(scope),character,choice,record,position,std::move(current));
}
bool SharedCharacterCreateOperation::NativeChoicePlan::current(const Scope& scope,
    std::uint64_t character,std::uint8_t choice,ChoiceCheck check) const {
    return scope==scope_ && character==character_ && choice==choice_ && current_ &&
        current_(scope_,character_,choice_,record_[1]&7,check);
}
SharedCharacterCreateOperation::SharedCharacterCreateOperation(
    const std::shared_ptr<Connection>& connection,RecoveredCharacterRepository& characters,
    Scope scope,Sources sources,CurrentSelection selection,std::vector<RecoveredCharacter> existing_rows)
    :connection_(connection),characters_(characters),scope_(std::move(scope)),sources_(std::move(sources)),
     selection_(std::move(selection)),existing_rows_(std::move(existing_rows)) {}
void SharedCharacterCreateOperation::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN create operation game owner mismatch");
}
std::shared_ptr<SharedCharacterCreateOperation> SharedCharacterCreateOperation::prepare(
    const std::shared_ptr<Connection>& connection,RecoveredCharacterRepository& characters,
    std::shared_ptr<const Request> request,Sources sources,CurrentSelection selection) {
    if(!connection || connection->closing() || connection->role()!=Connection::Transport::Role::World ||
       !connection->verified_account_id() || !connection->world_session_id() ||
       !connection->world_admission_current() || !request || !sources || !selection)return {};
    if(sources.characters && static_cast<RecoveredCharacterRepository*>(sources.characters)!=&characters)return {};
    Scope scope{connection->verified_account_id(),connection->world_session_id(),std::move(request)};
    auto rows=characters.list_for_account(scope.account);
    std::set<std::uint64_t> unique;
    for(const auto& row:rows) {
        if(!row.id || row.account_id!=scope.account || !unique.insert(row.id).second)return {};
    }
    // Selection designates this operation only after prepare returns; its exact
    // pointer-qualified predicate is first consulted by start, before the writer.
    return std::shared_ptr<SharedCharacterCreateOperation>(new SharedCharacterCreateOperation(
        connection,characters,std::move(scope),std::move(sources),std::move(selection),std::move(rows)));
}
bool SharedCharacterCreateOperation::selection_current() const {
    owner();const auto connection=connection_.lock();
    return connection && !connection->closing() && connection->role()==Connection::Transport::Role::World &&
        connection->verified_account_id()==scope_.account &&
        connection->world_session_id()==scope_.world_session && connection->world_admission_current() &&
        selection_ && selection_(scope_);
}
bool SharedCharacterCreateOperation::created_owned(bool exact_snapshot) const {
    owner();if(!created_ || !created_->created())return false;
    const auto& expected=created_->created()->character;
    if(std::any_of(existing_rows_.begin(),existing_rows_.end(),[&](const auto& row){return row.id==expected.id;}))return false;
    unsigned matches=0;
    for(const auto& row:characters_.list_for_account(scope_.account))
        if(row.id==expected.id && row.account_id==scope_.account) {
            ++matches;if(exact_snapshot && !same_row(row,expected))return false;
        }
    return matches==1;
}
bool SharedCharacterCreateOperation::pending_current(const std::shared_ptr<const Request>& request,
    std::uint64_t character,std::span<const std::uint8_t> choices) const {
    owner();
    if(phase_!=Phase::Choosing || request!=scope_.request || !selection_current() ||
       !created_ || !created_->created() || created_->created()->character.id!=character ||
       !created_->current(scope_) || !created_owned(true))return false;
    const auto& offered=created_->created()->permitted_choices;
    return choices.size()==offered.size() && std::equal(choices.begin(),choices.end(),offered.begin());
}
void SharedCharacterCreateOperation::stop() {
    owner();phase_=Phase::Stopped;if(const auto connection=connection_.lock())connection->close();
}
void SharedCharacterCreateOperation::start(Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN create queue completion required");
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[completion](bool accepted) {
        if(!*completion)return;auto callback=std::move(*completion);*completion={};callback(accepted);
    };
    try {
        if(phase_!=Phase::Prepared || !selection_current()) {stop();finish(false);return;}
        phase_=Phase::Creating;
        std::optional<CreateResult> supplied;
        if(sources_.prepare) {
            auto native=sources_.prepare(scope_,existing_rows_);
            if(!native || !selection_current() || phase_!=Phase::Creating ||
               !native->current(scope_,CreateCheck::Prepared)) {stop();finish(false);return;}
            // Keep the actual plan/authority alive through02 acceptance and18.
            auto plan=std::make_shared<NativeCreatePlan>(std::move(*native));
            // Copy choice metadata before changing saved state; result/queue
            // allocation failures after COMMIT still need durable recovery.
            auto choices=plan->choices_;
            std::optional<Created> created;
            if(plan->candidate_) {
                if(!plan->candidate_->matches(*scope_.request)) {stop();finish(false);return;}
                const auto current=[this,plan](SqliteRecoveredCharacterRepository::CreationPhase phase) {
                    const auto check=phase==SqliteRecoveredCharacterRepository::CreationPhase::BeforeInsert ?
                        CreateCheck::BeforeInsert:CreateCheck::BeforeCommit;
                    return phase_==Phase::Creating && selection_current() && plan->current(scope_,check) &&
                        selection_current() && phase_==Phase::Creating;
                };
                auto row=sources_.characters->create_owned_snapshot(scope_.account,existing_rows_,
                    plan->candidate_->storage_candidate(),current);
                if(!row || !plan->candidate_->matches_created(*row)) {stop();finish(false);return;}
                created=Created{std::move(*row),std::move(choices)};
            }
            supplied=CreateResult::from_native(scope_,plan->record_,std::move(created),
                [plan](const Scope& scope,ReplyCheck check){return plan->current(scope,
                    check==ReplyCheck::QueueAccepted?CreateCheck::QueueAccepted:CreateCheck::ReadyForReply);});
        }else supplied=sources_.create(scope_);
        if(!supplied || !selection_current() || !supplied->current(scope_) || phase_!=Phase::Creating) {
            stop();finish(false);return;
        }
        created_=std::make_shared<const CreateResult>(std::move(*supplied));
        if(created_->created() && !created_owned(true)) {stop();finish(false);return;}
        const auto bytes=created_->record_bytes();
        std::vector<god2cn::Bytes> sequence;sequence.emplace_back(bytes.begin(),bytes.end());
        phase_=Phase::CreateReplyQueued;
        const auto connection=connection_.lock();
        if(!connection || connection->closing()) {stop();finish(false);return;}
        const auto published=std::make_shared<bool>(false);
        const auto result=created_;
        connection->send_world_batch_with_publication(std::move(sequence),
            [weak=weak_from_this(),result,published] {
                const auto self=weak.lock();if(!self)return false;
                const auto current=[&] {
                    return self->phase_==Phase::CreateReplyQueued && self->created_==result &&
                        self->selection_current() && (!result->created() || self->created_owned(true));
                };
                if(!current() || !result->current(self->scope_,ReplyCheck::QueueAccepted) || !current())return false;
                // Publish the exact next operation stage BEFORE IO release.
                // No allocating callback or rule check after this transition.
                self->phase_=result->created()?Phase::AwaitingChoice:
                    (result->status()==god2cn::CnCharacterCreateStatus::name_collision_message_id?
                     Phase::RetryAvailable:Phase::Failed);
                *published=true;return true;
            },
            [weak=weak_from_this(),result,published,finish](bool accepted) {
                const auto self=weak.lock();const auto connection=self?self->connection_.lock():nullptr;
                // Local queue acceptance follows qualified publication. Do not
                // reapply old rules/root predicates after a valid fast choice.
                const bool valid=accepted && *published && self && self->created_==result &&
                    connection && !connection->closing() && connection->verified_account_id()==self->scope_.account &&
                    connection->world_session_id()==self->scope_.world_session;
                if(!valid && self)self->stop();finish(valid);
            });
    }catch(...) {stop();finish(false);}
}
void SharedCharacterCreateOperation::receive_choice(std::span<const std::uint8_t> bytes,
    Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN creation choice completion required");
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    auto finish=[completion](bool accepted) {
        if(!*completion)return;auto callback=std::move(*completion);*completion={};callback(accepted);
    };
    try {
        const auto choice=god2cn::CnCharacterLocationChoice::read_request(bytes);
        if(phase_!=Phase::AwaitingChoice || !choice || !selection_current() || !created_ ||
           !created_->created() || !created_->current(scope_) || !created_owned(true)) {
            stop();finish(false);return;
        }
        phase_=Phase::Choosing;
        const auto weak=weak_from_this();
        auto identity=SharedCreationLocationIdentity::resolve(connection_.lock(),characters_,scope_.request,
            created_->created()->character.id,created_->created()->permitted_choices,
            [weak](const std::shared_ptr<const Request>& request,std::uint64_t character,
                   std::span<const std::uint8_t> permitted) {
                const auto self=weak.lock();return self && self->pending_current(request,character,permitted);
            },bytes);
        if(!identity || !identity->current()) {stop();finish(false);return;}
        // Real writer rechecks its revision/CAS and consumes the pending choice
        // atomically. Identity resolution alone is never that transaction.
        const auto character=created_->created()->character.id;
        std::optional<ChoiceResult> supplied;
        if(sources_.prepare_choice) {
            auto native=sources_.prepare_choice(scope_,*identity,created_->created()->character);
            if(!native || !identity->current() || phase_!=Phase::Choosing ||
               !native->current(scope_,character,choice->raw_choice_byte,ChoiceCheck::Prepared)) {
                stop();finish(false);return;
            }
            auto plan=std::make_shared<NativeChoicePlan>(std::move(*native));
            const auto current=[this,plan,&identity,character,selected=choice->raw_choice_byte](
                SqliteRecoveredCharacterRepository::CreationPositionPhase phase) {
                const auto check=phase==SqliteRecoveredCharacterRepository::CreationPositionPhase::BeforeInsert ?
                    ChoiceCheck::BeforeInsert:ChoiceCheck::BeforeCommit;
                // Identity's root snapshot is intentionally unchanged by this
                // initial-position writer; it can be rechecked before COMMIT.
                return phase_==Phase::Choosing && identity->current() &&
                    plan->current(scope_,character,selected,check) && identity->current() && phase_==Phase::Choosing;
            };
            const auto position=sources_.characters->insert_owned_creation_position(
                created_->created()->character,plan->position_,current);
            if(!position) {stop();finish(false);return;}
            supplied=ChoiceResult::from_native(scope_,character,choice->raw_choice_byte,plan->record_,
                [plan,position=*position,repository=sources_.characters](const Scope& scope,std::uint64_t id,
                    std::uint8_t selected,std::uint8_t slot,ReplyCheck check) {
                    return slot==(plan->record_[1]&7) &&
                        plan->current(scope,id,selected,check==ReplyCheck::QueueAccepted?
                            ChoiceCheck::QueueAccepted:ChoiceCheck::ReadyForReply) &&
                        repository->load_position(scope.account,id)==std::optional<RecoveredPosition>{position};
                });
        }else supplied=sources_.choose(scope_,*identity);
        if(!supplied || !selection_current() || !created_owned(false) ||
           !supplied->current(scope_,character,choice->raw_choice_byte) || phase_!=Phase::Choosing) {
            stop();finish(false);return;
        }
        chosen_=std::make_shared<const ChoiceResult>(std::move(*supplied));
        const auto record=chosen_->record_bytes();
        std::vector<god2cn::Bytes> sequence;sequence.emplace_back(record.begin(),record.end());
        phase_=Phase::ChoiceReplyQueued;
        const auto connection=connection_.lock();
        if(!connection || connection->closing()) {stop();finish(false);return;}
        const auto published=std::make_shared<bool>(false);
        const auto result=chosen_;
        connection->send_world_batch_with_publication(std::move(sequence),
            [weak,result,published,character,choice=choice->raw_choice_byte] {
                const auto self=weak.lock();if(!self)return false;
                const auto current=[&] {
                    return self->phase_==Phase::ChoiceReplyQueued && self->chosen_==result &&
                        self->selection_current() && self->created_owned(false);
                };
                // The actual choice may change profile fields; its committed
                // CAS/position/current lease replaces the pre-choice snapshot.
                if(!current() || !result->current(self->scope_,character,choice,ReplyCheck::QueueAccepted) ||
                   !current())return false;
                self->phase_=Phase::Completed;*published=true;return true;
            },
            [weak,result,published,finish](bool accepted) {
                const auto self=weak.lock();const auto connection=self?self->connection_.lock():nullptr;
                const bool valid=accepted && *published && self && self->chosen_==result &&
                    connection && !connection->closing() && connection->verified_account_id()==self->scope_.account &&
                    connection->world_session_id()==self->scope_.world_session;
                // No late pre-choice predicate or saved-state rollback; the
                // original terminal/reconnect path uses the published stage.
                if(!valid && self)self->stop();finish(valid);
            });
    }catch(...) {stop();finish(false);}
}
bool SharedCharacterCreateOperation::retry_available() const {
    owner();return phase_==Phase::RetryAvailable && selection_current() && created_ && created_->current(scope_);
}
bool SharedCharacterCreateOperation::terminal_quiescent() const {
    owner();
    switch(phase_) {
    case Phase::AwaitingChoice:case Phase::RetryAvailable:case Phase::Failed:case Phase::Completed:
        return selection_current();
    default:return false;
    }
}
}
