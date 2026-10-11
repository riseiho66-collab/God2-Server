#pragma once
#include "db/NativeWorldEntrySnapshotRepository.h"
#include "protocol/RecoveredTaiwanDeityEquipmentState.h"
#include <utility>

namespace god2 {
class SqliteOwnedInventoryRepository;
// Full owner-local versioned observation. No deity row ID is decoded or
// inferred from D1/D2; current selected-deity lineage/real issuance remain open.
class NativeDeityEquipmentObservation final {
public:
    static constexpr const char* client_pin="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    static constexpr const char* kind="tw149c-deity-d1d2-ownerlocal-v1";
    const NativeWorldEntrySnapshot& snapshot() const noexcept{return snapshot_;}
    const RecoveredTaiwanDeityEquipmentState::Pair& records() const noexcept{return records_;}
    bool operator==(const NativeDeityEquipmentObservation&) const=default;
private:
    friend class SqliteOwnedInventoryRepository;
    NativeDeityEquipmentObservation(NativeWorldEntrySnapshot snapshot,
        RecoveredTaiwanDeityEquipmentState::Pair records)
        :snapshot_(std::move(snapshot)),records_(records) {}
    NativeWorldEntrySnapshot snapshot_;
    RecoveredTaiwanDeityEquipmentState::Pair records_;
};
}
