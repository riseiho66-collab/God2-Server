#include "handlers/OwnedGuildChatService.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
using namespace god2;
void require(bool b,const char* why){if(!b)throw std::runtime_error(why);}
int main(){try {
    using P=OwnedGuildChatService::Peer;std::map<std::uint64_t,P> live;
    for(unsigned i=1;i<=4;++i)live.emplace(i,P{{i,i,i,"Player"+std::to_string(i),true,i==2,0},
        {i<3?1u:2u,i<3?"First":"Second",5,i}});
    const auto resolve=[&](auto id)->std::optional<P>{const auto it=live.find(id);return it==live.end()?std::nullopt:std::optional{it->second};};
    const auto audience=[&]{std::vector<P> all;for(const auto& [id,p]:live)all.push_back(p);return all;};
    const auto project=[](const auto& source,const auto& recipient,const auto& request){
        return RecoveredGuildChat::display(source.actor.character,recipient.actor.simplified,source.actor.name+": "+request.legacy_text);
    };
    OwnedGuildChatService service(resolve,audience,project);
    RecoveredGuildChat::Request input{{3,0xa5,0,0},"guild"};
    for(const auto selector:{3,0x83})for(const auto caller:{0,0xffff,3,4}) {
        input.client_header={static_cast<std::uint8_t>(selector),0xa5,static_cast<std::uint8_t>(caller),static_cast<std::uint8_t>(caller>>8)};
        const auto wire=RecoveredGuildChat::encode(input);
        require(RecoveredGuildChat::decode(wire)==std::optional{input},"Header roundtrip");
        const auto parsed=RecoveredWorldRecords::decode(wire);
        require(parsed && std::get<RecoveredGuildChat::Request>(parsed->front())==input,"Guild parsed as common");
        for(std::size_t n=0;n<wire.size();++n)require(!RecoveredGuildChat::decode(std::span(wire).first(n)),"Truncated guild frame accepted");
    }
    std::vector<RecoveredGuildChat::Request> batch{input,input};
    require(service.prepare(1,batch)->size()==4,"Guild audience incomplete");
    for(const auto& d:*service.prepare(1,batch))require(d.recipient<=2 && d.logical[9]==(d.recipient==2?0x83:3),"Cross-guild leak/selector");
    const auto before=live;
    live.erase(1);require(!service.prepare(1,batch),"Nonmember sent");live=before;
    live.at(1).actor.ready=false;require(!service.prepare(1,batch),"Unready source sent");live=before;
    live.at(2).actor.ready=false;require(service.prepare(1,batch)->size()==2,"Unready target received");live=before;
    live.at(2).actor.character=1;require(!service.prepare(1,batch),"Duplicate owner character accepted");live=before;
    OwnedGuildChatService common(resolve,audience,[](const auto& s,const auto& r,const auto& q){return RecoveredChat::display(s.actor.character,r.actor.simplified,q.legacy_text);});
    require(!common.prepare(1,batch),"Wrong display channel accepted");
    OwnedGuildChatService late(resolve,audience,[&](const auto& s,const auto& r,const auto& q){
        live.at(2).membership.guild_id=2;return project(s,r,q);
    });
    require(!late.prepare(1,batch),"Late leave leaked prepared text");live=before;
    OwnedGuildChatService revision(resolve,audience,[&](const auto& s,const auto& r,const auto& q){
        ++live.at(1).membership.membership_revision;return project(s,r,q);
    });
    require(!revision.prepare(1,batch),"Changed membership generation accepted");live=before;
    OwnedGuildChatService join(resolve,audience,[&](const auto& s,const auto& r,const auto& q){
        live.at(3).membership=live.at(1).membership;return project(s,r,q);
    });
    require(!join.prepare(1,batch),"Late audience join published stale batch");live=before;
    require(RecoveredGuildChat::name("")==std::vector<std::uint8_t>({0x2d,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0}),"2D clear layout");
    require(RecoveredGuildChat::name(std::string(15,'a')).size()==17,"2D bound");
    try {RecoveredGuildChat::name(std::string(16,'a'));throw std::runtime_error("Long2D accepted");}catch(const std::invalid_argument&){}
    try {RecoveredGuildChat::name("100%");throw std::runtime_error("Native format name accepted");}catch(const std::invalid_argument&){}
    require(live==before,"Chat changed state");
    std::cout<<"Guild audience, native wire, atomic late leases and no common leakage passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
