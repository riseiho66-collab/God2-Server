#include "game/RecoveredWildernessTransfers.h"
#include "game/DiagnosticDoorRule.h"
#include "handlers/RecoveredCharacterService.h"
#include "handlers/RecoveredMovementService.h"
#include "db/SqliteDatabase.h"
#include "protocol/RecoveredWorldFrame.h"
#include "scripting/LuaEngine.h"
#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <set>
#include <sstream>
#include <source_location>
#include <stdexcept>
#include <nlohmann/json.hpp>

// CUSTOM-0153: direct service/Lua regression harness. Application socket and
// original-client acceptance remain separate; this test never uses a live DB.
namespace {
void require(bool value,const std::source_location where=std::source_location::current()) {
    if(!value)throw std::runtime_error("Wilderness invariant failed at line "+std::to_string(where.line()));
}
template<class F> void rejects(F&& action) {
    try { action(); } catch(const std::exception&) { return; }
    throw std::runtime_error("Unqualified wilderness operation accepted");
}
using Step=god2::RecoveredMovementService::CommittedMove::Step;
using Request=god2::RecoveredMovement::Request;
using Plan=god2::DiagnosticDoorPlan;
std::optional<Plan> proposal(god2::LuaEngine& lua,std::uint16_t before_x,std::uint16_t before_y,
                            std::uint16_t x,std::uint16_t y,std::uint16_t area=2) {
    return lua.diagnostic_door({area,0,before_x,before_y,x,y,area==2,false,false,area==4});
}
Step approach(god2::RecoveredMovementService& movement,god2::LuaEngine& lua,std::uint16_t x,std::uint16_t y,std::uint16_t area=2) {
    for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx) {
        if(!dx&&!dy)continue;
        const int nx=int(x)+dx,ny=int(y)+dy;
        if(nx<0||ny<0||nx>=0x4000||ny>0x7fff)continue;
        auto sx=static_cast<std::uint16_t>(nx),sy=static_cast<std::uint16_t>(ny);
        if(movement.qualifies_transfer_destination(area,0,sx,sy)&&!proposal(lua,x,y,sx,sy,area))return {sx,sy};
    }
    throw std::runtime_error("Qualified original endpoint has no safe adjacent approach");
}
void transfer_frame(const std::vector<std::uint8_t>& wire,std::uint16_t x,std::uint16_t y,std::uint16_t area=2) {
    const auto logical=god2::RecoveredWorldFrame::decode(wire);
    require(logical&&logical->size()==9&&(*logical)[0]==0x61&&(*logical)[1]==area&&(*logical)[2]==0);
    const auto packed=std::uint32_t((*logical)[5])|(std::uint32_t((*logical)[6])<<8)|
        (std::uint32_t((*logical)[7])<<16)|(std::uint32_t((*logical)[8])<<24);
    require((packed&0x10000u)==0); // Full parent reset must retire old walking motion/path.
    require((packed&3u)==1u&&((packed>>2)&0x3fffu)==x&&((packed>>17)&0x7fffu)==y);
}
std::set<std::array<std::uint16_t,6>> literal_lua_tuples(const std::filesystem::path& path) {
    std::ifstream input(path);require(bool(input));std::string line;
    std::set<std::array<std::uint16_t,6>> result;
    while(std::getline(input,line)) {
        const auto first=line.find_first_not_of(" \t\r");
        if(first==std::string::npos||line[first]!='{')continue;
        const auto end=line.find('}',first);require(end!=std::string::npos);
        std::istringstream row(line.substr(first+1,end-first-1));std::array<std::uint16_t,6> key{};
        for(std::size_t i=0;i<key.size();++i) {
            unsigned value=0;require(bool(row>>value)&&value<=0xffffu);key[i]=static_cast<std::uint16_t>(value);
            if(i+1<key.size()){char comma=0;require(bool(row>>comma)&&comma==',');}
        }
        row>>std::ws;require(row.eof());require(result.insert(key).second);
    }
    require(input.eof());return result;
}
}
int main() {
    try {
        const auto root=std::filesystem::path(GOD2_SOURCE_DIR);
        god2::LuaEngine lua(root/"scripts",false);require(lua.initialize());
        std::set<std::array<std::uint16_t,6>> exact;
        for(const auto& route:god2::kQualifiedWildernessTransfers) {
            require((route.area==2||route.area==4)&&route.scene==0);
            require(exact.insert({route.area,route.scene,route.source_x,route.source_y,route.target_x,route.target_y}).second);
            require(god2::qualified_wilderness_transfer(route.area,0,route.source_x,route.source_y,route.target_x,route.target_y));
            require(god2::qualified_wilderness_transfer(route.area,0,route.target_x,route.target_y,route.source_x,route.source_y));
            require(!god2::qualified_wilderness_transfer(route.area==2?4:2,0,route.source_x,route.source_y,route.target_x,route.target_y));
            require(!god2::qualified_wilderness_transfer(route.area,4,route.source_x,route.source_y,route.target_x,route.target_y));
            require(!god2::qualified_wilderness_transfer(route.area,0,route.source_x,route.source_y,route.target_x+1,route.target_y));
            require(proposal(lua,route.source_x-1,route.source_y,route.source_x,route.source_y,route.area)==
                    std::optional{Plan{route.area,0,route.target_x,route.target_y}});
            require(!proposal(lua,route.source_x,route.source_y,route.source_x,route.source_y,route.area));
            require(!proposal(lua,route.target_x,route.target_y,route.target_x,route.target_y,route.area));
            require(!lua.diagnostic_door({route.area,0,std::uint32_t(route.source_x-1),route.source_y,route.source_x,route.source_y,false}));
            // Each area must use its own existing flag, never the other parent's.
            require(!lua.diagnostic_door({route.area,0,std::uint32_t(route.source_x-1),route.source_y,route.source_x,route.source_y,route.area==4,false,false,route.area==2}));
            require(!lua.diagnostic_door({13,0,std::uint32_t(route.source_x-1),route.source_y,route.source_x,route.source_y,true,false,false,true}));
            require(!lua.diagnostic_door({route.area,1,std::uint32_t(route.source_x-1),route.source_y,route.source_x,route.source_y,true,false,false,true}));
        }
        require(exact.size()==98);
        require(std::count_if(exact.begin(),exact.end(),[](const auto& row){return row[0]==2;})==28);
        require(std::count_if(exact.begin(),exact.end(),[](const auto& row){return row[0]==4;})==70);
        // Read the independent Lua literals too: extra or duplicate Lua rows
        // must fail even if all C++ entries still return the expected proposal.
        require(literal_lua_tuples(root/"scripts/gameplay/current_wilderness_transfers_data.lua")==exact);
        require(god2::qualified_wilderness_transfer(2,0,407,256,384,275));
        require(!god2::qualified_wilderness_transfer(2,0,407,256,383,275)); // Marker2 is not native slot0's landing.
        // Frozen town/room and parent boundaries keep their distinct dispatch.
        require(lua.diagnostic_door({2,4,86,71,86,70})==std::optional{Plan{2,15,16,19}});
        require(lua.diagnostic_door({2,15,16,19,16,20})==std::optional{Plan{2,4,86,71}});
        require(lua.diagnostic_door({2,4,56,75,55,75,true})==std::optional{Plan{2,0,476,209}});
        require(lua.diagnostic_door({2,0,476,209,477,209,true})==std::optional{Plan{2,4,56,75}});
        require(lua.diagnostic_door({4,3,49,124,50,124,false,false,false,true})==std::optional{Plan{4,0,318,363}});

        god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
        const auto owner=db.accounts().create("wilderness-owner","hash").id;
        const auto other=db.accounts().create("wilderness-other","hash").id;
        god2::RecoveredCharacterService characters(db.recovered_characters());
        god2::RecoveredCharacterCreate create{};create.payload[0]='W';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
        const auto character=characters.create(owner,create);
        god2::RecoveredMovementService::TownDiagnostic settings{
            root/"artifacts/world-atlas/town-2-4.json",{4,3},86,71,true,
            root/"artifacts/world-atlas/indoor-2-15.json",
            root/"artifacts/world-atlas/island01-full-navigation-2-0.json"};
        // Source-only compatibility regression: both pinned contracts must load.
        auto legacy=settings;legacy.island_navigation.clear();
        legacy.indoor_scenes=root/"artifacts/world-atlas/town-doors-2.json";
        god2::RecoveredMovementService old_contract(db.recovered_characters(),legacy);
        settings.indoor_scenes=root/"resources/world/tw/town-doors-v2.json";
        settings.kunlun_parent_navigation=root/"artifacts/world-atlas/island03-full-navigation-4-0.json";
        settings.birthplace_navigation=root/"artifacts/world-atlas/kunlun-4-3.json";
        settings.birthplace_x=185;settings.birthplace_y=98;
        god2::RecoveredMovementService movement(db.recovered_characters(),settings);
        std::ifstream bundle(settings.indoor_scenes);const auto catalog=nlohmann::json::parse(bundle);
        require(catalog.at("routes").size()==26&&catalog.at("navigation").size()==26);
        for(const auto& route:catalog.at("routes"))if(route.at("navigation_eligible").get<bool>())
            require(movement.registered_door_pair(2,4,route.at("scene").get<std::uint16_t>()));
        auto position=[&]{return db.recovered_characters().load_position(owner,character);};
        std::uint64_t session=100;
        for(const auto& route:god2::kQualifiedWildernessTransfers) {
            require(movement.qualifies_transfer_destination(route.area,0,route.source_x,route.source_y));
            require(movement.qualifies_transfer_destination(route.area,0,route.target_x,route.target_y));
            const auto adjacent=approach(movement,lua,route.source_x,route.source_y,route.area);
            db.recovered_characters().commit_position(owner,character,position(),route.area,0,adjacent.x,adjacent.y);
            movement.prepare(session,owner,character);movement.bind(session,owner,character);
            std::optional<Plan> plan;
            const auto moved=movement.move_committed(session,owner,character,
                std::array{Request{route.source_x,route.source_y,1,0}},
                [&](const god2::RecoveredMovementService::MovePreview& preview) {
                    require(preview.displaced_steps==1);
                    plan=proposal(lua,preview.before_x,preview.before_y,preview.x,preview.y,preview.area);
                });
            require(plan==std::optional{Plan{route.area,0,route.target_x,route.target_y}});
            const auto ack=god2::RecoveredMovement::ack(1);
            require(moved.reply==std::vector<std::uint8_t>(ack.begin(),ack.end()));
            require(position()==std::optional{moved.after});
            rejects([&]{movement.begin_registered_wilderness_transfer(session,other,character,moved.after,route.target_x,route.target_y);});
            auto stale=moved.after;++stale.revision;
            rejects([&]{movement.begin_registered_wilderness_transfer(session,owner,character,stale,route.target_x,route.target_y);});
            auto zero=moved.after;zero.revision=0;
            rejects([&]{movement.begin_registered_wilderness_transfer(session,owner,character,zero,route.target_x,route.target_y);});
            rejects([&]{movement.begin_registered_wilderness_transfer(session,owner,character,moved.after,route.target_x+1,route.target_y);});
            require(position()==std::optional{moved.after});
            const auto wire=movement.begin_registered_wilderness_transfer(session,owner,character,moved.after,route.target_x,route.target_y);
            transfer_frame(wire,route.target_x,route.target_y,route.area);
            auto ordered=moved.reply;ordered.insert(ordered.end(),wire.begin(),wire.end());
            require(std::equal(ack.begin(),ack.end(),ordered.begin())); // Same ordering contract as Application.
            const auto landing=*position();
            require(landing==god2::RecoveredPosition{route.area,0,route.target_x,route.target_y,moved.after.revision+1});
            rejects([&]{movement.begin_registered_wilderness_transfer(session,owner,character,landing,route.source_x,route.source_y);});
            rejects([&]{movement.move_committed(session,owner,character,std::array{Request{landing.x,landing.y,1,0}});});
            rejects([&]{movement.finish_town_transfer(session,other,character);});
            require(position()==std::optional{landing});
            movement.finish_town_transfer(session,owner,character);
            rejects([&]{movement.finish_town_transfer(session,owner,character);});
            const auto idle=movement.move_committed(session,owner,character,std::array{Request{landing.x,landing.y,1,0}});
            require(idle.displaced_steps==0&&!proposal(lua,landing.x,landing.y,landing.x,landing.y,route.area));
            require(idle.after.x==landing.x&&idle.after.y==landing.y);
            const auto away=approach(movement,lua,landing.x,landing.y,route.area);
            movement.move_committed(session,owner,character,std::array{Request{away.x,away.y,2,0}});
            const auto returned=movement.move_committed(session,owner,character,std::array{Request{landing.x,landing.y,3,0}});
            require(returned.displaced_steps==1&&proposal(lua,away.x,away.y,landing.x,landing.y,route.area)==
                    std::optional{Plan{route.area,0,route.source_x,route.source_y}});
            const auto back=movement.begin_registered_wilderness_transfer(session,owner,character,returned.after,route.source_x,route.source_y);
            transfer_frame(back,route.source_x,route.source_y,route.area);
            require(position()==std::optional{god2::RecoveredPosition{route.area,0,route.source_x,route.source_y,returned.after.revision+1}});
            movement.finish_town_transfer(session,owner,character);movement.remove(session++);
        }
        {
            // A complete 3-step wire batch can visit the marker in the middle.
            // Start on it, walk away, return, then queue another old-scene step.
            // Aggregate origin==destination is deliberately not a no-op: the
            // second step has a real adjacent origin and must trigger exactly once.
            const Step marker{407,256};const auto away=approach(movement,lua,marker.x,marker.y);
            const std::array batch{Request{away.x,away.y,1,0},Request{marker.x,marker.y,2,0},Request{away.x,away.y,3,0}};
            const auto bind_at_marker=[&] {
                db.recovered_characters().commit_position(owner,character,position(),2,0,marker.x,marker.y);
                movement.prepare(session,owner,character);movement.bind(session,owner,character);
            };
            bind_at_marker();
            // Disabled route flags preserve full-batch ACKs, queue and final pose.
            std::size_t disabled_steps=0;
            const auto whole=movement.move_committed(session,owner,character,batch,{},
                [&](const god2::RecoveredMovementService::MovePreview& step) {
                    ++disabled_steps;
                    require(!lua.diagnostic_door({step.area,step.scene,step.before_x,step.before_y,step.x,step.y,false}));
                    return false;
                });
            require(disabled_steps==3&&whole.displaced_steps==3&&whole.reply.size()==15&&whole.path.size()==3);
            require(whole.after.x==away.x&&whole.after.y==away.y&&position()==std::optional{whole.after});
            movement.remove(session++);bind_at_marker();
            const auto saved=*position();
            std::optional<god2::RecoveredMovementService::MovePreview> last_step;
            std::optional<Plan> plan;std::size_t examined=0;
            const auto qualified_plan=[&](const god2::RecoveredMovementService::MovePreview& step)->std::optional<Plan> {
                if(!step.displaced_steps)return std::nullopt;
                auto found=proposal(lua,step.before_x,step.before_y,step.x,step.y);
                if(found)require(found->area==step.area&&found->scene==step.scene&&
                    god2::qualified_wilderness_transfer(step.area,step.scene,step.x,step.y,
                        static_cast<std::uint16_t>(found->x),static_cast<std::uint16_t>(found->y))&&
                    movement.qualifies_transfer_destination(2,0,static_cast<std::uint16_t>(found->x),static_cast<std::uint16_t>(found->y)));
                return found;
            };
            const auto prefix=movement.move_committed(session,owner,character,batch,
                [&](const god2::RecoveredMovementService::MovePreview& aggregate) {
                    require(last_step&&last_step->before_x==away.x&&last_step->before_y==away.y);
                    require(aggregate.before_x==marker.x&&aggregate.before_y==marker.y&&
                        aggregate.x==marker.x&&aggregate.y==marker.y&&aggregate.displaced_steps==2);
                    plan=qualified_plan(*last_step);
                },[&](const god2::RecoveredMovementService::MovePreview& step) {
                    ++examined;last_step=step;return qualified_plan(step).has_value();
                });
            const auto ack1=god2::RecoveredMovement::ack(1),ack2=god2::RecoveredMovement::ack(2);
            std::vector<std::uint8_t> prefix_acks(ack1.begin(),ack1.end());prefix_acks.insert(prefix_acks.end(),ack2.begin(),ack2.end());
            require(examined==2&&prefix.reply==prefix_acks&&prefix.displaced_steps==2);
            require(prefix.path==std::vector<Step>{{away.x,away.y},{marker.x,marker.y}});
            require(prefix.after==god2::RecoveredPosition{2,0,marker.x,marker.y,saved.revision+1}&&position()==std::optional{prefix.after});
            require(plan==std::optional{Plan{2,0,384,275}});
            const auto transfer=movement.begin_registered_wilderness_transfer(session,owner,character,prefix.after,384,275);
            transfer_frame(transfer,384,275);const auto landing=*position();
            rejects([&]{movement.move_committed(session,owner,character,std::span<const Request>(batch).subspan(2));});
            require(position()==std::optional{landing});
            movement.finish_town_transfer(session,owner,character);
            rejects([&]{movement.move_committed(session,owner,character,std::span<const Request>(batch).subspan(2));});
            const auto idle=movement.move_committed(session,owner,character,std::array{Request{384,275,1,0}}, {},
                [&](const god2::RecoveredMovementService::MovePreview& step) {return qualified_plan(step).has_value();});
            require(!idle.displaced_steps&&idle.reply==std::vector<std::uint8_t>(ack1.begin(),ack1.end())&&
                idle.after.x==384&&idle.after.y==275&&!proposal(lua,384,275,384,275));
            movement.remove(session++);
        }
        {
            // Only the wilderness API opts out. Preserve legacy kind0 town
            // same-scene reuse without making a new client acceptance claim.
            const auto before=db.recovered_characters().commit_position(owner,character,position(),2,4,86,71);
            movement.prepare(session,owner,character);movement.bind(session,owner,character);
            const auto wire=movement.begin_town_transfer(session,owner,character,before,86,71);
            const auto logical=god2::RecoveredWorldFrame::decode(wire);
            require(logical&&logical->size()==9&&(*logical)[1]==2&&(*logical)[2]==1);
            const auto packed=std::uint32_t((*logical)[5])|(std::uint32_t((*logical)[6])<<8)|
                (std::uint32_t((*logical)[7])<<16)|(std::uint32_t((*logical)[8])<<24);
            require((packed&0x10000u)!=0&&(packed&3u)==0&&((packed>>2)&0x3fffu)==86&&((packed>>17)&0x7fffu)==71);
            movement.finish_town_transfer(session,owner,character);movement.remove(session++);
        }
        std::cout<<"98 registry/Lua routes on two configured parent maps: direct-service full reset, owner/CAS, pending, no-op and reverse checks passed; legacy town reuse retained; not native socket acceptance\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
