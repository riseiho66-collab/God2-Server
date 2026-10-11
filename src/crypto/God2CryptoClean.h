#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace god2::crypto {

inline constexpr std::size_t STATE_SIZE = 0x255c;
inline constexpr std::size_t MAX_RAW_SIZE = 4096;

struct CryptoState {
    std::array<std::uint8_t, 256> key{};
    std::array<std::uint8_t, 16> proof{};
    std::uint8_t feedback{};
    std::uint32_t enabled = 1;
};

struct CryptoSession {
    CryptoState tx;
    CryptoState rx;
};

// Requires exactly 16 seed bytes and 1024 caller-supplied table bytes.
CryptoSession InitSession(std::span<const std::uint8_t> seed16,
                          std::span<const std::uint8_t> table1024);

// Raw body only: no header/checksum processing. Each call resets the local
// key index and feedback; neither transform changes persistent state.
// Invalid lengths throw std::invalid_argument (including bodies over 4096).
std::vector<std::uint8_t> Encrypt(CryptoState& state,
                                  std::span<const std::uint8_t> rawbody);
std::vector<std::uint8_t> Decrypt(CryptoState& state,
                                  std::span<const std::uint8_t> rawbody);

} // namespace god2::crypto
