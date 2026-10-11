#pragma once
#include "cn/assets/CnProgramMessageCatalog.h"
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Pinned CN 004D5030/004D5440 presentation operands, not common gameplay
// attributes. Both an actual retained row and explicit UI bonus inputs can
// come from server-owned sources; process memory/pointers are not required.
struct CnSubjectPanelOperands final {
    static constexpr std::size_t row_size=0x3ec;
    // WORDs at UI+42E14,16,18,1A,1C,1E,20,22,24 in that exact order.
    using InlineUiBonusWords=std::array<std::uint16_t,9>;
    struct Scalar {
        std::uint8_t native_control;
        std::uint16_t row_offset;
        bool row_is_zero_extended_word;
        std::uint32_t original_row_bits;
        std::optional<std::uint16_t> actual_ui_bonus_word;
        std::optional<std::uint32_t> native_integer_bits;
        // 004D5030 supplies these bits to 00450B80 using literal "%d".
        // Missing special-row bonuses stay unknown instead of becoming zero.
        std::optional<std::int32_t> native_signed_decimal_argument() const noexcept {
            if(!native_integer_bits)return std::nullopt;
            return std::bit_cast<std::int32_t>(*native_integer_bits);
        }
    };
    struct Pair {
        std::uint8_t native_control;
        bool row_is_zero_extended_word;
        std::uint32_t first_row_bits,second_row_bits;
    };
    struct Metric {
        std::uint16_t actual_row_word28;
        static constexpr std::uint8_t native_control=0x24;
        static constexpr std::uint32_t divisor_float_bits=0x42c80000; //100.0f.
        static constexpr std::uint16_t programmsg_zero_based_pointer_index=164;
        static constexpr std::uint16_t programmsg_csv_id=165;
        std::optional<CnProgramMessageCatalog::Record> actual_source_text(
            const CnProgramMessageCatalog& actual_catalog) const {
            return actual_catalog.lookup_zero_based_index(programmsg_zero_based_pointer_index);
        }
        // Actual floating conversion, text provider/GUI gates and rendered
        // result remain separate; a CSV label is not a server-side formula.
    };
    std::uint16_t native_subject_word;
    std::int8_t native_row_byte2;
    bool applies_special_ui_bonus;
    std::array<Scalar,9> scalars;
    std::array<Pair,2> pairs;
    Metric metric;

    static CnSubjectPanelOperands from_actual_row(
        std::span<const std::uint8_t,row_size> actual_row,
        std::optional<InlineUiBonusWords> actual_ui_bonus_words=std::nullopt) noexcept {
        const auto word=[&](std::size_t n) {
            return std::uint16_t(actual_row[n]|(std::uint16_t(actual_row[n+1])<<8));
        };
        const auto dword=[&](std::size_t n) {
            return std::uint32_t(word(n))|(std::uint32_t(word(n+2))<<16);
        };
        const auto identifier=word(0);
        // 16-bit SUB/CMP/JA, independent of the signed portrait selector.
        const bool special=std::uint16_t(identifier-101u)<=7u;
        CnSubjectPanelOperands result{identifier,std::bit_cast<std::int8_t>(actual_row[2]),
            special,{},{{Pair{4,false,dword(0x2c),dword(0x30)},
                       Pair{5,true,word(0x34),word(0x36)}}},Metric{word(0x28)}};
        constexpr std::array<std::uint8_t,9> controls{6,7,8,9,0xb,0xc,0xd,0xe,0xf};
        constexpr std::array<std::uint16_t,9> offsets{0x38,0x3a,0x3c,0x3e,0x44,0x48,0x4c,0x50,0x54};
        // Control F uses UI+42E20, while D/E use UI+42E22/24.
        constexpr std::array<std::size_t,9> bonus_indices{0,1,2,3,4,5,7,8,6};
        for(std::size_t i=0;i<result.scalars.size();++i) {
            const bool is_word=i<4;
            const auto original=is_word?std::uint32_t(word(offsets[i])):dword(offsets[i]);
            std::optional<std::uint16_t> bonus;
            std::optional<std::uint32_t> effective;
            if(!special)effective=original;
            else if(actual_ui_bonus_words) {
                bonus=(*actual_ui_bonus_words)[bonus_indices[i]];
                // Native DWORD ADD presentation only. Never use this wrapped
                // result as the widened common numeric/gameplay calculation.
                effective=original+std::uint32_t(*bonus);
            }
            result.scalars[i]=Scalar{controls[i],offsets[i],is_word,original,bonus,effective};
        }
        return result;
    }
};
}
