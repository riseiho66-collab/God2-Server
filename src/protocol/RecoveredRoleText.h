#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current 496890 ->4132E0: C2S20 is the editable secondary role text,
// independently of C2S2F chat and the primary name. Callers4B2AE0/4E7B20
// read at most15 bytes, copy to role+37, then queue16 bytes including NUL.
// Producer stack bytes after NUL are opaque and never persisted or echoed.
// S2C23: 40124C returns17; 469F02 copies text to local actor+C7, then
// refreshes role widget7 and renderer text buffer81. Human title/nickname
// terminology and any original server moderation policy remain unqualified.
struct RecoveredRoleText {
    static constexpr std::uint8_t c2s_opcode=0x20, s2c_opcode=0x23;
    static constexpr std::size_t logical_size=17, maximum_text_bytes=15;
    using Text=std::array<std::uint8_t,16>;
    using Logical=std::array<std::uint8_t,logical_size>;
    struct Request {
        Text raw{};
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=c2s_opcode)return std::nullopt;
        const auto payload=logical.subspan(1);
        if(std::find(payload.begin(),payload.end(),0)==payload.end())return std::nullopt;
        Request result;
        std::copy(payload.begin(),payload.end(),result.raw.begin());
        return result;
    }
    static std::optional<Text> canonical(const Request& request) noexcept {
        const auto end=std::find(request.raw.begin(),request.raw.end(),0);
        if(end==request.raw.end())return std::nullopt;
        Text result{};
        std::copy(request.raw.begin(),end,result.begin());
        return result;
    }
    static std::optional<Logical> encode_request(const Request& request) noexcept {
        if(!canonical(request))return std::nullopt;
        Logical result{c2s_opcode};
        std::copy(request.raw.begin(),request.raw.end(),result.begin()+1);
        return result;
    }
    // Caller authorizes ownership and commits the canonical bytes before send.
    // Empty text clears the field. Encoding is preserved without transcoding.
    static std::optional<Logical> update(const Text& text) noexcept {
        const auto clean=canonical(Request{text});
        if(!clean || *clean!=text)return std::nullopt;
        Logical result{s2c_opcode};
        std::copy(text.begin(),text.end(),result.begin()+1);
        return result;
    }
};
}
