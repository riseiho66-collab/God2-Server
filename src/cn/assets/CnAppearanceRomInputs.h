#pragma once
#include "cn/assets/CnAppearanceResources.h"
#include "cn/assets/CnRomAsset.h"
#include <array>
#include <cstddef>
#include <optional>

namespace god2cn {
struct CnAppearanceRomInput {
    CnSelectedResource selected; // Exact original path/bytes after004197E0 selection.
    CnRomAsset metadata; // Owned immutable decoded records, not a native ROM slot.
};
// Selection preview has four HeroDoll resources and its own native cache
// owner. It cannot borrow the in-world NPC two-cache bank or a driver0 ROM.
class CnSelectionAppearanceRomInputs {
public:
    static CnSelectionAppearanceRomInputs read(CnSelectionAppearanceRows,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    const auto& rows() const noexcept {return rows_;}
    const auto& parts() const noexcept {return parts_;}
private:
    CnSelectionAppearanceRomInputs(CnSelectionAppearanceRows,std::array<CnAppearanceRomInput,4>);
    CnSelectionAppearanceRows rows_;
    std::array<CnAppearanceRomInput,4> parts_;
};
// Actual full source record ->actual CSV rows ->each actual selected ROM input.
// Do not coalesce equal filenames: native HeroDoll caches are per row, and
// load order/ACTINDEX/current ROM bank may change command10 references.
// No slot/counter/cache/native allocator/cross-ROM rewrite/rendering authority.
class CnAppearanceRomInputs {
public:
    static CnAppearanceRomInputs read(CnAppearanceRowSelection,
        std::size_t max_encoded_bytes,std::size_t max_plain_bytes);
    const auto& rows() const noexcept {return rows_;}
    const auto& parts() const noexcept {return parts_;}
    const auto& driver() const noexcept {return driver_;}
    bool auxiliary_resource_prepared() const noexcept {return false;}
private:
    CnAppearanceRomInputs(CnAppearanceRowSelection,std::array<CnAppearanceRomInput,4>,
        std::optional<CnAppearanceRomInput>);
    CnAppearanceRowSelection rows_;
    std::array<CnAppearanceRomInput,4> parts_;
    std::optional<CnAppearanceRomInput> driver_;
};
}
