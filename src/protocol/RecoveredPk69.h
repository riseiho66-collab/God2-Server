#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Pinned mapped149c1b..:970A0/9712E C2S69;6AD80/84620 S2C8A.
// frontier-v3.json contains original instructions. Native format/consumer,
// not recovered server permission, room creation, fees or result authority.
struct RecoveredPk69 {
    static constexpr std::uint8_t opcode=0x69, invitation_opcode=0x8a;
    static constexpr std::size_t logical_size=45;
    using Bytes=std::array<std::uint8_t,logical_size>;
    using Text=std::array<std::uint8_t,16>;
    enum class Control:std::uint8_t { Invite=0,Accept=1,Reject=2,Busy=3 };
    struct Request {
        std::uint32_t first{},second{};
        Text first_text{},second_text{};
        Control control{};
        bool operator==(const Request&)const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> b) {
        if(b.size()!=logical_size||b[0]!=opcode||b[41]>3||b[42]||b[43]||b[44])return {};
        Request r;r.first=read(b,1);r.second=read(b,5);
        std::copy_n(b.begin()+9,16,r.first_text.begin());
        std::copy_n(b.begin()+25,16,r.second_text.begin());
        r.control=static_cast<Control>(b[41]);
        // 970A0 uses unbounded strlen/memcpy; bounded server parsing must not
        // permit a client string to cross the two native16-byte buffers.
        if(!terminated(r.first_text)||!terminated(r.second_text))return {};
        return r;
    }
    static Bytes encode(const Request&r) {
        Bytes b{};b[0]=opcode;put(b,1,r.first);put(b,5,r.second);
        std::copy(r.first_text.begin(),r.first_text.end(),b.begin()+9);
        std::copy(r.second_text.begin(),r.second_text.end(),b.begin()+25);
        b[41]=static_cast<std::uint8_t>(r.control);return b;
    }
    // Right-click action-5 supplies NULL,NULL. Limit this integration to that
    // source-qualified branch; arbitrary text producers remain unqualified.
    static bool right_click(const Request&r) {
        return r.control==Control::Invite&&r.first&&r.second&&r.first!=r.second&&
            r.first_text==Text{}&&r.second_text==Text{};
    }
    // CUSTOM-0086 request->invitation pairing. Consumer8A reads IDs/texts;
    // final four bytes have no recovered wrapper semantics and stay zero.
    // 8A ID+1 supplies FAC70's existing scene-player display-name lookup.
    static Bytes invitation(const Request&r) {
        auto b=encode(r);b[0]=invitation_opcode;b[41]=0;return b;
    }
    // 84620 saves +5,+1,+25,+9;970A0 reserializes that context. Do not use
    // 8B/8C or preserve the invitation's incoming ID order on replies.
    static Request expected_reply(const Request&r,Control control) {
        return {r.second,r.first,r.second_text,r.first_text,control};
    }
private:
    static bool terminated(const Text&t){return std::find(t.begin(),t.end(),0)!=t.end();}
    static std::uint32_t read(std::span<const std::uint8_t>b,std::size_t p){
        return std::uint32_t{b[p]}|(std::uint32_t{b[p+1]}<<8)|
            (std::uint32_t{b[p+2]}<<16)|(std::uint32_t{b[p+3]}<<24);
    }
    static void put(Bytes&b,std::size_t p,std::uint32_t n){for(unsigned i=0;i<4;++i)b[p+i]=static_cast<std::uint8_t>(n>>(8*i));}
};
}
