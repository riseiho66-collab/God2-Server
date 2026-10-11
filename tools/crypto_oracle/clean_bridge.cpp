#include "crypto/God2CryptoClean.h"

#include <algorithm>
#include <cstring>
#include <vector>

#ifdef _WIN32
#define GOD2_CLEAN_EXPORT extern "C" __declspec(dllexport)
#else
#define GOD2_CLEAN_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {
using namespace god2::crypto;
constexpr std::size_t KEY_OFFSET = 0x2420;
constexpr std::size_t PROOF_OFFSET = 0x2520;
constexpr std::size_t FEEDBACK_OFFSET = 0x2556;

bool Overlaps(const void* a, std::size_t an, const void* b, std::size_t bn) {
    if (an == 0 || bn == 0) return false;
    const auto av = reinterpret_cast<std::uintptr_t>(a);
    const auto bv = reinterpret_cast<std::uintptr_t>(b);
    return av <= bv ? bv - av < an : av - bv < bn;
}
} // namespace

// Returns the serialized size, or a negative error without writing outputs.
GOD2_CLEAN_EXPORT int God2CleanInit(
    const std::uint8_t* seed, unsigned seedlen,
    const std::uint8_t* table, unsigned tablelen,
    std::uint8_t* state, unsigned capacity) {
    if (!seed || seedlen != 16 || !table || tablelen != 1024 ||
        !state || capacity < STATE_SIZE) return -1;
    try {
        const auto session = InitSession({seed, seedlen}, {table, tablelen});
        std::array<std::uint8_t, STATE_SIZE> bytes{};
        bytes[8] = 1;
        std::copy(session.tx.key.begin(), session.tx.key.end(), bytes.begin() + KEY_OFFSET);
        std::copy(session.tx.proof.begin(), session.tx.proof.end(), bytes.begin() + PROOF_OFFSET);
        bytes[FEEDBACK_OFFSET] = session.tx.feedback;
        std::memcpy(state, bytes.data(), bytes.size());
        return static_cast<int>(STATE_SIZE);
    } catch (...) {
        return -2;
    }
}

// before may alias after; input may alias output. Output and after must not
// overlap, since they describe two independently observable results.
GOD2_CLEAN_EXPORT int God2CleanTransform(
    int decrypt, const std::uint8_t* before, unsigned statelen,
    const std::uint8_t* input, unsigned len,
    std::uint8_t* output, unsigned outcapacity,
    std::uint8_t* after, unsigned aftercapacity) {
    if ((decrypt != 0 && decrypt != 1) || !before || statelen < STATE_SIZE ||
        len > MAX_RAW_SIZE || (len && (!input || !output)) || outcapacity < len ||
        !after || aftercapacity < statelen || Overlaps(output, len, after, statelen)) {
        return -1;
    }
    try {
        CryptoState state;
        std::copy_n(before + KEY_OFFSET, state.key.size(), state.key.begin());
        std::copy_n(before + PROOF_OFFSET, state.proof.size(), state.proof.begin());
        state.feedback = before[FEEDBACK_OFFSET];
        state.enabled = std::uint32_t(before[8]) | (std::uint32_t(before[9]) << 8) |
                        (std::uint32_t(before[10]) << 16) | (std::uint32_t(before[11]) << 24);
        const std::span<const std::uint8_t> body = len
            ? std::span<const std::uint8_t>(input, len) : std::span<const std::uint8_t>();
        const auto result = decrypt ? Decrypt(state, body) : Encrypt(state, body);
        // Stage all bytes before committing, including unmodeled state fields.
        const std::vector<std::uint8_t> snapshot(before, before + statelen);
        if (len) std::memcpy(output, result.data(), len);
        std::memcpy(after, snapshot.data(), statelen);
        return static_cast<int>(len);
    } catch (...) {
        return -2;
    }
}
