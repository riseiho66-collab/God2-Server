#pragma once
#include "protocol/RecoveredChat.h"
namespace god2 {
// CUSTOM-0054: negotiated deployment extension for the matching embedded client.
// Native 5C framing retained; reserved bytes ST/version1 identify presentation.
// mode1 is consumed silently by the new client before native bubble/panel code.
struct StreamerPresentation {
 static void annotate(std::vector<std::uint8_t>& logical,std::uint8_t style) {
  if(style>3 || logical.size()<14 || logical[0]!=0x5c)throw std::invalid_argument("Streamer presentation bounds");
  logical[3]='S';logical[4]='T';logical[10]=style;logical[11]=1;logical[12]=0;
 }
 static std::vector<std::uint8_t> metadata(std::uint32_t character,std::uint8_t style,bool simplified,std::string_view name) {
  if(!character||character>0x3fff||name.empty()||name.size()>14)throw std::invalid_argument("Streamer identity bounds");
  auto out=RecoveredChat::display(character,simplified,name);annotate(out,style);out[12]=1;return out;
 }
};
}
