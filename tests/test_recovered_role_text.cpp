#include "protocol/RecoveredRoleText.h"
#include <cstdio>
#include <stdexcept>
#include <vector>
using Contract=god2::RecoveredRoleText;
static unsigned checks;
static void require(bool value){++checks;if(!value)throw std::runtime_error("role text contract failed");}
int main(){try{
    for(unsigned length=0;length<=15;++length)for(unsigned salt:{0u,0xa5u,0xffu}){
        Contract::Logical raw;raw.fill(static_cast<std::uint8_t>(salt));raw[0]=0x20;
        for(unsigned i=0;i<length;++i)raw[i+1]=static_cast<std::uint8_t>(0x80+i);
        raw[length+1]=0;
        const auto request=Contract::decode(raw);require(request.has_value());
        require(Contract::encode_request(*request)==raw);
        const auto clean=Contract::canonical(*request);require(clean.has_value());
        const auto response=Contract::update(*clean);require(response.has_value());
        require(response->size()==17 && (*response)[0]==0x23);
        for(unsigned i=0;i<16;++i)require((*clean)[i]==(i<length?raw[i+1]:0));
        auto noncanonical=*clean;if(length<15){noncanonical[length+1]=1;require(!Contract::update(noncanonical));}
    }
    Contract::Logical missing;missing.fill(0x41);missing[0]=0x20;
    require(!Contract::decode(missing));
    Contract::Request unterminated;unterminated.raw.fill(1);
    require(!Contract::canonical(unterminated) && !Contract::encode_request(unterminated));
    Contract::Logical valid{0x20};
    for(unsigned length=0;length<17;++length)require(!Contract::decode(std::span(valid).first(length)));
    std::vector<std::uint8_t> oversized(valid.begin(),valid.end());oversized.push_back(0);require(!Contract::decode(oversized));
    for(unsigned opcode=0;opcode<256;++opcode){valid[0]=static_cast<std::uint8_t>(opcode);require(Contract::decode(valid).has_value()==(opcode==0x20));}
    std::printf("PASS %u role text codec checks\n",checks);return 0;
}catch(const std::exception& e){std::fprintf(stderr,"%s\n",e.what());return 1;}}
