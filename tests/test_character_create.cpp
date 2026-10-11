#include "protocol/RecoveredCharacterCreate.h"
#include "protocol/RecoveredCharacterCreateResult.h"
#include <stdexcept>
#include <vector>

namespace {
void require(bool value) {
    if(!value) throw std::runtime_error("character-create decoder regression");
}
using Frame=std::array<std::uint8_t,48>;
Frame encode(Frame plain) {
    unsigned sum=0;
    for(std::size_t i=0;i+1<plain.size();++i) sum+=plain[i]+0x3c;
    plain.back()=static_cast<std::uint8_t>(sum);
    Frame wire=plain;
    for(std::size_t i=2;i<plain.size();++i) {
        const unsigned previous=i==2?0:plain[i-1];
        wire[i]=static_cast<std::uint8_t>((plain[i]^god2::recovered_zero_seed_key[i-2])+previous+253);
    }
    return wire;
}
}

void test_character_create() {
    using god2::RecoveredCharacterCreate;
    Frame plain{};
    plain[0]=48;plain[2]=0x1b;
    for(std::size_t i=3;i<47;++i) plain[i]=static_cast<std::uint8_t>(i);
    plain[43]=4;
    const auto wire=encode(plain);
    const auto parsed=RecoveredCharacterCreate::parse(wire);
    require(parsed.has_value());
    require(parsed->opcode==0x1b);
    auto native=plain;native[2]=0x17;
    const auto native_parsed=RecoveredCharacterCreate::parse(encode(native));
    require(native_parsed && native_parsed->opcode==0x17 && native_parsed->payload==parsed->payload);
    for(std::size_t i=0;i<44;++i) require(parsed->payload[i]==plain[i+3]);
    for(std::size_t size=0;size<wire.size();++size)
        require(!RecoveredCharacterCreate::parse(std::span(wire).first(size)));
    auto longer=std::vector<std::uint8_t>(wire.begin(),wire.end());longer.push_back(0);
    require(!RecoveredCharacterCreate::parse(longer));
    for(const auto index : {0U,1U,47U}) {
        auto bad=wire;bad[index]^=0x80;
        require(!RecoveredCharacterCreate::parse(bad));
    }
    for(const auto index : {2U,43U}) {
        auto bad=plain;bad[index]^=1;
        require(!RecoveredCharacterCreate::parse(encode(bad)));
    }
    RecoveredCharacterCreate named{};
    require(!named.name_bytes());
    std::fill_n(named.payload.begin(),14,static_cast<std::uint8_t>('A'));
    require(named.name_bytes()==std::string(14,'A'));
    named.payload[14]='B';
    require(!named.name_bytes());
    named.payload[2]=0;
    named.payload[0]=0xa4;named.payload[1]=0x40;
    const auto raw_name=named.name_bytes();
    require(raw_name && raw_name->size()==2);
    require(static_cast<unsigned char>((*raw_name)[0])==0xa4);
    require(static_cast<unsigned char>((*raw_name)[1])==0x40);
    const auto response=god2::RecoveredCharacterCreateResult::committed_success();
    require(response.size()==26 && response[0]==26 && response[1]==0);
    std::array<std::uint8_t,26> decoded=response;
    unsigned previous=0;
    for(std::size_t i=2;i<response.size();++i) {
        decoded[i]=static_cast<std::uint8_t>((response[i]+259-previous)&255)
            ^god2::recovered_zero_seed_key[i-2];
        previous=decoded[i];
    }
    require(decoded[2]==2 && decoded[3]==0 && decoded[4]==0);
    for(std::size_t i=5;i+1<decoded.size();++i) require(decoded[i]==0);
    require(decoded.back()==0xf8); // 26 + 2 + 25 * 0x3c modulo 256.
}
