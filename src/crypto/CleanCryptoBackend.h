#pragma once

#include "crypto/ICryptoBackend.h"

namespace god2::crypto {

class CleanCryptoBackend final : public ICryptoBackend {
public:
    CryptoSession InitSession(
        std::span<const std::uint8_t> seed,
        std::span<const std::uint8_t> table) override {
        return god2::crypto::InitSession(seed, table);
    }

    std::vector<std::uint8_t> Encrypt(
        CryptoState& state, std::span<const std::uint8_t> body) override {
        return god2::crypto::Encrypt(state, body);
    }

    std::vector<std::uint8_t> Decrypt(
        CryptoState& state, std::span<const std::uint8_t> body) override {
        return god2::crypto::Decrypt(state, body);
    }
};

} // namespace god2::crypto
