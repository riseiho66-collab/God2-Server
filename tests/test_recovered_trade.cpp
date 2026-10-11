#include "protocol/RecoveredTrade.h"
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string_view>
using namespace god2;
void require(bool ok,const char* message) {if(!ok)throw std::runtime_error(message);}
int main(int argc,char** argv) {try {
    using T=RecoveredTrade;using K=T::Kind;
    // Independent byte fixtures from original497250/497290/497A30/497A60.
    const std::array<std::vector<std::uint8_t>,5> native{{
        {0x29,0x34,0x12,0,0},
        {0x2a,0x78,0x56,2,1,0x34,0x12},
        {0x2b,0x34,0x12,0xa5,0xa5,0x78,0x56,0x34,0x12},
        {0x2c,0},{0x2d,0}}};
    if(argc==2 && std::string_view(argv[1])=="producer-fixtures") {
        T::Request open{K::Open};open.target=0x1234;
        T::Request item{K::OfferItem};item.item=0x5678;item.slot=2;item.quantity=1;item.target=0x1234;
        T::Request money{K::OfferMoney};money.target=0x1234;money.opaque=0xa5a5;money.money=0x12345678;
        for(const auto& r:{open,item,money,T::Request{K::Confirm},T::Request{K::Cancel}}) {
            for(const auto byte:T::encode(r))std::cout<<std::hex<<std::setfill('0')<<std::setw(2)<<unsigned(byte);
            std::cout<<'\n';
        }
        return 0;
    }
    for(const auto& wire:native) {
        const auto r=T::decode(wire);require(r.has_value(),"Native producer rejected");
        require(T::encode(*r)==wire,"Native raw bytes lost");
        for(std::size_t n=0;n<wire.size();++n)require(!T::decode(std::span(wire).first(n)),"Truncation accepted");
        auto excess=wire;excess.push_back(0);require(!T::decode(excess),"Trailing mutation byte accepted");
    }
    const auto money=T::decode(native[2]);require(money->target==0x1234 && money->money==0x12345678 && money->opaque==0xa5a5,"Native money padding/offset confused");
    require(!T::decode(std::array<std::uint8_t,5>{0x69,0,0,0,0}),"PK request treated as trade");
    T::Name name{};name[0]='P';const auto open=T::open(0x1234,name);
    require(open.size()==19 && open[1]=='P' && open[17]==0x34 && open[18]==0x12,"Peer/name order confused");
    // Test every byte-domain slot, including all signed-negative native cases.
    T::Item item{};
    for(unsigned slot=0;slot<=255;++slot) {
        for(unsigned n=0;n<24;++n)item[n]=static_cast<std::uint8_t>(n*7+3);
        item[1]=static_cast<std::uint8_t>(slot);
        const auto b=T::peer_item(item);require(b.has_value()==(slot<8),"Signed peer-slot admission mismatch");
        if(b)require(b->size()==25 && std::equal(item.begin(),item.end(),b->begin()+1),"Peer instance bytes changed");
    }
    require(T::peer_money(0x12345678,{1,2,3,4})==std::vector<std::uint8_t>{0x51,1,2,3,4,0x78,0x56,0x34,0x12},"Money at wrong dispatcher offset");
    require(T::peer_confirmation(0xabcd)==std::vector<std::uint8_t>{0x53,0xcd,0xab},"Confirmation WORD truncated");
    require(T::rollback_close(0x1234)==std::vector<std::uint8_t>{0x4f,0x34,0x12} &&
        T::close_without_refund(0x1234)==std::vector<std::uint8_t>{0x52,0x34,0x12},"Native close width confused");
    require(T::wallet(0xffffffff)==std::vector<std::uint8_t>{0x27,0xff,0xff,0xff,0xff},"Purse DWORD lost signed high bit");
    std::cout<<"Trade codec boundary/opaque/instance preservation passed; no runtime acceptance claim\n";
}catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}}
