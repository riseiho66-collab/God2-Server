#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582F BATTLE88 ->0054D450(full logical) ->00561C40(logical+1).
// Actual side0 fourteen base actors must all exist; not an enemy-stat batch.
struct CnBattleRoundBatch {
    static constexpr std::size_t logical_size=121,slots=14;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    struct CurrentPair {std::uint32_t a,b;};
    class Record {
    public:
        std::uint32_t round_word() const noexcept {return word32(1);}
        std::optional<CurrentPair> at(std::size_t slot) const noexcept {
            if(slot>=slots)return std::nullopt;
            return CurrentPair{word32(5+slot*8),word32(9+slot*8)};
        }
        std::uint8_t native_control_byte() const noexcept {return bytes_[118];}
        std::optional<Record> with_current_values(std::size_t slot,CurrentPair values) const noexcept {
            if(slot>=slots)return std::nullopt;
            auto result=*this;result.put32(5+slot*8,values.a);result.put32(9+slot*8,values.b);return result;
        }
    private:
        friend struct CnBattleRoundBatch;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint32_t word32(std::size_t at) const noexcept {
            return std::uint32_t(bytes_[at])|(std::uint32_t(bytes_[at+1])<<8)|
                (std::uint32_t(bytes_[at+2])<<16)|(std::uint32_t(bytes_[at+3])<<24);
        }
        void put32(std::size_t at,std::uint32_t value) noexcept {
            for(unsigned n=0;n<4;++n)bytes_[at+n]=static_cast<std::uint8_t>(value>>(8*n));
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x88)return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    // Byte117,bytes119..120 preserved. No blank records/default actors or rounds.
};
}
