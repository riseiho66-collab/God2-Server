#pragma once
#include "db/NativeBeastSourceCatalog.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Mapped149c1b45: class5 tooltip B90E7..B95EA, original PET parser5970D.
// Field interpretation only. No grant, food award, level threshold, cap,
// riding/teleport authority, elapsed-time increment or expiry rule.
struct RecoveredBeastInventoryFields {
    using Metadata=std::array<std::uint8_t,20>;
    enum class DisplayBranch {ClassicUses,ClassicElapsedMinutes,PackedDate};
    struct View {
        Metadata bytes;
        std::uint8_t tooltip_date_flag_byte;
        std::uint16_t key() const noexcept {return word(bytes,0);}
        std::uint16_t fatigue_limit_raw14() const noexcept {return word(bytes,4)&0x3fff;}
        std::uint16_t mode_raw2() const noexcept {return word(bytes,4)>>14;}
        std::uint8_t palette_raw3() const noexcept {return bytes[10]&7;}
        bool native_exploring_label() const noexcept {
            return mode_raw2()==2&&bytes[8]==1;
        }
        DisplayBranch display_branch() const noexcept {
            if(tooltip_date_flag_byte!=0)return DisplayBranch::PackedDate;
            return mode_raw2()==1||mode_raw2()==2?
                DisplayBranch::ClassicElapsedMinutes:DisplayBranch::ClassicUses;
        }
        std::optional<std::uint8_t> level_raw() const noexcept {
            if(tooltip_date_flag_byte!=0)return {};
            return bytes[9];
        }
        // Original tooltip FILD WORD+12 -> FLOAT0.01 -> %6.2f%s/Program58.
        // Retain integer wire value; do not invert display float as an award.
        std::optional<std::uint16_t> experience_percent_word_raw() const noexcept {
            if(tooltip_date_flag_byte!=0)return {};
            return word(bytes,12);
        }
        std::optional<std::uint16_t> use_count_raw() const noexcept {
            if(display_branch()!=DisplayBranch::ClassicUses)return {};
            return word(bytes,14);
        }
        std::optional<std::uint16_t> elapsed_minutes_raw() const noexcept {
            if(display_branch()!=DisplayBranch::ClassicElapsedMinutes)return {};
            return word(bytes,14);
        }
        // B955C is only reached in the classic elapsed-minutes branch.
        std::optional<std::uint16_t> transfer_use_count_raw15() const noexcept {
            if(display_branch()!=DisplayBranch::ClassicElapsedMinutes||(word(bytes,16)&0x8000)==0)return {};
            return word(bytes,16)&0x7fff;
        }
        std::optional<std::uint32_t> packed_date_raw() const noexcept {
            if(display_branch()!=DisplayBranch::PackedDate)return {};
            // B928F clears DL before SHL8; B929D shifts the combined DWORD14.
            const auto upper=((std::uint32_t{word(bytes,8)}&0xff00)<<8)|word(bytes,12);
            return (upper<<14)|word(bytes,14);
        }
    };
    static std::optional<View> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=20||(bytes[2]&0x3f)!=5)return {};
        const auto* definition=NativeBeastSourceCatalog::lookup(word(bytes,0));
        if(!definition)return {};
        View value{{},definition->tooltip_date_flag_byte};
        std::copy(bytes.begin(),bytes.end(),value.bytes.begin());return value;
    }
private:
    static std::uint16_t word(std::span<const std::uint8_t> bytes,std::size_t offset) noexcept {
        return static_cast<std::uint16_t>(bytes[offset]|(std::uint16_t{bytes[offset+1]}<<8));
    }
};
}
