#pragma once
#include "cn/assets/CnNativeSkillCatalog.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Readonly view of a complete CN582f/cbspec2-857b declared110-byte record.
// 0054FFC0's skill branches (raw command kinds03/17 hex) consume BYTE0/1,
// WORD3E and BYTE45. The command operand is a zero-extended raw ID/kind WORD;
// target interpretation also depends on actual native owner/branch state.
// This view preserves every unknown byte. It does not qualify the supplied
// catalog's hash, lifetime, source revision, learned skills, MP or cast rights.
// The actual catalog owner retains and qualifies provenance/current separately.
struct CnBattleSkillDefinition {
    static constexpr std::size_t record_size=CnNativeSkillCatalog::record_bytes;
    using RawRecord=std::array<std::uint8_t,record_size>;
    class Record {
    public:
        std::span<const std::uint8_t> raw_bytes() const noexcept {return raw_;}
        std::uint8_t definition_id() const noexcept {return raw_[0];}
        std::uint8_t kind() const noexcept {return raw_[1];}
        std::uint16_t raw_key_word() const noexcept {return word16(0);}
        std::uint16_t raw_word_3e() const noexcept {return word16(0x3e);}
        std::uint8_t raw_target_mode_byte_45() const noexcept {return raw_[0x45];}
        bool operator==(const Record&) const=default;
    private:
        friend struct CnBattleSkillDefinition;
        explicit Record(RawRecord raw):raw_(raw){}
        std::uint16_t word16(std::size_t at) const noexcept {
            return std::uint16_t(raw_[at])|(std::uint16_t(raw_[at+1])<<8);
        }
        RawRecord raw_;
    };
    // Structural view limited to this pinned catalog's declared identities.
    // Shared catalog callers retain their actual source/current evidence; this
    // function neither constructs nor substitutes a native Source revision.
    static std::optional<Record> read_raw(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=record_size || raw[1]>=CnNativeSkillCatalog::declared_counts.size() ||
           !raw[0] || raw[0]>CnNativeSkillCatalog::declared_counts[raw[1]])return {};
        RawRecord retained;
        std::copy(raw.begin(),raw.end(),retained.begin());
        return Record(retained);
    }
    static std::optional<Record> from_record(const CnNativeSkillCatalog::Record& record) noexcept {
        if(record.kind!=record.raw[1] || record.definition_id!=record.raw[0])return {};
        return read_raw(record.raw);
    }
};
}
