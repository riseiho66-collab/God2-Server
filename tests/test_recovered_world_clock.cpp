#include "protocol/RecoveredWorldClock.h"
#include <charconv>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <system_error>

using Clock=god2::RecoveredWorldClock;
namespace {
unsigned checks{};
void require(bool value) {++checks;if(!value)throw std::runtime_error("World clock contract mismatch");}
template<class F> void rejects(F action) {
    bool rejected=false;try{action();}catch(const std::invalid_argument&){rejected=true;}
    require(rejected);
}
template<class T> T number(std::string_view text) {
    T result{};
    const auto parsed=std::from_chars(text.data(),text.data()+text.size(),result);
    if(parsed.ec!=std::errc{} || parsed.ptr!=text.data()+text.size())
        throw std::invalid_argument("Invalid decimal clock argument");
    return result;
}
void print(Clock::Bytes bytes) {
    constexpr char hex[]="0123456789abcdef";
    for(const auto byte:bytes)std::cout<<hex[byte>>4]<<hex[byte&15];
    std::cout<<'\n';
}
}
int main(int argc,char** argv) {
    if(argc>1) {
        try {
            if(argc==3 && std::string_view(argv[1])=="--epoch")
                print(Clock::logical_from_unix_seconds(number<std::int64_t>(argv[2])));
            else if(argc==5 && std::string_view(argv[1])=="--encode")
                print(Clock::encode(number<std::uint64_t>(argv[2]),number<std::uint64_t>(argv[3]),number<std::uint64_t>(argv[4])));
            else throw std::invalid_argument("Usage: --epoch int64 | --encode unsigned unsigned unsigned");
            return 0;
        }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
    }
    static_assert(Clock::logical_from_unix_seconds(0)==Clock::Bytes{0x1a,0,0,0});
    static_assert(Clock::logical_from_unix_seconds(-1)==Clock::Bytes{0x1a,3,59,59});
    Clock::Bytes valid{0x1a,128,255,60};
    for(std::size_t length=0;length<4;++length)require(!Clock::decode(std::span(valid).first(length)));
    require(!Clock::decode(std::array<std::uint8_t,5>{0x1a,0,0,0,0}));
    for(unsigned opcode=0;opcode<=255;++opcode) {
        auto bytes=valid;bytes[0]=static_cast<std::uint8_t>(opcode);
        require(Clock::decode(bytes).has_value()==(opcode==0x1a));
    }
    // Every value of each byte is tested with nonzero other fields; no
    // normalization/rejection of minute/second >=60 or hour >=24 is allowed.
    for(unsigned field=0;field<3;++field)for(unsigned value=0;value<=255;++value) {
        auto bytes=valid;bytes[field+1]=static_cast<std::uint8_t>(value);
        const auto decoded=Clock::decode(bytes);require(decoded.has_value());
        require(Clock::encode(*decoded)==bytes);
        require(Clock::encode(bytes[1],bytes[2],bytes[3])==bytes);
        require(Clock::native_base_seconds(*decoded)==6u*(3600u*bytes[1]+60u*bytes[2]+bytes[3]));
    }
    for(const auto bad:std::array<std::uint64_t,5>{256,65536,0x100000000ull,
            std::numeric_limits<std::uint64_t>::max(),0x1000000ffull}) {
        rejects([&]{Clock::encode(bad,0,0);});
        rejects([&]{Clock::encode(0,bad,0);});
        rejects([&]{Clock::encode(0,0,bad);});
    }
    require(Clock::native_base_seconds({255,255,255})==5601330);
    require(Clock::native_base_seconds({0,0,1})==6);
    require(Clock::native_base_seconds({1,0,0})==21600);
    for(const auto& [epoch,expected]:std::array<std::pair<std::int64_t,Clock::Bytes>,12>{{
        {0,{0x1a,0,0,0}},{59,{0x1a,0,0,59}},{60,{0x1a,0,1,0}},
        {3599,{0x1a,0,59,59}},{3600,{0x1a,1,0,0}},{14399,{0x1a,3,59,59}},
        {14400,{0x1a,0,0,0}},{-1,{0x1a,3,59,59}},{-14400,{0x1a,0,0,0}},
        {-14401,{0x1a,3,59,59}},
        {std::numeric_limits<std::int64_t>::min(),{0x1a,0,29,52}},
        {std::numeric_limits<std::int64_t>::max(),{0x1a,3,30,7}}
    }})require(Clock::logical_from_unix_seconds(epoch)==expected);
    // Exhaust two whole cycles around zero: increasing real seconds add six
    // game seconds modulo86400, and adding four hours preserves the record.
    auto previous=Clock::native_base_seconds(*Clock::decode(Clock::logical_from_unix_seconds(-14400)));
    for(std::int64_t epoch=-14399;epoch<=14400;++epoch) {
        const auto bytes=Clock::logical_from_unix_seconds(epoch);
        const auto current=*Clock::decode(bytes);
        require(current.base_hours<4 && current.base_minutes<60 && current.base_seconds<60);
        const auto base=Clock::native_base_seconds(current);
        require(base==(previous+6)%86400);previous=base;
        require(bytes==Clock::logical_from_unix_seconds(epoch+14400));
    }
    std::cout<<"World clock checks passed: "<<checks<<'\n';
}
