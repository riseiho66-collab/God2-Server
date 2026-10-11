#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// CN582F WORLD71 ->00491752 ->00428500 ->004F92A0/004F9A80.
// This is a display instance, not a common monster definition or stat record.
// Full supplied records only; unknown bytes7..8/13..18 stay unchanged.
struct CnWorldMonster {
    static constexpr std::size_t logical_size=21;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t instance() const noexcept {return word16(1);}
        bool native_scene_high_bit() const noexcept {return (instance()&0x8000)!=0;}
        std::uint8_t direction() const noexcept {return static_cast<std::uint8_t>(word32(1)>>29);}
        std::uint8_t state_raw() const noexcept {return bytes_[4]&0x1f;}
        std::uint8_t resource_override() const noexcept {return bytes_[3];}
        std::uint8_t catalog_category() const noexcept {return bytes_[5]&0x3f;}
        std::uint16_t catalog_group() const noexcept {return word16(5)>>6;}
        std::uint16_t catalog_ordinal() const noexcept {return word16(19)>>3;}
        std::uint8_t resource_pose_raw() const noexcept {return bytes_[19]&7;}
        std::uint16_t x() const noexcept {return static_cast<std::uint16_t>((word32(9)>>2)&0x7fff);}
        std::uint16_t y() const noexcept {return static_cast<std::uint16_t>(word32(9)>>17);}
    private:
        friend struct CnWorldMonster;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint16_t word16(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(bytes_[at]|(std::uint16_t(bytes_[at+1])<<8));
        }
        std::uint32_t word32(std::size_t at) const noexcept {
            return std::uint32_t(bytes_[at])|(std::uint32_t(bytes_[at+1])<<8)|
                (std::uint32_t(bytes_[at+2])<<16)|(std::uint32_t(bytes_[at+3])<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x71)return std::nullopt;
        LogicalRecord retained;std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    static std::optional<Record> with_position(const Record& record,std::uint64_t x,std::uint64_t y) noexcept {
        if(x>0x7fff || y>0x7fff)return std::nullopt;
        auto bytes=record.bytes_;const auto packed=(record.word32(9)&3)|
            (static_cast<std::uint32_t>(x)<<2)|(static_cast<std::uint32_t>(y)<<17);
        for(unsigned i=0;i<4;++i)bytes[9+i]=static_cast<std::uint8_t>(packed>>(8*i));
        return Record(bytes);
    }
    static std::optional<Record> with_direction(const Record& record,std::uint64_t direction) noexcept {
        if(direction>7)return std::nullopt;
        auto bytes=record.bytes_;bytes[4]=static_cast<std::uint8_t>((bytes[4]&0x1f)|(direction<<5));return Record(bytes);
    }
    // Only the receiver projection uses these two mutations. Do not replace
    // the original wire record with the client's locally mutated buffer.
    static std::optional<Record> with_consumer_pose(const Record& record,std::uint64_t pose) noexcept {
        if(pose>7)return std::nullopt;
        auto bytes=record.bytes_;bytes[19]=static_cast<std::uint8_t>((bytes[19]&0xf8)|pose);return Record(bytes);
    }
    static Record with_consumer_override(const Record& record,std::uint8_t value) noexcept {
        auto bytes=record.bytes_;bytes[3]=value;return Record(bytes);
    }
};
}
