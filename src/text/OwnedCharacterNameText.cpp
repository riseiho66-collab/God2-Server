#include "text/OwnedCharacterNameText.h"
#include "text/LegacyChineseCodec.h"
#include "text/ChineseText.h"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace god2 {
namespace {
bool name_ascii(std::string_view bytes) {
    return std::all_of(bytes.begin(),bytes.end(),[](unsigned char c){return c<128;});
}
bool name_bytes(std::string_view bytes) {
    return !bytes.empty() && bytes.size()<=14 && bytes.find('\0')==bytes.npos;
}
}
OwnedCharacterNameText::OwnedCharacterNameText(std::string encoded,std::string utf8,std::uint16_t page)
    :encoded_(std::move(encoded)),utf8_(std::move(utf8)),codepage_(page) {}
std::optional<OwnedCharacterNameText> OwnedCharacterNameText::from_encoded(std::string_view bytes,std::uint16_t page) {
    if(!name_bytes(bytes) || (page!=0 && page!=936 && page!=950))return std::nullopt;
    //0 is an existing unbound common metadata value, not CP_ACP/host locale.
    // Only unchanged ASCII is unambiguous until an actual owner binds encoding.
    if(page==0)return name_ascii(bytes)?std::optional<OwnedCharacterNameText>{
        OwnedCharacterNameText(std::string(bytes),std::string(bytes),0)}:std::nullopt;
    try {
        auto utf8=LegacyChineseCodec::decode(bytes,page==936);
        if(!ChineseText::valid_utf8(utf8) || utf8.empty() || utf8.find('\0')!=utf8.npos ||
           LegacyChineseCodec::encode(utf8,page==936)!=bytes)return std::nullopt;
        return OwnedCharacterNameText(std::string(bytes),std::move(utf8),page);
    }catch(const std::invalid_argument&) {return std::nullopt;}
}
std::optional<OwnedCharacterNameText> OwnedCharacterNameText::from_utf8(std::string_view utf8,std::uint16_t page) {
    if(utf8.empty() || utf8.find('\0')!=utf8.npos || !ChineseText::valid_utf8(utf8) ||
       (page!=0 && page!=936 && page!=950))return std::nullopt;
    if(page==0)return name_ascii(utf8)?from_encoded(utf8,0):std::nullopt;
    try {
        const auto encoded=LegacyChineseCodec::encode(utf8,page==936);
        auto value=from_encoded(encoded,page);
        if(!value || value->original_utf8()!=utf8)return std::nullopt;
        return value;
    }catch(const std::invalid_argument&) {return std::nullopt;}
}
}
