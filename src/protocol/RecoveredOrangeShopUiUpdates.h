#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native OrangeShop-related UI updates. No BF purchase/result pairing is
// established by these independent consumer shapes.
struct RecoveredOrangeShopUiUpdates {
    static constexpr std::uint8_t quantity_opcode=0xef, record_opcode=0xf5;
    static constexpr std::size_t quantity_size=3, record_size=29;
    using Quantity=std::array<std::uint8_t,quantity_size>;
    using Record=std::array<std::uint8_t,record_size>;

    static std::optional<Quantity> decode_quantity(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=quantity_size || bytes[0]!=quantity_opcode)return {};
        Quantity out{};std::copy_n(bytes.begin(),quantity_size,out.begin());return out;
    }
    static std::uint16_t quantity_value(const Quantity& bytes) noexcept {
        return static_cast<std::uint16_t>(bytes[1] | (static_cast<std::uint16_t>(bytes[2])<<8));
    }
    static bool quantity_visible(const Quantity& bytes) noexcept {
        return quantity_value(bytes)!=0xffff;
    }
    static Quantity encode_quantity(std::uint16_t value) noexcept {
        return {quantity_opcode,static_cast<std::uint8_t>(value),
                static_cast<std::uint8_t>(value>>8)};
    }

    static std::optional<Record> decode_record(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=record_size || bytes[0]!=record_opcode)return {};
        Record out{};std::copy_n(bytes.begin(),record_size,out.begin());return out;
    }
    static std::uint16_t record_variant(const Record& bytes) noexcept {
        return static_cast<std::uint16_t>(bytes[1] | (static_cast<std::uint16_t>(bytes[2])<<8));
    }
    static bool known_record_variant(const Record& bytes) noexcept {
        return record_variant(bytes)==7 || record_variant(bytes)==8;
    }
    static std::optional<Record> encode_known_record(const Record& bytes) noexcept {
        if(bytes[0]!=record_opcode || !known_record_variant(bytes))return {};
        return bytes;
    }
};
}
