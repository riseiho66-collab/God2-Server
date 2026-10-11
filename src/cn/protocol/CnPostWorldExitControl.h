#pragma once
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
//0044A470 post-game return switch0044A960 ->same main+458 game transport.
//Cases1/2 send0201;case3 sends0200;case5 sends0200;case6 sends0202.
//These values have no recovered backend permission/reason/saving semantics.
//Pre-world0203/0204 remain in their separate mutation/lifecycle contract.
struct CnPostWorldExitControl {
    enum class Form:std::uint8_t {Native0=0,Native1=1,Native2=2};
    struct NativeWorldReturn {
        std::uint32_t loop_state;
        std::uint32_t main_return_eax;
        std::optional<Form> close_at_main_switch;
        bool calls_00480c50;
    };
    //Readonly internal-client lineage, NOT a wire field or server permission.
    //0048DA20 table0048E080 ->EAX ->0044A470 table0044A960.
    //State5 returns4 and has NO close at that main switch. States3/4 run
    //frame/transition branches; unsigned states>7 loop without this return.
    //Real pending operations/saves/native03 still require their actual owner.
    static constexpr std::optional<NativeWorldReturn> native_world_return(std::uint32_t state) {
        switch(state) {
        case 0:return NativeWorldReturn{state,1,Form::Native1,true};
        case 1:return NativeWorldReturn{state,2,Form::Native1,true};
        case 2:return NativeWorldReturn{state,6,Form::Native2,true};
        case 5:return NativeWorldReturn{state,4,std::nullopt,false};
        case 6:return NativeWorldReturn{state,5,Form::Native0,false};
        case 7:return NativeWorldReturn{state,3,Form::Native0,true};
        default:return std::nullopt;
        }
    }
    struct NativeCommandReturn {
        std::int32_t raw_command;
        NativeWorldReturn world_return;
    };
    //Actual signed004AE370 return consumed by0048AA10's primary selector
    //tables. Internal UI return values are not packets or backend reasons.
    static constexpr std::optional<NativeCommandReturn> native_command_return(std::int32_t command) {
        std::optional<NativeWorldReturn> result;
        switch(command) {
        case -26:result=native_world_return(2);break;
        case -15:result=native_world_return(5);break;
        case -9:result=native_world_return(1);break;
        case -2:result=native_world_return(0);break;
        default:return std::nullopt;
        }
        return NativeCommandReturn{command,*result};
    }
    //004AE370's four tail callbacks run BEFORE observing actual owner+8AC.
    //Use its post-callback value; no cached/predicted flag or server authority.
    static constexpr std::int32_t native_command_after_tail(std::int32_t before,
        std::int32_t actual_post_callback_8ac) {
        return actual_post_callback_8ac==1?-15:before;
    }
    Form form;
    static std::optional<CnPostWorldExitControl> read(std::span<const std::uint8_t> record) {
        if(record.size()!=2 || record[0]!=0x02 || record[1]>2)return std::nullopt;
        return CnPostWorldExitControl{static_cast<Form>(record[1])};
    }
};
}
