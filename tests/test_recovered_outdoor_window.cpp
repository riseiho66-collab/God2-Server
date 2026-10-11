#include "game/RecoveredOutdoorWindow.h"
#include <iostream>
#include <string>

namespace {
void require(bool v) { if(!v) throw std::runtime_error("Outdoor assertion failed"); }
int input(int low,int high) {
    long long value=0;
    if(!(std::cin>>value) || value<low || value>high) throw std::invalid_argument("Invalid outdoor input");
    return static_cast<int>(value);
}
}
int main(int argc,char** argv) {
    try {
        using W=god2::RecoveredOutdoorWindow;
        W::Blocks blocks{};
        W unknown(blocks);
        require(!unknown.cell(0,0) && !unknown.cell(-1,0) && !unknown.cell(63,0));
        std::vector<std::uint8_t> data(W::block_bytes,0xff);
        blocks[4]=data;
        require(W(blocks).cell(21,21)==1 && !W(blocks).cell(20,21));
        god2::OutdoorPlacement p{{2,2,{0,1,255,0}},21,21};
        p.points={{{0,0},{-1,-1}}};
        const std::array placements{p};
        W combined(blocks,placements);
        require(combined.cell(21,21)==2 && combined.cell(22,23)==0);
        blocks[0]=std::span(data).first(1);
        bool rejected=false;
        try { (void)W(blocks); } catch(const std::invalid_argument&) { rejected=true; }
        require(rejected);
        if(argc==2 && std::string(argv[1])=="--dump") {
            std::array<std::vector<std::uint8_t>,9> storage;
            for(std::size_t i=0;i<9;++i) {
                if(input(0,1)) {
                    storage[i].resize(W::block_bytes);
                    for(auto& byte:storage[i]) byte=static_cast<std::uint8_t>(input(0,255));
                }
                blocks[i]=storage[i];
            }
            std::vector<god2::OutdoorPlacement> objects;
            const auto count=input(0,20000);
            for(int i=0;i<count;++i) {
                god2::OutdoorPlacement object;
                object.x=input(-32768,32767);object.y=input(-32768,32767);
                object.grid.width=input(1,512);object.grid.height=input(1,512);
                for(auto& point:object.points) for(auto& value:point) value=input(-32768,32767);
                object.grid.cells.resize(static_cast<std::size_t>(object.grid.width*object.grid.height));
                for(auto& byte:object.grid.cells) byte=static_cast<std::uint8_t>(input(0,255));
                objects.push_back(std::move(object));
            }
            std::string extra;require(!(std::cin>>extra));
            W result(blocks,objects);
            constexpr char digits[]="0123456789abcdef";
            for(int y=0;y<W::side;++y) for(int x=0;x<W::side;++x) {
                const auto value=result.cell(x,y);
                if(!value) std::cout<<"??";
                else std::cout<<digits[*value>>4]<<digits[*value&15];
            }
            std::cout<<'\n';
        } else { require(argc==1);std::cout<<"Outdoor assertions passed\n"; }
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
