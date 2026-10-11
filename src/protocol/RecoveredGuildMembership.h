#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current149c / installedc5d8: S2C8D ->468B8C ->4EE4E0 ->4F1E50(4/5).
// Input4F21A0/4F2390 ->4EE5F0 ->4132E0 C2S6F body22. This codec
// establishes wire behavior only, not original fees, NPCs or join authority.
struct RecoveredGuildMembership {
    enum class Operation : std::uint8_t { Create=0, Join=1 };
    static constexpr std::uint8_t request_opcode=0x6f, prompt_opcode=0x8d;
    static constexpr std::size_t request_size=23, prompt_size=5;
    using Name=std::array<std::uint8_t,16>;
    using Prompt=std::array<std::uint8_t,prompt_size>;
    struct Request {
        std::uint16_t context{};
        // Native selected actor's first WORD. Its ownership/NPC meaning is
        // not proven and it must never identify an authoritative target.
        std::uint16_t selected_actor_hint{};
        Name raw_name{};
        Operation operation{};
        std::uint8_t opaque_stack_byte{};
        bool operator==(const Request&) const=default;
    };
    static constexpr bool supported(Operation operation) noexcept {
        return operation==Operation::Create || operation==Operation::Join;
    }
    static std::optional<Name> canonical(const Request& request) noexcept {
        const auto nul=std::find(request.raw_name.begin(),request.raw_name.end(),0);
        if(nul==request.raw_name.end())return {};
        Name result{};
        std::copy(request.raw_name.begin(),nul,result.begin());return result;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=request_size || logical[0]!=request_opcode || logical[21]>1)return {};
        Request result;
        result.context=static_cast<std::uint16_t>(logical[1]|(std::uint16_t{logical[2]}<<8));
        result.selected_actor_hint=static_cast<std::uint16_t>(logical[3]|(std::uint16_t{logical[4]}<<8));
        std::copy_n(logical.begin()+5,16,result.raw_name.begin());
        result.operation=static_cast<Operation>(logical[21]);result.opaque_stack_byte=logical[22];
        if(!canonical(result))return {};return result;
    }
    static std::optional<std::array<std::uint8_t,request_size>> encode_request(const Request& request) noexcept {
        if(!supported(request.operation) || !canonical(request))return {};
        std::array<std::uint8_t,request_size> result{request_opcode};
        result[1]=static_cast<std::uint8_t>(request.context);result[2]=static_cast<std::uint8_t>(request.context>>8);
        result[3]=static_cast<std::uint8_t>(request.selected_actor_hint);
        result[4]=static_cast<std::uint8_t>(request.selected_actor_hint>>8);
        std::copy(request.raw_name.begin(),request.raw_name.end(),result.begin()+5);
        result[21]=static_cast<std::uint8_t>(request.operation);result[22]=request.opaque_stack_byte;
        return result;
    }
    static constexpr std::optional<Prompt> prompt(std::uint16_t context,Operation operation) noexcept {
        if(!supported(operation))return {};
        // Native body+3 is not read. Zero is a canonical server serialization,
        // never a recovered original-server byte value or hidden permission.
        return Prompt{prompt_opcode,static_cast<std::uint8_t>(context),
            static_cast<std::uint8_t>(context>>8),static_cast<std::uint8_t>(operation),0};
    }
};
}
