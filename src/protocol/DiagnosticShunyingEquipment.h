#pragma once
#include <array>
#include <cstdint>
#include <vector>

namespace god2 {
// CUSTOM-0058: explicitly authorized isolated character 6 / test equipment.
// This is fixture data, not a general grant, original item-generation formula,
// or an authoritative item->HeroDoll mapping. Call ONLY behind the manual test
// gate AND the exact account/character/name guard used by that fixture.
// Native slots: 30 head, 31 armor, 32 gloves, 33 shoes, 34 weapon (498030,
// 5905F0 ProgramMsg labels64..68). Native3B copies20 bytes;41 sets occupancy.
// Item definitions are pinned gamedata.csvZ lines5805/5460/5884/5975/4907.
// 4B45B0/4B4690 decode physical +7, magic +12, Str/Con/Int/Speed +8..11;
// remaining bytes preserve the established CUSTOM-0046 fixture template.
struct DiagnosticShunyingEquipment {
    struct Item { std::uint8_t slot; std::array<std::uint8_t,20> instance; };
    inline static constexpr std::array<Item,5> items{{
        {30,{0x92,0x05,1,0,0,0,0,23,0,0,30,0,7,0,0,0,0,0,0,0}},
        {31,{0x02,0x04,1,0,0,0,0,25,0,30,0,0,7,0,0,0,0,0,0,0}},
        {32,{0xf6,0x05,1,0,0,0,0,16,30,0,0,0,16,0,0,0,0,0,0,0}},
        {33,{0x5a,0x06,1,0,0,0,0,16,0,0,0,30,16,0,0,0,0,0,0,0}},
        {34,{0x7e,0x00,1,0,0,0,0,61,48,0,48,0,19,0,0,0,0,0,0,0}}
    }};
    static std::vector<std::uint8_t> projection() {
        std::vector<std::uint8_t> out;
        out.reserve(150);
        for(const auto& item:items) {
            out.insert(out.end(),{0x41,item.instance[0],item.instance[1],item.slot,1,
                                 0x3b,1,item.slot,0,0});
            out.insert(out.end(),item.instance.begin(),item.instance.end());
        }
        return out;
    }
};
}
