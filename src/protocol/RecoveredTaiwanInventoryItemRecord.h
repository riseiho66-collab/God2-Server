#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace god2 {
// Same149c S3B498DD0 data prefix: complete20 at logical+5 -> row+4.
// Incoming count is NOT absolute (definition flag/add/signed clamp). Preserve
// opaque WORD explicitly; no default0 or inferred quantity/ownership/rules.
struct RecoveredTaiwanInventoryItemRecord {
    using Instance=std::array<std::uint8_t,20>;
    using LogicalRecord=std::array<std::uint8_t,25>;
    struct Fields {
        std::uint8_t incoming_count,slot;
        std::uint16_t opaque;
        Instance instance;
        Fields(std::uint8_t count,std::uint8_t actual_slot,std::uint16_t actual_opaque,Instance full_instance)
            :incoming_count(count),slot(actual_slot),opaque(actual_opaque),instance(full_instance) {}
    };
    static std::optional<LogicalRecord> encode(const Fields& fields) noexcept {
        if(fields.slot>=50)return std::nullopt;
        LogicalRecord result{0x3b,fields.incoming_count,fields.slot,
            static_cast<std::uint8_t>(fields.opaque),static_cast<std::uint8_t>(fields.opaque>>8)};
        for(std::size_t i=0;i<fields.instance.size();++i)result[i+5]=fields.instance[i];
        return result;
    }
};
}
