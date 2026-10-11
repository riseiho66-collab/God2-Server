#include "handlers/OwnedPartyPositionQuery.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <map>
using namespace god2;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
NativeParty::Member owner(unsigned id) {
    NativeParty::Member m{id,id,static_cast<std::uint16_t>(id),4,3,126,126};
    m.name="Player"+std::to_string(id);m.ready=true;m.level=1;m.resources={50,100,20,80};return m;
}
int main(){try {
    NativeParty parties;std::map<std::uint64_t,NativeParty::Member> live;
    for(unsigned id=1;id<=4;++id){live.emplace(id,owner(id));parties.observe(live.at(id));}
    const auto now=NativeParty::Time{};using K=RecoveredParty::Kind;
    require(parties.handle(2,{K::Join,2,1},now).size()==1,"Missing actual consent preview");
    require(!parties.handle(1,{K::Answer,0,2,1},now).empty(),"Missing accepted party");
    OwnedPartyPositionQuery service([&](auto id)->std::optional<NativeParty::Member> {
        const auto at=live.find(id);return at==live.end()?std::nullopt:std::optional{at->second};
    });
    RecoveredPartyPositionQuery::Request query{2};query.name.fill(0xff);query.name[2]=0;
    // Codec preserves the complete opaque residue; parsing does not admit its ID.
    for(const auto id:{0u,1u,2999u,3000u,65535u}) {
        auto q=query;q.target=static_cast<std::uint16_t>(id);const auto wire=RecoveredPartyPositionQuery::encode(q);
        require(RecoveredPartyPositionQuery::decode(wire)==std::optional{q},"Raw19 query roundtrip differs");
        const auto decoded=RecoveredWorldRecords::decode(wire);
        require(decoded && decoded->size()==1 && std::get<RecoveredPartyPositionQuery::Request>(decoded->front())==q,"World59 parser missing");
        for(std::size_t size=1;size<wire.size();++size)
            require(!RecoveredWorldRecords::decode(std::span(wire).first(size)),"Truncated query accepted");
    }
    auto wire=RecoveredPartyPositionQuery::encode(query);wire[0]=0;
    require(!RecoveredPartyPositionQuery::decode(wire),"Wrong opcode accepted");
    require(service.query(parties,1,query)==std::optional{RecoveredParty::position(2,126,126)},"Actual party target query failed");
    query.target=1;require(service.query(parties,2,query)==std::optional{RecoveredParty::position(1,126,126)},"Reverse party query failed");
    query.target=2;
    const auto baseline=live;
    const auto refused=[&](const char* reason){require(!service.query(parties,1,query),reason);live=baseline;};
    for(const auto target:{0u,1u,3u,2999u,3000u,65535u}) {
        query.target=static_cast<std::uint16_t>(target);refused("Unauthorized target accepted");
    }
    query.target=2;
    live.at(1).session=99;refused("Source session mismatch leaked query");
    live.at(1).account=99;refused("Source account mismatch leaked query");
    live.at(1).character=99;refused("Source character mismatch leaked query");
    live.at(1).ready=false;refused("Unavailable source leaked query");
    live.at(2).session=99;refused("Target session mismatch leaked query");
    live.at(2).account=99;refused("Target account mismatch leaked query");
    live.at(2).character=99;refused("Target character mismatch leaked query");
    live.at(2).ready=false;refused("Unavailable target leaked query");
    live.at(2).area=1;refused("Another area projected on current map");
    live.at(2).scene=4;refused("Another scene projected on current map");
    live.at(2).x=0x8000;refused("Signed marker X overflow admitted");
    live.at(2).y=0xffff;refused("Signed marker Y overflow admitted");
    live.at(2).x=132;live.at(2).y=129;
    require(service.query(parties,1,query)==std::optional{RecoveredParty::position(2,132,129)},"Cached coordinates overrode fresh owned location");
    live=baseline;
    unsigned reads=0;
    OwnedPartyPositionQuery changed([&](auto id)->std::optional<NativeParty::Member> {
        ++reads;auto m=live.at(id);if(reads==4)++m.x;return m;
    });
    require(!changed.query(parties,1,query),"Late location mutation admitted");
    reads=0;
    OwnedPartyPositionQuery disconnected([&](auto id)->std::optional<NativeParty::Member> {
        if(++reads==3)parties.disconnect(2);return live.at(id);
    });
    require(!disconnected.query(parties,1,query) && parties.party_size(1)==0,"Late membership change admitted");
    require(!service.query(parties,1,query) && !service.query(parties,3,query),"Nonparty query admitted");
    parties.observe(live.at(2));parties.handle(2,{K::Join,2,1},now);parties.handle(1,{K::Answer,0,2,1},now);
    require(service.query(parties,1,query).has_value() && parties.party_size(1)==2,"Queries damaged consent/rejoin lifecycle");
    auto leader=parties.member(1);auto peer=parties.member(2);
    for(unsigned i=0;i<8;++i)require(service.query(parties,1,query).has_value(),"Repeated readonly query failed");
    require(parties.member(1)==leader && parties.member(2)==peer && live==baseline,"Query mutated membership or owned state");
    std::cout<<"Native59 codec/framing, consenting ownership, fresh coordinates and late lease guards passed\n";
} catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
