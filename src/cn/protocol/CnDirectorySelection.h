#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <vector>

namespace god2cn {
// Pinned0050E5E0 UI-state selection and0050E3B0 request producer.
// Evidence:cn-directory-selection-producer-01. UI inputs are not on the wire,
// common entity IDs, server permissions or evidence that no other producer exists.
class CnDirectorySelection {
public:
    struct Origin {
        bool native_mode_bit0;
        std::int32_t ui_state,group;
        std::optional<std::int32_t> secondary; // Null means mapper ignores this input.
        std::uint8_t selector; // Zero can be a real native result, not a failure sentinel.
    };
    // All explicit successful local branches of this one mapper. Group2
    // ignores secondary; the calling producer separately suppresses either-1.
    inline static constexpr std::array<Origin,43> origins{{
        {true,0x2f,1,0,0x24},{true,0x2f,1,1,0x23},{true,0x2f,2,std::nullopt,0x19},
        {false,0x2f,0,0,0x01},{false,0x2f,0,1,0x00},
        {false,0x48,0,0,0x1f},{false,0x48,0,1,0x1e},
        {false,0x2f,1,0,0x03},{false,0x31,1,0,0x27},
        {false,0x32,1,0,0x2a},{false,0x33,1,0,0x2c},
        {false,0x2f,1,1,0x02},{false,0x31,1,1,0x28},
        {false,0x32,1,1,0x2b},{false,0x33,1,1,0x2d},
        {false,0x34,1,1,0x21},{false,0x35,1,1,0x22},
        {false,0x39,1,1,0x17},{false,0x3a,1,1,0x18},{false,0x3e,1,1,0x1b},
        {false,0x2f,2,std::nullopt,0x04},{false,0x30,2,std::nullopt,0x13},
        {false,0x34,2,std::nullopt,0x21},{false,0x35,2,std::nullopt,0x22},
        {false,0x36,2,std::nullopt,0x25},{false,0x37,2,std::nullopt,0x26},
        {false,0x38,2,std::nullopt,0x29},{false,0x39,2,std::nullopt,0x11},
        {false,0x3a,2,std::nullopt,0x12},{false,0x3b,2,std::nullopt,0x14},
        {false,0x3d,2,std::nullopt,0x0b},{false,0x3e,2,std::nullopt,0x1b},
        {false,0x3f,2,std::nullopt,0x0f},{false,0x40,2,std::nullopt,0x10},
        {false,0x41,2,std::nullopt,0x05},{false,0x42,2,std::nullopt,0x0e},
        {false,0x43,2,std::nullopt,0x06},{false,0x44,2,std::nullopt,0x07},
        {false,0x45,2,std::nullopt,0x08},{false,0x46,2,std::nullopt,0x09},
        {false,0x47,2,std::nullopt,0x0a},{false,0x48,2,std::nullopt,0x20},
        {false,0x4c,2,std::nullopt,0x0c}
    }};
    struct Result {
        std::uint8_t selector;
        std::optional<std::uint32_t> diagnostic_line;
        bool explicit_origin;
    };
    static Result select(bool mode,std::int32_t state,std::int32_t group,std::int32_t secondary) {
        for(const auto& origin:origins)
            if(origin.native_mode_bit0==mode && origin.ui_state==state && origin.group==group &&
               (!origin.secondary || *origin.secondary==secondary))return {origin.selector,std::nullopt,true};
        // Native default returns0. Some paths log a diagnostic, others return
        // silently. Preserve that distinction without issuing a wire reply.
        if(mode) {
            if(group==2)return {0,std::nullopt,false};
            if(group!=1)return {0,0x10a3,false};
            return {0,secondary==0?0x1087u:secondary==1?0x1092u:0x1096u,false};
        }
        if(group==2)return {0,std::nullopt,false};
        if(group==0) {
            if(state==0x2f)return {0,0x10b3,false};
            if(state==0x48)return {0,0x10bb,false};
            return {0,0x10be,false};
        }
        if(group==1)return {0,secondary==0?0x10dbu:secondary==1?0x1111u:0x1115u,false};
        return {0,0x118a,false};
    }
    static std::vector<Origin> known_origins(bool mode,std::uint8_t selector) {
        std::vector<Origin> result;
        for(const auto& origin:origins)
            if(origin.native_mode_bit0==mode && origin.selector==selector)result.push_back(origin);
        return result; // Empty is no explicit branch in this mapper, not forbidden traffic.
    }
    enum class CursorKind {PlayerField,Indirect1C85A8Field,GenericSelectorField,None,UnassignedStack};
    struct Producer {
        bool sends94,sendsD1; // When both are true, native sendsD1 first.
        CursorKind cursor_kind;
        std::optional<std::uint32_t> owner_cursor_offset;
    };
    static Producer producer(bool mode,std::uint8_t selector) {
        if(!mode) {
            switch(selector) {
            case 0x25:case 0x26:return {false,true,CursorKind::None,std::nullopt}; // D1 only.
            case 0x27:case 0x28:return {true,true,CursorKind::UnassignedStack,std::nullopt};
            case 0x11:return {true,false,CursorKind::PlayerField,0x2e234};
            case 0x12:return {true,false,CursorKind::PlayerField,0x2f1fc};
            case 0x15:return {true,false,CursorKind::PlayerField,0x30688};
            case 0x16:return {true,false,CursorKind::PlayerField,0x36560};
            case 0x17:return {true,false,CursorKind::PlayerField,0x345d0};
            case 0x18:return {true,false,CursorKind::PlayerField,0x35598};
            case 0x1b:return {true,false,CursorKind::PlayerField,0x31678};
            case 0x21:return {true,false,CursorKind::PlayerField,0x32640};
            case 0x22:return {true,false,CursorKind::PlayerField,0x33608};
            default:break;
            }
        }
        switch(selector) {
        case 0x19:return {true,false,CursorKind::PlayerField,0x30e80};
        case 0x23:return {true,false,CursorKind::PlayerField,0x36d58};
        case 0x24:return {true,false,CursorKind::Indirect1C85A8Field,0x46a8};
        default:return {true,false,CursorKind::GenericSelectorField,0x22d0c+std::uint32_t{selector}*0x3f0};
        }
    }
    static bool caller_suppresses(std::int32_t group,std::int32_t secondary) {
        return group==-1 || secondary==-1;
    }
};
}
