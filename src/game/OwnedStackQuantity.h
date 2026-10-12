#pragma once
#include <cstdint>
#include <optional>

namespace god2 {
// CUSTOM-0089: owner-selected quantity cap for source-qualified stackable
// items only. Not a bag slot count, equipment count, buy limit or item grant.
// Caller still owns identity, stackability, metadata, revisions and authority.
class OwnedStackQuantity {
public:
    static constexpr std::uint8_t maximum=99;
    // Common custody quantities are uint64. Check the complete input before
    // the bounded BYTE projection; a 32-bit argument would discard high bits.
    static std::optional<OwnedStackQuantity> from(std::uint64_t count)noexcept {
        if(count>maximum)return std::nullopt;
        return OwnedStackQuantity(static_cast<std::uint8_t>(count));
    }
    std::uint8_t value()const noexcept{return count_;}
    std::optional<OwnedStackQuantity> increase(std::uint64_t amount)const noexcept {
        if(amount>std::uint64_t(maximum-count_))return std::nullopt;
        return OwnedStackQuantity(static_cast<std::uint8_t>(count_+amount));
    }
    std::optional<OwnedStackQuantity> decrease(std::uint64_t amount)const noexcept {
        if(amount>count_)return std::nullopt;
        return OwnedStackQuantity(static_cast<std::uint8_t>(count_-amount));
    }
    bool operator==(const OwnedStackQuantity&)const=default;
private:
    explicit OwnedStackQuantity(std::uint8_t count)noexcept:count_(count){}
    std::uint8_t count_;
};
}
