#pragma once
#include <cstdint>
#include <limits>
#include <optional>

namespace god2 {
// Owner numeric64 directive, not a recovered award rule or progression cap.
// SQLite and this Lua integer path represent nonnegative signed64 amounts.
// The bound below is representability, NOT a chosen EXP gameplay maximum;
// coins'99999999999 cap never applies here. No implicit narrowing conversion.
class ExtendedExperienceAmount {
public:
    static constexpr std::uint64_t representation_maximum=
        static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    static std::optional<ExtendedExperienceAmount> from(std::uint64_t value) noexcept {
        if(value>representation_maximum)return std::nullopt;
        return ExtendedExperienceAmount(value);
    }
    std::uint64_t value() const noexcept {return value_;}
    std::int64_t sqlite_integer() const noexcept {return static_cast<std::int64_t>(value_);}
    std::optional<ExtendedExperienceAmount> credit(ExtendedExperienceAmount earned) const noexcept {
        if(earned.value_>representation_maximum-value_)return std::nullopt;
        return ExtendedExperienceAmount(value_+earned.value_);
    }
    static std::optional<ExtendedExperienceAmount> accumulate(std::uint64_t saved,std::uint64_t earned) noexcept {
        const auto before=from(saved),grant=from(earned);
        if(!before || !grant)return std::nullopt;
        return before->credit(*grant);
    }
    bool operator==(const ExtendedExperienceAmount&) const=default;
private:
    explicit ExtendedExperienceAmount(std::uint64_t value) noexcept:value_(value) {}
    std::uint64_t value_;
};
}
