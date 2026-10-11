#include "scripting/LuaEngine.h"
#include <iostream>
#include <limits>
#include <stdexcept>

static void require(bool yes) { if(!yes) throw std::runtime_error("Progression rule mismatch"); }
int main() {
    try {
        god2::LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        require(lua.initialize());
        // Synthetic table tests only. Not a game level curve or balance approval.
        for(std::uint64_t xp=0;xp<=1200;++xp) {
            const auto actual=lua.progression({xp,{0,100,300,1000},4});
            const unsigned level=xp<100?1:xp<300?2:xp<1000?3:4;
            const unsigned progress=xp<100?static_cast<unsigned>(xp*100):xp<300?static_cast<unsigned>((xp-100)*50):
                xp<1000?static_cast<unsigned>((xp-300)*10000/700):10000;
            require(actual.level==level && actual.progress_display==progress);
        }
        require(lua.progression({25,{0,100,300},3})==god2::ProgressionResult{1,2500});
        require(lua.progression({1000,{0,100,300,1000},2})==god2::ProgressionResult{2,10000});
        require(lua.progression({1000,{0,100,300,1000},4})==god2::ProgressionResult{4,10000});
        constexpr auto max=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
        const auto span=max/10000;
        require(lua.progression({span-1,{0,span},2})==god2::ProgressionResult{1,9999});
        require(lua.progression({max,{0,span},2})==god2::ProgressionResult{2,10000});
        std::vector<std::uint64_t> large;
        for(std::uint64_t i=0;i<255;++i) large.push_back(i*span);
        require(lua.progression({large[20]+span-1,large,255})==god2::ProgressionResult{21,9999});
        require(lua.progression({large.back(),large,255})==god2::ProgressionResult{255,10000});
        large.push_back(255*span);
        bool oversized_rejected=false;
        try {lua.progression({0,large,255});} catch(const std::invalid_argument&) {oversized_rejected=true;}
        require(oversized_rejected);
        for(const auto& invalid:std::vector<god2::ProgressionInput>{
            {0,{},1},{0,{1,100},2},{0,{0,0},2},{0,{0,100,99},3},
            {0,{0,100},0},{0,{0,100},3},{0,{0,span+1},2},{max+1,{0,100},2}}) {
            bool rejected=false;
            try {lua.progression(invalid);} catch(const std::invalid_argument&) {rejected=true;}
            require(rejected);
        }
        require(lua.reload_all());
        require(lua.progression({100,{0,100,300},3})==god2::ProgressionResult{2,0});
        std::cout<<"1201 explicit-table cases plus locks, boundaries, overflow and reload passed\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
