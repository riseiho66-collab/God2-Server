#pragma once
#include "db/NativeSkillCatalog.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <span>
#include <vector>

namespace god2 {
// Immutable definition-source material for explicit installed453 import only.
// Full owned bytes are independently pinned before any caller can reach SQL.
// This is not live filesystem/native Current, learned rights or cast authority.
class TaiwanInstalledSkillCatalogSource final {
public:
    static constexpr std::size_t file_bytes=112660,record_bytes=110,group_bytes=0x6e04,record_count=453;
    inline static constexpr std::array<std::uint32_t,4> declared_counts{126,129,87,111};
    // Own the supplied complete plain file, then validate its whole SHA/header,
    // all four declared banks and every eager raw row/hash/ordinal/offset.
    // Invalid bytes or an unavailable digest provider return null. No callbacks.
    static std::shared_ptr<const TaiwanInstalledSkillCatalogSource> read_actual_source(
        std::span<const std::uint8_t>);
    TaiwanInstalledSkillCatalogSource(const TaiwanInstalledSkillCatalogSource&)=delete;
    TaiwanInstalledSkillCatalogSource& operator=(const TaiwanInstalledSkillCatalogSource&)=delete;
    TaiwanInstalledSkillCatalogSource(TaiwanInstalledSkillCatalogSource&&)=delete;
    TaiwanInstalledSkillCatalogSource& operator=(TaiwanInstalledSkillCatalogSource&&)=delete;
    const NativeSkillSource& source() const noexcept {return source_;}
    std::span<const NativeSkillRecord> records() const noexcept {return {records_.data(),records_.size()};}
    std::span<const std::uint8_t> retained_bytes() const noexcept {return {bytes_.data(),bytes_.size()};}
private:
    TaiwanInstalledSkillCatalogSource(NativeSkillSource,std::vector<NativeSkillRecord>,
        std::vector<std::uint8_t>);
    const NativeSkillSource source_;
    const std::vector<NativeSkillRecord> records_;
    const std::vector<std::uint8_t> bytes_;
};
}
