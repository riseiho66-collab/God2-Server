#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// Logical opcode 0x72 only; no catalog, placement, or runtime eligibility policy.
// Evidence: docs/research/current-npc-record-20260919.md.
class RecoveredNpcRecord {
public:
    static constexpr std::size_t wireSize = 21;
    using Bytes = std::array<std::uint8_t, wireSize>;

    static std::optional<RecoveredNpcRecord> parse(std::span<const std::uint8_t> input) {
        if (input.size() != wireSize || input[0] != 0x72)
            return std::nullopt;
        Bytes bytes;
        std::copy(input.begin(), input.end(), bytes.begin());
        return RecoveredNpcRecord(bytes);
    }

    Bytes encode() const noexcept { return bytes_; }
    std::uint32_t rawSelector() const noexcept { return read32(1); }
    std::uint16_t primarySelector() const noexcept {
        return static_cast<std::uint16_t>(rawSelector());
    }
    // Both native 72 constructors mask the selector to 16 bits before pool
    // lookup/store. Native 75 later removes that same pool identity.
    std::uint16_t instanceIdentity() const noexcept { return primarySelector(); }
    std::uint16_t secondarySelector() const noexcept {
        return static_cast<std::uint16_t>(rawSelector() >> 16);
    }
    std::uint32_t packedPosition() const noexcept { return read32(17); }
    std::uint16_t x() const noexcept {
        return static_cast<std::uint16_t>((packedPosition() >> 2) & 0x7fff);
    }
    std::uint16_t y() const noexcept {
        return static_cast<std::uint16_t>(packedPosition() >> 17);
    }
    std::uint8_t opaquePositionLowBits() const noexcept {
        return static_cast<std::uint8_t>(packedPosition() & 3);
    }
    // 004CC635: three high bits of logical byte9, not a compass label.
    std::uint8_t facing() const noexcept { return bytes_[9] >> 5; }
    bool setFacing(std::uint64_t value) noexcept {
        if(value>7) return false;
        bytes_[9]=static_cast<std::uint8_t>((bytes_[9]&0x1f)|(value<<5));
        return true;
    }

    bool setRawSelector(std::uint64_t value) noexcept {
        if (value > 0xffffffffULL)
            return false;
        write32(1, static_cast<std::uint32_t>(value));
        return true;
    }

    bool setPosition(std::uint64_t xValue, std::uint64_t yValue) noexcept {
        if (xValue > 0x7fff || yValue > 0x7fff)
            return false;
        write32(17, static_cast<std::uint32_t>((yValue << 17) | (xValue << 2))
                        | opaquePositionLowBits());
        return true;
    }

private:
    explicit RecoveredNpcRecord(Bytes bytes) noexcept : bytes_(bytes) {}

    std::uint32_t read32(std::size_t offset) const noexcept {
        std::uint32_t result = 0;
        for (unsigned i = 0; i < 4; ++i)
            result |= static_cast<std::uint32_t>(bytes_[offset + i]) << (8 * i);
        return result;
    }
    void write32(std::size_t offset, std::uint32_t value) noexcept {
        for (unsigned i = 0; i < 4; ++i)
            bytes_[offset + i] = static_cast<std::uint8_t>(value >> (8 * i));
    }

    Bytes bytes_;
};

} // namespace god2
