#include "handlers/OwnedPrivateChatService.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <stdexcept>
using namespace god2;
void require(bool value,const char* error){if(!value)throw std::runtime_error(error);}
int main() {
 try {
    using S=OwnedPrivateChatService;using R=RecoveredPrivateChat;
    std::map<std::uint64_t,S::Peer> peers{{1,{1,101,4,"Source",true,false,1}},
        {2,{2,102,5,"Target",true,true,2}},{3,{3,103,6,"Outsider",true,false,0}}};
    auto resolve=[&](std::uint64_t id)->std::optional<S::Peer> {
        const auto at=peers.find(id);return at==peers.end()?std::optional<S::Peer>{}:at->second;
    };
    auto audience=[&]{std::vector<S::Peer> out;for(const auto& [id,peer]:peers)out.push_back(peer);return out;};
    auto decode=[](const auto&,const R::Request& request){return request.legacy_text;};
    auto wire=[](const auto& source,const auto& target,const auto& recipient,const R::Request& request,const R::Text& text) {
        return R::display(source.character,recipient.simplified,request.client_header[0]&0x7f,
            source.name+": ["+target.name+"] "+text.message);
    };
    S service(resolve,audience,decode,wire);
    R::Request input{{2,0xa5,0,0},"$Target hello"};
    for(const auto mode:{2,9,0x82,0x89})for(const auto word:{0,0xffff,6}) {
        input.client_header={static_cast<std::uint8_t>(mode),0xa5,static_cast<std::uint8_t>(word),static_cast<std::uint8_t>(word>>8)};
        const auto encoded=R::encode(input);require(R::decode(encoded)==std::optional{input},"Private opaque header roundtrip");
        const auto records=RecoveredWorldRecords::decode(encoded);
        require(records && records->size()==1 && std::get<R::Request>(records->front())==input,"Private parsed as common");
        const auto result=service.prepare(1,std::span(&input,1));
        require(result && result->size()==2 && result->at(0).recipient==1 && result->at(1).recipient==2,"Outsider received private or header chose target");
        require(result->at(0).logical[9]==(mode&0x7f) && result->at(1).logical[9]==((mode&0x7f)|0x80),"Private mode9/lang changed");
        for(std::size_t size=0;size<encoded.size();++size)require(!R::decode(std::span(encoded).first(size)),"Truncated private parsed");
    }
    require(R::split("$Target    hello")==std::optional{R::Text{"Target","hello"}},"Native separator skip");
    for(const auto* text:{"Target hello","$ hello","$Target","$Target   ","$Nobody hello","$Source hello"}) {
        input.legacy_text=text;require(!service.prepare(1,std::span(&input,1)),"Invalid/missing/self recipient accepted");
    }
    input.legacy_text="$Target hello";const auto original=peers;
    peers.at(3).name="Target";require(!service.prepare(1,std::span(&input,1)),"Ambiguous name granted");peers=original;
    peers.at(2).ready=false;require(!service.prepare(1,std::span(&input,1)),"Unavailable target granted");peers=original;
    peers.at(1).ready=false;require(!service.prepare(1,std::span(&input,1)),"Unavailable source granted");peers=original;
    peers.at(3).character=5;require(!service.prepare(1,std::span(&input,1)),"Duplicate owned character lease granted");peers=original;
    S late(resolve,audience,decode,[&](const auto& source,const auto& target,const auto& recipient,const auto& request,const auto& text) {
        auto out=wire(source,target,recipient,request,text);peers.at(3).name="Target";return out;
    });
    require(!late.prepare(1,std::span(&input,1)),"Late name ambiguity published partial batch");peers=original;
    S lease(resolve,audience,decode,[&](const auto& source,const auto& target,const auto& recipient,const auto& request,const auto& text) {
        auto out=wire(source,target,recipient,request,text);peers.at(2).account=999;return out;
    });
    require(!lease.prepare(1,std::span(&input,1)),"Changed owner lease published");peers=original;
    std::vector<R::Request> batch{input,{{9,0,0xff,0xff},"$Outsider away"}};
    const auto result=service.prepare(1,batch);
    require(result && result->size()==4 && result->at(3).recipient==3,"Multiple private targets failed");
    batch.back().legacy_text="$Nobody nope";require(!service.prepare(1,batch),"Partial multi-message delivery");
    S forged(resolve,audience,decode,[&](const auto& source,const auto& target,const auto& recipient,const auto& request,const auto& text) {
        auto out=wire(source,target,recipient,request,text);out[5]=6;return out;
    });
    require(!forged.prepare(1,std::span(&input,1)),"Spoofed source display granted");
    require(peers==original,"Private service changed peer state");
    std::cout<<"Private2/9 codec, audience isolation, exact names, fresh lease and atomic preparation passed\n";
    return 0;
 }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
