#include "protocol/RecoveredRoleProgress.h"
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using Codec=god2::RecoveredRoleProgress;
static void require(bool yes) { if(!yes) throw std::runtime_error("Role progress mismatch"); }
int main(int argc,char**) {
    if(argc>1) {
        std::string hex;
        while(std::cin>>hex) {
            std::vector<std::uint8_t> bytes;
            for(std::size_t i=0;i+1<hex.size();i+=2)
                bytes.push_back(static_cast<std::uint8_t>(std::stoul(hex.substr(i,2),nullptr,16)));
            auto record=Codec::parse(bytes);
            if(!record) { std::cout<<"reject\n";continue; }
            // Feed an actual C++ encoded record, not a Python reimplementation, to native tests.
            const auto output=Codec::encode(Codec::with_role(*record,record->role_hp(),record->role_mp(),record->role_progress_display()));
            constexpr char digits[]="0123456789abcdef";
            for(auto byte:output) std::cout<<digits[byte>>4]<<digits[byte&15];
            std::cout<<' '<<record->role_hp()<<' '<<record->role_mp()<<' '<<record->role_progress_display()
                     <<' '<<record->companion_hp()<<' '<<record->companion_scalar_raw()<<' '<<record->companion_progress_display()<<'\n';
        }
        return 0;
    }
    Codec::Bytes bytes{};bytes.fill(0xa5);bytes[0]=Codec::opcode;
    for(std::size_t size=0;size<bytes.size();++size) require(!Codec::parse(std::span(bytes).first(size)));
    auto oversized=std::vector<std::uint8_t>(bytes.begin(),bytes.end());oversized.push_back(0);
    require(!Codec::parse(oversized));
    for(unsigned opcode=0;opcode<256;++opcode) {
        bytes[0]=static_cast<std::uint8_t>(opcode);
        require(Codec::parse(bytes).has_value()==(opcode==Codec::opcode));
    }
    bytes[0]=Codec::opcode;
    const auto saved=*Codec::parse(bytes);
    for(const std::uint32_t value:{0u,1u,0x7fffffffu,0x80000000u,0xffffffffu}) {
        const auto changed=Codec::with_role(saved,value,value,static_cast<std::uint16_t>(value));
        require(changed.role_hp()==value && changed.role_mp()==value && changed.role_progress_display()==static_cast<std::uint16_t>(value));
        const auto encoded=Codec::encode(changed);
        for(std::size_t i=0;i<bytes.size();++i)
            if(!((i>=1 && i<=4)||(i>=9 && i<=12)||(i>=17 && i<=18))) require(encoded[i]==bytes[i]);
        require(Codec::encode(*Codec::parse(encoded))==encoded);
    }
    bytes.fill(0);
    require(Codec::encode(saved)[15]==0xa5);
}
