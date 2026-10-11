#include "protocol/RecoveredDeitySelection.h"
#include "protocol/RecoveredDeityState.h"
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace {
void require(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
using State=god2::RecoveredDeityState;
State::Snapshot snapshot(std::uint8_t key=101) {
    State::Declaration::Bytes declaration{};declaration[0]=0x30;declaration[1]=key;declaration[2]='A';
    State::Status::Bytes status{};status[0]=0x31;status[1]=key;
    for(std::size_t i=2;i<status.size();++i) status[i]=static_cast<std::uint8_t>(i*7);
    return {*State::Declaration::parse(declaration),*State::Status::parse(status),{}};
}
template<class Record> void lossless() {
    typename Record::Bytes bytes{};bytes[0]=Record::opcode;
    for(unsigned seed=0;seed<256;++seed) {
        for(std::size_t at=1;at<bytes.size();++at) bytes[at]=static_cast<std::uint8_t>(seed+at*31);
        require(Record::parse(bytes)->encode()==bytes,"Record did not preserve opaque bytes");
    }
    for(unsigned opcode=0;opcode<256;++opcode) {
        bytes[0]=static_cast<std::uint8_t>(opcode);
        require(Record::parse(bytes).has_value()==(opcode==Record::opcode),"Opcode mismatch accepted");
    }
    std::array<std::uint8_t,64> padded{};padded[0]=Record::opcode;
    for(std::size_t length=0;length<padded.size();++length)
        require(Record::parse(std::span(padded).first(length)).has_value()==(length==Record::logical_size),
                "Wrong logical length accepted");
}
}
int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string_view(argv[1])=="--icon-audit") {
            for(unsigned kind=0;kind<4;++kind)
                for(unsigned id=1;id<=State::current_skill_bank_counts[kind];++id)
                    std::cout<<kind<<' '<<id<<' '<<State::has_current_skill_icon(kind,id)<<'\n';
            return 0;
        }
        using Request=god2::RecoveredDeitySelection;
        for(unsigned key=0;key<256;++key) {
            Request::Request request{static_cast<std::uint8_t>(key)};
            require(Request::decode(Request::encode(request))==request,"Selection lost raw key");
        }
        for(unsigned opcode=0;opcode<256;++opcode) {
            const std::array<std::uint8_t,2> raw{static_cast<std::uint8_t>(opcode),101};
            require(Request::decode(raw).has_value()==(opcode==0x67),"Selection wrong opcode");
        }
        const std::array<std::uint8_t,4> selection{0x67,101,0,0};
        for(std::size_t length=0;length<=4;++length)
            require(Request::decode(std::span(selection).first(length)).has_value()==(length==2),"Selection wrong length");
        lossless<State::Declaration>();lossless<State::Status>();lossless<State::Skill>();
        auto owned=snapshot();require(State::valid(owned,{}),"Valid named snapshot rejected");
        require(State::selection_response(101,owned,{})->encode()==owned.status.encode(),"Selection altered stored bytes");
        require(!State::selection_response(102,owned,{}),"Foreign selection accepted");
        for(const auto raw: {std::array<std::uint8_t,4>{0x34,101,0,1}, {0x34,101,3,111}})
            owned.skills.push_back(*State::Skill::parse(raw));
        require(State::valid(owned,{}),"Qualified skill boundaries rejected");
        // Actual native graphics audit includes internal/non-display definitions.
        // Those raw records remain lossless but must never reach owned refresh.
        for(const auto raw:{std::array<std::uint8_t,4>{0x34,101,0,120},{0x34,101,0,121},
                            {0x34,101,1,73},{0x34,101,1,88},{0x34,101,2,63},{0x34,101,2,68},
                            {0x34,101,3,84},{0x34,101,3,98}}) {
            auto unsafe=snapshot();unsafe.skills.push_back(*State::Skill::parse(raw));
            require(!State::valid(unsafe,{}) && !State::restore(std::span(&unsafe,1),101,{}),
                    "Unavailable native icon reached owned restore");
        }
        auto capacity=snapshot();
        for(unsigned id=1;id<=100;++id)
            capacity.skills.push_back(*State::Skill::parse(std::array<std::uint8_t,4>{0x34,101,0,static_cast<std::uint8_t>(id)}));
        require(State::valid(capacity,{}) && State::restore(std::span(&capacity,1),101,{})->size()==448,
                "Full100 learned skills failed restore");
        unsigned display_count=0;
        for(unsigned kind=0;kind<4;++kind)
            for(unsigned id=1;id<=State::current_skill_bank_counts[kind];++id)
                display_count+=State::has_current_skill_icon(kind,id);
        require(display_count==409,"Current icon audit409/448 coverage changed");
        for(const auto raw: {std::array<std::uint8_t,4>{0x34,101,4,1}, {0x34,101,0,0},
                            {0x34,101,0,122}, {0x34,99,0,1}, {0x34,101,0,1}}) {
            auto invalid=owned;invalid.skills.push_back(*State::Skill::parse(raw));
            require(!State::valid(invalid,{}),"Invalid/duplicate learned skill accepted");
        }
        auto invalid=owned;invalid.skills.resize(101,owned.skills.front());
        require(!State::valid(invalid,{}),"Skill capacity exceeded");
        auto declaration=owned.declaration.encode();declaration[18]=1;
        invalid=owned;invalid.declaration=*State::Declaration::parse(declaration);
        require(!State::valid(invalid,{}),"Duplicate-reset declaration accepted");
        declaration=owned.declaration.encode();std::fill(declaration.begin()+2,declaration.begin()+18,'X');
        invalid.declaration=*State::Declaration::parse(declaration);
        require(!State::valid(invalid,{}),"Unterminated packet name accepted");
        for(const auto key:{0,128,255}) require(!State::valid(snapshot(static_cast<std::uint8_t>(key)),{}),"Invalid status key accepted");
        for(unsigned key=1;key<=127;++key) {
            const auto raw=static_cast<std::uint8_t>(key);
            const std::array<std::uint8_t,1> catalog{raw};
            const bool expected=key<=34 || (key>=101 && key<=108);
            require(State::valid(snapshot(raw),catalog)==expected,"Native portrait boundary mismatch");
        }
        const std::array<std::uint8_t,1> templates{1};
        require(!State::valid(snapshot(1),{}) && State::valid(snapshot(1),templates),"Catalog qualification missing");
        auto negative=snapshot();declaration=negative.declaration.encode();declaration[1]=155;
        negative.declaration=*State::Declaration::parse(declaration);
        require(State::valid(negative,{}),"Negative selected declaration rejected");
        std::vector<State::Snapshot> rows{owned,snapshot(102)};
        const auto restored=State::restore(rows,std::uint8_t{101},{});
        require(restored && restored->size()==104,"Restoration length mismatch");
        require(std::equal(owned.status.encode().begin(),owned.status.encode().end(),restored->end()-29),
                "Selected status not last or mutated");
        require((*restored)[0]==0x30 && (*restored)[19]==0x30 && (*restored)[38]==0x34,
                "Restoration dependency order mismatch");
        require(!State::restore(rows,std::uint8_t{103},{}),"Missing selected key accepted");
        rows.push_back(owned);require(!State::restore(rows,{},{}),"Duplicate owned row accepted");
        rows.assign(17,owned);require(!State::restore(rows,{},{}),"Row capacity exceeded");
        require(State::restore({}, {}, {})->empty() && !State::restore({},std::uint8_t{101},{}),"Empty ownership synthesized rows");
        std::cout<<"Deity selection, lossless records, owned snapshot validation and restoration passed\n";
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
