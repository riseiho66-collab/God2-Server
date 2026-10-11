#pragma once
#include "game/ExtendedBattleDeltaAmount.h"
#include <algorithm>
#include <cstdint>
#include <limits>
#include <optional>

namespace god2 {
// Owner numeric64 directive. Absolute HP representation, not a damage formula,
// native role authority or gameplay maximum. Zero is a valid remaining HP.
// SQLite INTEGER represents nonnegative signed64; the coin cap does not apply.
class ExtendedHealthAmount {
public:
    static constexpr std::uint64_t representation_maximum=
        static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    static std::optional<ExtendedHealthAmount> from(std::uint64_t value) noexcept {
        if(value>representation_maximum)return std::nullopt;
        return ExtendedHealthAmount(value);
    }
    // Owner-authorized extended arithmetic, distinct from original DWORD bitmath.
    // Preserve signed loss/healing; clamp to the actual owned [0, maximum] range
    // without overflowing or choosing a gameplay maximum. INT64_MIN is safe.
    static std::optional<ExtendedHealthAmount> apply(std::uint64_t current,
            std::uint64_t maximum, ExtendedBattleDeltaAmount change) noexcept {
        if(current>maximum || !from(current) || !from(maximum))return std::nullopt;
        const auto magnitude=change.magnitude();
        return ExtendedHealthAmount(change.value<0 ? current-std::min(current,magnitude) :
            current+std::min(maximum-current,magnitude));
    }
    std::uint64_t value() const noexcept {return value_;}
    std::int64_t sqlite_integer() const noexcept {return static_cast<std::int64_t>(value_);}
    // Absolute DWORD storage is distinct from a signed DWORD damage delta.
    // This check proves width only, not legacy bit31 arithmetic equivalence.
    std::optional<std::uint32_t> native_unsigned_dword() const noexcept {
        if(value_>std::numeric_limits<std::uint32_t>::max())return std::nullopt;
        return static_cast<std::uint32_t>(value_);
    }
    bool operator==(const ExtendedHealthAmount&) const=default;
private:
    explicit ExtendedHealthAmount(std::uint64_t value) noexcept:value_(value) {}
    std::uint64_t value_;
};
}
