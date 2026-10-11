#include "db/SqliteDatabase.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <cstdlib>
#include <iostream>
#include <string>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
}

// Child-process fault injection only; no crash hooks are linked into the server.
int main(int argc, char** argv) {
    try {
        using namespace god2;
        require(argc == 4, "Expected database, action and fault point");
        const std::filesystem::path path(argv[1]);
        const std::string action(argv[2]), point(argv[3]);
        CharacterResources resources{100,120,50,80,2,"CUSTOM-0012"};
        const std::array<BattleActor,2> actors{{
            {0,1,100,120,50,80,31,40,8,10}, {14,0,150,150,0,0,20,25,13,6}}};
        Battle battle(1,actors,123);
        StoredBattleCheckpoint baseline{battle.checkpoint(),2,"CUSTOM-0012/diagnostic-v1"};
        if (action == "init") {
            require(!std::filesystem::exists(path), "Refusing to overwrite database");
            SqliteDatabase db(path); db.initialize(); db.migrate();
            require(db.accounts().create("crash-test","test-hash").id == 1, "Unexpected account");
            auto& repo=static_cast<SqliteRecoveredCharacterRepository&>(db.recovered_characters());
            std::array<std::uint8_t,40> profile{}; profile[0]='C';
            require(repo.create(1,profile).id == 1, "Unexpected character");
            auto initial=resources; initial.revision=0;
            initial=repo.commit_resources(1,1,{},initial);
            require(repo.reserve_battle(1,1,initial)==1, "Unexpected reservation");
            require(repo.commit_checkpoint(1,1,{},initial,battle.checkpoint(),initial,baseline.policy_id)==baseline,
                    "Unexpected checkpoint baseline");
            return 0;
        }
        sqlite3* raw=nullptr;
        require(sqlite3_open_v2(argv[1],&raw,SQLITE_OPEN_READWRITE,nullptr)==SQLITE_OK, "Open failed");
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
        SqliteRecoveredCharacterRepository repo(raw);
        battle.act(1,1,{0,{14},true,1000,100,8,0,150},
            [](const auto& input){return CombatRuleResult{1000,input.mp_cost,false};},
            [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        const auto terminal=battle.checkpoint();
        auto next=resources; next.mp=42;
        if (action == "crash") {
            sqlite3_update_hook(raw, [](void* context,int,const char*,const char* table,sqlite3_int64) {
                if (*static_cast<const std::string*>(context)==table) std::_Exit(73);
            },const_cast<std::string*>(&point));
            if (point=="commit") sqlite3_commit_hook(raw,[](void*) -> int {std::_Exit(74);},nullptr);
            repo.settle_checkpoint(1,1,baseline,resources,terminal,next,true,25);
            if (point=="after_commit") std::_Exit(75);
            throw std::runtime_error("Fault point was not reached");
        }
        require(action=="verify", "Unknown action");
        const bool committed=point=="after_commit";
        auto expected=resources;
        if(committed) {expected.mp=42; ++expected.revision;}
        require(repo.load_resources(1,1)==expected,"Partial resource commit");
        const auto checkpoint=repo.load_checkpoint(1,1,1);
        require(checkpoint && checkpoint->checkpoint==(committed?terminal:baseline.checkpoint),
                "Partial checkpoint commit");
        require(checkpoint->resource_revision==expected.revision,"Checkpoint/resource revision mismatch");
        const auto xp=repo.load_experience(1,1);
        require(committed ? xp && xp->total==25 : !xp,"Partial experience commit");
        require(repo.load_pending_checkpoint(1,1).has_value()!=committed,"Incorrect pending battle");
        const auto count=[&] {
            sqlite_detail::Statement query(raw,"SELECT count(*) FROM battle_settlements");
            require(query.row(),"Missing count"); return query.integer(0);
        };
        require(count()==(committed?1:0),"Partial settlement receipt");
        const auto settled=repo.settle_checkpoint(1,1,baseline,resources,terminal,next,true,25);
        require(settled.total_experience==25 && settled.resources.mp==42 && settled.resources.revision==3,
                "Recovery changed reward or resources");
        require(repo.settle_checkpoint(1,1,baseline,resources,terminal,next,true,25)==settled && count()==1,
                "Recovery retry duplicated settlement");
        sqlite3_close(raw);
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n'; return 1;}
}
