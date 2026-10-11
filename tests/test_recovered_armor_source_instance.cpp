#include "protocol/RecoveredArmorSourceInstance.h"
#include <array>
#include <iostream>
#include <stdexcept>
namespace {
void require(bool ok){if(!ok)throw std::runtime_error("Armor source-instance exact mismatch");}
}
int main(){
    try {
        using Contract=god2::RecoveredArmorSourceInstance;
        std::array<std::uint8_t,20> bytes{};
        for(const auto key:{std::uint16_t{1001},std::uint16_t{20001}}){
            bytes[0]=static_cast<std::uint8_t>(key);bytes[1]=static_cast<std::uint8_t>(key>>8);
            for(unsigned flags=0;flags<1024;++flags)for(unsigned family=0;family<64;++family){
                bytes[2]=static_cast<std::uint8_t>(family|((flags&3)<<6));bytes[3]=static_cast<std::uint8_t>(flags>>2);
                const auto before=bytes;
                require(Contract::matches(key,"EQU",bytes)==(family==2));
                require(Contract::matches(key,"TEQ",bytes)==(family==26));
                require(!Contract::matches(static_cast<std::uint16_t>(key+1),"EQU",bytes));
                require(!Contract::matches(key,"WPN",bytes));require(bytes==before);
            }
        }
        require(!Contract::matches(0,"EQU",bytes));
        bytes[0]=0x58;bytes[1]=0x7f;bytes[2]=2;bytes[3]=0;
        require(!Contract::matches(0x7f58,"EQU",bytes));
        require(!Contract::matches(1001,"EQU",std::span<const std::uint8_t>(bytes).first(19)));
        std::cout<<"Exact EQU2/TEQ26 key/family consistency, all high flag preservation and bounds passed\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
