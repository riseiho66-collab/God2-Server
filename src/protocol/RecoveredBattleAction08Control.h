#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW S2C83/action08 only, pinned mapped149c. First116CC8 reads logical
// WORD+9 as a zero/nonzero condition for B+488 on acting side0; side1
// preserves that flag. Actor12C69F ->12A8D0 passes logical BYTE+3 and
// action08 with last arg0. Conditional setup writes source actor+1E7/+1E9,
// then+1EB=0x88/+232=0. These are consumer branches, not defense/turn rules.
// The outer current-batch gate, source/target actor presence, unsigned source
// WORD+1A<0x1000, actor lifetime and manager binding remain caller obligations.
// Normal first-stage return1 does not establish that actor stores occurred.
struct RecoveredBattleAction08Control {
    static constexpr std::size_t logical_size=15;
    static constexpr bool runtime_emission_enabled=false;
    static constexpr bool runtime_mutation_enabled=false;
    static constexpr char image_sha256[]=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    using Bytes=std::array<std::uint8_t,logical_size>;
    enum class FirstStageBranch {
        Side0ClearFlag488,
        Side0SetFlag488,
        Side1PreserveFlag488
    };
    class Record {
    public:
        std::uint8_t source() const noexcept {return bytes_[2];}
        std::uint8_t side() const noexcept {return source()/14;}
        std::uint8_t slot() const noexcept {return source()%14;}
        std::uint8_t logical3_operand() const noexcept {return bytes_[3];}
        std::array<std::uint16_t,2> target_masks() const noexcept {
            return {word(5),word(7)};
        }
        std::uint16_t word9_operand() const noexcept {return word(9);}
        // Describes the branch only when the actual current native dispatcher
        // admits the record; this view never reads or mutates a battle object.
        FirstStageBranch first_stage_branch() const noexcept {
            if(side()==1)return FirstStageBranch::Side1PreserveFlag488;
            return word9_operand()==0 ? FirstStageBranch::Side0ClearFlag488 :
                FirstStageBranch::Side0SetFlag488;
        }
        std::uint8_t opaque4() const noexcept {return bytes_[4];}
        std::span<const std::uint8_t,4> opaque_tail() const noexcept {
            return std::span<const std::uint8_t,logical_size>(bytes_).subspan<11,4>();
        }
    private:
        friend struct RecoveredBattleAction08Control;
        explicit Record(Bytes bytes) noexcept:bytes_(bytes){}
        std::uint16_t word(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(bytes_[at]|(std::uint16_t{bytes_[at+1]}<<8));
        }
        Bytes bytes_;
    };
    // Caller establishes TW S2C direction and current battle context. Source
    //0..27 is the actual116C0F/116C18 guard. No actor/state predicate is
    // synthesized here. Masks stay raw, including high bits, empty masks and
    // same-side/multiple targets; the native first-bit scan may fall back to
    // source. No action01/03 damage, target or skill constraints are borrowed.
    static std::optional<Record> parse(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=0x83 || raw[1]!=0x08 || raw[2]>=28)
            return std::nullopt;
        Bytes bytes;
        std::copy(raw.begin(),raw.end(),bytes.begin());
        return Record(bytes);
    }
    static Bytes encode(const Record& record) noexcept {return record.bytes_;}
};
}
