#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Pinned mapped149c S2C83 consumer view, exactly actions02 and0C.
// RVA116BB1/116C38 obtains source and target masks;117183 forwards logical+1
// to12C520. Cases12C645/12C672 forward logical BYTE+3 to12A8D0.
// Common setup writes actor+1E7 from that operand and actor+1E9 from action.
// Its table12AB9C sends02 to12AA78 (actor+1EB=03),0C to12AB93 (return).
// These conditional native stores describe presentation, not game authority.
// Actor presence, source WORD+1A<0x1000, current batch/phase and lifetime remain
// caller obligations. The first stage's local-owner flag update is separate.
// No defense/timeout/revival meaning, official server pairing or rendering is
// inferred. Action08 has separate research evidence and is outside this view.
struct RecoveredBattleActorControl {
    static constexpr std::size_t logical_size=15;
    static constexpr bool runtime_emission_enabled=false;
    static constexpr bool runtime_mutation_enabled=false;
    static constexpr char image_sha256[]=
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    using Bytes=std::array<std::uint8_t,logical_size>;
    enum class Action : std::uint8_t { Action02=0x02, Action0C=0x0c };
    enum class SetupEffect : std::uint8_t {
        Action02CommonFieldsAndState03,
        Action0CCommonFieldsOnly
    };
    class Record {
    public:
        Action action() const noexcept {return static_cast<Action>(bytes_[1]);}
        std::uint8_t source() const noexcept {return bytes_[2];}
        std::uint8_t logical3_operand() const noexcept {return bytes_[3];}
        std::array<std::uint16_t,2> target_masks() const noexcept {
            return {word(5),word(7)};
        }
        std::uint8_t opaque4() const noexcept {return bytes_[4];}
        std::span<const std::uint8_t,6> opaque_tail() const noexcept {
            return std::span<const std::uint8_t,logical_size>(bytes_).subspan<9,6>();
        }
        SetupEffect setup_effect() const noexcept {
            return action()==Action::Action02 ? SetupEffect::Action02CommonFieldsAndState03 :
                SetupEffect::Action0CCommonFieldsOnly;
        }
    private:
        friend struct RecoveredBattleActorControl;
        explicit Record(Bytes bytes) noexcept:bytes_(bytes){}
        std::uint16_t word(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(bytes_[at]|(std::uint16_t{bytes_[at+1]}<<8));
        }
        Bytes bytes_;
    };
    // Shape/action filters delimit this view; other83 actions remain unqualified
    // here. Native116C0F..116C1B rejects source positions outside0..27.
    // No opposing-side, one-target, nonempty-mask or HP-loss restriction is
    // imported from attack1/3. Native116C5F..116C75 can fall back to source;
    // all raw mask bits and uninterpreted bytes are preserved, never normalized.
    static std::optional<Record> parse(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=0x83 ||
           (raw[1]!=0x02 && raw[1]!=0x0c) || raw[2]>=28)return std::nullopt;
        Bytes bytes;
        std::copy(raw.begin(),raw.end(),bytes.begin());
        return Record(bytes);
    }
    static Bytes encode(const Record& record) noexcept {return record.bytes_;}
};
}
