#include "scripting/LuaEngine.h"
#include <algorithm>
#include <array>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
}
int main() {
    try {
        god2::LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts", false);
        require(lua.initialize(), "Production Lua initialization failed");
        // Explicit synthetic inputs: no defaults enter catalogs or saved actors.
        std::size_t count=0;
        for(auto attack : {0u,1u,31u,1000000u})
        for(auto defense : {0u,1u,13u,1000000u})
        for(auto power : {0u,100u,175u,10000u})
        for(auto defense_percent : {0u,50u,100u})
        for(auto roll : {0u,999u,1000u,9999u}) {
            god2::CombatRuleInput p{attack,defense,power,defense_percent,8,24,1000,150,roll};
            const auto actual=lua.combat_damage(p);
            const auto raw=std::max<std::int64_t>(1,
                std::int64_t{attack}*power/100-std::int64_t{defense}*defense_percent/100);
            const auto expected=std::min<std::int64_t>(1000000,roll<1000?raw*150/100:raw);
            require(actual.damage==expected && actual.mp_cost==8 && actual.critical==(roll<1000),
                    "Explicit Lua combat formula mismatch");
            ++count;
        }
        const god2::CombatRuleInput valid{31,13,175,100,8,24,1000,150,1000};
        for(unsigned field=0;field<10;++field) {
            auto p=valid;
            switch(field) {
            case 0:p.attack=1000001;break;
            case 1:p.defense=1000001;break;
            case 2:p.power_percent=10001;break;
            case 3:p.defense_percent=101;break;
            case 4:p.mp_cost=25;break;
            case 5:p.available_mp=1000001;break;
            case 6:p.critical_chance_bp=10001;break;
            case 7:p.critical_multiplier_percent=99;break;
            case 8:p.critical_multiplier_percent=1001;break;
            case 9:p.roll=10000;break;
            }
            bool threw=false;
            try {(void)lua.combat_damage(p);} catch(const std::invalid_argument&) {threw=true;}
            require(threw,"Invalid combat input accepted");
        }
        auto p=valid;p.critical_chance_bp=10000;p.roll=9999;
        require(lua.combat_damage(p).critical,"Guaranteed crit boundary");
        p.critical_chance_bp=0;p.roll=0;
        require(!lua.combat_damage(p).critical,"Zero crit boundary");
        p.mp_cost=p.available_mp;
        require(lua.combat_damage(p).mp_cost==p.available_mp,"Exact MP cost rejected");
        require(lua.reload_all(),"Reload failed");
        require(lua.combat_damage(valid).damage==41,"Reload changed formula");
        // CUSTOM-0012 diagnostic encounter budgets, not native birth stats or
        // approval of production balance. Exercise the actual Lua rule each turn.
        struct Encounter { unsigned hp,mp; bool skill; unsigned turns,left_hp,left_mp; bool won; };
        const std::array<Encounter,6> encounters{{
            {100,50,false,9,4,50,true}, {100,50,true,3,76,26,true},
            {76,34,false,7,0,34,false}, {76,34,true,3,52,10,true},
            {100,7,true,9,4,7,true}, {76,0,true,7,0,0,false}}};
        for(const auto& e:encounters) {
            auto hp=e.hp,mp=e.mp,enemy=150u,turns=0u;
            while(hp && enemy && turns<100) {
                const bool cast=e.skill && mp>=8;
                const god2::CombatRuleInput action{cast?40u:31u,cast?6u:13u,
                    cast?150u:100u,100,cast?8u:0u,mp,0,150,0};
                const auto hit=lua.combat_damage(action);
                enemy-=std::min(enemy,hit.damage);mp-=hit.mp_cost;++turns;
                if(enemy) {
                    const auto reply=lua.combat_damage({20,8,100,100,0,0,0,150,0});
                    hp-=std::min(hp,reply.damage);
                }
            }
            require(turns==e.turns && hp==e.left_hp && mp==e.left_mp && (enemy==0)==e.won,
                    "Diagnostic encounter resource budget changed");
            std::cout<<"CUSTOM-0012 budget hp="<<e.hp<<" mp="<<e.mp<<" skill="<<e.skill
                     <<" turns="<<turns<<" hp_after="<<hp<<" mp_after="<<mp<<" won="<<(enemy==0)<<'\n';
        }
        std::cout<<count<<" formula cases and boundary checks passed\n";
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
