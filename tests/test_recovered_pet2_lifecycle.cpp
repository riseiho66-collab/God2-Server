#include "protocol/RecoveredPet2Lifecycle.h"
#include <iostream>
#include <stdexcept>
using P=god2::RecoveredPet2Lifecycle;
static void require(bool ok) { if(!ok) throw std::runtime_error("Pet2 lifecycle regression"); }
static P::Snapshot pet(std::uint8_t slot,std::uint16_t key,std::uint8_t poison) {
    god2::RecoveredPet2Stats::LogicalRecord raw;
    raw.fill(poison);raw[0]=0xfb;raw[1]=static_cast<std::uint8_t>(key);
    raw[2]=static_cast<std::uint8_t>(key>>8);raw[3]=slot;
    auto record=god2::RecoveredPet2Stats::parse_logical(raw);require(record.has_value());
    P::Metadata metadata;metadata.fill(poison);metadata[0]=raw[1];metadata[1]=raw[2];metadata[2]=34;
    return {{1,2},metadata,*record};
}
static void output(const std::vector<std::uint8_t>& bytes) {
    constexpr char hex[]="0123456789abcdef";
    for(auto b:bytes) std::cout<<hex[b>>4]<<hex[b&15];
    std::cout<<'\n';
}
int main() {
    const P::Context context{{1,2},true,false};
    const auto resolver=[](std::uint16_t key){return key==28001 || key==28002;};
    for(std::uint8_t slot=42;slot<=44;++slot) {
        const auto p=pet(slot,28001,0xa5);
        const auto wire=god2::RecoveredSelectionItemRequest::encode({28001,slot});
        const auto r=P::decode(wire);require(r.has_value());
        require(P::accepts(context,*r,p,resolver));
        for(std::size_t length=0;length<wire.size();++length) require(!P::decode(std::span(wire).first(length)));
        auto extra=std::vector<std::uint8_t>(wire.begin(),wire.end());extra.push_back(0);require(!P::decode(extra));
        for(const auto denied:std::array<P::Context,3>{{{{9,2},true,false},{{1,9},true,false},{{1,2},false,false}}})
            require(!P::restore(denied,p,resolver));
        require(!P::restore(P::Context{{1,2},true,true},p,resolver));
        require(!P::restore(context,p,[](auto){return false;}));
        auto bad=p;bad.inventory[2]=13;require(!P::restore(context,bad,resolver));
        bad=p;bad.inventory[0]^=1;require(!P::restore(context,bad,resolver));
        const auto projected=P::restore(context,p,resolver);require(projected && projected->size()==108);
        const auto original=god2::RecoveredPet2Stats::encode_logical(p.stats);
        require(std::equal(original.begin(),original.end(),projected->end()-73));
        output(*projected);
    }
    for(std::uint8_t source=42;source<=43;++source) {
        const auto p=pet(source,28001,0xa5),active=pet(44,28002,0x3c);
        const auto r=*P::decode(god2::RecoveredSelectionItemRequest::encode({28001,source}));
        const auto move=P::transfer(context,r,p,44,std::nullopt,resolver);
        require(move && move->size()==113);output(*move);
        const auto swap=P::transfer(context,r,p,44,active,resolver);
        require(swap && swap->size()==216);output(*swap);
        require(!P::transfer(context,r,p,43,std::nullopt,resolver));
        auto wrong=r;wrong.key=28002;require(!P::transfer(context,wrong,p,44,std::nullopt,resolver));
    }
    const auto active=pet(44,28001,0xa5);
    const auto r=*P::decode(god2::RecoveredSelectionItemRequest::encode({28001,44}));
    for(std::uint8_t target=42;target<=43;++target) {
        const auto move=P::transfer(context,r,active,target,std::nullopt,resolver);
        require(move && move->size()==113);output(*move);
        require(!P::transfer(context,r,active,target,pet(target,28002,0x3c),resolver));
    }
    for(unsigned slot=0;slot<256;++slot) {
        const auto raw=god2::RecoveredSelectionItemRequest::encode({28001,static_cast<std::uint8_t>(slot)});
        require(P::decode(raw).has_value()==(slot>=42 && slot<=44));
    }
}
