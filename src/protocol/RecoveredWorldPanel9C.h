#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c S2C9C: logical49/body48; actual WORLD468C8C -> primary UI
// Main+A7F2F6C ->4F34C0. Signed handle U232E22 gates its direct reads.
// Body pointers0/10h go to an opaque UI child; no fixed-size/terminated
// string contract follows from those addresses. This is not a U0A list,
// owned-item snapshot, operation result, authoritative issuer or causal reply.
struct RecoveredWorldPanel9C {
    static constexpr std::uint8_t opcode=0x9c;
    static constexpr std::size_t logical_size=49,body_size=48;
    static constexpr bool runtime_emission_enabled=false, runtime_mutation_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::span<const std::uint8_t,body_size> raw_body() const noexcept {
            return std::span<const std::uint8_t,body_size>{bytes_.data()+1,body_size};
        }
        // Raw incoming DWORDs; no display meaning, signed game domain or
        // final/current UI state is assigned to the native operands.
        std::uint32_t raw_dword20() const noexcept {return dword(0x21);}
        std::uint32_t raw_dword24() const noexcept {return dword(0x25);}
    private:
        friend struct RecoveredWorldPanel9C;
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
