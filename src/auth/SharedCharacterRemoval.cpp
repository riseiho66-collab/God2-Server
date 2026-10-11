#include "auth/SharedCharacterRemoval.h"
#include <stdexcept>
#include <utility>

namespace god2 {
bool SharedCharacterRemoval::begin_observation(CommitObservation* observation,const RecoveredCharacter& expected) noexcept {
    if(!observation)return true;
    if(observation->state_!=CommitObservation::State::Unused)return false;
    // Consume before even the first observing presence/plan call. A refused or
    // throwing attempt must never make this exact object reusable.
    observation->state_=CommitObservation::State::Started;
    observation->account_=expected.account_id;observation->character_=expected.id;
    return true;
}
bool SharedCharacterRemoval::commit(SqliteRecoveredCharacterRepository& characters,
    SharedWorldAdmission& admission,const SharedCharacterRemovalPresence& presence,
    RecoveredCharacter expected,Current operation) {
    return commit_impl(characters,admission,presence,std::move(expected),std::move(operation),nullptr);
}
bool SharedCharacterRemoval::commit_observed(SqliteRecoveredCharacterRepository& characters,
    SharedWorldAdmission& admission,const SharedCharacterRemovalPresence& presence,
    RecoveredCharacter expected,Current operation,CommitObservation& observation) {
    return commit_impl(characters,admission,presence,std::move(expected),std::move(operation),&observation);
}
bool SharedCharacterRemoval::commit_impl(SqliteRecoveredCharacterRepository& characters,
    SharedWorldAdmission& admission,const SharedCharacterRemovalPresence& presence,
    RecoveredCharacter expected,Current operation,CommitObservation* observation) {
    if(!begin_observation(observation,expected))return false;
    if(!operation || !presence.owns_repository(characters))return false;
    // All plan allocations precede saved-state changes. This covers every TW/CN
    // grant for this common account/character, independent of wire name/slot.
    auto invalidation=admission.prepare_character_offer_invalidation(expected.account_id,expected.id);
    if(!invalidation)return false;
    const auto current=[&admission,&invalidation,&presence,&expected,&operation](Phase phase) {
        // Raw prepared/active occupancy is independent of SQL root existence.
        // Mandatory common gate for both adapters; native rule source remains
        // separate and cannot bypass occupancy by returning true.
        return admission.character_offer_invalidation_current(*invalidation) &&
            presence.unreserved(expected.account_id,expected.id) && operation(phase) &&
            presence.unreserved(expected.account_id,expected.id) &&
            admission.character_offer_invalidation_current(*invalidation);
    };
    if(!characters.erase_owned_snapshot(expected,current))return false;
    // The actual writer returned after successful COMMIT; no callback,
    // allocation or yield intervenes before this owned scalar fact.
    if(observation)observation->state_=CommitObservation::State::Committed;
    // No callback, allocation or serial-game yield between COMMIT and apply.
    // Preserve the world's exact ticket for native terminal drain/cleanup.
    if(!admission.apply_character_offer_invalidation(*invalidation))
        throw std::logic_error("Committed character removal lost its prepared offer invalidation");
    if(observation)observation->state_=CommitObservation::State::Invalidated;
    return true;
}
bool SharedCharacterRemoval::commit_with_native_summaries(SqliteRecoveredCharacterRepository& characters,
    SqliteNativeCharacterSummarySnapshotRepository& summaries,SharedWorldAdmission& admission,
    const SharedCharacterRemovalPresence& presence,RecoveredCharacter expected,
    std::vector<NativeCharacterSummarySnapshot> complete_expected,NativeSummaryCurrent operation) {
    return commit_with_native_summaries_impl(characters,summaries,admission,presence,std::move(expected),
        std::move(complete_expected),std::move(operation),nullptr);
}
bool SharedCharacterRemoval::commit_with_native_summaries_observed(SqliteRecoveredCharacterRepository& characters,
    SqliteNativeCharacterSummarySnapshotRepository& summaries,SharedWorldAdmission& admission,
    const SharedCharacterRemovalPresence& presence,RecoveredCharacter expected,
    std::vector<NativeCharacterSummarySnapshot> complete_expected,NativeSummaryCurrent operation,CommitObservation& observation) {
    return commit_with_native_summaries_impl(characters,summaries,admission,presence,std::move(expected),
        std::move(complete_expected),std::move(operation),&observation);
}
bool SharedCharacterRemoval::commit_with_native_summaries_impl(SqliteRecoveredCharacterRepository& characters,
    SqliteNativeCharacterSummarySnapshotRepository& summaries,SharedWorldAdmission& admission,
    const SharedCharacterRemovalPresence& presence,RecoveredCharacter expected,
    std::vector<NativeCharacterSummarySnapshot> complete_expected,NativeSummaryCurrent operation,CommitObservation* observation) {
    if(!begin_observation(observation,expected))return false;
    if(!operation || !presence.owns_repository(characters))return false;
    auto invalidation=admission.prepare_character_offer_invalidation(expected.account_id,expected.id);
    if(!invalidation)return false;
    const auto current=[&](Phase phase,std::span<const NativeCharacterSummarySnapshot> inventory,
        std::span<const RecoveredCharacter> roots) {
        return admission.character_offer_invalidation_current(*invalidation) &&
            presence.unreserved(expected.account_id,expected.id) && operation(phase,inventory,roots) &&
            presence.unreserved(expected.account_id,expected.id) &&
            admission.character_offer_invalidation_current(*invalidation);
    };
    if(!characters.erase_owned_snapshot_with_native_summaries(expected,summaries,std::move(complete_expected),current))return false;
    if(observation)observation->state_=CommitObservation::State::Committed;
    // Prepared allocations only; synchronous game owner does not yield here.
    if(!admission.apply_character_offer_invalidation(*invalidation))
        throw std::logic_error("Committed summary removal lost its prepared character offer invalidation");
    if(observation)observation->state_=CommitObservation::State::Invalidated;
    return true;
}
}
