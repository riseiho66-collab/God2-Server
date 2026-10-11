#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current mapped image: 842E4/CFC87/CFE77 directly queue opcode BF plus an
// eight-byte body. A fourth daily-panel dialog32 branch 8433D reaches the
// shared queue call8450B with item WORD,01,01,display amount DWORD. The first
// direct sender is a cached dialog payload; two others use OrangeShop UI rows
// supplied by S2C EE/F3. No branch establishes purchase authority or a causal
// S2C BF response. Daily and OrangeShop shapes can overlap on the wire; the
// issued server-side context, not these predicates, must select the branch.
struct RecoveredBFRequest {
    static constexpr std::uint8_t opcode=0xbf;
    static constexpr std::size_t request_size=9;
    struct Request {
        std::array<std::uint8_t,8> body{};
        bool operator==(const Request&) const=default;
    };
    struct DailyPurchase {
        std::uint16_t item{};
        std::uint32_t displayed_amount{};
    };
    struct OrangeShopSelection {
        std::uint16_t item{};
        std::uint8_t quantity{};
        std::uint8_t category{};
        std::uint16_t displayed_money{};
    };
    static std::optional<Request> decode_request(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=request_size || bytes[0]!=opcode)return {};
        Request request{};std::copy_n(bytes.begin()+1,8,request.body.begin());return request;
    }
    static std::array<std::uint8_t,request_size> encode_request(const Request& request) noexcept {
        std::array<std::uint8_t,request_size> bytes{};bytes[0]=opcode;
        std::copy(request.body.begin(),request.body.end(),bytes.begin()+1);return bytes;
    }
    static std::optional<DailyPurchase> daily_purchase_shape(const Request& request) noexcept {
        const auto& b=request.body;
        if(b[2]!=1 || b[3]!=1)return {};
        return DailyPurchase{
            static_cast<std::uint16_t>(b[0] | (std::uint16_t{b[1]}<<8)),
            std::uint32_t{b[4]} | (std::uint32_t{b[5]}<<8) |
                (std::uint32_t{b[6]}<<16) | (std::uint32_t{b[7]}<<24)};
    }
    static std::optional<OrangeShopSelection> orange_shop_selection_shape(
        const Request& request) noexcept {
        const auto& b=request.body;
        // Native UI selects 1..30 units, maps category 1..4 and zero-extends
        // the selected EE/F3 row's u16 money field into the outgoing DWORD.
        if(b[2]<1 || b[2]>30 || b[3]<1 || b[3]>4 || b[6]!=0 || b[7]!=0)return {};
        return OrangeShopSelection{
            static_cast<std::uint16_t>(b[0] | (std::uint16_t{b[1]}<<8)),
            b[2],b[3],
            static_cast<std::uint16_t>(b[4] | (std::uint16_t{b[5]}<<8))};
    }
};
}
