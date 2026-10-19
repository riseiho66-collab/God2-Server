#include "relations53/SharedGuildChannelDirectory53.h"
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
        unsigned ready=0,sends=0,baselines=0,names=0,closed_calls=0;
        std::function<void()> on_ready,on_send,on_baseline,on_enumerate,on_name;
        std::function<void(bool)> held_ack;
        bool async=false,throw_send=false,null_baseline=false;
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
        s.owner=[&c](auto id)->std::optional<Owner>{const auto at=c.owners.find(id);return at==c.owners.end()?std::nullopt:std::optional{at->second};};
        s.peer_ready=[&c](const Owner&){++c.ready;if(c.on_ready)c.on_ready();return true;};s.recipient_ready=s.peer_ready;
        s.closed=[&c](const Owner& value){++c.closed_calls;return c.closed.contains(value.session);};
        s.send=[&c](const Owner&,auto,std::function<void(bool)> ack){++c.sends;if(c.async)c.held_ack=ack;else{ack(true);ack(true);}if(c.on_send)c.on_send();if(c.throw_send)throw std::runtime_error("Synthetic send failure");};
        s.baseline=[&c](const Owner& value)->std::optional<Directory::Common::Baseline>{++c.baselines;if(c.on_baseline)c.on_baseline();if(c.null_baseline)return {};return Directory::Common::Baseline{value,{},false};};
        s.online=[&c]{return c.online;};s.sync_name=[&c](const Owner&){++c.names;if(c.on_name)c.on_name();};return s;
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
}
void test_shared_guild_channel_directory53(){routing_and_identity();closure_and_reentry();retirement_and_thread();}
