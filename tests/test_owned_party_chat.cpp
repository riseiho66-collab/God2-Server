#include "handlers/OwnedPartyChatService.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
using namespace god2;
void require(bool value,const char* text){if(!value)throw std::runtime_error(text);}
OwnedPartyChatService::Peer owner(unsigned id) {
    NativeParty::Member m{id,id,static_cast<std::uint16_t>(id),4,3,126,126};
    m.name="Player"+std::to_string(id);m.ready=true;return {m,id==2,static_cast<std::uint8_t>(id%4)};
}
int main(){try {
    NativeParty parties;std::map<std::uint64_t,OwnedPartyChatService::Peer> live;
    for(unsigned i=1;i<=4;++i){live.emplace(i,owner(i));parties.observe(live.at(i).member);}
    using K=RecoveredParty::Kind;const auto now=NativeParty::Time{};
    parties.handle(2,{K::Join,2,1},now);parties.handle(1,{K::Answer,0,2,1},now);
    const auto resolve=[&](auto id)->std::optional<OwnedPartyChatService::Peer> {
        const auto at=live.find(id);return at==live.end()?std::nullopt:std::optional{at->second};
    };
    const auto prepare=[](const auto& source,const auto& recipient,const auto& message) {
        return RecoveredPartyChat::display(source.member.character,recipient.simplified,source.member.name+": "+message.legacy_text);
    };
    OwnedPartyChatService service(resolve,prepare);
    RecoveredPartyChat::Request input{{1,0xa5,0,0},"hello"};
    for(const auto language:{0,0x80})for(const auto target:{0,0xff00,0xffff,0x1234}) {
        input.client_header={static_cast<std::uint8_t>(language|1),0xa5,static_cast<std::uint8_t>(target),static_cast<std::uint8_t>(target>>8)};
        const auto wire=RecoveredPartyChat::encode(input);
        require(RecoveredPartyChat::decode(wire)==std::optional{input},"Native header/residue roundtrip differs");
        const auto parsed=RecoveredWorldRecords::decode(wire);
        require(parsed && parsed->size()==1 && std::get<RecoveredPartyChat::Request>(parsed->front())==input,"Party selector parsed as common chat");
        for(std::size_t n=0;n<wire.size();++n)require(!RecoveredPartyChat::decode(std::span(wire).first(n)),"Truncated2F accepted");
        auto wrong=wire;wrong[3]=static_cast<std::uint8_t>(language);require(!RecoveredPartyChat::decode(wrong),"Common selector reinterpreted as party");
        const auto common=RecoveredWorldRecords::decode(wrong);
        require(common && std::holds_alternative<RecoveredChat::Request>(common->front()),"Frozen common selector disappeared");
    }
    std::vector<RecoveredPartyChat::Request> batch{input,input};
    const auto good=service.prepare(parties,1,batch);
    require(good && good->size()==4,"Both party recipients/multiple messages missing");
    for(const auto& d:*good)require((d.recipient==1 || d.recipient==2) && d.logical[9]==(d.recipient==2?0x81:1),"Audience/language selector mismatch");
    require(!service.prepare(parties,3,batch),"Outsider heard party channel");
    const auto baseline=live;
    for(const auto id:{1u,2u}) {
        live.at(id).member.session=99;require(!service.prepare(parties,1,batch),"Stale session leaked party chat");live=baseline;
        live.at(id).member.account=99;require(!service.prepare(parties,1,batch),"Stale account leaked party chat");live=baseline;
        live.at(id).member.character=99;require(!service.prepare(parties,1,batch),"Stale character leaked party chat");live=baseline;
    }
    live.at(1).member.ready=false;require(!service.prepare(parties,1,batch),"Unavailable sender published chat");live=baseline;
    live.at(2).member.ready=false;require(service.prepare(parties,1,batch)->size()==2,"Unavailable recipient blocked other owned delivery");live=baseline;
    live.at(2).member.scene=7;live.at(2).member.area=9;
    require(service.prepare(parties,1,batch)->size()==4,"Party chat incorrectly scoped by map coordinates");live=baseline;
    OwnedPartyChatService malformed(resolve,[](const auto& s,const auto& r,const auto& q) {
        return RecoveredChat::display(s.member.character,r.simplified,q.legacy_text);
    });
    require(!malformed.prepare(parties,1,batch),"Callback accidentally emitted common channel");
    OwnedPartyChatService late(resolve,[&](const auto& s,const auto& r,const auto& q) {
        ++live.at(2).member.account;return prepare(s,r,q);
    });
    require(!late.prepare(parties,1,batch),"Late lease change published partial messages");live=baseline;
    OwnedPartyChatService departed(resolve,[&](const auto& s,const auto& r,const auto& q) {
        parties.disconnect(2);return prepare(s,r,q);
    });
    require(!departed.prepare(parties,1,batch),"Late party departure published messages");
    require(!service.prepare(parties,1,batch),"Nonparty sender still delivered");
    parties.observe(live.at(2).member);parties.handle(2,{K::Join,2,1},now);parties.handle(1,{K::Answer,0,2,1},now);
    const auto members=parties.participants(1);
    for(unsigned i=0;i<8;++i)require(service.prepare(parties,2,batch)->size()==4,"Reverse repeated messages missing");
    require(live==baseline && parties.participants(1)==members,"Chat mutated saved/party state");
    std::cout<<"Party selector codec, owned audience, multilingual projection, same-group different-map and late lease gates passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
