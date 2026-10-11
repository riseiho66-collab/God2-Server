#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Original E3 world receiver 46919E -> 4A2B70; panel 4A1CF0.
// First-generation instance status, not a wild-monster or growth formula.
struct RecoveredPet1Stats {
    static constexpr std::uint8_t opcode=0xe3;
    static constexpr std::size_t logical_size=53;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    struct Vitals {std::uint16_t current_hp,maximum_hp,current_mp,maximum_mp;};
    struct CombatValues {std::uint16_t physical_attack,physical_defense,magical_attack,magical_defense;};
    struct Attributes {std::uint16_t strength,constitution,intelligence,speed;};
    struct Elements {std::uint16_t metal,wood,water,fire,earth;};
    class Record {
    public:
        std::uint16_t metadata_key() const noexcept {return word(0x1c);}
        std::uint8_t slot() const noexcept {return bytes_[0x27];}
        std::uint8_t level() const noexcept {return bytes_[0x24];}
        Vitals vitals() const noexcept {return {word(0),word(2),word(4),word(6)};}
        CombatValues combat_values() const noexcept {
            return {static_cast<std::uint16_t>(dword(8)&0xfff),static_cast<std::uint16_t>(dword(12)&0xfff),
                static_cast<std::uint16_t>(dword(16)&0xfff),static_cast<std::uint16_t>(dword(20)&0xfff)};
        }
        Attributes attributes() const noexcept {return {
            static_cast<std::uint16_t>((dword(16)>>12)&0x3ff),static_cast<std::uint16_t>(dword(16)>>22),
            static_cast<std::uint16_t>((dword(20)>>12)&0x3ff),static_cast<std::uint16_t>(dword(20)>>22)};}
        Attributes allocation_bonuses() const noexcept {return {
            static_cast<std::uint16_t>(dword(24)>>24),bytes_[0x1f],bytes_[0x20],bytes_[0x21]};}
        Elements elements() const noexcept {return {
            static_cast<std::uint16_t>((dword(8)>>12)&0x3ff),static_cast<std::uint16_t>(dword(8)>>22),
            static_cast<std::uint16_t>((dword(12)>>12)&0x3ff),static_cast<std::uint16_t>(dword(12)>>22),
            static_cast<std::uint16_t>(dword(24)&0x3ff)};}
        // 4A1D63..4A1D9C: percentage display * binary32(.01), not accumulated EXP.
        std::uint16_t progress_display_raw14() const noexcept {return static_cast<std::uint16_t>((dword(24)>>10)&0x3fff);}
        std::uint8_t life_display_raw() const noexcept {return bytes_[0x23];}
        std::uint16_t remaining_points() const noexcept {return word(0x24);}
        std::uint8_t rebirth_count() const noexcept {return bytes_[0x28];}
        // Raw timestamp consumed by CRT localtime. Timezone/unit not qualified here.
        std::uint32_t fusion_expiry_raw() const noexcept {return dword(0x30);}
        std::span<const std::uint8_t,52> opaque_body() const noexcept {
            return std::span<const std::uint8_t,logical_size>(bytes_).subspan<1,52>();
        }
    private:
        friend struct RecoveredPet1Stats;
        explicit Record(const LogicalRecord& bytes):bytes_(bytes) {}
        std::uint16_t word(std::size_t offset) const noexcept {
            return static_cast<std::uint16_t>(bytes_[offset+1]|(std::uint16_t{bytes_[offset+2]}<<8));
        }
        std::uint32_t dword(std::size_t offset) const noexcept {
            return std::uint32_t{word(offset)}|(std::uint32_t{word(offset+2)}<<16);
        }
        LogicalRecord bytes_;
    };
    // Original A29A0 integer gate, separate actual metadata/ownership required.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode || bytes[0x27]<42 || bytes[0x27]>44) return {};
        const auto key=static_cast<std::uint16_t>(bytes[0x1d]|(std::uint16_t{bytes[0x1e]}<<8));
        if(!((key>=0x3391 && key<=0x3778)||(key>=0x5dc1 && key<=0x6d60))) return {};
        LogicalRecord owned;std::copy(bytes.begin(),bytes.end(),owned.begin());return Record(owned);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
};
}
