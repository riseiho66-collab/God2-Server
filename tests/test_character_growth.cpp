#include "scripting/LuaEngine.h"
#include "handlers/RecoveredCharacterGrowth.h"
#include "handlers/OwnedAttributeAllocation.h"
#include "protocol/RecoveredWorldRecords.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "protocol/DiagnosticBattleParticipants.h"
#include <iostream>
#include <stdexcept>
namespace {
void require(bool ok) { if(!ok) throw std::runtime_error("Character growth invariant failed"); }
template<class F> void rejects(F f) {try {f();} catch(const std::exception&) {return;} throw std::runtime_error("Invalid growth accepted");}
}
int main() {try {
    god2::LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);require(lua.initialize());
    constexpr std::array<std::array<std::uint16_t,4>,4> rules{{{2,3,0,1},{1,0,3,2},{2,0,2,2},{1,1,1,3}}};
    unsigned cases=0;
    for(unsigned cls=1;cls<=4;++cls) for(unsigned level=1;level<=255;++level) {
        god2::CharacterGrowthInput input{static_cast<god2::CharacterGrowthClass>(cls),1,
            static_cast<std::uint16_t>(level),{28,32,20,20},0};
        auto result=lua.character_growth(input);
        for(unsigned i=0;i<4;++i) require(result.attributes[i]==input.attributes[i]+rules[cls-1][i]*(level-1));
        require(result.unspent_points==4*(level-1));
        // Baseline level carries prior growth: replaying no level delta grants nothing.
        require(lua.character_growth({input.profession,input.next_level,input.next_level,result.attributes,
                                      result.unspent_points})==result);
        if(level>1) {
            auto middle=lua.character_growth({input.profession,1,static_cast<std::uint16_t>(level-1),input.attributes,0});
            require(lua.character_growth({input.profession,static_cast<std::uint16_t>(level-1),input.next_level,
                                          middle.attributes,middle.unspent_points})==result);
        }
        ++cases;
    }
    rejects([&]{lua.character_growth({god2::CharacterGrowthClass::Swordsman,0,1,{0,0,0,0},0});});
    rejects([&]{lua.character_growth({god2::CharacterGrowthClass::Swordsman,2,1,{0,0,0,0},0});});
    rejects([&]{lua.character_growth({god2::CharacterGrowthClass::Swordsman,1,256,{0,0,0,0},0});});
    rejects([&]{lua.character_growth({static_cast<god2::CharacterGrowthClass>(0),1,2,{0,0,0,0},0});});
    rejects([&]{lua.character_growth({god2::CharacterGrowthClass::Swordsman,1,2,{65535,0,0,0},0});});
    rejects([&]{lua.character_growth({god2::CharacterGrowthClass::Swordsman,1,2,{0,0,0,0},32766});});
    require(lua.reload_all());require(lua.character_growth({god2::CharacterGrowthClass::Taoist,1,2,{0,0,0,0},0})==
        god2::CharacterGrowthResult{{1,0,3,2},4});
    constexpr std::array mapped{god2::CharacterGrowthClass::Swordsman,god2::CharacterGrowthClass::Taoist,
        god2::CharacterGrowthClass::Warlock,god2::CharacterGrowthClass::Pharmacist};
    for(unsigned wire=1;wire<=8;++wire) {
        std::array<std::uint8_t,40> profile{};profile[0]='A';profile[29]=static_cast<std::uint8_t>(wire);
        profile[31]=1;profile[33]=profile[38]=static_cast<std::uint8_t>((wire-1)&1);
        const auto cls=god2::recovered_growth_class(profile);require(cls==mapped[(wire-1)/2]);
        const auto seed=god2::RecoveredRoleLevel::parse(god2::diagnostic_role_level_seed());require(seed.has_value());
        const auto grown=god2::project_character_growth(lua,cls,*seed,2,1250);
        const auto previous=god2::RecoveredRoleLevel::encode(*seed),logical=god2::RecoveredRoleLevel::encode(grown);
        for(unsigned at=0;at<logical.size();++at)
            if(at!=1 && !(at>=3 && at<=14))require(logical[at]==previous[at]);
        const auto rule=rules[static_cast<unsigned>(cls)-1];
        for(unsigned i=0;i<4;++i)require(grown.base_stats()[i]==seed->base_stats()[i]+rule[i]);
        require(grown.state_word()==seed->state_word()+4);
        require(god2::RecoveredRoleLevel::encode(god2::project_character_growth(lua,cls,grown,2,1250))==logical);
        auto bad=profile;bad[33]^=1;rejects([&]{god2::recovered_growth_class(bad);});
        bad=profile;bad[29]=0;rejects([&]{god2::recovered_growth_class(bad);});

        sqlite3* raw=nullptr;require(sqlite3_open(":memory:",&raw)==SQLITE_OK);
        std::unique_ptr<sqlite3,decltype(&sqlite3_close)> db(raw,&sqlite3_close);
        god2::sqlite_detail::execute(db.get(),"PRAGMA foreign_keys=ON");
        god2::SqliteMigrationManager(db.get(),god2::default_sqlite_migrations()).migrate();
        god2::sqlite_detail::execute(db.get(),"INSERT INTO accounts(id,username,password_hash) VALUES(1,'growth','test_hash')");
        god2::SqliteRecoveredCharacterRepository repo(db.get());const auto character=repo.create(1,profile);
        auto resources=repo.commit_resources(1,character.id,{}, {76,120,26,80,0,"CUSTOM-0012"});
        const auto baseline=repo.commit_role_resources(1,character.id,{},resources,{previous,0,"CUSTOM-0013"},resources);
        resources=baseline.resources;
        const auto battle=repo.reserve_battle(1,character.id,resources);
        const god2::BattleProgressionCommit progression{{},baseline.role,{logical,0,"CUSTOM-0013"}};
        const auto result=repo.settle_battle(1,character.id,battle,resources,resources,true,250,progression);
        require(result.role && result.role->logical==logical && result.total_experience==250);
        const auto saved=repo.load_role(1,character.id);
        const auto retry=repo.settle_battle(1,character.id,battle,resources,resources,true,250,progression);
        require(retry.role==result.role && repo.load_role(1,character.id)==saved);
        require(repo.load_experience(1,character.id)->total==250);
        auto changed=progression;changed.next_role.logical[3]^=1;
        rejects([&]{repo.settle_battle(1,character.id,battle,resources,resources,true,250,changed);});
        require(repo.load_role(1,character.id)==saved);
        // A late resource write failure must roll back the preceding role update.
        const auto allocation_resources=repo.load_resources(1,character.id);
        god2::sqlite_detail::execute(db.get(),"CREATE TEMP TRIGGER reject_allocation BEFORE UPDATE ON character_resources BEGIN SELECT RAISE(ABORT,'allocation resource failure'); END");
        rejects([&]{god2::allocate_owned_attribute(repo,lua,1,character.id,{2});});
        require(repo.load_role(1,character.id)==saved && repo.load_resources(1,character.id)==allocation_resources);
        god2::sqlite_detail::execute(db.get(),"DROP TRIGGER reject_allocation");
        const std::array<god2::RecoveredAttributeAllocation::Request,5> excessive{{{2},{2},{1},{4},{3}}};
        const auto overspend=god2::allocate_owned_attributes(repo,lua,1,character.id,excessive);
        require(repo.load_role(1,character.id)==saved && repo.load_resources(1,character.id)==allocation_resources);
        require(god2::RecoveredWorldFrame::decode(overspend)==std::optional<std::vector<std::uint8_t>>{
            std::vector<std::uint8_t>(saved->logical.begin(),saved->logical.end())});
        const std::array<god2::RecoveredAttributeAllocation::Request,3> invalid_batch{{{2},{0},{1}}};
        rejects([&]{god2::allocate_owned_attributes(repo,lua,1,character.id,invalid_batch);});
        require(repo.load_role(1,character.id)==saved && repo.load_resources(1,character.id)==allocation_resources);
        auto allocated=grown.base_stats();
        constexpr std::array<unsigned,4> indices{2,0,1,3};
        // Identical native requests are separate one-point actions; no nonce exists.
        const std::array<unsigned,4> sequence=wire&1 ? std::array<unsigned,4>{2,2,1,4} : std::array<unsigned,4>{2,3,1,4};
        unsigned spent=0;
        for(const auto selector:sequence) {
            const auto frame=god2::allocate_owned_attribute(repo,lua,1,character.id,{static_cast<std::uint8_t>(selector)});
            const auto logical_response=god2::RecoveredWorldFrame::decode(frame);require(logical_response.has_value());
            const auto snapshot=god2::RecoveredRoleLevel::parse(*logical_response);require(snapshot.has_value());
            allocated[indices[selector-1]]++;spent++;
            require(snapshot->base_stats()==allocated && snapshot->state_word()==4-spent);
            require(snapshot->level()==2 && snapshot->progress_display()==1250 && snapshot->max_hp()==120 && snapshot->max_mp()==80);
            require(repo.load_role(1,character.id)->logical==god2::RecoveredRoleLevel::encode(*snapshot));
            require(repo.load_experience(1,character.id)->total==250);
        }
        const auto exhausted=repo.load_role(1,character.id);
        const auto unchanged_resources=repo.load_resources(1,character.id);
        const auto refusal=god2::allocate_owned_attribute(repo,lua,1,character.id,{2});
        require(god2::RecoveredWorldFrame::decode(refusal)==std::optional<std::vector<std::uint8_t>>{
            std::vector<std::uint8_t>(exhausted->logical.begin(),exhausted->logical.end())});
        require(repo.load_role(1,character.id)==exhausted && repo.load_resources(1,character.id)==unchanged_resources);
        rejects([&]{god2::allocate_owned_attribute(repo,lua,2,character.id,{2});});
        // Fresh isolated snapshot: one native queued batch must commit all four
        // clicks once, including identical selectors, or roll back all of them.
        const auto restored=repo.commit_role_resources(1,character.id,exhausted,*unchanged_resources,*saved,*unchanged_resources);
        const std::array<god2::RecoveredAttributeAllocation::Request,4> batch{{{2},{2},{1},{4}}};
        god2::sqlite_detail::execute(db.get(),"CREATE TEMP TRIGGER reject_allocation BEFORE UPDATE ON character_resources BEGIN SELECT RAISE(ABORT,'allocation batch failure'); END");
        rejects([&]{god2::allocate_owned_attributes(repo,lua,1,character.id,batch);});
        require(repo.load_role(1,character.id)==restored.role && repo.load_resources(1,character.id)==restored.resources);
        god2::sqlite_detail::execute(db.get(),"DROP TRIGGER reject_allocation");
        const auto response=god2::RecoveredWorldFrame::decode(god2::allocate_owned_attributes(repo,lua,1,character.id,batch));
        require(response.has_value());const auto batched=god2::RecoveredRoleLevel::parse(*response);require(batched.has_value());
        auto expected_batch=grown.base_stats();expected_batch[0]+=2;expected_batch[2]++;expected_batch[3]++;
        require(batched->base_stats()==expected_batch && batched->state_word()==0);
        require(repo.load_role(1,character.id)->revision==restored.role.revision+1 &&
            repo.load_resources(1,character.id)->revision==restored.resources.revision+1);
        require(repo.load_experience(1,character.id)->total==250);
    }
    for(unsigned selector=1;selector<=4;++selector) {
        const std::array<std::uint8_t,4> logical{0x21,static_cast<std::uint8_t>(selector),0x30,0};
        const auto records=god2::RecoveredWorldRecords::decode(logical);
        require(records && records->size()==2 && std::get<god2::RecoveredAttributeAllocation::Request>((*records)[0]).selector==selector);
    }
    for(const auto logical:{std::vector<std::uint8_t>{0x21},std::vector<std::uint8_t>{0x21,0},std::vector<std::uint8_t>{0x21,5},std::vector<std::uint8_t>{0x21,2,0xff}})
        require(!god2::RecoveredWorldRecords::decode(logical));
    rejects([&]{lua.allocate_attribute({0,{1,2,3,4},1});});
    rejects([&]{lua.allocate_attribute({1,{1,2,3,4},0});});
    rejects([&]{lua.allocate_attribute({2,{65535,2,3,4},1});});
    std::cout<<cases<<" growth cases, partition/replay/overflow and reload passed\n";
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}}
