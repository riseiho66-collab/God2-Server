#include "protocol/RecoveredTeleportGem.h"
#include <iostream>
#include <stdexcept>

using Gem=god2::RecoveredTeleportGem;
static unsigned checks=0;
static void check(bool condition) {
    ++checks;
    if(!condition) throw std::runtime_error("RecoveredTeleportGem contract mismatch");
}
static Gem::Metadata instance(unsigned type,unsigned flags,unsigned charges) {
    Gem::Metadata value{};
    for(unsigned i=0;i<value.size();++i)value[i]=static_cast<std::uint8_t>(i*7+3);
    const auto word=std::uint32_t{16055}|(type<<16)|(flags<<22)|(charges<<25);
    for(unsigned i=0;i<4;++i)value[i]=static_cast<std::uint8_t>(word>>(8*i));
    return value;
}
int main() {
    try {
        for(unsigned flags=0;flags<8;++flags) {
            for(unsigned before=0;before<128;++before) {
                const auto source=instance(8,flags,before);
                const auto display=Gem::displayed_charges(source);
                check(display.has_value()==(before>=1 && before<=10));
                if(display)check(*display==before);
                for(unsigned after=0;after<=10;++after) {
                    const auto next=Gem::with_charges(source,static_cast<std::uint8_t>(after));
                    check(next.has_value());
                    check(*next==instance(8,flags,after));
                    check(Gem::header(*next)>>25==after);
                    check((Gem::header(*next)&0x1ffffffu)==(Gem::header(source)&0x1ffffffu));
                    const auto projected=god2::RecoveredInventoryProjection::encode({29,1,*next});
                    check(projected.has_value() && projected->size()==35);
                    check(std::equal(next->begin(),next->end(),projected->begin()+10));
                }
            }
        }
        for(unsigned type=0;type<64;++type) {
            const auto value=instance(type,7,10);
            check(Gem::matches(value)==(type==8));
            check(Gem::displayed_charges(value).has_value()==(type==8));
            check(Gem::with_charges(value,9).has_value()==(type==8));
        }
        for(unsigned charge=11;charge<256;++charge)
            check(!Gem::with_charges(instance(8,0,10),static_cast<std::uint8_t>(charge)));
        auto wrong=instance(8,0,10);wrong[0]^=1;
        check(!Gem::matches(wrong));check(!Gem::displayed_charges(wrong));check(!Gem::with_charges(wrong,9));
        // Consumption/removal is deliberately outside this projection helper.
        const auto exhausted=Gem::with_charges(instance(8,0,1),0);
        check(exhausted.has_value() && !Gem::displayed_charges(*exhausted));
        std::cout << "PASS " << checks << " checks\n";
    } catch(const std::exception& error) {
        std::cerr << error.what() << '\n';return 1;
    }
}
