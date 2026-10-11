#include "game/NativeSkillTargeting.h"
#include <iostream>
#include <sstream>
#include <string>

namespace {
using Rules = god2::NativeSkillTargeting;
void require(bool ok) { if (!ok) throw std::runtime_error("Native targeting check failed"); }
template<class F> void rejected(F&& fn) {
    try { fn(); } catch (const std::invalid_argument&) { return; }
    throw std::runtime_error("Invalid targeting input accepted");
}
void checks() {
    std::array<std::uint8_t,111> raw{}; raw[0]=1;
    for(std::size_t size=0;size<110;++size)
        rejected([&] { Rules::from_record(std::span(raw).first(size)); });
    rejected([&] { Rules::from_record(raw); });
    auto record=std::span(raw).first(110);
    auto fields=Rules::from_record(record);
    raw[0]=0;rejected([&] { Rules::from_record(record); });raw[0]=1;
    raw[1]=4;rejected([&] { Rules::from_record(record); });raw[1]=0;
    rejected([] { Rules::row_index(2,0); });
    rejected([] { Rules::row_index(0,14); });
    Rules::State state{{0,0},{0x12345678,0xabcdef01},{}};
    rejected([&] { Rules::evaluate(fields,14,state); });
    require(Rules::row_distance(0,12,1,12,state.masks)==1);
    require(Rules::row_distance(0,12,1,12,{0x3fff,0x3fff})==7);
    fields.mode_45=8;fields.reach_44=7;
    const auto broad=Rules::evaluate(fields,0,state);
    require(broad.masks==Rules::Masks{0x1f,0x1f});
    fields.mode_45=17;
    const auto saved=Rules::evaluate(fields,13,state);
    require(saved.saved_masks==state.masks && saved.masks==Rules::Masks{0x2000,0});
    fields.mode_45=0;
    require(!Rules::evaluate(fields,0,state).setup);
    fields.kind=2;fields.word_3e=0;
    require(!Rules::evaluate(fields,0,state).passes_kind_gate);
    fields.word_3e=0xff5;
    require(Rules::evaluate(fields,0,state).passes_kind_gate);
    require(state.saved_masks==Rules::Masks{0x12345678,0xabcdef01});
}
void batch() {
    std::string line;
    while(std::getline(std::cin,line)) {
        std::istringstream input(line);
        std::array<std::int64_t,38> values{};
        for(auto& value:values) if(!(input>>value)) throw std::runtime_error("Incomplete batch record");
        std::string extra;if(input>>extra) throw std::runtime_error("Extra batch field");
        for(unsigned i=0;i<5;++i)
            require(values[i]>=0 && values[i]<=(i==2?65535:255));
        require(values[5]>=0 && values[5]<14);
        Rules::Fields fields{static_cast<std::uint8_t>(values[0]),static_cast<std::uint8_t>(values[1]),
            static_cast<std::uint16_t>(values[2]),static_cast<std::uint8_t>(values[3]),
            static_cast<std::uint8_t>(values[4])};
        Rules::State state;
        for(unsigned i=0;i<4;++i) {
            require(values[6+i]>=0 && values[6+i]<=0xffffffffLL);
            (i<2?state.masks[i]:state.saved_masks[i-2])=static_cast<std::uint32_t>(values[6+i]);
        }
        for(unsigned i=0;i<28;++i) {
            const auto word=values[10+i];require(word>=-32768 && word<=32768);
            if(word==32768) state.entity_words[i]=std::nullopt;
            else state.entity_words[i]=static_cast<std::int16_t>(word);
        }
        const auto result=Rules::evaluate(fields,static_cast<unsigned>(values[5]),state);
        std::cout<<result.masks[0]<<' '<<result.masks[1]<<' '
            <<result.saved_masks[0]<<' '<<result.saved_masks[1]<<' '<<result.stored_mode<<' '
            <<(result.setup?static_cast<std::int64_t>(result.setup->first):-1)<<' '
            <<(result.setup?static_cast<std::int64_t>(result.setup->second):-1)<<' '
            <<result.passes_kind_gate<<'\n';
    }
}
}
int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="--batch") batch();
        else if(argc==1) { checks();std::cout<<"Native targeting bounded checks passed\n"; }
        else throw std::runtime_error("Unknown test arguments");
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n';return 1; }
}
