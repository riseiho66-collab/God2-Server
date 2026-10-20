#include "game/NativeParty.h"
#include "game/OwnedPartyPublicationGuard.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <type_traits>
using namespace god2;
void require(bool n,const char* message){if(!n)throw std::runtime_error(message);}
NativeParty::Member member(unsigned n) {
    NativeParty::Member m{n,n,static_cast<std::uint16_t>(n),4,3,126,126};
    m.name="Player"+std::to_string(n);m.profession=1;m.level=1;m.resources={50,100,20,80};m.ready=true;return m;
}
int main(){try{
    // Source-only regression cases. These exercise the actual publication
    // helper used by every Application party writer; they are not run in PHASE1.
    {
        OwnedPartyPublicationGuard guard;NativeParty state;state.observe(member(1));
        {
            OwnedPartyPublicationGuard::Scope outer(guard);auto stale=state;
            {
                OwnedPartyPublicationGuard::Scope inner(guard);
                // Even an equal-value nested publication is an intervening write.
                require(inner.publish(state,NativeParty(state)),"Nested current party publish failed");
            }
            require(!outer.publish(state,std::move(stale)),"Same-value ABA overwrote nested party publication");
        }
        {
            OwnedPartyPublicationGuard::Scope outer(guard);
            {OwnedPartyPublicationGuard::Scope nested(guard);}
            require(!outer.current(),"Caught no-write nested entry did not poison party dispatch");
        }
        {
            OwnedPartyPublicationGuard::Scope publication(guard);bool first=true,last=true,paired=false;
            guard.observe([&]{return first;});guard.observe([&]{return last;});
            first=false; // The last successful observer cannot replace the first witness.
            require(!publication.publish_if(state,NativeParty(state),[&]() noexcept {paired=true;return true;}),"Stale early party peer published");
            require(!paired,"Paired directory changed before party source fence");
        }
        {
            OwnedPartyPublicationGuard::Scope publication(guard);auto next=state;next.observe(member(2));
            const auto source=guard.source_epoch();
            require(!publication.publish_if(state,NativeParty(next),[]() noexcept {return false;}),"Failed directory CAS published party model");
            require(!state.member(2),"Directory rejection partially published party model");
            require(publication.publish_if(state,std::move(next),[]() noexcept {return true;}),"Valid paired publication failed");
            require(guard.source_current(source)&&publication.current(),"Own party publish retired valid delivery source");
        }
        {
            OwnedPartyPublicationGuard::Scope stale(guard);const auto source=guard.source_epoch();guard.invalidate();
            require(!stale.current(),"Rebinding did not invalidate earlier party scope");
            require(!guard.source_current(source),"Scope-free observer retained a rebound party source");
        }
        {OwnedPartyPublicationGuard::Scope cleanup(guard);require(cleanup.publish(state,NativeParty{}),"Invalidation blocked later disconnect cleanup");}
        guard.stop();
        {OwnedPartyPublicationGuard::Scope stopped(guard);require(!stopped.publish(state,NativeParty{}),"Stopped guard accepted publication");}
    }
    NativeParty p;for(unsigned n=1;n<=7;++n)p.observe(member(n));
    auto now=std::chrono::steady_clock::now();
    using K=RecoveredParty::Kind;
    // An observation cannot silently hand a previous role's consent or group
    // to a new account/character on the same transport identity.
    {
        NativeParty identities;for(unsigned n=1;n<=4;++n)identities.observe(member(n));
        const auto reject_rebind=[&](unsigned session) {
            const auto before=identities;
            for(unsigned field=0;field<2;++field) {
                auto replacement=*identities.member(session);
                if(field==0)replacement.account=100;else replacement.character=100;
                bool rejected=false;
                try{identities.observe(replacement);}catch(const std::invalid_argument&){rejected=true;}
                require(rejected&&identities.same_state(before),"Role rebind inherited party state or changed consent");
            }
        };
        reject_rebind(1); // An ungrouped cached owner also has an incarnation.
        identities.handle(2,{K::Join,2,1},now);
        reject_rebind(1);reject_rebind(2); // Both sides of pending consent.
        require(!identities.handle(1,{K::Answer,0,2,1},now).empty(),"Rejected rebind destroyed valid consent");
        reject_rebind(1);reject_rebind(2); // Leader and member after acceptance.
        const auto before=*identities.member(2);auto refreshed=before;
        refreshed.x+=1;refreshed.resources[0]-=1;identities.observe(refreshed);
        require(!identities.refresh(2,before).empty()&&identities.party_size(2)==2,
            "Same owner resource refresh was rejected by identity fence");
        identities.handle(3,{K::Join,3,1},now);
        identities.disconnect(1); // Retire membership and every predecessor offer.
        auto replacement=member(1);replacement.account=100;replacement.character=100;
        identities.observe(replacement);
        require(!identities.party_size(1)&&!identities.party_size(2)&&
            identities.handle(1,{K::Answer,0,3,1},now).empty(),"Retired leader consent survived identity replacement");
        identities.disconnect(2);
        replacement=member(2);replacement.account=101;replacement.character=101;identities.observe(replacement);
        require(identities.handle(2,{K::Join,101,100},now).size()==1&&
            !identities.handle(1,{K::Answer,0,101,1},now).empty(),"Fresh explicitly retired owners cannot create a new party");
    }
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
    for(const auto r:{RecoveredParty::Request{K::Answer,0,0x1234,2,0xa5}}) {
        auto wire=RecoveredParty::encode(r);require(RecoveredParty::decode(wire)==std::optional{r},"Request raw roundtrip");
        const auto parsed=RecoveredWorldRecords::decode(wire);require(parsed && parsed->size()==1,"Party world parser");
        for(std::size_t n=1;n<wire.size();++n)require(!RecoveredWorldRecords::decode(std::span(wire).first(n)),"Party truncation accepted");
    }
    for(const auto r:{RecoveredParty::Request{K::Join,0xffffffff,0x12345678},
        RecoveredParty::Request{K::Kick,0,0xffffffff},
        RecoveredParty::Request{K::Answer,0,0x10000,1},
        RecoveredParty::Request{K::Leave,0x10000}}) {
        bool rejected=false;try{RecoveredParty::encode(r);}catch(const std::invalid_argument&){rejected=true;}
        require(rejected,"Unsupported internal party wire or native WORD overflow accepted");
    }
    // Source/static regression only: original cursor6 support.ani is C6A;
    // never reinterpret it as transient consenting CUSTOM party membership.
    using Sos=RecoveredSosSupportRequest;
    static_assert(!std::is_convertible_v<Sos::Request,RecoveredParty::Request>);
    require(RecoveredParty::size(0x6a)==0,"SOS wire still exposed by party codec");
    require(RecoveredParty::size(0x57)==0,"Team request still exposed as party Kick");
    require(RecoveredParty::size(0x5a)==0,"Dual self/member exit still exposed as self-only Leave");
    using Exit=RecoveredPartyExitRequest5A;
    for(const auto target:{0u,1u,65535u}) {
        Exit::Request request{static_cast<std::uint16_t>(target),{}};request.name.fill(0xa5);request.name[0]=0;
        const auto wire=Exit::encode(request);
        require(Exit::decode(wire)==std::optional{request} && !RecoveredParty::decode(wire),"Self/member target or name tail lost");
        const auto parsed=RecoveredWorldRecords::decode(wire);
        require(parsed && parsed->size()==1 && std::get<Exit::Request>(parsed->front())==request,"C5A didn't preserve raw member target");
    }
    using Team=RecoveredTeamRequest57;
    static_assert(!std::is_convertible_v<Team::Request,RecoveredParty::Request>);
    for(const auto target:{0u,0x12345678u,0xffffffffu}) {
        const auto wire=Team::encode({target});
        require(Team::decode(wire)==std::optional{Team::Request{target}} && !RecoveredParty::decode(wire),"Raw C57 team target lost or became Kick");
        const auto parsed=RecoveredWorldRecords::decode(wire);
        require(parsed && parsed->size()==1 && std::get<Team::Request>(parsed->front()).target==target,"World C57 did not retain independent team type");
    }
    for(const auto raw:{Sos::Request{0,0},Sos::Request{0xffffffffu,0x12345678u},
        Sos::Request{0x87654321u,0xffffffffu}}) {
        const auto wire=Sos::encode(raw);
        require(Sos::decode(wire)==std::optional{raw},"Full support DWORDs changed");
        require(!RecoveredParty::decode(wire),"Support request decoded into party Join");
        const auto parsed=RecoveredWorldRecords::decode(wire);
        require(parsed && parsed->size()==1 && std::get<Sos::Request>(parsed->front())==raw,"World C6A is not independent support type");
        for(std::size_t n=0;n<wire.size();++n)require(!Sos::decode(std::span(wire).first(n)),"Support truncation escaped");
        auto extra=std::vector<std::uint8_t>(wire.begin(),wire.end());extra.push_back(0);
        require(!Sos::decode(extra),"Support codec swallowed a suffix");
        require(!RecoveredWorldRecords::decode(extra),"Whole world batch leaked support before malformed suffix");
        extra.back()=0x30;extra.push_back(0);
        const auto mixed=RecoveredWorldRecords::decode(extra);
        require(mixed && mixed->size()==2 && std::holds_alternative<Sos::Request>((*mixed)[0]) &&
            std::holds_alternative<RecoveredWorldRecords::Tick>((*mixed)[1]),"Support/tick ordered flush changed");
    }
    using SosCommand=RecoveredSosBattleCommand;
    for(std::uint8_t actor=0;actor<=14;++actor)for(std::uint8_t secondary=0;secondary<2;++secondary)
        for(std::uint8_t requested=0;requested<2;++requested) {
        SosCommand::Bytes wire{0x35,actor,8,secondary,0xa5};
        const auto bit=static_cast<std::uint16_t>(1u<<(actor%14));
        const auto mask=actor<14?5u:7u;wire[mask]=static_cast<std::uint8_t>(bit);wire[mask+1]=static_cast<std::uint8_t>(bit>>8);
        wire[9]=0x78;wire[10]=0x56;wire[11]=0x34;wire[12]=0x12;wire[13]=requested;
        const auto command=SosCommand::decode(wire);
        require(command && SosCommand::encode(*command)==wire && command->actor_position()==actor &&
            command->side_flag()==secondary && command->opaque4()==0xa5 && command->context()==0x12345678u &&
            command->requested_flag()==requested,"SOS action8 exact producer bytes changed");
        const auto parsed=RecoveredWorldRecords::decode(wire);
        require(parsed && parsed->size()==1 && std::holds_alternative<SosCommand::Request>(parsed->front()),"C35 action8 still falls into attack/skill parser");
        for(std::size_t n=0;n<wire.size();++n)require(!SosCommand::decode(std::span(wire).first(n)),"SOS command truncation escaped");
        auto bad=wire;bad[13]=2;require(!SosCommand::decode(bad),"SOS request invented another flag");
        bad=wire;bad[mask]^=1;require(!SosCommand::decode(bad),"SOS target no longer the actual producer actor");
    }
    RecoveredParty::Name name{};name[0]='P';std::array<std::uint8_t,4> hud{0,0,1,0};
    require(RecoveredParty::preview(1,name,1,0,hud,1).size()==29 && RecoveredParty::member(1,name,true,hud).size()==25 &&
        RecoveredParty::remove(1,name).size()==19 && RecoveredParty::position(1,126,126).size()==7 &&
        RecoveredParty::vitals(1,50,100,20,80).size()==21,"Native response widths");
    require(RecoveredParty::vitals(1,50,100,20,80)==std::vector<std::uint8_t>{
        0x58,1,0,0,0,50,0,0,0,20,0,0,0,100,0,0,0,80,0,0,0},"Native HP/MP/maxHP/maxMP order");
    std::cout<<"Party consent/cap/ownership/leave/kick/lease/expiry and native codecs passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
