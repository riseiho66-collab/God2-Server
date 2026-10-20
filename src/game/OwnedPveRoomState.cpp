#include "game/OwnedPveRoomState.h"
#include "protocol/RecoveredRoleAuxiliary.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include <algorithm>
#include <limits>
#include <set>
namespace god2 {
namespace {
using T=OwnedPveRoomTypes;
void require(bool value,const char* message){if(!value)throw DatabaseError(message);}
std::uint64_t advance(std::uint64_t n){require(n<std::uint64_t(INT64_MAX),"PvE revision exhausted");return n+1;}
BattleActor player(const T::MemberInput& m){
    const auto& r=m.resources;const auto& a=m.auxiliary.logical;
    return {m.primary_slot,m.identity.character,r.hp,r.max_hp,r.mp,r.max_mp,
        RecoveredRoleAuxiliary::physical_attack(a),RecoveredRoleAuxiliary::magical_attack(a),
        RecoveredRoleAuxiliary::physical_defense(a),RecoveredRoleAuxiliary::magical_defense(a)};
}
BattleActor pet(const T::MemberInput& m){
    const auto& p=*m.pet;const auto& saved=p.saved;
    require(bool(saved.pet)!=bool(saved.pet1),"PvE secondary needs exactly one actual saved pet kind");
    if(saved.pet){const auto r=saved.pet->stats.vitals();const auto a=saved.pet->stats.combat_values();
        return {p.actor_slot,m.identity.character,r.current_hp,r.maximum_hp,r.current_mp,r.maximum_mp,
            a.physical_attack,a.magical_attack,a.physical_defense,a.magical_defense};}
    const auto r=saved.pet1->stats.vitals();const auto a=saved.pet1->stats.combat_values();
    return {p.actor_slot,m.identity.character,r.current_hp,r.maximum_hp,r.current_mp,r.maximum_mp,
        a.physical_attack,a.magical_attack,a.physical_defense,a.magical_defense};
}
void add_member(T::Snapshot& state,T::MemberInput input,bool initial){
    const auto i=input.identity;
    require(i.session&&i.account&&i.character&&i.world_generation&&i.battle_generation&&
        i.channel>=1&&i.channel<=3&&i.actor_handle&&i.actor_handle<0x4000&&input.primary_slot<14&&
        input.resources.hp&&input.resources.valid_health()&&input.resources.mp<=input.resources.max_mp,
        "PvE member has no complete actual owner/alive resources/qualified slots");
    require(!state.members.contains(i.character),"PvE member already retained in this incarnation");
    for(const auto& [id,other]:state.members){(void)id;
        require(other.input.identity.session!=i.session&&other.input.identity.actor_handle!=i.actor_handle,
            "PvE duplicate Session/native actor incarnation");
        require(other.input.identity.channel==i.channel&&other.input.return_position.area==input.return_position.area&&
            other.input.return_position.scene==input.return_position.scene,"PvE admission crosses channel/scene");
    }
    require(!state.checkpoint.snapshot.actors[input.primary_slot],"PvE primary slot already occupied");
    state.checkpoint.snapshot.actors[input.primary_slot]=player(input);
    if(input.pet){require(input.pet->actor_slot<14&&input.pet->actor_slot!=input.primary_slot&&
        !state.checkpoint.snapshot.actors[input.pet->actor_slot]&&input.pet->saved.slot==44,
        "PvE secondary is not an unoccupied explicitly assigned active-pet slot");
        const auto actor=pet(input);require(actor.max_hp&&actor.hp<=actor.max_hp&&actor.mp<=actor.max_mp,"PvE secondary saved resources are invalid");
        state.checkpoint.snapshot.actors[input.pet->actor_slot]=actor;
    }
    T::Member member;member.input=std::move(input);member.grant_epoch=state.grant_epoch;
    // CUSTOM-0161: initial entry carries the first grants. A late member waits
    // for the next explicit grant_round, never resets already-consumed turns.
    member.primary_grant=initial;member.secondary_grant=initial&&member.input.pet&&
        state.checkpoint.snapshot.actors[member.input.pet->actor_slot]->hp!=0;
    state.members.emplace(i.character,std::move(member));
}
void revoke_dead(T::Snapshot& state){
    for(auto& [id,m]:state.members){(void)id;
        const bool usable=m.status!=T::MemberStatus::Withdrawn&&m.status!=T::MemberStatus::Returned&&!m.disconnected&&!m.return_context&&
            state.checkpoint.snapshot.state==BattleState::Active;
        if(!usable||!state.checkpoint.snapshot.actors[m.input.primary_slot]->hp)m.primary_grant=false;
        if(!usable||!m.input.pet||!state.checkpoint.snapshot.actors[m.input.pet->actor_slot]->hp)m.secondary_grant=false;
    }
}
}
struct OwnedPveRoomState::Room {
    Ticket ticket;std::shared_ptr<const State> state;std::shared_ptr<const void> claim;
    bool operating=false,invalidated=false,recovery=false;
    Room(Ticket t,std::shared_ptr<const State> s,std::shared_ptr<const void> c):ticket(std::move(t)),state(std::move(s)),claim(std::move(c)){}
};
class OwnedPveRoomState::Operation {
public:
    OwnedPveRoomState& owner;std::shared_ptr<Room> room;bool persisting=false;
    Operation(OwnedPveRoomState& o,std::shared_ptr<Room> r):owner(o),room(std::move(r)){
        require(owner.thread_==std::this_thread::get_id()&&!owner.stopped_,"PvE room executor stopped/mismatched");
        if(room->operating){room->invalidated=true;throw DatabaseError("PvE room operation reentered");}
        require(!room->recovery,"PvE durable room needs recovery");room->operating=true;room->invalidated=false;
    }
    ~Operation(){if(persisting&&room->invalidated)room->recovery=true;room->operating=false;}
    void current()const{require(!owner.stopped_&&!room->invalidated&&!room->recovery,"PvE operation source retired");}
};
OwnedPveRoomState::OwnedPveRoomState(SqliteOwnedPveRoomRepository& r):repository_(r),thread_(std::this_thread::get_id()){}
OwnedPveRoomState::~OwnedPveRoomState(){stop();}
void OwnedPveRoomState::check_current(const Types::PureCurrent& current){require(bool(current)&&current(),"PvE actual host source no longer current");}
std::shared_ptr<OwnedPveRoomState::Room> OwnedPveRoomState::find(const Ticket& ticket)const{
    require(thread_==std::this_thread::get_id(),"PvE room GAME executor mismatch");
    const auto at=rooms_.find(ticket.id());require(at!=rooms_.end()&&at->second->ticket.same_incarnation(ticket),"PvE private room ticket mismatch");return at->second;
}
OwnedPveRoomTypes::Member& OwnedPveRoomState::member(State& s,const Types::Identity& id){
    const auto at=s.members.find(id.character);require(at!=s.members.end()&&at->second.input.identity==id&&
        at->second.status!=Types::MemberStatus::Returned&&at->second.status!=Types::MemberStatus::Retired,"PvE actual member incarnation mismatch");return at->second;
}
void OwnedPveRoomState::require_drained(const State& s){require(std::none_of(s.outbox.begin(),s.outbox.end(),[](const auto& d){return d.status==Types::OutputStatus::Pending;}),"PvE earlier actual output not fully written");}
void OwnedPveRoomState::append(State& s,std::vector<Types::Output> outputs,bool every){
    std::set<std::uint64_t> recipients;
    for(auto& output:outputs){const auto at=s.members.find(output.character);
        require(at!=s.members.end()&&at->second.status!=Types::MemberStatus::Returned&&!at->second.disconnected,
            "PvE output names no retained live recipient");
        require(!output.logical.empty()&&output.logical.size()<=RecoveredWorldFrame::max_logical_size,
            "PvE actual projection is empty/too large");
        require(bool(RecoveredTaiwanServerRecords::read(output.logical)),"PvE projection is not a complete native server record sequence");
        // Validate framing/all allocations before ANY persistence/publication.
        (void)RecoveredWorldFrame::encode(output.logical);
        require(s.next_sequence<std::uint64_t(INT64_MAX),"PvE outbox sequence exhausted");
        s.outbox.push_back({s.next_sequence++,at->second.input.identity,output.kind,std::move(output.logical),Types::OutputStatus::Pending});
        recipients.insert(output.character);
    }
    if(every)for(const auto& [id,m]:s.members)if(m.status!=Types::MemberStatus::Returned&&!m.disconnected)
        require(recipients.contains(id),"PvE whole-room publication omitted a current recipient");
}
void OwnedPveRoomState::project(Operation& op,State& next,const Types::Change& change,const Types::Project& encode){
    require(bool(encode),"PvE actual projection provider missing");op.current();auto outputs=encode(next,change);op.current();append(next,std::move(outputs),true);
}
void OwnedPveRoomState::publish(Operation& op,std::shared_ptr<State> next,const Types::PureCurrent& current){
    op.current();check_current(current);op.current();
    next->revision=advance(op.room->state->revision);
    // Full historical bytes stay in the durable outbox table. Runtime retains
    // pending flights and each written return only, not an unbounded wire log.
    std::erase_if(next->outbox,[&](const auto& d){
        if(d.status==Types::OutputStatus::Written&&next->members.at(d.recipient.character).status==Types::MemberStatus::Returned)return true;
        if(d.status!=Types::OutputStatus::Failed)return false;
        return std::any_of(op.room->state->outbox.begin(),op.room->state->outbox.end(),[&](const auto& old){return old.sequence==d.sequence&&old.status==Types::OutputStatus::Failed;});
    });
    for(auto& [id,m]:next->members){(void)id;
        if(m.status!=Types::MemberStatus::Returned&&m.status!=Types::MemberStatus::Retired)m.input=repository_.updated_resources(std::move(m.input),next->checkpoint.snapshot,m.status==Types::MemberStatus::Withdrawn);
    }
    const auto before=op.room->state;op.persisting=true;
    const auto committed=repository_.replace(op.room->ticket,*before,*next,[&]{return !stopped_&&!op.room->invalidated&&current&&current();});
    require(committed.durable,"PvE repository returned without durable commit");
    // Durable after-state always replaces memory, even if COMMIT observers
    // retired the caller. Never retry the old resources/RNG/model as rollback.
    op.room->state=std::move(next);
    if(!committed.current||op.room->invalidated||stopped_)op.room->recovery=true;
}
OwnedPveRoomState::Ticket OwnedPveRoomState::create(Types::Encounter input,Types::Project encode,Types::PureCurrent current){
    require(thread_==std::this_thread::get_id()&&!stopped_,"PvE creation GAME owner unavailable");
    if(creating_){creation_reentered_=true;throw DatabaseError("PvE creation reentered");}
    creating_=true;creation_reentered_=false;struct End{bool& b;~End(){b=false;}}end{creating_};
    check_current(current);require(!input.members.empty()&&input.members.size()<=14&&!input.enemies.empty(),"PvE needs actual encounter participants/enemies");
    require(input.source_sha256.size()==64&&!input.source_record.empty(),"PvE encounter source provenance missing");
    auto guard=[&]{return !stopped_&&!creation_reentered_&&current&&current();};
    auto ticket=repository_.reserve(guard);
    try{
        auto next=std::make_shared<State>();next->id=ticket.id();next->incarnation=ticket.incarnation();next->revision=1;
        next->source_sha256=std::move(input.source_sha256);next->source_record=std::move(input.source_record);next->support_enabled=input.support_enabled;
        next->checkpoint.snapshot.id=ticket.id();next->checkpoint.snapshot.state=BattleState::Active;
        for(const auto& enemy:input.enemies){require(enemy.controller==0&&enemy.position>=14&&enemy.position<28&&
            !next->checkpoint.snapshot.actors[enemy.position],"PvE enemy lacks unique actual encounter authority");next->checkpoint.snapshot.actors[enemy.position]=enemy;}
        for(auto& m:input.members)add_member(*next,std::move(m),true);
        std::vector<BattleActor> actors;for(const auto& a:next->checkpoint.snapshot.actors)if(a)actors.push_back(*a);
        next->checkpoint=Battle(ticket.id(),actors,input.seed,input.numeric_profile).checkpoint();
        require(bool(encode),"PvE entry projection missing");auto outputs=encode(*next,{Types::Change::Kind::Entry,0,{}});check_current(guard);
        append(*next,std::move(outputs),true);
        for(const auto& [id,m]:next->members){(void)m;require(std::any_of(next->outbox.begin(),next->outbox.end(),[&](const auto& d){return d.recipient.character==id&&d.kind==Types::OutputKind::Entry;}),"PvE initial member has no actual entry output");}
        auto claim=repository_.claim_runtime(ticket);auto room=std::make_shared<Room>(ticket,next,std::move(claim));
        std::map<std::uint64_t,std::shared_ptr<Room>> staged;staged.emplace(ticket.id(),room);auto node=staged.extract(ticket.id());
        const auto committed=repository_.activate(ticket,*next,guard);require(committed.durable,"PvE activation not durable");
        room->recovery=!committed.current||stopped_||creation_reentered_;rooms_.insert(std::move(node));return ticket;
    }catch(...){repository_.abandon(ticket);throw;}
}
void OwnedPveRoomState::admit(const Ticket& ticket,Types::MemberInput input,Types::Project encode,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);require_drained(*op.room->state);
    auto next=std::make_shared<State>(*op.room->state);require(next->support_enabled&&next->checkpoint.snapshot.state==BattleState::Active,"PvE support is not currently open");
    const auto id=input.identity.character;add_member(*next,std::move(input),false);
    next->checkpoint.snapshot.revision=advance(next->checkpoint.snapshot.revision);(void)Battle::restore(next->checkpoint);
    project(op,*next,{Types::Change::Kind::Admission,id,{}},encode);
    require(std::any_of(next->outbox.begin(),next->outbox.end(),[&](const auto& d){return d.recipient.character==id&&d.kind==Types::OutputKind::Entry&&d.status==Types::OutputStatus::Pending;}),"PvE helper needs its own actual current-roster entry");
    publish(op,std::move(next),current);
}
void OwnedPveRoomState::toggle_support(const Ticket& ticket,Types::Identity identity,std::uint64_t epoch,std::uint8_t slot,bool enabled,Types::Project encode,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);require_drained(*op.room->state);auto next=std::make_shared<State>(*op.room->state);
    auto& m=member(*next,identity);require(m.status==Types::MemberStatus::Active&&!m.disconnected&&!m.return_context&&
        m.grant_epoch==epoch&&next->checkpoint.snapshot.state==BattleState::Active,"PvE support control has no current owned grant");
    const bool primary=slot==m.input.primary_slot,secondary=m.input.pet&&slot==m.input.pet->actor_slot;
    require(((primary&&m.primary_grant)||(secondary&&m.secondary_grant))&&
        next->checkpoint.snapshot.actors[slot]&&next->checkpoint.snapshot.actors[slot]->hp,
        "PvE support control does not own this living granted actor");
    // CUSTOM-0161: SOS control consumes the acting member's one granted actor
    // command. No original server timing, fee or admission formula is inferred.
    if(primary)m.primary_grant=false;else m.secondary_grant=false;
    next->support_enabled=enabled;project(op,*next,{Types::Change::Kind::Support,identity.character,{},slot},encode);publish(op,std::move(next),current);
}
void OwnedPveRoomState::act(const Ticket& ticket,Types::Identity identity,std::uint64_t epoch,BattleAction action,Battle::Rule rule,Types::Project encode,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);require_drained(*op.room->state);auto next=std::make_shared<State>(*op.room->state);
    auto& m=member(*next,identity);require(m.status==Types::MemberStatus::Active&&!m.disconnected&&!m.return_context&&m.grant_epoch==epoch,"PvE command has no current actual member/grant epoch");
    const bool primary=action.source==m.input.primary_slot,secondary=m.input.pet&&action.source==m.input.pet->actor_slot;
    require((primary&&m.primary_grant)||(secondary&&m.secondary_grant),"PvE command does not own this living granted actor");
    require(bool(rule),"PvE trusted action rule missing");auto battle=Battle::restore(next->checkpoint);std::optional<BattleActionResult> result;
    (void)battle.act(identity.character,next->checkpoint.snapshot.revision,action,[&](const auto& r){op.current();check_current(current);auto value=rule(r);op.current();check_current(current);return value;},
        [&](const auto&,const auto& r){result=r;return std::vector<std::uint8_t>{1};}); // Internal computation marker, NEVER native output.
    next->checkpoint=battle.checkpoint();if(primary)m.primary_grant=false;else m.secondary_grant=false;revoke_dead(*next);
    for(auto& [id,peer]:next->members){(void)id;if(peer.status!=Types::MemberStatus::Returned&&peer.status!=Types::MemberStatus::Retired)peer.input=repository_.updated_resources(std::move(peer.input),next->checkpoint.snapshot,peer.status==Types::MemberStatus::Withdrawn);}
    project(op,*next,{next->checkpoint.snapshot.state==BattleState::Finished?Types::Change::Kind::Terminal:Types::Change::Kind::Action,identity.character,std::move(result)},encode);publish(op,std::move(next),current);
}
void OwnedPveRoomState::act_ai(const Ticket& ticket,BattleAction action,Battle::Rule rule,Types::Project encode,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);require_drained(*op.room->state);auto next=std::make_shared<State>(*op.room->state);
    require(action.source<28&&next->checkpoint.snapshot.actors[action.source]&&next->checkpoint.snapshot.actors[action.source]->controller==0,"PvE AI command lacks actual encounter actor");
    require(bool(rule),"PvE AI trusted rule missing");auto battle=Battle::restore(next->checkpoint);std::optional<BattleActionResult> result;
    (void)battle.act(0,next->checkpoint.snapshot.revision,action,[&](const auto& r){op.current();check_current(current);auto value=rule(r);op.current();check_current(current);return value;},
        [&](const auto&,const auto& r){result=r;return std::vector<std::uint8_t>{1};});
    next->checkpoint=battle.checkpoint();revoke_dead(*next);
    for(auto& [id,m]:next->members){(void)id;if(m.status!=Types::MemberStatus::Returned&&m.status!=Types::MemberStatus::Retired)m.input=repository_.updated_resources(std::move(m.input),next->checkpoint.snapshot,m.status==Types::MemberStatus::Withdrawn);}
    project(op,*next,{next->checkpoint.snapshot.state==BattleState::Finished?Types::Change::Kind::Terminal:Types::Change::Kind::Action,0,std::move(result)},encode);publish(op,std::move(next),current);
}
void OwnedPveRoomState::grant_round(const Ticket& ticket,Types::Project encode,Types::PureCurrent current,bool observed){
    Operation op(*this,find(ticket));check_current(current);require_drained(*op.room->state);auto next=std::make_shared<State>(*op.room->state);
    require(next->checkpoint.snapshot.state==BattleState::Active,"PvE finished room cannot issue grants");
    for(const auto& [id,m]:next->members){(void)id;require(!m.primary_grant&&!m.secondary_grant,"PvE previous actor grants remain unconsumed");}
    next->grant_epoch=advance(next->grant_epoch);
    for(auto& [id,m]:next->members){(void)id;if(m.status==Types::MemberStatus::Returned||m.status==Types::MemberStatus::Retired)continue;
        m.grant_epoch=next->grant_epoch;if(m.status!=Types::MemberStatus::Active||m.disconnected||m.return_context)continue;
        m.primary_grant=next->checkpoint.snapshot.actors[m.input.primary_slot]->hp!=0;
        m.secondary_grant=m.input.pet&&next->checkpoint.snapshot.actors[m.input.pet->actor_slot]->hp!=0;
    }
    project(op,*next,{Types::Change::Kind::Grant,0,{},{},observed},encode);publish(op,std::move(next),current);
}
void OwnedPveRoomState::pass(const Ticket& ticket,Types::Identity identity,std::uint64_t epoch,std::uint8_t slot,Types::Project encode,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);require_drained(*op.room->state);
    auto next=std::make_shared<State>(*op.room->state);auto& m=member(*next,identity);
    require(m.status==Types::MemberStatus::Active&&!m.disconnected&&!m.return_context&&
        next->checkpoint.snapshot.state==BattleState::Active&&m.grant_epoch==epoch,
        "PvE CUSTOM pass has no current actual member/grant");
    const bool primary=slot==m.input.primary_slot,secondary=m.input.pet&&slot==m.input.pet->actor_slot;
    require(((primary&&m.primary_grant)||(secondary&&m.secondary_grant))&&
        next->checkpoint.snapshot.actors[slot]&&next->checkpoint.snapshot.actors[slot]->hp,
        "PvE CUSTOM pass does not own this living grant");
    if(primary)m.primary_grant=false;else m.secondary_grant=false;
    project(op,*next,{Types::Change::Kind::Grant,identity.character,{},slot},encode);
    publish(op,std::move(next),current);
}
void OwnedPveRoomState::withdraw(const Ticket& ticket,Types::Identity identity,bool disconnected,Types::Project encode,Types::PureCurrent current){
    if(disconnected){retire_disconnected(ticket,{identity},std::move(encode),std::move(current));return;}
    Operation op(*this,find(ticket));check_current(current);auto next=std::make_shared<State>(*op.room->state);auto& m=member(*next,identity);
    require(disconnected||!m.return_context,"PvE return already owns this member");
    // Capture actual pre-withdraw HP/MP in the SAME future resource transaction.
    if(m.status!=Types::MemberStatus::Withdrawn)m.input=repository_.updated_resources(std::move(m.input),next->checkpoint.snapshot,false);
    m.status=disconnected?Types::MemberStatus::Retired:Types::MemberStatus::Withdrawn;m.disconnected=disconnected;m.primary_grant=false;m.secondary_grant=false;
    // An already finished result/RNG is immutable. Zeroing its last victorious
    // actor after both sides' death would invent an impossible second outcome.
    if(next->checkpoint.snapshot.state==BattleState::Active){
        next->checkpoint.snapshot.actors[m.input.primary_slot]->hp=0;
        if(m.input.pet)next->checkpoint.snapshot.actors[m.input.pet->actor_slot]->hp=0;
        std::array<bool,2> living{};for(const auto& a:next->checkpoint.snapshot.actors)if(a&&a->hp)living[a->position/14]=true;
        if(!living[0]||!living[1]){next->checkpoint.snapshot.state=BattleState::Finished;next->checkpoint.snapshot.victorious_side=living[0]?0:1;}
    }
    if(disconnected)for(auto& d:next->outbox)if(d.recipient==identity&&d.status==Types::OutputStatus::Pending)d.status=Types::OutputStatus::Failed;
    next->checkpoint.snapshot.revision=advance(next->checkpoint.snapshot.revision);(void)Battle::restore(next->checkpoint);revoke_dead(*next);
    next->closed=std::all_of(next->members.begin(),next->members.end(),[](const auto& p){return p.second.status==Types::MemberStatus::Returned||p.second.status==Types::MemberStatus::Retired;});
    project(op,*next,{Types::Change::Kind::Withdrawal,identity.character,{}},encode);publish(op,std::move(next),current);
}
void OwnedPveRoomState::retire_disconnected(const Ticket& ticket,std::vector<Types::Identity> identities,Types::Project encode,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);require(!identities.empty(),"PvE disconnect cleanup needs an exact retained member set");
    auto next=std::make_shared<State>(*op.room->state);std::set<std::uint64_t> unique;
    const bool active=next->checkpoint.snapshot.state==BattleState::Active;
    for(const auto& identity:identities){require(unique.insert(identity.character).second,"PvE duplicate cleanup member");auto& m=member(*next,identity);
        if(m.status!=Types::MemberStatus::Withdrawn)m.input=repository_.updated_resources(std::move(m.input),next->checkpoint.snapshot,false);
        m.status=Types::MemberStatus::Retired;m.disconnected=true;m.primary_grant=false;m.secondary_grant=false;
        if(active){next->checkpoint.snapshot.actors[m.input.primary_slot]->hp=0;if(m.input.pet)next->checkpoint.snapshot.actors[m.input.pet->actor_slot]->hp=0;}
        for(auto& d:next->outbox)if(d.recipient==identity&&d.status==Types::OutputStatus::Pending)d.status=Types::OutputStatus::Failed;
    }
    if(active){std::array<bool,2> living{};for(const auto& a:next->checkpoint.snapshot.actors)if(a&&a->hp)living[a->position/14]=true;
        if(!living[0]||!living[1]){next->checkpoint.snapshot.state=BattleState::Finished;next->checkpoint.snapshot.victorious_side=living[0]?0:1;}}
    next->checkpoint.snapshot.revision=advance(next->checkpoint.snapshot.revision);(void)Battle::restore(next->checkpoint);revoke_dead(*next);
    next->closed=std::all_of(next->members.begin(),next->members.end(),[](const auto& p){return p.second.status==Types::MemberStatus::Returned||p.second.status==Types::MemberStatus::Retired;});
    for(const auto& identity:identities)project(op,*next,{Types::Change::Kind::Withdrawal,identity.character,{}},encode);
    publish(op,std::move(next),current);
}
std::vector<OwnedPveRoomTypes::Delivery> OwnedPveRoomState::pending(const Ticket& ticket)const{
    const auto room=find(ticket);require(!room->recovery&&!stopped_,"PvE outbox requires actual runtime recovery");std::vector<Types::Delivery> result;
    for(const auto& d:room->state->outbox)if(d.status==Types::OutputStatus::Pending)result.push_back(d);return result;
}
void OwnedPveRoomState::written(const Ticket& ticket,std::uint64_t sequence,Types::Identity identity,bool success,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);auto next=std::make_shared<State>(*op.room->state);auto& m=member(*next,identity);
    const auto at=std::find_if(next->outbox.begin(),next->outbox.end(),[&](const auto& d){return d.sequence==sequence;});
    require(at!=next->outbox.end()&&at->recipient==identity&&at->status==Types::OutputStatus::Pending,"PvE receipt does not own an exact pending output");
    if(success&&at->kind!=Types::OutputKind::Return)next->outbox.erase(at);
    else at->status=success?Types::OutputStatus::Written:Types::OutputStatus::Failed;
    if(!success){m.disconnected=true;m.primary_grant=false;m.secondary_grant=false;
        for(auto& d:next->outbox)if(d.recipient==identity&&d.status==Types::OutputStatus::Pending)d.status=Types::OutputStatus::Failed;
    }
    if(success&&!m.disconnected&&m.status==Types::MemberStatus::Entering&&std::none_of(next->outbox.begin(),next->outbox.end(),[&](const auto& d){return d.recipient==identity&&d.status==Types::OutputStatus::Pending;}))m.status=Types::MemberStatus::Active;
    publish(op,std::move(next),current);
}
void OwnedPveRoomState::prepare_return(const Ticket& ticket,Types::Identity identity,std::vector<std::uint8_t> logical,std::array<std::uint8_t,4> context,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);auto next=std::make_shared<State>(*op.room->state);auto& m=member(*next,identity);
    require(!m.disconnected&&!m.return_context&&(m.status==Types::MemberStatus::Withdrawn||next->checkpoint.snapshot.state==BattleState::Finished),"PvE member has no committed terminal/withdraw return");
    require(std::none_of(next->outbox.begin(),next->outbox.end(),[&](const auto& d){return d.recipient==identity&&d.status==Types::OutputStatus::Pending;}),"PvE return precedes this member's actual earlier fullwrites");
    const auto records=RecoveredTaiwanServerRecords::read_aggregate(logical);
    require(records&&!records->empty(),"PvE fresh return must be a bounded complete native aggregate");
    std::vector<Types::Output> outputs;std::vector<std::uint8_t> frame;
    for(const auto& record:*records){require(record.bytes.size()<=RecoveredWorldFrame::max_logical_size,"PvE return native record exceeds a whole frame");
        if(frame.size()>RecoveredWorldFrame::max_logical_size-record.bytes.size()){
            outputs.push_back({identity.character,Types::OutputKind::Return,std::move(frame)});frame.clear();}
        frame.insert(frame.end(),record.bytes.begin(),record.bytes.end());
    }
    if(!frame.empty())outputs.push_back({identity.character,Types::OutputKind::Return,std::move(frame)});
    m.return_context=context;m.primary_grant=false;m.secondary_grant=false;
    append(*next,std::move(outputs),false);m.return_sequence=next->next_sequence-1;
    publish(op,std::move(next),current);
}
void OwnedPveRoomState::complete_return(const Ticket& ticket,Types::Identity identity,std::array<std::uint8_t,4> context,Types::PureCurrent current){
    Operation op(*this,find(ticket));check_current(current);auto next=std::make_shared<State>(*op.room->state);auto& m=member(*next,identity);
    require(m.return_context&&*m.return_context==context,"PvE terminal context differs from actual retained return");
    const auto at=std::find_if(next->outbox.begin(),next->outbox.end(),[&](const auto& d){return d.sequence==m.return_sequence;});
    require(at!=next->outbox.end()&&at->kind==Types::OutputKind::Return&&at->recipient==identity&&at->status==Types::OutputStatus::Written,"PvE return lacks its exact fullwritten output");
    require(std::all_of(next->outbox.begin(),next->outbox.end(),[&](const auto& d){
        return d.recipient!=identity||d.kind!=Types::OutputKind::Return||
            (d.sequence<=m.return_sequence&&d.status==Types::OutputStatus::Written);}),
        "PvE return has an earlier pending/failed aggregate frame");
    m.status=Types::MemberStatus::Returned;next->closed=std::all_of(next->members.begin(),next->members.end(),[](const auto& p){return p.second.status==Types::MemberStatus::Returned||p.second.status==Types::MemberStatus::Retired;});publish(op,std::move(next),current);
}
std::shared_ptr<const OwnedPveRoomTypes::Snapshot> OwnedPveRoomState::inspect(const Ticket& ticket)const{const auto room=find(ticket);require(!room->recovery,"PvE durable state needs recovery");return room->state;}
bool OwnedPveRoomState::recovery_required(const Ticket& ticket)const noexcept{const auto at=rooms_.find(ticket.id());return at==rooms_.end()||!at->second->ticket.same_incarnation(ticket)||at->second->recovery;}
void OwnedPveRoomState::retire_closed(const Ticket& ticket){
    const auto room=find(ticket);require(!room->operating&&!room->recovery&&room->state->closed,"PvE live/recovery room cannot retire");
    require_drained(*room->state);rooms_.erase(ticket.id());
}
void OwnedPveRoomState::stop()noexcept{stopped_=true;creation_reentered_=true;for(auto& [id,room]:rooms_){(void)id;room->invalidated=true;room->recovery=true;}}
}
