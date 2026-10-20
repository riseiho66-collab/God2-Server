#include "handlers/RecoveredMovementService.h"
#include "handlers/RecoveredCharacterService.h"
#include "db/SqliteDatabase.h"
#include "protocol/RecoveredWorldFrame.h"
#include <array>
#include <functional>
#include <stdexcept>

namespace {
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
template<class F> void rejects(F f) {
    try { f(); } catch(const std::exception&) { return; }
    throw std::runtime_error("Invalid recovered movement accepted");
}
// Delegate real persisted material, injecting only a repository read observer.
// This is a SOURCE regression, not an executed DB/native acceptance claim.
struct ObservedPositions final:god2::RecoveredCharacterRepository {
    god2::RecoveredCharacterRepository& source;std::function<void()> read;
    explicit ObservedPositions(god2::RecoveredCharacterRepository& value):source(value){}
    std::optional<god2::CharacterRoleSnapshot> load_role(std::uint64_t a,std::uint64_t c)override{return source.load_role(a,c);}
    god2::RoleResourceCommit commit_role_resources(std::uint64_t a,std::uint64_t c,
        const std::optional<god2::CharacterRoleSnapshot>& r,const god2::CharacterResources& e,
        god2::CharacterRoleSnapshot n,god2::CharacterResources v)override{return source.commit_role_resources(a,c,r,e,std::move(n),v);}
    std::optional<god2::CharacterExperience> load_experience(std::uint64_t a,std::uint64_t c)override{return source.load_experience(a,c);}
    god2::BattleSettlement settle_battle(std::uint64_t a,std::uint64_t c,std::uint64_t b,
        const god2::CharacterResources& e,god2::CharacterResources n,bool w,std::uint64_t x,
        const std::optional<god2::BattleProgressionCommit>& p)override{return source.settle_battle(a,c,b,e,n,w,x,p);}
    std::uint64_t reserve_battle(std::uint64_t a,std::uint64_t c,const god2::CharacterResources& e)override{return source.reserve_battle(a,c,e);}
    std::optional<god2::CharacterResources> load_resources(std::uint64_t a,std::uint64_t c)override{return source.load_resources(a,c);}
    god2::CharacterResources commit_resources(std::uint64_t a,std::uint64_t c,
        const std::optional<god2::CharacterResources>& e,god2::CharacterResources n)override{return source.commit_resources(a,c,e,n);}
    god2::RecoveredCharacter create(std::uint64_t a,const std::array<std::uint8_t,40>& p)override{return source.create(a,p);}
    std::vector<god2::RecoveredCharacter> list_for_account(std::uint64_t a)override{return source.list_for_account(a);}
    std::optional<god2::RecoveredPosition> load_position(std::uint64_t a,std::uint64_t c)override{
        const auto value=source.load_position(a,c);if(read)read();return value;}
    god2::RecoveredPosition commit_position(std::uint64_t a,std::uint64_t c,
        const std::optional<god2::RecoveredPosition>& e,std::uint16_t ar,std::uint16_t s,std::uint16_t x,std::uint16_t y)override{
        return source.commit_position(a,c,e,ar,s,x,y);}
};
}
void test_recovered_movement_service() {
    using Request=god2::RecoveredMovement::Request;
    using Step=god2::RecoveredMovementService::CommittedMove::Step;
    god2::SqliteDatabase db(":memory:");db.initialize();db.migrate();
    const auto owner=db.accounts().create("move-owner","test-hash").id;
    const auto other=db.accounts().create("move-other","test-hash").id;
    god2::RecoveredCharacterService characters(db.recovered_characters());
    god2::RecoveredCharacterCreate create{};
    create.payload[0]='A';create.payload[29]=1;create.payload[31]=1;create.payload[40]=4;
    const auto character=characters.create(owner,create);
    god2::RecoveredMovementService service(db.recovered_characters(),
        std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/indoor-2-15.json");
    const std::array first{Request{18,12,1,0}};
    rejects([&]{service.move(1,owner,character,first);});
    rejects([&]{service.prepare(1,other,character);});
    rejects([&]{service.prepare(0,owner,character);});
    rejects([&]{service.bind(1,owner,character);});
    require(!service.character_active(owner,character),"Unprepared character reported active");
    service.prepare(1,owner,character);
    require(service.character_active(owner,character) && !service.character_active(other,character),
        "Prepared native lease missing or cross-account active lookup");
    rejects([&]{service.move(1,owner,character,first);});
    service.bind(1,owner,character);
    require(service.current_location(1,owner,character)==god2::RecoveredPosition{2,15,17,13,0},
        "First world-entry location unavailable without a saved row");
    rejects([&]{service.prepare(2,owner,character);});
    rejects([&]{service.move(1,other,character,first);});
    rejects([&]{service.move(1,owner,character+1,first);});
    const std::array bad_batch{first[0],Request{30,30,2,255}};
    bool checked_invalid=false;
    rejects([&]{service.move_committed(1,owner,character,bad_batch,
        [&](const auto&){checked_invalid=true;});});
    require(!checked_invalid,"Precommit ran on invalid movement batch");
    require(!db.recovered_characters().load_position(owner,character),"Rejected batch committed location");
    bool checked_valid=false;
    rejects([&]{service.move_committed(1,owner,character,first,
        [&](const god2::RecoveredMovementService::MovePreview& preview){
            checked_valid=true;
            require(preview.area==2 && preview.scene==15 &&
                preview.before_x==17 && preview.before_y==13 &&
                preview.x==18 && preview.y==12 && preview.displaced_steps==1,
                "Precommit movement preview incorrect");
            throw std::runtime_error("Injected precommit failure");
        });});
    require(checked_valid && !db.recovered_characters().load_position(owner,character),
        "Precommit failure changed durable position");
    const auto ack=god2::RecoveredMovement::ack(1);
    const auto committed=service.move_committed(1,owner,character,first);
    require(committed.reply==std::vector<std::uint8_t>(ack.begin(),ack.end()),
            "Failed batch consumed first movement state");
    require(!committed.before && committed.after==*db.recovered_characters().load_position(owner,character) &&
            committed.displaced_steps==1,"Committed movement evidence mismatch");
    require(committed.path==std::vector<Step>{{18,12}},"First committed path missing");
    require(service.current_location(1,owner,character)==committed.after,
        "Committed location not reflected in bound session");
    rejects([&]{service.move(1,owner,character,first);});
    for(unsigned step=2;step<83;++step) {
        const auto index=static_cast<std::uint8_t>(step%40);
        const std::array request{Request{static_cast<std::uint16_t>(step&1?18:17),
            static_cast<std::uint16_t>(step&1?12:13),index,static_cast<std::uint8_t>(step)}};
        const auto result=service.move(1,owner,character,request);
        const auto expected=god2::RecoveredMovement::ack(index);
        require(result==std::vector<std::uint8_t>(expected.begin(),expected.end()),"Ring wrap ACK mismatch");
    }
    service.remove(2); // A refused second session cannot evict the first.
    rejects([&]{service.prepare(2,owner,character);});
    service.remove(1);
    require(!service.character_active(owner,character),"Removed native lease still active");
    const auto saved=db.recovered_characters().load_position(owner,character);
    require(saved && saved->x==17 && saved->y==13 && saved->revision==82,"Committed position or revision mismatch");
    service.prepare(2,owner,character);
    service.bind(2,owner,character);
    const auto reconnected=service.move_committed(2,owner,character,first);
    require(reconnected.reply.size()==5,"Reconnect did not reset connection ring index");
    require(reconnected.before==saved && reconnected.after.revision==83 &&
            reconnected.displaced_steps==1,"Reconnect location evidence lost saved baseline");
    const std::array stationary{Request{18,12,2,0}};
    const auto idle=service.move_committed(2,owner,character,stationary);
    require(idle.displaced_steps==0 && idle.before==reconnected.after &&
            idle.after.x==18 && idle.after.y==12,"Stationary input counted as displacement");
    require(idle.path.empty(),"Stationary input published a remote step");
    const std::array round_trip{Request{17,13,3,0},Request{17,13,4,0},Request{18,12,5,0}};
    const auto walked=service.move_committed(2,owner,character,round_trip);
    require(walked.before==idle.after && walked.after.revision==idle.after.revision+1 &&
            walked.displaced_steps==2 && walked.reply.size()==15 &&
            walked.after==*db.recovered_characters().load_position(owner,character),
            "Batch movement lost real steps or committed multiple revisions");
    require(walked.path==std::vector<Step>{{17,13},{18,12}} &&
            walked.path.size()==walked.displaced_steps,
            "Committed path lost round trip ordering or retained stationary input");
    service.resume_after_battle(2,owner,character);
    const auto reset_move=service.move_committed(2,owner,character,first);
    require(reset_move.before==walked.after && reset_move.displaced_steps==0 &&
            reset_move.reply==std::vector<std::uint8_t>(ack.begin(),ack.end()),
            "Battle return did not reset ring while retaining position");
    ObservedPositions observed(db.recovered_characters());
    god2::RecoveredMovementService reentrant(observed,
        std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/indoor-2-15.json");
    reentrant.prepare(99,owner,character);reentrant.bind(99,owner,character);
    bool replaced=false;
    observed.read=[&]{reentrant.remove(99);
        try{reentrant.prepare(99,owner,character);replaced=true;}catch(const std::exception&){}
    };
    rejects([&]{reentrant.resume_after_battle(99,owner,character);});
    require(!replaced&&!reentrant.current_world_location(99,owner,character),
        "SQL return observer recreated or retained an erased movement owner");
    observed.read={};reentrant.prepare(99,owner,character);reentrant.bind(99,owner,character);
    observed.read=[&]{reentrant.remove(99);};
    require(!reentrant.current_location(99,owner,character),
        "Read-only position observation retained a node erased by SQL observer");
    observed.read={};reentrant.prepare(99,owner,character);reentrant.bind(99,owner,character);
    require(reentrant.current_location(99,owner,character)==reset_move.after,
        "Rejected observer must release the fence for a distinct subsequent owner");
    reentrant.remove(99);
    service.remove(2);
    const auto restored=service.prepare(3,owner,character);
    require(restored==god2::RecoveredWorldEntry::wire(character,
        db.recovered_characters().list_for_account(owner).front().profile,18,12),"World frame did not restore persisted position");
    service.bind(3,owner,character);
    rejects([&]{service.resume_after_battle(3,other,character);});
    const auto battle_return_before=db.recovered_characters().load_position(owner,character);
    service.resume_after_battle(3,owner,character);
    require(db.recovered_characters().load_position(owner,character)==battle_return_before,"Battle return changed saved location");
    const auto prior=db.recovered_characters().load_position(owner,character);
    require(service.current_world_location(3,owner,character)==prior,
        "Pure world snapshot differs from settled saved baseline");
    db.recovered_characters().commit_position(owner,character,prior,2,15,17,13);
    require(!service.current_location(3,owner,character),
        "Externally changed position retained bound authority");
    require(service.current_world_location(3,owner,character)==prior&&
        !service.current_world_location(3,other,character),
        "Pure world snapshot must remain local evidence, not adopt external SQL or another owner");
    rejects([&]{service.resume_after_battle(3,owner,character);});
    rejects([&]{service.move_committed(3,owner,character,first);});
    service.remove(3);
    require(!service.current_world_location(3,owner,character),"Removed pure world owner remained visible");
    service.prepare(4,owner,character);
    require(!service.current_world_location(4,owner,character),"Unbound pure world preparation became ready");
    db.recovered_characters().commit_position(owner,character,
        db.recovered_characters().load_position(owner,character),2,15,18,12);
    rejects([&]{service.bind(4,owner,character);});
    service.remove(4);
    const auto unsupported=db.recovered_characters().commit_position(owner,character,
        db.recovered_characters().load_position(owner,character),2,99,18,12);
    rejects([&]{service.prepare(5,owner,character);});
    require(db.recovered_characters().load_position(owner,character)==unsupported,
            "Unavailable saved scene was silently reset");
    const auto blocked=db.recovered_characters().commit_position(owner,character,unsupported,2,15,0,0);
    rejects([&]{service.prepare(5,owner,character);});
    require(db.recovered_characters().load_position(owner,character)==blocked,
            "Blocked saved position was silently reset");
    require(db.characters().list_for_account(owner).empty(),"Recovered movement touched mock characters");
    require(db.recovered_characters().list_for_account(owner).front().profile[0]=='A',"Movement mutated profile");

    const auto town_path=std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/town-2-4.json";
    god2::RecoveredTownNavigation town_grid(town_path);
    std::uint16_t tx=0,ty=0;
    bool found=false;
    for(int y=42;y<84 && !found;++y) for(int x=42;x<83 && !found;++x) {
        const auto a=town_grid.cell(3,3,x,y),b=town_grid.cell(3,3,x+1,y);
        if(a && b && *a!=0 && *b!=0) {
            tx=static_cast<std::uint16_t>(x);ty=static_cast<std::uint16_t>(y);found=true;
        }
    }
    require(found,"Town test requires two adjacent qualified static cells");
    using Town=god2::RecoveredMovementService::TownDiagnostic;
    rejects([&]{god2::RecoveredMovementService bad(db.recovered_characters(),Town{town_path,{0,0},tx,ty});});
    rejects([&]{god2::RecoveredMovementService bad(db.recovered_characters(),Town{town_path,{3,3},0,0});});
    god2::RecoveredMovementService town(db.recovered_characters(),Town{town_path,{3,3},tx,ty});
    // Existing indoor saves must never be silently teleported by a lab configuration.
    rejects([&]{town.prepare(10,owner,character);});
    require(db.recovered_characters().load_position(owner,character)==blocked,"Town reset indoor save");
    create.payload[0]='T';
    const auto town_character=characters.create(other,create);
    const auto town_profile=db.recovered_characters().list_for_account(other).front().profile;
    require(town.prepare(11,other,town_character)==god2::RecoveredWorldEntry::wire(
        town_character,town_profile,tx,ty,2,4,0),"Town entry scene/kind mismatch");
    town.bind(11,other,town_character);
    const std::array town_step{Request{static_cast<std::uint16_t>(tx+1),ty,1,0}};
    const std::array invalid_town_batch{town_step[0],Request{0,0,2,0}};
    rejects([&]{town.move_committed(11,other,town_character,invalid_town_batch);});
    require(!db.recovered_characters().load_position(other,town_character),"Bad town batch persisted");
    const auto town_move=town.move_committed(11,other,town_character,town_step);
    require(town_move.after.area==2 && town_move.after.scene==4 && town_move.after.x==tx+1 &&
            town_move.after.y==ty && town_move.displaced_steps==1,"Town commit scene/position mismatch");
    town.remove(11);
    require(town.prepare(12,other,town_character)==god2::RecoveredWorldEntry::wire(
        town_character,town_profile,static_cast<std::uint16_t>(tx+1),ty,2,4,0),"Town reconnect lost position");
    town.bind(12,other,town_character);
    const std::array town_return{Request{tx,ty,1,0}};
    const auto returned=town.move_committed(12,other,town_character,town_return);
    require(returned.before==town_move.after && returned.after.revision==town_move.after.revision+1,
            "Town reconnect did not preserve durable baseline");
    rejects([&]{service.prepare(13,other,town_character);});
    // Extend only the diagnostic authority to source-agreeing cells. Conflicts
    // remain unknown; this is not a recovered client streaming policy.
    rejects([&]{god2::RecoveredMovementService bad(db.recovered_characters(),Town{town_path,{3,3},80,35,true});});
    std::uint16_t gx=0,gy=0;
    found=false;
    for(int y=63;y<84 && !found;++y) for(int x=105;x<125 && !found;++x) {
        const auto a=town_grid.consistent_cell(x,y),b=town_grid.consistent_cell(x+1,y);
        if(a && b && *a!=0 && *b!=0) {gx=static_cast<std::uint16_t>(x);gy=static_cast<std::uint16_t>(y);found=true;}
    }
    require(found,"Need agreed cells beyond fixed window");
    rejects([&]{god2::RecoveredMovementService bad(db.recovered_characters(),Town{town_path,{3,3},gx,gy});});
    god2::RecoveredMovementService global(db.recovered_characters(),Town{town_path,{3,3},gx,gy,true});
    create.payload[0]='G';const auto global_character=characters.create(other,create);
    global.prepare(20,other,global_character);global.bind(20,other,global_character);
    const std::array global_step{Request{static_cast<std::uint16_t>(gx+1),gy,1,0}};
    const auto global_move=global.move_committed(20,other,global_character,global_step);
    require(global_move.after.scene==4 && global_move.after.x==gx+1,"Cross-window diagnostic commit mismatch");
    rejects([&]{global.finish_town_transfer(20,other,global_character);});
    rejects([&]{global.begin_town_transfer(20,owner,global_character,global_move.after,gx,gy);});
    rejects([&]{global.begin_town_transfer(20,other,global_character,global_move.after,0,0);});
    rejects([&]{global.begin_town_transfer(20,other,global_character,global_move.after,0x4000,gy);});
    const auto transfer=global.begin_town_transfer(20,other,global_character,global_move.after,gx,gy);
    const auto transfer_plain=god2::RecoveredWorldFrame::decode(transfer);
    require(transfer.size()==12 && transfer_plain && transfer_plain->size()==9 && (*transfer_plain)[0]==0x61,
            "Town transfer frame mismatch");
    const auto destination=*db.recovered_characters().load_position(other,global_character);
    require(destination.x==gx && destination.y==gy && destination.revision==global_move.after.revision+1,
            "Town transfer did not persist destination");
    rejects([&]{global.move(20,other,global_character,global_step);});
    rejects([&]{global.resume_after_battle(20,other,global_character);});
    rejects([&]{global.begin_town_transfer(20,other,global_character,destination,gx,gy);});
    rejects([&]{global.finish_town_transfer(20,owner,global_character);});
    global.finish_town_transfer(20,other,global_character);
    rejects([&]{global.finish_town_transfer(20,other,global_character);});
    const auto after_transfer=global.move_committed(20,other,global_character,global_step);
    require(after_transfer.before==destination && after_transfer.after.x==gx+1,
            "Post-transfer movement used old coordinates or ring");
    global.begin_town_transfer(20,other,global_character,after_transfer.after,gx,gy);
    global.remove(20); // Connection lost after commit, before its scene notification.
    require(global.prepare(21,other,global_character)==god2::RecoveredWorldEntry::wire(
        global_character,db.recovered_characters().list_for_account(other).back().profile,gx,gy,2,4,0),
        "Disconnected transfer did not restore committed target");
    global.bind(21,other,global_character);
    global.move(21,other,global_character,global_step);

    // CUSTOM-0024: two characters share immutable navigation, never mutable scene state.
    const auto dual_owner=db.accounts().create("dual-map-owner","test-hash").id;
    create.payload[0]='D';const auto indoor_character=characters.create(dual_owner,create);
    create.payload[0]='E';const auto outdoor_character=characters.create(dual_owner,create);
    const Town dual_maps{town_path,{3,3},110,70,true,
        std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/indoor-2-15.json"};
    god2::RecoveredMovementService dual(db.recovered_characters(),dual_maps);
    const auto initial_owner=db.accounts().create("initial-map-owner","test-hash").id;
    create.payload[0]='I';const auto initial_character=characters.create(initial_owner,create);
    dual.prepare(35,initial_owner,initial_character);dual.bind(35,initial_owner,initial_character);
    require(!db.recovered_characters().load_position(initial_owner,initial_character),
        "Fresh town character unexpectedly has a save");
    rejects([&]{dual.begin_initial_indoor_transfer(35,other,initial_character,17,13);});
    rejects([&]{dual.begin_initial_indoor_transfer(35,initial_owner,initial_character,0,0);});
    require(!db.recovered_characters().load_position(initial_owner,initial_character),
        "Rejected initial transfer changed position");
    const auto initial_crossing=dual.begin_initial_indoor_transfer(35,initial_owner,initial_character,17,13);
    require(god2::RecoveredWorldFrame::decode(initial_crossing)==
        std::optional<std::vector<std::uint8_t>>({0x61,0xc2,3,0,0,0x46,0,0x1a,0}),
        "Initial crossing packet disagrees with native transport evidence");
    require(db.recovered_characters().load_position(initial_owner,initial_character)==
        god2::RecoveredPosition{2,15,17,13,1},
        "Initial transfer failed to create its first durable position");
    rejects([&]{dual.begin_initial_indoor_transfer(35,initial_owner,initial_character,17,13);});
    dual.finish_town_transfer(35,initial_owner,initial_character);
    dual.remove(35);
    dual.prepare(30,dual_owner,indoor_character);dual.bind(30,dual_owner,indoor_character);
    dual.prepare(31,dual_owner,outdoor_character);dual.bind(31,dual_owner,outdoor_character);
    const std::array at_origin{Request{110,70,1,0}};
    const auto indoor_origin=dual.move_committed(30,dual_owner,indoor_character,at_origin).after;
    const auto outdoor_origin=dual.move_committed(31,dual_owner,outdoor_character,at_origin).after;
    rejects([&]{town.begin_indoor_transfer(12,other,town_character,returned.after,17,13);});
    rejects([&]{dual.begin_indoor_transfer(30,other,indoor_character,indoor_origin,17,13);});
    rejects([&]{dual.begin_indoor_transfer(30,dual_owner,indoor_character,indoor_origin,0,0);});
    const auto crossing=dual.begin_indoor_transfer(30,dual_owner,indoor_character,indoor_origin,17,13);
    const auto crossing_plain=god2::RecoveredWorldFrame::decode(crossing);
    require(crossing_plain && *crossing_plain==std::vector<std::uint8_t>({0x61,0xc2,3,0,0,0x46,0,0x1a,0}),
            "Cross-map packet disagrees with native transport evidence");
    require(db.recovered_characters().load_position(dual_owner,outdoor_character)==outdoor_origin,
            "One character transfer changed another save");
    rejects([&]{dual.prepare(32,dual_owner,indoor_character);});
    rejects([&]{dual.move(30,dual_owner,indoor_character,first);});
    rejects([&]{dual.finish_town_transfer(30,dual_owner,outdoor_character);});
    const std::array outdoor_step{Request{111,70,2,0}};
    const auto unaffected=dual.move_committed(31,dual_owner,outdoor_character,outdoor_step);
    require(unaffected.after.scene==4 && unaffected.after.x==111,"Pending crossing changed other character navigation/ring");
    dual.finish_town_transfer(30,dual_owner,indoor_character);
    rejects([&]{dual.move(30,dual_owner,indoor_character,outdoor_step);});
    const auto indoor_move=dual.move_committed(30,dual_owner,indoor_character,first);
    require(indoor_move.after.scene==15 && indoor_move.after.x==18 && indoor_move.after.y==12,
            "Destination movement committed default town scene");
    rejects([&]{dual.begin_town_transfer(30,dual_owner,indoor_character,indoor_move.after,110,70);});
    const std::array outdoor_back{Request{110,70,3,0}};
    const auto outdoor_saved=dual.move_committed(31,dual_owner,outdoor_character,outdoor_back).after;
    require(outdoor_saved.scene==4,"Completed crossing changed another binding");
    dual.remove(30);
    const auto profiles=db.recovered_characters().list_for_account(dual_owner);
    require(dual.prepare(32,dual_owner,indoor_character)==god2::RecoveredWorldEntry::wire(
        indoor_character,profiles.front().profile,18,12,2,15,2),"Cross-map reconnect lost scene or kind");
    dual.bind(32,dual_owner,indoor_character);
    rejects([&]{town.prepare(33,dual_owner,indoor_character);}); // Unregistered map stays rejected.
    dual.begin_indoor_transfer(31,dual_owner,outdoor_character,outdoor_saved,17,13);
    dual.remove(31); // Commit survives a missing context receipt.
    god2::RecoveredMovementService reopened(db.recovered_characters(),dual_maps);
    require(reopened.prepare(34,dual_owner,outdoor_character)==god2::RecoveredWorldEntry::wire(
        outdoor_character,profiles.back().profile,17,13,2,15,2),"Fresh service lost pending cross-map save");
    reopened.bind(34,dual_owner,outdoor_character);
    require(reopened.move_committed(34,dual_owner,outdoor_character,first).after.scene==15,
            "Fresh service used default navigation instead of saved scene");

    const auto conflict_owner=db.accounts().create("map-conflict-owner","test-hash").id;
    create.payload[0]='F';const auto conflict_character=characters.create(conflict_owner,create);
    dual.prepare(40,conflict_owner,conflict_character);dual.bind(40,conflict_owner,conflict_character);
    const auto conflict_origin=dual.move_committed(40,conflict_owner,conflict_character,at_origin).after;
    const auto external=db.recovered_characters().commit_position(
        conflict_owner,conflict_character,conflict_origin,2,4,111,70);
    rejects([&]{dual.begin_indoor_transfer(40,conflict_owner,conflict_character,conflict_origin,17,13);});
    require(db.recovered_characters().load_position(conflict_owner,conflict_character)==external,
            "Stale transfer overwrote newer position");
    rejects([&]{dual.finish_town_transfer(40,conflict_owner,conflict_character);});
    dual.remove(40);
    dual.prepare(41,conflict_owner,conflict_character);dual.bind(41,conflict_owner,conflict_character);
    dual.begin_indoor_transfer(41,conflict_owner,conflict_character,external,17,13);
    const auto committed_target=db.recovered_characters().load_position(conflict_owner,conflict_character);
    const auto newer_target=db.recovered_characters().commit_position(
        conflict_owner,conflict_character,committed_target,2,15,18,12);
    rejects([&]{dual.finish_town_transfer(41,conflict_owner,conflict_character);});
    rejects([&]{dual.move(41,conflict_owner,conflict_character,first);});
    require(db.recovered_characters().load_position(conflict_owner,conflict_character)==newer_target,
            "Stale transfer receipt or movement changed newer save");
    dual.remove(41);
    dual.prepare(42,conflict_owner,conflict_character);dual.bind(42,conflict_owner,conflict_character);
    const auto resumed=dual.move_committed(42,conflict_owner,conflict_character,first);
    require(resumed.before==newer_target && resumed.displaced_steps==0 && resumed.after.scene==15,
            "Reconnect after rejected receipt failed to restore authoritative save");
    const auto untouched_indoor=db.recovered_characters().load_position(dual_owner,outdoor_character);
    rejects([&]{dual.begin_outdoor_return(42,other,conflict_character,resumed.after,110,70);});
    rejects([&]{dual.begin_outdoor_return(42,conflict_owner,conflict_character,resumed.after,0,0);});
    const auto return_wire=dual.begin_outdoor_return(42,conflict_owner,conflict_character,resumed.after,110,70);
    const auto return_plain=god2::RecoveredWorldFrame::decode(return_wire);
    require(return_plain && *return_plain==std::vector<std::uint8_t>({0x61,2,1,0,0,0xb8,1,0x8c,0}),
            "Return frame set same-scene reuse bit or wrong destination");
    const auto town_returned=db.recovered_characters().load_position(conflict_owner,conflict_character);
    require(town_returned && town_returned->scene==4 && town_returned->x==110 &&
            town_returned->y==70 && town_returned->revision==resumed.after.revision+1,
            "Return did not persist town destination");
    rejects([&]{dual.move(42,conflict_owner,conflict_character,first);});
    dual.finish_town_transfer(42,conflict_owner,conflict_character);
    rejects([&]{dual.move(42,conflict_owner,conflict_character,first);});
    const std::array returned_step{Request{111,70,1,0}};
    const auto returned_move=dual.move_committed(42,conflict_owner,conflict_character,returned_step);
    require(returned_move.after.scene==4 && returned_move.before==town_returned,"Return retained indoor navigation or ring");
    rejects([&]{dual.begin_outdoor_return(42,conflict_owner,conflict_character,returned_move.after,110,70);});
    dual.begin_indoor_transfer(42,conflict_owner,conflict_character,returned_move.after,17,13);
    dual.finish_town_transfer(42,conflict_owner,conflict_character);
    const auto indoor_again=*db.recovered_characters().load_position(conflict_owner,conflict_character);
    dual.begin_outdoor_return(42,conflict_owner,conflict_character,indoor_again,110,70);
    dual.remove(42); // Return save must survive losing the scene context receipt.
    god2::RecoveredMovementService return_reopened(db.recovered_characters(),dual_maps);
    require(return_reopened.prepare(43,conflict_owner,conflict_character)==god2::RecoveredWorldEntry::wire(
        conflict_character,db.recovered_characters().list_for_account(conflict_owner).front().profile,110,70,2,4,0),
        "Return reconnect lost town destination");
    return_reopened.bind(43,conflict_owner,conflict_character);
    require(return_reopened.move_committed(43,conflict_owner,conflict_character,returned_step).after.scene==4,
            "Return reconnect could not move in town");
    require(db.recovered_characters().load_position(dual_owner,outdoor_character)==untouched_indoor,
            "Return changed another character's indoor save");

    // Scene0 is available only when the pinned static navigation is explicitly loaded.
    // This exercises the packet, durable scene/kind, reconnect and movement gates;
    // no original-client portal trigger is asserted by this unit test.
    const Town island_maps{town_path,{3,3},110,70,true,
        std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/indoor-2-15.json",
        std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas/island01-entry-2-0.json"};
    god2::RecoveredMovementService island(db.recovered_characters(),island_maps);
    const auto island_owner=db.accounts().create("island-map-owner","test-hash").id;
    create.payload[0]='H';const auto island_character=characters.create(island_owner,create);
    island.prepare(50,island_owner,island_character);island.bind(50,island_owner,island_character);
    const auto island_origin=island.move_committed(50,island_owner,island_character,at_origin).after;
    rejects([&]{dual.begin_island_transfer(30,dual_owner,indoor_character,indoor_origin,477,209);});
    rejects([&]{island.begin_island_transfer(50,island_owner,island_character,island_origin,478,209);});
    const auto island_wire=island.begin_island_transfer(50,island_owner,island_character,island_origin,477,209);
    const auto island_plain=god2::RecoveredWorldFrame::decode(island_wire);
    const auto island_packed=1u|(477u<<2)|(209u<<17);
    require(island_plain && island_plain->size()==9 && (*island_plain)[0]==0x61 &&
            (*island_plain)[1]==2 && (*island_plain)[2]==0 &&
            (*island_plain)[5]==static_cast<std::uint8_t>(island_packed) &&
            (*island_plain)[6]==static_cast<std::uint8_t>(island_packed>>8) &&
            (*island_plain)[7]==static_cast<std::uint8_t>(island_packed>>16) &&
            (*island_plain)[8]==static_cast<std::uint8_t>(island_packed>>24),
            "Scene0 transfer frame selector/kind/coordinate mismatch");
    rejects([&]{island.move(50,island_owner,island_character,
                            std::array{Request{477,210,1,0}});});
    island.finish_town_transfer(50,island_owner,island_character);
    rejects([&]{island.move(50,island_owner,island_character,
                            std::array{Request{478,209,1,0}});});
    const auto island_saved=island.move_committed(50,island_owner,island_character,
                            std::array{Request{477,210,1,0}}).after;
    require(island_saved.scene==0 && island_saved.x==477 && island_saved.y==210,
            "Scene0 movement did not persist on the island map");
    island.remove(50);
    god2::RecoveredMovementService island_reopened(db.recovered_characters(),island_maps);
    require(island_reopened.prepare(51,island_owner,island_character)==god2::RecoveredWorldEntry::wire(
        island_character,db.recovered_characters().list_for_account(island_owner).front().profile,
        477,210,2,0,1),"Scene0 reconnect lost kind1 or saved coordinates");
    rejects([&]{dual.prepare(52,island_owner,island_character);});
    island_reopened.bind(51,island_owner,island_character);
    rejects([&]{island_reopened.begin_island_return(51,island_owner,island_character,
        island_saved,0,0);});
    const auto island_return=island_reopened.begin_island_return(51,island_owner,island_character,
        island_saved,56,76);
    const auto island_return_plain=god2::RecoveredWorldFrame::decode(island_return);
    const auto return_packed=(56u<<2)|(76u<<17);
    require(island_return_plain && island_return_plain->size()==9 &&
            (*island_return_plain)[0]==0x61 && (*island_return_plain)[1]==2 &&
            (*island_return_plain)[2]==1 &&
            (*island_return_plain)[5]==static_cast<std::uint8_t>(return_packed) &&
            (*island_return_plain)[6]==static_cast<std::uint8_t>(return_packed>>8) &&
            (*island_return_plain)[7]==static_cast<std::uint8_t>(return_packed>>16) &&
            (*island_return_plain)[8]==static_cast<std::uint8_t>(return_packed>>24),
            "Island return frame selector/kind/coordinate mismatch");
    require(db.recovered_characters().load_position(island_owner,island_character)==
            god2::RecoveredPosition{2,4,56,76,island_saved.revision+1},
            "Island return did not persist town arrival");
    rejects([&]{island_reopened.move(51,island_owner,island_character,
                            std::array{Request{56,77,1,0}});});
    island_reopened.finish_town_transfer(51,island_owner,island_character);
    require(island_reopened.move_committed(51,island_owner,island_character,
                            std::array{Request{56,77,1,0}}).after.scene==4,
            "Island return did not restore town movement");
}
