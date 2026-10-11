#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582F WORLD5F004919F4 ->+1499FA0/004FC6A0 ->004FAC00.
// Same pool as71, NOT60/+147C720 and NOT player5E movement.
// Full native source inputs only; no synthesized timing/path/state/defaults.
struct CnWorldMonsterMotion {
    static constexpr std::size_t logical_size=21;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t instance() const noexcept {return word16(1);}
        std::uint8_t state_raw() const noexcept {return bytes_[4]&0x1f;}
        std::uint16_t target_x() const noexcept {return static_cast<std::uint16_t>((word32(9)>>2)&0x7fff);}
        std::uint16_t target_y() const noexcept {return static_cast<std::uint16_t>(word32(9)>>17);}
        // Primary004FC6E7/F2 MOVZX, regardless of the decompiler's signed cast.
        std::uint16_t supplied_anchor_x() const noexcept {return word16(13);}
        std::uint16_t supplied_anchor_y() const noexcept {return word16(15);}
        std::uint16_t timing_word() const noexcept {return word16(17);}
        // Native adds signed promotion(word)-40 to current clock with32-bit
        // machine arithmetic. Under40 is not rejected by this consumer.
        std::int32_t native_deadline_delta() const noexcept {return std::int32_t(timing_word())-40;}
    private:
        friend struct CnWorldMonsterMotion;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint16_t word16(std::size_t at) const noexcept {return bytes_[at]|(std::uint16_t(bytes_[at+1])<<8);}
        std::uint32_t word32(std::size_t at) const noexcept {
            return std::uint32_t(bytes_[at])|(std::uint32_t(bytes_[at+1])<<8)|
                (std::uint32_t(bytes_[at+2])<<16)|(std::uint32_t(bytes_[at+3])<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x5f)return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    // Bytes3,5..8,19..20 and known-word opaque bits retained verbatim.
    // A full15-bit target does not prove the native <=20-step path reaches it.
};
}
