#pragma once
#include <cstdint>
#include <limits>
#include <optional>
#include <string>

namespace god2 {
// CUSTOM-0088: owner-selected exact coin cap, not original native economy.
// Shared wallet arithmetic uses this domain; native DWORD consumers and an
// existing database's CHECK constraints still require separate extensions.
// No implicit narrowing conversion.
class ExtendedCoinAmount {
public:
    static constexpr std::uint64_t maximum=99999999999ULL;
    static std::optional<ExtendedCoinAmount> from(std::uint64_t value) noexcept {
        if(value>maximum)return std::nullopt;return ExtendedCoinAmount(value);
    }
    std::uint64_t value()const noexcept{return value_;}
    std::int64_t sqlite_integer()const noexcept{return static_cast<std::int64_t>(value_);}
    std::string decimal()const{return std::to_string(value_);}
    std::optional<ExtendedCoinAmount> credit(ExtendedCoinAmount amount)const noexcept {
        if(amount.value_>maximum-value_)return std::nullopt;
        return ExtendedCoinAmount(value_+amount.value_);
    }
    std::optional<ExtendedCoinAmount> debit(ExtendedCoinAmount amount)const noexcept {
        if(amount.value_>value_)return std::nullopt;
        return ExtendedCoinAmount(value_-amount.value_);
    }
    // One conserved outgoing/incoming exchange, with validation BEFORE any
    // arithmetic. The caller still owns participants, CAS and settlement.
    static std::optional<ExtendedCoinAmount> exchange(
        std::uint64_t balance,std::uint64_t outgoing,std::uint64_t incoming) noexcept {
        const auto saved=from(balance),sent=from(outgoing),received=from(incoming);
        if(!saved || !sent || !received)return std::nullopt;
        const auto remaining=saved->debit(*sent);
        return remaining?remaining->credit(*received):std::nullopt;
    }
    // Bits alone do not qualify signed native GUI/arithmetic. A caller must
    // still establish its client capability before using a native DWORD.
    std::optional<std::uint32_t> native_dword_bits()const noexcept {
        if(value_>std::numeric_limits<std::uint32_t>::max())return std::nullopt;
        return static_cast<std::uint32_t>(value_);
    }
    bool operator==(const ExtendedCoinAmount&)const=default;
private:
    explicit ExtendedCoinAmount(std::uint64_t v)noexcept:value_(v){}
    std::uint64_t value_;
};
}
