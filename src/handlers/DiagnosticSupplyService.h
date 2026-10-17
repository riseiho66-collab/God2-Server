#pragma once
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/NativeSupplyCatalog.h"
#include "game/BattleNumericProfile.h"
#include "scripting/LuaEngine.h"
#include <functional>
#include <span>
#include <vector>

namespace god2 {
// CUSTOM-0016. Trusted game-executor admission only, not a network/session router.
// Caller must establish world-ready ownership and catalog eligibility before use.
// Uses native26 layout only. Caller must prove target-to-owned-character mapping;
// a matching raw word alone is not ownership proof. The diagnostic route and
// separately qualified CUSTOM-0050 owner route share this atomic boundary.
class DiagnosticSupplyService {
public:
    struct Policy {
        std::uint16_t item_id;
        std::uint16_t expected_target;
        std::string source_sha256;
        std::uint64_t restore_hp;
        std::uint32_t restore_mp;
        BattleNumericProfile numeric_profile{BattleNumericProfile::LegacyCustom};
        // Trusted logical projection only: no send, persist or reentry. It must
        std::function<std::vector<std::uint8_t>(std::uint8_t,
            const StoredInventorySlot&,const CharacterResources&)> projector{};
    };
    struct Result {
        bool consumed{};
        std::vector<std::uint8_t> wire;
        std::optional<CharacterResources> resources;
    };
    // Current MED02 lines6354/6360: native text amounts, custom consumption/caps.
    // Two-record fallback when the pinned MED02 declaration catalog is absent.
    static std::optional<Policy> current_supply_policy(std::uint16_t item, std::uint16_t target);
    // Source-backed text amount, with the same CUSTOM-0016 consumption/cap rule.
    static std::optional<Policy> native_declared_policy(const NativeSupplyCatalog& catalog,
        std::uint16_t item,std::uint16_t target);
    DiagnosticSupplyService(SqliteRecoveredCharacterRepository& repository, LuaEngine& lua)
        : repository_(repository), lua_(lua) {}
    // Baselines are server-held snapshots, never supplied by the client.
    Result use(std::uint64_t account, std::uint64_t character,
        std::span<const std::uint8_t> logical, const Policy& policy,
        const StoredInventorySlot& expected_slot, const CharacterResources& expected_resources);
private:
    SqliteRecoveredCharacterRepository& repository_;
    LuaEngine& lua_;
};
}
