#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace god2cn {
// Native0047E960, reached through the actual world network UI+16180.
// Retained upstream record53 parsing; credentials are claims to compare with
// this connection's owned identity, never an independent deletion authority.
// Evidence: cn-character-mutation-contract-01 and upstream lifecycle snapshot.
class CnCharacterDelete {
public:
    static constexpr std::size_t record_size=54;
    ~CnCharacterDelete() {
        volatile std::uint8_t* p=payload_.data();
        for(std::size_t i=0;i<payload_.size();++i)p[i]=0;
    }
    static std::optional<CnCharacterDelete> read(std::span<const std::uint8_t> record) {
        if(record.size()!=record_size || record[0]!=0x19)return std::nullopt;
        const auto payload=record.subspan(1);
        // Callers emit summary-row19&7, not the row ordinal. Unlike TW's
        // bounded two-slot parser, all native low3 values are structural here.
        if(payload[32]>=8 || payload[33]!=4)return std::nullopt;
        for(const auto offset:{0u,16u,37u})
            if(std::find(payload.begin()+offset,payload.begin()+offset+16,0)==payload.begin()+offset+16)
                return std::nullopt;
        CnCharacterDelete value;
        std::copy(payload.begin(),payload.end(),value.payload_.begin());return value;
    }
    std::string_view account() const {return field(0);}
    std::string_view credential() const {return field(16);}
    std::string_view character_name() const {return field(37);}
    std::uint8_t native_slot() const {return payload_[32];}
    // Bytes34..36 and string tails are native unwritten bytes. No zero check,
    // name/codepage normalization, logging, Lua exposure or guessed02 reply.
private:
    CnCharacterDelete()=default;
    std::string_view field(std::size_t offset) const {
        const auto start=payload_.begin()+offset;
        const auto end=std::find(start,start+16,0);
        return {reinterpret_cast<const char*>(payload_.data()+offset),
                static_cast<std::size_t>(end-start)};
    }
    std::array<std::uint8_t,53> payload_{};
};
}
