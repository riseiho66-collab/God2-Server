#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Same149c1b45 native: 401252/469369 select logical DA15. Source qualification
// and bounded consumers are retained in round226/227/229. This independent
// wire record does not promote the old6bf fixture or grant equipment authority.
// Remote4FC130 updates only odd-byte high3 bits; this is NOT an after6F cache.
class RecoveredTaiwanPlayerAppearanceUpdate {
public:
    static constexpr std::uint8_t opcode=0xda;
    static constexpr std::size_t logical_size=15;
    // Same149c DA consumer: logical3/4 transformation WORD,5/6 raw
    // scalars,7..14 packed components. These are independent of6F offsets.
    static constexpr std::size_t transform_offset=3,raw_scalar5_offset=5,
        raw_scalar6_offset=6,components_offset=7,component_bytes=8;
    using Bytes=std::array<std::uint8_t,logical_size>;
    class Record {
    public:
        std::uint16_t actor_identity() const noexcept {
            return std::uint16_t(bytes_[1])|(std::uint16_t(bytes_[2])<<8);
        }
        std::uint16_t transform_key() const noexcept {
            return std::uint16_t(bytes_[transform_offset])|
                (std::uint16_t(bytes_[transform_offset+1])<<8);
        }
        std::uint8_t raw_scalar5() const noexcept {return bytes_[raw_scalar5_offset];}
        std::uint8_t raw_scalar6() const noexcept {return bytes_[raw_scalar6_offset];}
        std::span<const std::uint8_t,component_bytes> components() const noexcept {
            return std::span<const std::uint8_t,component_bytes>{bytes_.data()+components_offset,component_bytes};
        }
        bool operator==(const Record&) const = default;
    private:
        friend class RecoveredTaiwanPlayerAppearanceUpdate;
        explicit Record(Bytes bytes):bytes_(bytes) {}
        Bytes bytes_;
    };
    // Complete actual producer bytes only. Width/opcode validation is not proof
    // of native resource eligibility, durable state, identity or ownership.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return std::nullopt;
        Bytes owned;
        for(std::size_t i=0;i<owned.size();++i)owned[i]=bytes[i];
        return Record(owned);
    }
    static const Bytes& encode_logical(const Record& record) noexcept {return record.bytes_;}
};
}
