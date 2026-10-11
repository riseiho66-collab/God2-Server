#include "protocol/RecoveredDailyQuestRequest.h"
#include "handlers/RecoveredOwnedDailyQuestView.h"
#include <stdexcept>
#include <vector>
#include <iostream>
using Q=god2::RecoveredDailyQuestRequest;
static void require(bool pass) { if(!pass) throw std::runtime_error("daily quest contract mismatch"); }
int main() {
    unsigned vectors=0;
    for(const auto side: {1,2}) for(const auto slot: {0,29,255}) for(const auto tail: {0,165,255}) {
        const Q::Selection request{7,9,static_cast<std::uint8_t>(slot),
            static_cast<std::uint16_t>(side==1 ? 0x1234 : 0xabcd),
            static_cast<std::uint8_t>(side),static_cast<std::uint8_t>(tail)};
        const auto wire=Q::encode(request);require(wire.has_value());
        const auto decoded=Q::decode(*wire);require(decoded.has_value());
        require(std::get<Q::Selection>(*decoded)==request);
        require((*wire)[8]==tail && (*wire)[4]==slot && (*wire)[7]==side);
        require(Q::matches(request,{7,9,0x1234,0xabcd,0x3f}));
        require(!Q::matches(request,{7,9,0x1234,0xabcd,0x40}));
        require(!Q::matches(request,{8,9,0x1234,0xabcd,1}));
        require(!Q::matches(request,{7,8,0x1234,0xabcd,1}));
        require(!Q::matches(request,{7,9,0,0,1}));
        for(std::size_t length=0;length<wire->size();++length) require(!Q::decode(std::span(*wire).first(length)));
        auto extra=std::vector<std::uint8_t>(wire->begin(),wire->end());extra.push_back(0);require(!Q::decode(extra));
        ++vectors;
    }
    // Namespace zero and high bytes are not rejected merely as invalid journal IDs.
    for(unsigned value=0;value<256;++value) {
        const auto v=static_cast<std::uint8_t>(value);
        const Q::Selection q{v,v,0xff,0xffff,1,v};require(Q::decode(*Q::encode(q)).has_value());
        auto wrong=q;wrong.item_slot=v;require(Q::encode(wrong).has_value()==(value<30 || value==255));
        wrong=q;wrong.side=v;require(Q::encode(wrong).has_value()==(value==1 || value==2));
    }
    auto auxiliary=Q::encode(Q::Auxiliary{});
    require(std::holds_alternative<Q::Auxiliary>(*Q::decode(auxiliary)));
    for(std::size_t i=2;i<auxiliary.size();++i) {auto bad=auxiliary;bad[i]=1;require(!Q::decode(bad));}
    for(unsigned mode=0;mode<256;++mode) if(mode!=2) {
        auto bad=auxiliary;bad[1]=static_cast<std::uint8_t>(mode);require(!Q::decode(bad));
    }
    std::array<std::uint8_t,172> list{};list[0]=0xfd;list[1]=172;list[3]=2;
    for(unsigned count=0;count<256;++count) {list[164]=static_cast<std::uint8_t>(count);require(Q::valid_list(list)==(count<=40));}
    list[164]=40;
    for(std::size_t length=0;length<list.size();++length) require(!Q::valid_list(std::span(list).first(length)));
    for(const auto at:{0u,1u,2u,3u}) {auto bad=list;bad[at]^=1;require(!Q::valid_list(bad));}
    const std::array<std::uint8_t,2> open{0xd7,0};
    const auto opened=god2::RecoveredWorldRecords::decode(open);require(opened && opened->size()==1);
    require(std::holds_alternative<god2::RecoveredWorldRecords::DailyPanelOpen>(opened->front()));
    require(god2::RecoveredOwnedDailyQuestView::request(*opened).has_value());
    const std::array<std::uint8_t,1> short_open{0xd7};require(!god2::RecoveredWorldRecords::decode(short_open));
    const std::array<std::uint8_t,2> bad_open{0xd7,1};require(!god2::RecoveredWorldRecords::decode(bad_open));
    auto mixed=*opened;mixed.push_back(opened->front());require(!god2::RecoveredOwnedDailyQuestView::request(mixed));
    god2::OwnedDailyQuestList issued{};issued.logical=list;issued.logical[164]=1;
    issued.logical[4]=0;issued.logical[5]=0;issued.logical[7]=0x41;
    god2::NativeDailyQuestDisplay source{};source.index=0;source.branch=0;source.logical[2]=0x34;source.logical[3]=0x12;source.logical[4]=0xcd;source.logical[5]=0xab;
    const std::array sources{source};
    const Q::Selection start{0,0,0xff,0x1234,1,0},end{0,0,0xff,0xabcd,2,0};
    require(god2::RecoveredOwnedDailyQuestView::binding(issued,start,sources).has_value());
    require(god2::RecoveredOwnedDailyQuestView::binding(issued,end,sources).has_value());
    auto wrong=start;wrong.npc=0xabcd;require(!god2::RecoveredOwnedDailyQuestView::binding(issued,wrong,sources));
    for(const auto flags:{0u,1u,0x40u,0x81u,0xc1u}) {
        issued.logical[7]=static_cast<std::uint8_t>(flags);require(!god2::RecoveredOwnedDailyQuestView::binding(issued,start,sources));
    }
    issued.logical[7]=0x41;issued.logical[164]=0;require(!god2::RecoveredOwnedDailyQuestView::binding(issued,start,sources));
    issued.logical[164]=41;require(!god2::RecoveredOwnedDailyQuestView::binding(issued,start,sources));
    issued.logical[164]=1;require(!god2::RecoveredOwnedDailyQuestView::auxiliary(issued));
    issued.logical[165]=0x10;issued.logical[170]=1;require(god2::RecoveredOwnedDailyQuestView::auxiliary(issued));
    issued.logical[165]=0x20;require(!god2::RecoveredOwnedDailyQuestView::auxiliary(issued));
    std::cout<<"PASS daily request "<<vectors<<" native-shaped vectors, source binding and bounds\n";
}
