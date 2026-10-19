#include "game/SharedTaiwanChannelWorlds.h"
#include "game/SharedWorldPresence.h"
#include "game/SharedNativeWorldTransports.h"
#include "shared/world/SharedActorVisibility.h"
#include "db/RecoveredCharacterRepository.h"
#include <array>
#include <functional>
#include <map>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>

namespace {
using namespace god2;
using Presence=SharedWorldPresence;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class Exception,class F> bool refuses(F&& call){
    try{call();}catch(const Exception&){return true;}return false;
}
// Synthetic CUSTOM-0159 scalar/storage fixture only. No Session pointer,
// authentication, wire handle issuer, native gameplay or switch receipt exists.
struct Repository final:RecoveredCharacterRepository {
    struct Row{RecoveredCharacter root;RecoveredPosition position;};
    std::map<std::uint64_t,Row> rows;
    std::size_t observations=0;
    std::function<void()> on_list,on_position;
    bool fail_list=false,fail_position=false;
    void add(std::uint64_t account,std::uint64_t id,std::uint8_t slot=0){
        RecoveredCharacter root;root.id=id;root.account_id=account;root.slot=slot;
        root.profile[0]=static_cast<std::uint8_t>('A'+slot);root.created_at="synthetic-channel-source";
        rows.emplace(id,Row{root,{1,0,static_cast<std::uint16_t>(10+slot),20,0x100000001ULL+slot}});
    }
    const RecoveredPosition& position(std::uint64_t id)const{return rows.at(id).position;}
    std::vector<RecoveredCharacter> list_for_account(std::uint64_t account) override{
        ++observations;if(auto callback=std::exchange(on_list,{}))callback();
        if(fail_list)throw std::runtime_error("Synthetic list observer failure");
        std::vector<RecoveredCharacter> result;
        for(const auto& [id,row]:rows)if(row.root.account_id==account)result.push_back(row.root);
        return result;
    }
    std::optional<RecoveredPosition> load_position(std::uint64_t account,std::uint64_t id) override{
        ++observations;if(auto callback=std::exchange(on_position,{}))callback();
        if(fail_position)throw std::runtime_error("Synthetic position observer failure");
        const auto at=rows.find(id);
        return at!=rows.end()&&at->second.root.account_id==account?std::optional{at->second.position}:std::nullopt;
    }
    [[noreturn]] static void unused(){throw std::runtime_error("Unused repository method entered");}
    std::optional<CharacterRoleSnapshot> load_role(std::uint64_t,std::uint64_t) override{unused();}
    RoleResourceCommit commit_role_resources(std::uint64_t,std::uint64_t,const std::optional<CharacterRoleSnapshot>&,
        const CharacterResources&,CharacterRoleSnapshot,CharacterResources) override{unused();}
    std::optional<CharacterExperience> load_experience(std::uint64_t,std::uint64_t) override{unused();}
    BattleSettlement settle_battle(std::uint64_t,std::uint64_t,std::uint64_t,const CharacterResources&,
        CharacterResources,bool,std::uint64_t,const std::optional<BattleProgressionCommit>&) override{unused();}
    std::uint64_t reserve_battle(std::uint64_t,std::uint64_t,const CharacterResources&) override{unused();}
    std::optional<CharacterResources> load_resources(std::uint64_t,std::uint64_t) override{unused();}
    CharacterResources commit_resources(std::uint64_t,std::uint64_t,const std::optional<CharacterResources>&,
        CharacterResources) override{unused();}
    RecoveredCharacter create(std::uint64_t,const std::array<std::uint8_t,40>&) override{unused();}
    RecoveredPosition commit_position(std::uint64_t,std::uint64_t,const std::optional<RecoveredPosition>&,
        std::uint16_t,std::uint16_t,std::uint16_t,std::uint16_t) override{unused();}
};
constexpr std::uint64_t account=0x100000007ULL,other_account=0x200000007ULL;
constexpr std::uint64_t a=0x1000000a1ULL,b=0x2000000a1ULL,c=0x3000000a1ULL,d=0x4000000a1ULL;
constexpr std::uint64_t sa=0x100000011ULL,sb=0x200000011ULL,sc=0x300000011ULL,sd=0x400000011ULL;
void seed(Repository& repository){repository.add(account,a);repository.add(account,b,1);repository.add(other_account,c);repository.add(other_account,d,1);}

void distinct_worlds_and_exclusion(){
    Repository repository,foreign;seed(repository);
    SharedTaiwanChannelWorlds worlds(repository);
    require(worlds.owns_repository(repository)&&!worlds.owns_repository(foreign),"Collection mixed repository identity");
    std::array<std::shared_ptr<SharedWorldHost>,3> hosts{worlds.world(0),worlds.world(1),worlds.world(2)};
    std::array<std::shared_ptr<Presence>,3> presence{hosts[0]->presence(),hosts[1]->presence(),hosts[2]->presence()};
    for(std::uint8_t k=0;k<3;++k){
        require(hosts[k]->channel()==k&&presence[k]->channel()==k&&hosts[k]->owns_repository(repository)&&
            hosts[k]->visibility()->owns_presence(presence[k])&&hosts[k]->transports()->owns_presence(presence[k]),
            "Actual world registries do not share their own channel presence");
        for(std::uint8_t j=0;j<k;++j)
            require(hosts[k]!=hosts[j]&&presence[k]!=presence[j]&&hosts[k]->visibility()!=hosts[j]->visibility()&&
                hosts[k]->transports()!=hosts[j]->transports()&&!hosts[k]->visibility()->owns_presence(presence[j])&&
                !hosts[k]->transports()->owns_presence(presence[j]),"Channels reused world visibility/transport registries");
    }
    const auto first=presence[0]->prepare(sa,account,a,41,repository.position(a));
    require(first&&worlds.character_reserved(a)&&presence[2]->character_reserved(a),"Pending entry did not hold global character custody");
    const auto before_collision=repository.observations;
    require(!presence[1]->prepare(sb,account,a,41,repository.position(a))&&
        !presence[1]->prepare(sa,account,b,41,repository.position(b))&&repository.observations==before_collision,
        "Cross-channel pending character/session collision reached repository or admitted twice");
    const auto second=presence[1]->prepare(sb,account,b,41,repository.position(b));
    const auto third=presence[2]->prepare(sc,other_account,c,41,repository.position(c));
    require(second&&third,"Same-account distinct characters or world-local actor41 were excluded across channels");
    for(const auto& p:presence){const auto empty=p->observe_ready_population();require(empty&&empty->characters().empty(),"Pending character became ready population");}
    require(presence[0]->activate(*first,41),"First channel could not activate its exact pending lease");
    for(std::uint8_t k=0;k<3;++k){
        const auto population=presence[k]->observe_ready_population();
        require(population&&population->characters().size()==(k==0?1u:0u),"Ready population crossed channel boundary");
    }
    require(presence[1]->activate(*second,41)&&presence[2]->activate(*third,41),"Independent channels could not activate repeated local actor41");
    std::array<Presence::Lease,3> leases{*first,*second,*third};
    const auto active_collisions=repository.observations;
    for(std::uint8_t k=0;k<3;++k)for(std::uint8_t j=0;j<3;++j)if(k!=j)
        require(!presence[j]->prepare(0x500000000ULL+10*k+j,leases[k].account,leases[k].character,42,leases[k].position),
            "Active character obtained a second channel owner");
    require(repository.observations==active_collisions,"Active global character collision reached repository observers");
    std::array<std::optional<Presence::ReadyPopulation>,3> populations;
    for(std::uint8_t k=0;k<3;++k){
        populations[k]=presence[k]->observe_ready_population();
        require(populations[k]&&populations[k]->characters().size()==1&&populations[k]->characters()[0].lease==leases[k]&&
            populations[k]->characters()[0].character.id==leases[k].character,"Full64 ready root/lease lost channel identity");
    }
    const auto retained_before=repository.observations;
    for(std::uint8_t k=0;k<3;++k){
        require(worlds.character_reserved(leases[k].character)&&presence[k]->retained_ready_current(leases[k])&&
            presence[k]->retained_population_current(*populations[k]),"Exact retained source was not current");
        for(std::uint8_t j=0;j<3;++j)if(j!=k)
            require(!presence[k]->retained_ready_current(leases[j])&&!presence[k]->retained_population_current(*populations[j])&&
                !presence[k]->release(leases[j]),"Foreign channel lease/population affected local registry");
    }
    require(repository.observations==retained_before,"Global reserved/retained fences called repository observers");
    const auto local_collision=repository.observations;
    require(!presence[0]->prepare(sd,other_account,d,41,repository.position(d))&&
        !worlds.character_reserved(d)&&repository.observations==local_collision,"World-local duplicate actor mutated global custody");
    require(presence[0]->release(*first)&&!worlds.character_reserved(a),"Exact release did not free global claim");
    const auto successor=presence[0]->prepare(sa,account,a,41,repository.position(a));
    require(successor&&successor->generation>first->generation&&presence[0]->activate(*successor,41)&&
        !presence[0]->release(*first)&&worlds.character_reserved(a)&&presence[0]->retained_ready_current(*successor),
        "Stale generation release freed a successor claim");
    require(!presence[0]->retained_population_current(*populations[0])&&presence[1]->retained_population_current(*populations[1])&&
        presence[2]->retained_population_current(*populations[2]),"Local replacement invalidated another channel population");
    auto narrowed=*successor;narrowed.account^=std::uint64_t{1}<<32;
    require(!presence[0]->retained_ready_current(narrowed)&&!presence[0]->release(narrowed)&&worlds.character_reserved(a),
        "Retained/release identity narrowed the full account value");
    require(presence[0]->release(*successor),"Successor did not release normally");
    const auto transferred=presence[2]->prepare(sa,account,a,42,repository.position(a));
    require(transferred&&presence[2]->activate(*transferred,42)&&!presence[0]->release(*successor)&&worlds.character_reserved(a),
        "Released character could not occupy another channel or stale release freed it");
}

void failures_and_reentrant_observers(){
    Repository repository;seed(repository);SharedTaiwanChannelWorlds worlds(repository);
    const auto p0=worlds.world(0)->presence(),p1=worlds.world(1)->presence();
    auto wrong=repository.position(a);++wrong.revision;
    require(!p0->prepare(sa,account,a,41,wrong)&&!worlds.character_reserved(a),"Stored-position rejection leaked global pending claim");
    repository.fail_list=true;
    require(refuses<std::runtime_error>([&]{(void)p0->prepare(sa,account,a,41,repository.position(a));})&&!worlds.character_reserved(a),
        "Throwing root observer leaked global pending claim");repository.fail_list=false;
    repository.fail_position=true;
    require(refuses<std::runtime_error>([&]{(void)p0->prepare(sa,account,a,41,repository.position(a));})&&!worlds.character_reserved(a),
        "Throwing position observer leaked global pending claim");repository.fail_position=false;
    bool pending_seen=false,duplicate_refused=false;
    repository.on_list=[&]{
        pending_seen=worlds.character_reserved(a);const auto before=repository.observations;
        duplicate_refused=!p1->prepare(sb,account,a,41,repository.position(a))&&repository.observations==before;
    };
    const auto first=p0->prepare(sa,account,a,41,repository.position(a));
    require(first&&pending_seen&&duplicate_refused,"Global claim was acquired after repository observation");
    std::optional<Presence::Lease> replacement;
    repository.on_list=[&]{
        require(p0->release(*first),"Reentrant release failed to retire original pending lease");
        replacement=p1->prepare(sb,account,a,41,repository.position(a));
        require(replacement&&p1->activate(*replacement,41),"Reentrant successor could not occupy freed global claim");
    };
    require(!p0->activate(*first,41)&&replacement&&!p0->release(*first)&&p1->retained_ready_current(*replacement)&&worlds.character_reserved(a),
        "Activation resurrected released source or stale cleanup freed reentrant successor");
    require(p1->release(*replacement),"Reentrant successor cleanup failed");
    bool nested_prepare_refused=false;
    repository.on_list=[&]{nested_prepare_refused=!p0->prepare(sb,account,b,42,repository.position(b));};
    require(!p0->prepare(sa,account,a,41,repository.position(a))&&nested_prepare_refused&&
        !worlds.character_reserved(a)&&!worlds.character_reserved(b),"Nested prepare retained an unqualified outer/global claim");
    const auto other=p0->prepare(sb,account,b,42,repository.position(b));require(bool(other),"Independent prepared fixture absent");
    bool nested_active=false;
    repository.on_list=[&]{nested_active=p0->activate(*other,42);};
    require(!p0->prepare(sa,account,a,41,repository.position(a))&&nested_active&&p0->retained_ready_current(*other)&&
        !worlds.character_reserved(a)&&worlds.character_reserved(b),"Reentrant activation silently installed the outer source or lost an independent claim");
    repository.on_list=[&]{require(p0->release(*other),"Nested release did not retire independent active lease");};
    require(!p0->prepare(sa,account,a,41,repository.position(a))&&!worlds.character_reserved(a)&&!worlds.character_reserved(b),
        "Reentrant release was ignored at outer preparation fence");
    const auto clean=p1->prepare(sa,account,a,41,repository.position(a));
    require(clean&&p1->activate(*clean,41),"Rejected/throwing/reentrant sources left global ownership stuck");
    const auto expected=repository.position(a);
    std::optional<Presence::Lease> step_successor;
    repository.on_position=[&]{
        require(p1->release(*clean),"Position observer could not retire original ready source");
        step_successor=p0->prepare(sb,account,a,41,repository.position(a));
        require(step_successor&&p0->activate(*step_successor,41),"Position observer could not install cross-channel successor");
    };
    // commit_position deliberately throws if entered: only the actual retained
    // fence after the observer can keep the obsolete source away from the CAS.
    require(!p1->commit_owned_step(*clean,expected,static_cast<std::uint16_t>(expected.x+1),expected.y)&&
        step_successor&&p0->retained_ready_current(*step_successor)&&!p1->release(*clean)&&worlds.character_reserved(a),
        "Obsolete position observer source reached CAS or freed its real cross-channel successor");
}

void construction_and_thread_bounds(){
    Repository repository,foreign;seed(repository);
    auto ownership=std::make_shared<SharedChannelCharacterOwnership>(repository);
    require(refuses<std::invalid_argument>([&]{Presence bad(repository,{},0);})&&
        refuses<std::invalid_argument>([&]{Presence bad(foreign,ownership,0);})&&
        refuses<std::invalid_argument>([&]{Presence bad(repository,ownership,3);})&&
        refuses<std::invalid_argument>([&]{SharedWorldHost bad(repository,{},0);})&&
        refuses<std::invalid_argument>([&]{SharedWorldHost bad(foreign,ownership,0);}),"Invalid channel constructor succeeded");
    auto host=std::make_shared<SharedWorldHost>(repository,ownership,0);
    require(refuses<std::invalid_argument>([&]{Presence duplicate(repository,ownership,0);})&&
        refuses<std::invalid_argument>([&]{SharedWorldHost duplicate(repository,ownership,0);}),"Two live registries claimed one channel ordinal");
    SharedTaiwanChannelWorlds worlds(repository);
    require(refuses<std::out_of_range>([&]{(void)worlds.world(3);}),"Fourth collection channel was exposed");
    const auto presence=host->presence();
    unsigned wrong_thread_refusals=0;
    std::thread other([&]{
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)worlds.world(0);});
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)worlds.character_reserved(a);});
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)worlds.owns_repository(repository);});
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)host->presence();});
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)host->channel();});
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)presence->channel();});
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)ownership->character_reserved(a);});
        wrong_thread_refusals+=refuses<std::logic_error>([&]{(void)ownership->owns_repository(repository);});
    });other.join();
    require(wrong_thread_refusals==8&&worlds.owns_repository(repository),"Wrong-thread getter escaped owner fence or damaged actual owner");
    // Existing private single-host construction remains an independent world0.
    // Two unrelated defaults do not silently join a three-channel owner.
    SharedWorldHost single(repository),independent(repository);
    const auto one=single.presence()->prepare(sa,account,a,41,repository.position(a));
    const auto two=independent.presence()->prepare(sa,account,a,41,repository.position(a));
    require(one&&two&&single.channel()==0&&independent.channel()==0&&single.presence()!=independent.presence(),
        "Default one-host construction changed its private ownership semantics");
}

void retained_tokens_do_not_keep_retired_world_alive(){
    Repository repository;seed(repository);
    auto ownership=std::make_shared<SharedChannelCharacterOwnership>(repository);
    std::optional<Presence::ReadyPopulation> old_ready;
    std::optional<Presence::InitialPopulation> old_initial;
    std::optional<Presence::Lease> old_lease;
    {
        SharedWorldHost old(repository,ownership,0);const auto presence=old.presence();
        old_lease=presence->prepare(sa,account,a,41,repository.position(a));require(bool(old_lease),"Retirement fixture could not prepare");
        old_initial=presence->observe_initial_population(*old_lease);require(bool(old_initial),"Retirement fixture missing private initial token");
        require(presence->activate(*old_lease,41),"Retirement fixture could not activate");
        old_ready=presence->observe_ready_population();
        require(old_ready&&ownership->character_reserved(a),"Retirement fixture missing ready token/global claim");
    }
    const auto before=repository.observations;
    require(!ownership->character_reserved(a)&&repository.observations==before,"Held population token kept destroyed world/global claim current");
    SharedWorldHost replacement(repository,ownership,0);const auto presence=replacement.presence();
    const auto successor=presence->prepare(sb,account,a,41,repository.position(a));
    require(successor&&presence->activate(*successor,41)&&!presence->retained_population_current(*old_ready)&&
        !presence->retained_initial_population_current(*old_initial)&&!presence->release(*old_lease)&&ownership->character_reserved(a),
        "Retained private token/scalar old session gained authority over replacement channel slot");
}
} // namespace

void test_taiwan_channel_worlds(){
    distinct_worlds_and_exclusion();failures_and_reentrant_observers();
    construction_and_thread_bounds();retained_tokens_do_not_keep_retired_world_alive();
}
