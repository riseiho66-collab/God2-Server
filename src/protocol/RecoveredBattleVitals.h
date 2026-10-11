#pragma once

#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// Current S2C86 kinds 0/1. Native 117230/1173A0 -> E71E0 -> role HP/MP.
// Format and consumer semantics only: no monster template or damage authority.
struct RecoveredBattleVitals {
    static constexpr std::size_t logical_size = 17;
    static constexpr bool runtime_emission_enabled = false;
    static constexpr bool runtime_mutation_enabled = false;
    using Bytes = std::array<std::uint8_t, logical_size>;
    enum class Resource : std::uint8_t { Hp = 0, Mp = 1 };

    class Record {
    public:
        Resource resource() const noexcept { return static_cast<Resource>(bytes_[1]); }
        std::uint8_t position() const noexcept { return bytes_[2]; }
        std::uint8_t side() const noexcept { return position() / 14; }
        std::uint8_t slot() const noexcept { return position() % 14; }
        std::uint32_t current() const noexcept { return word32(9); }
        std::uint32_t maximum() const noexcept { return word32(5); }
        // True identifies a native write branch, not a guarantee that its actor exists.
        bool native_actor_write_supported() const noexcept {
            return resource() == Resource::Hp || side() == 0;
        }
        std::span<const std::uint8_t, 2> opaque_word() const noexcept {
            return std::span<const std::uint8_t, logical_size>(bytes_).subspan<3, 2>();
        }
        std::span<const std::uint8_t, 4> opaque_tail() const noexcept {
            return std::span<const std::uint8_t, logical_size>(bytes_).subspan<13, 4>();
        }
    private:
        friend struct RecoveredBattleVitals;
        explicit Record(const Bytes& bytes) noexcept : bytes_(bytes) {}
        std::uint32_t word32(std::size_t offset) const noexcept {
            return std::uint32_t{bytes_[offset]} | (std::uint32_t{bytes_[offset + 1]} << 8) |
                (std::uint32_t{bytes_[offset + 2]} << 16) | (std::uint32_t{bytes_[offset + 3]} << 24);
        }
        Bytes bytes_;
    };

    // Caller must establish S2C direction and battle state. This is not C2S86.
    // Preserve unsupported-side MP records without pretending the client applies them.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != 0x86 ||
            logical[1] > 1 || logical[2] >= 28) return std::nullopt;
        Bytes bytes;
        std::copy(logical.begin(), logical.end(), bytes.begin());
        return Record(bytes);
    }
    static Bytes encode_logical(const Record& record) noexcept { return record.bytes_; }
};
}
