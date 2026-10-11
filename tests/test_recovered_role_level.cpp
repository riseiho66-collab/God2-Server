#include "protocol/RecoveredRoleLevel.h"
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using Codec=god2::RecoveredRoleLevel;
static void require(bool yes) {if(!yes) throw std::runtime_error("Role level codec mismatch");}
int main(int argc,char**) {
    if(argc>1) {
        std::string hex;
        while(std::cin>>hex) {
            std::vector<std::uint8_t> bytes;
            for(std::size_t i=0;i+1<hex.size();i+=2) bytes.push_back(static_cast<std::uint8_t>(std::stoul(hex.substr(i,2),nullptr,16)));
            const auto record=Codec::parse(bytes);
            if(!record) {std::cout<<"reject\n";continue;}
            const auto encoded=Codec::encode(Codec::with_level_progress(*record,record->level(),record->progress_display()));
            constexpr char digits[]="0123456789abcdef";
            for(auto b:encoded) std::cout<<digits[b>>4]<<digits[b&15];
            std::cout<<'\n';
        }
        return 0;
    }
    Codec::Bytes bytes{};bytes.fill(0xa5);bytes[0]=0x22;
    for(std::size_t n=0;n<25;++n) require(!Codec::parse(std::span(bytes).first(n)));
    std::vector<std::uint8_t> long_record(bytes.begin(),bytes.end());long_record.push_back(0);
    require(!Codec::parse(long_record));
    for(unsigned opcode=0;opcode<256;++opcode) {
        bytes[0]=static_cast<std::uint8_t>(opcode);require(Codec::parse(bytes).has_value()==(opcode==0x22));
    }
    bytes[0]=0x22;const auto original=*Codec::parse(bytes);
    for(unsigned level=0;level<256;++level) for(const auto progress:std::array<std::uint16_t,5>{0,1,10000,32768,65535}) {
        const auto updated=Codec::with_level_progress(original,static_cast<std::uint8_t>(level),progress);
        require(updated.level()==level && updated.progress_display()==progress);
        require(updated.base_stats()==original.base_stats() && updated.max_hp()==original.max_hp() && updated.max_mp()==original.max_mp());
        const auto wire=Codec::encode(updated);
        for(std::size_t i=0;i<25;++i) if(i!=1 && i!=13 && i!=14) require(wire[i]==bytes[i]);
        require(Codec::encode(*Codec::parse(wire))==wire);
    }
    bytes.fill(0);require(Codec::encode(original)[2]==0xa5);
}
