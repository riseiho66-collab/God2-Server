#pragma once
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
namespace god2 {
// Current native83/1 basic and83/3 scalar attack presentation only.
// The battle83 selector has 23 values (1..17 hex) and a second actor-action
// table. Action17 shares both case RVAs with3, but is NOT licensed by this
// scalar codec: shared dispatch does not prove the same effect/ownership.
// See s2c-battle83-action-frontier-v1.json; other actions need separate routes.
// Format field evidence:116AE0 ->12C520 ->12A8D0/12B060; signed display
//12B48E; outcome table12C000/171610. Does not recover a damage formula,
// skill ownership, critical display, original server pairing or full83 grammar.
// Normal Type3 first116DC1 associates THIS observed id/kind in actor+DF8,
// then117183 ->12C731 scans51 entries; see frontier-v4-pk-skill-cache.json.
// This is not a complete carried list or ownership proof; catalog/resources,
// fresh actor lifetime, native cache bounds and rendering still matter.
struct RecoveredBattleAttackPresentation {
    using Bytes=std::array<std::uint8_t,15>;
    class Record {
    public:
        bool basic()const noexcept{return bytes_[1]==1;}
        std::uint8_t source()const noexcept{return bytes_[2];}
        std::uint8_t group()const noexcept{return bytes_[3];}
        std::optional<std::uint16_t> skill_key()const noexcept{
            if(basic())return {};
            return static_cast<std::uint16_t>((std::uint16_t{bytes_[12]}<<8)|bytes_[11]);
        }
    private:
        friend struct RecoveredBattleAttackPresentation;
        explicit Record(Bytes bytes):bytes_(bytes){}
        Bytes bytes_;
    };
    // Retain the original full raw record: no implicit zero/diagnostic template.
    // Excludes basic status0B/default1C and non-damage skill selectors/effects.
    static std::optional<Record> parse(std::span<const std::uint8_t> input)noexcept{
        if(input.size()!=15||input[0]!=0x83||input[2]>=28||
           (input[1]!=1&&input[1]!=3))return {};
        const auto masks=std::array<std::uint16_t,2>{word(input,5),word(input,7)};
        if(((masks[0]|masks[1])&0xc000)||std::popcount(masks[0])+std::popcount(masks[1])!=1||
           masks[input[2]/14]!=0)return {};
        if(input[1]==1){if(input[11]!=0||(input[12]!=0&&input[12]!=28))return {};}
        else if(!input[11]||input[12]>1||input[13]!=0||(input[14]!=0&&input[14]!=28))return {};
        Bytes bytes;std::copy(input.begin(),input.end(),bytes.begin());return Record(bytes);
    }
    static Bytes encode(const Record& record)noexcept{return record.bytes_;}
    // CUSTOM-0086 binds the already-qualified raw presentation to ONE actual
    // shared hit. Unknown bits, skill identity and batch group are preserved.
    static Bytes hit(const Record& prototype,std::uint8_t source,std::uint8_t target,
                     std::uint64_t hp_loss,bool target_alive){
        if(source>=28||target>=28||source/14==target/14||hp_loss>0x7fff)
            throw std::invalid_argument("PK scalar attack presentation outside recovered range");
        auto bytes=prototype.bytes_;bytes[2]=source;
        bytes[5]=bytes[6]=bytes[7]=bytes[8]=0;
        const auto mask=static_cast<std::uint16_t>(1u<<(target%14));const auto at=5+2*(target/14);
        bytes[at]=static_cast<std::uint8_t>(mask);bytes[at+1]=static_cast<std::uint8_t>(mask>>8);
        const auto delta=static_cast<std::uint16_t>(-static_cast<std::int32_t>(hp_loss));
        bytes[9]=static_cast<std::uint8_t>(delta);bytes[10]=static_cast<std::uint8_t>(delta>>8);
        bytes[prototype.basic()?12:14]=target_alive?28:0;
        return bytes;
    }
private:
    static std::uint16_t word(std::span<const std::uint8_t> input,std::size_t at)noexcept{
        return static_cast<std::uint16_t>(input[at]|(std::uint16_t{input[at+1]}<<8));
    }
};
}
