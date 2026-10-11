#pragma once
#include "protocol/RecoveredChat.h"
namespace god2 {
// Native496990: private2 and automatic reply9 retain the2F envelope.
// Recipient authority is in "$name message", never the opaque caller WORD.
struct RecoveredPrivateChat {
    struct Request {
        std::array<std::uint8_t,4> client_header{};
        std::string legacy_text;
        bool operator==(const Request&) const=default;
    };
    struct Text {std::string recipient,message;bool operator==(const Text&) const=default;};
    static bool selected(const RecoveredChat::Request& input) noexcept {
        const auto mode=input.client_header[0]&0x7f;return mode==2 || mode==9;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) {
        const auto input=RecoveredChat::parse_common(logical);
        if(!input || !selected(*input))return {};
        return Request{input->client_header,input->legacy_text};
    }
    static std::vector<std::uint8_t> encode(const Request& request) {
        const auto mode=request.client_header[0]&0x7f;
        if((mode!=2 && mode!=9) || request.legacy_text.empty() ||
           request.legacy_text.size()>RecoveredChat::max_text_bytes ||
           request.legacy_text.find('\0')!=std::string::npos)
            throw std::invalid_argument("Native private2F text/selector bounds");
        const auto size=request.legacy_text.size()+8;
        std::vector<std::uint8_t> out(size,0);out[0]=0x2f;
        out[1]=static_cast<std::uint8_t>(size);out[2]=static_cast<std::uint8_t>(size>>8);
        std::copy(request.client_header.begin(),request.client_header.end(),out.begin()+3);
        std::copy(request.legacy_text.begin(),request.legacy_text.end(),out.begin()+7);return out;
    }
    // Operate on decoded Unicode, not raw DBCS bytes. Native delimiter005823C8
    // is ASCII space; the producer skips repeated separator spaces.
    static std::optional<Text> split(std::string_view unicode) {
        if(unicode.size()<4 || unicode.front()!='$' || unicode.find('\0')!=std::string_view::npos)return {};
        const auto space=unicode.find(' ',1);
        if(space==std::string_view::npos || space==1)return {};
        const auto start=unicode.find_first_not_of(' ',space);
        if(start==std::string_view::npos)return {};
        return Text{std::string(unicode.substr(1,space-1)),std::string(unicode.substr(start))};
    }
    static std::vector<std::uint8_t> display(std::uint32_t sender,bool simplified,
        std::uint8_t mode,std::string_view encoded) {
        if(mode!=2 && mode!=9)throw std::invalid_argument("Native private display mode");
        auto out=RecoveredChat::display(sender,simplified,encoded);
        out[9]=static_cast<std::uint8_t>((simplified?0x80:0)|mode);return out;
    }
};
}
