#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW S2C83/action0D, logical WORD+11 == 0, received playback data only.
// Current aaf0 client: 0052C520/0052CAAA stores logical WORD+9 at
// actor+280+2*manager[30B]. 0052C000 maps logical BYTE+13 via00571600;
// 0052C0C0 stores indexed+27A/+27D. 00528660 consumes that bank later.
// This is distinct from RecoveredBattleDelta's nonzero WORD+11 branch.
// No DoT interval, turn count, skill magnitude or server authority is inferred.
struct RecoveredBattleDeferredEffect {
    static constexpr std::size_t logical_size=15;
    static constexpr bool runtime_emission_enabled=false;
    static constexpr bool runtime_mutation_enabled=false;
    static constexpr char image_sha256[]=
        "aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48";
    using Bytes=std::array<std::uint8_t,logical_size>;

    class Record {
    public:
        // Wire source position only. Binding the playback consumer actor needs
        // 00516AE0 ->0052C520 arguments and the actual actor lookup context.
        std::uint8_t source() const noexcept {return bytes_[2];}
        std::uint8_t logical3_operand() const noexcept {return bytes_[3];}
        std::uint8_t opaque4() const noexcept {return bytes_[4];}
        std::array<std::uint16_t,2> target_masks() const noexcept {
            return {word(5),word(7)};
        }
        std::uint16_t received_word_bits() const noexcept {return word(9);}
        // This bank's selected playback consumers sign-extend the WORD.
        // It is not a shared64 value, a general83 amount, or a formula input.
        std::int32_t signed_received_word() const noexcept {
            const auto value=received_word_bits();
            return value<0x8000 ? std::int32_t{value} : std::int32_t{value}-65536;
        }
        std::uint8_t result_code() const noexcept {return bytes_[13];}
        // Raw00571610 table index, not the mapped actor type.
        std::uint8_t effect_selector_code() const noexcept {return bytes_[14];}
        // Exact0052C000 table lookup only; not the later actor state after
        // 0052C0C0's target-dependent guards, and not a probability roll.
        std::optional<std::uint8_t> mapped_result_state() const noexcept {
            constexpr std::array<std::uint8_t,13> states{
                0x0f,0x7a,0x7b,0x7c,0x7d,0x7e,0x7f,0x03,0x05,0x87,0x07,0x82,0x58};
            const auto code=result_code();
            if(code>=states.size())return std::nullopt;
            return states[code];
        }
    private:
        friend struct RecoveredBattleDeferredEffect;
        explicit Record(Bytes bytes) noexcept:bytes_(bytes){}
        std::uint16_t word(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(bytes_[at]|(std::uint16_t{bytes_[at+1]}<<8));
        }
        Bytes bytes_;
    };

    // Caller establishes S2C direction and battle context. The native source
    // guard bounds positions0..27; no one-target/opposing-side/known-result
    // restriction is borrowed from scalar attacks. Every accepted raw byte
    // survives encode, including masks, opaque bytes and unmapped result codes.
    // manager30B/30C sequencing, actor lifetime and admission remain unproved
    // caller obligations; this view neither allocates a bank nor applies HP.
    static std::optional<Record> parse(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=0x83 || raw[1]!=0x0d ||
           raw[2]>=28 || raw[11]!=0 || raw[12]!=0)return std::nullopt;
        Bytes bytes;
        std::copy(raw.begin(),raw.end(),bytes.begin());
        return Record(bytes);
    }
    static Bytes encode(const Record& record) noexcept {return record.bytes_;}
};
}
