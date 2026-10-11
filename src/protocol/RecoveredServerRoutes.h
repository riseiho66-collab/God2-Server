#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <stdexcept>

namespace god2 {
// Loopback candidate, not captured server bytes. Current pinned client RVAs
// 14234/1426F/142D0 consume 04/05/06; 12310 resolves record byte 32.
// See docs/research/current-login-character-socket-topology-20260919.md.
struct RecoveredServerRoutes {
    using Address = std::array<std::uint8_t, 4>;
    struct Frames {
        std::array<std::uint8_t, 8> group;
        std::array<std::uint8_t, 12> endpoint;
        std::array<std::uint8_t, 8> route;
    };

    // Exactly one endpoint in group 0/subgroup 0, emitted in member order.
    // Field types bound port/ID; zero cannot identify a usable route.
    static constexpr Frames decoded(Address address, std::uint16_t port,
                                    std::uint8_t route_id = 1) {
        if (address[0] != 127 || port == 0 || route_id == 0)
            throw std::invalid_argument("Route requires loopback IPv4, port 1..65535 and ID 1..255");
        Frames frames{
            {8, 0, 4, 0, 0, 1, 0, 0},
            {12, 0, 5, 0, 0, address[0], address[1], address[2], address[3],
             static_cast<std::uint8_t>(port), static_cast<std::uint8_t>(port >> 8), 0},
            {8, 0, 6, static_cast<std::uint8_t>(route_id), 0, 0, 0, 0},
        };
        // Uninterpreted 05 byte 2 and 06 bytes 2..4 remain zero.
        checksum(frames.group);
        checksum(frames.endpoint);
        checksum(frames.route);
        return frames;
    }

    static constexpr Frames wire(std::uint16_t port, std::uint8_t route_id,
                                 Address address = {127, 0, 0, 1}) {
        auto frames = decoded(address, port, route_id);
        encode(frames.group);
        encode(frames.endpoint);
        encode(frames.route);
        return frames;
    }

    static constexpr std::array<std::uint8_t, 28> wire(
            Address address, std::uint16_t port, std::uint8_t route_id = 1) {
        const auto frames = wire(port, route_id, address);
        std::array<std::uint8_t, 28> result{};
        std::size_t at = 0;
        for (auto byte : frames.group) result[at++] = byte;
        for (auto byte : frames.endpoint) result[at++] = byte;
        for (auto byte : frames.route) result[at++] = byte;
        return result;
    }

private:
    template<std::size_t N>
    static constexpr void checksum(std::array<std::uint8_t, N>& frame) {
        std::uint8_t sum = 0;
        for (std::size_t i = 0; i + 1 < N; ++i)
            sum = static_cast<std::uint8_t>(sum + frame[i] + 0x3c);
        frame.back() = sum;
    }

    template<std::size_t N>
    static constexpr void encode(std::array<std::uint8_t, N>& frame) {
        std::uint8_t previous = 0;
        for (std::size_t i = 2; i < N; ++i) {
            const auto clear = frame[i];
            frame[i] = static_cast<std::uint8_t>(
                (clear ^ recovered_zero_seed_key[i - 2]) + previous - 3);
            previous = clear;
        }
    }
};
}
