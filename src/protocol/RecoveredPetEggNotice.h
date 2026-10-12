#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c: WORLD4691FD -> primary UI WORLD+A7F2F6C ->4D6340.
// Fixed logical2/body1. The receiver selects branches using body0 &7F;
// child4D9990 also reads the raw high bit for statuses37/38/39.
// Local type/row predicates and opaque children do not establish a server
// result, owned-item selection, request pairing, or final UI/current state.
struct RecoveredPetEggNotice {
    static constexpr std::uint8_t opcode=0xe7;
    static constexpr std::size_t logical_size=2;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint8_t raw_status() const noexcept {return raw_;}
        std::uint8_t status_low7() const noexcept {return raw_ & 0x7f;}
    private:
        friend struct RecoveredPetEggNotice;
        explicit Record(std::uint8_t raw):raw_(raw) {}
        std::uint8_t raw_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        return Record(bytes[1]);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {
        return {opcode,record.raw_};
    }
};
}
