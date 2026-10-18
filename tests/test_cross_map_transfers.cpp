#include "game/RecoveredCrossMapNavigation.h"
#include "handlers/RecoveredCharacterService.h"
#include "handlers/RecoveredMovementService.h"
#include "handlers/RecoveredPlayerPresence.h"
#include "db/SqliteDatabase.h"
#include "protocol/DiagnosticRemoteActor.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "protocol/RecoveredWorldFrame.h"
#include "scripting/LuaEngine.h"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <source_location>
#include <sstream>
#include <stdexcept>

void test_config();
namespace {
void require(bool value,const std::source_location where=std::source_location::current()) {
    if(!value)throw std::runtime_error("Cross-map invariant failed at line "+std::to_string(where.line()));
}
template<class F> void rejects(F&& action) {
    try {action();}catch(const std::exception&){return;}
    throw std::runtime_error("Unqualified cross-map operation accepted");
}
using Route=god2::RecoveredCrossMapNavigation::Route;
using Plan=god2::DiagnosticDoorPlan;
using Request=god2::RecoveredMovement::Request;
using Step=god2::RecoveredMovementService::CommittedMove::Step;
using Key=std::array<std::uint16_t,7>;
Key key(const Route& route) {return {route.area,route.source_scene,route.source_x,route.source_y,route.target_scene,route.target_x,route.target_y};}
std::optional<Plan> proposal(god2::LuaEngine& lua,std::uint16_t scene,std::uint16_t before_x,std::uint16_t before_y,
    std::uint16_t x,std::uint16_t y,bool enabled=true) {
    return lua.diagnostic_door({2,scene,before_x,before_y,x,y,true,false,false,false,enabled});
}
Step adjacent(god2::RecoveredMovementService& movement,god2::LuaEngine& lua,std::uint16_t scene,std::uint16_t x,std::uint16_t y) {
    for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx) {
        if(!dx&&!dy)continue;
        const int nx=int(x)+dx,ny=int(y)+dy;if(nx<0||ny<0||nx>=0x4000||ny>0x7fff)continue;
        const auto sx=static_cast<std::uint16_t>(nx),sy=static_cast<std::uint16_t>(ny);
        if(movement.qualifies_transfer_destination(2,scene,sx,sy)&&!proposal(lua,scene,x,y,sx,sy))return {sx,sy};
    }
    throw std::runtime_error("Qualified cross-map point lacks a safe adjacent cell");
}
void check_transfer(const std::vector<std::uint8_t>& wire,const Route& route) {
    const auto logical=god2::RecoveredWorldFrame::decode(wire);
    require(logical&&logical->size()==9&&(*logical)[0]==0x61);
    const auto selector=std::uint16_t((*logical)[1])|(std::uint16_t((*logical)[2])<<8);
    require(selector==(route.area|(route.target_scene<<6)));
    std::uint32_t packed=0;for(unsigned i=0;i<4;++i)packed|=std::uint32_t((*logical)[5+i])<<(8*i);
    require(!(packed&0x10000u));
    require((packed&3u)==(route.target_scene?3u:1u));
    require(((packed>>2)&0x3fffu)==route.target_x&&((packed>>17)&0x7fffu)==route.target_y);
}
std::set<Key> lua_literals(const std::filesystem::path& path) {
    std::ifstream input(path);require(bool(input));std::string line;std::set<Key> result;
    while(std::getline(input,line)) {
        const auto first=line.find_first_not_of(" \t\r");if(first==std::string::npos||line[first]!='{')continue;
        const auto end=line.find('}',first);require(end!=std::string::npos);
        std::istringstream row(line.substr(first+1,end-first-1));Key values{};
        for(std::size_t i=0;i<values.size();++i) {
            unsigned value=0;require(bool(row>>value)&&value<=0xffffu);values[i]=static_cast<std::uint16_t>(value);
            if(i+1<values.size()){char comma=0;require(bool(row>>comma)&&comma==',');}
        }
        row>>std::ws;require(row.eof());require(result.insert(values).second);
    }
    require(input.eof());return result;
}
}
int main() {
    try {
        test_config();
        const auto root=std::filesystem::path(GOD2_SOURCE_DIR);
        god2::RecoveredCrossMapNavigation registry(root/"resources/world/tw/cross-map-v4.json");
        require(registry.routes().size()==48);
        for(const auto scene:{2u,32u,43u,108u})require(registry.kind(2,static_cast<std::uint16_t>(scene))==3);
        require(!registry.kind(2,1)&&!registry.kind(4,43));
        require(!registry.cell(2,43,-1,0)&&!registry.cell(2,43,735,0));
        god2::LuaEngine lua(root/"scripts",false);require(lua.initialize());std::set<Key> exact;
        std::size_t inward=0,outward=0;
        for(const auto& route:registry.routes()) {
            require(exact.insert(key(route)).second);require(registry.contains(route));
            inward+=route.target_scene!=0;outward+=route.source_scene!=0;
            require(proposal(lua,route.source_scene,route.source_x-1,route.source_y,route.source_x,route.source_y)==
                std::optional{Plan{route.area,route.target_scene,route.target_x,route.target_y}});
            require(!proposal(lua,route.source_scene,route.source_x,route.source_y,route.source_x,route.source_y));
            require(!proposal(lua,route.source_scene,route.source_x-1,route.source_y,route.source_x,route.source_y,false));
            auto wrong=route;++wrong.target_x;require(!registry.contains(wrong));
            wrong=route;wrong.area=4;require(!registry.contains(wrong));
        }
        require(inward==24&&outward==24&&lua_literals(root/"scripts/gameplay/current_cross_map_transfers_data.lua")==exact);
        // The cross-MDL policy uses independently qualified marker2/3 arrivals.
        // Neither the exact inverse nor same-slot landing is manufactured.
        require(registry.contains({2,0,302,429,43,188,55}));
        require(registry.contains({2,0,284,452,43,52,184}));
        require(registry.contains({2,43,51,185,0,283,453}));
        require(registry.contains({2,0,394,96,2,60,78}));
        require(registry.contains({2,2,60,77,0,393,96}));
        require(registry.contains({2,0,119,287,32,59,62}));
        require(registry.contains({2,32,58,62,0,118,287}));
        require(registry.contains({2,0,641,456,108,85,55}));
        require(registry.contains({2,108,85,54,0,640,456}));
        require(!registry.contains({2,0,302,429,43,188,54}));

        god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
        const auto owner=db.accounts().create("cross-map-owner","hash").id;
        const auto other=db.accounts().create("cross-map-other","hash").id;
        god2::RecoveredCharacterService characters(db.recovered_characters());
        god2::RecoveredCharacterCreate create{};create.payload[0]='C';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
        const auto character=characters.create(owner,create);
        const auto profile=db.recovered_characters().list_for_account(owner).front().profile;
        god2::RecoveredMovementService::TownDiagnostic settings{
            root/"artifacts/world-atlas/town-2-4.json",{4,3},86,71,true,
            root/"artifacts/world-atlas/indoor-2-15.json",
            root/"artifacts/world-atlas/island01-full-navigation-2-0.json"};
        god2::RecoveredMovementService disabled(db.recovered_characters(),settings);
        require(!disabled.has_cross_map_navigation()&&!disabled.registered_cross_map_scene(2,43));
        require(!disabled.qualified_scene_kind(2,43)&&!disabled.qualifies_transfer_destination(2,43,188,55));
        settings.cross_map_navigation=root/"resources/world/tw/cross-map-v4.json";
        god2::RecoveredMovementService movement(db.recovered_characters(),settings);
        require(movement.has_cross_map_navigation()&&movement.qualified_scene_kind(2,43)==3);
        require(!movement.registered_door_pair(2,4,43)&&!movement.qualified_scene_kind(2,107));
        // Unanimous nonzero is deliberately restricted to two original trigger
        // points. Raw consensus still reports each 01/02 conflict as unknown.
        god2::RecoveredParentNavigation parent(settings.island_navigation,2);
        require(!parent.consistent_cell(394,96)&&parent.consistently_walkable(394,96));
        require(!registry.cell(2,2,60,77)&&registry.consistently_walkable(2,2,60,77));
        require(!disabled.qualifies_transfer_destination(2,0,394,96));
        require(!disabled.qualifies_transfer_destination(2,2,60,77));
        require(movement.qualifies_transfer_destination(2,0,394,96));
        require(movement.qualifies_transfer_destination(2,2,60,77));
        require(!parent.consistent_cell(437,85)&&parent.consistently_walkable(437,85));
        require(!movement.qualifies_transfer_destination(2,0,437,85));
        require(parent.consistent_cell(392,94)==0&&!parent.consistently_walkable(392,94));
        require(registry.cell(2,2,59,77)==0&&!registry.consistently_walkable(2,2,59,77));
        require(!movement.qualifies_transfer_destination(2,0,392,94));
        require(!movement.qualifies_transfer_destination(2,2,59,77));
        require(!registry.cell(2,2,-1,0)&&!registry.consistently_walkable(2,2,-1,0));
        require(!movement.qualifies_transfer_destination(2,2,0,0));
        auto position=[&]{return db.recovered_characters().load_position(owner,character);};
        std::uint64_t session=100;
        const auto spawn=god2::RecoveredRemoteActor::parse_logical(god2::DiagnosticRemoteActor::logical(0,0)).value();
        const auto removal=god2::RecoveredRemoteActorRemove::parse_logical(god2::DiagnosticRemoteActor::logical(2,0)).value();
        for(const auto& route:registry.routes()) {
            require(movement.qualifies_transfer_destination(2,route.source_scene,route.source_x,route.source_y));
            require(movement.qualifies_transfer_destination(2,route.target_scene,route.target_x,route.target_y));
            const auto start=adjacent(movement,lua,route.source_scene,route.source_x,route.source_y);
            db.recovered_characters().commit_position(owner,character,position(),2,route.source_scene,start.x,start.y);
            const auto entry=movement.prepare(session,owner,character);
            require(god2::RecoveredWorldEntryView::read(entry)->kind==(route.source_scene?3:1));
            movement.bind(session,owner,character);
            const auto moved=movement.move_committed(session,owner,character,
                std::array{Request{route.source_x,route.source_y,1,0}}, {},
                [&](const god2::RecoveredMovementService::MovePreview& step) {
                    const auto plan=proposal(lua,step.scene,step.before_x,step.before_y,step.x,step.y);
                    return plan.has_value();
                });
            require(moved.displaced_steps==1&&moved.path.size()==1&&position()==std::optional{moved.after});
            const auto ack=god2::RecoveredMovement::ack(1);
            require(moved.reply==std::vector<std::uint8_t>(ack.begin(),ack.end()));
            rejects([&]{movement.begin_registered_cross_map_transfer(session,other,character,moved.after,route.target_scene,route.target_x,route.target_y);});
            auto stale=moved.after;++stale.revision;
            rejects([&]{movement.begin_registered_cross_map_transfer(session,owner,character,stale,route.target_scene,route.target_x,route.target_y);});
            auto zero=moved.after;zero.revision=0;
            rejects([&]{movement.begin_registered_cross_map_transfer(session,owner,character,zero,route.target_scene,route.target_x,route.target_y);});
            rejects([&]{movement.begin_registered_cross_map_transfer(session,owner,character,moved.after,route.target_scene,route.target_x+1,route.target_y);});
            require(position()==std::optional{moved.after});
            check_transfer(movement.begin_registered_cross_map_transfer(session,owner,character,moved.after,
                route.target_scene,route.target_x,route.target_y),route);
            const auto landing=*position();
            require(landing==god2::RecoveredPosition{2,route.target_scene,route.target_x,route.target_y,moved.after.revision+1});
            rejects([&]{movement.move_committed(session,owner,character,std::array{Request{landing.x,landing.y,1,0}});});
            rejects([&]{movement.finish_town_transfer(session,other,character);});
            movement.finish_town_transfer(session,owner,character);
            const auto idle=movement.move_committed(session,owner,character,std::array{Request{landing.x,landing.y,1,0}});
            require(!idle.displaced_steps&&!proposal(lua,landing.scene,landing.x,landing.y,landing.x,landing.y));
            const auto away=adjacent(movement,lua,landing.scene,landing.x,landing.y);
            const auto walked=movement.move_committed(session,owner,character,std::array{Request{away.x,away.y,2,0}});
            require(walked.displaced_steps==1);movement.remove(session++);
            const auto restored=movement.prepare(session,owner,character);
            const auto view=god2::RecoveredWorldEntryView::read(restored);require(view.has_value());
            require(view->scene==landing.scene&&view->x==away.x&&view->y==away.y&&view->kind==(landing.scene?3:1));
            const auto presence=god2::RecoveredPlayerPresence::from_world_entry(session,owner,character,restored,profile,
                spawn,removal,movement.qualified_scene_kind(2,landing.scene));
            require(presence.location==god2::RecoveredVisibility::Scene{2,landing.scene});
            require((god2::RecoveredRemoteActor::encode_logical(presence.spawn)[13]&3u)==view->kind);
            if(landing.scene) {
                rejects([&]{god2::RecoveredPlayerPresence::from_world_entry(session,owner,character,restored,profile,spawn,removal);});
                rejects([&]{god2::RecoveredPlayerPresence::from_world_entry(session,owner,character,restored,profile,spawn,removal,2);});
            }
            movement.remove(session++);
            // Actual native entry bookkeeping rejects kind2 aliases of MDT scenes.
            if(landing.scene) {
                const auto wrong=god2::RecoveredWorldEntry::wire(character,profile,away.x,away.y,2,landing.scene,2);
                rejects([&]{movement.prepare_native(session,owner,character,wrong);});
                rejects([&]{movement.prepare_native_scene(session,owner,character,wrong);});
            }
            movement.prepare_native(session,owner,character,restored);movement.bind(session,owner,character);
            require(movement.current_location(session,owner,character)==position());movement.remove(session++);
        }
        std::cout<<"Cross-map service/Lua, exact owner/CAS/pending/navigation, kind3 entry/presence and restore PASS; native UI separate\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
