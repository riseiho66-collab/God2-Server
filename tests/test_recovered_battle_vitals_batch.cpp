#include "protocol/RecoveredBattleVitalsBatch.h"
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Codec=god2::RecoveredBattleVitalsBatch;
void counter_checks() {
    Codec::Bytes original{};
    for(std::size_t i=0;i<original.size();++i)original[i]=static_cast<std::uint8_t>(i*37u+11u);
    original[0]=0x88;
    const auto unchanged=original;
    for(const std::uint64_t counter:{0ull,1ull,255ull,256ull,65535ull,65536ull,0xffffffffull}) {
        const auto updated=Codec::with_counter(original,counter);
        const auto parsed=Codec::parse_logical(updated);
        if(!parsed || parsed->counter_bits()!=counter || original!=unchanged)
            throw std::runtime_error("Full DWORD counter projection regression");
        for(std::size_t i=0;i<original.size();++i) {
            const auto expected=i>=1&&i<=4?static_cast<std::uint8_t>(counter>>(8*(i-1))):original[i];
            if(updated[i]!=expected)throw std::runtime_error("Counter update changed actor/opaque bytes");
        }
        for(std::size_t slot=0;slot<Codec::slots;++slot) {
            const auto before=*Codec::parse_logical(original)->at(slot);
            const auto after=*parsed->at(slot);
            if(before.hp!=after.hp || before.mp!=after.mp)
                throw std::runtime_error("Counter update changed stored vitals");
        }
    }
    for(const auto overflow:std::array<std::uint64_t,2>{0x100000000ull,std::numeric_limits<std::uint64_t>::max()}) {
        bool threw=false;
        try{(void)Codec::with_counter(original,overflow);}catch(const std::invalid_argument&){threw=true;}
        if(!threw || original!=unchanged)throw std::runtime_error("Overflowing counter accepted or input modified");
    }
    auto wrong=original;wrong[0]=0x83;bool threw=false;
    try{(void)Codec::with_counter(wrong,256);}catch(const std::invalid_argument&){threw=true;}
    if(!threw)throw std::runtime_error("Wrong counter opcode accepted");
}
}

int main() {
    using Codec = god2::RecoveredBattleVitalsBatch;
    static_assert(!Codec::runtime_emission_enabled);
    counter_checks(); // Preserve the existing stdin/stdout codec-probe contract.
    std::string line;
    while (std::getline(std::cin, line)) {
        std::vector<std::uint8_t> raw;
        for (std::size_t i = 0; i + 1 < line.size(); i += 2)
            raw.push_back(static_cast<std::uint8_t>(std::stoul(line.substr(i, 2), nullptr, 16)));
        const auto record = Codec::parse_logical(raw);
        if (!record) { std::cout << "reject\n"; continue; }
        const auto before = raw;
        std::fill(raw.begin(), raw.end(), std::uint8_t{0});
        const auto encoded = Codec::encode_logical(*record);
        if (!std::equal(encoded.begin(), encoded.end(), before.begin(), before.end()) ||
            record->at(14) || record->at(std::numeric_limits<std::size_t>::max()))
            throw std::runtime_error("Owning record/bounds regression");
        for (std::size_t slot = 0; slot < Codec::slots; ++slot) {
            const auto value = record->at(slot);
            std::cout << value->hp << ' ' << value->mp << ' ';
        }
        std::cout << '\n';
    }
}
