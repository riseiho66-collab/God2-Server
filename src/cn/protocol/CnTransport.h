#pragma once
#include <array>
#include <cstdint>
#include <span>
#include <vector>

namespace god2cn {
using Bytes = std::vector<std::uint8_t>;
// CN-native transport only. Logical bytes may contain MORE THAN ONE record;
// the S2C length table must never be used to split C2S requests.
class CnTransport {
public:
    static constexpr std::size_t max_logical = 0xa00;
    static constexpr std::size_t max_wire = max_logical + 3;
    explicit CnTransport(const std::array<std::uint8_t,16>& seed);
    Bytes seed_frame() const;
    bool accepts_challenge(std::span<const std::uint8_t> frame) const;
    Bytes decode_client_frame(std::span<const std::uint8_t> frame) const;
    Bytes encode_server_frame(std::span<const std::uint8_t> logical) const;
private:
    std::array<std::uint8_t,16> seed_{}, challenge_{};
    std::array<std::uint8_t,256> key_{};
    std::uint8_t initial_previous_{};
    Bytes frame(std::span<const std::uint8_t> logical, bool encrypted) const;
};
}
