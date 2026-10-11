#include "scripting/LuaEngine.h"
#include <array>
#include <iostream>
#include <stdexcept>

static void require(bool yes) { if(!yes) throw std::runtime_error("Town guide rule mismatch"); }
int main() {
    try {
        god2::LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        require(lua.initialize());
        constexpr std::array<std::array<god2::TownGuidePlan,2>,4> expected{{
            {{{894,1,1,false},{898,0,0,false}}},
            {{{895,1,1,false},{899,2,2,false}}},
            {{{896,3,0,true},{900,2,2,false}}},
            {{{897,3,0,false},{901,3,0,false}}}
        }};
        for(unsigned stage=0;stage<4;++stage) for(unsigned npc=0;npc<2;++npc)
            require(lua.town_guide({stage,1606+npc})==expected[stage][npc]);
        // Exhaust every six-contact trace. Three choices per contact: either
        // NPC confirmed, or cancel/no confirmation. Only this test commits plans.
        for(unsigned trace=0;trace<729;++trace) {
            unsigned choices=trace,stage=0,rewards=0;
            for(unsigned step=0;step<6;++step) {
                const auto choice=choices%3;choices/=3;
                if(choice==2) {
                    const auto pending=lua.town_guide({stage,1606});
                    require(pending==lua.town_guide({stage,1606}));
                    continue;
                }
                const auto plan=lua.town_guide({stage,1606+choice});
                require(plan==expected[stage][choice]);
                rewards+=plan.requires_reward?1:0;
                stage=plan.confirmed_stage;
                require(rewards<=1);
                require((stage==3)==(rewards==1));
            }
        }
        for(const auto input:std::array<god2::TownGuideInput,6>{{{4,1606},{0,0},{0,1605},
                {0,1608},{0,0x10000646},{0xffffffff,1607}}}) {
            bool rejected=false;
            try { lua.town_guide(input); } catch(const std::invalid_argument&) { rejected=true; }
            require(rejected);
        }
        require(lua.reload_all());
        require(lua.town_guide({2,1606})==expected[2][0]);
        const god2::DiagnosticDoorPlan indoor{2,15,16,19},town{2,4,86,71};
        require(lua.diagnostic_door({2,4,86,71,86,70})==indoor);
        require(lua.diagnostic_door({2,15,16,19,16,20})==town);
        for(unsigned area:std::array<unsigned,3>{1,2,3})
            for(unsigned scene:std::array<unsigned,3>{4,15,50})
                for(unsigned x=85;x<=87;++x) for(unsigned y=69;y<=71;++y) {
                    const auto plan=lua.diagnostic_door({area,scene,84,69,x,y});
                    require(plan.has_value()==(area==2 && scene==4 && x==86 && y==70));
                }
        require(!lua.diagnostic_door({2,4,86,70,86,70}));
        require(!lua.diagnostic_door({2,15,16,20,16,20}));
        require(!lua.diagnostic_door({2,15,16,20,16,19}));
        require(!lua.diagnostic_door({2,4,86,70,86,71}));
        for(auto input:std::array<god2::DiagnosticDoorInput,3>{{{64,4,0,0,86,70},
                {2,1024,0,0,86,70},{2,4,0,0,0x4000,70}}}) {
            bool rejected=false;
            try { lua.diagnostic_door(input); } catch(const std::invalid_argument&) { rejected=true; }
            require(rejected);
        }
        require(lua.reload_all());
        require(lua.diagnostic_door({2,4,86,71,86,70})==indoor);
        std::cout<<"8 plans, 729 six-contact traces, bounds and reload passed; no persistence/rewards executed\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
