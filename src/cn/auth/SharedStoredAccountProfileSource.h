#pragma once
#include "cn/auth/SharedIssuedAccountSource.h"
#include "db/NativeAccountSnapshotRepository.h"
#include <functional>
#include <memory>
#include <utility>

namespace god2::cn {
// Real common persisted snapshot -> existing native1D/0A assembler. Reading
// bytes/provenance is not authority; actual rights/catalog/deadline observers
// remain mandatory and cannot be replaced by an always-true storage predicate.
class SharedStoredAccountProfileSource {
public:
    using Native=SharedAccountSuccess::NativeData;
    using Profile=SharedIssuedAccountSource::Profile;
    struct Plan {
        SharedWorldAdmission::Clock::time_point deadline;
        std::vector<god2cn::CnAccountReplies::CatalogGroup> catalog;
        SharedAccountSelection::SummarySource summaries;
        std::optional<SharedAccountSelection::NameSources> naming;
        std::shared_ptr<SharedWorldPreparation> naming_preparation;
        std::optional<SharedAccountDirectorySource::Plan> directory;
    };
    // No password/credential/Login is passed to plan preparation.
    // The snapshot is complete owned data; callbacks do not retain references,
    // write/yield/pump events or send output. Existing issuer checks full plan.
    using Prepare=std::function<std::optional<Plan>(const Native::Scope&,const NativeAccountSnapshot&)>;
    // Retain the actual managed listener/config owners at construction, but do
    // not observe or prepare until an account request on this same game owner.
    // Qualify the actual provider's complete directory without inventing fields.
    // Directory-only plans keep their original object in the returned Plan;
    // existing issuer/composition checks and publication binding still apply.
    static Prepare with_active_directory(Prepare actual_prepare,
        std::shared_ptr<const SharedListenerRegistry> listeners,
        std::shared_ptr<const god2cn::CnClientGroupConfiguration> client_groups);
    using Authority=std::function<bool(const NativeAccountSnapshot&,const Profile::Scope&,
        Native::Check,const Native::Observation&)>;
    struct Config {
        std::reference_wrapper<NativeAccountSnapshotRepository> snapshots;
        Prepare prepare;
        Authority authority;
        Config(NativeAccountSnapshotRepository& repository,Prepare plan,Authority current)
            :snapshots(repository),prepare(std::move(plan)),authority(std::move(current)) {}
    };
    // Bound by composition to actual Context.accounts. Uses fixed CN profile,
    // exact40+16 stored bytes; missing/malformed/stale never becomes success.
    // Same serial game owner and repository lifetime through transport drain.
    static SharedIssuedAccountSource::Prepare create(AccountRepository&,Config);
};
}
