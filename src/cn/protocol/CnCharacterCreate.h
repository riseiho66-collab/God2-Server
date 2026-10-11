#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace god2cn {
// Bounded ordinary17 view from the retained upstream CnCharacterRequests.
// Provenance: cn-character-create-fields-agent-01/findings.json and
// cn-character-mutation-contract-01. No mutation, TW CUSTOM profile mapping,
// name conversion or rule authorization is established by reading this record.
class CnCharacterCreate {
public:
    static constexpr std::size_t record_size=45;
    static std::optional<CnCharacterCreate> read(std::span<const std::uint8_t> record) {
        // 0047E900 writes payload40=4 then sends17 with44 payload bytes.
        // 00481390 sends1B instead; its operation/continuation is separate.
        if(record.size()!=record_size || record[0]!=0x17 || record[41]!=4)return std::nullopt;
        CnCharacterCreate value;
        std::copy(record.begin()+1,record.end(),value.payload_.begin());return value;
    }
    std::optional<std::string_view> ui_name() const {
        // Ordinary input0043D8B0 copies <=14 encoded bytes plusNUL. This
        // accessor is optional; do not apply that UI limit to every producer.
        const auto limit=payload_.begin()+15;
        const auto end=std::find(payload_.begin(),limit,0);
        if(end==limit)return std::nullopt;
        return std::string_view{reinterpret_cast<const char*>(payload_.data()),
            static_cast<std::size_t>(end-payload_.begin())};
    }
    std::uint8_t paired_choice_one_based() const {return payload_[29];}
    std::uint8_t masked_choice_one_based() const {return payload_[31];}
    std::uint8_t seven_step_choice() const {return payload_[32];}
    std::uint8_t binary_choice() const {return payload_[33];}
    std::uint16_t appearance_word_36() const {return word(36);}
    std::uint16_t appearance_word_38() const {return word(38);}
    // Retain unknown UI bytes verbatim; raw data is not a common gameplay model.
    // Do not pass opaque0..27/28/30/34..35 or41..43 to Lua as recovered rules.
    std::span<const std::uint8_t,44> payload_bytes() const {return payload_;}
    std::array<std::uint8_t,record_size> record_bytes() const {
        std::array<std::uint8_t,record_size> bytes;
        bytes[0]=0x17;std::copy(payload_.begin(),payload_.end(),bytes.begin()+1);return bytes;
    }
private:
    CnCharacterCreate()=default;
    std::uint16_t word(std::size_t offset) const {
        return static_cast<std::uint16_t>(payload_[offset]|(std::uint16_t(payload_[offset+1])<<8));
    }
    std::array<std::uint8_t,44> payload_{};
};
}
