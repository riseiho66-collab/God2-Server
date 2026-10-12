#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c WORLD46B46E/46B480 -> primary UI Main+A7F2F6C (U).
// E8 ->4E8550 copies body0 to BYTE [P+15E], P=[U+8688C], then
// rereads P before4E8580(P+90). E9 ->4F9980 copies body0 to U8B747,
// clears WORD U8B744 and BYTE U8B746, then invokes opaque children.
// These initial writes neither certify final/current objects nor identify
// owned items, PetEgg list contents, a server operation or causal reply.
struct RecoveredWorldUiByteUpdates {
    enum class Kind:std::uint8_t {IndirectContextE8=0xe8, PrimaryContextE9=0xe9};
    static constexpr std::size_t logical_size=2;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        Kind kind() const noexcept {return kind_;}
        // Full BYTE, without status whitelist, mask or boolean coercion.
        std::uint8_t raw_byte() const noexcept {return raw_;}
    private:
        friend struct RecoveredWorldUiByteUpdates;
        Record(Kind kind,std::uint8_t raw):kind_(kind),raw_(raw) {}
        Kind kind_;
        std::uint8_t raw_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || (bytes[0]!=0xe8 && bytes[0]!=0xe9))return {};
        return Record(static_cast<Kind>(bytes[0]),bytes[1]);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {
        return {static_cast<std::uint8_t>(record.kind_),record.raw_};
    }
};
}
