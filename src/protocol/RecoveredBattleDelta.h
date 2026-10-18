#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// 83/0D existing-action, nonzero WORD+11 branch of 0052C520.
// Received results only: does not calculate attack/defense or skill power.
struct RecoveredBattleDelta {
    using Bytes=std::array<std::uint8_t,15>;
    struct Accumulator {std::uint32_t hp{},mp{};bool operator==(const Accumulator&) const=default;};
    class Record {
    public:
        std::uint8_t source() const noexcept{return bytes_[2];}
        std::uint16_t targetMask(unsigned side) const noexcept{return side<2?word(5+side*2):0;}
        // Current TW516AE0 ->51E5E0 scans side0 slots0..13, then side1,
        // and returns at the first set bit. One52C520 invocation receives
        // that selected side/slot; the raw masks are not an effect fan-out.
        // This is mask selection only: kind2 overrides the target with source,
        // and actor lookup/playback eligibility still belong to the caller.
        std::optional<std::uint8_t> selected_mask_target() const noexcept {
            for(unsigned side=0;side<2;++side) for(unsigned slot=0;slot<14;++slot)
                if(targetMask(side)&(1u<<slot))
                    return static_cast<std::uint8_t>(side*14+slot);
            return std::nullopt;
        }
        std::uint16_t amountBits() const noexcept{return word(9);}
        std::int32_t amount() const noexcept{return amountBits()<0x8000?amountBits():std::int32_t{amountBits()}-65536;}
        std::uint8_t selector() const noexcept{return bytes_[13];}
        // Nonzero logical WORD+11 copied to actor+4D0[index]. Kinds2/3
        // select different actors/sign handling in0052B870, not kind1 deltas.
        std::uint16_t accumulator_kind_bits() const noexcept{return word(11);}
        // 0052CB8E/0052CBDE reads payload+D (logical14), then0052BFC0.
        // Native table maps0 to death state9,28 to ordinary live state0.
        std::uint8_t targetOutcome() const noexcept{return bytes_[14];}
        // Receive-side accumulator arithmetic only. Selector20 replaces HP
        // accumulator bits, but0052B870/0052BC50 skip scalar HP/MP application
        // when its stored selector is20. This is not a ready-to-apply delta.
        Accumulator accumulate(Accumulator current) const noexcept {
            const auto delta=static_cast<std::uint32_t>(amount());
            if(selector()<=5)current.hp+=delta;
            else if(selector()==9)current.mp+=delta;
            else if(selector()==20)current.hp=delta;
            return current;
        }
    private:
        friend struct RecoveredBattleDelta;
        explicit Record(Bytes bytes):bytes_(bytes){}
        std::uint16_t word(std::size_t offset) const noexcept {
            return static_cast<std::uint16_t>(bytes_[offset]|(std::uint16_t{bytes_[offset+1]}<<8));
        }
        Bytes bytes_;
    };
    static std::optional<Record> parse(std::span<const std::uint8_t> input) noexcept {
        if(input.size()!=15 || input[0]!=0x83 || input[1]!=0x0d || input[2]>=28 ||
           !(input[11]|input[12]) || ((input[6]|input[8])&0xc0) ||
           !(input[5]|input[6]|input[7]|input[8]))return std::nullopt;
        const auto selector=input[13];
        if(!(selector<=5 || selector==7 || selector==8 || selector==9 || selector==20))return std::nullopt;
        Bytes bytes;std::copy(input.begin(),input.end(),bytes.begin());return Record(bytes);
    }
    static Bytes encode(const Record& record) noexcept{return record.bytes_;}
    // 00528A70/00528AC0: DWORD wrapping ADD, sign floor, signed cap CMP.
    // Explicit bit tests avoid signed overflow and implementation-defined casts.
    static std::uint32_t apply(std::uint32_t current,std::uint32_t delta,std::uint32_t cap) noexcept {
        const std::uint32_t sum=current+delta;
        if(sum&0x80000000u)return 0;
        return (cap&0x80000000u) || sum>cap ? cap:sum;
    }
};
}
