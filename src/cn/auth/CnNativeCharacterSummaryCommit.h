#pragma once
#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"

namespace god2 {class SqliteDatabase;}
namespace god2::cn {
// Explicit own-server materialization of real issuer output, not a client
// command, guessed native producer, default migration or success response.
class CnNativeCharacterSummaryCommit final {
public:
    using Snapshot=NativeCharacterSummarySnapshot;
    using Issuer=SqliteNativeCharacterSummarySnapshotRepository::Issuer;
    class Plan {
    public:
        // Entire actual75-byte07 and ordered common IDs/name modes, with
        // optional actual25-byteCN22/revision/origin. Native shape is checked;
        // real rights/visibility/revision/operation source remains mandatory.
        static std::optional<Plan> from_actual_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer);
        Plan(const Plan&)=delete;
        Plan& operator=(const Plan&)=delete;
        Plan(Plan&&) noexcept=default;
        Plan& operator=(Plan&&)=delete;
    private:
        friend class CnNativeCharacterSummaryCommit;
        Plan(std::optional<Snapshot>,Snapshot,Issuer);
        std::optional<Snapshot> expected_;
        Snapshot next_;
        Issuer issuer_;
    };
    // Same migrated Application database reader/writer, own atomic transaction.
    // No schema install/data defaults. Nullopt is no COMMIT, not native failure
    // serialization. Successful storage COMMIT is not client ACK/acceptance,
    // active login or automatic account/world offer invalidation.
    static std::optional<Snapshot> commit_actual_source(SqliteDatabase&,Plan);
};
}
