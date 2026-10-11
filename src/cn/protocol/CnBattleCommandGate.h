#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582F BATTLE86/5 ->0054CD80. Display WORD5 is not clock duration.
struct CnBattleCommandGate {
    static constexpr std::size_t logical_size=17;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        bool primary_requested() const noexcept {return (bytes_[3]&1)!=0;}
        bool secondary_requested() const noexcept {return (bytes_[3]&2)!=0;}
        std::uint8_t primary_position() const noexcept {return bytes_[4]&0xf;}
        std::uint8_t secondary_position() const noexcept {return bytes_[4]>>4;}
        bool requested_slots_in_range() const noexcept {
            return (!primary_requested() || primary_position()<14) &&
                (!secondary_requested() || secondary_position()<14);
        }
        std::uint16_t supplied_display_word() const noexcept {
            return bytes_[5]|(std::uint16_t(bytes_[6])<<8);
        }
        // Native displays the last three decimal digits of promoted WORD+1.
        unsigned displayed_counter() const noexcept {return (unsigned(supplied_display_word())+1)%1000;}
    private:
        friend struct CnBattleCommandGate;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x86 || bytes[1]!=5)return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    // Actual0054CD80 always copies main+A97130 into+A970D8 and resets the
    // start tick. Pass actual prior duration/start/current tick; no defaults.
    static std::uint32_t native_remaining_bits(std::uint32_t duration,
        std::uint32_t start_tick,std::uint32_t actual_tick) noexcept {
        const auto elapsed=std::uint32_t(actual_tick-start_tick);
        return duration-elapsed/1000;
    }
    static bool native_remaining_negative(std::uint32_t remaining_bits) noexcept {
        return (remaining_bits&0x80000000U)!=0;
    }
    //0054D450: first round when prior current word==-1 retains actual context
    // duration; later88 sets it to20. This is client state, not server policy.
    static std::uint32_t native_duration_after_batch(std::uint32_t prior_round_word,
        std::uint32_t prior_duration) noexcept {
        return prior_round_word==0xffffffffU?prior_duration:20U;
    }
};
}
