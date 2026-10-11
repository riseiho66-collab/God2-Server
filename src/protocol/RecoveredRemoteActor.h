#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include "protocol/RecoveredPlayerAppearanceUpdate.h"

namespace god2 {
// Current 6F receive layout: 695C8, FC2C3..FC3BE. No complete spawn builder.
struct RecoveredRemoteActor {
    static constexpr std::size_t logical_size=81;
    static constexpr bool runtime_emission_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t identity() const noexcept { return static_cast<std::uint16_t>(u32(1)&0xfff); }
        std::uint16_t x() const noexcept { return static_cast<std::uint16_t>((u32(13)>>2)&0x7fff); }
        std::uint16_t y() const noexcept { return static_cast<std::uint16_t>(u32(13)>>17); }
    private:
        friend struct RecoveredRemoteActor;
        explicit Record(const LogicalRecord& bytes):bytes_(bytes) {}
        std::uint32_t u32(std::size_t offset) const noexcept {
            return std::uint32_t{bytes_[offset]}|(std::uint32_t{bytes_[offset+1]}<<8)|
                (std::uint32_t{bytes_[offset+2]}<<16)|(std::uint32_t{bytes_[offset+3]}<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=0x6f) return std::nullopt;
        // Native unbounded copies target three adjacent 16-byte regions.
        // This is a defensive admission restriction, not a native reject branch.
        for(const auto offset:{29u,45u,61u}) {
            const auto field=logical.subspan(offset,16);
            if(std::find(field.begin(),field.end(),0)==field.end()) return std::nullopt;
        }
        LogicalRecord bytes;
        std::copy(logical.begin(),logical.end(),bytes.begin());
        return Record(bytes);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept { return record.bytes_; }
    // Native FC1C0 stores body76 WORD at actor262 and body78/79 at264/265.
    // DA describes the same saved ordinary appearance; identity is never masked.
    static std::optional<Record> with_appearance(const Record& record,
        const RecoveredPlayerAppearanceUpdate::Fields& appearance) noexcept {
        if(!appearance.actor_identity || appearance.actor_identity!=record.identity() ||
           appearance.transform_key || record.bytes_[77] || record.bytes_[78])return std::nullopt;
        auto bytes=record.bytes_;
        std::copy(appearance.components.begin(),appearance.components.end(),bytes.begin()+21);
        bytes[79]=appearance.raw_scalar5;
        bytes[80]=appearance.raw_scalar6;
        return Record(bytes);
    }
    // FC2C3..FC33F copies these byte strings without bounds. No encoding conversion.
    static std::optional<Record> with_text_fields(const Record& record,
        const std::array<std::span<const std::uint8_t>,3>& fields) noexcept {
        for(const auto field:fields)
            if(field.size()>15 || std::find(field.begin(),field.end(),0)!=field.end())
                return std::nullopt;
        auto bytes=record.bytes_;
        for(std::size_t index=0;index<fields.size();++index) {
            const auto start=bytes.begin()+29+16*index;
            std::fill_n(start,16,0);
            std::copy(fields[index].begin(),fields[index].end(),start);
        }
        return Record(bytes);
    }
    static std::optional<Record> with_identity(const Record& record,std::uint64_t identity) noexcept {
        if(identity>0xfff) return std::nullopt;
        auto bytes=record.bytes_;
        bytes[1]=static_cast<std::uint8_t>(identity);
        bytes[2]=static_cast<std::uint8_t>((bytes[2]&0xf0)|(identity>>8));
        return Record(bytes);
    }
    static std::optional<Record> with_position(const Record& record,std::uint64_t x,std::uint64_t y) noexcept {
        if(x>0x7fff || y>0x7fff) return std::nullopt;
        auto bytes=record.bytes_;
        const auto point=(record.u32(13)&3)|(static_cast<std::uint32_t>(x)<<2)|
                         (static_cast<std::uint32_t>(y)<<17);
        for(unsigned i=0;i<4;++i) bytes[13+i]=static_cast<std::uint8_t>(point>>(8*i));
        return Record(bytes);
    }
    // 684CD/69941 normal branches. Field projection, not resource/ownership validation.
    static std::optional<Record> with_normal_world_components(
        const Record& record,std::span<const std::uint8_t> world_body) noexcept {
        if(world_body.size()!=36 || world_body[32]!=0 || world_body[33]!=0 ||
           world_body[6]>0x7f || record.bytes_[77]!=0 || record.bytes_[78]!=0)
            return std::nullopt;
        auto bytes=record.bytes_;
        const auto selector=static_cast<std::uint32_t>(world_body[2]&0x7f);
        const auto first=(record.u32(1)&~(std::uint32_t{0x7f}<<14))|(selector<<14);
        for(unsigned i=0;i<4;++i) bytes[1+i]=static_cast<std::uint8_t>(first>>(8*i));
        bytes[6]=static_cast<std::uint8_t>((bytes[6]&0x80)|world_body[6]);
        std::copy_n(world_body.begin()+12,8,bytes.begin()+21);
        bytes[79]=world_body[34];
        bytes[80]=world_body[35];
        return Record(bytes);
    }
};

// Original world cases69A60/69A28. Preserve appearance and unqualified bits.
template<std::uint8_t Opcode, std::size_t Size>
struct RecoveredRemoteActorEvent {
    static_assert((Opcode==0x5e && Size==13) || (Opcode==0x73 && Size==5));
    static constexpr std::size_t logical_size=Size;
    static constexpr bool runtime_emission_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,Size>;
    class Record {
    public:
        std::uint16_t identity() const noexcept { return static_cast<std::uint16_t>(u32(1)); }
        std::uint16_t x() const noexcept requires (Opcode==0x5e) { return u32(9)&0x7ff; }
        std::uint16_t y() const noexcept requires (Opcode==0x5e) { return (u32(9)>>11)&0x7ff; }
        std::uint16_t state() const noexcept requires (Opcode==0x5e) {
            return static_cast<std::uint16_t>(u32(5));
        }
    private:
        friend struct RecoveredRemoteActorEvent;
        explicit Record(const LogicalRecord& bytes):bytes_(bytes) {}
        std::uint32_t u32(std::size_t offset) const noexcept {
            return std::uint32_t{bytes_[offset]}|(std::uint32_t{bytes_[offset+1]}<<8)|
                (std::uint32_t{bytes_[offset+2]}<<16)|(std::uint32_t{bytes_[offset+3]}<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=Size || logical[0]!=Opcode) return std::nullopt;
        LogicalRecord bytes;
        std::copy(logical.begin(),logical.end(),bytes.begin());
        return Record(bytes);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept { return record.bytes_; }
    static std::optional<Record> with_identity(const Record& record,std::uint64_t identity) noexcept {
        if(identity>0xffff) return std::nullopt;
        auto bytes=record.bytes_;
        bytes[1]=static_cast<std::uint8_t>(identity);
        bytes[2]=static_cast<std::uint8_t>(identity>>8);
        return Record(bytes);
    }
    // Native69A60 and FC movement consumer read two11-bit coordinates.
    // Extend only this immutable projection; existing TW visibility stays frozen.
    static std::optional<Record> with_position(const Record& record,std::uint64_t x,std::uint64_t y) noexcept
        requires (Opcode==0x5e) {
        if(x>0x7ff || y>0x7ff)return std::nullopt;
        auto bytes=record.bytes_;
        const auto point=(record.u32(9)&~std::uint32_t{0x3fffff})|
            static_cast<std::uint32_t>(x)|(static_cast<std::uint32_t>(y)<<11);
        for(unsigned i=0;i<4;++i)bytes[9+i]=static_cast<std::uint8_t>(point>>(8*i));
        return Record(bytes);
    }
};
using RecoveredRemoteActorMove=RecoveredRemoteActorEvent<0x5e,13>;
using RecoveredRemoteActorRemove=RecoveredRemoteActorEvent<0x73,5>;
}
