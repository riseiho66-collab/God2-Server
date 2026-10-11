#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current 69EB0 -> E6390 / AA3F0. Percent input is NOT absolute XP.
struct RecoveredRoleProgress {
    static constexpr std::uint8_t opcode=0x2b;
    static constexpr std::size_t logical_size=21;
    using Bytes=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint32_t role_hp() const noexcept { return u32(1); }
        std::uint32_t role_mp() const noexcept { return u32(9); }
        std::uint16_t role_progress_display() const noexcept { return u16(17); }
        std::uint32_t companion_hp() const noexcept { return u32(5); }
        std::uint16_t companion_scalar_raw() const noexcept { return u16(13); }
        std::uint16_t companion_progress_display() const noexcept { return u16(19); }
    private:
        friend struct RecoveredRoleProgress;
        explicit Record(Bytes bytes):bytes_(bytes) {}
        std::uint16_t u16(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(bytes_[at]|(std::uint16_t{bytes_[at+1]}<<8));
        }
        std::uint32_t u32(std::size_t at) const noexcept {
            return u16(at)|(std::uint32_t{u16(at+2)}<<16);
        }
        Bytes bytes_;
    };
    static std::optional<Record> parse(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode) return std::nullopt;
        Bytes copy{};std::copy(bytes.begin(),bytes.end(),copy.begin());
        return Record(copy);
    }
    static Bytes encode(const Record& record) noexcept { return record.bytes_; }
    // Requires a complete existing record: companion fields and opaque15..16 survive.
    static Record with_role(const Record& original,std::uint32_t hp,std::uint32_t mp,
                            std::uint16_t progress_display) noexcept {
        auto result=original;
        for(unsigned i=0;i<4;++i) {
            result.bytes_[1+i]=static_cast<std::uint8_t>(hp>>(8*i));
            result.bytes_[9+i]=static_cast<std::uint8_t>(mp>>(8*i));
        }
        result.bytes_[17]=static_cast<std::uint8_t>(progress_display);
        result.bytes_[18]=static_cast<std::uint8_t>(progress_display>>8);
        return result;
    }
};
}
