#pragma once
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Read-only native1D payloadA8. Named bit groups describe consumer operations,
// not backend entitlement, GM/ban permissions or a flag issuer/default.
class CnIssuedLoginFlags {
public:
    static std::optional<CnIssuedLoginFlags> read(std::span<const std::uint8_t> record) {
        if(record.size()!=205 || record[0]!=0x1d)return std::nullopt;
        return CnIssuedLoginFlags(record[1+0xa8]);
    }
    std::uint8_t raw() const {return raw_;}
    // 0047FE30 ->network+40EC ->SendMessage040A ->0044AAB0 ->00449440
    // ->UI+17AABE. Local provider mode3/selection presentation conditions are
    // separate and do not authorize a service to manufacture this value.
    std::uint8_t provider_selector() const {return raw_>>6;}
    // 1 and3 invoke distinct native account notices;2 has no such branch.
    std::uint8_t account_notice_selector() const {return (raw_>>4)&3;}
    // Native tests only nonzero here and invokes00567AA0. Preserve all4 bits;
    // do not invent a meaning or four independent permissions.
    std::uint8_t membership_notice_operand() const {return raw_&15;}
private:
    explicit CnIssuedLoginFlags(std::uint8_t raw):raw_(raw) {}
    std::uint8_t raw_;
};
}
