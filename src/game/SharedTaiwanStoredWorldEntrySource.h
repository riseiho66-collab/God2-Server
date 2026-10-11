#pragma once
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "game/SharedTaiwanWorldEntrySource.h"
#include <string>

namespace god2 {
class SharedTaiwanStoredWorldEntrySource {
public:
    using Scope=SharedTaiwanWorldEntrySource::Scope;
    using Frame=SharedTaiwanWorldEntrySource::Frame;
    using Snapshot=NativeWorldEntrySnapshot;
    enum class Check {Supply,Current};
    // Real complete native producer/provenance/resource/phase qualification.
    // Geometry and storage freshness alone never establish all opaque fields.
    // Pure synchronous observer; no SQL writes, yields, pump or borrowed captures.
    using Qualify=std::function<bool(const Snapshot&,const Scope&,const Frame&,Check)>;
    static constexpr const char* record_kind="tw.world-entry.2a.zero-seed";
    // Borrowed repositories/catalog, owned immutable snapshots and shared guard.
    // Actual database and catalogs must outlive EVERY Source/Native/Current;
    // drain all copied closures before destroying their database. This API
    // does not create fake shared ownership of a borrowed Database/Context.
    // Build digest supplied explicitly; no historical/current-client default.
    static SharedTaiwanWorldEntrySource::NativeSource create(NativeWorldEntrySnapshotRepository&,
        RecoveredCharacterRepository&,const NativeMapCatalog&,std::string client_sha256,Qualify);
};
}
