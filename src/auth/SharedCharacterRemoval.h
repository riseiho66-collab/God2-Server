#pragma once
#include "auth/SharedWorldAdmission.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "auth/SharedCharacterRemovalPresence.h"
#include <cstdint>

namespace god2 {
// Common SQL/offer coordination only. Not a native permission,19 handler,
// replay receipt or response issuer. Run on the serial game owner; required
// current-operation predicates observe rules/online leases without yielding.
class SharedCharacterRemoval {
public:
    // One process-local observation of an actual call, not permission, native
    // success, client receipt or durable replay/recovery. No public reset or
    // copy/move: false/throw attempts consume this same observing object too.
    class CommitObservation {
        friend class SharedCharacterRemoval;
    public:
        CommitObservation()=default;
        CommitObservation(const CommitObservation&)=delete;
        CommitObservation& operator=(const CommitObservation&)=delete;
        CommitObservation(CommitObservation&&)=delete;
        CommitObservation& operator=(CommitObservation&&)=delete;
        bool attempted() const noexcept {return state_!=State::Unused;}
        bool storage_committed() const noexcept {return state_==State::Committed || state_==State::Invalidated;}
        bool offers_invalidated() const noexcept {return state_==State::Invalidated;}
        std::uint64_t account() const noexcept {return account_;}
        std::uint64_t character() const noexcept {return character_;}
    private:
        enum class State {Unused,Started,Committed,Invalidated};
        State state_=State::Unused;
        std::uint64_t account_=0,character_=0;
    };
    using Phase=SqliteRecoveredCharacterRepository::RemovalPhase;
    using Current=SqliteRecoveredCharacterRepository::CurrentRemoval;
    static bool commit(SqliteRecoveredCharacterRepository&,SharedWorldAdmission&,
                       const SharedCharacterRemovalPresence&,
                       RecoveredCharacter expected,Current actual_operation);
    using NativeSummaryCurrent=SqliteRecoveredCharacterRepository::CurrentNativeSummaryRemoval;
    // Actual issuer explicitly authorizes invalidation of ALL stored account
    // delivery scopes. Same DB transaction as root deletion; same prepared
    // character-offer invalidation after COMMIT. Not general summary CAS
    // invalidation of every issued account/world offer or a native handler.
    static bool commit_with_native_summaries(SqliteRecoveredCharacterRepository&,
        SqliteNativeCharacterSummarySnapshotRepository&,SharedWorldAdmission&,
        const SharedCharacterRemovalPresence&,RecoveredCharacter,
        std::vector<NativeCharacterSummarySnapshot> complete_expected,NativeSummaryCurrent);
    // Explicit observing entries. Writer return true immediately records the
    // actual COMMIT before prepared offer application can return false/throw.
    // Existing bool-only callers keep their original behavior and exceptions.
    static bool commit_observed(SqliteRecoveredCharacterRepository&,SharedWorldAdmission&,
        const SharedCharacterRemovalPresence&,RecoveredCharacter,Current,CommitObservation&);
    static bool commit_with_native_summaries_observed(SqliteRecoveredCharacterRepository&,
        SqliteNativeCharacterSummarySnapshotRepository&,SharedWorldAdmission&,
        const SharedCharacterRemovalPresence&,RecoveredCharacter,
        std::vector<NativeCharacterSummarySnapshot>,NativeSummaryCurrent,CommitObservation&);
private:
    static bool begin_observation(CommitObservation*,const RecoveredCharacter&) noexcept;
    static bool commit_impl(SqliteRecoveredCharacterRepository&,SharedWorldAdmission&,
        const SharedCharacterRemovalPresence&,RecoveredCharacter,Current,CommitObservation*);
    static bool commit_with_native_summaries_impl(SqliteRecoveredCharacterRepository&,
        SqliteNativeCharacterSummarySnapshotRepository&,SharedWorldAdmission&,
        const SharedCharacterRemovalPresence&,RecoveredCharacter,
        std::vector<NativeCharacterSummarySnapshot>,NativeSummaryCurrent,CommitObservation*);
};
}
