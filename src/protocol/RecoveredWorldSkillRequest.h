#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Same149c C2S497A90 ->4132E0: opcode56 plus six body bytes.
// This is distinct from C35 battle commands and S2C56 party position.
// Field5 copies U23D872; field6 is unwritten native local residue. Preserve
// every bit. Target namespace, meaning of field5, learning, phase, cost,
// action and native reply require their actual sources; grammar grants none.
struct RecoveredWorldSkillRequest {
    static constexpr std::uint8_t opcode=0x56;
    static constexpr std::size_t logical_size=7;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Request {
    public:
        const LogicalRecord& raw() const noexcept {return raw_;}
        std::uint16_t raw_target() const noexcept {
            return static_cast<std::uint16_t>(std::uint16_t{raw_[1]}|(std::uint16_t{raw_[2]}<<8));
        }
        std::uint8_t kind() const noexcept {return raw_[3];}
        std::uint8_t definition_id() const noexcept {return raw_[4];}
        std::uint8_t raw5() const noexcept {return raw_[5];}
        std::uint8_t raw_tail() const noexcept {return raw_[6];}
        bool operator==(const Request&) const=default;
    private:
        friend struct RecoveredWorldSkillRequest;
        explicit Request(const LogicalRecord& raw):raw_(raw) {}
        LogicalRecord raw_;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=opcode)return std::nullopt;
        LogicalRecord owned;
        std::copy(raw.begin(),raw.end(),owned.begin());
        return Request(owned);
    }
    static LogicalRecord encode(const Request& request) noexcept {return request.raw();}
};
}
