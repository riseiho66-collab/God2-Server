#include "relations53/SharedGuildChannelDirectory53.h"
#include "game/OwnedTaiwanGuildChatDispatch.h"
#include <array>
#include <map>
#include <stdexcept>
#include <thread>

namespace {
using namespace god2;
using Directory=SharedGuildChannelDirectory53;
using Owner=Directory::Owner;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> bool refuses(F&& f){try{f();}catch(const std::exception&){return true;}return false;}
// These are real Session objects with explicitly synthetic public scalar state.
// No login, native world-ready output, private receipt, membership or SQL grant
// is claimed. The tests exercise routing/callback custody, not Common53 rules.
struct Fixture {
    asio::io_context game;
    struct Channel {
        std::map<std::uint64_t,std::shared_ptr<Session>> peers;
        std::map<std::uint64_t,Owner> owners;
        std::vector<Directory::Host::Live> rows;
        std::set<std::uint64_t> closed;
        std::set<std::uint32_t> online;
        std::map<std::uint64_t,Directory::Chat::Peer> chat_peers;
        std::vector<std::pair<std::shared_ptr<Session>,std::vector<std::uint8_t>>> chats;
        unsigned ready=0,sends=0,baselines=0,names=0,closed_calls=0;
        unsigned chat_reads=0,owner_reads=0;
        std::function<void()> on_ready,on_send,on_baseline,on_enumerate,on_name;
        std::function<void()> on_chat_peer,on_chat_send;
        std::function<void(bool)> held_ack;
        bool async=false,throw_send=false,null_baseline=false,throw_chat=false;
    };
    std::array<Channel,3> channels;
    std::shared_ptr<Directory> directory=Directory::create();
    Directory::Binding binding=directory->binding();
    Owner add(std::uint8_t k,std::uint64_t id,std::uint64_t character,bool permitted=true){
        auto& c=channels[k];auto peer=std::make_shared<Session>(asio::ip::tcp::socket(game),game.get_executor(),id,false,Session::PacketHandler{},Session::DisconnectHandler{});
        peer->account_id=0x800000001ULL+k;peer->character_id=character;peer->set_state(SessionState::InWorld);
        Owner owner{id,peer->account_id,character,9,7,2,100,200,950,4,11};
        c.peers[id]=peer;c.owners[id]=owner;c.rows.push_back({id,owner.account,character,permitted});return owner;
    }
    Directory::Source source(std::uint8_t k){
        auto& c=channels[k];Directory::Source s;
        s.session=[&c](auto id){const auto at=c.peers.find(id);return at==c.peers.end()?std::shared_ptr<Session>{}:at->second;};
        s.enumerate=[&c]{if(c.on_enumerate)c.on_enumerate();return c.rows;};
        s.owner=[&c](auto id)->std::optional<Owner>{++c.owner_reads;const auto at=c.owners.find(id);return at==c.owners.end()?std::nullopt:std::optional{at->second};};
        s.peer_ready=[&c](const Owner&){++c.ready;if(c.on_ready)c.on_ready();return true;};s.recipient_ready=s.peer_ready;
        s.closed=[&c](const Owner& value){++c.closed_calls;return c.closed.contains(value.session);};
        s.send=[&c](const Owner&,auto,std::function<void(bool)> ack){++c.sends;if(c.async)c.held_ack=ack;else{ack(true);ack(true);}if(c.on_send)c.on_send();if(c.throw_send)throw std::runtime_error("Synthetic send failure");};
        s.baseline=[&c](const Owner& value)->std::optional<Directory::Common::Baseline>{++c.baselines;if(c.on_baseline)c.on_baseline();if(c.null_baseline)return {};return Directory::Common::Baseline{value,{},false};};
        s.online=[&c]{return c.online;};s.sync_name=[&c](const Owner&){++c.names;if(c.on_name)c.on_name();};
        s.chat_peer=[&c](auto id)->std::optional<Directory::Chat::Peer>{++c.chat_reads;if(c.on_chat_peer)c.on_chat_peer();const auto at=c.chat_peers.find(id);return at==c.chat_peers.end()?std::nullopt:std::optional{at->second};};
        s.chat_send=[&c](const std::shared_ptr<Session>& peer,auto logical){const auto at=c.peers.find(peer->id());if(at==c.peers.end()||at->second!=peer||peer->closing())throw std::runtime_error("Synthetic chat peer no longer local");c.chats.emplace_back(peer,std::move(logical));if(c.on_chat_send)c.on_chat_send();if(c.throw_chat)throw std::runtime_error("Synthetic chat enqueue exception");};
        return s;
    }
    void seal(){for(std::uint8_t k=0;k<3;++k)directory->install(k,source(k));directory->seal();}
    ~Fixture(){directory->retire();}
};
void routing_and_identity(){
    Fixture f;const auto a=f.add(0,0x100000001ULL,0x300000001ULL),b=f.add(1,0x200000001ULL,0x400000001ULL),c=f.add(2,0x300000001ULL,0x500000001ULL,false);
    f.channels[0].online={17};f.channels[1].online={18};f.channels[2].online={17,19};
    require(refuses([&]{(void)f.binding.enumerate();}),"Unsealed topology cannot masquerade as everyone offline");f.seal();
    const auto rows=f.binding.enumerate();require(rows.size()==3&&!rows.back().permitted_state,"Enumeration includes unpermitted live peer");
    require(f.binding.owner(a.session)==a&&f.binding.owner(b.session)==b&&!f.binding.owner(c.session),"Exact full64 owner route");
    require(f.channels[0].ready+f.channels[1].ready+f.channels[2].ready==0,"Pure owner and enumeration invoke no peer projection");
    f.channels[0].peers[a.session]->set_state(SessionState::CharacterSelected);require(f.binding.owner(a.session)==a&&f.binding.recipient_ready(a),"Actual ready entry tail may remain CharacterSelected");
    f.channels[0].peers[a.session]->set_state(SessionState::InWorld);f.channels[0].ready=0;
    require(f.binding.peer_ready(b)&&f.channels[1].ready==1&&f.channels[0].ready==0,"Readiness routes exact issuer");
    auto wrong=b;++wrong.position_revision;require(!f.binding.recipient_ready(wrong),"Whole Owner required");
    require(f.binding.online()==std::set<std::uint32_t>({17,18,19}),"Online union keeps supplied native32 IDs without truncating full64 identities");
    f.binding.sync_name(b);require(f.channels[1].names==1&&f.channels[0].names==0,"Name projection selects actual owner channel");
    const auto baseline=f.binding.baseline(a);require(baseline&&baseline->recipient==a&&f.channels[0].baselines==1,"Baseline exact issuer");
    unsigned acknowledgements=0;bool accepted=false;
    f.binding.send(b,{0x91},[&](bool good){++acknowledgements;accepted=good;require(f.binding.owner(a.session)==a,"Synchronous ACK permits legitimate nested resolve");});
    require(accepted&&acknowledgements==1&&f.channels[1].sends==1,"Exact send deduplicates ACK");
    f.channels[2].peers[a.session]=f.channels[0].peers[a.session];
    require(refuses([&]{(void)f.binding.enumerate();})&&!f.binding.owner(a.session),"Hidden duplicate source pointer refuses whole topology");f.channels[2].peers.erase(a.session);
    f.channels[2].rows.push_back(f.channels[0].rows.front());require(refuses([&]{(void)f.binding.enumerate();}),"Duplicate full64 session refuses, never silently deduplicates");f.channels[2].rows.pop_back();
    const auto old=f.channels[2].rows.front().character;f.channels[2].rows.front().character=a.character;
    require(refuses([&]{(void)f.binding.enumerate();}),"Mismatched identity refuses even unpermitted row");f.channels[2].rows.front().character=old;
    f.channels[2].rows.front().character=a.character;f.channels[2].peers[c.session]->character_id=a.character;f.channels[2].owners[c.session].character=a.character;
    require(refuses([&]{(void)f.binding.enumerate();}),"Two matching actual peers cannot advertise the same full64 character");
    f.channels[2].rows.front().character=old;f.channels[2].peers[c.session]->character_id=old;f.channels[2].owners[c.session]=c;
    f.channels[0].peers[a.session]->account_id++;require(!f.binding.owner(a.session),"High64 actual Session identity must agree");f.channels[0].peers[a.session]->account_id--;
    f.channels[2].on_enumerate=[&]{++f.channels[0].peers[a.session]->account_id;};
    require(refuses([&]{(void)f.binding.enumerate();}),"Later supplier cannot mutate previously captured actual Session");f.channels[2].on_enumerate={};--f.channels[0].peers[a.session]->account_id;
    require(refuses([&]{f.directory->install(0,f.source(0));}),"Sealed source replacement refused");
    require(f.channels[0].chat_reads+f.channels[1].chat_reads+f.channels[2].chat_reads==0,"Common53 pure and readiness routes never observe chat membership");
}
void closure_and_reentry(){
    Fixture f;const auto owner=f.add(1,0x100000005ULL,0x900000003ULL);f.seal();
    f.channels[1].closed.insert(owner.session);require(!f.binding.closed(owner),"Closed claim cannot override live Session");
    f.channels[1].peers.clear();f.channels[1].rows.clear();require(f.binding.closed(owner),"Exactly one supplied exact retired claim");
    require(f.channels[0].closed_calls&&f.channels[1].closed_calls&&f.channels[2].closed_calls,"Closed probes all issuers");
    f.channels[2].closed.insert(owner.session);require(!f.binding.closed(owner),"Ambiguous retired claims refused");f.channels[2].closed.clear();f.channels[1].closed.clear();
    require(!f.binding.closed(owner),"No supplier claim is not closed evidence");
    Fixture g;const auto current=g.add(0,0x100000002ULL,0x800000002ULL);g.seal();
    g.channels[0].on_ready=[&]{++g.channels[0].owners[current.session].position_revision;};require(!g.binding.peer_ready(current),"Readiness observer cannot retain stale Owner");
    g.channels[0].owners[current.session]=current;g.channels[0].on_ready={};
    g.channels[0].on_baseline=[&]{g.binding.sync_name(current);};require(g.binding.baseline(current).has_value(),"Baseline can synchronously reenter projection routing");
    g.channels[0].null_baseline=true;require(!g.binding.baseline(current)&&g.channels[0].names==2,"Baseline may trigger original async bootstrap and return no evidence");
    g.channels[0].on_send=[&]{++g.channels[0].owners[current.session].position_revision;};unsigned calls=0;bool good=true;
    g.binding.send(current,{1},[&](bool value){++calls;good=value;});require(calls==1&&!good,"Synchronous positive deferred until post-supplier owner fence");
    g.channels[0].owners[current.session]=current;g.channels[0].on_send={};g.channels[0].async=true;
    g.binding.send(current,{2},[&](bool value){++calls;good=value;});require(calls==1,"Async ACK remains pending");
    auto old=g.channels[0].peers[current.session];auto replacement=std::make_shared<Session>(asio::ip::tcp::socket(g.game),g.game.get_executor(),current.session,false,Session::PacketHandler{},Session::DisconnectHandler{});
    replacement->account_id=current.account;replacement->character_id=current.character;replacement->set_state(SessionState::InWorld);g.channels[0].peers[current.session]=replacement;
    g.channels[0].held_ack(true);g.channels[0].held_ack(true);require(calls==2&&!good,"Same full scalar identity cannot replace original Session pointer");
    g.channels[0].peers[current.session]=old;g.channels[0].async=false;g.channels[0].throw_send=true;
    require(refuses([&]{g.binding.send(current,{3},[&](bool value){++calls;good=value;});})&&calls==3&&!good,"Throw after synchronous positive ACK is one refusal");
}
void retirement_and_thread(){
    {
        Fixture reentrant;const auto owner=reentrant.add(0,0x700000009ULL,0x600000009ULL);reentrant.seal();unsigned calls=0;bool good=true;
        reentrant.channels[0].on_send=[&]{reentrant.directory->retire();};
        reentrant.binding.send(owner,{8},[&](bool accepted){++calls;good=accepted;});
        require(calls==1&&!good,"Supplier retirement cannot publish its deferred positive ACK");
    }
    Fixture f;const auto owner=f.add(2,0x700000001ULL,0x600000001ULL);f.seal();f.channels[2].async=true;
    unsigned calls=0;bool good=true;f.binding.send(owner,{9},[&](bool accepted){++calls;good=accepted;});
    f.directory->retire();f.directory->retire();f.channels[2].held_ack(true);require(calls==1&&!good,"Retirement revokes pending ACK and is idempotent");
    require(!f.binding.owner(owner.session)&&!f.binding.peer_ready(owner)&&!f.binding.closed(owner),"Retired facades grant no authority");
    require(refuses([&]{(void)f.binding.enumerate();})&&refuses([&]{(void)f.binding.online();}),"Retired enumeration cannot imply all offline");
    bool foreign=false;std::thread worker([&]{foreign=refuses([&]{(void)f.binding.owner(owner.session);});});worker.join();require(foreign,"Wrong-thread facade refuses before weak lock");
    require(refuses([]{(void)Directory::create(2);}),"Exactly three channels required");
    auto unsealed=Directory::create();require(refuses([&]{unsealed->seal();}),"All three sources mandatory");
    auto incomplete=f.source(0);incomplete.sync_name={};require(refuses([&]{unsealed->install(0,incomplete);}),"Every supplied callback mandatory");
}
struct ChatFixture:Fixture {
    std::array<Owner,3> owners;
    std::array<RecoveredGuildChat::Request,1> requests{RecoveredGuildChat::Request{{3,0xa5,0,0},"guild"}};
    ChatFixture(){
        for(std::uint8_t k=0;k<3;++k){
            const auto actor=std::uint32_t{11}+k;owners[k]=add(k,0x100000001ULL+0x100000000ULL*k,actor,k!=2);
            channels[k].chat_peers.emplace(owners[k].session,Directory::Chat::Peer{{owners[k].session,owners[k].account,actor,"Player"+std::to_string(k),true,k==1,0},{77,"SyntheticGuild",5,std::uint64_t{8}+k}});
        }
        // Actual public phase change supplies a battle generation. The native
        // ready bit is not forged; these explicit synthetic source callbacks
        // exercise directory policy only, not native gameplay entitlement.
        channels[2].peers[owners[2].session]->set_state(SessionState::InBattle);seal();
    }
    static Directory::Chat::Prepare renderer(){return [](const auto& sender,const auto& recipient,const auto& request){return RecoveredGuildChat::display(sender.actor.character,recipient.actor.simplified,sender.actor.name+": "+request.legacy_text);};}
    auto prepare(){return directory->prepare_chat(owners[0].session,requests,renderer());}
    unsigned submitted()const{return static_cast<unsigned>(channels[0].chats.size()+channels[1].chats.size()+channels[2].chats.size());}
};
void chat_routing_and_one_use(){
    ChatFixture f;auto batch=f.prepare();require(batch.has_value(),"Global guild chat prepares across three supplied worlds");
    require(f.channels[0].owner_reads+f.channels[1].owner_reads+f.channels[2].owner_reads==0&&f.channels[0].ready+f.channels[1].ready+f.channels[2].ready==0,"Chat does not borrow Common53 owner/readiness policy that excludes battle");
    unsigned echoes=0;std::vector<std::uint8_t> self;
    const auto result=f.directory->dispatch_chat(*batch,[&](auto bytes){++echoes;self=std::move(bytes);});
    require(result.complete&&result.submitted==3&&echoes==1&&f.channels[0].chats.empty()&&f.channels[1].chats.size()==1&&f.channels[2].chats.size()==1,"Self echo only original sender, cross-world sends include eligible battle row");
    require(self[0]==0x5c&&self[9]==3&&f.channels[1].chats.front().second[9]==0x83,"Existing guild display validation preserves recipient selector/codepage");
    const auto repeated=f.directory->dispatch_chat(*batch);require(!repeated.complete&&repeated.submitted==0,"Opaque ticket is consumed once");
    auto next=f.prepare();require(next.has_value(),"Independent later request can prepare");auto moved=std::move(*next);
    require(!f.directory->dispatch_chat(*next).complete&&f.directory->dispatch_chat(moved).complete,"Moved-from ticket has no dispatch authority");
    ChatFixture foreign;auto original=foreign.prepare();require(original.has_value()&&!f.directory->dispatch_chat(*original).complete&&foreign.directory->dispatch_chat(*original).complete,"Foreign directory cannot consume or dispatch original issuer ticket");
    ChatFixture other_guild;other_guild.channels[1].chat_peers.at(other_guild.owners[1].session).membership.guild_id=99;
    auto audience=other_guild.prepare();require(audience.has_value(),"Other-guild source remains globally observed");
    const auto scoped=other_guild.directory->dispatch_chat(*audience);require(scoped.complete&&scoped.submitted==2&&other_guild.channels[1].chats.empty(),"Native guild service prevents cross-guild leak");
}
void chat_freshness_and_partial_delivery(){
    ChatFixture f;auto batch=f.prepare();require(batch.has_value(),"Initial chat prepared");
    ++f.channels[1].chat_peers.at(f.owners[1].session).membership.membership_revision;
    require(!f.directory->dispatch_chat(*batch).complete&&f.submitted()==0,"Changed membership refuses before first submission");
    auto phase=f.prepare();require(phase.has_value(),"Refreshed chat prepared");
    f.channels[2].peers[f.owners[2].session]->set_state(SessionState::InWorld);f.channels[2].peers[f.owners[2].session]->set_state(SessionState::InBattle);
    require(!f.directory->dispatch_chat(*phase).complete&&f.submitted()==0,"Battle out-and-back generation cannot reuse original batch");
    auto identity=f.prepare();require(identity.has_value(),"Current battle source prepares");
    const auto previous=f.channels[1].peers[f.owners[1].session];auto replacement=std::make_shared<Session>(asio::ip::tcp::socket(f.game),f.game.get_executor(),previous->id(),false,Session::PacketHandler{},Session::DisconnectHandler{});
    replacement->account_id=previous->account_id;replacement->character_id=previous->character_id;replacement->set_state(previous->state());f.channels[1].peers[previous->id()]=replacement;
    require(!f.directory->dispatch_chat(*identity).complete&&f.submitted()==0,"Same full scalar identity with replacement pointer refuses");
    f.channels[1].peers[previous->id()]=previous;
    auto partial=f.prepare();require(partial.has_value(),"Partial-delivery fixture prepares");
    f.channels[0].on_chat_send=[&]{++f.channels[1].chat_peers.at(f.owners[1].session).membership.membership_revision;};
    const auto result=f.directory->dispatch_chat(*partial);require(!result.complete&&result.submitted==1&&f.submitted()==1,"Late membership change stops remainder, retains returned enqueue count");
    require(!f.directory->dispatch_chat(*partial).complete&&f.submitted()==1,"Partial attempt cannot replay already submitted prefix");
    ChatFixture throwing;auto failed=throwing.prepare();require(failed.has_value(),"Throwing-send fixture prepares");throwing.channels[0].throw_chat=true;
    const auto thrown=throwing.directory->dispatch_chat(*failed);require(!thrown.complete&&thrown.submitted==0&&throwing.submitted()==1,"Throwing callback is not reported returned/accepted even if it recorded an attempt");
    ChatFixture echo;auto echo_batch=echo.prepare();require(echo_batch.has_value(),"Throwing-echo fixture prepares");
    const auto echo_result=echo.directory->dispatch_chat(*echo_batch,[](auto){throw std::runtime_error("Synthetic echo allocation failure");});
    require(!echo_result.complete&&echo_result.submitted==0&&echo.submitted()==0,"Echo exception stops chat without throwing through movement caller");
}
void chat_renderer_reentry_and_retirement(){
    ChatFixture f;bool entered=false,nested_refused=false;
    auto reentrant=f.directory->prepare_chat(f.owners[0].session,f.requests,[&](const auto& sender,const auto& recipient,const auto& request){
        entered=true;nested_refused=!f.prepare();return ChatFixture::renderer()(sender,recipient,request);
    });
    require(entered&&nested_refused&&!reentrant&&f.submitted()==0,"Caught renderer reentry invalidates entire pending preparation");
    auto batch=f.prepare();require(batch.has_value(),"Clean preparation after refused reentry");
    f.channels[0].on_chat_send=[&]{require(!f.directory->dispatch_chat(*batch).complete,"Nested consumed dispatch refuses");};
    const auto result=f.directory->dispatch_chat(*batch);require(!result.complete&&result.submitted==1&&f.submitted()==1,"Caught dispatch reentry invalidates remaining batch");
    ChatFixture retired;auto before=retired.prepare();require(before.has_value(),"Retire fixture prepares");retired.directory->retire();
    require(!retired.directory->dispatch_chat(*before).complete&&retired.submitted()==0&&!retired.prepare(),"Retirement revokes all pending chat tickets");
    ChatFixture late_retire;auto late=late_retire.prepare();require(late.has_value(),"In-callback retire fixture prepares");late_retire.channels[0].on_chat_send=[&]{late_retire.directory->retire();};
    const auto retired_result=late_retire.directory->dispatch_chat(*late);require(!retired_result.complete&&retired_result.submitted==1&&late_retire.submitted()==1,"Retiring supplier preserves submitted prefix and refuses remaining worlds");
    ChatFixture render_change;const auto invalid=render_change.directory->prepare_chat(render_change.owners[0].session,render_change.requests,[&](const auto& sender,const auto& recipient,const auto& request){
        ++render_change.channels[2].chat_peers.at(render_change.owners[2].session).membership.membership_revision;return ChatFixture::renderer()(sender,recipient,request);
    });require(!invalid&&render_change.submitted()==0,"Renderer changing distant world membership cannot mint ticket");
    ChatFixture mismatch;mismatch.channels[0].peers[mismatch.owners[0].session]->character_id=0x10000000bULL;mismatch.channels[0].rows[0].character=0x10000000bULL;
    require(!mismatch.prepare(),"Full64 character may not silently truncate into native32 peer projection");
    ChatFixture malformed;auto bad=malformed.directory->prepare_chat(malformed.owners[0].session,malformed.requests,[](const auto& sender,const auto& recipient,const auto& request){return RecoveredChat::display(sender.actor.character,recipient.actor.simplified,request.legacy_text);});
    require(!bad,"Original chat validator still rejects non-guild 5C selector");
    ChatFixture actor_mismatch;++actor_mismatch.channels[1].chat_peers.at(actor_mismatch.owners[1].session).actor.account;
    require(!actor_mismatch.prepare(),"Source chat actor must match actual full64 Session account");
    bool foreign=false;std::thread worker([&]{foreign=refuses([&]{(void)malformed.prepare();});});worker.join();require(foreign,"Chat checks GAME before source callbacks");
}
void native_holder_invalidation_stops_actual_directory_batch(){
    ChatFixture f;
    struct Observation {Directory::ChatDispatch result;unsigned invalidations=0;bool supplier_observed=false;};
    const auto observation=std::make_shared<Observation>();const auto holder=OwnedTaiwanGuildChatDispatch::create();const auto binding=holder->binding();
    holder->install([directory=f.directory,observation](Session& sender,std::span<const RecoveredGuildChat::Request> requests)->std::optional<SharedTaiwanWorldRecordSource::Reply>{
        auto batch=directory->prepare_chat(sender.id(),requests,ChatFixture::renderer());if(!batch)return SharedTaiwanWorldRecordSource::Reply::no_reply();
        observation->result=directory->dispatch_chat(*batch);return SharedTaiwanWorldRecordSource::Reply::no_reply();
    },[directory=f.directory,observation]{++observation->invalidations;directory->invalidate_chat();});
    f.channels[0].on_chat_send=[binding,observation]{binding.invalidate_active();observation->supplier_observed=observation->invalidations==1;};
    const auto result=binding.dispatch(*f.channels[0].peers[f.owners[0].session],f.requests);
    require(!result&&observation->supplier_observed&&observation->invalidations==1,"Native owner cancellation reaches directory before send supplier returns");
    require(!observation->result.complete&&observation->result.submitted==1&&f.channels[0].chats.size()==1&&f.channels[1].chats.empty()&&f.channels[2].chats.empty(),"Actual directory stops before later worlds after caught outer native invalidation");
    holder->stop();f.directory->retire();f.directory->invalidate_chat();
}
void action_observer_cancellation_and_successor(){
    for(unsigned mode=0;mode<3;++mode){
        Fixture f;const auto owner=f.add(1,0x100000011ULL,0x900000011ULL);f.seal();
        auto action=f.directory->begin_action();const auto live=f.directory->action_liveness();
        bool observed=false,nested_refused=false;
        const auto cancel=[&]{
            if(mode==2)nested_refused=refuses([&]{(void)f.directory->begin_action();});else action.invalidate();
            observed=!live->load()&&!action.current()&&!f.directory->action_permitted();
        };
        if(mode==0){f.channels[1].on_ready=cancel;require(!f.binding.peer_ready(owner),"Cancellation inside ready observer refuses its positive result");}
        if(mode==1){f.channels[1].on_baseline=cancel;require(!f.binding.baseline(owner),"Cancellation inside baseline observer refuses its returned evidence");}
        if(mode==2){f.channels[1].on_name=cancel;require(refuses([&]{f.binding.sync_name(owner);}),"Caught nested action invalidates name observer continuation");}
        require(observed&&(mode!=2||nested_refused),"Action observer sees cancellation synchronously before returning");
        if(mode==0)require(refuses([&]{action.finish(true);}),"Cancelled scope cannot claim handler acceptance");
        action.finish(false);require(f.directory->action_permitted(),"Failed handler clears active pointer without retaining global cancellation");
        auto next=f.directory->begin_action();const auto next_live=f.directory->action_liveness();
        action.invalidate();action.finish(false);
        require(next.current()&&next_live->load()&&f.directory->action_permitted(),"Old finished action cannot cancel or clear actual successor");
        next.finish(true);
    }
}
void action_delayed_ack_after_handler_end(){
    for(bool accepted:{false,true}){
        Fixture f;const auto owner=f.add(0,0x100000012ULL,0x900000012ULL);f.seal();f.channels[0].async=true;
        auto action=f.directory->begin_action();const auto live=f.directory->action_liveness();
        unsigned calls=0;bool good=!accepted,inherited=false;
        f.binding.send(owner,{0x91},[&](bool value){
            ++calls;good=value;inherited=f.directory->action_liveness()==live;
            require(f.directory->action_permitted()==accepted,"Delayed ACK inherits accepted or cancelled origin after active pointer cleared");
            require(f.binding.owner(owner.session).has_value()==accepted,"Cancelled delayed continuation cannot recover fresh owner authority");
        });
        require(calls==0&&action.current(),"Actual async source retains unresolved ACK during handler");
        const auto ack=f.channels[0].held_ack;action.finish(accepted);
        require(!action.current()&&f.directory->action_permitted()&&live->load()==accepted,"Handler finish clears active pointer but preserves exact origin liveness");
        ack(true);ack(true);
        require(calls==1&&good==accepted&&inherited,"Handler acceptance permits one delayed ACK; failed handler refuses positive supplier ACK");
    }
    Fixture abandoned;const auto owner=abandoned.add(2,0x100000013ULL,0x900000013ULL);abandoned.seal();abandoned.channels[2].async=true;
    unsigned calls=0;bool good=true;std::shared_ptr<const std::atomic_bool> live;
    {auto action=abandoned.directory->begin_action();live=abandoned.directory->action_liveness();
        abandoned.binding.send(owner,{0x92},[&](bool accepted){++calls;good=accepted;});}
    require(!live->load()&&abandoned.directory->action_permitted(),"Abandoning scope cancels its own origin and clears active pointer");
    abandoned.channels[2].held_ack(true);require(calls==1&&!good,"Abandoned handler cannot later publish positive ACK");
}
void action_chained_ack_inherits_original_scope(){
    Fixture f;const auto owner=f.add(0,0x100000014ULL,0x900000014ULL);f.seal();f.channels[0].async=true;
    auto action=f.directory->begin_action();const auto original_live=f.directory->action_liveness();
    unsigned first=0,second=0;bool first_good=false,second_good=true,second_inherited=false;
    f.binding.send(owner,{0x93},[&](bool accepted){
        ++first;first_good=accepted;
        require(accepted&&f.directory->action_liveness()==original_live,"First delayed chunk inherits original accepted action");
        f.binding.send(owner,{0x94},[&](bool chained){
            ++second;second_good=chained;second_inherited=f.directory->action_liveness()==original_live;
            require(!f.directory->action_permitted(),"Cancelled inherited chunk blocks follow-on publication even beside live successor");
            require(refuses([&]{f.binding.send(owner,{0x95},{});}),"Cancelled chained ACK cannot send a later chunk");
        });
    });
    const auto first_ack=f.channels[0].held_ack;action.finish(true);first_ack(true);
    require(first==1&&first_good&&second==0&&f.channels[0].sends==2,"Accepted handler may continue one later async chunk");
    const auto second_ack=f.channels[0].held_ack;action.invalidate();
    auto successor=f.directory->begin_action();const auto successor_live=f.directory->action_liveness();
    require(successor.current()&&successor_live->load(),"Old origin cancellation leaves independent successor live");
    second_ack(true);second_ack(true);
    require(second==1&&!second_good&&second_inherited&&f.channels[0].sends==2,"Chained delayed chunk retains old cancellation after original active pointer cleared");
    require(successor.current()&&successor_live->load()&&f.directory->action_permitted(),"Inherited callback restores successor gate after cancelling old continuation");
    successor.finish(true);
}
void action_live_ack_cannot_borrow_active_successor(){
    Fixture f;const auto owner=f.add(0,0x100000015ULL,0x900000015ULL);f.seal();f.channels[0].async=true;
    auto original=f.directory->begin_action();const auto original_live=f.directory->action_liveness();
    unsigned calls=0;bool good=true;
    f.binding.send(owner,{0x96},[&](bool accepted){
        ++calls;good=accepted;
        require(f.directory->action_liveness()==original_live,"Retained ACK always keeps its original token");
        require(!f.directory->action_permitted(),"Different active and inherited issuers deny causal continuation");
        require(refuses([&]{f.binding.send(owner,{0x97},{});}),"Retained ACK cannot attach a continuation to successor token");
        require(refuses([&]{(void)f.directory->begin_action();}),"Retained ACK cannot begin a nested action");
    });
    const auto ack=f.channels[0].held_ack;original.finish(true);
    auto successor=f.directory->begin_action();const auto successor_live=f.directory->action_liveness();
    ack(true);ack(true);
    require(calls==1&&!good&&f.channels[0].sends==1,"Overlapping retained ACK is rejected once before follow-on sends");
    require(!original_live->load()&&successor_live->load()&&successor.current()&&f.directory->action_permitted(),"Caught old ACK nested refusal cancels only original source and leaves successor live");
    successor.finish(true);
}
void action_liveness_survives_token_and_retires(){
    Fixture f;f.seal();const auto lifetime=f.directory->action_liveness();
    std::shared_ptr<const std::atomic_bool> finished_live;
    {auto action=f.directory->begin_action();finished_live=f.directory->action_liveness();
        require(finished_live!=lifetime&&action.current(),"Action has distinct liveness from directory lifetime");action.finish(true);}
    // No send retains this action token. Only the public atomic flag survives.
    require(finished_live->load()&&lifetime->load()&&f.directory->action_liveness()==lifetime,"Accepted expired token leaves flag alive until real directory retirement");
    f.directory->retire();
    require(!finished_live->load()&&!lifetime->load()&&!f.directory->action_permitted(),"Retirement revokes retained flags even after their action tokens expired");
    require(refuses([&]{(void)f.directory->begin_action();}),"Retired directory cannot issue new action scope");
}
}
void test_shared_guild_channel_directory53(){routing_and_identity();closure_and_reentry();retirement_and_thread();chat_routing_and_one_use();chat_freshness_and_partial_delivery();chat_renderer_reentry_and_retirement();native_holder_invalidation_stops_actual_directory_batch();action_observer_cancellation_and_successor();action_delayed_ack_after_handler_end();action_chained_ack_inherits_original_scope();action_live_ack_cannot_borrow_active_successor();action_liveness_survives_token_and_retires();}
