#include "scripting/LuaEngine.h"
#include "handlers/RecoveredMovementService.h"
#include "handlers/RecoveredCharacterService.h"
#include "handlers/DiagnosticQuestConversation.h"
#include "db/SqliteDatabase.h"
#include "protocol/RecoveredWorldFrame.h"
#include "game/DiagnosticDoorRule.h"
#include <array>
#include <iostream>
#include <stdexcept>
#include <source_location>
#include <fstream>
#include <nlohmann/json.hpp>

namespace {
void require(bool ok,const std::source_location where=std::source_location::current()) {
    if(!ok) throw std::runtime_error("Diagnostic doorway invariant failed at line "+std::to_string(where.line()));
}
template<class F> void rejects(F f) {
    try { f(); } catch(const std::exception&) { return; }
    throw std::runtime_error("Invalid doorway operation accepted");
}
}
int main() {
    try {
        for(std::uint64_t character: {1u,2u,3u,4u,5u,255u,256u,0x3fffu}) {
            for(std::uint8_t flag=0;flag<=1;++flag) {
                const std::array<std::uint8_t,4> receipt{static_cast<std::uint8_t>(character),static_cast<std::uint8_t>(character>>8),flag,0};
                require(god2::diagnostic_door_context_receipt(receipt,true,flag,character));
                require(!god2::diagnostic_door_context_receipt(receipt,false,flag,character));
                require(!god2::diagnostic_door_context_receipt(receipt,true,1-flag,character));
                require(!god2::diagnostic_door_context_receipt(receipt,true,flag,character==1?2:1));
                auto malformed=receipt;malformed[3]=1;
                require(!god2::diagnostic_door_context_receipt(malformed,true,flag,character));
                require(god2::diagnostic_island_arrival_receipt(receipt,true,0,character,flag));
                require(!god2::diagnostic_island_arrival_receipt(receipt,true,4,character,flag));
                require(!god2::diagnostic_island_arrival_receipt(receipt,false,0,character,flag));
                require(god2::diagnostic_island_return_receipt(receipt,true,4,character,flag));
                require(!god2::diagnostic_island_return_receipt(receipt,false,4,character,flag));
                require(!god2::diagnostic_island_return_receipt(receipt,true,0,character,flag));
            }
        }
        for(unsigned flag=2;flag<=255;++flag)
            require(!god2::diagnostic_owned_scene_receipt({2,0,static_cast<std::uint8_t>(flag),0},2,static_cast<std::uint8_t>(flag)));
        require(!god2::diagnostic_owned_scene_receipt({0,0,0,0},0,0));
        require(!god2::diagnostic_owned_scene_receipt({0,0x40,0,0},0x4000,0));
        const auto root=std::filesystem::path(GOD2_SOURCE_DIR);
        god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
        const auto owner=db.accounts().create("door-owner","test-hash").id;
        const auto other=db.accounts().create("door-other","test-hash").id;
        god2::RecoveredCharacterService characters(db.recovered_characters());
        god2::RecoveredCharacterCreate create{};
        create.payload[0]='A';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
        const auto character=characters.create(owner,create);
        god2::LuaEngine lua(root/"scripts",false);require(lua.initialize());
        for(std::uint32_t y=75;y<=80;++y) {
            const auto out=lua.diagnostic_door({2,4,56,y,55,y,true});
            require(out && *out==god2::DiagnosticDoorPlan{2,0,476,y+134});
            const auto back=lua.diagnostic_door({2,0,476,y+134,477,y+134,true});
            require(back && *back==god2::DiagnosticDoorPlan{2,4,56,y});
            if(y<80) {
                const auto diagonal=lua.diagnostic_door({2,0,476,y+134,477,y+135,true});
                require(diagonal && *diagonal==god2::DiagnosticDoorPlan{2,4,56,y+1});
            }
            require(!lua.diagnostic_door({2,4,56,y,55,y}));
            require(!lua.diagnostic_door({2,4,55,y,55,y+1,true}));
        }
        require(!lua.diagnostic_door({2,0,476,208,477,209,true}));
        require(!lua.diagnostic_door({2,0,476,214,477,215,true}));
        require(!lua.diagnostic_door({2,0,476,209,477,214,true}));
        require(!lua.diagnostic_door({2,0,475,212,477,213,true}));
        god2::RecoveredMovementService::TownDiagnostic settings{
            root/"artifacts/world-atlas/town-2-4.json",{4,3},86,71,true,
            root/"artifacts/world-atlas/indoor-2-15.json"};
        god2::RecoveredMovementService movement(db.recovered_characters(),settings);
        require(movement.qualifies_transfer_destination(15,16,19));
        require(!movement.qualifies_transfer_destination(99,16,19));
        require(!movement.qualifies_transfer_destination(15,0x4000,19));
        movement.prepare(1,owner,character);movement.bind(1,owner,character);
        using Request=god2::RecoveredMovement::Request;
        auto position=[&]{return *db.recovered_characters().load_position(owner,character);};
        for(unsigned cycle=0;cycle<2;++cycle) {
            std::optional<god2::DiagnosticDoorPlan> plan;
            const auto moved=movement.move_committed(1,owner,character,
                std::array{Request{86,70,1,0}},[&](const god2::RecoveredMovementService::MovePreview& preview){
                    require(preview.area==2 && preview.scene==4 &&
                        preview.before_x==86 && preview.before_y==71 &&
                        preview.x==86 && preview.y==70 && preview.displaced_steps==1);
                    plan=lua.diagnostic_door({preview.area,preview.scene,
                        preview.before_x,preview.before_y,preview.x,preview.y});
                });
            require(moved.displaced_steps==1 && moved.after==position());
            require(plan.has_value() && plan->area==2 && plan->scene==15);
            // Test harness supplies sequencing; no Application activation or
            // native socket acceptance is claimed by this direct service test.
            const auto before=position();
            rejects([&]{movement.begin_indoor_transfer(1,other,character,before,16,19);});
            require(position()==before);
            const auto packet=movement.begin_indoor_transfer(1,owner,character,before,
                static_cast<std::uint16_t>(plan->x),static_cast<std::uint16_t>(plan->y));
            const auto logical=god2::RecoveredWorldFrame::decode(packet);
            require(logical && *logical==std::vector<std::uint8_t>{0x61,0xc2,3,0,0,0x42,0,0x26,0});
            require(position().scene==15 && position().x==16 && position().y==19);
            const auto destination=position();
            rejects([&]{movement.move(1,owner,character,std::array{Request{16,20,1,0}});});
            rejects([&]{movement.resume_after_battle(1,owner,character);});
            rejects([&]{movement.begin_indoor_transfer(1,owner,character,before,16,19);});
            rejects([&]{movement.finish_town_transfer(1,other,character);});
            require(position()==destination);
            movement.finish_town_transfer(1,owner,character);
            rejects([&]{movement.finish_town_transfer(1,owner,character);});
            const auto exit=movement.move_committed(1,owner,character,std::array{Request{16,20,1,0}});
            const auto back=lua.diagnostic_door({2,15,16,19,exit.after.x,exit.after.y});
            require(back.has_value() && back->area==2 && back->scene==4);
            movement.begin_outdoor_return(1,owner,character,exit.after,
                static_cast<std::uint16_t>(back->x),static_cast<std::uint16_t>(back->y));
            require(position().scene==4 && position().x==86 && position().y==71);
            movement.finish_town_transfer(1,owner,character);
            require(!lua.diagnostic_door({2,4,86,71,86,71}));
        }
        const auto saved=position();
        movement.remove(1);
        god2::RecoveredMovementService fresh(db.recovered_characters(),settings);
        fresh.prepare(2,owner,character);fresh.bind(2,owner,character);
        require(position()==saved);
        const auto stationary=fresh.move_committed(2,owner,character,std::array{Request{86,71,1,0}});
        require(stationary.displaced_steps==0);
        require(!lua.diagnostic_door({2,4,86,71,stationary.after.x,stationary.after.y}));
        // Interleave two owners while one transfer loses its context receipt.
        create.payload[0]='B';
        const auto second=characters.create(other,create);
        fresh.prepare(3,other,second);fresh.bind(3,other,second);
        god2::DiagnosticQuestConversation conversations;
        require(conversations.bind(2,owner,character));
        require(conversations.bind(3,other,second));
        require(conversations.spawn(2,owner,character));
        require(conversations.spawn(3,other,second));
        require(conversations.open(2,owner,character));
        require(conversations.open(3,other,second));
        const auto entry=fresh.move_committed(2,owner,character,std::array{Request{86,70,2,0}});
        fresh.begin_indoor_transfer(2,owner,character,entry.after,16,19);
        const auto pending=position();
        rejects([&]{fresh.finish_town_transfer(3,owner,character);});
        require(!conversations.leave_scene(3,owner,character));
        const auto independent=fresh.move_committed(3,other,second,std::array{Request{86,70,1,0}});
        require(independent.after.scene==4 && position()==pending);
        require(conversations.consume(3,other,second,{0x1234,2,0x9a,0}));
        fresh.remove(2);conversations.remove(2);
        rejects([&]{fresh.finish_town_transfer(2,owner,character);});
        require(!conversations.consume(2,owner,character,{0x1234,2,0x9a,0}));
        fresh.prepare(4,owner,character);fresh.bind(4,owner,character);
        require(position()==pending);
        rejects([&]{fresh.finish_town_transfer(4,owner,character);});
        rejects([&]{fresh.move(4,owner,character,std::array{Request{86,70,2,0}});});
        const auto exit=fresh.move_committed(4,owner,character,std::array{Request{16,20,1,0}});
        fresh.begin_outdoor_return(4,owner,character,exit.after,86,71);
        const auto returning=position();
        fresh.remove(4);
        fresh.prepare(5,owner,character);fresh.bind(5,owner,character);
        require(position()==returning);
        rejects([&]{fresh.finish_town_transfer(5,owner,character);});
        require(fresh.move_committed(5,owner,character,std::array{Request{86,70,1,0}}).after.scene==4);
        require(db.recovered_characters().load_position(other,second)==independent.after);
        require(!conversations.consume(3,other,second,{0x1234,2,0x9a,0}));
        require(conversations.allow_followup(3,other,second));
        require(conversations.next_request_word(3,other,second)==0x1235);
        // CUSTOM-0052: every source-linked door point pair crosses both ways,
        // loses one pending receipt, reconnects, and resumes native movement.
        settings.indoor_scenes=root/"artifacts/world-atlas/town-doors-2.json";
        std::ifstream bundle(settings.indoor_scenes);
        const auto catalog=nlohmann::json::parse(bundle);
        unsigned checked_pairs=0;
        for(const auto& route:catalog.at("routes")) {
            if(!route.at("navigation_eligible").get<bool>())continue;
            const auto scene=route.at("scene").get<std::uint16_t>();
            for(const auto& pair:route.at("pairs")) {
                const auto tx=pair.at("town_trigger")[0].get<std::uint16_t>();
                const auto ty=pair.at("town_trigger")[1].get<std::uint16_t>();
                const auto ax=pair.at("town_arrival")[0].get<std::uint16_t>();
                const auto ay=pair.at("town_arrival")[1].get<std::uint16_t>();
                const auto ix=pair.at("indoor_arrival")[0].get<std::uint16_t>();
                const auto iy=pair.at("indoor_arrival")[1].get<std::uint16_t>();
                const auto ex=pair.at("indoor_trigger")[0].get<std::uint16_t>();
                const auto ey=pair.at("indoor_trigger")[1].get<std::uint16_t>();
                god2::SqliteDatabase room_db(":memory:");room_db.initialize();room_db.migrate();
                const auto room_owner=room_db.accounts().create("room-owner","hash").id;
                god2::RecoveredCharacterService room_characters(room_db.recovered_characters());
                create.payload[0]='R';
                const auto room_character=room_characters.create(room_owner,create);
                const auto town_start=room_db.recovered_characters().commit_position(room_owner,room_character,{},2,4,ax,ay);
                god2::RecoveredMovementService all_rooms(room_db.recovered_characters(),settings);
                require(all_rooms.registered_door_pair(4,scene));
                require(!all_rooms.registered_door_pair(scene,scene));
                require(all_rooms.qualifies_transfer_destination(scene,ix,iy));
                all_rooms.prepare(20,room_owner,room_character);all_rooms.bind(20,room_owner,room_character);
                const auto proposal=lua.diagnostic_door({2,4,ax,ay,tx,ty,false,true});
                require(proposal && *proposal==god2::DiagnosticDoorPlan{2,scene,ix,iy});
                require(!lua.diagnostic_door({2,scene,ix,iy,ix,iy,false,true}));
                const auto step=all_rooms.move_committed(20,room_owner,room_character,std::array{Request{tx,ty,1,0}});
                const auto wire=all_rooms.begin_registered_door_transfer(20,room_owner,room_character,step.after,scene,ix,iy);
                const auto decoded=god2::RecoveredWorldFrame::decode(wire);
                require(decoded && decoded->size()==9 && (*decoded)[0]==0x61);
                require(((*decoded)[1]+256u*(*decoded)[2])==(2u+(scene<<6)));
                require(((*decoded)[5]&3)==2);
                rejects([&]{all_rooms.move(20,room_owner,room_character,std::array{Request{ex,ey,1,0}});});
                all_rooms.remove(20); // disconnect before the receipt
                god2::RecoveredMovementService restored(room_db.recovered_characters(),settings);
                restored.prepare(21,room_owner,room_character);restored.bind(21,room_owner,room_character);
                const auto indoors=restored.current_location(21,room_owner,room_character);
                require(indoors && indoors->scene==scene && indoors->x==ix && indoors->y==iy);
                const auto exit_step=restored.move_committed(21,room_owner,room_character,std::array{Request{ex,ey,1,0}});
                const auto back=lua.diagnostic_door({2,scene,ix,iy,ex,ey,false,true});
                require(back && *back==god2::DiagnosticDoorPlan{2,4,ax,ay});
                restored.begin_registered_door_transfer(21,room_owner,room_character,exit_step.after,4,ax,ay);
                rejects([&]{restored.finish_town_transfer(21,room_owner+1,room_character);});
                restored.finish_town_transfer(21,room_owner,room_character);
                const auto after=room_db.recovered_characters().load_position(room_owner,room_character);
                require(after && after->scene==4 && after->x==ax && after->y==ay && after->revision==town_start.revision+4);
                restored.remove(21);restored.prepare(22,room_owner,room_character);restored.bind(22,room_owner,room_character);
                require(restored.current_location(22,room_owner,room_character)==after);
                ++checked_pairs;
            }
        }
        require(checked_pairs==26);
        require(!lua.diagnostic_door({2,4,65,46,65,45,false}));
        std::cout<<"23 rooms / 26 point pairs: 52 directed transfers with persisted reconnect passed\n";
        {
        settings.birthplace_navigation=root/"artifacts/world-atlas/kunlun-4-3.json";
        settings.birthplace_x=185;settings.birthplace_y=98;
        settings.kunlun_indoor_scenes=root/"artifacts/world-atlas/kunlun-doors-4.json";
        std::ifstream kunlun_file(settings.kunlun_indoor_scenes);
        const auto kunlun_catalog=nlohmann::json::parse(kunlun_file);
        unsigned checked_pairs=0;
        for(const auto& route:kunlun_catalog.at("routes")) {
            if(!route.at("navigation_eligible").get<bool>())continue;
            const auto scene=route.at("scene").get<std::uint16_t>();
            for(const auto& pair:route.at("pairs")) {
                const auto tx=pair.at("town_trigger")[0].get<std::uint16_t>();
                const auto ty=pair.at("town_trigger")[1].get<std::uint16_t>();
                const auto ax=pair.at("town_arrival")[0].get<std::uint16_t>();
                const auto ay=pair.at("town_arrival")[1].get<std::uint16_t>();
                const auto ix=pair.at("indoor_arrival")[0].get<std::uint16_t>();
                const auto iy=pair.at("indoor_arrival")[1].get<std::uint16_t>();
                const auto ex=pair.at("indoor_trigger")[0].get<std::uint16_t>();
                const auto ey=pair.at("indoor_trigger")[1].get<std::uint16_t>();
                god2::SqliteDatabase room_db(":memory:");room_db.initialize();room_db.migrate();
                const auto room_owner=room_db.accounts().create("room-owner","hash").id;
                god2::RecoveredCharacterService room_characters(room_db.recovered_characters());
                create.payload[0]='R';
                const auto room_character=room_characters.create(room_owner,create);
                const auto town_start=room_db.recovered_characters().commit_position(room_owner,room_character,{},4,3,ax,ay);
                god2::RecoveredMovementService all_rooms(room_db.recovered_characters(),settings);
                require(all_rooms.registered_door_pair(4,3,scene));
                require(!all_rooms.registered_door_pair(4,scene,scene));
                require(all_rooms.qualifies_transfer_destination(4,scene,ix,iy));
                all_rooms.prepare(20,room_owner,room_character);all_rooms.bind(20,room_owner,room_character);
                const auto proposal=lua.diagnostic_door({4,3,ax,ay,tx,ty,false,false,true});
                require(proposal && *proposal==god2::DiagnosticDoorPlan{4,scene,ix,iy});
                require(!lua.diagnostic_door({4,scene,ix,iy,ix,iy,false,false,true}));
                const auto step=all_rooms.move_committed(20,room_owner,room_character,std::array{Request{tx,ty,1,0}});
                const auto wire=all_rooms.begin_registered_door_transfer(20,room_owner,room_character,step.after,scene,ix,iy);
                const auto decoded=god2::RecoveredWorldFrame::decode(wire);
                require(decoded && decoded->size()==9 && (*decoded)[0]==0x61);
                require(((*decoded)[1]+256u*(*decoded)[2])==(4u+(scene<<6)));
                require(((*decoded)[5]&3)==2);
                rejects([&]{all_rooms.move(20,room_owner,room_character,std::array{Request{ex,ey,1,0}});});
                all_rooms.remove(20); // disconnect before the receipt
                god2::RecoveredMovementService restored(room_db.recovered_characters(),settings);
                restored.prepare(21,room_owner,room_character);restored.bind(21,room_owner,room_character);
                const auto indoors=restored.current_location(21,room_owner,room_character);
                require(indoors && indoors->scene==scene && indoors->x==ix && indoors->y==iy);
                const auto exit_step=restored.move_committed(21,room_owner,room_character,std::array{Request{ex,ey,1,0}});
                const auto back=lua.diagnostic_door({4,scene,ix,iy,ex,ey,false,false,true});
                require(back && *back==god2::DiagnosticDoorPlan{4,3,ax,ay});
                restored.begin_registered_door_transfer(21,room_owner,room_character,exit_step.after,3,ax,ay);
                rejects([&]{restored.finish_town_transfer(21,room_owner+1,room_character);});
                restored.finish_town_transfer(21,room_owner,room_character);
                const auto after=room_db.recovered_characters().load_position(room_owner,room_character);
                require(after && after->area==4 && after->scene==3 && after->x==ax && after->y==ay && after->revision==town_start.revision+4);
                restored.remove(21);restored.prepare(22,room_owner,room_character);restored.bind(22,room_owner,room_character);
                require(restored.current_location(22,room_owner,room_character)==after);
                ++checked_pairs;
            }
        }
        require(checked_pairs==12);
        std::cout<<"6 Kunlun rooms / 12 point pairs: 24 directed transfers with persisted reconnect passed\n";
        }
        settings.island_navigation=root/"artifacts/world-atlas/island01-full-navigation-2-0.json";
        std::ifstream boundary_file(root/"artifacts/world-atlas/island01-all-boundaries-routes-2-0.json");
        const auto boundaries=nlohmann::json::parse(boundary_file);
        unsigned checked_boundaries=0;
        for(const auto& edge:boundaries.at("pairs")) {
            if(!edge.at("navigation_eligible").get<bool>())continue;
            const auto tx=edge.at("town").at("trigger")[0].get<std::uint16_t>();
            const auto ty=edge.at("town").at("trigger")[1].get<std::uint16_t>();
            const auto ax=edge.at("town").at("arrival")[0].get<std::uint16_t>();
            const auto ay=edge.at("town").at("arrival")[1].get<std::uint16_t>();
            const auto ix=edge.at("island").at("arrival")[0].get<std::uint16_t>();
            const auto iy=edge.at("island").at("arrival")[1].get<std::uint16_t>();
            const auto ex=edge.at("island").at("trigger")[0].get<std::uint16_t>();
            const auto ey=edge.at("island").at("trigger")[1].get<std::uint16_t>();
            god2::SqliteDatabase portal_db(":memory:");portal_db.initialize();portal_db.migrate();
            const auto portal_owner=portal_db.accounts().create("portal-owner","hash").id;
            god2::RecoveredCharacterService portal_characters(portal_db.recovered_characters());
            create.payload[0]='P';
            const auto portal_character=portal_characters.create(portal_owner,create);
            portal_db.recovered_characters().commit_position(portal_owner,portal_character,{},2,4,ax,ay);
            god2::RecoveredMovementService all_boundaries(portal_db.recovered_characters(),settings);
            all_boundaries.prepare(30,portal_owner,portal_character);all_boundaries.bind(30,portal_owner,portal_character);
            const auto go=lua.diagnostic_door({2,4,ax,ay,tx,ty,true,true});
            require(go && *go==god2::DiagnosticDoorPlan{2,0,ix,iy});
            const auto entered=all_boundaries.move_committed(30,portal_owner,portal_character,std::array{Request{tx,ty,1,0}});
            all_boundaries.begin_island_transfer(30,portal_owner,portal_character,entered.after,ix,iy);
            all_boundaries.finish_town_transfer(30,portal_owner,portal_character);
            all_boundaries.remove(30);all_boundaries.prepare(31,portal_owner,portal_character);all_boundaries.bind(31,portal_owner,portal_character);
            const auto arrived=all_boundaries.current_location(31,portal_owner,portal_character);
            require(arrived && arrived->scene==0 && arrived->x==ix && arrived->y==iy);
            const auto back=lua.diagnostic_door({2,0,ix,iy,ex,ey,true,true});
            require(back && *back==god2::DiagnosticDoorPlan{2,4,ax,ay});
            const auto leaving=all_boundaries.move_committed(31,portal_owner,portal_character,std::array{Request{ex,ey,1,0}});
            all_boundaries.begin_island_return(31,portal_owner,portal_character,leaving.after,ax,ay);
            all_boundaries.finish_town_transfer(31,portal_owner,portal_character);
            const auto returned=all_boundaries.current_location(31,portal_owner,portal_character);
            require(returned && returned->scene==4 && returned->x==ax && returned->y==ay);
            ++checked_boundaries;
        }
        require(checked_boundaries==22);
        require(!lua.diagnostic_door({2,4,134,83,135,83,true,true}));
        std::cout<<"22 of 23 parent boundary pairs: 44 directed transfers/relogin passed; blocked543,207 omitted\n";
        std::cout<<"Two Lua/C++ doorway roundtrips, pending/ownership/replay gates and service restore passed; not live acceptance\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
