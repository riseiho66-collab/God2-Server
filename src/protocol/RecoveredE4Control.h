#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current mapped image: 95AFE/95B30 client UI senders queue E4 plus one
// operation BYTE (observed 0..3; 0..2 have button gates, 3 a separate
// eight-flag composite UI path). World dispatcher691C7 routes a distinct
// 17-byte S2CE4 to4A3180, which conditionally updates an existing E3 pet row.
// The same opcode number does not prove request/response causality or rules.
struct RecoveredE4Control {
    static constexpr std::uint8_t opcode=0xe4;
    static constexpr std::size_t request_size=2, update_size=17;
    using Update=std::array<std::uint8_t,update_size>;
    // Receive-side projection only. Native A3180 requires an existing E3 row,
    // a valid metadata key and slot 42..44 before applying any of these fields.
    // This is not an authoritative pet-stat calculation or C2S reply contract.
    struct UpdateView {
        Update raw{};
        std::uint8_t pet_slot() const noexcept {return raw[8];}
        bool native_slot_range() const noexcept {return pet_slot()>=42 && pet_slot()<=44;}
        std::uint8_t bonus_index_raw() const noexcept {return raw[12];}
        std::optional<std::uint8_t> incremented_bonus_index() const noexcept {
            const auto value=bonus_index_raw();
            return value<=3 ? std::optional<std::uint8_t>{value} : std::nullopt;
        }
        std::uint16_t maximum_hp() const noexcept {return word(1);}
        std::uint16_t maximum_mp() const noexcept {return word(3);}
        std::uint16_t physical_attack() const noexcept {return static_cast<std::uint16_t>(dword(5)&0xfff);}
        std::uint16_t physical_defense() const noexcept {return static_cast<std::uint16_t>((dword(5)>>12)&0xfff);}
        std::uint16_t magical_attack() const noexcept {return static_cast<std::uint16_t>(dword(9)&0xfff);}
        std::uint16_t magical_defense() const noexcept {return static_cast<std::uint16_t>((dword(9)>>12)&0xfff);}
        std::uint16_t remaining_points() const noexcept {return word(13);}
        std::span<const std::uint8_t,2> opaque_tail() const noexcept {
            return std::span<const std::uint8_t,update_size>(raw).subspan<15,2>();
        }
    private:
        std::uint16_t word(std::size_t offset) const noexcept {
            return static_cast<std::uint16_t>(raw[offset]|(std::uint16_t{raw[offset+1]}<<8));
        }
        std::uint32_t dword(std::size_t offset) const noexcept {
            return std::uint32_t{word(offset)}|(std::uint32_t{word(offset+2)}<<16);
        }
    };
    struct Request {
        std::uint8_t operation{};
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode_request(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=request_size || bytes[0]!=opcode)return {};
        // Preserve even unobserved raw BYTEs structurally; no operation is
        // authorized by this format-only codec.
        return Request{bytes[1]};
    }
    static std::array<std::uint8_t,request_size> encode_request(Request value) noexcept {
        return {opcode,value.operation};
    }
    static std::optional<Update> decode_update(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=update_size || bytes[0]!=opcode)return {};
        Update raw{};std::copy(bytes.begin(),bytes.end(),raw.begin());return raw;
    }
    static std::optional<UpdateView> inspect_update(std::span<const std::uint8_t> bytes) noexcept {
        const auto raw=decode_update(bytes);
        return raw ? std::optional<UpdateView>{UpdateView{*raw}} : std::nullopt;
    }
};
}
