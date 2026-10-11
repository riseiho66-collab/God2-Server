#pragma once
#include "cn/assets/CnCurrentEnemyDisplayCatalog.h"
#include <array>
#include <functional>
#include <optional>

namespace god2::cn {
// Conditional primary WORLD71 display preparation. No common monster/spawn/
// combat authority, receiver pool mutation, wire publication or Application
// hosting is supplied. Existing IDs do not replace appearance in the native
// constructors; this projection must not be mistaken for an actor allocator.
struct CnWorldMonsterDisplay {
    using Wire=god2cn::CnWorldMonster;
    using Catalog=god2cn::CnCurrentEnemyDisplayCatalog;
    struct Resources {
        std::uint64_t revision{};
        // Mandatory real receiver/resource state qualification, not server PE
        // presence. Catalog and model-cache revisions must remain current.
        std::function<bool(const Catalog::Resource&,std::uint64_t)> current;
        // 004829D0 first, then004828F0 (which can load the actual model cache).
        std::function<std::optional<std::uint16_t>(std::uint8_t)> single_auxiliary;
        std::function<std::optional<std::uint16_t>(std::uint8_t)> single_model;
        // Actual00483C10(5,1,parts,handles), including native missing resources.
        std::function<std::optional<std::array<std::int16_t,4>>(
            const std::array<std::uint16_t,4>&)> composite_models;
    };
    struct Projection {
        Wire::Record original_wire,native_consumed;
        Catalog::Appearance appearance;
        std::uint64_t catalog_revision,model_revision;
        std::optional<std::uint16_t> single_model,single_auxiliary;
        std::optional<std::array<std::int16_t,4>> composite_models;
        // color_selector_raw remains presentation, not a five-element value.
        std::uint8_t effective_native_color_slot() const noexcept {
            const auto value=appearance.color_selector_raw();return value<5?value:0;
        }
    };
    static std::optional<Projection> prepare(const Wire::Record& record,
        Catalog::Resource catalog,Resources resources);
};
}
