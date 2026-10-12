#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c WORLD4691EB ->4D6D20: logical13, body12. ECX is the
// primary UI context at WORLD+A7F2F6C, also used by E5 family1.
// These incoming scalar copies do not decode an owned20-byte instance or
// establish a pet grant, timer rule, request pairing or authoritative issuer.
struct RecoveredPetEggStatus {
    static constexpr std::uint8_t opcode=0xe6;
    static constexpr std::size_t logical_size=13;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    struct DirectCopy {
        std::uint8_t primary_context_offset;
        std::uint32_t incoming_value;
    };
    class Record {
    public:
        // Unconditional initial copies, before handle/key gates and opaque
        // children. Conditional4D5970 can clear context44's low28 bits;
        // these values must not be used as the final context or E5 input.
        std::array<DirectCopy,3> direct_copies() const noexcept {
            return {{{0x44,dword(1)},{0x48,dword(5)},{0x4c,dword(9)}}};
        }
    private:
        friend struct RecoveredPetEggStatus;
        explicit Record(const LogicalRecord& bytes):bytes_(bytes) {}
        std::uint32_t dword(std::size_t offset) const noexcept {
            return std::uint32_t{bytes_[offset]}|(std::uint32_t{bytes_[offset+1]}<<8)|
                (std::uint32_t{bytes_[offset+2]}<<16)|(std::uint32_t{bytes_[offset+3]}<<24);
        }
        LogicalRecord bytes_;
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        LogicalRecord raw;std::copy(bytes.begin(),bytes.end(),raw.begin());return Record(raw);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes_;}
};
}
