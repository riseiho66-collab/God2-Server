// DRAFT ONLY. Compile with this artifact folder before src in include paths so
// protocol/RecoveredWorldRecords.h uses the reviewed additive parser draft.
// Parser/callback counters are structural proofs, not SQL/Application/live UI.
#include "protocol/RecoveredGuildDisband75.h"
#include "protocol/RecoveredWorldRecords.h"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>

using Wire=god2::RecoveredGuildDisband75;
using World=god2::RecoveredWorldRecords;
using Frame=god2::RecoveredWorldFrame;
using Bytes=std::vector<std::uint8_t>;
namespace {
unsigned checks=0;
void check(bool value){++checks;if(!value)throw std::runtime_error("Guild75 wire0081 check "+std::to_string(checks));}
void requests(){
    static_assert(Wire::opcode==0x75 && Wire::request_size==2 && Wire::slot_limit==50);
    check(Wire::decode(std::array<std::uint8_t,2>{0x75,0})==std::optional(Wire::Request{0}));
    for(unsigned opcode=0;opcode<256;++opcode)for(unsigned slot=0;slot<256;++slot){
        const std::array<std::uint8_t,2> raw={static_cast<std::uint8_t>(opcode),static_cast<std::uint8_t>(slot)};
        const auto decoded=Wire::decode(raw);check(decoded.has_value()==(opcode==0x75 && slot<50));
        if(decoded)check(decoded->slot==slot);
    }
    const std::array<std::uint8_t,2> native={0x75,0};
    for(std::size_t n=0;n<2;++n)check(!Wire::decode(std::span(native).first(n)));
    check(!Wire::decode(std::array<std::uint8_t,3>{0x75,0,0}));
    check(!Wire::decode(std::array<std::uint8_t,2>{0x73,0}));
    // Slots1..49 are grammar-valid; this does NOT grant service authority.
    for(unsigned slot=0;slot<50;++slot){
        const auto parsed=World::decode(std::array<std::uint8_t,2>{0x75,static_cast<std::uint8_t>(slot)});
        check(parsed && parsed->size()==1);
        check(std::get<Wire::Request>(parsed->front()).slot==slot);
    }
}
struct Counters{unsigned calls{},disbands{},chats{};};
bool dispatch_only_after_complete_parse(const Bytes& logical,Counters& counters){
    // Mirrors the existing Session parse_frame-before-world callback boundary.
    // No record callback escapes from a malformed suffix in ONE complete frame.
    const auto parsed=World::parse_frame(Frame::encode(logical));
    if(!parsed)return false;
    ++counters.calls;
    for(const auto& record:*parsed){
        if(std::holds_alternative<Wire::Request>(record))++counters.disbands;
        if(std::holds_alternative<god2::RecoveredChat::Request>(record))++counters.chats;
    }
    return true;
}
void whole_frame(){
    const Bytes chat={0x2f,9,0,0,0,0,0,'x',0};
    const Bytes native={0x75,0};
    const Bytes neutral={0x30,0,0x75,0,0xb8,0};
    auto parsed=World::decode(neutral);check(parsed && parsed->size()==3);
    check(std::holds_alternative<World::Tick>((*parsed)[0]));
    check(std::holds_alternative<Wire::Request>((*parsed)[1]));
    check(std::holds_alternative<god2::RecoveredGuildRoster::PanelReady>((*parsed)[2]));
    auto suffix75=chat;suffix75.insert(suffix75.end(),native.begin(),native.end());
    Counters accepted;check(dispatch_only_after_complete_parse(suffix75,accepted));
    check(accepted.calls==1 && accepted.disbands==1 && accepted.chats==1);
    for(const auto& suffix:std::vector<Bytes>{{0x75},{0x75,50},{0x75,255},{0x71},{0x79,1,0},{0xff},{0x30,1}}){
        // Chat and75 are both structurally valid early records. Malformed later
        // data denies the entire frame BEFORE either would mutate/send.
        auto logical=chat;logical.insert(logical.end(),native.begin(),native.end());
        logical.insert(logical.end(),suffix.begin(),suffix.end());
        Counters denied;check(!dispatch_only_after_complete_parse(logical,denied));
        check(denied.calls==0 && denied.disbands==0 && denied.chats==0);
    }
    const auto two=World::decode(Bytes{0x75,0,0x75,0});check(two && two->size()==2);
    // Structurally two75 is legal; single-use at-most-one SQL commit belongs to
    // service/Application tests, not this parser test.
    auto wire=Frame::encode(native);check(World::parse_frame(wire).has_value());
    wire.back()^=1;check(!World::parse_frame(wire));
    auto badlogical=native;badlogical.push_back(0xff);
    check(!World::decode(badlogical));
    const auto oldleadership=World::decode(Bytes{0x71,7,0x72,7,0x73,0});
    check(oldleadership && oldleadership->size()==3);
    check(std::get<god2::RecoveredGuildLeadership::Request>((*oldleadership)[0]).slot==7);
    check(std::get<god2::RecoveredGuildLeadership::Request>((*oldleadership)[1]).slot==7);
    check(std::get<god2::RecoveredGuildLeave::Request>((*oldleadership)[2]).slot==0);
}
}
int main(){try{requests();whole_frame();std::cout<<"Guild75 wire0081: "<<checks<<" checks passed\n";}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
