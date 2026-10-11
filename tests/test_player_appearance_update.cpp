#include "protocol/RecoveredPlayerAppearanceUpdate.h"
#include <charconv>
#include <iostream>
#include <limits>
#include <string_view>
#include <vector>

using Appearance=god2::RecoveredPlayerAppearanceUpdate;
namespace {
unsigned checks{};
void require(bool value) {++checks;if(!value)throw std::runtime_error("DA appearance contract mismatch");}
template<class F> void rejects(F action) {
    bool rejected=false;try{action();}catch(const std::invalid_argument&){rejected=true;}
    require(rejected);
}
std::uint64_t number(std::string_view input) {
    std::uint64_t value{};
    const auto parsed=std::from_chars(input.data(),input.data()+input.size(),value);
    if(parsed.ec!=std::errc{} || parsed.ptr!=input.data()+input.size())throw std::invalid_argument("Invalid unsigned decimal");
    return value;
}
std::vector<std::uint8_t> unhex(std::string_view input) {
    if(input.size()%2)throw std::invalid_argument("Odd hex length");
    std::vector<std::uint8_t> bytes;
    for(std::size_t i=0;i<input.size();i+=2) {
        unsigned value{};const auto parsed=std::from_chars(input.data()+i,input.data()+i+2,value,16);
        if(parsed.ec!=std::errc{} || parsed.ptr!=input.data()+i+2)throw std::invalid_argument("Invalid hex");
        bytes.push_back(static_cast<std::uint8_t>(value));
    }
    return bytes;
}
void print(const Appearance::Bytes& bytes) {
    constexpr char hex[]="0123456789abcdef";
    for(auto byte:bytes)std::cout<<hex[byte>>4]<<hex[byte&15];
    std::cout<<'\n';
}
}
int main(int argc,char** argv) {
    try {
        if(argc>1) {
            if(argc==7 && std::string_view(argv[1])=="--encode")
                print(Appearance::encode(number(argv[2]),number(argv[3]),number(argv[4]),number(argv[5]),unhex(argv[6])));
            else if(argc==3 && std::string_view(argv[1])=="--roundtrip") {
                const auto value=Appearance::decode(unhex(argv[2]));
                if(!value)throw std::invalid_argument("Invalid exact DA logical record");
                print(Appearance::encode(*value));
            }else throw std::invalid_argument("Usage: --encode actor transform scalar5 scalar6 components_hex16 | --roundtrip logical_hex30");
            return 0;
        }
        constexpr Appearance::Fields fields{0xc0d9,0xfedc,0x87,0xf9,{0x12,0xa3,0x45,0xc6,0x78,0xe9,0xab,0xff}};
        constexpr Appearance::Bytes golden{0xda,0xd9,0xc0,0xdc,0xfe,0x87,0xf9,0x12,0xa3,0x45,0xc6,0x78,0xe9,0xab,0xff};
        static_assert(Appearance::encode(fields)==golden);
        static_assert(Appearance::decode(golden)==fields);
        for(std::size_t length=0;length<15;++length)require(!Appearance::decode(std::span(golden).first(length)));
        require(!Appearance::decode(std::array<std::uint8_t,16>{0xda}));
        for(unsigned op=0;op<=255;++op) {
            auto bytes=golden;bytes[0]=static_cast<std::uint8_t>(op);
            require(Appearance::decode(bytes).has_value()==(op==0xda));
        }
        // Exhaust both WORD domains, including upper identity bits and nonzero
        // transform keys. This is wire preservation, not transform eligibility.
        for(unsigned word=0;word<=0xffff;++word) {
            auto value=fields;value.actor_identity=static_cast<std::uint16_t>(word);
            value.transform_key=static_cast<std::uint16_t>(0xffff-word);
            const auto encoded=Appearance::encode(value);
            require(encoded[1]==(word&255) && encoded[2]==(word>>8));
            require(Appearance::decode(encoded)==value);
        }
        // Every scalar/component byte value must survive untouched. Variant
        // bits and unusual component categories must not be normalized here.
        for(unsigned offset=5;offset<15;++offset)for(unsigned byte=0;byte<=255;++byte) {
            auto bytes=golden;bytes[offset]=static_cast<std::uint8_t>(byte);
            const auto decoded=Appearance::decode(bytes);require(decoded.has_value());
            require(Appearance::encode(*decoded)==bytes);
            require(Appearance::encode(decoded->actor_identity,decoded->transform_key,
                decoded->raw_scalar5,decoded->raw_scalar6,decoded->components)==bytes);
        }
        for(auto bad:std::array<std::uint64_t,3>{65536,0x100000000ull,std::numeric_limits<std::uint64_t>::max()}) {
            rejects([&]{Appearance::encode(bad,0,0,0,fields.components);});
            rejects([&]{Appearance::encode(0,bad,0,0,fields.components);});
        }
        for(auto bad:std::array<std::uint64_t,4>{256,65536,0x100000000ull,std::numeric_limits<std::uint64_t>::max()}) {
            rejects([&]{Appearance::encode(0,0,bad,0,fields.components);});
            rejects([&]{Appearance::encode(0,0,0,bad,fields.components);});
        }
        for(unsigned length=0;length<8;++length)
            rejects([&]{Appearance::encode(0,0,0,0,std::span(fields.components).first(length));});
        rejects([&]{Appearance::encode(0,0,0,0,std::array<std::uint8_t,9>{});});
        // Exact packet used by all27 current native DA routing-prefix vectors.
        require(Appearance::encode(217,0,7,9,unhex("0020004000008000"))==
            Appearance::Bytes{0xda,0xd9,0,0,0,7,9,0,0x20,0,0x40,0,0,0x80,0});
        std::cout<<"Player appearance checks passed: "<<checks<<'\n';
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
