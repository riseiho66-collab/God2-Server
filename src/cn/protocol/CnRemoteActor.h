#pragma once
#include "cn/protocol/CnWorldEntry.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace god2cn {
// CN582f2695 WORLD6F ->0052F5A0/00532410, WORLD73 ->0052FD40.
// Full native records only. No TW-as-CN evidence, spawn builder, text
// conversion, resource fallback or authoritative appearance rules here.
struct CnRemoteActor {
    static constexpr std::size_t logical_size=81;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t identity() const noexcept {return static_cast<std::uint16_t>(word(1)&0xfff);}
        std::uint16_t x() const noexcept {return static_cast<std::uint16_t>((word(13)>>2)&0x7fff);}
        std::uint16_t y() const noexcept {return static_cast<std::uint16_t>(word(13)>>17);}
        std::uint16_t state_raw() const noexcept {return static_cast<std::uint16_t>(word(7));}
        std::uint8_t native_language_tag() const noexcept {return static_cast<std::uint8_t>((word(1)>>25)&1);}
        // Ordinary WORLD6F ->00482C90: same native resolver as normal2A,
        // but different packed header positions and narrower driver field.
        std::uint8_t mount_driver_resource_selector_raw() const noexcept {return static_cast<std::uint8_t>((word(5)>>8)&0x7f);}
        std::uint8_t auxiliary_resource_selector_raw() const noexcept {return static_cast<std::uint8_t>((word(1)>>14)&0x7f);}
        std::uint16_t alternate_appearance_resource_key_raw() const noexcept {
            return static_cast<std::uint16_t>(bytes_[77]|(std::uint16_t(bytes_[78])<<8));
        }
        std::array<std::uint8_t,8> appearance_components_raw() const noexcept {
            std::array<std::uint8_t,8> result;
            std::copy_n(bytes_.begin()+21,8,result.begin());return result;
        }
        std::optional<CnWorldEntry::BeginPlay::AppearanceInput> appearance_input(unsigned part) const noexcept {
            if(part>=4)return std::nullopt;
            const auto a=bytes_[21+part*2],b=bytes_[22+part*2];
            return CnWorldEntry::BeginPlay::AppearanceInput{static_cast<std::uint8_t>(a&15),
                static_cast<std::uint8_t>(a>>4),static_cast<std::uint8_t>(b&31),static_cast<std::uint8_t>(b>>5)};
        }
        //0052F990 and later00532800 send this input to005356D0. It is a
        // renderer palette operand, never an attribute/status authority.
        std::optional<std::uint8_t> native_palette_operand(unsigned part) const noexcept {
            const auto input=appearance_input(part);if(!input)return std::nullopt;
            return state_raw()&0x1000?std::uint8_t{7}:input->palette;
        }
        bool matches_normal_world_components(const CnWorldEntry::BeginPlay& source) const noexcept {
            return source.actor_handle()<=0xfff && source.actor_handle()==identity() &&
                !source.alternate_appearance_resource_key_raw() && !alternate_appearance_resource_key_raw() &&
                source.mount_driver_selector_raw()<=0x7f &&
                mount_driver_resource_selector_raw()==source.mount_driver_selector_raw() &&
                auxiliary_resource_selector_raw()==source.auxiliary_appearance_selector_raw() &&
                appearance_components_raw()==source.appearance_components_raw();
        }
        //00532410 copies body+28 ->actor entry+1C; record owns this view.
        // This is the raw wire name, not a claimed converted/native memory name.
        std::string_view wire_name() const noexcept {
            const auto first=bytes_.begin()+29,last=first+16;
            const auto end=std::find(first,last,0);
            return {reinterpret_cast<const char*>(bytes_.data()+29),static_cast<std::size_t>(end-first)};
        }
    private:
        friend struct CnRemoteActor;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        std::uint32_t word(std::size_t at) const noexcept {
            return std::uint32_t(bytes_[at])|(std::uint32_t(bytes_[at+1])<<8)|
                (std::uint32_t(bytes_[at+2])<<16)|(std::uint32_t(bytes_[at+3])<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x6f)return std::nullopt;
        // Defensive server admission to the native three16-byte copy regions.
        // This is not a recovered official rejection or resource qualification.
        for(const auto at:{29u,45u,61u}) {
            const auto field=bytes.subspan(at,16);
            if(std::find(field.begin(),field.end(),0)==field.end())return std::nullopt;
        }
        LogicalRecord retained;
        std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
    // Project only proven ordinary resolver operands from the actual same
    // actor's normal2A. Complete real6F is still required for every other bit,
    // name, state, resource/layer/flag/opaque field. No whole spawn builder.
    static std::optional<Record> with_normal_world_components(const Record& record,
        const CnWorldEntry::BeginPlay& source) noexcept {
        if(source.actor_handle()>0xfff || source.actor_handle()!=record.identity() ||
           source.mount_driver_selector_raw()>0x7f || source.alternate_appearance_resource_key_raw() ||
           record.alternate_appearance_resource_key_raw())return std::nullopt;
        auto bytes=record.bytes_;
        const auto selector=(record.word(1)&~(std::uint32_t{0x7f}<<14))|
            (std::uint32_t(source.auxiliary_appearance_selector_raw())<<14);
        for(unsigned i=0;i<4;++i)bytes[1+i]=static_cast<std::uint8_t>(selector>>(8*i));
        bytes[6]=static_cast<std::uint8_t>((bytes[6]&0x80)|source.mount_driver_selector_raw());
        const auto components=source.appearance_components_raw();
        std::copy(components.begin(),components.end(),bytes.begin()+21);
        return Record(bytes);
    }
    static std::optional<Record> with_position(const Record& record,std::uint64_t x,std::uint64_t y) noexcept {
        if(x>0x7fff || y>0x7fff)return std::nullopt;
        auto bytes=record.bytes_;
        const auto packed=(record.word(13)&3)|(static_cast<std::uint32_t>(x)<<2)|
            (static_cast<std::uint32_t>(y)<<17);
        for(unsigned i=0;i<4;++i)bytes[13+i]=static_cast<std::uint8_t>(packed>>(8*i));
        return Record(bytes);
    }
};
struct CnRemoteActorRemove {
    static constexpr std::size_t logical_size=5;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t identity() const noexcept {
            return static_cast<std::uint16_t>(bytes_[1]|(std::uint16_t(bytes_[2])<<8));
        }
    private:
        friend struct CnRemoteActorRemove;
        explicit Record(LogicalRecord bytes):bytes_(bytes){}
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x73)return std::nullopt;
        LogicalRecord retained;
        std::copy(bytes.begin(),bytes.end(),retained.begin());return Record(retained);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
};
}
