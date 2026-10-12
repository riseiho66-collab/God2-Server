#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c S2CF4: WORLD469233 supplies body and the same primary U
// Main+A7F2F6C to4A3380. The direct unsigned index<24 branch copies
// bodyWORD2 into U0A+2*index, the array later read by4DC710/4DC880.
// No owned item, eligibility, B1 pairing or final post-child state follows.
struct RecoveredPetRoomListEntry {
    static constexpr std::uint8_t opcode=0xf4;
    static constexpr std::size_t logical_size=5;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    struct DirectCopy {
        std::uint8_t primary_context_offset;
        std::uint16_t incoming_word;
    };
    class Record {
    public:
        std::uint8_t raw_index() const noexcept {return bytes_[1];}
        // BodyBYTE1 is retained even though the direct receiver does not read it.
        std::uint8_t raw_body_byte1() const noexcept {return bytes_[2];}
        std::uint16_t raw_word() const noexcept {
            return static_cast<std::uint16_t>(std::uint16_t{bytes_[3]}|
                (std::uint16_t{bytes_[4]}<<8));
        }
        // This is the initial direct-copy operand, without a WORD value gate.
        // Initial index>=24 invokes an opaque assertion before rereading the
        // index; that path is not modeled here. All records remain lossless.
        // No server mutation or current array is supplied.
        std::optional<DirectCopy> direct_copy() const noexcept {
            if(raw_index()>=24)return {};
            return DirectCopy{static_cast<std::uint8_t>(0x0a+2*raw_index()),raw_word()};
        }
    private:
        friend struct RecoveredPetRoomListEntry;
        explicit Record(const LogicalRecord& bytes):bytes_(bytes) {}
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        LogicalRecord raw;std::copy(bytes.begin(),bytes.end(),raw.begin());return Record(raw);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
};
}
