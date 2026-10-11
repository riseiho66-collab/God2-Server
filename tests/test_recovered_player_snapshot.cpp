#include "handlers/RecoveredPlayerSnapshot.h"
#include "protocol/RecoveredRoleVitals.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <iostream>
#include <stdexcept>

using namespace god2;
namespace {
int checks{};
void require(bool condition) {
    ++checks;
    if(!condition) throw std::runtime_error("Saved player snapshot check failed");
}
template<class F> void rejects(F action) {
    bool failed=false;
    try {action();} catch(const std::exception&) {failed=true;}
    require(failed);
}
struct Repository final : RecoveredCharacterRepository {
    std::optional<CharacterResources> resources;
    std::optional<CharacterRoleSnapshot> role;
    unsigned resource_reads{},role_reads{};
    bool change_resources{},change_role{};
    static void owner(std::uint64_t account,std::uint64_t character) {
        if(account!=17 || character!=42) throw std::runtime_error("Wrong owner");
    }
    std::optional<CharacterResources> load_resources(std::uint64_t a,std::uint64_t c) override {
        owner(a,c);
        if(++resource_reads==2 && change_resources && resources) ++resources->revision;
        return resources;
    }
    std::optional<CharacterRoleSnapshot> load_role(std::uint64_t a,std::uint64_t c) override {
        owner(a,c);
        if(++role_reads==2 && change_role && role) ++role->revision;
        return role;
    }
    // Any unexpected read or mutation is a failure: snapshot replay must never
    // derive progress from cumulative XP or seed a new row.
    [[noreturn]] static void unused() { throw std::runtime_error("Unexpected repository operation"); }
    std::optional<CharacterExperience> load_experience(std::uint64_t,std::uint64_t) override {unused();}
    RoleResourceCommit commit_role_resources(std::uint64_t,std::uint64_t,
        const std::optional<CharacterRoleSnapshot>&,const CharacterResources&,
        CharacterRoleSnapshot,CharacterResources) override {unused();}
    BattleSettlement settle_battle(std::uint64_t,std::uint64_t,std::uint64_t,
        const CharacterResources&,CharacterResources,bool,std::uint64_t,
        const std::optional<BattleProgressionCommit>&) override {unused();}
    std::uint64_t reserve_battle(std::uint64_t,std::uint64_t,const CharacterResources&) override {unused();}
    CharacterResources commit_resources(std::uint64_t,std::uint64_t,
        const std::optional<CharacterResources>&,CharacterResources) override {unused();}
    RecoveredCharacter create(std::uint64_t,const std::array<std::uint8_t,40>&) override {unused();}
    std::vector<RecoveredCharacter> list_for_account(std::uint64_t) override {unused();}
    std::optional<RecoveredPosition> load_position(std::uint64_t,std::uint64_t) override {unused();}
    RecoveredPosition commit_position(std::uint64_t,std::uint64_t,
        const std::optional<RecoveredPosition>&,std::uint16_t,std::uint16_t,
        std::uint16_t,std::uint16_t) override {unused();}
};
Repository fixture() {
    Repository result;
    // Deliberately synthetic TEST values; never a character-creation policy.
    result.resources=CharacterResources{73,123,19,91,4,"CUSTOM-0012"};
    CharacterRoleSnapshot role{};
    role.logical.fill(0xa5);role.logical[0]=0x22;role.logical[1]=9;
    for(unsigned n=0;n<4;++n) {
        role.logical[17+n]=static_cast<std::uint8_t>(123u>>(8*n));
        role.logical[21+n]=static_cast<std::uint8_t>(91u>>(8*n));
    }
    role.revision=3;role.design_id="CUSTOM-0013";result.role=role;
    return result;
}
auto load(Repository& repo) {return RecoveredPlayerSnapshot::load_for_world_entry(repo,17,42);}
}
int main() {
    Repository empty;
    require(!load(empty));require(empty.resource_reads==2 && empty.role_reads==2);
    for(const auto ids:{std::pair{0u,42u},std::pair{17u,0u},std::pair{18u,42u},std::pair{17u,43u}})
        rejects([&]{RecoveredPlayerSnapshot::load_for_world_entry(empty,ids.first,ids.second);});
    auto repo=fixture();const auto before_resources=repo.resources;const auto before_role=repo.role;
    const auto snapshot=load(repo);
    require(snapshot && snapshot->resources==before_resources && snapshot->role==before_role);
    require(repo.resources==before_resources && repo.role==before_role);
    const auto& logical=snapshot->logical_before_companion_binding;
    require(logical.size()==42 && logical[0]==0x22 && logical[25]==0x24);
    require(std::equal(before_role->logical.begin(),before_role->logical.end(),logical.begin()));
    const auto vitals=RecoveredRoleVitals::encode(73,19,123,91);
    require(std::equal(vitals.begin(),vitals.end(),logical.begin()+25));
    require(RecoveredWorldFrame::decode(RecoveredWorldFrame::encode(logical))==logical);
    // Resource-only saved characters can restore vitals without invented level,
    // base stats, EXP progress, modifiers, learned skills or companion rows.
    repo=fixture();repo.role.reset();const auto only=load(repo);
    require(only && only->logical_before_companion_binding==std::vector<std::uint8_t>(vitals.begin(),vitals.end()));
    // Dead character and zero maximum MP remain exact saved values.
    repo=fixture();repo.role.reset();repo.resources->hp=0;repo.resources->mp=0;repo.resources->max_mp=0;
    require(load(repo)->logical_before_companion_binding[1]==0);
    for(unsigned problem=0;problem<12;++problem) {
        repo=fixture();
        switch(problem) {
        case 0: repo.resources.reset();break;
        case 1: repo.resources->design_id="NATIVE_VERIFIED";break;
        case 2: repo.resources->revision=0;break;
        case 3: repo.resources->hp=124;break;
        case 4: repo.resources->mp=92;break;
        case 5: repo.resources->max_hp=0;break;
        case 6: repo.role->logical[0]=0x2b;break;
        case 7: repo.role->logical[1]=0;break;
        case 8: repo.role->logical[17]=124;break;
        case 9: repo.role->logical[21]=92;break;
        case 10: repo.role->design_id="NATIVE_VERIFIED";break;
        case 11: repo.role->revision=0;break;
        }
        rejects([&]{load(repo);});
    }
    repo=fixture();repo.change_resources=true;rejects([&]{load(repo);});
    repo=fixture();repo.change_role=true;rejects([&]{load(repo);});
    std::cout<<"Saved player snapshot checks passed: "<<checks<<'\n';
}
