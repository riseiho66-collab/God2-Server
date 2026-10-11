#pragma once
#include "protocol/RecoveredRoleAuxiliary.h"
#include <bit>

namespace god2 {
// NATIVE_VERIFIED wire/display contract only: fresh S2C2C -> 4E6600 ->
// 4E6710/4E6DB0. See current-armor-equipped-attributes-20261002/contract.md.
// No equipment aggregation, base-stat, resource or combat formula is supplied.
// Updates require an existing raw snapshot and preserve all unrelated bytes.
struct RecoveredRoleAuxiliaryProjection {
    using Logical=RecoveredRoleAuxiliary::Logical;
    struct Combat {
        std::uint32_t physical_attack{},physical_defense{},magical_attack{},magical_defense{};
        bool operator==(const Combat&) const=default;
    };
    class Record {
        friend struct RecoveredRoleAuxiliaryProjection;
        Logical raw_;
        explicit Record(Logical raw):raw_(raw){}
    public:
        const Logical& raw() const noexcept {return raw_;}
        // Native sign handling is a WORD negation with positive-bit precedence.
        // This is the first fresh-snapshot display, not transformed actor RAM.
        std::array<std::int16_t,4> displayed_modifiers() const noexcept {
            std::array<std::int16_t,4> result{};
            const auto positive=word(raw_,37),negative=word(raw_,41);
            for(std::size_t i=0;i<4;++i){
                auto value=word(raw_,1+4*i);
                if(!(positive&bits[i])&&(negative&bits[i]))
                    value=static_cast<std::uint16_t>(0u-value);
                result[i]=std::bit_cast<std::int16_t>(value);
            }
            return result;
        }
        std::array<std::uint32_t,5> elements() const noexcept {
            std::array<std::uint32_t,5> result{};
            for(std::size_t i=0;i<5;++i)result[i]=dword(raw_,17+4*i);
            return result;
        }
        Combat combat() const noexcept {
            return {dword(raw_,49),dword(raw_,45),dword(raw_,57),dword(raw_,53)};
        }
        // Raw transport permits all DWORDs; original %d displays signed values.
        // This reports the display domain without rejecting captured raw data.
        bool nonnegative_combat_display() const noexcept {
            const auto values=combat();
            return !(values.physical_attack&0x80000000u)&&!(values.physical_defense&0x80000000u)&&
                !(values.magical_attack&0x80000000u)&&!(values.magical_defense&0x80000000u);
        }
    };
    static std::optional<Record> parse(std::span<const std::uint8_t> raw) noexcept {
        const auto parsed=RecoveredRoleAuxiliary::parse(raw);
        return parsed?std::optional<Record>{Record(*parsed)}:std::nullopt;
    }
    // Canonical sign encoding affects only four lowWORDs and known mask bits.
    // High words and unclassified mask bits remain the caller's original data.
    static Record with_modifiers(const Record& previous,const std::array<std::int16_t,4>& modifiers) noexcept {
        auto next=previous;
        auto positive=static_cast<std::uint16_t>(word(next.raw_,37)&0xfff0u);
        auto negative=static_cast<std::uint16_t>(word(next.raw_,41)&0xfff0u);
        for(std::size_t i=0;i<4;++i){
            const auto value=static_cast<std::int32_t>(modifiers[i]);
            put_word(next.raw_,1+4*i,static_cast<std::uint16_t>(value<0?-value:value));
            if(value>0)positive=static_cast<std::uint16_t>(positive|bits[i]);
            if(value<0)negative=static_cast<std::uint16_t>(negative|bits[i]);
        }
        put_word(next.raw_,37,positive);put_word(next.raw_,41,negative);return next;
    }
    // Authoritative absolute totals only, never accumulating packet deltas.
    static Record with_combat(const Record& previous,const Combat& totals) noexcept {
        auto next=previous;
        put_dword(next.raw_,49,totals.physical_attack);put_dword(next.raw_,45,totals.physical_defense);
        put_dword(next.raw_,57,totals.magical_attack);put_dword(next.raw_,53,totals.magical_defense);
        return next;
    }
private:
    static constexpr std::array<std::uint16_t,4> bits{2,4,1,8};
    static std::uint16_t word(const Logical& raw,std::size_t at) noexcept {
        return static_cast<std::uint16_t>(raw[at]|(std::uint16_t{raw[at+1]}<<8));
    }
    static std::uint32_t dword(const Logical& raw,std::size_t at) noexcept {
        return word(raw,at)|(std::uint32_t{word(raw,at+2)}<<16);
    }
    static void put_word(Logical& raw,std::size_t at,std::uint16_t value) noexcept {
        raw[at]=static_cast<std::uint8_t>(value);raw[at+1]=static_cast<std::uint8_t>(value>>8);
    }
    static void put_dword(Logical& raw,std::size_t at,std::uint32_t value) noexcept {
        put_word(raw,at,static_cast<std::uint16_t>(value));put_word(raw,at+2,static_cast<std::uint16_t>(value>>16));
    }
};
}
