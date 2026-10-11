#include "scripting/LuaEngine.h"
#include <algorithm>
#include <iostream>
#include <stdexcept>

static void require(bool yes) { if (!yes) throw std::runtime_error("Supply rule mismatch"); }
int main() {
    try {
        god2::LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR) / "scripts", false);
        require(lua.initialize());
        unsigned cases = 0;
        for (unsigned hp = 0; hp <= 12; ++hp)
            for (unsigned mp = 0; mp <= 8; ++mp)
                for (unsigned dh = 0; dh <= 15; ++dh)
                    for (unsigned dm = 0; dm <= 10; ++dm) {
                        if (!dh && !dm) continue;
                        const auto next_hp = hp ? std::min(12u, hp + dh) : hp;
                        const auto next_mp = hp ? std::min(8u, mp + dm) : mp;
                        require(lua.supply({hp,12,mp,8,dh,dm}) ==
                            god2::SupplyResult{next_hp,next_mp,next_hp != hp || next_mp != mp});
                        ++cases;
                    }
        require(lua.supply({52,120,2,80,0,50}) == god2::SupplyResult{52,52,true});
        require(lua.supply({52,120,52,80,0,50}) == god2::SupplyResult{52,80,true});
        require(lua.supply({52,120,80,80,0,50}) == god2::SupplyResult{52,80,false});
        require(lua.supply({1,2147483647,0,2147483647,2147483647,2147483647}) ==
            god2::SupplyResult{2147483647,2147483647,true});
        require(lua.supply({1,1,0,0,0,50}) == god2::SupplyResult{1,0,false});
        for (const auto& input : {god2::SupplyInput{0,0,0,0,1,0},
                {2,1,0,0,1,0},{1,1,2,1,1,0},{1,1,0,0,0,0},
                {1,2147483648u,0,0,1,0},{1,1,0,2147483648u,1,0},
                {1,1,0,0,2147483648u,0},{1,1,0,0,0,2147483648u}}) {
            bool rejected = false;
            try { lua.supply(input); } catch (const std::invalid_argument&) { rejected = true; }
            require(rejected);
        }
        require(lua.reload_all());
        require(lua.supply({52,120,2,80,0,50}) == god2::SupplyResult{52,52,true});
        std::cout << cases << " supply projections, bounds and reload passed\n";
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
