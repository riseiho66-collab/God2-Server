#include "God2CryptoClean.h"

#include <algorithm>
#include <stdexcept>

namespace god2::crypto {

CryptoSession InitSession(std::span<const std::uint8_t> seed16,
                          std::span<const std::uint8_t> table1024) {
    if (seed16.size() != 16 || table1024.size() != 1024) {
        throw std::invalid_argument("Expected 16 seed bytes and 1024 table bytes");
    }
    CryptoState state;
    std::copy(seed16.begin(), seed16.end(), state.key.begin());
    // 0x410570 -> 0x410490 -> 0x410370. The helper's second argument is
    // seed[i & 15], not i; that byte selects another seed byte and four signs.
    for (std::size_t i = 16; i < state.key.size(); ++i) {
        const auto selector = seed16[i & 15];
        const auto value = seed16[selector & 15];
        auto mixed = static_cast<std::uint8_t>(i + selector);
        for (unsigned shift = 0; shift < 4; ++shift) {
            mixed = static_cast<std::uint8_t>(
                (selector & (0x80u >> shift))
                    ? mixed + (value >> shift)
                    : mixed - (value << shift));
        }
        state.key[i] = static_cast<std::uint8_t>(table1024[i] + mixed);
    }
    // 0x410420: adjacent table-byte sum selects an expanded key byte.
    for (std::size_t i = 0; i < state.proof.size(); ++i) {
        const auto index = (unsigned(table1024[i]) + table1024[i + 1]) & 255u;
        state.proof[i] = static_cast<std::uint8_t>(state.key[index] + table1024[i]);
    }
    for (const auto value : state.key) {
        state.feedback = static_cast<std::uint8_t>(state.feedback - value);
    }
    return {state, state};
}

namespace {
std::vector<std::uint8_t> Transform(const CryptoState& state,
                                    std::span<const std::uint8_t> body,
                                    bool decrypt) {
    if (body.size() > MAX_RAW_SIZE) {
        throw std::invalid_argument("Raw body exceeds 4096 bytes");
    }
    std::vector<std::uint8_t> result(body.begin(), body.end());
    if (state.enabled == 0) {
        return result;
    }
    auto previous = state.feedback;
    // 0x410690 / 0x4106f0: feedback is the preceding plaintext byte.
    for (std::size_t i = 0; i < body.size(); ++i) {
        const auto plain = decrypt
            ? static_cast<std::uint8_t>(
                  static_cast<std::uint8_t>(body[i] + 3 - previous) ^ state.key[i & 255])
            : body[i];
        result[i] = decrypt ? plain : static_cast<std::uint8_t>(
            (plain ^ state.key[i & 255]) + previous - 3);
        previous = plain;
    }
    return result;
}
} // namespace

std::vector<std::uint8_t> Encrypt(CryptoState& state,
                                  std::span<const std::uint8_t> rawbody) {
    return Transform(state, rawbody, false);
}

std::vector<std::uint8_t> Decrypt(CryptoState& state,
                                  std::span<const std::uint8_t> rawbody) {
    return Transform(state, rawbody, true);
}

} // namespace god2::crypto
