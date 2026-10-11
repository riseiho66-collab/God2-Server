#include "protocol/RecoveredWorldFrame.h"
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace {
using Codec=god2::RecoveredWorldFrame;
void require(bool value,const char* message) {
    if(!value) throw std::runtime_error(message);
}
std::vector<std::uint8_t> hex(std::string_view value) {
    require(value.size()%2==0 && value.size()<=2*(Codec::max_logical_size+3),"Invalid hex length");
    const auto digit=[](char c)->unsigned {
        if(c>='0' && c<='9') return static_cast<unsigned>(c-'0');
        if(c>='a' && c<='f') return static_cast<unsigned>(c-'a'+10);
        if(c>='A' && c<='F') return static_cast<unsigned>(c-'A'+10);
        throw std::invalid_argument("Invalid hex digit");
    };
    std::vector<std::uint8_t> bytes;
    for(std::size_t i=0;i<value.size();i+=2)
        bytes.push_back(static_cast<std::uint8_t>(16*digit(value[i])+digit(value[i+1])));
    return bytes;
}
void print(std::span<const std::uint8_t> bytes) {
    constexpr char digits[]="0123456789abcdef";
    for(const auto b:bytes) std::cout<<digits[b>>4]<<digits[b&15];
    std::cout<<'\n';
}
void assertions() {
    const auto known_plain=hex("a60000");
    // Permanent known-plaintext oracle, with the current zero-seed transform.
    require(Codec::encode(known_plain)==hex("0600a3a3fdd5"),"Six-byte zero-seed regression changed");
    require(Codec::encode(hex("3000"))==hex("05002d2d22"),"Native periodic fixture changed");
    require(Codec::decode(hex("05002d2d22"))==hex("3000"),"Native periodic decode changed");
    std::uint32_t state=0x17a645u;
    const auto next=[&state]() {
        state^=state<<13;state^=state>>17;state^=state<<5;
        return state;
    };
    std::vector<std::uint8_t> logical;
    for(std::size_t size=1;size<=Codec::max_logical_size;++size) {
        logical.push_back(static_cast<std::uint8_t>(next()));
        const auto wire=Codec::encode(logical);
        const auto plain=Codec::decode(wire);
        require(plain && *plain==logical,"Reversible codec lost logical bytes");
        require(Codec::encode(*plain)==wire,"Re-encoding changed wire bytes");
        auto bad=wire;bad.back()^=1;
        require(!Codec::decode(bad),"Checksum corruption accepted");
        require(!Codec::decode(std::span(wire).first(wire.size()-1)),"Truncation accepted");
    }
    for(std::size_t size:{0u,1u,2u,3u,2564u,65535u}) {
        std::vector<std::uint8_t> bad(size,0);
        if(size>=2) { bad[0]=static_cast<std::uint8_t>(size);bad[1]=static_cast<std::uint8_t>(size>>8); }
        require(!Codec::decode(bad),"Envelope size outside bounds accepted");
    }
    for(std::size_t size:{0u,2561u}) {
        bool rejected=false;
        try { (void)Codec::encode(std::vector<std::uint8_t>(size)); }
        catch(const std::invalid_argument&) { rejected=true; }
        require(rejected,"Encoder limit bypassed");
    }
    for(unsigned iteration=0;iteration<4096;++iteration) {
        std::vector<std::uint8_t> wire(next()%3000);
        for(auto& byte:wire) byte=static_cast<std::uint8_t>(next());
        if(wire.size()>=2 && iteration%2) {
            wire[0]=static_cast<std::uint8_t>(wire.size());
            wire[1]=static_cast<std::uint8_t>(wire.size()>>8);
        }
        const auto plain=Codec::decode(wire);
        if(plain) require(Codec::encode(*plain)==wire,"Accepted fuzz input is not reversible");
    }
}
}
int main(int argc,char** argv) {
    try {
        if(argc==3 && std::string_view(argv[1])=="--encode") print(Codec::encode(hex(argv[2])));
        else if(argc==3 && std::string_view(argv[1])=="--decode") {
            const auto logical=Codec::decode(hex(argv[2]));
            require(logical.has_value(),"Invalid frame");print(*logical);
        } else { require(argc==1,"Expected --encode/--decode HEX");assertions(); }
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
