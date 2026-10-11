#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Pinned WORLD/BATTLE22 ->00519590 -> actual UI+430A8 role object.
// Original25-byte status, not a level-up command or an authority/growth model.
// Caller must qualify actual CN provenance; a matching TW diagnostic layout
// is not authoritative input. This reader never infers request/reply pairing.
class CnRoleStatus {
public:
    static constexpr std::size_t record_size=25;
    static std::optional<CnRoleStatus> read(std::span<const std::uint8_t> record) {
        if(record.size()!=record_size || record[0]!=0x22)return std::nullopt;
        std::array<std::uint8_t,record_size> bytes;
        std::copy(record.begin(),record.end(),bytes.begin());return CnRoleStatus(bytes);
    }
    bool operator==(const CnRoleStatus&) const = default;
    std::array<std::uint8_t,record_size> record_bytes() const noexcept {return bytes_;}
    //005195A2 role+26;00519700 zero-extends BYTE before %d/control5.
    std::uint8_t native_level_byte() const noexcept {return bytes_[1];}
    std::uint16_t state_word_raw() const noexcept {return word(3);}
    //005195D8/E5/F2/00519602 zero-extend WORDs to role+78/7C/80/84.
    // No growth, attack/defense, enemy attributes or resource formulas inferred.
    std::array<std::uint16_t,4> stat_words_raw() const noexcept {return {word(5),word(7),word(9),word(11)};}
    std::uint16_t progress_word_raw() const noexcept {return word(13);}
    std::array<std::uint32_t,2> resource_dwords_raw() const noexcept {return {dword(17),dword(21)};}
    // Not read by this00519590 prefix: preserve, never label padding/zero.
    std::array<std::uint8_t,3> unconsumed_bytes_raw() const noexcept {return {bytes_[2],bytes_[15],bytes_[16]};}
    // CN07's004438BE/C8 transforms FF to1 locally; CN22's panel keeps255.
    // That value cannot represent the same displayed level in this projection.
    // Do not clamp, wrap, alter progression or claim a common gameplay cap.
    std::optional<std::uint8_t> exact_selection_level_byte() const noexcept {
        if(native_level_byte()==0xff)return std::nullopt;
        return native_level_byte();
    }
private:
    explicit CnRoleStatus(std::array<std::uint8_t,record_size> bytes):bytes_(bytes) {}
    std::uint16_t word(std::size_t at) const noexcept {
        return static_cast<std::uint16_t>(bytes_[at]|(std::uint16_t{bytes_[at+1]}<<8));
    }
    std::uint32_t dword(std::size_t at) const noexcept {return word(at)|(std::uint32_t{word(at+2)}<<16);}
    std::array<std::uint8_t,record_size> bytes_;
};
}
