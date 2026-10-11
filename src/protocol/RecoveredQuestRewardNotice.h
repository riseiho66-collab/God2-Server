#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>

namespace god2 {
// Current Taiwan S2C02, SystemMessage626/644, native channel4 notification.
// Presentation of an already committed award only. Does not synchronize total
// EXP/reputation, derive progression, or modify role/God/pet state.
struct RecoveredQuestRewardNotice {
    enum class Kind : std::uint16_t { Reputation = 626, Experience = 644 };
    using Logical = std::array<std::uint8_t, 23>;
    static constexpr std::uint64_t maximum_amount = 999999999999999ULL;
    static constexpr Logical logical(Kind kind, std::uint64_t amount) {
        if (kind != Kind::Reputation && kind != Kind::Experience)
            throw std::invalid_argument("Unqualified reward notice kind");
        if (!amount || amount > maximum_amount)
            throw std::invalid_argument("Reward notice needs 1..15 decimal digits");
        const auto message = static_cast<std::uint16_t>(kind);
        Logical out{0x02, static_cast<std::uint8_t>(message),
                    static_cast<std::uint8_t>(message >> 8)};
        std::array<std::uint8_t, 15> reversed{};
        unsigned digits = 0;
        do {
            reversed[digits++] = static_cast<std::uint8_t>('0' + amount % 10);
            amount /= 10;
        } while (amount);
        for (unsigned i = 0; i < digits; ++i) out[5+i] = reversed[digits-1-i];
        // Item key0 selects text16; variant0 and opaque tail0 are qualified.
        // The remaining text bytes include at least one explicit NUL.
        return out;
    }
};
}
