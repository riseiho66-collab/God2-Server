#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582f client inventory memory projection, not a wire decoder or authority.
// 4C9AE0: WORD slot <=37, stride36, item WORD+4 nonzero -> record pointer.
// 4C72E0 separately updates slots0..49; this getter domain is not bag capacity.
struct CnBattleInventorySlot {
    static constexpr std::size_t record_size=0x24;
    static bool getter_slot_domain(std::uint16_t raw_slot) noexcept {return raw_slot<=0x25;}
    class Record {
    public:
        std::span<const std::uint8_t> raw_bytes() const noexcept {return bytes_;}
        std::uint8_t raw_quantity_byte() const noexcept {return bytes_[0];}
        // 54A9A0 scans only signed BYTE+0 >0; preserve the signed view exactly.
        std::int16_t raw_quantity_signed() const noexcept {
            return bytes_[0]<0x80?std::int16_t(bytes_[0]):std::int16_t(int(bytes_[0])-0x100);
        }
        std::uint16_t raw_item_word() const noexcept {
            return std::uint16_t(bytes_[4]) | (std::uint16_t(bytes_[5])<<8);
        }
    private:
        friend struct CnBattleInventorySlot;
        explicit Record(std::array<std::uint8_t,record_size> raw):bytes_(raw) {}
        std::array<std::uint8_t,record_size> bytes_;
    };
    // Copies a complete actual supplied memory-record projection. All other
    // bytes remain opaque; quantity/item do not prove custody/use/cost/grant.
    static std::optional<Record> read(std::span<const std::uint8_t> actual) {
        if(actual.size()!=record_size)return {};
        std::array<std::uint8_t,record_size> raw;
        std::copy(actual.begin(),actual.end(),raw.begin());
        return Record(raw);
    }
};
}
