#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current client F6360/F6DF0/F7090/F72B0. Native wire/UI contract only;
// this does not authorize a destination, price, cooldown or position change.
struct RecoveredTeleport {
    struct Destination {
        std::uint8_t id{}, opaque{};
        std::uint16_t displayed_cost{};
        bool operator==(const Destination&) const = default;
    };
    struct Menu {
        std::uint16_t context{}, message_id{};
        std::uint8_t count_flags{}, minutes{}, level{}, opaque{};
        std::array<Destination,5> destinations{};
        bool operator==(const Menu&) const = default;
    };
    struct Selection {
        std::uint8_t opcode{};
        std::uint16_t context{};
        std::uint8_t destination{}, opaque_tail{};
        bool operator==(const Selection&) const = default;
    };
    using MenuBytes = std::array<std::uint8_t,29>;
    using SelectionBytes = std::array<std::uint8_t,5>;
    static constexpr bool special_context(std::uint16_t value) {
        return value>=0x61e && value<=0x622;
    }
    static constexpr std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t at) {
        return static_cast<std::uint16_t>(bytes[at]+256u*bytes[at+1]);
    }
    static constexpr bool valid(const Menu& value) {
        const auto count=value.count_flags&0x7f;
        if(count>value.destinations.size()) return false;
        for(std::size_t i=0;i<count;++i)
            if(value.destinations[i].id>5) return false; // six native label pointers
        return true;
    }
    static constexpr std::optional<MenuBytes> encode(const Menu& value) {
        if(!valid(value)) return std::nullopt;
        MenuBytes out{0x6d,static_cast<std::uint8_t>(value.context),
            static_cast<std::uint8_t>(value.context>>8),static_cast<std::uint8_t>(value.message_id),
            static_cast<std::uint8_t>(value.message_id>>8),value.count_flags,value.minutes,value.level,value.opaque};
        for(std::size_t i=0;i<5;++i) {
            const auto& row=value.destinations[i];const auto at=9+4*i;
            out[at]=row.id;out[at+1]=row.opaque;
            out[at+2]=static_cast<std::uint8_t>(row.displayed_cost);
            out[at+3]=static_cast<std::uint8_t>(row.displayed_cost>>8);
        }
        return out;
    }
    static constexpr std::optional<Menu> decode_menu(std::span<const std::uint8_t> bytes) {
        if(bytes.size()!=29 || bytes[0]!=0x6d) return std::nullopt;
        Menu out{word(bytes,1),word(bytes,3),bytes[5],bytes[6],bytes[7],bytes[8]};
        for(std::size_t i=0;i<5;++i) {
            const auto at=9+4*i;
            out.destinations[i]={bytes[at],bytes[at+1],word(bytes,at+2)};
        }
        if(!valid(out)) return std::nullopt;
        return out;
    }
    static constexpr std::optional<Selection> decode_selection(std::span<const std::uint8_t> bytes) {
        if(bytes.size()!=5 || (bytes[0]!=0x99 && bytes[0]!=0xa9) || bytes[3]<1 || bytes[3]>5)
            return std::nullopt;
        const auto context=word(bytes,1);
        if(bytes[0]!=(special_context(context)?0xa9:0x99)) return std::nullopt;
        return Selection{bytes[0],context,bytes[3],bytes[4]};
    }
};
}
