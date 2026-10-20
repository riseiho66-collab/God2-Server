#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
namespace god2 {
// Current aaf0:516AE0/52C520/52A8D0 -> native state97/525B90.
// WORD5 and WORD7 are flat positions, NOT target masks. WORD9 is a
// zero/nonzero success gate. Actual six-layer swap is renderer-deferred;
// parsing, preparing or writing this record does not observe its completion.
struct RecoveredBattleRowSwapResult {
    using Bytes=std::array<std::uint8_t,15>;
    class Record {
    public:
        std::uint8_t source()const noexcept{return raw_[2];}
        std::uint8_t group()const noexcept{return raw_[3];}
        std::uint16_t from()const noexcept{return word(raw_,5);}
        std::uint16_t to()const noexcept{return word(raw_,7);}
        std::uint16_t success_operand()const noexcept{return word(raw_,9);}
    private:
        friend struct RecoveredBattleRowSwapResult;
        explicit Record(Bytes raw):raw_(raw){}
        Bytes raw_;
    };
    static std::optional<Record> parse(std::span<const std::uint8_t> raw)noexcept {
        if(raw.size()!=15||raw[0]!=0x83||raw[1]!=9||raw[2]>=28||word(raw,5)>=28||word(raw,7)>=28)return {};
        Bytes owned;std::copy(raw.begin(),raw.end(),owned.begin());return Record(owned);
    }
    static Bytes encode(const Record& r)noexcept{return r.raw_;}
    static Record positioned(const Record& prototype,std::uint8_t source,std::uint8_t from,std::uint8_t to){
        if(source>=28||from>=28||to>=28||from==to||!prototype.success_operand())
            throw std::invalid_argument("Row swap needs actual distinct pair and complete successful native template");
        auto raw=prototype.raw_;raw[2]=source;put(raw,5,from);put(raw,7,to);return Record(raw);
    }
private:
    static std::uint16_t word(std::span<const std::uint8_t> b,std::size_t p)noexcept{return std::uint16_t(b[p])|(std::uint16_t(b[p+1])<<8);}
    static void put(Bytes& b,std::size_t p,std::uint16_t n)noexcept{b[p]=std::uint8_t(n);b[p+1]=std::uint8_t(n>>8);}
};
}
