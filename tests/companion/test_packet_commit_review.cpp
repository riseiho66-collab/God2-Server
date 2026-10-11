#include "db/Migration.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteRoleTextRepository.h"
#include "db/SqliteSupport.h"
#include "db/SqliteTeleportGemRepository.h"
#include "handlers/RecoveredMovementService.h"
#include "protocol/RecoveredWorldFrame.h"
#include <iostream>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool condition){++checks;if(!condition)throw std::runtime_error("Packet commit review failed");}
template<class F>void rejects(F callback){bool rejected=false;try{callback();}catch(const std::exception&){rejected=true;}check(rejected);}
void sql(sqlite3* db,const std::string& statement){sqlite_detail::execute(db,statement);}
RecoveredRoleText::Text text(const char* value){RecoveredRoleText::Text out{};std::copy(value,value+std::char_traits<char>::length(value),out.begin());return out;}
struct Fixture {
    sqlite3* db=nullptr;
    static sqlite3* open(){sqlite3* db=nullptr;if(sqlite3_open(":memory:",&db)!=SQLITE_OK)throw std::runtime_error("sqlite open failed");return db;}
    SqliteRecoveredCharacterRepository characters;
    SqliteTeleportGemRepository gems;
    SqliteRoleTextRepository roles;
    Fixture():db(open()),characters(db),gems(db),roles(db){
        sql(db,"PRAGMA foreign_keys=ON");
        for(const auto& migration:default_sqlite_migrations())sql(db,migration.sql);
        sql(db,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'commit-owner','hash'),(2,'commit-other','hash')");
        std::array<std::uint8_t,40> profile{};profile[0]='A';profile[29]=1;profile[31]=1;
        check(characters.create(1,profile).id==1);
        sql(db,"INSERT INTO recovered_positions VALUES(1,2,0,477,210,5)");
        sql(db,"INSERT INTO diagnostic_inventory_slots VALUES(1,12,16055,1,9,'"+
            std::string(SqliteTeleportGemRepository::source_sha256)+"','CUSTOM-0015')");
        RecoveredTeleportGem::Metadata metadata{0xb7,0x3e,8,6};metadata[19]=0xee;
        gems.save_existing(1,1,12,{16055,1,9,SqliteTeleportGemRepository::source_sha256},metadata,
                           "CUSTOM_TEST_NOT_NATIVE","independent commit review");
    }
    ~Fixture(){sqlite3_close(db);}
    static RecoveredMovementService::TownDiagnostic maps(){
        const auto root=std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/world-atlas";
        return {root/"town-2-4.json",{3,3},110,70,true,root/"indoor-2-15.json",root/"island01-entry-2-0.json"};
    }
};
void role_prepare(){
    Fixture f;bool called=false;
    rejects([&]{f.roles.save(1,1,{},text("first"),950,[&](const auto& next){
        called=true;check(next.revision==1 && next.utf8=="first" && sqlite3_get_autocommit(f.db)==0);
        check(f.roles.load(1,1)==std::optional(next));throw std::runtime_error("peer projection failed");
    });});
    check(called && !f.roles.load(1,1));
    const auto saved=f.roles.save(1,1,{},text("first"),950);
    rejects([&]{f.roles.save(1,1,saved.revision,text("next"),950,[](const auto&){throw std::runtime_error("frame encode failed");});});
    check(f.roles.load(1,1)==std::optional(saved));
    called=false;
    rejects([&]{f.roles.save(1,1,0,text("badcas"),950,[&](const auto&){called=true;});});
    rejects([&]{f.roles.save(2,1,saved.revision,text("other"),950,[&](const auto&){called=true;});});
    check(!called && f.roles.load(1,1)==std::optional(saved));
    unsigned preparations=0;
    const auto retried=f.roles.save(1,1,saved.revision,saved.text,950,[&](const auto& next){
        ++preparations;check(sqlite3_get_autocommit(f.db)==0 && next==saved);
    });
    check(preparations==1 && retried==saved);
    rejects([&]{f.roles.save(1,1,saved.revision,saved.text,950,[](const auto&){throw std::runtime_error("retry projection failed");});});
    check(f.roles.load(1,1)==std::optional(saved));
    for(const auto value:{"first","changed"}){
        rejects([&]{f.roles.save(1,1,saved.revision,text(value),950,[&](const auto&){
            sql(f.db,"UPDATE character_role_text SET utf8_text='corrupted' WHERE character_id=1");
        });});
        check(f.roles.load(1,1)==std::optional(saved));
    }
    const auto next=f.roles.save(1,1,saved.revision,text("published"),950,[&](const auto& prepared){
        check(prepared.revision==2 && prepared.utf8=="published");
        check(RecoveredWorldFrame::encode(*RecoveredRoleText::update(prepared.text)).size()>0);
    });
    check(next.revision==2 && f.roles.load(1,1)==std::optional(next));
}
void movement_commit(){
    Fixture f;RecoveredMovementService movement(f.characters,Fixture::maps());
    const auto source=*f.characters.load_position(1,1);
    const auto gem=*f.gems.load(1,1,12);
    rejects([&]{movement.prepare_owned_island_return(7,1,1,source);});
    movement.prepare(7,1,1);
    rejects([&]{movement.prepare_owned_island_return(7,1,1,source);});
    movement.bind(7,1,1);
    rejects([&]{movement.prepare_owned_island_return(7,2,1,source);});
    rejects([&]{movement.prepare_owned_island_return(8,1,1,source);});
    auto stale=source;++stale.revision;
    rejects([&]{movement.prepare_owned_island_return(7,1,1,stale);});
    const auto plan=movement.prepare_owned_island_return(7,1,1,source);
    check(plan.before==source && plan.after==RecoveredPosition{2,4,56,75,6});
    check(plan.logical[0]==0x61 && plan.logical[1]==2 && plan.logical[2]==1);
    const auto packed=(56u<<2)|(75u<<17);
    for(unsigned index=0;index<4;++index)check(plan.logical[5+index]==static_cast<std::uint8_t>(packed>>(8*index)));
    check(f.characters.load_position(1,1)==std::optional(source) && movement.current_location(7,1,1)==std::optional(source));
    rejects([&]{f.gems.prepare_transfer(1,1,gem,source,[&](const auto& next){
        check(next.position_after==plan.after && next.position_before==plan.before);
        check(f.characters.load_position(1,1)==std::optional(plan.after));
        check(!movement.current_location(7,1,1)); // DB candidate is not memory authority before commit.
        throw std::runtime_error("combined projection failed");
    });});
    check(f.gems.load(1,1,12)==std::optional(gem) && f.characters.load_position(1,1)==std::optional(source));
    check(movement.current_location(7,1,1)==std::optional(source));
    // Simulate another writer winning position CAS after planning. Never let
    // the stale plan charge an item or advance in-memory movement authority.
    sql(f.db,"UPDATE recovered_positions SET revision=6 WHERE character_id=1");
    bool prepared=false;
    rejects([&]{f.gems.prepare_transfer(1,1,gem,source,[&](const auto&){prepared=true;});});
    check(!prepared && f.gems.load(1,1,12)==std::optional(gem) && !movement.current_location(7,1,1));
    sql(f.db,"UPDATE recovered_positions SET revision=5 WHERE character_id=1");
    const auto commit=f.gems.prepare_transfer(1,1,gem,source,[&](const auto& result){
        check(result.position_after==plan.after);
        check(RecoveredWorldFrame::encode(plan.logical).size()>0);
    });
    check(sqlite3_get_autocommit(f.db)!=0 && commit.position_after==plan.after);
    movement.commit_owned_island_return(plan,commit.position_after);
    check(!movement.current_location(7,1,1)); // Destination receipt still required.
    rejects([&]{movement.prepare_owned_island_return(7,1,1,source);});
    rejects([&]{movement.finish_town_transfer(7,2,1);});
    movement.finish_town_transfer(7,1,1);
    check(movement.current_location(7,1,1)==std::optional(plan.after));
    check(f.characters.load_position(1,1)==std::optional(plan.after));
    check(RecoveredTeleportGem::displayed_charges(f.gems.load(1,1,12)->metadata20)==2);
    rejects([&]{f.gems.prepare_transfer(1,1,gem,source,[](const auto&){});});
    movement.remove(7);movement.prepare(8,1,1);movement.bind(8,1,1);
    check(movement.current_location(8,1,1)==std::optional(plan.after));
    rejects([&]{movement.prepare_owned_island_return(8,1,1,plan.after);});
}
}
int main(){try{role_prepare();movement_commit();std::cout<<"Packet commit review PASS "<<checks<<" checks\n";return 0;}
    catch(const std::exception& error){std::cerr<<error.what()<<" after "<<checks<<" checks\n";return 1;}}
