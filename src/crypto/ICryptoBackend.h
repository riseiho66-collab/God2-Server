#pragma once

#include "crypto/God2CryptoClean.h"

#include <cstdint>
#include <span>
#include <vector>

namespace god2::crypto {

enum class CryptoBackend { Clean, OracleLab };

// Bodies only. Framing, checksums and protocol transitions belong to the caller.
// Each connection owns a CryptoSession; TX and RX must remain separate.
class ICryptoBackend {
public:
    virtual ~ICryptoBackend() = default;

    virtual CryptoSession InitSession(
        std::span<const std::uint8_t> seed,
        std::span<const std::uint8_t> table) = 0;
    virtual std::vector<std::uint8_t> Encrypt(
        CryptoState& state, std::span<const std::uint8_t> body) = 0;
    virtual std::vector<std::uint8_t> Decrypt(
        CryptoState& state, std::span<const std::uint8_t> body) = 0;
};

} // namespace god2::crypto
