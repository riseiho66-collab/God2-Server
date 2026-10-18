#include "game/WorldTransferCatalog.h"
#include "core/Application.h"
#include "core/SharedWorldHostPlan.h"
#include "handlers/RecoveredCharacterService.h"
#include "handlers/RecoveredMovementService.h"
#include "handlers/RecoveredPlayerPresence.h"
#include "db/SqliteDatabase.h"
#include "protocol/DiagnosticRemoteActor.h"
#include "protocol/RecoveredWorldEntryView.h"
#include "scripting/LuaEngine.h"
#include <array>
#include <filesystem>
#include <iostream>
#include <source_location>
#include <stdexcept>

void test_config();
namespace {
void require(bool value,const std::source_location where=std::source_location::current()) {
    if(!value)throw std::runtime_error("World transfer invariant failed at line "+std::to_string(where.line()));
}
template<class F> void rejects(F&& action){try{action();}catch(const std::exception&){return;}throw std::runtime_error("Unqualified world transfer accepted");}
using Catalog=god2::WorldTransferCatalog;
using Request=god2::RecoveredMovement::Request;
std::optional<std::array<std::uint16_t,2>> approach(const Catalog& catalog,const Catalog::Route& route) {
    for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx) {
        if(!dx&&!dy)continue;
        const int x=int(route.source.x)+dx,y=int(route.source.y)+dy;if(x<0||y<0||x>0x3fff||y>0x7fff)continue;
        const auto sx=static_cast<std::uint16_t>(x),sy=static_cast<std::uint16_t>(y);
        if(catalog.available({route.source.scene,sx,sy})&&
           catalog.route_for_step(route.source.scene,sx,sy,route.source.x,route.source.y)==&route)return std::array{sx,sy};
    }
    return std::nullopt;
}
}
int main() {
    try {
        test_config();
        // Actual supplied owners would replace the world dispatcher. Reject
        // before calling factories, opening a database or binding listeners.
        for(const bool entry_override:{false,true}) {
            god2::Config config;config.world_transfers_enabled=true;bool called=false;
            god2::SharedWorldHostPlan plan;
            if(entry_override)plan.make_taiwan_world_entry=[&](const auto&)->god2::SharedTaiwanWorldEntrySource::Entry {called=true;throw std::runtime_error("Unexpected entry source activation");};
            else plan.make_taiwan_movement=[&](const auto&)->god2::SharedTaiwanMovementSource::Binding {called=true;throw std::runtime_error("Unexpected movement source activation");};
            bool rejected=false;
            try {god2::run_server(config,plan,1);}catch(const std::invalid_argument& error){rejected=std::string(error.what()).find("actual native source transfer bridge unavailable")!=std::string::npos;}
            require(rejected&&!called);
        }
        const auto root=std::filesystem::path(GOD2_SOURCE_DIR);
        Catalog catalog(root/"resources/world/tw/world-transfer-v1/catalog.json");
        require(!catalog.scenes().empty()&&!catalog.routes().empty());
        require(!catalog.scene({0,0})&&!catalog.scene({17,0})&&!catalog.route("unissued/arbitrary-destination"));
        god2::LuaEngine lua(root/"scripts",false);require(lua.initialize());
        god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
        const auto owner=db.accounts().create("world-transfer-owner","hash").id;
        const auto other=db.accounts().create("world-transfer-other","hash").id;
        god2::RecoveredCharacterService characters(db.recovered_characters());
        god2::RecoveredCharacterCreate create{};create.payload[0]='G';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
        const auto character=characters.create(owner,create);
        const auto profile=db.recovered_characters().list_for_account(owner).front().profile;
        god2::RecoveredMovementService::TownDiagnostic settings{root/"artifacts/world-atlas/town-2-4.json",{4,3},86,71,true,
            root/"artifacts/world-atlas/indoor-2-15.json",root/"artifacts/world-atlas/island01-full-navigation-2-0.json"};
        settings.world_transfer_catalog=root/"resources/world/tw/world-transfer-v1/catalog.json";
        god2::RecoveredMovementService movement(db.recovered_characters(),settings);
        const auto* actual=movement.world_catalog();require(actual);
        const auto spawn=god2::RecoveredRemoteActor::parse_logical(god2::DiagnosticRemoteActor::logical(0,0)).value();
        const auto removal=god2::RecoveredRemoteActorRemove::parse_logical(god2::DiagnosticRemoteActor::logical(2,0)).value();
        auto position=[&]{return db.recovered_characters().load_position(owner,character);};
        std::uint64_t session=100;std::size_t restored=0,moved_routes=0;
        std::array<std::size_t,4> restored_kinds{};
        for(const auto& scene:actual->scenes()) {
            require(movement.qualified_scene_kind(scene.key.area,scene.key.scene)==scene.kind);
            std::optional<Catalog::Point> cell;
            for(std::uint16_t y=0;y<scene.height&&!cell;++y)for(std::uint16_t x=0;x<scene.width;++x)
                if(actual->available({scene.key,x,y})){cell=Catalog::Point{scene.key,x,y};break;}
            if(!cell)continue; // Fully blocked source scenes cannot yield a player spawn.
            db.recovered_characters().commit_position(owner,character,position(),scene.key.area,scene.key.scene,cell->x,cell->y);
            const auto frame=movement.prepare(session,owner,character);const auto view=god2::RecoveredWorldEntryView::read(frame);
            require(view&&view->area==scene.key.area&&view->scene==scene.key.scene&&view->kind==scene.kind);
            const auto presence=god2::RecoveredPlayerPresence::from_world_entry(session,owner,character,frame,profile,spawn,removal,scene.kind);
            require(presence.location==god2::RecoveredVisibility::Scene{scene.key.area,scene.key.scene});
            require((god2::RecoveredRemoteActor::encode_logical(presence.spawn)[13]&3u)==scene.kind);
            movement.remove(session++);
            movement.prepare_native(session,owner,character,frame);movement.bind(session,owner,character);
            require(movement.current_location(session,owner,character)==position());movement.remove(session++);
            const auto wrong=god2::RecoveredWorldEntry::wire(character,profile,cell->x,cell->y,scene.key.area,scene.key.scene,(scene.kind+1)%4);
            rejects([&]{movement.prepare_native(session,owner,character,wrong);});
            ++restored;++restored_kinds[scene.kind];
        }
        require(restored&&restored_kinds[0]&&restored_kinds[1]&&restored_kinds[2]&&restored_kinds[3]);
        for(const auto& route:actual->routes()) {
            require(actual->route(route.id)==&route&&actual->available(route.destination));
            if(route.trigger==Catalog::Trigger::NpcOffer)continue; // Separate issued-offer authority is mandatory.
            const auto start=approach(*actual,route);require(start.has_value());
            require(!actual->route_for_step(route.source.scene,route.source.x,route.source.y,route.source.x,route.source.y));
            require(lua.world_transfer_proposal(route,(*start)[0],(*start)[1],route.source.x,route.source.y));
            require(!lua.world_transfer_proposal(route,route.source.x,route.source.y,route.source.x,route.source.y));
            // Merely restoring/standing on a trigger never mints displacement
            // authority. Even an acknowledged no-op remains inadmissible.
            db.recovered_characters().commit_position(owner,character,position(),route.source.scene.area,route.source.scene.scene,route.source.x,route.source.y);
            movement.prepare(session,owner,character);movement.bind(session,owner,character);
            rejects([&]{movement.begin_world_transfer(session,owner,character,*position(),route.id);});
            movement.move_committed(session,owner,character,std::array{Request{route.source.x,route.source.y,1,0}});
            rejects([&]{movement.begin_world_transfer(session,owner,character,*position(),route.id);});
            movement.remove(session++);
            db.recovered_characters().commit_position(owner,character,position(),route.source.scene.area,route.source.scene.scene,(*start)[0],(*start)[1]);
            movement.prepare(session,owner,character);movement.bind(session,owner,character);
            rejects([&]{movement.begin_world_transfer(session,owner,character,*position(),route.id);});
            const auto moved=movement.move_committed(session,owner,character,
                std::array{Request{route.source.x,route.source.y,1,0},Request{65535,65535,2,0}}, {},
                [&](const god2::RecoveredMovementService::MovePreview& step){return actual->route_for_step({step.area,step.scene},step.before_x,step.before_y,step.x,step.y)!=nullptr;});
            const auto before=*position();require(before==moved.after&&moved.displaced_steps==1&&moved.reply.size()==5&&moved.path.size()==1);
            rejects([&]{movement.begin_world_transfer(session,other,character,before,route.id);});
            auto stale=before;++stale.revision;rejects([&]{movement.begin_world_transfer(session,owner,character,stale,route.id);});
            rejects([&]{movement.begin_world_transfer(session,owner,character,before,"unissued/arbitrary-destination");});
            require(position()==std::optional{before});
            const auto wire=movement.begin_world_transfer(session,owner,character,before,route.id);
            const auto logical=god2::RecoveredWorldFrame::decode(wire);require(logical&&logical->size()==9&&logical->front()==0x61);
            const auto selector=std::uint16_t((*logical)[1])|(std::uint16_t((*logical)[2])<<8);
            require(selector==(route.destination.scene.area|(route.destination.scene.scene<<6)));
            std::uint32_t packed=0;for(unsigned i=0;i<4;++i)packed|=std::uint32_t((*logical)[5+i])<<(8*i);
            require(!(packed&0x10000u)&&(packed&3u)==actual->scene(route.destination.scene)->kind);
            require(((packed>>2)&0x3fffu)==route.destination.x&&((packed>>17)&0x7fffu)==route.destination.y);
            const auto landing=*position();require(landing==god2::RecoveredPosition{route.destination.scene.area,route.destination.scene.scene,route.destination.x,route.destination.y,before.revision+1});
            rejects([&]{movement.move_committed(session,owner,character,std::array{Request{landing.x,landing.y,1,0}});});
            movement.finish_town_transfer(session,owner,character);
            require(!movement.move_committed(session,owner,character,std::array{Request{landing.x,landing.y,1,0}}).displaced_steps);
            movement.remove(session++);const auto restored_frame=movement.prepare(session,owner,character);
            const auto view=god2::RecoveredWorldEntryView::read(restored_frame);
            require(view&&view->area==landing.area&&view->scene==landing.scene&&view->x==landing.x&&view->y==landing.y);
            movement.remove(session++);++moved_routes;
        }
        std::cout<<"World catalog restored_scenes="<<restored<<" committed_routes="<<moved_routes<<" owner/CAS/pending/kind/restore PASS; native UI and NPC positive authority separate\n";return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
