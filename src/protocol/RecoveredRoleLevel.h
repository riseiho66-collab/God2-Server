#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native22 -> E6B40. A full state snapshot, NOT an incremental level-up command.
struct RecoveredRoleLevel {
    using Bytes=std::array<std::uint8_t,25>;
    class Record {
    public:
        std::uint8_t level() const noexcept { return bytes_[1]; }
        std::uint16_t state_word() const noexcept { return word(3); }
        std::array<std::uint16_t,4> base_stats() const noexcept { return {word(5),word(7),word(9),word(11)}; }
        std::uint16_t progress_display() const noexcept { return word(13); }
        std::uint32_t max_hp() const noexcept { return dword(17); }
        std::uint32_t max_mp() const noexcept { return dword(21); }
    private:
        friend struct RecoveredRoleLevel;
        explicit Record(Bytes bytes):bytes_(bytes) {}
        std::uint16_t word(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(bytes_[at]|(std::uint16_t{bytes_[at+1]}<<8));
        }
        std::uint32_t dword(std::size_t at) const noexcept { return word(at)|(std::uint32_t{word(at+2)}<<16); }
        Bytes bytes_;
    };
    static std::optional<Record> parse(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=25 || bytes[0]!=0x22) return std::nullopt;
        Bytes owned{};std::copy(bytes.begin(),bytes.end(),owned.begin());return Record(owned);
    }
    static Bytes encode(const Record& record) noexcept { return record.bytes_; }
    // Preserve unknown bytes and caller-provided stats/maxima; no inferred growth.
    static Record with_level_progress(const Record& previous,std::uint8_t level,std::uint16_t progress) noexcept {
        auto result=previous;result.bytes_[1]=level;
        result.bytes_[13]=static_cast<std::uint8_t>(progress);
        result.bytes_[14]=static_cast<std::uint8_t>(progress>>8);
        return result;
    }
    // Native E6B40 -> E6DB0 controls0E..11 bind Con/Str/Int/Speed; control16
    // is remaining allocation points. Preserve opaque bytes and resource maxima.
    static Record with_base_stats_and_points(const Record& previous,
        const std::array<std::uint16_t,4>& stats,std::uint16_t points) noexcept {
        auto result=previous;
        auto word=[&](unsigned at,std::uint16_t value) {
            result.bytes_[at]=static_cast<std::uint8_t>(value);
            result.bytes_[at+1]=static_cast<std::uint8_t>(value>>8);
        };
        word(3,points);
        for(unsigned i=0;i<4;++i)word(5+2*i,stats[i]);
        return result;
    }
};
}
