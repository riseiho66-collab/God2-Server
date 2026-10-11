#include "handlers/RecoveredMovementService.h"
#include "handlers/RecoveredCharacterService.h"
#include "db/SqliteDatabase.h"
#include "scripting/LuaEngine.h"
#include "protocol/RecoveredWorldFrame.h"
#include <array>
#include <iostream>
#include <source_location>
#include <stdexcept>

namespace {
void check(bool ok,const std::source_location where=std::source_location::current()) {
    if(!ok)throw std::runtime_error("Parent route invariant at line "+std::to_string(where.line()));
}
template<class F>void rejects(F f){try{f();}catch(const std::exception&){return;}throw std::runtime_error("Invalid parent accepted");}
}
int main(){try{
    const auto root=std::filesystem::path(GOD2_SOURCE_DIR);
    god2::RecoveredParentNavigation nav(root/"artifacts/world-atlas/island03-full-navigation-4-0.json");
    check(nav.consistent_cell(318,363)==2 && nav.consistent_cell(318,362)==1);
    check(!nav.consistent_cell(-1,363) && !nav.consistent_cell(420,363) && !nav.consistent_cell(318,1092));
    god2::RecoveredParentNavigation island01(root/"artifacts/world-atlas/island01-full-navigation-2-0.json",2);
    check(island01.consistent_cell(477,209)==2 && island01.consistent_cell(476,209)==1);
    god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
    const auto owner=db.accounts().create("parent-owner","hash").id;
    god2::RecoveredCharacterService chars(db.recovered_characters());
    god2::RecoveredCharacterCreate create{};create.payload[0]='P';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
    const auto character=chars.create(owner,create);
    const auto profile=db.recovered_characters().list_for_account(owner).front().profile;
    const auto before=db.recovered_characters().commit_position(owner,character,{},4,3,50,123);
    god2::RecoveredMovementService::TownDiagnostic settings{root/"artifacts/world-atlas/town-2-4.json",{4,3},86,71,true};
    settings.birthplace_navigation=root/"artifacts/world-atlas/kunlun-4-3.json";settings.birthplace_x=126;settings.birthplace_y=126;
    settings.kunlun_parent_navigation=root/"artifacts/world-atlas/island03-full-navigation-4-0.json";
    settings.island_navigation=root/"artifacts/world-atlas/island01-full-navigation-2-0.json";
    god2::RecoveredMovementService move(db.recovered_characters(),settings);
    check(move.qualifies_transfer_destination(2,0,476,209));
    check(move.registered_parent_pair(4,3,0) && move.registered_parent_pair(4,0,3));
    check(!move.registered_parent_pair(2,3,0) && !move.registered_door_pair(4,3,0));
    move.prepare(1,owner,character);move.bind(1,owner,character);
    god2::LuaEngine lua(root/"scripts",false);check(lua.initialize());
    check(!lua.diagnostic_door({4,3,50,123,50,124}));
    check(!lua.diagnostic_door({4,0,318,363,318,363,false,false,false,true}));
    const auto plan=lua.diagnostic_door({4,3,50,123,50,124,false,false,false,true});
    check(plan && *plan==god2::DiagnosticDoorPlan{4,0,318,363});
    using Request=god2::RecoveredMovement::Request;
    const auto step=move.move_committed(1,owner,character,std::array{Request{50,124,1,0}});
    rejects([&]{move.begin_registered_parent_transfer(1,owner+1,character,step.after,0,318,363);});
    rejects([&]{move.begin_registered_parent_transfer(1,owner,character,step.after,0,318,362);});
    rejects([&]{move.begin_registered_parent_transfer(1,owner,character,before,0,318,363);});
    const auto wire=god2::RecoveredWorldFrame::decode(move.begin_registered_parent_transfer(1,owner,character,step.after,0,318,363));
    check(wire && wire->size()==9 && (*wire)[0]==0x61 && (*wire)[1]==4 && (*wire)[2]==0 && ((*wire)[5]&3)==1);
    rejects([&]{move.move(1,owner,character,std::array{Request{318,362,1,0}});});
    rejects([&]{move.finish_town_transfer(1,owner+1,character);});
    move.remove(1); // persisted island arrival survives a lost context receipt
    god2::RecoveredMovementService cold(db.recovered_characters(),settings);
    check(cold.prepare(2,owner,character)==god2::RecoveredWorldEntry::wire(character,profile,318,363,4,0,1));
    cold.bind(2,owner,character);
    const auto island=db.recovered_characters().load_position(owner,character);check(island && island->revision==before.revision+2);
    rejects([&]{cold.begin_registered_parent_transfer(2,owner,character,*island,3,50,123);});
    // Leave and reenter the exact original point to avoid immediate bounce.
    cold.move(2,owner,character,std::array{Request{318,362,1,0}});
    const auto returning=cold.move_committed(2,owner,character,std::array{Request{318,363,2,0}});
    check(lua.diagnostic_door({4,0,318,362,318,363,false,false,false,true})==std::optional{god2::DiagnosticDoorPlan{4,3,50,124}});
    const auto back=god2::RecoveredWorldFrame::decode(cold.begin_registered_parent_transfer(2,owner,character,returning.after,3,50,124));
    check(back && (*back)[1]==196 && (*back)[2]==0 && ((*back)[5]&3)==0);
    cold.finish_town_transfer(2,owner,character);
    const auto after=db.recovered_characters().load_position(owner,character);
    check(after && after->area==4 && after->scene==3 && after->x==50 && after->y==124 && after->revision==before.revision+5);
    cold.remove(2);check(cold.prepare(3,owner,character)==god2::RecoveredWorldEntry::wire(character,profile,50,124,4,3,0));
    // Disabled registry must refuse a durable island save instead of aliasing town.
    cold.remove(3);db.recovered_characters().commit_position(owner,character,after,4,0,318,363);
    settings.kunlun_parent_navigation.clear();god2::RecoveredMovementService disabled(db.recovered_characters(),settings);
    rejects([&]{disabled.prepare(4,owner,character);});
    std::cout<<"CUSTOM-0053 parent2 directions, native selectors/kinds, exact points, CAS/pending/cold restore passed\n";return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
