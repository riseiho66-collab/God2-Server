#include "protocol/RecoveredGuildAnnouncement.h"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using Codec=god2::RecoveredGuildAnnouncement;
namespace {
unsigned checks=0;
void check(bool condition) {
    ++checks;if(!condition)throw std::runtime_error("Announcement check "+std::to_string(checks));
}
template<class F> void rejects(F fn) {
    bool threw=false;try{fn();}catch(const std::invalid_argument&){threw=true;}check(threw);
}
std::string utf8(std::u8string_view s) {return {reinterpret_cast<const char*>(s.data()),s.size()};}
void wire() {
    check(Codec::encode_request({})==std::optional(Codec::Logical{0x79,4,0,0}));
    check(Codec::update({})==std::optional(Codec::Logical{0x98,4,0,0}));
    check(Codec::decode(Codec::Logical{0x79,4,0,0})==std::optional(Codec::Request{}));
    // Recorded native getter: row1 "line1", row2 "line2" concatenate without CRLF.
    const Codec::Request text{{'l','i','n','e','1','l','i','n','e','2'}};
    const Codec::Logical native{0x79,14,0,'l','i','n','e','1','l','i','n','e','2',0};
    check(Codec::encode_request(text)==native);check(Codec::decode(native)==text);
    for(unsigned op=0;op<256;++op) {
        auto value=native;value[0]=static_cast<std::uint8_t>(op);
        check(Codec::decode(value).has_value()==(op==0x79));
    }
    // Exhaustive WORD collision/truncation attack against one valid record.
    for(unsigned size=0;size<65536;++size) {
        auto value=native;value[1]=static_cast<std::uint8_t>(size);value[2]=static_cast<std::uint8_t>(size>>8);
        check(Codec::decode(value).has_value()==(size==native.size()));
    }
    for(std::size_t n=0;n<native.size();++n)check(!Codec::decode(std::span(native).first(n)));
    auto appended=native;appended.push_back(0);check(!Codec::decode(appended));
    auto missing=native;missing.back()='X';check(!Codec::decode(missing));
    auto embedded=native;embedded[5]=0;check(!Codec::decode(embedded));
    check(!Codec::canonical(Codec::Request{{'a',0,'b'}}));
    check(!Codec::encode_request(Codec::Request{{0}}));check(!Codec::update(Codec::Request{{0}}));
    for(std::size_t length=0;length<=1040;++length) {
        Codec::Request request{std::vector<std::uint8_t>(length,'x')};
        auto raw=Codec::encode_request(request);auto s2c=Codec::update(request);
        check(raw && raw->size()==length+4 && Codec::decode(*raw)==request);
        check(s2c && s2c->size()==length+4 && (*s2c)[0]==0x98 && s2c->back()==0);
        check((*raw)[1]+256u*(*raw)[2]==raw->size());
        check(!Codec::decode(*s2c)); // Direction isolation.
    }
    Codec::Request maximum{std::vector<std::uint8_t>(1040,'A')};
    check((*Codec::update(maximum))[1]==0x14 && (*Codec::update(maximum))[2]==4);
    maximum.text.push_back('B');check(!Codec::encode_request(maximum));check(!Codec::update(maximum));
    Codec::Logical oversize{0x79,0x15,4};oversize.insert(oversize.end(),1041,'x');oversize.push_back(0);
    check(!Codec::decode(oversize));
    check(!Codec::decode(Codec::Logical{0x99,0,0}));check(!Codec::decode(Codec::Logical{0x9a,1}));
}
void text() {
    for(const auto cp:std::array<std::uint16_t,2>{950,936}) {
        check(Codec::text_request("",cp)==Codec::Request{});
        check(Codec::text_utf8({},cp).empty());
        const auto spaces=Codec::text_request("   ",cp);
        check(spaces.text==std::vector<std::uint8_t>({' ',' ',' '}));
        check(Codec::text_utf8(spaces,cp)=="   "); // No silent trim/clear.
        const auto ascii=Codec::text_request("Notice 123 %s",cp);
        check(Codec::text_utf8(ascii,cp)=="Notice 123 %s"); // Codec is not a moderation policy.
        auto max=Codec::text_request(std::string(1040,'A'),cp);check(max.text.size()==1040);
        rejects([&]{Codec::text_request(std::string(1041,'A'),cp);});
        rejects([&]{Codec::text_request(std::string("a\0b",3),cp);});
        rejects([&]{Codec::text_request(std::string("\xC0\xAF",2),cp);});
        rejects([&]{Codec::text_request(utf8(u8"😀"),cp);});
        rejects([&]{Codec::text_utf8(Codec::Request{{0x81}},cp);});
        rejects([&]{Codec::text_utf8(Codec::Request{{'a',0,'b'}},cp);});
        const auto chinese=utf8(u8"公告仙界");
        const auto request=Codec::text_request(chinese,cp);check(request.text.size()==8);
        check(Codec::text_utf8(request,cp)==chinese);
        std::string long_chinese;for(unsigned n=0;n<520;++n)long_chinese+=utf8(u8"界");
        check(Codec::text_request(long_chinese,cp).text.size()==1040);
        long_chinese+=utf8(u8"界");rejects([&]{Codec::text_request(long_chinese,cp);});
    }
    // Exact encoding samples emitted by the real native getter oracle.
    const auto traditional=Codec::text_request(utf8(u8"繁體公告"),950);
    check(traditional.text==std::vector<std::uint8_t>({0xC1,0x63,0xC5,0xE9,0xA4,0xBD,0xA7,0x69}));
    const auto simplified=Codec::text_request(utf8(u8"简体公告"),936);
    check(simplified.text==std::vector<std::uint8_t>({0xBC,0xF2,0xCC,0xE5,0xB9,0xAB,0xB8,0xE6}));
    const auto shared=utf8(u8"公告仙界");const auto bilingual=Codec::bilingual_text(shared);
    check(Codec::text_utf8(bilingual.traditional,950)==shared);
    check(Codec::text_utf8(bilingual.simplified,936)==shared);
    check(bilingual.traditional.text!=bilingual.simplified.text);
    rejects([&]{Codec::bilingual_text(utf8(u8"简体"));}); // No conversion/replacement into CP950.
    for(const auto cp:std::array<std::uint16_t,4>{0,65001,1252,951}) {
        rejects([&]{Codec::text_request("ASCII",cp);});
        rejects([&]{Codec::text_utf8({},cp);});
    }
}
}
int main() {
    try{wire();text();std::cout<<"PASS announcement wire/encoding checks="<<checks<<'\n';return 0;}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
