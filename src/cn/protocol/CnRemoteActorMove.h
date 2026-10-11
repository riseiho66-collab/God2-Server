#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Pinned582f2695 WORLD00490BF2..00490CFE ->00532800. This is the
// seventeen-byte CN record, not TW's thirteen-byte record. No spawn builder
// or fabricated appearance/mount/resource data is supplied here.
struct CnRemoteActorMove {
    static constexpr std::size_t logical_size=17;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t identity() const noexcept {return static_cast<std::uint16_t>(word(1));}
        std::uint16_t x() const noexcept {return static_cast<std::uint16_t>(word(9)&0x7ff);}
        std::uint16_t y() const noexcept {return static_cast<std::uint16_t>((word(9)>>11)&0x7ff);}
        std::uint16_t state_raw() const noexcept {return static_cast<std::uint16_t>(word(5));}
        std::uint8_t driver_resource_selector_raw() const noexcept {return static_cast<std::uint8_t>((word(1)>>16)&0x7f);}
        std::uint8_t auxiliary_resource_selector_raw() const noexcept {return static_cast<std::uint8_t>(word(9)>>25);}
        std::uint8_t mount_branch_raw() const noexcept {return static_cast<std::uint8_t>(word(5)>>30);}
        std::uint16_t linked_handle_raw() const noexcept {return static_cast<std::uint16_t>((word(5)>>16)&0x3fff);}
        std::uint8_t companion_visual_byte_raw() const noexcept {return bytes_[13];}
    private:
        friend struct CnRemoteActorMove;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint32_t word(std::size_t at) const noexcept {
            return std::uint32_t(bytes_[at])|(std::uint32_t(bytes_[at+1])<<8)|
                (std::uint32_t(bytes_[at+2])<<16)|(std::uint32_t(bytes_[at+3])<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x5e)return std::nullopt;
        LogicalRecord retained;
        std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    static std::optional<Record> with_position(const Record& record,std::uint64_t x,std::uint64_t y) noexcept {
        if(x>0x7ff || y>0x7ff)return std::nullopt;
        auto bytes=record.bytes_;
        const auto point=(record.word(9)&~std::uint32_t{0x3fffff})|
            static_cast<std::uint32_t>(x)|(static_cast<std::uint32_t>(y)<<11);
        for(unsigned i=0;i<4;++i)bytes[9+i]=static_cast<std::uint8_t>(point>>(8*i));
        return Record(bytes); // Preserve identity, state, mount and every opaque byte/bit.
    }
};
}
