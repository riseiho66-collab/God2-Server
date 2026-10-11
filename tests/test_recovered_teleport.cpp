#include "protocol/RecoveredTeleport.h"
#include <iostream>
#include <stdexcept>

void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
int main() {
    using T=god2::RecoveredTeleport;
    try {
        T::Menu menu{0x1234,517,0x85,7,10,0xa5,
            {{{1,0x11,123},{2,0x22,456},{3,0x33,789},{4,0x44,1024},{5,0x55,65535}}}};
        const auto bytes=T::encode(menu);
        require(bytes && bytes->size()==29,"Menu length");
        require((*bytes)[0]==0x6d && (*bytes)[1]==0x34 && (*bytes)[2]==0x12 &&
            (*bytes)[5]==0x85 && (*bytes)[9]==1 && (*bytes)[11]==123 &&
            (*bytes)[25]==5 && (*bytes)[27]==255 && (*bytes)[28]==255,"Menu offsets");
        require(T::decode_menu(*bytes)==menu,"Menu lossless fields");
        for(std::size_t n=0;n<29;++n) require(!T::decode_menu(std::span(*bytes).first(n)),"Short menu");
        auto invalid=menu;invalid.count_flags=6;require(!T::encode(invalid),"Count overflows five entries");
        invalid=menu;invalid.destinations[0].id=6;require(!T::encode(invalid),"Native label table overflow");
        for(const auto context:{0u,0x61du,0x61eu,0x622u,0x623u,0xffffu}) {
            for(unsigned tail=0;tail<256;++tail) {
                const auto opcode=static_cast<std::uint8_t>(T::special_context(static_cast<std::uint16_t>(context))?0xa9:0x99);
                T::SelectionBytes request{opcode,static_cast<std::uint8_t>(context),static_cast<std::uint8_t>(context>>8),5,static_cast<std::uint8_t>(tail)};
                const auto parsed=T::decode_selection(request);
                require(parsed && parsed->context==context && parsed->destination==5 && parsed->opaque_tail==tail,"Selection fields");
                request[0]=opcode==0x99?0xa9:0x99;
                require(!T::decode_selection(request),"Wrong native context branch");
            }
        }
        require(!T::decode_selection(T::SelectionBytes{0x99,0,0,0,0}),"Unselected destination");
        require(!T::decode_selection(T::SelectionBytes{0x99,0,0,6,0}),"Unknown destination");
        std::cout<<"Recovered teleport contracts passed\n";
        return 0;
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
