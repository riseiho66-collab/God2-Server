#pragma once
#include "db/SqliteRecoveredCharacterRepository.h"
#include "protocol/RecoveredTeleportGem.h"
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace god2 {
struct StoredTeleportGemSlot {
    std::uint8_t slot{};
    std::uint16_t item_id{};
    std::uint8_t count{};
    std::uint64_t revision{};
    RecoveredTeleportGem::Metadata metadata20{};
    bool metadata_present{};
    std::string origin,provenance;
    bool operator==(const StoredTeleportGemSlot&) const = default;
};
struct TeleportGemTransfer {
    StoredTeleportGemSlot before,after;
    RecoveredPosition position_before,position_after;
};
struct TeleportGemMove {StoredTeleportGemSlot source,destination;};

// CUSTOM-0057: owned instance persistence and one-charge town return policy.
// No acquisition/provisioning; an existing16055 scalar alone cannot establish
// charges. Every operation rejects weapon overlays and unknown occupied cells.
class SqliteTeleportGemRepository {
public:
    using PrepareTransfer=std::function<void(const TeleportGemTransfer&)>;
    using PrepareMove=std::function<void(const TeleportGemMove&)>;
    static constexpr const char* source_sha256="70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731";
    explicit SqliteTeleportGemRepository(sqlite3* db);
    static std::string schema();
    // Missing/other scalar -> absent; explicit empty scalar -> empty slot;
    // gem with missing/corrupt metadata or any weapon overlay -> error.
    std::optional<StoredTeleportGemSlot> load(std::uint64_t account,std::uint64_t character,std::uint8_t slot);
    // Project only saved full-instance evidence. Legacy16055 scalars without
    // an overlay are left untouched/unprojected, never granted inferred charges.
    std::vector<StoredTeleportGemSlot> load_saved(std::uint64_t account,std::uint64_t character);
    // Attach qualified full20 evidence to an ALREADY owned16055/count1 scalar.
    // Scalar occupancy/revision is unchanged. Existing metadata cannot be reset.
    StoredTeleportGemSlot save_existing(std::uint64_t account,std::uint64_t character,std::uint8_t slot,
        const StoredInventorySlot& expected,const RecoveredTeleportGem::Metadata& metadata,
        const std::string& origin,const std::string& provenance);
    // Atomic scalar+metadata charge debit AND position CAS. Source must be2/0;
    // fixed destination2/4/56/75, position revision+1. CUSTOM-0057 exhausts a
    // one-charge instance by clearing its scalar and deleting its overlay.
    // prepare must encode all output before COMMIT; any exception rolls back.
    TeleportGemTransfer prepare_transfer(std::uint64_t account,std::uint64_t character,
        const StoredTeleportGemSlot& expected,const RecoveredPosition& position,const PrepareTransfer& prepare);
    // Existing bag cells only, occupied gem source, empty/gem destination.
    // Complete metadata/provenance follows the instance; each cell advances CAS.
    TeleportGemMove move_whole(std::uint64_t account,std::uint64_t character,
        const StoredTeleportGemSlot& source,const StoredTeleportGemSlot& destination,const PrepareMove& prepare);
private:
    sqlite3* db_;
    void owner(std::uint64_t account,std::uint64_t character);
    void no_pending_battle(std::uint64_t character);
    void no_weapon_overlay(std::uint64_t character,std::uint8_t slot);
    std::optional<StoredTeleportGemSlot> read(std::uint64_t character,std::uint8_t slot);
    RecoveredPosition position(std::uint64_t character);
    void write(std::uint64_t character,const StoredTeleportGemSlot& before,const StoredTeleportGemSlot& after);
};
}
