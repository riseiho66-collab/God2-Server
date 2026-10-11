#pragma once
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace god2cn {
struct CnSelectionNativeNameBuffer {
    std::uint32_t native_buffer_word; // Actual source identifier, never dereferenced.
    std::vector<std::uint8_t> bytes; // Actual256-byte allocation for active names.
};
struct CnSelectionFilenameOperand {
    enum class Kind {ExistingName,LoadRequired,CapacityUnqualified};
    Kind kind;
    std::uint64_t owner_revision;
    std::uint32_t native_rom_bank_word;
    std::uint32_t slot_operand;
};
// CN00445040's separate selection pool and00446740's filename lookup.
// Actual native-owner snapshots only; not a constructor, allocator, native
// pointer reader, ROM handle, metadata bank or recovered success issuer.
class CnSelectionFilenameCacheSnapshot {
public:
    struct Scope {
        std::uint32_t ui_owner_word,filename_pool_word,rom_bank_word,ascii_compare_flag_source_word;
        std::uint64_t revision;
        bool operator==(const Scope&) const=default;
    };
    // Observes the actual UI/pool/bank/CRT comparator flag and supplied buffer lifetime/revision;
    // no writes, yields, event pumping, borrowed temporary captures or default
    // true predicate. Independent from in-world NPC cache revisions/contexts.
    using Current=std::function<bool(const Scope&)>;
    static std::optional<CnSelectionFilenameCacheSnapshot> read_native_owner(
        std::uint32_t actual_ui_owner_word,std::uint32_t actual_filename_pool_word,
        std::span<const std::uint8_t> actual_ui_bytes,
        std::span<const std::uint8_t> actual_pool_bytes,
        const std::vector<CnSelectionNativeNameBuffer>& actual_ordered_buffers,
        std::uint32_t actual_ascii_compare_flag_source_word,
        std::span<const std::uint8_t> actual_ascii_compare_flag_bytes,
        std::uint64_t owner_revision,Current);
    const Scope& scope() const noexcept {return scope_;}
    std::uint32_t current_count() const noexcept {return count_;}
    std::uint32_t allocated_capacity() const noexcept {return capacity_;}
    std::uint32_t preload_count() const noexcept {return preload_;}
    //00446740 compares the FULL original requested name, first match among
    // [0,current_count). Requires actual CRT flag009FA544=0, the original
    // ASCII fastpath: bytewise A..Z folding, all other bytes unchanged. The
    // locale fallback/canonicalization remain open. A hit is a slot operand,
    // never proof the ROM/ACT is loaded. A miss does not increment the count.
    std::optional<CnSelectionFilenameOperand> probe_native_filename(std::string_view) const;
    //00443080/004405F0 restore count=preload with allocator checkpoint0.
    // Read-only operand, no restoration, zero initialization or ROM deletion.
    std::optional<std::uint32_t> restore_preload_count_operand() const;
    bool current() const;
private:
    CnSelectionFilenameCacheSnapshot(Scope,std::uint32_t,std::uint32_t,std::uint32_t,
        std::vector<std::string>,Current);
    Scope scope_;
    std::uint32_t count_,capacity_,preload_;
    std::vector<std::string> active_names_;
    Current current_;
};
}
