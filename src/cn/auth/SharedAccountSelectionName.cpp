#include "cn/auth/SharedAccountSelection.h"
#include "cn/protocol/CnCharacterSummary.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
SharedAccountSelection::NameIdentity::NameIdentity(std::weak_ptr<SharedAccountSelection> controller,
    std::shared_ptr<const NativeSummary> summary,Admission::AccountOffer offer,
    std::uint64_t account,std::uint64_t character,std::uint16_t ordinal,std::function<bool()> phase)
    :controller_(std::move(controller)),summary_(std::move(summary)),offer_(std::move(offer)),
     account_(account),character_(character),ordinal_(ordinal),phase_(std::move(phase)) {}
bool SharedAccountSelection::NameIdentity::current() const {
    const auto controller=controller_.lock();
    return controller && controller->name_identity_current(*this);
}
std::vector<RecoveredCharacter> SharedAccountSelection::NameIdentity::expected_roots() const {
    const auto controller=controller_.lock();
    return controller?controller->name_identity_roots(*this):std::vector<RecoveredCharacter>{};
}
std::vector<RecoveredCharacter> SharedAccountSelection::name_identity_roots(const NameIdentity& identity) const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN name identity game owner mismatch");
    // Captured historical CAS input only; current() is mandatory again BEFORE
    // staged mutation. The actual writer owner must observe its staged roots
    // separately at BeforeCommit. This snapshot is not current permission.
    if(identity.controller_.lock().get()!=this || !identity.summary_)return {};
    return identity.summary_->account_snapshot_;
}
bool SharedAccountSelection::name_identity_current(const NameIdentity& identity) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN name identity game owner mismatch");
    const auto connection=connection_.lock();
    if(identity.controller_.lock().get()!=this || !identity.phase_ || !identity.summary_ ||
       published_summary_!=identity.summary_ || selection_queue_pending_ || !connection || connection->closing() ||
       connection->role()!=Connection::Transport::Role::Account || identity.account_!=grant_.key.account ||
       connection->verified_account_id()!=identity.account_ ||
       !admission_->selected_account_offer_current(identity.offer_,Admission::Clock::now()))return false;
    const auto& summary=*identity.summary_;
    const auto& offered=identity.offer_.source();
    if(summary.scope_!=NativeSummary::Scope{identity.account_,identity.offer_.target()} ||
       summary.record_!=offered.adapter_record || summary.character_ids_!=offered.character_ids ||
       identity.ordinal_>=summary.character_ids_.size() ||
       summary.character_ids_[identity.ordinal_]!=identity.character_)return false;
    const auto native=god2cn::CnCharacterSummary::read(summary.record_);
    const auto row=native?native->character(identity.ordinal_):std::nullopt;
    if(!row || !row->native_name_prompt_marker() || !identity.phase_() ||
       !qualify(identity.offer_.target(),summary,NativeSummary::Check::NameSubmission) || !identity.phase_())return false;
    // Suppliers observe only, without writes/yields/events. Recheck exact
    // generation/session/revision after both phase and actual issuer checks.
    return !connection->closing() && connection->verified_account_id()==identity.account_ &&
        !selection_queue_pending_ && published_summary_==identity.summary_ &&
        admission_->selected_account_offer_current(identity.offer_,Admission::Clock::now());
}
std::optional<SharedAccountSelection::NameIdentity> SharedAccountSelection::resolve_name_submission(
    const god2cn::CnSelectionNameSubmission& request,std::function<bool()> phase) {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN name identity game owner mismatch");
    const auto connection=connection_.lock();
    if(!phase || !request.matches_observed_ui_shape() || !published_summary_ || !published_ticket_ || selection_queue_pending_ ||
       !connection || connection->closing() || connection->role()!=Connection::Transport::Role::Account ||
       connection->verified_account_id()!=grant_.key.account)return std::nullopt;
    auto offer=admission_->selected_account_offer(*published_ticket_,connection->verified_account_id(),
        Admission::Clock::now());
    if(!offer || published_summary_->character_ids_!=offer->source().character_ids ||
       published_summary_->record_!=offer->source().adapter_record ||
       request.native_selection_ordinal()>=published_summary_->character_ids_.size())return std::nullopt;
    const auto ordinal=request.native_selection_ordinal();
    NameIdentity result(weak_from_this(),published_summary_,std::move(*offer),grant_.key.account,
        published_summary_->character_ids_[ordinal],ordinal,std::move(phase));
    if(!result.current())return std::nullopt;
    // Submitted raw name is not used to look up identity, normalize storage or
    // grant permission. Actual rule/source must prepare its common candidate.
    return result;
}
}
