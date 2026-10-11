#include "cn/text/CnChatContent.h"

namespace god2cn {
bool CnChatContent::has_control_bytes(std::string_view text) {
    for(const unsigned char byte:text)if(byte<0x20 || byte==0x7f)return true;
    return false;
}
CnChatContent CnChatContent::split(const CnChat::Request& request) {
    const std::string_view text=request.text;
    if(text.empty())return {};
    // 0054B470 consumes channel1 text containing native05/16 battle control.
    // A plain Chinese converter must never rewrite those fields or link tokens.
    if(has_control_bytes(text))return {Kind::Structured,{},text};
    // 004B1390 recognizes /board and /board<space>, routing it through channel0.
    if(text=="/board" || text.starts_with("/board "))return {Kind::Board,{},text};
    if(request.channel==2 || request.channel==9) {
        // 007F2F90 = "$%s %s", used by004B1390 and the channel9 auto reply.
        // Target names retain their original script/bytes for authoritative lookup.
        const auto delimiter=text.find(' ');
        if(text.front()!='$' || delimiter==std::string_view::npos || delimiter<=1 || delimiter+1>=text.size())return {};
        return {Kind::NamedWhisper,text.substr(1,delimiter-1),text.substr(delimiter+1)};
    }
    switch(request.channel) {
    case 0:case 1:case 3:case 13:case 18:
        // A leading named-whisper marker in a different channel is rewritten
        // by the native producer; do not treat an unresolved variant as prose.
        if(text.front()=='$' || (request.channel==18 && text.front()=='^'))return {};
        return {Kind::PlayerText,{},text};
    default:return {};
    }
}
}
