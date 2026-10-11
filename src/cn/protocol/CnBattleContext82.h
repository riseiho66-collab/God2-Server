#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Independent CN582f S2C82: 00567BA8 returns logical9; 004921E8
// copies logical DWORD+1/+5 into the supplied object's +28/+2C.
// The native phase4 entry bridge supplies that same object to0054A320,
// which copies the values to battle owner+3C/+40. C2S35 uses owner+3C.
// These are raw context fields, not common identities or server grants.
// Record preserves all supplied bytes; it does not construct an ACK or rights.
struct CnBattleContext82 {
    static constexpr std::uint8_t opcode=0x82;
    static constexpr std::size_t logical_size=9;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::span<const std::uint8_t> logical_bytes() const noexcept {return bytes_;}
        std::span<const std::uint8_t> body() const noexcept {return {bytes_.data()+1,8};}
        std::uint32_t raw_context_a() const noexcept {return word32(1);}
        std::uint32_t raw_context_b() const noexcept {return word32(5);}
        bool operator==(const Record&) const=default;
    private:
        friend struct CnBattleContext82;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint32_t word32(std::size_t offset) const noexcept {
            return std::uint32_t{bytes_[offset]} |
                   (std::uint32_t{bytes_[offset+1]}<<8) |
                   (std::uint32_t{bytes_[offset+2]}<<16) |
                   (std::uint32_t{bytes_[offset+3]}<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        LogicalRecord retained;
        std::copy(bytes.begin(),bytes.end(),retained.begin());
        return Record(retained);
    }
};
}
