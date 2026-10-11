#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace god2 {
// Original 2.40.83 client: common chat producer 4968E0 -> 4132E0 and
// world receiver 46AE96. The optional channel producer 496990 is separate.
struct RecoveredChat {
    static constexpr std::uint8_t c2s_opcode=0x2f;
    static constexpr std::uint8_t s2c_opcode=0x5c;
    static constexpr std::size_t max_text_bytes=254;
    struct Request {
        // The current client can send nonzero bytes here. They are retained
        // for protocol accounting; only the authenticated session selects the
        // sender and common-chat scope.
        std::array<std::uint8_t,4> client_header{};
        std::string legacy_text;
    };

    static std::optional<Request> parse_common(std::span<const std::uint8_t> logical) {
        if(logical.size()<9 || logical.size()>max_text_bytes+8 ||
           logical[0]!=c2s_opcode ||
           (static_cast<std::size_t>(logical[1])+256u*logical[2])!=logical.size() ||
           logical.back()!=0 || logical[7]==0 ||
           std::find(logical.begin()+7,logical.end()-1,0)!=logical.end()-1)
            return std::nullopt;
        Request request{};
        std::copy_n(logical.begin()+3,4,request.client_header.begin());
        request.legacy_text.assign(logical.begin()+7,logical.end()-1);
        return request;
    }

    static std::vector<std::uint8_t> display(std::uint32_t sender,
        bool simplified,std::string_view legacy_text) {
        if(legacy_text.empty() || legacy_text.size()>max_text_bytes ||
           legacy_text.find('\0')!=std::string_view::npos)
            throw std::invalid_argument("Original chat text bounds");
        const auto size=legacy_text.size()+14;
        std::vector<std::uint8_t> logical(size,0);
        logical[0]=s2c_opcode;
        logical[1]=static_cast<std::uint8_t>(size);
        logical[2]=static_cast<std::uint8_t>(size>>8);
        for(unsigned i=0;i<4;++i)logical[5+i]=static_cast<std::uint8_t>(sender>>(8*i));
        logical[9]=simplified?0x80:0;
        std::copy(legacy_text.begin(),legacy_text.end(),logical.begin()+13);
        return logical;
    }
};
}
