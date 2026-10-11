#include "protocol/RecoveredGuildLeadership.h"
#include <iostream>
#include <string>
#include <vector>

using Wire=god2::RecoveredGuildLeadership;
namespace {
unsigned checks=0;
void check(bool value) {
    ++checks;
    if(!value)throw std::runtime_error("Guild leadership wire0078 check "+std::to_string(checks));
}
void requests() {
    // Exact machine outputs selected slot7: native control18 targetrole0..3;
    // modal3 acceptance for targetrole0/1/2/3. These bytes cannot prove policy.
    check(Wire::decode(std::array<std::uint8_t,2>{0x71,7})==
        std::optional(Wire::Request{Wire::Action::ApproveOrAppoint,7}));
    check(Wire::decode(std::array<std::uint8_t,2>{0x72,7})==
        std::optional(Wire::Request{Wire::Action::RejectOrRemove,7}));
    for(unsigned opcode=0;opcode<256;++opcode) {
        for(unsigned slot=0;slot<256;++slot) {
            const std::array<std::uint8_t,2> raw={static_cast<std::uint8_t>(opcode),static_cast<std::uint8_t>(slot)};
            const auto result=Wire::decode(raw);
            const bool expected=(opcode==0x71 || opcode==0x72) && slot<50;
            check(result.has_value()==expected);
            if(result)check(static_cast<unsigned>(result->action)==opcode && result->slot==slot);
        }
    }
    const std::array<std::uint8_t,2> native={0x71,7};
    for(std::size_t n=0;n<2;++n)check(!Wire::decode(std::span(native).first(n)));
    check(!Wire::decode(std::array<std::uint8_t,3>{0x71,7,0}));
    check(!Wire::decode(std::array<std::uint8_t,3>{0x72,7,0}));
    check(!Wire::decode(std::array<std::uint8_t,3>{0x93,7,1}));
}
void updates() {
    // Native existing-self93 case: role3 promotes controls; role1/0 removes
    // them. Codec serialization is not proof of an authorized promotion.
    check(Wire::role_update(0,3)==std::array<std::uint8_t,3>{0x93,0,3});
    check(Wire::decode_role_update(std::array<std::uint8_t,3>{0x93,0,3})==
        std::optional(Wire::RoleUpdate{0,3}));
    for(unsigned slot=0;slot<256;++slot) {
        for(unsigned role=0;role<256;++role) {
            const std::array<std::uint8_t,3> raw={0x93,static_cast<std::uint8_t>(slot),static_cast<std::uint8_t>(role)};
            const auto result=Wire::decode_role_update(raw);
            const bool expected=slot<50 && role<=3;
            check(result.has_value()==expected);
            if(result) {
                check(result->slot==slot && result->role==role);
                check(Wire::role_update(result->slot,result->role)==raw);
            }
        }
    }
    for(unsigned opcode=0;opcode<256;++opcode)
        check(Wire::decode_role_update(std::array<std::uint8_t,3>{static_cast<std::uint8_t>(opcode),0,0}).has_value()==(opcode==0x93));
    for(const auto bad: {Wire::RoleUpdate{50,0},Wire::RoleUpdate{255,3},Wire::RoleUpdate{0,4},
                         Wire::RoleUpdate{49,255},Wire::RoleUpdate{255,255}}) {
        bool threw=false;
        try{(void)Wire::role_update(bad.slot,bad.role);}catch(const std::invalid_argument&){threw=true;}
        check(threw);
    }
    const std::array<std::uint8_t,3> native={0x93,49,3};
    for(std::size_t n=0;n<3;++n)check(!Wire::decode_role_update(std::span(native).first(n)));
    check(!Wire::decode_role_update(std::array<std::uint8_t,4>{0x93,49,3,0}));
    check(!Wire::decode_role_update(std::array<std::uint8_t,2>{0x71,7}));
    check(!Wire::decode_role_update(std::array<std::uint8_t,2>{0x72,7}));
}
}
int main() {
    try {
        requests();updates();
        std::cout<<"PASS leadership0078 wire checks="<<checks<<'\n';
        return 0;
    }catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';return 1;
    }
}
