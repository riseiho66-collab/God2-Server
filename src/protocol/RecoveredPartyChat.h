#pragma once
#include "protocol/RecoveredChat.h"
namespace god2 {
// Native496990/46AE96: party selector1 uses the existing2F/5C envelopes.
// Retain the unwritten header byte and caller-supplied WORD independently.
struct RecoveredPartyChat {
    struct Request {
        std::array<std::uint8_t,4> client_header{};
        std::string legacy_text;
        bool operator==(const Request&) const=default;
    };
    static bool selected(const RecoveredChat::Request& input) noexcept {
        return (input.client_header[0]&0x7f)==1;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) {
        const auto input=RecoveredChat::parse_common(logical);
        if(!input || !selected(*input))return {};
        return Request{input->client_header,input->legacy_text};
    }
    static std::vector<std::uint8_t> encode(const Request& request) {
        if((request.client_header[0]&0x7f)!=1 || request.legacy_text.empty() ||
           request.legacy_text.size()>RecoveredChat::max_text_bytes ||
           request.legacy_text.find('\0')!=std::string::npos)
            throw std::invalid_argument("Native party2F text/selector bounds");
        const auto size=request.legacy_text.size()+8;
        std::vector<std::uint8_t> out(size,0);
        out[0]=RecoveredChat::c2s_opcode;out[1]=static_cast<std::uint8_t>(size);out[2]=static_cast<std::uint8_t>(size>>8);
        std::copy(request.client_header.begin(),request.client_header.end(),out.begin()+3);
        std::copy(request.legacy_text.begin(),request.legacy_text.end(),out.begin()+7);return out;
    }
    static std::vector<std::uint8_t> display(std::uint32_t sender,bool simplified,std::string_view encoded) {
        auto out=RecoveredChat::display(sender,simplified,encoded);
        out[9]=static_cast<std::uint8_t>((simplified?0x80:0)|1);return out;
    }
};
}
