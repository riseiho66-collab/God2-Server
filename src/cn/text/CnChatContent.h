#pragma once
#include "cn/protocol/CnChat.h"
#include <string_view>

namespace god2cn {
// Native envelope classification, not a channel permission decision. Views
// borrow Request::text and must not outlive/move that request.
struct CnChatContent {
    enum class Kind {PlayerText,NamedWhisper,Board,Structured,Unresolved};
    Kind kind=Kind::Unresolved;
    std::string_view target_wire_name;
    std::string_view body_wire_text;
    static CnChatContent split(const CnChat::Request& request);
    static bool has_control_bytes(std::string_view text);
};
}
