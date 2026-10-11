#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
//Pinned CN WORLD connection1 S2C only:0048FCC0 ->00534D10/00533430.
//00567B50 qualifies BOTH full records as3 bytes, even though00533430
//does not read its two payload bytes. Preserve them; no fabricated sender.
struct CnWorldExitLifecycleControl {
    enum class Form:std::uint8_t {NativeA0=0xA0,NativeA3=0xA3};
    Form form;
    std::array<std::uint8_t,3> native_record;

    static std::optional<CnWorldExitLifecycleControl> read(std::span<const std::uint8_t> record) {
        if(record.size()!=3 || (record[0]!=0xA0 && record[0]!=0xA3))return std::nullopt;
        return CnWorldExitLifecycleControl{static_cast<Form>(record[0]),
            {record[0],record[1],record[2]}};
    }

    //Readonly native member-write projection, NOT permission/save/replay.
    //A0 observes BYTE(*(owner+430A8)+D4)>0, copies byte1/2 to F74/F75,
    //calls00534640, then clears8AC ONLY after that call normally returns.
    //False gate performs no8AC write. A3 writes1 without this gate.
    //Feed the actual final flag to CnPostWorldExitControl's post-tail
    //projection after its FOUR callbacks; this write alone is not that value.
    std::optional<std::uint32_t> native_8ac_write_after_normal_consumer(
        bool actual_owner_430a8_d4_nonzero) const {
        if(form==Form::NativeA3)return 1;
        if(form==Form::NativeA0 && actual_owner_430a8_d4_nonzero)return 0;
        return std::nullopt;
    }

    //005277A0: ProgramMsg IDs from primary WORD table008A3638.
    //00527650 binds them to item2/item3 at actual WORD handle owner+1C8544.
    //One-based pointers require id!=0 and id<=signed resource+B2F64;
    //otherwise native stores NULL. No replacement UI/font/text is installed.
    static constexpr std::array<std::uint16_t,2> confirmation_programmsg_ids{62,63};
};
}
