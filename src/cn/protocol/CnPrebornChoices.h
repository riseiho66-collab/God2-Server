#pragma once
#include "cn/protocol/CnWorldExitLifecycleControl.h"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <variant>
#include <vector>
#include <utility>

namespace god2cn {
//Pinned original preborn.cpp UI context, WORLD connection1 only.
//00534810's complete primary CFG queues81 then83 from mode1/item6 with8A8=0.
//Do not apply this contract to BATTLE's same opcode values.
struct CnPrebornChoices {
    struct Limits {
        std::uint8_t mimic_selections;
        std::uint8_t special_skill_selections;
        bool operator==(const Limits&) const=default;
    };
    struct Mask {std::uint8_t raw;}; //Preserve high bits;00533290 observes only0..3.
    struct Words {std::vector<std::uint16_t> raw;}; //Native low-byte ID/high-byte kind, no entitlement.
    using Request=std::variant<Mask,Words>;

    //A0 record bytes1/2 ->F74/F75 ->mode0/1 remaining-count displays.
    //ProgramMsg281/282 qualify labels; byte counts are NOT server rules.
    static std::optional<Limits> read_limits(std::span<const std::uint8_t> record) {
        const auto control=CnWorldExitLifecycleControl::read(record);
        if(!control || control->form!=CnWorldExitLifecycleControl::Form::NativeA0)return std::nullopt;
        return Limits{record[1],record[2]};
    }
    static std::optional<std::size_t> request_size(std::span<const std::uint8_t> rest) {
        if(rest.empty())return std::nullopt;
        if(rest[0]==0x81)return rest.size()>=2?std::optional<std::size_t>{2}:std::nullopt;
        if(rest[0]!=0x83 || rest.size()<3)return std::nullopt;
        const auto length=std::size_t(rest[1])+256u*rest[2];
        if(length<3 || (length-3)%2 || length>rest.size())return std::nullopt;
        return length;
    }
    static std::optional<Mask> read_mask(std::span<const std::uint8_t> record,std::uint8_t opcode) {
        if((opcode!=0x81 && opcode!=0xA1) || record.size()!=2 || record[0]!=opcode)return std::nullopt;
        return Mask{record[1]};
    }
    static std::optional<Words> read_words(std::span<const std::uint8_t> record,std::uint8_t opcode) {
        if((opcode!=0x83 && opcode!=0xA2) || record.size()<3 || record[0]!=opcode)return std::nullopt;
        const auto length=std::size_t(record[1])+256u*record[2];
        if(length!=record.size() || length<3 || (length-3)%2)return std::nullopt;
        Words result;result.raw.reserve((length-3)/2);
        for(std::size_t n=3;n<length;n+=2)
            result.raw.push_back(static_cast<std::uint16_t>(record[n]+256u*record[n+1]));
        return result;
    }
    static std::optional<Request> read_request(std::span<const std::uint8_t> record) {
        if(record.empty())return std::nullopt;
        if(record[0]==0x81) {auto mask=read_mask(record,0x81);if(mask)return Request{*mask};}
        if(record[0]==0x83) {auto words=read_words(record,0x83);if(words)return Request{std::move(*words)};}
        return std::nullopt;
    }
    //Qualified family shapes only. Actual reply selection/order/all fields,
    //client capacity, rule/save/replay and revision belong to the real issuer.
    static bool supported_reply(std::span<const std::uint8_t> record) {
        if(record.empty())return false;
        switch(record[0]) {
        case 0xA0:case 0xA3:return bool(CnWorldExitLifecycleControl::read(record));
        case 0xA1:return bool(read_mask(record,0xA1));
        case 0xA2:return bool(read_words(record,0xA2));
        default:return false;
        }
    }
};
}
