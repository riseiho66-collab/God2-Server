#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582F BATTLE1C:005485F0 ->main+A97980 queue ->00551D50
// ->0054D5E0. Full logical packet, not WORLD71 or common monster stats.
struct CnBattleSingleObject {
    static constexpr std::size_t logical_size=45;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    using NativeObjectPrefix=std::array<std::uint8_t,56>;
    class Record {
    public:
        std::uint8_t packed_position() const noexcept {return bytes_[1];}
        unsigned side() const noexcept {return packed_position()/14;}
        unsigned position() const noexcept {return packed_position()%14;}
        // Actual0055E220 accepts two sides and fourteen positions; malformed
        // values remain inspectable, and do not become a valid recipient slot.
        bool native_slot_in_range() const noexcept {return side()<2;}
        std::uint8_t supplied_level_byte() const noexcept {return bytes_[2];}
        std::uint16_t supplied_identity() const noexcept {return word16(3);}
        std::uint16_t role_word() const noexcept {return word16(5);}
        unsigned role_kind() const noexcept {return (role_word()>>13)&3;}
        std::uint8_t override_selector() const noexcept {return static_cast<std::uint8_t>(role_word());}
        unsigned supplied_pose() const noexcept {return (role_word()>>10)&7;}
        std::uint16_t selector_word() const noexcept {return word16(7);}
        // Union depends on role_kind and later resource branches: resource
        // selectors, names and other presentation data. No stat/skill labels.
        std::span<const std::uint8_t,32> presentation_union() const noexcept {
            return std::span<const std::uint8_t,32>(bytes_.data()+9,32);
        }
        std::uint32_t trailing_word() const noexcept {return word32(41);}
        std::uint32_t native_trailing_projection() const noexcept {
            const auto value=trailing_word();return (value&1)?1:value;
        }
        // Exact primary0054D65A..0054D760 prefix transformation BEFORE the
        // role/resource switch. prior must be the real native local56 buffer
        // (copied from existing object or initialized by the actual consumer).
        // Later branches rewrite pose/name/model and allocate/update objects;
        // this projection does not emulate those branches or prove acceptance.
        NativeObjectPrefix project_before_resource_branch(const NativeObjectPrefix& prior) const noexcept {
            auto result=prior;
            put16(result,0,supplied_identity());
            auto flags=get32(prior,4);
            flags=(flags&0xffffdfffU)|((std::uint32_t(role_word())>>2)&0xe000U);
            flags=(flags&0x0000ffffU)|(std::uint32_t(override_selector())<<16)|
                (std::uint32_t(supplied_level_byte())<<24);
            flags^=(flags^std::uint32_t(role_word()))&0x1c00U;
            flags^=(flags^(std::uint32_t(role_word())*2))&0xc000U;
            put32(result,4,flags);put32(result,8,native_trailing_projection());
            put16(result,12,selector_word());
            std::copy(bytes_.begin()+9,bytes_.begin()+41,result.begin()+14);
            return result;
        }
    private:
        friend struct CnBattleSingleObject;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint16_t word16(std::size_t at) const noexcept {
            return bytes_[at]|(std::uint16_t(bytes_[at+1])<<8);
        }
        std::uint32_t word32(std::size_t at) const noexcept {return get32(bytes_,at);}
        template<std::size_t N> static std::uint32_t get32(const std::array<std::uint8_t,N>& b,std::size_t at) noexcept {
            return std::uint32_t(b[at])|(std::uint32_t(b[at+1])<<8)|
                (std::uint32_t(b[at+2])<<16)|(std::uint32_t(b[at+3])<<24);
        }
        static void put16(NativeObjectPrefix& b,std::size_t at,std::uint16_t v) noexcept {
            b[at]=static_cast<std::uint8_t>(v);b[at+1]=static_cast<std::uint8_t>(v>>8);
        }
        static void put32(NativeObjectPrefix& b,std::size_t at,std::uint32_t v) noexcept {
            for(unsigned n=0;n<4;++n)b[at+n]=static_cast<std::uint8_t>(v>>(n*8));
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x1c)return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    // No blank object builder, inferred common/world ID, authority or sends.
};
}
