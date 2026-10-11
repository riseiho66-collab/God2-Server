#pragma once
#include "cn/auth/SharedCommonCharacterSummarySource.h"
#include "db/NativeCharacterSummarySnapshotRepository.h"
#include <functional>
#include <utility>

namespace god2::cn {
// Actual persisted issuer output -> existing full07/common-name projection.
// Storage existence/provenance never supplies visibility, rights or rules.
class SharedStoredCharacterSummarySource {
public:
    using Common=SharedCommonCharacterSummarySource;
    using Snapshot=NativeCharacterSummarySnapshot;
    using Authority=std::function<bool(const Snapshot&,const Common::Scope&,
        Common::Summary::Check,const Common::NativeMetadata::Observation&)>;
    struct Config {
        std::reference_wrapper<NativeCharacterSummarySnapshotRepository> snapshots;
        Authority authority;
        Config(NativeCharacterSummarySnapshotRepository& source,Authority current)
            :snapshots(source),authority(std::move(current)) {}
    };
    // Required exact common repositories/real observer. No schema installation,
    // data production/import or default record, row, level, visibility or flags.
    // Returned prepare is used inside existing Common::create on the game owner;
    // repositories must outlive account/controller/transport drain.
    static Common::Prepare create(AccountRepository&,RecoveredCharacterRepository&,Config);
};
}
