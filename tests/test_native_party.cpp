#include "game/NativeParty.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
using namespace god2;
void require(bool n,const char* message){if(!n)throw std::runtime_error(message);}
NativeParty::Member member(unsigned n) {
    NativeParty::Member m{n,n,static_cast<std::uint16_t>(n),4,3,126,126};
    m.name="Player"+std::to_string(n);m.profession=1;m.level=1;m.resources={50,100,20,80};m.ready=true;return m;
}
int main(){try{
    NativeParty p;for(unsigned n=1;n<=7;++n)p.observe(member(n));
    auto now=std::chrono::steady_clock::now();
    using K=RecoveredParty::Kind;
    require(p.handle(2,{K::Join,3,1},now).empty(),"Forged source joined");
    require(p.handle(2,{K::Join,2,2},now).empty(),"Self join");
    require(p.handle(2,{K::Join,2,1},now).size()==1,"Preview missing");
    require(p.handle(3,{K::Answer,0,2,1},now).empty(),"Wrong leader accepted");
    require(p.handle(1,{K::Answer,0,2,0},now).empty() && !p.party_size(1),"Decline created party");
    require(p.handle(2,{K::Join,2,1},now).size()==1,"Second preview missing");
    require(p.handle(1,{K::Answer,0,2,1},now).size()==8 && p.party_size(2)==2,"Acceptance roster");
    for(unsigned n=3;n<=5;++n){require(p.handle(n,{K::Join,n,1},now).size()==1,"Join preview");
        require(!p.handle(1,{K::Answer,0,n,1},now).empty(),"Join accept");}
    require(p.party_size(1)==5 && p.handle(6,{K::Join,6,1},now).empty(),"Native five member cap");
    require(p.handle(2,{K::Kick,0,3},now).empty(),"Nonleader kick");
    auto before=*p.member(2);auto after=before;after.x+=1;after.resources[0]-=1;p.observe(after);
    require(p.refresh(2,before).size()==8,"Four peers missing position/vitals");
    require(p.handle(1,{K::Kick,0,2},now).size()==5 && !p.party_size(2),"Leader kick");
    require(p.handle(2,{K::Join,2,1},now).size()==1,"Kicked member cannot rejoin");
    require(p.handle(1,{K::Answer,0,2,1},now+std::chrono::seconds(31)).empty(),"Expired invitation accepted");
    auto remote=member(6);remote.scene=4;p.observe(remote);
    require(p.handle(6,{K::Join,6,1},now).empty(),"Cross scene join");
    require(p.disconnect(1).size()==16 && !p.party_size(3),"Leader disconnect did not disband");
    p.observe(member(1));require(p.handle(3,{K::Join,3,1},now).size()==1,"Leader lease cannot reopen");
    require(!p.handle(1,{K::Answer,0,3,1},now).empty(),"Reopen accept");
    require(p.handle(3,{K::Leave,3},now).size()==2 && !p.party_size(1),"Leave last other did not clear leader");
    require(p.handle(3,{K::Join,3,1},now).size()==1,"Cancellation preview missing");
    require(p.handle(3,{K::Leave,3},now).empty(),"Pending cancellation created membership");
    require(p.handle(1,{K::Answer,0,3,1},now).empty() && !p.party_size(3),"Cancelled invitation accepted");
    // A ready recipient must recover changes missed while unavailable, even
    // when no actor changes again after the recipient returns.
    NativeParty recovery;for(unsigned n=1;n<=4;++n)recovery.observe(member(n));
    recovery.handle(2,{K::Join,2,1},now);recovery.handle(1,{K::Answer,0,2,1},now);
    auto unavailable=*recovery.member(2);unavailable.ready=false;recovery.observe(unavailable);
    auto old=*recovery.member(1);auto moved=old;moved.x=130;moved.resources[0]=37;recovery.observe(moved);
    require(recovery.refresh(1,old).empty(),"Unavailable recipient received party stats");
    auto restored=unavailable;restored.ready=true;recovery.observe(restored);
    const auto hydrated=recovery.refresh(2,unavailable);
    require(hydrated.size()==4,"Readiness recovery did not replay both directions");
    require(std::any_of(hydrated.begin(),hydrated.end(),[](const auto& d){return d.recipient==2 &&
        d.event==NativeParty::Event::Position && d.actor.character==1 && d.actor.x==130;}),"Returned peer position stale");
    require(std::any_of(hydrated.begin(),hydrated.end(),[](const auto& d){return d.recipient==2 &&
        d.event==NativeParty::Event::Vitals && d.actor.character==1 && d.actor.resources[0]==37;}),"Returned peer HP stale");
    recovery.observe(unavailable);recovery.handle(3,{K::Join,3,1},now);
    require(recovery.handle(1,{K::Answer,0,3,1},now).empty() && recovery.party_size(1)==2,
        "Accept replay bypassed unavailable existing member");
    restored.scene=4;recovery.observe(restored);recovery.handle(3,{K::Join,3,1},now);
    require(recovery.handle(1,{K::Answer,0,3,1},now).empty(),"Cross-scene existing member bypassed admission");
    const auto different_scene=recovery.refresh(2,unavailable);
    require(std::none_of(different_scene.begin(),different_scene.end(),[](const auto& d) {
        return d.event==NativeParty::Event::Position;
    }),"Cross-scene coordinates replayed");
    auto scene_before=restored;restored.scene=3;recovery.observe(restored);
    const auto scene_back=recovery.refresh(2,scene_before);
    require(std::count_if(scene_back.begin(),scene_back.end(),[](const auto& d){return d.event==NativeParty::Event::Position;})==2,
        "Scene return did not rehydrate current positions");
    recovery.handle(3,{K::Join,3,1},now);require(!recovery.handle(1,{K::Answer,0,3,1},now).empty(),"Qualified member cannot join after recovery");
    require(recovery.participants(1).size()==3 && recovery.participants(4)==std::vector<std::uint64_t>{4},"Relevant party snapshot scope");
    for(const auto r:{RecoveredParty::Request{K::Join,0xffffffff,0x12345678},
        {K::Answer,0,0x1234,2,0xa5},{K::Kick,0,0xffffffff},{K::Leave,0x1234}}) {
        auto wire=RecoveredParty::encode(r);require(RecoveredParty::decode(wire)==std::optional{r},"Request raw roundtrip");
        const auto parsed=RecoveredWorldRecords::decode(wire);require(parsed && parsed->size()==1,"Party world parser");
        for(std::size_t n=1;n<wire.size();++n)require(!RecoveredWorldRecords::decode(std::span(wire).first(n)),"Party truncation accepted");
    }
    for(const auto r:{RecoveredParty::Request{K::Answer,0,0x10000,1},
        RecoveredParty::Request{K::Leave,0x10000}}) {
        bool rejected=false;try{RecoveredParty::encode(r);}catch(const std::invalid_argument&){rejected=true;}
        require(rejected,"Native WORD overflow silently truncated");
    }
    RecoveredParty::Name name{};name[0]='P';std::array<std::uint8_t,4> hud{0,0,1,0};
    require(RecoveredParty::preview(1,name,1,0,hud,1).size()==29 && RecoveredParty::member(1,name,true,hud).size()==25 &&
        RecoveredParty::remove(1,name).size()==19 && RecoveredParty::position(1,126,126).size()==7 &&
        RecoveredParty::vitals(1,50,100,20,80).size()==21,"Native response widths");
    require(RecoveredParty::vitals(1,50,100,20,80)==std::vector<std::uint8_t>{
        0x58,1,0,0,0,50,0,0,0,20,0,0,0,100,0,0,0,80,0,0,0},"Native HP/MP/maxHP/maxMP order");
    std::cout<<"Party consent/cap/ownership/leave/kick/lease/expiry and native codecs passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
