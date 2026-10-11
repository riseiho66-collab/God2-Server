#pragma once
#include "cn/protocol/CnWorldConsumerRecords.h"

namespace god2cn {
// Pinned WORLD31 ->004D58B0, independent of C2S31/68/6D. Exact native
// operand projection; no stat names, common actor ID or authoritative rules.
class CnSubjectStatus31 final {
public:
    static constexpr std::size_t record_size=29;
    struct Fields {
        std::uint16_t native_target_word; // Sign-extended BYTE, not zero-extended.
        std::uint8_t native_entry_byte2;
        std::array<std::uint32_t,5> native_entry_dwords44_through54;
        std::array<std::uint16_t,4> native_entry_words38_through3E;
        std::uint16_t native_entry_word28;
        std::uint8_t native_entry_byte5A;
        std::array<std::uint8_t,6> unconsumed_payload_bytes; //12..15,26..27.
    };
    static std::optional<CnSubjectStatus31> read(std::span<const std::uint8_t> record) {
        const auto exact=CnOwnedRowRecord31::parse_logical(record);
        if(!exact)return std::nullopt;
        std::array<std::uint8_t,record_size> bytes;
        std::copy(record.begin(),record.end(),bytes.begin());return CnSubjectStatus31(bytes);
    }
    std::array<std::uint8_t,record_size> record_bytes() const noexcept {return bytes_;}
    //004D58D8 MOVSX CX,BYTE[actual payload];004D58E0 compares WORD entry+0.
    //This differs from WORLD34/35's zero-extended subject byte comparison.
    std::uint16_t native_target_word() const noexcept {
        const int raw=bytes_[1];return static_cast<std::uint16_t>(raw<128?raw:raw-256);
    }
    //004D58B0 stops at the first equal WORD within the actual BYTE roster count.
    //Caller supplies the qualified real roster in its order. A match alone
    //is not common identity/ownership, permission or server mutation authority.
    std::optional<std::size_t> first_native_roster_match(
        std::span<const std::uint16_t> actual_roster_identifiers) const noexcept {
        for(std::size_t n=0;n<actual_roster_identifiers.size();++n)
            if(actual_roster_identifiers[n]==native_target_word())return n;
        return std::nullopt;
    }
    Fields native_fields() const noexcept {
        //Payload2/4/6/8/10 are zero-extended WORDs into DWORD storage.
        //Native payload24 splits into low15 WORD and high1 BYTE; keep the raw
        //record too. No clipping/widened native profile or numeric cap implied.
        const auto split=payload_word(24);
        return Fields{native_target_word(),bytes_[2],
            {payload_word(2),payload_word(4),payload_word(6),payload_word(8),payload_word(10)},
            {payload_word(16),payload_word(18),payload_word(20),payload_word(22)},
            static_cast<std::uint16_t>(split&0x7fff),static_cast<std::uint8_t>(split>>15),
            {bytes_[13],bytes_[14],bytes_[15],bytes_[16],bytes_[27],bytes_[28]}};
    }
private:
    explicit CnSubjectStatus31(std::array<std::uint8_t,record_size> bytes):bytes_(bytes) {}
    std::uint16_t payload_word(std::size_t at) const noexcept {
        return static_cast<std::uint16_t>(bytes_[at+1]|(std::uint16_t(bytes_[at+2])<<8));
    }
    std::array<std::uint8_t,record_size> bytes_;
};
}
