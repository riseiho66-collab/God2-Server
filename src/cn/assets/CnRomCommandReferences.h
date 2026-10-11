#pragma once
#include "cn/assets/CnRomAsset.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <vector>

namespace god2cn {
class CnAppearanceCacheSnapshot;
// Read-only projection of00417620 using an actual owner-supplied bank snapshot.
// Default slots are UNKNOWN. initialized_empty means the native owner actually
// proved identityFFFFFFFF/action-count0; it never initializes an absent bank.
struct CnRomBankSlotSource {
    enum class Kind {Unknown,InitializedEmpty,Loaded};
    Kind kind=Kind::Unknown;
    const CnRomAsset* metadata=nullptr; // Immutable actual loaded source, owner retained.
    static CnRomBankSlotSource initialized_empty() noexcept {return {Kind::InitializedEmpty,nullptr};}
    static CnRomBankSlotSource loaded(const CnRomAsset& asset) noexcept {return {Kind::Loaded,&asset};}
};
struct CnRomBankSourceView {
    std::uint64_t owner_revision=0;
    std::uint8_t native_context=0xff; // Qualified NPC appearance two-cache context0/1 only.
    std::uint16_t current_slot=0xffff;
    std::uint32_t native_bank_source_word=0; // Actual owner-layout bank ID, never dereferenced here.
    std::array<CnRomBankSlotSource,512> slots{};
    // Actual non-yielding source/lifetime/context observation, before/after.
    // No default true predicate, fabricated bank, save, send or event pumping.
    std::function<bool()> current;
};
struct CnRomCommandStepProjection {
    std::size_t action_ordinal,step_ordinal;
    std::vector<std::uint8_t> bytes; // Complete owned step including untouched tail.
};
struct CnRomCommandProjection {
    std::uint64_t bank_owner_revision;
    std::uint8_t native_context;
    std::uint16_t source_slot;
    std::vector<CnRomCommandStepProjection> steps;
};
class CnRomCommandReferences {
public:
    // Source must be the bank's exact current-slot metadata. Unknown earlier
    // lookup/target slots or unbounded unterminated native steps are unqualified.
    // Full proven no-match keeps original >1000 ref; slot>=512 keeps action ref.
    // Does not mutate raw assets, cache/counter/native ACTs or execute commands.
    static std::optional<CnRomCommandProjection> project(const CnRomAsset&,const CnRomBankSourceView&);
    // Explicit stronger path: actual selected two-cache bank and same owner
    // revision/current observation before/after the existing source projection.
    // Previous no-cache-witness API retains its narrower source-only scope.
    static std::optional<CnRomCommandProjection> project(const CnRomAsset&,const CnRomBankSourceView&,
        const CnAppearanceCacheSnapshot& actual_cache);
};
}
