#include "game/RecoveredFruitNavigation.h"
#include <array>
#include <cstdio>
#include <limits>
#include <stdexcept>
#include <string_view>

static void require(bool ok) { if(!ok)throw std::runtime_error("Fruit navigation test failed"); }
int main(int argc,char** argv) {
    try {
        if(argc==3 && std::string_view(argv[1])=="--reject") {
            bool rejected=false;
            try {(void)god2::RecoveredFruitNavigation::load(argv[2]);}
            catch(const std::exception&) {rejected=true;}
            require(rejected);std::puts("PASS rejected unqualified source");return 0;
        }
        if(argc!=2)throw std::invalid_argument("Expected qualified navigation path");
        const auto navigation=god2::RecoveredFruitNavigation::load(argv[1]);
        const god2::RecoveredFruitNavigation constructed(argv[1]);
        std::array<std::size_t,3> counts{};
        for(int y=0;y<189;++y)for(int x=0;x<189;++x) {
            const auto value=navigation.consistent_cell(x,y);
            require(value<=2 && value==constructed.consistent_cell(x,y));++counts[value];
        }
        require(counts==std::array<std::size_t,3>{27927,7768,26});
        for(const auto [x,y]:std::array<std::array<int,2>,9>{{
            {-1,0},{0,-1},{189,0},{0,189},{-1,-1},{189,189},
            {std::numeric_limits<int>::min(),0},{0,std::numeric_limits<int>::max()},{61,43}}})
            require(navigation.consistent_cell(x,y)==0);
        require(navigation.consistent_cell(0,0)==0); // source unknown255
        require(navigation.consistent_cell(168,0)==0); // source blocked0
        require(navigation.consistent_cell(92,43)==1);
        require(navigation.consistent_cell(95,43)==2);
        for(const auto [x,y]:std::array<std::array<int,2>,4>{{{108,110},{113,69},{69,72},{68,116}}})
            require(navigation.consistent_cell(x,y)==1);
        std::puts("PASS 35721 fruit cells, consensus/bounds");return 0;
    } catch(const std::exception& e) {std::fprintf(stderr,"%s\n",e.what());return 1;}
}
