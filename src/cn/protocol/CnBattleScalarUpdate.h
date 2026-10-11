#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582F BATTLE86 ->00551D50 nested switch0055212D, kinds0/1/6 only.
// Native scalar stores, not enemy base stats, damage authority or skill list.
struct CnBattleScalarUpdate {
    static constexpr std::size_t logical_size=17;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint8_t kind() const noexcept {return bytes_[1];}
        std::uint8_t packed_position() const noexcept {return bytes_[2];}
        unsigned side() const noexcept {return packed_position()/14;}
        unsigned position() const noexcept {return packed_position()%14;}
        std::uint32_t supplied_maximum() const noexcept {return word32(5);}
        std::uint32_t supplied_current() const noexcept {return word32(9);}
        std::span<const std::uint8_t,2> opaque_word() const noexcept {return std::span<const std::uint8_t,2>(bytes_.data()+3,2);}
        std::span<const std::uint8_t,4> opaque_tail() const noexcept {return std::span<const std::uint8_t,4>(bytes_.data()+13,4);}
        // Main scalar-object branch only. For side1,0 and6 additionally need
        // an actual object whose unsigned render handle at+1A is <1000.
        bool has_primary_actor_store_branch() const noexcept {
            return side()==0?kind()!=6:kind()!=1;
        }
        // Caller must qualify actual phase, authority, slot incarnation and
        // resource semantics. Preserve all other bytes; no blank constructor.
        Record with_supplied_values(std::uint32_t current,std::uint32_t maximum) const noexcept {
            auto result=*this;result.put32(5,maximum);result.put32(9,current);return result;
        }
    private:
        friend struct CnBattleScalarUpdate;
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
        if(bytes.size()!=logical_size || bytes[0]!=0x86 || bytes[2]>=28 ||
            (bytes[1]!=0 && bytes[1]!=1 && bytes[1]!=6))return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    // Kinds2..5 remain separate native consumers; do not default them to0.
};
}
