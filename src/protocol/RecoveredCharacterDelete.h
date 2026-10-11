#pragma once
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <array>
#include <optional>
#include <span>

namespace god2 {
// Current mapped image RVA152E0 queues opcode19 with 53 payload bytes.
// Strings begin at payload0,16,37; selection at32, language marker at33.
// Unwritten padding bytes34..36 are deliberately not constrained.
struct RecoveredCharacterDelete {
    static constexpr std::size_t wire_size=57;
    std::array<std::uint8_t,16> account{},password{},name{};
    std::uint8_t token{};
    static std::optional<RecoveredCharacterDelete> parse(std::span<const std::uint8_t> wire) {
        if(wire.size()!=wire_size)return std::nullopt;
        const auto logical=RecoveredWorldFrame::decode(wire);
        if(!logical || logical->size()!=54 || (*logical)[0]!=0x19 ||
           (*logical)[33]>=2 || (*logical)[34]!=4)return std::nullopt;
        RecoveredCharacterDelete result;result.token=(*logical)[33];
        std::copy_n(logical->begin()+1,16,result.account.begin());
        std::copy_n(logical->begin()+17,16,result.password.begin());
        std::copy_n(logical->begin()+38,16,result.name.begin());
        for(const auto* field:{&result.account,&result.password,&result.name})
            if(field->front()==0 || std::find(field->begin(),field->end(),0)==field->end())return std::nullopt;
        return result;
    }
    // RVA15475 checks WORD+1; zero consumes record and returns success.
    // The opcode02 S2C length table specifies23 bytes, shared by selection.
    static std::vector<std::uint8_t> response(bool accepted) {
        std::array<std::uint8_t,23> logical{};logical[0]=2;
        if(!accepted)logical[1]=1;
        return RecoveredWorldFrame::encode(logical);
    }
};
}
