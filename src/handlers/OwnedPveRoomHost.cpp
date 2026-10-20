#include "handlers/OwnedPveRoomHost.h"
#include "protocol/RecoveredWorldEntryView.h"
#include <algorithm>
#include <set>
#include <deque>
#include <variant>
namespace god2 {
namespace {
using T=OwnedPveRoomTypes;
void need(bool value,const char* why){if(!value)throw DatabaseError(why);}
bool finalized(const T::Member& m){return m.status==T::MemberStatus::Returned||m.status==T::MemberStatus::Retired;}
void sourced(const T::MemberInput& m,const Session::OwnedPveBinding& b){
    const auto& i=m.identity;
    need(i.session==b.session_id()&&i.account==b.account()&&i.character==b.character()&&
        i.world_generation==b.world_generation()&&i.battle_generation==b.battle_generation()&&
        i.channel==b.channel(),"PvE provider cannot replace actual prepared Session owner");
}
void fields(const RecoveredBattleCommand::BasicAttackRequest& r,const T::Member& m,const T::Snapshot& s,bool alive){
    const auto slot=r.actor_position;
    need(r.side_flag==(slot==m.input.primary_slot?0:1)&&r.context_storage==m.input.command_context&&
        (slot==m.input.primary_slot||(m.input.pet&&slot==m.input.pet->actor_slot))&&
        slot<14&&s.checkpoint.snapshot.actors[slot]&&
        (!alive||s.checkpoint.snapshot.actors[slot]->hp),"PvE native command lacks actual actor/context ownership");
    for(unsigned side=0;side<2;++side){need(!(r.target_masks[side]&0xc000u),"PvE command target mask exceeds native roster");
        for(unsigned bit=0;bit<14;++bit)if(r.target_masks[side]&(1u<<bit))
            need(bool(s.checkpoint.snapshot.actors[side*14+bit]),"PvE native command target names no current actor");}
}
}
struct OwnedPveRoomHost::Peer {
    std::shared_ptr<Session> session;Binding binding;T::Identity identity;
    bool prepared=true,retired=false,returned=false;
    std::optional<std::uint64_t> flight;
    std::optional<std::array<std::uint8_t,4>> return_context;
    Peer(std::shared_ptr<Session> s,Binding b):session(std::move(s)),binding(std::move(b)){}
};
struct OwnedPveRoomHost::Room {
    enum class Cycle {Player,AwaitPlayerProgress,Ai,AwaitAiProgress};
    struct Queued {std::shared_ptr<Peer> peer;std::uint64_t grant_epoch;std::vector<RecoveredWorldRecords::Record> records;};
    std::optional<Ticket> ticket;
    std::shared_ptr<const Sources> sources;
    std::map<std::uint64_t,std::shared_ptr<Peer>> peers;
    std::vector<std::uint8_t> ai_remaining;
    std::deque<Queued> queued;
    Cycle cycle{Cycle::Player};std::set<std::uint64_t> progress;
    bool ai_emitted=false,busy=false,poisoned=false,failed=false;
};
class OwnedPveRoomHost::Operation {
public:
    std::shared_ptr<Room> room;
    explicit Operation(std::shared_ptr<Room> r):room(std::move(r)){
        need(!room->failed,"PvE room host needs explicit durable recovery");
        if(room->busy){room->poisoned=true;throw DatabaseError("PvE host source callback reentered");}
        room->busy=true;room->poisoned=false;
    }
    ~Operation(){room->busy=false;}
};
OwnedPveRoomHost::OwnedPveRoomHost(SqliteOwnedPveRoomRepository& repo):state_(repo),thread_(std::this_thread::get_id()){}
OwnedPveRoomHost::~OwnedPveRoomHost(){stop();}
bool OwnedPveRoomHost::bound(const Session& s)const noexcept{
    const auto at=sessions_.find(s.id());if(at==sessions_.end())return false;
    const auto room=at->second.lock();if(!room)return false;
    const auto peer=room->peers.find(s.id());return peer!=room->peers.end()&&peer->second->session.get()==&s&&!peer->second->returned;
}
std::shared_ptr<OwnedPveRoomHost::Room> OwnedPveRoomHost::room_for(const Session& s)const{
    need(thread_==std::this_thread::get_id()&&!stopped_,"PvE host GAME owner unavailable");
    const auto at=sessions_.find(s.id());need(at!=sessions_.end(),"PvE actual Session has no retained room");
    auto room=at->second.lock();need(room&&room->ticket&&!room->failed,"PvE retained room unavailable");
    const auto peer=room->peers.find(s.id());need(peer!=room->peers.end()&&peer->second->session.get()==&s&&!peer->second->returned,"PvE actual Session object differs from retained owner");return room;
}
OwnedPveRoomTypes::PureCurrent OwnedPveRoomHost::current(const std::shared_ptr<Room>& room,std::optional<std::uint64_t> retired)const{
    // Own the readset across arbitrary providers. Retired cleanup grants only
    // the private room/member withdrawal CAS, never output or WORLD authority.
    std::vector<std::shared_ptr<Peer>> peers;for(const auto& [id,p]:room->peers){(void)id;peers.push_back(p);}
    return [this,room,peers=std::move(peers),retired]{
        if(thread_!=std::this_thread::get_id()||stopped_||room->failed||room->poisoned)return false;
        for(const auto& p:peers){if(p->returned||p->retired)continue;
            if(retired&&(*retired==p->binding.session_id()||p->session->closing())){
                if(!p->session->owned_pve_cleanup_current(p->binding))return false;continue;}
            if(p->prepared?!p->session->owned_pve_prepared_current(p->binding):!p->session->owned_pve_current(p->binding))return false;}
        return true;
    };
}
OwnedPveRoomHost::Ticket OwnedPveRoomHost::create(std::vector<std::shared_ptr<Session>> sessions,std::shared_ptr<const Sources> sources){
    need(thread_==std::this_thread::get_id()&&accepting_&&!stopped_&&!weak_from_this().expired(),"PvE host requires a live accepting shared GAME owner");
    if(creating_){creation_poisoned_=true;throw DatabaseError("PvE actual encounter creation reentered");}
    need(sources&&sources->member&&sources->project&&sources->rule&&sources->action&&sources->control&&sources->ai&&sources->return_world&&
        sources->encounter.members.empty()&&!sessions.empty()&&sessions.size()<=14,"PvE actual immutable provider set/count incomplete");
    creating_=true;creation_poisoned_=false;struct End{bool& v;~End(){v=false;}}end{creating_};
    auto room=std::make_shared<Room>();room->sources=std::move(sources);Operation operation(room);
    bool durable=false;
    try{
        for(auto& s:sessions){need(s&&!sessions_.contains(s->id())&&!room->peers.contains(s->id()),"PvE initial actual Session already retained");
            auto binding=s->prepare_owned_pve_entry();auto peer=std::make_shared<Peer>(s,binding);room->peers.emplace(s->id(),std::move(peer));}
        auto encounter=room->sources->encounter;
        // Sources see the progressively complete staged member list, including
        // reserved pair slots, before any SQL mutation. Not a mutable Battle.
        auto staged=std::make_shared<T::Snapshot>();
        auto pure=current(room);
        for(auto& [id,p]:room->peers){(void)id;auto m=room->sources->member(p->session,p->binding,staged);need(pure()&&!creation_poisoned_,"PvE initial source retired during provider");sourced(m,p->binding);p->identity=m.identity;
            T::Member member;member.input=m;staged->members.emplace(m.identity.character,std::move(member));encounter.members.push_back(std::move(m));}
        std::map<std::uint64_t,std::shared_ptr<Room>> room_node;room_node.emplace(0,room);auto node=room_node.extract(0);
        std::map<std::uint64_t,std::weak_ptr<Room>> session_nodes;for(const auto& [id,p]:room->peers){(void)p;session_nodes.emplace(id,room);}
        auto ticket=state_.create(std::move(encounter),room->sources->project,[&]{return pure()&&!creation_poisoned_;});durable=true;room->ticket=ticket;
        node.key()=ticket.id();rooms_.insert(std::move(node));
        while(!session_nodes.empty())sessions_.insert(session_nodes.extract(session_nodes.begin()));
        need(!state_.recovery_required(ticket)&&pure()&&!creation_poisoned_,"PvE durable creation source retired");
        for(auto& [id,p]:room->peers){(void)id;need(p->session->commit_owned_pve_entry(p->binding),"PvE durable entry could not bind its actual Session");p->prepared=false;}
        need(current(room)(),"PvE entry retired after actual binding");
        drain(room);return ticket;
    }catch(...){if(durable)fail(room);else for(auto& [id,p]:room->peers){(void)id;try{if(p->session->owned_pve_prepared_current(p->binding))p->session->abort_owned_pve_entry(p->binding);else p->session->close();}catch(...){p->session->close();}}throw;}
}
void OwnedPveRoomHost::support(std::shared_ptr<Session> session,RecoveredSosSupportRequest::Request request){
    need(session&&thread_==std::this_thread::get_id()&&accepting_&&!stopped_&&!sessions_.contains(session->id()),"PvE helper is not an eligible actual WORLD Session");
    auto binding=session->prepare_owned_pve_entry();auto peer=std::make_shared<Peer>(session,binding);bool durable=false;
    std::shared_ptr<Room> target;
    try{
        const auto entry=RecoveredWorldEntryView::read(binding.initialization().entry_frame());need(bool(entry),"PvE helper has no actual normal-entry scene witness");
        for(const auto& [id,room]:rooms_){(void)id;if(room->failed)continue;
            const auto snapshot=state_.inspect(*room->ticket);
            for(const auto& [sid,p]:room->peers){(void)sid;if(!p->retired&&!p->returned&&p->binding.channel()==binding.channel()&&
                p->identity.actor_handle==request.target&&p->session->owned_pve_current(p->binding)){
                const auto& member=snapshot->members.at(p->identity.character);
                if(member.status!=T::MemberStatus::Active||member.disconnected||member.return_context)continue;
                const auto& position=member.input.return_position;
                if(position.area!=entry->area||position.scene!=entry->scene)continue;
                need(!target||target==room,"PvE support native target is ambiguous in this actual channel/scene");target=room;}}}
        need(bool(target),"PvE support target is not an actual same-channel/scene shared-room member");Operation operation(target);
        auto before=state_.inspect(*target->ticket);auto input=target->sources->member(session,binding,before);sourced(input,binding);
        need(input.identity.actor_handle==request.self&&request.target&&input.identity.channel==target->peers.begin()->second->identity.channel,
            "PvE helper self/target/channel differs from actual retained WORLD handles");peer->identity=input.identity;
        // Preallocate publication nodes before the all-member transaction.
        std::map<std::uint64_t,std::shared_ptr<Peer>> peer_node;peer_node.emplace(session->id(),peer);
        std::map<std::uint64_t,std::weak_ptr<Room>> session_node;session_node.emplace(session->id(),target);
        const auto pure=current(target);const auto helper_current=[&,pure]{return pure()&&session->owned_pve_prepared_current(binding);};
        need(helper_current(),"PvE helper source retired during provider");
        state_.admit(*target->ticket,std::move(input),target->sources->project,helper_current);durable=true;target->progress.clear();
        target->peers.insert(peer_node.extract(peer_node.begin()));sessions_.insert(session_node.extract(session_node.begin()));
        need(!state_.recovery_required(*target->ticket)&&helper_current(),"PvE durable helper admission retired");
        need(session->commit_owned_pve_entry(binding),"PvE durable helper could not bind actual Session");peer->prepared=false;
        need(current(target)(),"PvE helper entry retired after actual binding");drain(target);
    }catch(...){if(durable)fail(target);else try{if(session->owned_pve_prepared_current(binding))session->abort_owned_pve_entry(binding);else session->close();}catch(...){session->close();}throw;}
}
bool OwnedPveRoomHost::handle(Session& session,std::span<const RecoveredWorldRecords::Record> records){
    if(!bound(session))return false;auto room=room_for(session);Operation operation(room);
    need(accepting_,"PvE dispatcher retired; only actual cleanup may persist");
    return process(room,session,records,true);
}
bool OwnedPveRoomHost::process(const std::shared_ptr<Room>& room,Session& session,
        std::span<const RecoveredWorldRecords::Record> records,bool allow_queue){
    auto peer=room->peers.at(session.id());need(!peer->retired&&current(room)(),"PvE bound source is retired");
    // Original context address stays borrowed only for Session's occurrence
    // check. All other request values are owned before provider/repository calls.
    std::optional<RecoveredBattleCommand::BasicAttackRequest> basic,control,timeout;
    std::optional<RecoveredSosBattleCommand::Request> support;
    std::optional<RecoveredBattleFleeCommand::Request> flee;
    const RecoveredWorldRecords::ContextNotification* context=nullptr;
    for(const auto& r:records){
        if(std::holds_alternative<RecoveredWorldRecords::Tick>(r)||std::holds_alternative<RecoveredWorldRecords::TimerNotification>(r))continue;
        if(const auto* p=std::get_if<RecoveredBattleCommand::BasicAttackRequest>(&r)){need(!basic&&!support&&!flee&&!timeout&&!context,"PvE batch contains multiple mutations");basic=*p;}
        else if(const auto* p=std::get_if<RecoveredSosBattleCommand::Request>(&r)){need(!basic&&!support&&!flee&&!timeout&&!context,"PvE batch contains multiple mutations");support=*p;}
        else if(const auto* p=std::get_if<RecoveredBattleFleeCommand::Request>(&r)){need(!basic&&!support&&!flee&&!timeout&&!context,"PvE batch contains multiple mutations");flee=*p;}
        else if(const auto* p=std::get_if<RecoveredBattleCommand::ControlRequest>(&r)){need(!control&&!context,"PvE batch repeats control");control=p->fields;}
        else if(const auto* p=std::get_if<RecoveredBattleCommand::Action2Request>(&r)){need(!basic&&!support&&!flee&&!timeout&&!context,"PvE batch contains multiple mutations");timeout=p->fields;}
        else if(const auto* p=std::get_if<RecoveredWorldRecords::ContextNotification>(&r)){need(!basic&&!support&&!flee&&!timeout&&!control&&!context,"PvE terminal context must be its own original mutation");context=p;}
        else throw DatabaseError("PvE bound batch has an unsupported native action; no prefix applied");
    }
    auto snapshot=state_.inspect(*room->ticket);const auto at=snapshot->members.find(peer->identity.character);
    need(at!=snapshot->members.end()&&at->second.input.identity==peer->identity&&!finalized(at->second),"PvE bound actual member no longer current");
    const auto member=at->second;const auto pure=current(room);
    if(!basic&&!support&&!flee&&!timeout&&!control&&!context)return true; // Heartbeat never occupies a command/progress queue slot.
    std::optional<BattleAction> action;
    bool target_gone=false;
    std::optional<Sources::ControlDecision> decision;
    if(basic){fields(*basic,member,*snapshot,true);action=room->sources->action(*snapshot,member,*basic);need(pure(),"PvE action source retired in provider");
        need(action->source==basic->actor_position,"PvE trusted action changed actual client-owned source");
        std::vector<std::uint8_t> targets;for(unsigned side=0;side<2;++side)for(unsigned bit=0;bit<14;++bit)if(basic->target_masks[side]&(1u<<bit))targets.push_back(std::uint8_t(side*14+bit));
        need(action->targets==targets&&!targets.empty(),"PvE trusted action changed/emptied requested current targets");
        target_gone=std::any_of(targets.begin(),targets.end(),[&](auto p){return !snapshot->checkpoint.snapshot.actors[p]->hp;});}
    if(control){fields(*control,member,*snapshot,false);const auto d=room->sources->control(*snapshot,member,false,*control);need(pure(),"PvE control source retired in provider");need(d==Sources::ControlDecision::ObserveOnly,"PvE 0B cannot grant/pass/ACK a turn");}
    if(timeout){fields(*timeout,member,*snapshot,true);decision=room->sources->control(*snapshot,member,true,*timeout);need(pure(),"PvE action2 policy source retired in provider");}
    if(support){need(support->side_flag()==(support->actor_position()==member.input.primary_slot?0:1)&&support->context()==member.input.command_context&&support->actor_position()<14&&
        (support->actor_position()==member.input.primary_slot||(member.input.pet&&support->actor_position()==member.input.pet->actor_slot)),"PvE SOS8 is not the actual owned actor/context");}
    if(flee){need(flee->side_flag()==(flee->actor_position()==member.input.primary_slot?0:1)&&flee->context()==member.input.command_context&&flee->actor_position()<14&&
        (flee->actor_position()==member.input.primary_slot||(member.input.pet&&flee->actor_position()==member.input.pet->actor_slot)),"PvE FLEE6 is not the actual owned actor/context");}
    const auto requested=basic?std::optional{basic->actor_position}:support?std::optional{support->actor_position()}:
        flee?std::optional{flee->actor_position()}:timeout&&decision==Sources::ControlDecision::Pass?std::optional{timeout->actor_position}:std::nullopt;
    if(requested){const auto slot=*requested;need(member.status==T::MemberStatus::Active&&!member.disconnected&&!member.return_context&&
        snapshot->checkpoint.snapshot.state==BattleState::Active&&slot<14&&snapshot->checkpoint.snapshot.actors[slot]&&snapshot->checkpoint.snapshot.actors[slot]->hp&&
        ((slot==member.input.primary_slot&&member.primary_grant)||(!member.primary_grant&&member.input.pet&&slot==member.input.pet->actor_slot&&member.secondary_grant)),
        "PvE request does not own this current living slot grant");}
    if(!context&&!state_.pending(*room->ticket).empty()){
        need(allow_queue&&room->queued.size()<room->peers.size()&&
            std::none_of(room->queued.begin(),room->queued.end(),[&](const auto& q){return q.peer==peer;}),
            "PvE fullwrite wait exceeds one queued native batch per actual member");
        room->queued.push_back({peer,member.grant_epoch,{records.begin(),records.end()}});return true;
    }
    try{
        if(context){
            need(member.status==T::MemberStatus::Withdrawn||snapshot->checkpoint.snapshot.state==BattleState::Finished,"PvE return has no durable terminal result");
            // Source produces fresh owned bytes before changing Session phase.
            const auto original=*context;auto logical=room->sources->return_world(peer->session,peer->binding,member.input,original);need(pure(),"PvE fresh return source retired");
            session.prepare_owned_pve_return(peer->binding,*context);peer->return_context=original.payload;
            state_.prepare_return(*room->ticket,peer->identity,std::move(logical),original.payload,current(room));
        }else if(action&&target_gone)state_.pass(*room->ticket,peer->identity,member.grant_epoch,action->source,room->sources->project,pure);
        else if(action)state_.act(*room->ticket,peer->identity,member.grant_epoch,std::move(*action),room->sources->rule,room->sources->project,pure);
        else if(support)state_.toggle_support(*room->ticket,peer->identity,member.grant_epoch,support->actor_position(),support->requested_flag()!=0,room->sources->project,pure);
        else if(flee)state_.withdraw(*room->ticket,peer->identity,false,room->sources->project,pure);
        else if(timeout&&decision==Sources::ControlDecision::Pass)state_.pass(*room->ticket,peer->identity,member.grant_epoch,timeout->actor_position,room->sources->project,pure);
        need(!state_.recovery_required(*room->ticket)&&current(room)(),"PvE durable command retired after commit");
        if(flee)room->progress.clear();
        if(control&&!basic&&!support&&!flee&&!timeout&&!context&&
            (room->cycle==Room::Cycle::AwaitPlayerProgress||room->cycle==Room::Cycle::AwaitAiProgress)&&
            member.status==T::MemberStatus::Active&&!member.return_context)
            room->progress.insert(session.id());
        drain(room);return true;
    }catch(...){if(state_.recovery_required(*room->ticket)||room->poisoned||peer->return_context)fail(room);throw;}
}
void OwnedPveRoomHost::drain(const std::shared_ptr<Room>& room){
    try{
    need(room->ticket&&current(room)(),"PvE drain source retired");const auto pending=state_.pending(*room->ticket);
    for(const auto& [sid,p]:room->peers){(void)sid;if(p->retired||p->returned||p->flight)continue;
        const auto at=std::find_if(pending.begin(),pending.end(),[&](const auto& d){return d.recipient==p->identity;});
        if(at==pending.end())continue;
        p->flight=at->sequence;
        const bool returning=at->kind==T::OutputKind::Return;
        const bool final_return=!returning||state_.inspect(*room->ticket)->members.at(p->identity.character).return_sequence==at->sequence;
        try{p->session->send_owned_pve_output(p->binding,at->sequence,at->logical,weak_from_this(),returning,final_return);}
        catch(...){fail(room);throw;}
    }
    if(pending.empty())advance(room);
    }catch(...){fail(room);throw;}
}
void OwnedPveRoomHost::advance(const std::shared_ptr<Room>& room){
    const auto pure=current(room);need(pure(),"PvE next-round source retired");auto snapshot=state_.inspect(*room->ticket);
    if(snapshot->closed){
        for(const auto& [id,p]:room->peers){(void)p;sessions_.erase(id);}
        state_.retire_closed(*room->ticket);rooms_.erase(room->ticket->id());return;
    }
    if(!accepting_)return; // Dispatch retirement preserves cleanup; never starts another AI/turn.
    if(snapshot->checkpoint.snapshot.state==BattleState::Active){
        const bool grants=std::any_of(snapshot->members.begin(),snapshot->members.end(),[](const auto& p){return p.second.primary_grant||p.second.secondary_grant;});
        if(!grants&&room->cycle==Room::Cycle::Player){room->cycle=Room::Cycle::AwaitPlayerProgress;room->progress.clear();}
        if(!grants&&room->cycle==Room::Cycle::Ai&&room->ai_remaining.empty()&&room->ai_emitted){room->cycle=Room::Cycle::AwaitAiProgress;room->progress.clear();}
    }
    while(!room->queued.empty()){
        auto queued=std::move(room->queued.front());room->queued.pop_front();
        const auto at=snapshot->members.find(queued.peer->identity.character);
        const bool observation=std::all_of(queued.records.begin(),queued.records.end(),[](const auto& r){return
            std::holds_alternative<RecoveredWorldRecords::Tick>(r)||std::holds_alternative<RecoveredWorldRecords::TimerNotification>(r)||
            std::holds_alternative<RecoveredBattleCommand::ControlRequest>(r);});
        if(queued.peer->retired||queued.peer->returned||at==snapshot->members.end()||
            finalized(at->second)||at->second.grant_epoch!=queued.grant_epoch||
            (!observation&&!at->second.primary_grant&&!at->second.secondary_grant))continue;
        bool stale=false;
        for(const auto& r:queued.records){std::optional<std::uint8_t> source;
            if(const auto* p=std::get_if<RecoveredBattleCommand::BasicAttackRequest>(&r)){
                source=p->actor_position;
            }else if(const auto* p=std::get_if<RecoveredSosBattleCommand::Request>(&r))source=p->actor_position();
            else if(const auto* p=std::get_if<RecoveredBattleFleeCommand::Request>(&r))source=p->actor_position();
            else if(const auto* p=std::get_if<RecoveredBattleCommand::Action2Request>(&r))source=p->fields.actor_position;
            if(source)stale=stale||*source>=28||!snapshot->checkpoint.snapshot.actors[*source]||!snapshot->checkpoint.snapshot.actors[*source]->hp;
        }
        // A previously valid actor can die in another member's committed
        // action. A dead target instead reaches the same explicit target-gone
        // pass policy as a retained whole Session input job.
        if(stale)continue;
        // No ContextNotification is ever copied/replayed here. This queue owns
        // only preclassified values and exact original-round member grants.
        process(room,*queued.peer->session,queued.records,false);return;
    }
    if(snapshot->checkpoint.snapshot.state==BattleState::Active){
        const bool granted=std::any_of(snapshot->members.begin(),snapshot->members.end(),[](const auto& pair){return pair.second.primary_grant||pair.second.secondary_grant;});
        if(!granted){
            if(room->cycle==Room::Cycle::Player){room->cycle=Room::Cycle::AwaitPlayerProgress;room->progress.clear();}
            const auto progressed=[&]{
                for(const auto& [id,m]:snapshot->members){(void)id;
                    const auto& actors=snapshot->checkpoint.snapshot.actors;
                    const bool living=(actors[m.input.primary_slot]&&actors[m.input.primary_slot]->hp)||
                        (m.input.pet&&actors[m.input.pet->actor_slot]&&actors[m.input.pet->actor_slot]->hp);
                    if(m.status==T::MemberStatus::Active&&!m.disconnected&&!m.return_context&&living&&
                       !room->progress.contains(m.input.identity.session))return false;}
                return true;
            };
            if(room->cycle==Room::Cycle::AwaitPlayerProgress&&progressed()){
                room->cycle=Room::Cycle::Ai;room->progress.clear();room->ai_remaining.clear();room->ai_emitted=false;
                for(std::uint8_t p=14;p<28;++p)if(snapshot->checkpoint.snapshot.actors[p]&&snapshot->checkpoint.snapshot.actors[p]->hp)room->ai_remaining.push_back(p);
            }
            while(room->cycle==Room::Cycle::Ai&&!room->ai_remaining.empty()){
                const auto position=room->ai_remaining.front();snapshot=state_.inspect(*room->ticket);
                if(snapshot->checkpoint.snapshot.state!=BattleState::Active)break;
                auto action=room->sources->ai(*snapshot,position);need(pure(),"PvE AI provider retired source");
                if(action){need(action->source==position,"PvE AI policy cannot substitute another enemy actor");state_.act_ai(*room->ticket,std::move(*action),room->sources->rule,room->sources->project,pure);room->ai_emitted=true;}
                room->ai_remaining.erase(room->ai_remaining.begin());
                need(!state_.recovery_required(*room->ticket)&&pure(),"PvE durable AI retired after commit");
                if(action){drain(room);return;}
            }
            snapshot=state_.inspect(*room->ticket);
            if(snapshot->checkpoint.snapshot.state==BattleState::Active&&room->cycle==Room::Cycle::Ai&&room->ai_remaining.empty()){
                if(!room->ai_emitted){ // Explicit CUSTOM empty-AI policy: no new client animation can produce a second progress report.
                    room->cycle=Room::Cycle::Player;room->progress.clear();state_.grant_round(*room->ticket,room->sources->project,pure,true);drain(room);return;
                }
                room->cycle=Room::Cycle::AwaitAiProgress;room->progress.clear();
            }else if(snapshot->checkpoint.snapshot.state==BattleState::Active&&room->cycle==Room::Cycle::AwaitAiProgress&&progressed()){
                room->cycle=Room::Cycle::Player;room->progress.clear();state_.grant_round(*room->ticket,room->sources->project,pure,true);drain(room);return;
            }
        }
    }
    // Whole-room outbox drained, not a timer or client control notification.
    for(const auto& [sid,p]:room->peers){(void)sid;if(!p->retired&&!p->returned&&!p->return_context)p->session->release_owned_pve_input(p->binding);}
}
void OwnedPveRoomHost::owned_pve_written(Session& session,const Binding& binding,std::uint64_t sequence,bool success){
    if(!bound(session))return; // Once-retired flight cannot renew an owner.
    auto room=room_for(session);Operation operation(room);const auto peer=room->peers.at(session.id());
    need(peer->binding.same_binding(binding)&&peer->flight==sequence,"PvE Written callback does not own retained exact output");
    try{
        if(!success){cleanup(room,session.id());drain(room);return;}
        state_.written(*room->ticket,sequence,peer->identity,true,current(room,0));peer->flight.reset();
        need(!state_.recovery_required(*room->ticket),"PvE durable receipt retired after commit");
        const auto closing=std::find_if(room->peers.begin(),room->peers.end(),[](const auto& item){return !item.second->retired&&!item.second->returned&&item.second->session->closing();});
        if(closing!=room->peers.end())cleanup(room,closing->first);
        if(peer->retired){drain(room);return;}
        if(peer->return_context&&state_.inspect(*room->ticket)->members.at(peer->identity.character).return_sequence==sequence){
            state_.complete_return(*room->ticket,peer->identity,*peer->return_context,current(room));
            need(!state_.recovery_required(*room->ticket),"PvE durable individual return retired after commit");
            if(!session.complete_owned_pve_return(binding)){session.close();throw DatabaseError("PvE durable return could not renew actual WORLD owner");}
            peer->returned=true;sessions_.erase(session.id());
            try{
                if(room->sources->returned){const auto saved=state_.inspect(*room->ticket)->members.at(peer->identity.character).input;
                    room->sources->returned(peer->session,peer->binding,saved);}
                session.resume_owned_pve_return_input(binding);
            }catch(...){session.close();throw;}
        }
        drain(room);
    }catch(...){fail(room);throw;}
}
void OwnedPveRoomHost::disconnected(Session& session){
    if(!bound(session))return;auto room=room_for(session);Operation operation(room);auto peer=room->peers.at(session.id());
    if(peer->retired||peer->returned)return;
    try{cleanup(room,session.id());drain(room);
    }catch(...){fail(room);throw;}
}
void OwnedPveRoomHost::cleanup(const std::shared_ptr<Room>& room,std::uint64_t triggering){
    std::vector<T::Identity> identities;std::vector<std::shared_ptr<Peer>> retiring;
    for(const auto& [id,p]:room->peers)if(!p->returned&&!p->retired&&(id==triggering||p->session->closing())){
        need(p->session->owned_pve_cleanup_current(p->binding),"PvE cleanup lost the actual private retained binding");
        identities.push_back(p->identity);retiring.push_back(p);
    }
    need(!retiring.empty(),"PvE actual disconnect cleanup has no retained member");
    const auto source=current(room,triggering);
    // Source permits only exact private cleanup witnesses for concurrently
    // closing peers, not an entry/action/output grant or relabelled new owner.
    const auto pure=[this,room,source,retiring]{if(!source())return false;
        for(const auto& p:retiring)if(!p->session->owned_pve_cleanup_current(p->binding))return false;return true;};
    for(const auto& p:retiring)p->retired=true;
    state_.retire_disconnected(*room->ticket,std::move(identities),room->sources->project,pure);
    need(!state_.recovery_required(*room->ticket),"PvE durable private cleanup retired during commit");
    for(const auto& p:retiring){p->flight.reset();sessions_.erase(p->identity.session);}
    room->progress.clear();
}
void OwnedPveRoomHost::retire_dispatch()noexcept{accepting_=false;creation_poisoned_=true;}
void OwnedPveRoomHost::fail(const std::shared_ptr<Room>& room)noexcept{
    room->failed=true;room->poisoned=true;
    // Claims/checkpoint/outbox remain durable. Closing sockets is not rollback,
    // an automatic resumption grant, or proof of a returned world scene.
    for(const auto& [id,p]:room->peers){(void)id;if(!p->returned)try{p->session->close();}catch(...) {}}
}
void OwnedPveRoomHost::stop()noexcept{
    if(stopped_)return;accepting_=false;stopped_=true;creation_poisoned_=true;state_.stop();
    for(const auto& [id,room]:rooms_){(void)id;fail(room);}
}
}
