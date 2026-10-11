#pragma once
#include "db/SqliteNativeAccountSnapshotRepository.h"

namespace god2 {class SqliteDatabase;}
namespace god2::cn {
// Explicit own-server materialization of actual account issuer output. This
// does not implement native rights, login serialization, keys or a client ACK.
class CnNativeAccountSnapshotCommit final {
public:
    using Snapshot=NativeAccountSnapshot;
    using Issuer=SqliteNativeAccountSnapshotRepository::Issuer;
    class Plan {
    public:
        // Complete supplied account/build/revision/origin/metadata40/billing16
        // tuple and real issuer. No generated revision or default native data.
        static std::optional<Plan> from_actual_issuer(std::optional<Snapshot> expected,Snapshot next,Issuer);
        Plan(const Plan&)=delete;
        Plan& operator=(const Plan&)=delete;
        Plan(Plan&&) noexcept=default;
        Plan& operator=(Plan&&)=delete;
    private:
        friend class CnNativeAccountSnapshotCommit;
        Plan(std::optional<Snapshot>,Snapshot,Issuer);
        std::optional<Snapshot> expected_;
        Snapshot next_;
        Issuer issuer_;
    };
    // Same migrated Application account reader/writer, own atomic fulltuple CAS.
    // No schema install, automatic snapshot mutation or grant invalidation.
    // Nullopt means no COMMIT; storage COMMIT is not native ACK/acceptance,
    // issuer authority recovery, login activation or a client success reply.
    static std::optional<Snapshot> commit_actual_source(SqliteDatabase&,Plan);
};
}
