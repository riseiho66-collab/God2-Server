#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Independent CN582f 0054FFC0 producer passes opcode35/body16 to00481440.
// Body0/1/2 are raw actor position/command kind/source selector. Body3 is
// local padding with no explicit scalar write in this producer. Aliased writes
// through its target helper/out-of-domain positions are not recovered here.
// Body4/8/12 are raw target field/context/operand.
// Operand initialization depends on the native branch; unknown raw kinds and
// their bytes must survive parsing. Client position is not a common actor ID;
// target field is not uniformly a bitmask in every native command branch.
// This C2S record is distinct from C56 and S2C world35. No authority or reply.
struct CnBattleCommand35 {
    static constexpr std::uint8_t opcode=0x35;
    static constexpr std::size_t logical_size=17;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Request {
    public:
        std::span<const std::uint8_t> logical_bytes() const noexcept {return bytes_;}
        std::span<const std::uint8_t> body() const noexcept {return {bytes_.data()+1,16};}
        std::uint8_t raw_actor_position() const noexcept {return bytes_[1];}
        std::uint8_t raw_command_kind() const noexcept {return bytes_[2];}
        std::uint8_t raw_source_slot() const noexcept {return bytes_[3];}
        std::uint8_t raw_padding() const noexcept {return bytes_[4];}
        std::uint32_t raw_target_field() const noexcept {return word32(5);}
        std::uint32_t context() const noexcept {return word32(9);}
        std::uint32_t operand() const noexcept {return word32(13);}
        bool operator==(const Request&) const=default;
    private:
        friend struct CnBattleCommand35;
        explicit Request(LogicalRecord bytes):bytes_(bytes){}
        std::uint32_t word32(std::size_t offset) const noexcept {
            return std::uint32_t{bytes_[offset]} |
                   (std::uint32_t{bytes_[offset+1]}<<8) |
                   (std::uint32_t{bytes_[offset+2]}<<16) |
                   (std::uint32_t{bytes_[offset+3]}<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        LogicalRecord retained;
        std::copy(bytes.begin(),bytes.end(),retained.begin());
        return Request(retained);
    }
};
}
