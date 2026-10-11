#pragma once
#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <span>

namespace god2cn {
struct CnAppearanceCacheContext {
    std::uint32_t native_bank_word;
    std::uint16_t current_cursor,base_cursor,family_word,map_word;
};
struct CnAppearanceCacheSwitchSource {
    std::uint64_t owner_revision;
    std::uint8_t context;
    std::uint32_t native_bank_word;
    std::uint16_t cursor_after,family_word,map_word;
    bool cache_hit,restore_checkpoint0;
};
// CN582f2695 native004826C0/00482F40 owner layout. Reads an explicitly
// supplied actual owner snapshot; no process access, pointer dereference,
// constructor/allocator execution or native bank created from metadata.
class CnAppearanceCacheSnapshot {
public:
    using Current=std::function<bool()>;
    // Required real owner observation in the same revision domain as the bank
    // source. No default zeros, guessed empty banks or constant-true supplier.
    static std::optional<CnAppearanceCacheSnapshot> read_native_owner(
        std::span<const std::uint8_t> actual_owner_bytes,std::uint64_t owner_revision,Current);
    const auto& contexts() const noexcept {return contexts_;}
    std::int32_t active_context() const noexcept {return active_;}
    std::uint64_t owner_revision() const noexcept {return revision_;}
    // Read-only original selection/cursor operands; not a cache mutation or
    // proof checkpoint/resource/ACT loads succeeded. Miss preserves bank slots.
    std::optional<CnAppearanceCacheSwitchSource> switch_source(std::uint16_t family,std::uint16_t map) const;
    bool selected_bank_current(std::uint8_t context,std::uint32_t native_bank_word,std::uint64_t owner_revision) const;
private:
    CnAppearanceCacheSnapshot(std::array<CnAppearanceCacheContext,2>,std::int32_t,std::uint64_t,Current);
    std::array<CnAppearanceCacheContext,2> contexts_;
    std::int32_t active_;
    std::uint64_t revision_;
    Current current_; // Actual immutable-byte/current-owner lifetime, non-yielding.
};
}
