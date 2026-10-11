#include "protocol/RecoveredCharacterListCandidate.h"
#include <stdexcept>
#include <vector>

namespace {
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
template<class F> void rejects(F call) {
    try { call(); } catch(const std::invalid_argument&) { return; }
    throw std::runtime_error("Invalid populated character list accepted");
}
god2::RecoveredCharacter character(std::uint8_t slot) {
    god2::RecoveredCharacter c{};c.id=slot+1;c.account_id=1;c.slot=slot;
    c.profile[0]=static_cast<std::uint8_t>('A'+slot);
    c.profile[29]=2;c.profile[31]=1;c.profile[32]=3;c.profile[33]=1;
    c.profile[36]=0x41;
    const unsigned packed=1+(9<<4)+(8<<10);
    c.profile[38]=static_cast<std::uint8_t>(packed);c.profile[39]=static_cast<std::uint8_t>(packed>>8);
    return c;
}
}
void test_recovered_character_list() {
    using Codec=god2::RecoveredCharacterListCandidate;
    require(Codec::wire({})==god2::LegacyCharacterListCandidate::wire(),"Empty baseline changed");
    std::vector<god2::RecoveredCharacter> characters{character(0),character(1)};
    const auto frame=Codec::decoded(characters),wire=Codec::wire(characters);
    require(frame[0]==78 && frame[1]==0 && frame[2]==7 && frame[3]==2 && frame[4]==0,"List frame shape");
    for(std::size_t i=0;i<characters.size();++i) {
        const auto at=5+36*i;
        require(frame[at]=='A'+i && frame[at+1]==0 && frame[at+15]==0,"Terminated name not preserved");
        require(frame[at+17]==2 && frame[at+19]==i,"Category and local token");
        require(frame[at+20]==0x41 && frame[at+22]==0x90 && frame[at+23]==0x20,"Mapped appearance bits");
        require(frame[at+24]==1 && frame[at+25]==0x60 && frame[at+26]==1 &&
                frame[at+27]==0x40 && frame[at+28]==1 && frame[at+29]==0 &&
                frame[at+30]==0x81 && frame[at+31]==0,"Native preview/selection component records");
        for(const auto field:{16,18,21,32,33,34,35})
            require(frame[at+field]==0,"Unknown field assigned fabricated semantics");
    }
    std::uint8_t previous=0,checksum=0;
    for(std::size_t i=0;i<frame.size();++i) {
        if(i>=2) {
            previous=static_cast<std::uint8_t>(wire[i]+3-previous)^god2::recovered_zero_seed_key[i-2];
            require(previous==frame[i],"List zero-seed transform mismatch");
        }
        if(i+1<frame.size()) checksum=static_cast<std::uint8_t>(checksum+frame[i]+0x3c);
    }
    require(checksum==frame.back(),"List checksum");
    characters.push_back(character(0));rejects([&]{Codec::wire(characters);});characters.pop_back();
    characters[1].slot=0;rejects([&]{Codec::wire(characters);});characters[1].slot=2;
    rejects([&]{Codec::wire(characters);});
    for(const auto& change:std::vector<std::pair<int,std::uint8_t>>{{0,0},{29,0},{29,9},{31,0},{31,6},
            {32,7},{33,2},{36,0xe0},{38,0},{38,0xa1},{39,0x28}}) {
        auto invalid=character(0);invalid.profile[change.first]=change.second;
        require(!Codec::valid_profile(invalid.profile),"Invalid generated profile accepted");
    }
    auto maximum=character(0);
    std::fill_n(maximum.profile.begin(),14,0xa4);maximum.profile[14]=0;
    maximum.profile[31]=5;
    require(Codec::valid_profile(maximum.profile),"Possible sentinel or byte-length name rejected");
    maximum.profile[14]=0x40;
    require(!Codec::valid_profile(maximum.profile),"Unterminated name accepted");
}
