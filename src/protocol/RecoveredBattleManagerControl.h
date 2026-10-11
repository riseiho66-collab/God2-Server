#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// TW battle S2C86/selector2: RVA1144D8 ->117500 in the pinned
// God2.unpacked.exe identified below. This view retains supplied native bytes;
// it supplies no issuer, permission, queue, template or state mutation.
struct RecoveredBattleManagerControl {
    static constexpr char image_sha256[] =
        "5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde";
    static constexpr std::size_t logical_size = 17;
    static constexpr bool runtime_emission_enabled = false;
    static constexpr bool runtime_mutation_enabled = false;
    using Bytes = std::array<std::uint8_t, logical_size>;

    enum class HelperBranch {
        AttachmentThenHideSide1,
        ResetAllPrimaryActors,
        NoRecoveredHelperCall
    };

    class Record {
    public:
        std::uint8_t mode() const noexcept { return bytes_[3]; }
        // The selector2 handler does not read logical+2 as an actor position.
        std::uint8_t opaque_byte2() const noexcept { return bytes_[2]; }
        HelperBranch helper_branch() const noexcept {
            if (mode() == 1) return HelperBranch::AttachmentThenHideSide1;
            if (mode() == 2) return HelperBranch::ResetAllPrimaryActors;
            // The bounded handler calls neither recovered helper for other
            // modes. Its return value is not server success or permission.
            return HelperBranch::NoRecoveredHelperCall;
        }
        std::optional<std::uint8_t> raw_attachment_index() const noexcept {
            if (mode() != 1) return std::nullopt;
            // 126060 checks index<2 only for attachment cleanup. Every BYTE
            // still reaches its side1 loop; index>=2 is not packet rejection.
            return bytes_[5];
        }
    private:
        friend struct RecoveredBattleManagerControl;
        explicit Record(const Bytes& bytes) noexcept : bytes_(bytes) {}
        Bytes bytes_;
    };

    // Caller establishes S2C direction, battle state and matching client build.
    // Retain all modes, all index bytes and every uninterpreted original byte.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != 0x86 || logical[1] != 2)
            return std::nullopt;
        Bytes bytes;
        std::copy(logical.begin(), logical.end(), bytes.begin());
        return Record(bytes);
    }
    static Bytes encode_logical(const Record& record) noexcept { return record.bytes_; }
};
}
